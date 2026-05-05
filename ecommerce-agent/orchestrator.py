"""Central Orchestrator — coordinates all four agents and manages scheduling."""

import time
from database.db_manager import SQLiteManager
from services.claude_service import ClaudeService
from services.scraping_service import ScrapingService
from services.image_service import ImageService
from agents.recon_agent import ReconAgent
from agents.sentiment_agent import SentimentAgent
from agents.creative_agent import CreativeAgent
from agents.pricing_agent import PricingBiddingAgent
from config import DB_PATH, IMAGE_DIR


class Orchestrator:
    def __init__(self, api_key: str = None):
        self.db = SQLiteManager(DB_PATH)
        self.claude = ClaudeService(api_key=api_key)
        self.scraper = ScrapingService()
        self.image_svc = ImageService(IMAGE_DIR)

        self.recon = ReconAgent(self.db, self.claude, self.scraper)
        self.sentiment = SentimentAgent(self.db, self.claude)
        self.creative = CreativeAgent(self.db, self.claude, self.image_svc)
        self.pricing = PricingBiddingAgent(self.db, self.claude)

        self._initialized = False

    def initialize(self):
        if self._initialized:
            return
        self.db.initialize()
        if self.db.is_empty():
            from data.generator import MockDataGenerator
            MockDataGenerator(self.db, self.scraper, self.claude).populate()
        self._initialized = True

    def run_recon(self, product_ids: list[int] = None) -> dict:
        return self.recon.run(product_ids)

    def run_sentiment(self, product_ids: list[int] = None) -> dict:
        return self.sentiment.run(product_ids)

    def run_creative(self, product_id: int, trigger: str = "scheduled", tone: str = "persuasive") -> dict:
        return self.creative.run(product_id, trigger, tone)

    def run_pricing(self, product_ids: list[int] = None) -> dict:
        return self.pricing.run(product_ids)

    def run_all(self) -> dict:
        t0 = time.time()
        self.initialize()
        results = {}

        results["recon"] = self.run_recon()
        results["sentiment"] = self.run_sentiment()
        results["pricing"] = self.run_pricing()

        # Trigger creative for products with high-severity insights
        high_alert_products = self.db.fetch_all(
            "SELECT DISTINCT product_id FROM strategy_insights "
            "WHERE severity='high' AND actionable=1 AND acted_upon=0 "
            "ORDER BY created_at DESC LIMIT 3"
        )
        creative_results = []
        for p in high_alert_products:
            creative_results.append(
                self.run_creative(p["product_id"], trigger="sentiment_alert")
            )
        if not creative_results:
            products = self.db.fetch_all("SELECT id FROM products LIMIT 2")
            for p in products:
                creative_results.append(
                    self.run_creative(p["id"], trigger="scheduled")
                )
        results["creative"] = creative_results

        results["total_duration_ms"] = int((time.time() - t0) * 1000)
        return results

    def get_overview_stats(self) -> dict:
        return {
            "products": self.db.table_count("products"),
            "avg_price_gap": self._avg_price_gap(),
            "sentiment_score": self._overall_sentiment(),
            "pending_decisions": self.db.table_count("pricing_decisions"),
            "active_insights": self.db.fetch_one(
                "SELECT COUNT(*) as cnt FROM strategy_insights WHERE actionable=1 AND acted_upon=0"
            )["cnt"],
        }

    def _avg_price_gap(self) -> float:
        rows = self.db.fetch_all(
            "SELECT p.our_price, c.price FROM products p "
            "JOIN competitor_listings c ON c.product_id=p.id "
            "WHERE c.scraped_at >= datetime('now', '-7 days')"
        )
        if not rows:
            return 0
        gaps = [(r["price"] - r["our_price"]) / r["our_price"] * 100 for r in rows]
        return round(sum(gaps) / len(gaps), 1)

    def _overall_sentiment(self) -> float:
        row = self.db.fetch_one(
            "SELECT AVG(sentiment_score) as avg_score FROM reviews WHERE sentiment_score IS NOT NULL"
        )
        return round(row["avg_score"] * 100, 1) if row and row["avg_score"] else 50.0
