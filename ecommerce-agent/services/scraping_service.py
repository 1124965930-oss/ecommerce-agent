"""Scraping service — mock competitor data with realistic jitter."""

import random
import time


class ScrapingService:
    def __init__(self, seed: int = 42):
        random.seed(seed)

    def fetch_competitor_data(
        self, product_asin: str, our_price: float, our_rating: float = 4.3
    ) -> list[dict]:
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
        from config import COMPETITOR_NAMES

        random.seed(hash(product_asin) % 2**31)
        time.sleep(0.02)

        results = []
        for name in COMPETITOR_NAMES:
            price_offset = random.uniform(-0.18, 0.22)
            price = round(our_price * (1 + price_offset), 2)
            price = max(our_price * 0.5, min(our_price * 2.0, price))

            rating_offset = random.uniform(-0.6, 0.4)
            rating = round(min(5.0, max(1.0, our_rating + rating_offset)), 1)

            stock_roll = random.random()
            if stock_roll < 0.10:
                stock = "out_of_stock"
            elif stock_roll < 0.25:
                stock = "low_stock"
            else:
                stock = "in_stock"

            results.append({
                "competitor_name": name,
                "competitor_asin": f"B0{random.randint(100000000,999999999)}",
                "price": price,
                "rating": rating,
                "review_count": random.randint(50, 3500),
                "stock_status": stock,
            })
        return results

    def fetch_reviews(
        self, product_asin: str, count: int = 25
    ) -> list[dict]:
        random.seed(hash(product_asin) % 2**31)
        return [self._generate_review(product_asin) for _ in range(count)]

    def _generate_review(self, asin: str) -> dict:
        from datetime import datetime, timedelta

        sentiment_roll = random.random()
        if sentiment_roll < 0.25:
            rating = random.randint(1, 2)
            templates = [
                ("Disappointed", "Battery life is terrible, only lasted 2 weeks. Waste of money."),
                ("Stopped working", "Worked fine for a month then just stopped working. Very disappointed."),
                ("Poor quality", "The material feels cheap and flimsy. Not worth the price at all."),
                ("Arrived damaged", "Packaging was torn and the product was scratched. Returning."),
                ("Defective unit", "Received a defective unit. Button was stuck right out of the box."),
                ("Doesn't match description", "Looks nothing like the photos. Size is way smaller than advertised."),
            ]
        elif sentiment_roll < 0.45:
            rating = 3
            templates = [
                ("It's okay", "Does the job but nothing special. Expected better for the price."),
                ("Mixed feelings", "Decent quality but the design could be improved. Average overall."),
                ("Not bad", "Functional but had some minor issues with setup. Works fine now."),
                ("Average product", "Fair quality for the price. Wouldn't buy again though."),
            ]
        else:
            rating = random.randint(4, 5)
            templates = [
                ("Love it!", "Amazing quality, exceeded expectations. Highly recommend to everyone!"),
                ("Great purchase", "Best one I've tried so far. Solid build quality and works perfectly."),
                ("Perfect", "Exactly what I needed. Fast shipping and well packaged. 5 stars!"),
                ("Excellent product", "Using it daily for 3 months now, still like new. Great value."),
                ("Very impressed", "The quality is outstanding. Will definitely buy more from this brand."),
                ("Fantastic", "Better than the expensive alternatives. Glad I chose this one."),
            ]

        title, body = random.choice(templates)
        days_ago = random.randint(1, 120)
        return {
            "platform": "amazon",
            "rating": rating,
            "title": title,
            "body": body,
            "author": f"Customer{random.randint(1000, 9999)}",
            "posted_at": (datetime.now() - timedelta(days=days_ago)).isoformat(),
        }
