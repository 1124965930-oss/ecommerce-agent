"""SQLite database schema for the Marketing AI Agent system."""

SCHEMA = """

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asin TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    category TEXT,
    brand TEXT DEFAULT 'OurBrand',
    platform TEXT DEFAULT 'amazon',
    market TEXT DEFAULT 'US',
    our_price REAL NOT NULL,
    cost REAL NOT NULL,
    ad_budget_daily REAL DEFAULT 0,
    current_bid REAL DEFAULT 0,
    target_acos REAL DEFAULT 0.30,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS competitor_listings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL REFERENCES products(id),
    competitor_name TEXT NOT NULL,
    competitor_asin TEXT,
    price REAL,
    rating REAL,
    review_count INTEGER DEFAULT 0,
    stock_status TEXT DEFAULT 'in_stock',
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL REFERENCES products(id),
    platform TEXT DEFAULT 'amazon',
    rating INTEGER CHECK(rating BETWEEN 1 AND 5),
    title TEXT,
    body TEXT NOT NULL,
    author TEXT,
    sentiment_score REAL,
    sentiment_label TEXT,
    key_issues TEXT,
    responded BOOLEAN DEFAULT 0,
    suggested_reply TEXT,
    posted_at TIMESTAMP,
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS generated_content (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL REFERENCES products(id),
    content_type TEXT NOT NULL,
    variant_name TEXT,
    content_text TEXT,
    image_path TEXT,
    trigger_reason TEXT DEFAULT 'scheduled',
    status TEXT DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pricing_decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL REFERENCES products(id),
    old_price REAL,
    new_price REAL NOT NULL,
    old_bid REAL,
    new_bid REAL,
    reasoning TEXT NOT NULL,
    margin_impact_pct REAL,
    conversion_estimate_delta REAL,
    applied BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS strategy_insights (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER REFERENCES products(id),
    insight_type TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    severity TEXT DEFAULT 'medium',
    actionable BOOLEAN DEFAULT 1,
    acted_upon BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS agent_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_name TEXT NOT NULL,
    status TEXT NOT NULL,
    input_summary TEXT,
    output_summary TEXT,
    duration_ms INTEGER,
    error TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_competitor_product ON competitor_listings(product_id);
CREATE INDEX IF NOT EXISTS idx_reviews_product ON reviews(product_id);
CREATE INDEX IF NOT EXISTS idx_reviews_sentiment ON reviews(sentiment_label);
CREATE INDEX IF NOT EXISTS idx_content_product ON generated_content(product_id);
CREATE INDEX IF NOT EXISTS idx_pricing_product ON pricing_decisions(product_id);
CREATE INDEX IF NOT EXISTS idx_insights_product ON strategy_insights(product_id);
"""
