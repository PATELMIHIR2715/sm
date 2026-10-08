# Institutional Stock Market News Impact & Microstructure Defense Platform

> **High-Conviction Financial Catalyst Intelligence & Defended 1-Day Price Target (T+1) Engine for Indian Equities (NSE/BSE)**

---

## 🏛️ Platform Architecture Overview

This platform processes corporate announcements, regulatory filings, and government contract awards in real-time. It applies calibrated **TypeSafe AI Jev SystemOne (`jev-1.13.0`)** classification, vector retrieval augmented generation (RAG) against a 10-year historical market events corpus, and 7-scenario microstructure defense modeling to output defended **1-Day Price Targets (T+1 / Tomorrow)** with quantitative Kelly criterion capital sizing.

```
                              ┌────────────────────────────────────────┐
                              │  NSE / BSE / PIB Real-Time Feed Poller │
                              └───────────────────┬────────────────────┘
                                                  │
                                                  ▼
                        ┌─────────────────────────────────────────────────────┐
                        │      4-Stage Credit-Optimized Classification       │
                        │  Stage 1: Local Exchange Noise Gatekeeper (0 Cost)  │
                        │  Stage 2: Persistent SHA-256 Deduplication (0 Cost) │
                        │  Stage 3: Token Compression (40-60% input saved)   │
                        │  Stage 4: TypeSafe AI Jev SystemOne (jev-1.13.0)    │
                        └─────────────────────────┬───────────────────────────┘
                                                  │
                                                  ▼
                         ┌───────────────────────────────────────────────────┐
                         │   Microstructure Defense & Confluence Engine     │
                         │   - Pre-Catalyst Rumor Leakage Detection          │
                         │   - Gap-Up Fade / Trap Mitigation ("DO NOT CHASE")│
                         │   - Nifty Macro Regime Drag Compensation          │
                         │   - High-Frequency Front-Running Protection       │
                         └─────────────────────────┬───────────────────────────┘
                                                  │
                        ┌─────────────────────────┴──────────────────────────┐
                        │                                                    │
                        ▼                                                    ▼
       ┌───────────────────────────────────┐               ┌───────────────────────────────────┐
       │   Automated Multi-Channel Dispatch│               │   Institutional White-Theme UI    │
       │   - WhatsApp Web Headless Gateway │               │   - Vite / React / Tailwind       │
       │   - Gmail SMTP HTML Briefings     │               │   - Defended 1-Day Target Corridors│
       │   - Cryptographic Admin Console   │               │   - Rolling 90-Day Retention DB   │
       └───────────────────────────────────┘               └───────────────────────────────────┘
```

---

## 🚀 Key Features

1. **Defended 1-Day Price Targets (T+1)**: High-conviction next-session corridors calibrated by historical beta, daily ATR, and event materiality ratio.
2. **TypeSafe AI Jev SystemOne Engine**: Structured probabilistic classification (`BULLISH`, `BEARISH`, `NEUTRAL`) with domain-calibrated materiality scores and zero-downtime fallback.
3. **4-Stage Credit Optimization**: Pre-filters ~75% of routine compliance filings locally at ₹0 cost, deduplicates polled headlines, and compresses token payloads.
4. **Hardened Administrator Console**:
   - Zero public discovery (no navbar buttons or public markers).
   - Cryptographic constant-time authentication (`timingSafeEqual` / `compare_digest`).
   - Rate-limiting brute-force guard (5 failed attempts = 15-minute lockout).
   - Inactivity auto-lockout (15 minutes).
5. **Rolling 90-Day Retention Store**: Retains all processed signals with automated archival pruning and audit verification.
6. **Multi-Channel Alert Hub**: Instant WhatsApp and responsive HTML email dispatch.

---

## 🛠️ Quick Start & Setup

### 1. Prerequisites
- **Python**: 3.10+
- **Node.js**: 18+
- **npm**: 9+

### 2. Environment Configuration
Copy `.env.example` to `.env` and fill in your credentials:
```bash
cp .env.example .env
```

Key environment parameters:
```env
# Gmail SMTP
SMTP_HOST="smtp.gmail.com"
SMTP_PORT=465
SMTP_USER="your-email@gmail.com"
SMTP_PASS="your-google-app-password"
SMTP_FROM="Institutional AI News Engine <your-email@gmail.com>"

# Security
ADMIN_SECRET_KEY="your-admin-secret"

# TypeSafe AI Jev
JEV_API_KEY="your-typesafe-jev-key"
JEV_API_URL="https://api.typesafe.ai/v1/systemone"
JEV_MODEL="jev-latest"
```

### 3. Install Dependencies
```bash
# Frontend
cd apps/dashboard
npm install
cd ../..

# Notifications Hub
cd services/notifications
npm install
cd ../..

# Python Pipeline
pip install -r requirements.txt # or install requests, yfinance, numpy
```

### 4. Running the Platform Services

Start the 4 platform services:

```bash
# 1. Frontend Dashboard (Port 5173)
cd apps/dashboard && npm run dev -- --port 5173 --host

# 2. Live Sync API Server (Port 5000)
python services/api/live_sync_server.py 5000

# 3. Notification & Admin Hub (Port 5001)
node services/notifications/server.js

# 4. Auto Stream Daemon (Background Ingestion)
python services/ingestion/auto_live_stream_worker.py --daemon
```

---

## 🔒 Security Architecture

- **Public Isolation**: The administrative console has zero buttons or traces on public screens.
- **Access Route**: Press `Ctrl + Shift + A` (or `Cmd + Shift + A` on macOS) or navigate to `/#admin`.
- **Constant-Time Verification**: Uses `crypto.timingSafeEqual` in Node and `hmac.compare_digest` in Python.
- **Git Hygiene**: All `.env` files, WhatsApp pairing session tokens, and local cache databases are strictly excluded via `.gitignore`.

---

## 📄 License

Proprietary Institutional Trading Software. All rights reserved.
