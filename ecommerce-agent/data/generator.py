"""Mock data generator — populates the DB with realistic cross-border e-commerce data."""

import random
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class MockDataGenerator:
    def __init__(self, db_manager, scraping_service, claude_service):
        self.db = db_manager
        self.scraper = scraping_service
        self.claude = claude_service

    def populate(self):
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
        from config import MOCK_PRODUCTS

        for p in MOCK_PRODUCTS:
            pid = self.db.insert("products", {
                "asin": p["asin"], "title": p["title"], "category": p["category"],
                "brand": p["brand"], "our_price": p["price"], "cost": p["cost"],
                "ad_budget_daily": p["ad_budget_daily"], "current_bid": p["current_bid"],
                "target_acos": p["target_acos"], "market": p.get("market", "US"),
            })

            # Generate competitor data
            comps = self.scraper.fetch_competitor_data(p["asin"], p["price"])
            for c in comps:
                c["product_id"] = pid
            self.db.insert_many("competitor_listings", comps)

            # Generate reviews
            reviews = self.scraper.fetch_reviews(p["asin"], count=20)
            batch_texts = [r["body"] for r in reviews]
            sentiment_results = self.claude.analyze_sentiment_batch(batch_texts)

            for j, r in enumerate(reviews):
                r["product_id"] = pid
                if j < len(sentiment_results):
                    sr = sentiment_results[j]
                    r["sentiment_score"] = sr.get("score", 0.5)
                    r["sentiment_label"] = sr.get("sentiment", "neutral")
                    r["key_issues"] = ",".join(sr.get("issues", []))
                else:
                    r["sentiment_score"] = 0.5
                    r["sentiment_label"] = "neutral"
                    r["key_issues"] = ""
                r.pop("platform", None)
            self.db.insert_many("reviews", reviews)

        # Seed strategy insights
        products = self.db.fetch_all("SELECT id, asin, title FROM products")
        for prod in products:
            comps_latest = self.db.fetch_all(
                "SELECT * FROM competitor_listings WHERE product_id=? ORDER BY scraped_at DESC LIMIT 4",
                (prod["id"],),
            )
            prices = [c["price"] for c in comps_latest]
            if prices:
                avg_comp = sum(prices) / len(prices)
                our = self.db.fetch_one("SELECT our_price FROM products WHERE id=?", (prod["id"],))
                gap = (avg_comp - our["our_price"]) / our["our_price"] if our else 0
                if abs(gap) > 0.10:
                    self.db.insert("strategy_insights", {
                        "product_id": prod["id"],
                        "insight_type": "price_gap",
                        "title": f"{'Above' if gap > 0 else 'Below'} market by {abs(gap)*100:.0f}%",
                        "description": f"Our price is {'higher' if gap > 0 else 'lower'} than competitor average (${avg_comp:.2f} vs ${our['our_price']:.2f}). Consider {'lowering' if gap > 0 else 'raising'} price to optimize margin vs conversion.",
                        "severity": "high" if abs(gap) > 0.15 else "medium",
                    })

            # Check stock gaps
            out_of_stock = [c for c in comps_latest if c["stock_status"] == "out_of_stock"]
            if len(out_of_stock) >= 2:
                self.db.insert("strategy_insights", {
                    "product_id": prod["id"],
                    "insight_type": "stock_opportunity",
                    "title": f"{len(out_of_stock)} competitors out of stock!",
                    "description": f"Opportunity to capture market share while {', '.join(c['competitor_name'] for c in out_of_stock)} are out of stock. Consider increasing ad spend and highlighting fast shipping.",
                    "severity": "high",
                })
