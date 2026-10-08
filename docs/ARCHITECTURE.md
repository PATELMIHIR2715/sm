# System Architecture & Technical Specifications

## 1. Overview
The Stock Market News Impact Platform is a high-accuracy, zero-drop AI-augmented intelligence engine for the Nifty 500 universe. It ingests exchange announcements, bulk/block deals, government press releases, and news, maps them to historical macro regimes (2015–2025), and outputs calibrated directional signals + conservative price impact ranges.

---

## 2. Pipeline Stages & Microstructure Defense Stack

```
   Raw Event (NSE / US FDA / PIB / F&O Derivatives Feed)
                          │
                          ▼
           [1. Ingestion & News Deduplication]
       (Sha256 hash check, source type validation)
                          │
                          ▼
        [2. Company Intelligence Provider (NSE/Disk)]
       (Live Market Cap, Topline Revenue, 14D ATR, 50/200 EMA)
                          │
                          ▼
       [3. Microstructure Defense Engine (NEW)]
       ├── A. Annualized Run-Rate Materiality (Value / [Tenor × Revenue])
       ├── B. Scheduled Calendar Conflict Filter (Auto Sales Day 60% discount)
       ├── C. Sector P/E Valuation Multiplier (Sector P/E vs 5-Yr Median)
       ├── D. Pre-Market Gap Fading (Transforms to Limit on VWAP Pullback)
       ├── E. F&O Call OI Resistance Wall Clamping (0.2% below Round Strikes)
       └── F. Multi-Factor Beta Drag ((Beta_nifty × ΔNifty) + (Beta_sec × ΔSec))
                          │
                          ▼
        [4. 10-Year Historical Macro RAG Engine]
      (Pgvector HNSW / Scaled Archetype similarity)
                          │
                          ▼
         [5. Dynamic Kelly Capital Position Sizer]
      (f* = (p*b - q)/b with 25% max portfolio cap)
                          │
                          ▼
         [6. Real-time Live Sync API & Dashboard]
      (FastAPI / Python live feed + React / Tailwind UI)
```

---

## 3. Core Engine Components

1. **[`MicrostructureDefenseEngine`](file:///d:/sm/services/ai_pipeline/microstructure_defense_engine.py):**
   - Eliminates single-day target overshooting by converting gross multi-year contracts to annualized run-rate ratios.
   - Adjusts for sector overvaluation / undervaluation using 5-year historical median P/E multiples.
   - Clamps upper target corridors below massive Call Open Interest round strikes to avoid options barrier misses.
   - Intercepts pre-market opening gaps and converts aggressive market buys into disciplined VWAP pullback limit entries.
   - Quarantines unverified social media leaks into Rumor Quarantine with ₹0 capital allocated.

2. **[`CompanyIntelligenceProvider`](file:///d:/sm/services/market_data/company_intelligence_provider.py):**
   - High-speed on-demand caching of company fundamentals (Market Cap, Revenue, Margins, True ATR, Sector Median P/E) in `data/company_profiles/` with 6-Hour TTL.

3. **[`LivePriceProvider`](file:///d:/sm/services/market_data/live_price_provider.py):**
   - Direct real-time quotes, OHLC daily bars, sector breadth, and NIFTY 50 systemic drag.

4. **[`KellyPositionSizer`](file:///d:/sm/services/ai_pipeline/kelly_position_sizer.py):**
   - Fractional Kelly criterion sizing for optimal risk management.

---

## 4. Hardware & Local Inference Strategy (16GB RAM, CPU-Only)
- **Local LLM Engine:** Ollama (`qwen2.5:3b-instruct-q4_K_M` or `llama3.2:3b-instruct-q4_K_M`).
- **Embedding Model:** `bge-small-en-v1.5` (384-dimensional vector, fast CPU inference via ONNX).
- **Vector DB:** PostgreSQL 16 with `pgvector` extension and HNSW indexing (`m=16, ef_construction=64`).
- **Disk Cache:** Fast JSON profile cache (`data/company_profiles/`) with automatic cache invalidation.

---

## 5. Comprehensive Failure Analysis & Evolution
For detailed documentation on what hypotheses were tested, what failed and why, and what solutions worked, refer to:
👉 [`docs/EXPERIMENTATION_AND_FAILURE_ANALYSIS.md`](file:///d:/sm/docs/EXPERIMENTATION_AND_FAILURE_ANALYSIS.md)

