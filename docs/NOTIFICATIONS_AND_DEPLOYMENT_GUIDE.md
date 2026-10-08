# Institutional Stock News Impact Engine — Production & Notification Deployment Guide

This guide details the multi-channel notification infrastructure, real-time live ingestion worker, and production deployment configuration.

---

## 1. System Architecture Overview

```
                      REAL-TIME MARKET INGESTION FEEDS
      ┌────────────────────────┬─────────────────────────┬──────────────────────┐
      │  NSE Corporate Feed    │ GeM / CPPP Tender Wins  │ US FDA Approvals /   │
      │  & Bulk Deals          │ & PIB Cabinet Orders    │ PIT Insider Actions  │
      └───────────┬────────────┴────────────┬────────────┴──────────┬───────────┘
                  │                         │                       │
                  ▼                         ▼                       ▼
┌───────────────────────────────────────────────────────────────────────────────┐
│        Automated Live Ingestion Worker (`services/ingestion/auto_live_stream_worker.py`)│
│        - Polls 5 real-time streams every 30 seconds with SHA256 deduplication │
│        - Runs Calibrated NLP, Materiality Assessment & Microstructure Defenses│
│        - Fetches genuine live ticks from NSE / Yahoo Finance Tick API         │
└──────────────────────────────────────┬────────────────────────────────────────┘
                                       │
                        Triggers High-Conviction Broadcast
                                       │
                                       ▼
┌───────────────────────────────────────────────────────────────────────────────┐
│           Multi-Channel Notification Hub (`services/notifications/server.js`)  │
│                                Port: 5001                                     │
│  ┌───────────────────────────────────┐    ┌─────────────────────────────────┐ │
│  │     WhatsApp-Web.js Gateway       │    │    Nodemailer HTML Gateway      │ │
│  │  - Free open-source WhatsApp API  │    │  - Verified Gmail SMTP (Port 465)│ │
│  │  - Headless Chromium session      │    │  - Responsive TradingView dark  │ │
│  │  - Persistent LocalAuth storage   │    │    HTML alert template          │ │
│  │  - QR code pairing in web UI      │    │  - Multi-horizon target cards   │ │
│  └───────────────────────────────────┘    └─────────────────────────────────┘ │
└──────────────────────────────────────┬────────────────────────────────────────┘
                                       │
                      Dispatches Instant Mobile Alerts to
                                       │
                  ┌────────────────────┴────────────────────┐
                  ▼                                         ▼
         📱 WhatsApp Alert                         📧 Rich HTML Email
    • Entry Corridor & Stop Loss               • Target T+1 / T+5 / T+10
    • Catalyst Absorption %                    • Kelly Capital Allocation
    • Smart Money Footprint                    • Microstructure Defense
```

---

## 2. Notification Hub Configuration

### A. Environment Variables (`.env`)

```env
# Gmail SMTP Credentials (Configured & Verified)
SMTP_HOST="smtp.gmail.com"
SMTP_PORT=465
SMTP_USER="mihirpqtel@gmail.com"
SMTP_PASS="qbjh xpul mqyt jjnm"
SMTP_FROM="Institutional AI News Engine <mihirpqtel@gmail.com>"
ALERT_EMAIL_RECIPIENTS="mihirpqtel@gmail.com"

# Notification Hub Port
NOTIFICATION_PORT=5001

# Primary WhatsApp Subscriber Mobile Numbers
ALERT_WHATSAPP_NUMBERS="+919876543210"

# Live Sync Port
LIVE_SYNC_PORT=5000
```

### B. Tested & Verified Endpoints

| Endpoint | Method | Purpose | Test Status |
| :--- | :--- | :--- | :--- |
| `http://127.0.0.1:5001/api/notifications/status` | `GET` | Health check, WhatsApp session state, SMTP verification | ✅ `READY_VERIFIED` |
| `http://127.0.0.1:5001/api/notifications/qr` | `GET` | Returns WhatsApp Web QR code as base64 PNG for UI | ✅ `QR_READY` |
| `http://127.0.0.1:5001/api/notifications/test-email` | `POST` | Dispatches live test email via Gmail SMTP to `mihirpqtel@gmail.com` | ✅ Delivered |
| `http://127.0.0.1:5001/api/notifications/test-whatsapp` | `POST` | Dispatches formatted trade alert to WhatsApp gateway | ✅ Active |
| `http://127.0.0.1:5001/api/notifications/broadcast-signal` | `POST` | Broadcasts full signal payload across WhatsApp + Email | ✅ Multi-Channel Active |
| `http://127.0.0.1:5001/api/notifications/history` | `GET` | Returns audit trail of recent dispatched alerts | ✅ Persisted in JSON |

---

## 3. How to Pair WhatsApp Web for Free Mobile Delivery

1. Open the Dashboard at **`http://localhost:5173/`**.
2. Click **`Alerts (WA & Mail)`** in the top navigation bar.
3. Under the **WhatsApp Web Gateway** card:
   - If not yet paired, a live QR code is displayed directly inside the modal.
   - Open **WhatsApp** on your mobile phone &gt; tap **Settings / Three Dots** &gt; **Linked Devices** &gt; **Link a Device**.
   - Point your phone camera at the QR code.
4. Once scanned, the status instantly flips to **`CONNECTED_READY`**.
5. Sessions are permanently persisted in `services/notifications/.wwebjs_auth`, so pairing only needs to be done once!

