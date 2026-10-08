-- ==============================================================================
-- Institutional AI Stock Engine - Supabase Cloud PostgreSQL Schema
-- Zero-Data-Loss Historical Storage for Model Training & Accuracy Improvement
-- ==============================================================================
-- Instructions:
-- 1. Open your Supabase Project Dashboard (https://supabase.com/dashboard)
-- 2. Go to the "SQL Editor" in the left sidebar
-- 3. Paste this entire script and click "Run"
-- ==============================================================================

-- 1. Signals Master Table (Retains 100% of Signal Properties + Raw Metadata)
CREATE TABLE IF NOT EXISTS public.signals (
    id TEXT PRIMARY KEY,
    symbol TEXT NOT NULL,
    company_name TEXT,
    sector TEXT,
    source_type TEXT DEFAULT 'NSE_EXCHANGE_DISCLOSURE',
    headline TEXT NOT NULL,
    news_date TEXT,
    news_time TEXT,
    current_base_price_inr NUMERIC(14, 2) DEFAULT 0.0,
    day_change_pct NUMERIC(6, 2) DEFAULT 0.0,
    day_high NUMERIC(14, 2),
    day_low NUMERIC(14, 2),
    predicted_direction TEXT DEFAULT 'BULLISH',
    conviction_score_pct NUMERIC(5, 2) DEFAULT 75.0,
    materiality_ratio NUMERIC(10, 4) DEFAULT 0.0,
    ai_model TEXT DEFAULT 'JEV_SYSTEM_ONE',
    is_useful BOOLEAN DEFAULT TRUE,
    is_rumor BOOLEAN DEFAULT FALSE,
    t1_target JSONB DEFAULT '{}'::jsonb,
    t5_target JSONB DEFAULT '{}'::jsonb,
    t10_target JSONB DEFAULT '{}'::jsonb,
    recommended_stop_loss TEXT,
    recommended_strategy TEXT DEFAULT 'ACCUMULATE',
    execution_order_type TEXT,
    optimal_entry_price NUMERIC(14, 2),
    kelly_capital_allocation_inr NUMERIC(14, 2) DEFAULT 15000.0,
    tracking_status TEXT DEFAULT 'ACTIVE_MONITORING',
    max_gain_reached_pct NUMERIC(6, 2) DEFAULT 0.0,
    target_hit BOOLEAN DEFAULT FALSE,
    actual_move_pct NUMERIC(6, 2) DEFAULT 0.0,
    retention_policy_days INTEGER DEFAULT 90,
    days_retained NUMERIC(6, 2) DEFAULT 0.0,
    days_remaining NUMERIC(6, 2) DEFAULT 90.0,
    epoch_timestamp NUMERIC(16, 4),
    raw_metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_signals_symbol ON public.signals(symbol);
CREATE INDEX IF NOT EXISTS idx_signals_created_at ON public.signals(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_signals_direction ON public.signals(predicted_direction);
CREATE INDEX IF NOT EXISTS idx_signals_conviction ON public.signals(conviction_score_pct DESC);
CREATE INDEX IF NOT EXISTS idx_signals_target_hit ON public.signals(target_hit);

-- 2. Evaluation Benchmark Runs (Historical Backtests & Blind Evaluation Windows)
CREATE TABLE IF NOT EXISTS public.evaluation_benchmarks (
    run_key TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    badge TEXT,
    period TEXT,
    description TEXT,
    capital NUMERIC(14, 2) DEFAULT 100000.0,
    total_signals INTEGER DEFAULT 0,
    passed_useful INTEGER DEFAULT 0,
    filtered_noise INTEGER DEFAULT 0,
    win_rate_pct NUMERIC(5, 2) DEFAULT 0.0,
    winning_trades INTEGER DEFAULT 0,
    losing_trades INTEGER DEFAULT 0,
    t1_hit_rate_pct NUMERIC(5, 2) DEFAULT 0.0,
    net_pnl_inr NUMERIC(14, 2) DEFAULT 0.0,
    portfolio_roi_pct NUMERIC(6, 2) DEFAULT 0.0,
    signals_json JSONB DEFAULT '[]'::jsonb,
    accuracy_json JSONB DEFAULT '[]'::jsonb,
    trades_json JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Accuracy Audits (Signal-by-Signal Performance & Calibration Verification)
CREATE TABLE IF NOT EXISTS public.accuracy_audits (
    id TEXT PRIMARY KEY,
    run_key TEXT NOT NULL REFERENCES public.evaluation_benchmarks(run_key) ON DELETE CASCADE,
    symbol TEXT NOT NULL,
    headline TEXT NOT NULL,
    sector TEXT,
    predicted_direction TEXT NOT NULL,
    confidence_pct NUMERIC(5, 2) DEFAULT 0.0,
    t1_target_range TEXT,
    actual_t1_move_pct NUMERIC(6, 2) DEFAULT 0.0,
    t1_hit_status TEXT NOT NULL,
    raw_audit JSONB DEFAULT '{}'::jsonb,
    audited_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_accuracy_run_key ON public.accuracy_audits(run_key);
CREATE INDEX IF NOT EXISTS idx_accuracy_symbol ON public.accuracy_audits(symbol);
CREATE INDEX IF NOT EXISTS idx_accuracy_status ON public.accuracy_audits(t1_hit_status);

-- 4. Jev AI Classifications Cache & Telemetry (For Model Training & Zero Credit Waste)
CREATE TABLE IF NOT EXISTS public.jev_classifications (
    cache_hash TEXT PRIMARY KEY,
    headline TEXT NOT NULL,
    company_symbol TEXT,
    sentiment TEXT,
    direction TEXT,
    conviction NUMERIC(5, 2) DEFAULT 0.0,
    reasoning TEXT,
    raw_jev_response JSONB DEFAULT '{}'::jsonb,
    tokens_used INTEGER DEFAULT 0,
    model_name TEXT DEFAULT 'jev-latest',
    cached_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_jev_symbol ON public.jev_classifications(company_symbol);
CREATE INDEX IF NOT EXISTS idx_jev_cached_at ON public.jev_classifications(cached_at DESC);

-- 5. Market Live Price Snapshots (Real-Time Exchange Verifications)
CREATE TABLE IF NOT EXISTS public.market_price_snapshots (
    id TEXT PRIMARY KEY,
    symbol TEXT NOT NULL,
    price NUMERIC(14, 2) NOT NULL,
    day_high NUMERIC(14, 2),
    day_low NUMERIC(14, 2),
    day_change_pct NUMERIC(6, 2),
    volume BIGINT DEFAULT 0,
    verified_source TEXT DEFAULT 'NSE_YFINANCE_HYBRID',
    recorded_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_price_snapshots_symbol ON public.market_price_snapshots(symbol);
CREATE INDEX IF NOT EXISTS idx_price_snapshots_recorded ON public.market_price_snapshots(recorded_at DESC);

-- 6. Sync Logs & Execution Telemetry
CREATE TABLE IF NOT EXISTS public.sync_telemetry_logs (
    id TEXT PRIMARY KEY,
    sync_mode TEXT NOT NULL, -- 'MIDNIGHT_CRON', 'MANUAL_ADMIN', 'INITIAL_BOOT'
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    status TEXT NOT NULL, -- 'SUCCESS', 'PARTIAL_ERROR', 'DRY_RUN'
    signals_synced INTEGER DEFAULT 0,
    benchmarks_synced INTEGER DEFAULT 0,
    accuracy_records_synced INTEGER DEFAULT 0,
    jev_records_synced INTEGER DEFAULT 0,
    prices_synced INTEGER DEFAULT 0,
    total_records_pushed INTEGER DEFAULT 0,
    duration_ms INTEGER DEFAULT 0,
    error_message TEXT,
    details JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_sync_logs_started ON public.sync_telemetry_logs(started_at DESC);

-- 7. Enable Row-Level Security (RLS)
ALTER TABLE public.signals ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.evaluation_benchmarks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.accuracy_audits ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.jev_classifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.market_price_snapshots ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sync_telemetry_logs ENABLE ROW LEVEL SECURITY;

-- 8. Policies for Service Role Full Access (Used by Nightly Cron Job)
CREATE POLICY "Service Role Full Access Signals" ON public.signals
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "Service Role Full Access Benchmarks" ON public.evaluation_benchmarks
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "Service Role Full Access Accuracy" ON public.accuracy_audits
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "Service Role Full Access Jev" ON public.jev_classifications
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "Service Role Full Access Prices" ON public.market_price_snapshots
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "Service Role Full Access Sync Logs" ON public.sync_telemetry_logs
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- 9. Read-Only Policies for Anon / Authenticated Users (If public dashboard connects to Supabase directly)
CREATE POLICY "Public Read Access Signals" ON public.signals
    FOR SELECT TO anon, authenticated USING (true);

CREATE POLICY "Public Read Access Benchmarks" ON public.evaluation_benchmarks
    FOR SELECT TO anon, authenticated USING (true);

CREATE POLICY "Public Read Access Accuracy" ON public.accuracy_audits
    FOR SELECT TO anon, authenticated USING (true);

CREATE POLICY "Public Read Access Prices" ON public.market_price_snapshots
    FOR SELECT TO anon, authenticated USING (true);
