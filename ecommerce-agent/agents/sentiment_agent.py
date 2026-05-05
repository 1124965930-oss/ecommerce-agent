"""Sentiment Agent — review sentiment analysis, issue extraction, reply generation."""

import time
import json
from collections import Counter
from .base_agent import BaseAgent


class SentimentAgent(BaseAgent):
    def __init__(self, db_manager, claude_service, config: dict = None):
        super().__init__(db_manager, claude_service, config)
        self.agent_name = "sentiment"

    def run(self, product_ids: list[int] = None) -> dict:
        t0 = time.time()
        try:
            products = self._get_products(product_ids)
            total_reviews = 0
            all_issues = Counter()

            for p in products:
                result = self.analyze_product_reviews(p["id"])
                total_reviews += result["reviews_processed"]
                for issue, count in result.get("top_issues", []):
                    all_issues[issue] += count

            duration = int((time.time() - t0) * 1000)
            output = {
                "products_analyzed": len(products),
                "reviews_processed": total_reviews,
                "top_issues": all_issues.most_common(10),
            }
            self.log_run("completed", str(product_ids), str(output), duration)
            return output
        except Exception as e:
            self.log_run("failed", str(product_ids), "", 0, str(e))
            raise

    def analyze_product_reviews(self, product_id: int) -> dict:
        reviews = self.db.fetch_all(
            "SELECT id, body FROM reviews WHERE product_id=? AND sentiment_score IS NULL "
            "ORDER BY collected_at DESC LIMIT 30",
            (product_id,),
        )
        if not reviews:
            stats = self.db.fetch_one(
                "SELECT COUNT(*) as total, "
                "SUM(CASE WHEN sentiment_label='positive' THEN 1 ELSE 0 END) as pos, "
                "SUM(CASE WHEN sentiment_label='negative' THEN 1 ELSE 0 END) as neg, "
                "SUM(CASE WHEN sentiment_label='neutral' THEN 1 ELSE 0 END) as neu "
                "FROM reviews WHERE product_id=?",
                (product_id,),
            )
            return {
                "reviews_processed": 0,
                "total": stats["total"] if stats else 0,
                "positive": stats["pos"] if stats else 0,
                "negative": stats["neg"] if stats else 0,
                "top_issues": [],
            }

        texts = [r["body"] for r in reviews]
        results = self.claude.analyze_sentiment_batch(texts)

        issue_counter = Counter()
        for i, r in enumerate(reviews):
            if i < len(results):
                sr = results[i]
                self.db.execute(
                    "UPDATE reviews SET sentiment_score=?, sentiment_label=?, key_issues=? WHERE id=?",
                    (sr.get("score", 0.5), sr.get("sentiment", "neutral"),
                     ",".join(sr.get("issues", [])), r["id"]),
                )
                for issue in sr.get("issues", []):
                    issue_counter[issue] += 1

        stats = self.db.fetch_one(
            "SELECT COUNT(*) as total, "
            "SUM(CASE WHEN sentiment_label='positive' THEN 1 ELSE 0 END) as pos, "
            "SUM(CASE WHEN sentiment_label='negative' THEN 1 ELSE 0 END) as neg "
            "FROM reviews WHERE product_id=?",
            (product_id,),
        )

        return {
            "reviews_processed": len(reviews),
            "total": stats["total"] if stats else 0,
            "positive": stats["pos"] if stats else 0,
            "negative": stats["neg"] if stats else 0,
            "top_issues": issue_counter.most_common(5),
        }

    def extract_top_issues(self, product_id: int, top_n: int = 5) -> list[tuple]:
        rows = self.db.fetch_all(
            "SELECT key_issues FROM reviews WHERE product_id=? AND key_issues IS NOT NULL AND key_issues != ''",
            (product_id,),
        )
        counter = Counter()
        for r in rows:
            for issue in r["key_issues"].split(","):
                issue = issue.strip()
                if issue:
                    counter[issue] += 1
        return counter.most_common(top_n)

    def generate_reply(self, review_body: str, tone: str = "professional") -> str:
        system = (
            "You are a customer service specialist for an e-commerce brand. "
            "Write a helpful, empathetic reply to this customer review. "
            f"Tone: {tone}. Keep it concise (2-4 sentences)."
        )
        return self.claude.complete(system, f"Review: {review_body}", max_tokens=300)

    def _get_products(self, product_ids):
        if product_ids:
            placeholders = ",".join("?" * len(product_ids))
            return self.db.fetch_all(
                f"SELECT id, title FROM products WHERE id IN ({placeholders})",
                tuple(product_ids),
            )
        return self.db.fetch_all("SELECT id, title FROM products")
