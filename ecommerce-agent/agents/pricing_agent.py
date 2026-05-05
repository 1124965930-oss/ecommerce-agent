"""Pricing & Bidding Agent — dynamic price optimization, ad bid adjustment."""

import time
from .base_agent import BaseAgent
from config import PRICING_WEIGHTS


class PricingBiddingAgent(BaseAgent):
    def __init__(self, db_manager, claude_service, config: dict = None):
        super().__init__(db_manager, claude_service, config)
        self.agent_name = "pricing"

    def run(self, product_ids: list[int] = None) -> dict:
        t0 = time.time()
        try:
            products = self._get_products(product_ids)
            decisions = []

            for p in products:
                price_decision = self.calculate_optimal_price(p["id"])
                bid_decision = self.optimize_ad_bid(p["id"])

                reasoning = self.claude.generate_decision(
                    f"Product: {p['title']} | Current Price: ${p['our_price']:.2f} | "
                    f"Cost: ${p['cost']:.2f} | Current Bid: ${p['current_bid']:.2f} | "
                    f"Suggested Price: ${price_decision['price']:.2f} | "
                    f"Suggested Bid: ${bid_decision['bid']:.2f} | "
                    f"Margin Impact: {price_decision['margin_delta']:+.1f}% | "
                    f"Market: {p.get('market', 'US')}",
                    ["Keep current price", f"Adjust to ${price_decision['price']:.2f}", "Monitor and re-evaluate in 24h"],
                )

                did = self.db.insert("pricing_decisions", {
                    "product_id": p["id"],
                    "old_price": p["our_price"],
                    "new_price": price_decision["price"],
                    "old_bid": p["current_bid"],
                    "new_bid": bid_decision["bid"],
                    "reasoning": reasoning,
                    "margin_impact_pct": price_decision["margin_delta"],
                    "conversion_estimate_delta": price_decision.get("conversion_delta", 0),
                })
                decisions.append({
                    "id": did,
                    "product": p["title"],
                    "price": price_decision["price"],
                    "bid": bid_decision["bid"],
                })

            duration = int((time.time() - t0) * 1000)
            output = {"decisions": len(decisions), "details": decisions}
            self.log_run("completed", str(product_ids), str(output), duration)
            return output
        except Exception as e:
            self.log_run("failed", str(product_ids), "", 0, str(e))
            raise

    def calculate_optimal_price(self, product_id: int) -> dict:
        product = self.db.fetch_one("SELECT * FROM products WHERE id=?", (product_id,))
        if not product:
            return {"price": 0, "margin_delta": 0}

        comps = self.db.fetch_all(
            "SELECT price FROM competitor_listings WHERE product_id=? "
            "ORDER BY scraped_at DESC LIMIT 4",
            (product_id,),
        )
        if not comps:
            return {
                "price": round(product["our_price"], 2),
                "margin_delta": round((product["our_price"] - product["cost"]) / product["our_price"] * 100, 1),
            }

        avg_comp = sum(c["price"] for c in comps) / len(comps)
        current_price = product["our_price"]
        cost = product["cost"]

        # Weighted optimization
        w_m = PRICING_WEIGHTS["margin"]
        w_c = PRICING_WEIGHTS["conversion"]

        candidates = [
            round(current_price * (1 + d), 2)
            for d in [-0.08, -0.04, 0, 0.04, 0.08]
        ]
        candidates = [c for c in candidates if c > cost * 1.1]
        if not candidates:
            candidates = [round(cost * 1.2, 2)]

        best_price = current_price
        best_score = -999

        for c in candidates:
            margin = (c - cost) / c * 100
            conv = max(0, 1 - abs(c - avg_comp) / avg_comp * 0.5)
            score = w_m * margin / 100 + w_c * conv
            if score > best_score:
                best_score = score
                best_price = c

        current_margin = (current_price - cost) / current_price * 100
        new_margin = (best_price - cost) / best_price * 100

        return {
            "price": round(best_price, 2),
            "margin_delta": round(new_margin - current_margin, 1),
            "conversion_delta": round(
                max(0, 1 - abs(best_price - avg_comp) / avg_comp * 0.5)
                - max(0, 1 - abs(current_price - avg_comp) / avg_comp * 0.5),
                3,
            ),
        }

    def optimize_ad_bid(self, product_id: int) -> dict:
        product = self.db.fetch_one("SELECT * FROM products WHERE id=?", (product_id,))
        if not product:
            return {"bid": 0, "acos_estimate": 0}

        # Bid = target_acos * avg_order_value * est_conversion_rate
        target_acos = product.get("target_acos", 0.30)
        avg_order = product["our_price"]
        est_conv = 0.08  # baseline 8% conversion

        optimal_bid = round(target_acos * avg_order * est_conv, 2)
        optimal_bid = max(0.10, min(2.0, optimal_bid))

        return {
            "bid": optimal_bid,
            "current_bid": product.get("current_bid", 0),
            "acos_estimate": round(target_acos * 100, 1),
            "change_pct": (
                round((optimal_bid - product.get("current_bid", 0)) / product.get("current_bid", 1) * 100, 1)
                if product.get("current_bid", 0) > 0
                else 0
            ),
        }

    def simulate_margin_impact(self, product_id: int, new_price: float) -> dict:
        product = self.db.fetch_one("SELECT * FROM products WHERE id=?", (product_id,))
        if not product:
            return {}

        cost = product["cost"]
        old_margin = (product["our_price"] - cost) / product["our_price"] * 100
        new_margin = (new_price - cost) / new_price * 100

        return {
            "old_price": product["our_price"],
            "new_price": new_price,
            "old_margin_pct": round(old_margin, 1),
            "new_margin_pct": round(new_margin, 1),
            "margin_delta": round(new_margin - old_margin, 1),
        }

    def _get_products(self, product_ids):
        if product_ids:
            placeholders = ",".join("?" * len(product_ids))
            return self.db.fetch_all(
                f"SELECT * FROM products WHERE id IN ({placeholders})",
                tuple(product_ids),
            )
        return self.db.fetch_all("SELECT * FROM products")
