-- Enable vector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Companies Table (Nifty 500 Master Registry)
CREATE TABLE IF NOT EXISTS companies (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) UNIQUE NOT NULL,
    bse_code VARCHAR(20),
    isin VARCHAR(20) UNIQUE NOT NULL,
    company_name VARCHAR(255) NOT NULL,
    sector VARCHAR(100) NOT NULL,
    industry VARCHAR(100),
    market_cap_cr NUMERIC(12, 2),
    annual_revenue_cr NUMERIC(12, 2),
    atr_percentage NUMERIC(5, 2) DEFAULT 2.50, -- Historical Average True Range %
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_companies_symbol ON companies(symbol);
CREATE INDEX IF NOT EXISTS idx_companies_sector ON companies(sector);

-- Raw Events & Announcements Table
CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    event_uuid VARCHAR(64) UNIQUE NOT NULL, -- SHA256 canonical hash
    source_type VARCHAR(50) NOT NULL, -- NSE_FILING, PIT_INSIDER, BULK_DEAL, PIB, GEM_TENDER, NEWS, BROKER_REPORT
    source_tier INT NOT NULL CHECK (source_tier BETWEEN 1 AND 4),
    headline TEXT NOT NULL,
    body_text TEXT,
    source_url TEXT,
    company_id INT REFERENCES companies(id) ON DELETE SET NULL,
    raw_payload JSONB,
    published_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_events_company_id ON events(company_id);
CREATE INDEX IF NOT EXISTS idx_events_published_at ON events(published_at DESC);
CREATE INDEX IF NOT EXISTS idx_events_source_type ON events(source_type);

-- Bulk, Block & Insider Trading Deals Table
CREATE TABLE IF NOT EXISTS bulk_insider_deals (
    id SERIAL PRIMARY KEY,
    company_id INT REFERENCES companies(id) ON DELETE CASCADE,
    deal_type VARCHAR(30) NOT NULL, -- BULK_BUY, BULK_SELL, BLOCK_DEAL, PROMOTER_BUY, PROMOTER_PLEDGE
    client_name VARCHAR(255) NOT NULL,
    quantity BIGINT NOT NULL,
    traded_price NUMERIC(12, 2),
    total_value_cr NUMERIC(12, 2),
    deal_date DATE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_deals_company_date ON bulk_insider_deals(company_id, deal_date DESC);

-- Historical Patterns Vector Table (10-Year Macro RAG Dataset)
CREATE TABLE IF NOT EXISTS historical_patterns (
    id SERIAL PRIMARY KEY,
    pattern_uuid VARCHAR(64) UNIQUE NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    sector VARCHAR(100) NOT NULL,
    macro_regime VARCHAR(100) NOT NULL, -- COVID_PANDEMIC, RUSSIA_UKRAINE_WAR, RATE_HIKE_CYCLE, PLI_SCHEME, DEMONETIZATION, REGULAR
    event_type VARCHAR(50) NOT NULL, -- ORDER_WIN, EARNINGS_BEAT, RATING_UPGRADE, PROMOTER_BUYING, PENALTY
    actual_direction VARCHAR(10) NOT NULL CHECK (actual_direction IN ('BULLISH', 'BEARISH', 'NEUTRAL')),
    actual_move_pct NUMERIC(5, 2) NOT NULL, -- Actual percentage move in N days
    embedding vector(384), -- bge-small-en-v1.5 embedding size (384 dimensions)
    event_date DATE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- HNSW Vector Index for sub-10ms Cosine Similarity Search
CREATE INDEX IF NOT EXISTS idx_historical_patterns_embedding 
ON historical_patterns USING hnsw (embedding vector_cosine_ops) 
WITH (m = 16, ef_construction = 64);

-- Signal Alerts & Predictions Log
CREATE TABLE IF NOT EXISTS signals (
    id SERIAL PRIMARY KEY,
    event_id INT REFERENCES events(id) ON DELETE CASCADE,
    company_id INT REFERENCES companies(id) ON DELETE CASCADE,
    direction VARCHAR(10) NOT NULL CHECK (direction IN ('BULLISH', 'BEARISH', 'NEUTRAL')),
    direction_confidence NUMERIC(5, 2) NOT NULL, -- 0.00 to 100.00%
    magnitude_min_pct NUMERIC(5, 2), -- Floored conservative lower bound
    magnitude_max_pct NUMERIC(5, 2), -- Conservative upper bound
    materiality_ratio NUMERIC(8, 4), -- Event Value / Annual Revenue
    historical_matches JSONB, -- Retracted top-3 pgvector historical pattern details
    is_rumor BOOLEAN DEFAULT FALSE,
    is_published BOOLEAN DEFAULT FALSE,
    actual_outcome_pct NUMERIC(5, 2), -- Filled post-event for calibration tracking
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_signals_company_created ON signals(company_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_signals_is_rumor ON signals(is_rumor);