---

## 4. Real-Time Live Ingestion & Automated Streaming

The system runs an active background worker that continuously monitors breaking market announcements:

- **Worker Script:** `services/ingestion/auto_live_stream_worker.py`
- **Polling Frequency:** Every 30 seconds.
- **Deduplication:** SHA256 content hashes in `data/seen_filing_hashes.json`.
- **Auto-Broadcast Rule:** Whenever a signal with **Conviction $\ge 70\%$** and non-rumor status is processed, it automatically calls the notification hub to broadcast instant WhatsApp and Email alerts.
- **REST Feed:** `GET http://127.0.0.1:5000/api/live-stream`

---

## 5. Production Service Management

All 4 microservices run independently and recover gracefully:

| Service | Technology | Port / Role | Start Command |
| :--- | :--- | :--- | :--- |
| **Notification Hub** | Node.js / Express | Port 5001 | `node services/notifications/server.js` |
| **Live Sync API** | Python HTTP Server | Port 5000 | `python services/api/live_sync_server.py 5000` |
| **Auto-Stream Worker** | Python Poller | Background Daemon | `python services/ingestion/auto_live_stream_worker.py --daemon` |
| **Trading Dashboard** | React / Vite / Tailwind | Port 5173 | `npm run dev -- --port 5173 --host` (in `apps/dashboard`) |

---

## 6. Dynamic User Subscription & Platform Onboarding

Users arriving on the trading platform can subscribe their WhatsApp number and Email directly:

1. **Onboarding Banner (`LiveAlertSubscriptionBanner.tsx`):**
   - Displayed prominently at the top of the dashboard.
   - Users enter their **WhatsApp Number** (auto-normalizes to `+91` standard) and **Email Address**.
   - Clicking **"Subscribe"** persists their profile into `data/notification_subscribers.json` and optionally triggers an instant welcome alert to both devices.
   - Clicking **"Test"** dispatches immediate test signals so users verify delivery instantly.

2. **Endpoints for Subscriber Management:**
   - `POST /api/notifications/subscribe`: Adds or updates a subscriber profile with granular preference toggles.
   - `GET /api/notifications/subscribers`: Lists all active registered subscribers.
   - `POST /api/notifications/unsubscribe`: Deactivates a subscriber profile.

---

## 7. Jev AI Model Classifier Architecture

Jev is integrated as the primary AI classification engine for Indian equity corporate announcements:

1. **Jev Classifier Adapter (`services/ai_pipeline/jev_classifier.py`):**
   - Configurable via `.env`, `data/jev_config.json`, or the Dashboard UI settings tab.
   - **Zero-Downtime Fallback:** If `JEV_API_KEY` is not yet provided, the engine runs seamlessly on our local calibrated institutional NLP ensemble (`CalibratedSentimentScorer`), tagging all predictions as `CALIBRATED_FALLBACK_ENSEMBLE (Ready for Jev API Key)`.
   - **Dynamic Key Activation:** When the user enters their `JEV_API_KEY`, live announcements are immediately routed to the Jev model API with zero service restart required.

2. **Endpoints for Jev Configuration & Testing:**
   - `GET http://127.0.0.1:5000/api/settings/jev-model`: Returns Jev connection status, masked key, and active mode.
   - `POST http://127.0.0.1:5000/api/settings/jev-model`: Updates and persists `JEV_API_KEY` and model parameters.
   - `POST http://127.0.0.1:5000/api/settings/jev-model/test`: Tests the key with a benchmark Indian corporate announcement and outputs live direction, conviction %, materiality ratio, and latency.

---

## 8. Dedicated Institutional Admin Panel

Administrators can manage the entire platform from a central management console:

1. **How to Access:**
   - Click the **"Admin Panel"** button in the dashboard top navigation bar (or press keyboard shortcut `A` / navigate to `/#admin`).
   - Click **"Return to Terminal"** to switch back to the trader terminal.

2. **Core Capabilities Managed from the Admin Panel:**
   - **Subscribers Hub:** View all registered users, add new subscribers manually, toggle active/paused status (`POST /subscribers/:id/toggle`), permanently delete subscribers (`DELETE /subscribers/:id`), and send one-click test pings (`POST /subscribers/:id/test`).
   - **Gateways & SMTP Control:**
     - WhatsApp Web.js gateway live status, authenticated number, QR code viewer, and restart trigger (`POST /restart-whatsapp`).
     - Dynamic Gmail SMTP credentials editor (`POST /smtp-config`) allowing updates to `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, and `SMTP_FROM` with instant transport re-verification without server restarts.
     - Direct test email dispatch tester (`POST /test-email`).
   - **Jev AI Model Center:** Inspect status, update Jev API Key, and run live connection handshake diagnostics (`POST /settings/jev-model/test`).
   - **Live Broadcast Center:** Compose custom or emergency signals, quick-load parameters from today's live signals, select delivery channels (WhatsApp, Email, or Both), preview the rendered alert in real time, and blast to all active subscribers with 1 click (`POST /broadcast-signal`).
   - **Exchange Ingestion & Pipeline:** Inspect daemon status, filing counts, Nifty drag beta, and trigger manual exchange polling immediately (`POST /api/pipeline/poll-now`).
   - **Audit Trail & History:** Chronological log of all sent alerts with channel, recipient, timestamp, and status. Clear logs button (`POST /history/clear`).

