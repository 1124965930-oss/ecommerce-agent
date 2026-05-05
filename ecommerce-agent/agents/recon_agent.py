"""Reconnaissance Agent — competitor monitoring, price gap detection, stock opportunities."""

import time
from .base_agent import BaseAgent
from config import PRICE_GAP_THRESHOLDS


class ReconAgent(BaseAgent):
    def __init__(self, db_manager, claude_service, scraping_service, config: dict = None):
        super().__init__(db_manager, claude_service, config)
        self.scraper = scraping_service
        self.agent_name = "recon"

    def run(self, product_ids: list[int] = None) -> dict:
        t0 = time.time()
        try:
            products = self._get_products(product_ids)
            total_insights = 0

            for p in products:
                comps = self.scraper.fetch_competitor_data(p["asin"], p["our_price"])
                for c in comps:
                    c["product_id"] = p["id"]
                self.db.insert_many("competitor_listings", comps)

                insights = self.analyze_price_gaps(p["id"], p["our_price"])
                for ins in insights:
                    self.db.insert("strategy_insights", ins)
                    total_insights += 1

                stock_insights = self.detect_stock_opportunities(p["id"])
                for si in stock_insights:
                    self.db.insert("strategy_insights", si)
                    total_insights += 1

            duration = int((time.time() - t0) * 1000)
            result = {
                "products_scanned": len(products),
                "new_listings": len(products) * 4,
                "insights_generated": total_insights,
            }
            self.log_run("completed", str(product_ids), str(result), duration)
            return result
        except Exception as e:
            self.log_run("failed", str(product_ids), "", 0, str(e))
            raise

    def analyze_price_gaps(self, product_id: int, our_price: float) -> list[dict]:
        latest = self.db.fetch_all(
            "SELECT DISTINCT competitor_name, price FROM competitor_listings "
            "WHERE product_id=? AND scraped_at >= datetime('now', '-1 day') "
            "ORDER BY scraped_at DESC",
            (product_id,),
        )
        if not latest:
            return []

        prices = [c["price"] for c in latest]
        avg_comp = sum(prices) / len(prices)
        gap_pct = (avg_comp - our_price) / our_price

        if abs(gap_pct) < 0.05:
            return []

        description = (
            f"Our price (${our_price:.2f}) is {'above' if gap_pct > 0 else 'below'} "
            f"competitor average (${avg_comp:.2f}) by {abs(gap_pct)*100:.1f}%. "
            f"Range: ${min(prices):.2f} — ${max(prices):.2f}."
        )
        return [{
            "product_id": product_id,
            "insight_type": "price_gap",
            "title": f"Price {'premium' if gap_pct > 0 else 'discount'} of {abs(gap_pct)*100:.0f}% vs market",
            "description": description,
            "severity": "high" if abs(gap_pct) > 0.12 else "medium",
        }]

    def detect_stock_opportunities(self, product_id: int) -> list[dict]:
        stocks = self.db.fetch_all(
            "SELECT competitor_name, stock_status FROM competitor_listings "
            "WHERE product_id=? ORDER BY scraped_at DESC LIMIT 4",
            (product_id,),
        )
        out_of_stock = [s for s in stocks if s["stock_status"] == "out_of_stock"]
        if len(out_of_stock) < 2:
            return []

        return [{
            "product_id": product_id,
            "insight_type": "stock_opportunity",
            "title": f"{len(out_of_stock)} competitors out of stock — market gap",
            "description": (
                f"Competitors {', '.join(s['competitor_name'] for s in out_of_stock)} "
                f"are out of stock. Increase ad spend and highlight shipping speed to capture demand."
            ),
            "severity": "high",
        }]

    def _get_products(self, product_ids):
        if product_ids:
            placeholders = ",".join("?" * len(product_ids))
            return self.db.fetch_all(
                f"SELECT id, asin, title, our_price FROM products WHERE id IN ({placeholders})",
                tuple(product_ids),
            )
        return self.db.fetch_all("SELECT id, asin, title, our_price FROM products")
