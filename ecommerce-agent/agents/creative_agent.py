"""Creative Agent — multi-modal content generation: copywriting + product images."""

import time
from .base_agent import BaseAgent


class CreativeAgent(BaseAgent):
    def __init__(self, db_manager, claude_service, image_service, config: dict = None):
        super().__init__(db_manager, claude_service, config)
        self.image_svc = image_service
        self.agent_name = "creative"

    CONTENT_TYPES = {
        "listing_copy": "Amazon listing bullet points (5 bullets, 200 chars each)",
        "a_plus": "A+ Content / Enhanced Brand Content description (300 words, with subheadings)",
        "social_post": "Social media promotional post (Instagram/TikTok style, 150 words max)",
        "ad_copy": "Sponsored Products ad headline + description (50 + 150 chars)",
    }

    def run(self, product_id: int, trigger: str = "scheduled", tone: str = "persuasive") -> dict:
        t0 = time.time()
        try:
            product = self.db.fetch_one(
                "SELECT * FROM products WHERE id=?", (product_id,)
            )
            if not product:
                raise ValueError(f"Product {product_id} not found")

            generated = []

            # Generate text content for each type
            for ctype, cdesc in self.CONTENT_TYPES.items():
                text = self.generate_copy(
                    product["title"],
                    self._get_product_features(product_id),
                    tone,
                    cdesc,
                    product.get("market", "US"),
                )
                cid = self.db.insert("generated_content", {
                    "product_id": product_id,
                    "content_type": ctype,
                    "variant_name": f"v1_{trigger}",
                    "content_text": text,
                    "trigger_reason": trigger,
                })
                generated.append({"id": cid, "type": ctype, "text": text[:100] + "..."})

            # Generate product image
            issues = self._get_top_issues(product_id)
            features = self._get_product_features(product_id)
            badge = "SALE" if trigger == "price_drop" else ("NEW" if trigger == "trend_detected" else None)
            img_path = self.image_svc.generate_product_image(
                product["title"],
                features[:4] + ([f"Fixed: {issues[0]}" if issues else "Premium Quality"][:1]),
                badge=badge,
            )
            if img_path:
                self.db.insert("generated_content", {
                    "product_id": product_id,
                    "content_type": "detail_image",
                    "variant_name": f"v1_{trigger}",
                    "image_path": img_path,
                    "trigger_reason": trigger,
                })
                generated.append({"type": "detail_image", "path": img_path})

            duration = int((time.time() - t0) * 1000)
            output = {"product": product["title"], "generated": len(generated), "trigger": trigger}
            self.log_run("completed", f"product_id={product_id}, trigger={trigger}", str(output), duration)
            return output
        except Exception as e:
            self.log_run("failed", f"product_id={product_id}", "", 0, str(e))
            raise

    def generate_copy(
        self, product_title: str, features: list[str], tone: str, content_desc: str, market: str
    ) -> str:
        return self.claude.generate_copy(product_title, features, tone, content_desc, market)

    def _get_product_features(self, product_id: int) -> list[str]:
        product = self.db.fetch_one("SELECT * FROM products WHERE id=?", (product_id,))
        if not product:
            return []
        return [
            f"Premium {product['category']} quality",
            f"Professional-grade {product['brand']} design",
            "Fast free shipping available",
            "30-day money-back guarantee",
            "24/7 customer support",
        ]

    def _get_top_issues(self, product_id: int) -> list[str]:
        from collections import Counter
        rows = self.db.fetch_all(
            "SELECT key_issues FROM reviews WHERE product_id=? AND key_issues IS NOT NULL AND key_issues!=''",
            (product_id,),
        )
        counter = Counter()
        for r in rows:
            for issue in r["key_issues"].split(","):
                issue = issue.strip()
                if issue:
                    counter[issue] += 1
        return [i for i, _ in counter.most_common(3)]
