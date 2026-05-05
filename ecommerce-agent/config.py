"""Configuration constants for the Marketing AI Agent system."""

import os

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "marketing_agent.db")
IMAGE_DIR = os.path.join(os.path.dirname(__file__), "data", "generated_images")

MARKETS = {
    "US": {"currency": "USD", "vat": 0.0, "locale": "en-US"},
    "DE": {"currency": "EUR", "vat": 0.19, "locale": "de-DE"},
    "JP": {"currency": "JPY", "vat": 0.10, "locale": "ja-JP"},
    "UK": {"currency": "GBP", "vat": 0.20, "locale": "en-GB"},
}

PRICE_GAP_THRESHOLDS = {
    "undercut": -0.10,
    "parity_low": -0.10,
    "parity_high": 0.10,
    "premium": 0.10,
}

PRICING_WEIGHTS = {
    "margin": 0.55,
    "conversion": 0.45,
}

MOCK_PRODUCTS = [
    {
        "asin": "B07XK8QNX9",
        "title": "Precision Digital Coffee Scale with Timer",
        "category": "Kitchen & Dining",
        "brand": "BrewMaster Pro",
        "price": 39.99,
        "cost": 22.50,
        "ad_budget_daily": 25.0,
        "current_bid": 0.45,
        "target_acos": 0.28,
        "market": "US",
    },
    {
        "asin": "B08N5KWB2M",
        "title": "LED Desk Lamp with Wireless Charger, 5 Modes",
        "category": "Office Products",
        "brand": "LumiDesk",
        "price": 49.99,
        "cost": 28.00,
        "ad_budget_daily": 35.0,
        "current_bid": 0.55,
        "target_acos": 0.25,
        "market": "US",
    },
    {
        "asin": "B09G9FPNWK",
        "title": "Eco-Friendly Non-Slip Yoga Mat 6mm",
        "category": "Sports & Outdoors",
        "brand": "ZenFlow",
        "price": 34.99,
        "cost": 15.00,
        "ad_budget_daily": 20.0,
        "current_bid": 0.35,
        "target_acos": 0.30,
        "market": "DE",
    },
    {
        "asin": "B0BXQKJ5LR",
        "title": "Bluetooth 5.3 Earbuds with ANC, 40h Playtime",
        "category": "Electronics",
        "brand": "SoundPulse",
        "price": 59.99,
        "cost": 32.00,
        "ad_budget_daily": 50.0,
        "current_bid": 0.65,
        "target_acos": 0.22,
        "market": "US",
    },
    {
        "asin": "B0C5TMWR8V",
        "title": "Organic Bamboo Cutting Board Set 3-Piece",
        "category": "Kitchen & Dining",
        "brand": "EcoHome",
        "price": 29.99,
        "cost": 13.50,
        "ad_budget_daily": 15.0,
        "current_bid": 0.30,
        "target_acos": 0.30,
        "market": "UK",
    },
]

COMPETITOR_NAMES = ["MarketLeader", "ValueDeal", "PremiumPicks", "GlobalGoods"]
