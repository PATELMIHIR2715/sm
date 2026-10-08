-- ==============================================================================
-- Institutional AI Stock Engine - Add Subscribers Table to Supabase Cloud
-- Zero-Data-Loss Persistent Cloud Storage for Alert Subscribers (WhatsApp & Email)
-- ==============================================================================

CREATE TABLE IF NOT EXISTS public.notification_subscribers (
    id TEXT PRIMARY KEY,
    name TEXT DEFAULT 'Institutional Trader',
    whatsapp TEXT,
    email TEXT,
    active BOOLEAN DEFAULT TRUE,
    preferences JSONB DEFAULT '{
        "preCatalystRadar": true,
        "liveSignals": true,
        "doNotChaseAlerts": true,
        "stopLossWarnings": true,
        "dailyBriefing": true,
        "targetHits": true
    }'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_subscribers_whatsapp ON public.notification_subscribers(whatsapp);
CREATE INDEX IF NOT EXISTS idx_subscribers_email ON public.notification_subscribers(email);
CREATE INDEX IF NOT EXISTS idx_subscribers_active ON public.notification_subscribers(active);

-- Enable RLS
ALTER TABLE public.notification_subscribers ENABLE ROW LEVEL SECURITY;

-- Service Role Full Access
CREATE POLICY "Service Role Full Access Subscribers" ON public.notification_subscribers
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- Public Read / Insert Access (Optional for client apps)
CREATE POLICY "Public Read Access Subscribers" ON public.notification_subscribers
    FOR SELECT TO anon, authenticated USING (true);
