# Stock Market News Impact Platform — Full Project Plan

> Purpose of this document: complete reference for building this project — for Mihir, and for any AI tool (Claude Code, Codex, etc.) picking up implementation work. Contains everything decided during planning. If anything needed for implementation is not covered here, ask before proceeding rather than assuming.

---

## 1. Project Overview

A platform that watches live-published news, government/exchange data, and filings, and identifies:
- Whether an event could impact a listed company's stock price
- Which specific stock(s) are affected
- Whether the likely impact is positive or negative
- How confident the system is, and (when confidence is high enough) a historical-pattern-based impact range — never a single confident price-move number

Example use case: government announces a ₹3000cr defence order → system identifies which company received it → estimates how significant this is for that specific company (relative to its size) → notifies relevant users with direction + confidence + historical context.

**Core design philosophy:** accuracy and honesty over speed or confident-sounding but wrong predictions. The system must be comfortable saying "not confident enough to call this" rather than guessing. A stated predicted range should be conservative — better to under-promise (e.g. say 2–5% when the real move is 8%) than over-promise (say 10% when it only moves 2%). Never call direction wrong if avoidable — abstaining is always preferable to a confident wrong call.

---

## 2. Problem Being Solved

Retail investors:
- Don't have time to read every news item and judge its market relevance
- Get flooded with irrelevant alerts from generic "all news" tools
- Rely on GMP/hype and social media tips rather than verified structured data (IPO context, general trading context)
- Have no way to verify whether a stock tip/rumor is legitimate before acting
- Get no personalized, portfolio-specific signal — most tools broadcast the same firehose to everyone

---

## 3. Competitive Landscape (why this is worth building, and where gaps are)

Existing tools researched:
- **newstockai** — real-time AI news-to-signal engine for intraday/F&O traders. Scans headlines + corporate filings, pushes Telegram alerts, claims high accuracy %. English-only, Telegram/web only, not personalized to individual holdings, no public verifiable track record, marketing-style accuracy claims without visible methodology.
- **YouStockAI** — impact-scored news + "causal chains" historical pattern-matching (honest approach: shows % of similar past setups that moved a certain way, not a fake confident number). General stock-intelligence tool, not built around real-time alerting.
- **Sensibull** — has an "Event Analysis" feature predicting how earnings/elections/budget events might move options prices.
- **Trendlyne** — real-time AI alerts on volume shocks and major corporate actions.

**Gaps none of them cover, which this platform should fill:**
1. Portfolio/watchlist-based **notification** filtering (analysis still runs on all stocks — see Section 13)
2. Government/exchange **structured data sources** (PIB releases, GeM/e-tender awards, NSE/BSE filings) prioritized over generic news scraping — more verifiable, lower noise, and directly matches real use cases like tender/order announcements
3. **Small/mid-cap focus** — the same event that's irrelevant to a large-cap can be transformative for a small-cap; existing tools don't specifically emphasize this
4. **Regional language delivery** — all existing tools found are English/Telegram-only
5. **Public, verifiable track record** — log every past signal and its actual outcome, visible to anyone, instead of an unverifiable "87% accuracy" badge
6. **Risk-protection framing** — alerting on negative news for stocks a user already holds, not just "find new opportunities"
7. **Dynamic, reputation-based source weighting** with escalation as bigger sources corroborate a story (see Section 11) — not found in any competitor researched
8. **Dedicated Rumors feed** — separating unconfirmed/low-confidence items from the main confirmed feed, rather than either suppressing them entirely or mixing them in

---

## 4. What This System Architecturally Is

Clarified during planning — important framing for implementation:

- This is **not a pure "agent"** — the pipeline is a fixed sequence (ingest → filter → classify → resolve entity → retrieve historical pattern → score confidence → notify), not an LLM autonomously deciding its own steps. Agentic decision-making (e.g. "this is ambiguous, let me search for more corroboration before deciding") is a valid **future enhancement**, not part of the MVP.
- It **does use RAG** (Retrieval-Augmented Generation) specifically for the historical pattern-matching feature: embed the incoming event → similarity search in a vector store for past similar events → feed matched results to an LLM to generate the pattern summary.
- Most accurate description: an **AI-augmented data pipeline** — a traditional backend pipeline where specific steps use an LLM for tasks hard to hand-code (classification, entity extraction, summarization), plus one RAG component for pattern-matching. This is normal, common architecture — not everything needs to be "agentic" to be useful.
- **Embeddings vs vectorization terminology:** "embedding" is the correct term — a vector representing text meaning, generated by an embedding model, used specifically for the historical pattern-matching feature. Not used for entity resolution, direction classification, or portfolio filtering (those don't need it — direct LLM calls or plain DB queries handle those).

---

## 5. Full Feature List

### Core Engine
- Real-time ingestion from structured, verifiable sources first (exchange filings, PIB releases, GeM/e-tender data), general news APIs as supplement
- Entity resolution: correctly identify which listed company a news item refers to
- Direction classification: positive/negative/neutral
- Historical pattern-matching via RAG (not a fake confident %)
- Impact-magnitude weighting relative to company size (event value ÷ company revenue/market cap)

### Personalization
- Portfolio/watchlist-based **notification delivery** filtering (analysis itself runs on all stocks — see Section 13)
- Risk-protection alerts for negative news on stocks a user already holds

### Trust & Delivery
- Public, verifiable track record of past signals and actual outcomes
- Regional language support (text + voice) — Hindi/Gujarati first, others later
- Multi-channel delivery — WhatsApp + web app push (not just Telegram)
- Full source traceability on every alert (link to actual filing/release/tender record)
- **Dedicated Rumors feed** for unconfirmed/low-confidence items (see Section 14)

### Compliance
- Explicit "data intelligence, not investment advice" framing throughout — avoid definitive buy/sell language, matching how non-advisory data platforms operate under SEBI's advisory-registration rules
- Only ever present direction + confidence + historical range — never a single confident price-move prediction

---

## 6. Signal Analysis Parameters (what decides direction & magnitude)

All of these should feed into the scoring/confidence system:

1. **Event type/category** — order wins, capacity expansion, product launches, positive earnings surprises generally bullish; lawsuits, regulatory penalties, auditor resignation, executive exits, missed earnings, debt downgrades generally bearish. Some types (mergers) are ambiguous by type alone and need more context.
2. **Magnitude relative to company size** — event value ÷ company's revenue or market cap, not the raw number. Most important single calculation for the small-cap-focus differentiator.
3. **Historical pattern for similar past events** (the RAG piece) — how did this company/sector react to comparable news before. Must also filter historical matches by **similar macro regime** at the time (see #8), not just event-type similarity.
4. **Sentiment/language strength in the source** — definitive ("has received an order") vs speculative ("in talks for") language should weight differently.
5. **Source reliability** — see Section 11 for full tiering/reputation system.
6. **Existing market expectation** — a rumored-for-months event has less "surprise" and likely smaller price reaction than a genuine surprise. Hard to model well without analyst-estimate data; acceptable known limitation for MVP, not something to force-solve early.
7. **Broader market/sector conditions that day** — same news lands differently in a bullish vs bearish market day.
8. **Macro/regime context** — overall market trend (bull/bear/sideways), global risk events (war, pandemic, major central bank moves), crude oil price (important for import/export-heavy sectors), USD/INR rate, FII/DII flow trends. Acts as a multiplier/dampener on all other signals.
9. **Stock's own volatility profile** — scale predicted range to each stock's historical volatility (ATR/std dev) rather than using one generic range for every stock.
10. **Liquidity/free float** — thinly-traded small-caps can move dramatically on modest news simply due to low float; affects how wide the predicted range should be.
11. **Sector/peer correlation** — check if peers are moving together (sector-wide sentiment) vs an isolated company-specific move; affects confidence, since a peer-driven move is a different kind of signal.
12. **Insider/promoter activity and bulk deals** — recent promoter buying/pledging changes or large bulk/block deals around the same time as news add or subtract conviction.
13. **F&O positioning** — unusual open-interest buildup or put-call ratio shifts. Genuinely useful in Indian markets but a **later-stage addition**, not MVP.

---

## 7. Accuracy-First Design Principles

Non-negotiable design rules given the stated priority on accuracy over speed:

- **Split direction confidence from magnitude confidence** as two separate scores — don't force a magnitude estimate whenever direction is confident, and vice versa.
- **Minimum confidence threshold to output anything directional at all.** Below threshold → output "mixed signals — monitor," not a guess. This is the single biggest lever for avoiding overconfident wrong calls.
- **Always round predicted ranges down/inward, never up** (e.g. if raw model estimate says 5–9% up, report 2–5% up). A narrower stated range the market exceeds feels like a win; an overstated range that falls short feels broken.
- **Backtest against 3–5 years of historical news + price data** before trusting any output in production — measure both direction accuracy and how often actual moves fall inside the predicted range.
- **Track calibration continuously** — if the system says "70% confidence" 100 times, roughly 70 of those should actually be correct. This is the honest metric to optimize for, distinct from raw accuracy, and is what separates this from competitors' unverifiable accuracy claims.

---

## 8. Source Reliability & Dynamic Weighting System

- **Tier 1 (near-certain):** Exchange filings (NSE/BSE), SEBI announcements, PIB releases, company's own official press release/investor communication
- **Tier 2 (high confidence):** Major established financial media (Reuters, Bloomberg, ET, Moneycontrol, Business Standard, CNBC-TV18)
- **Tier 3 (needs corroboration):** Smaller publications, regional outlets, individual financial bloggers/analysts
- **Tier 4 (rumor only, never actionable alone):** Social media, Telegram/WhatsApp forwards, unverified posts

**Dynamic escalation:** When a Tier 3/4 source breaks something first, mark it internally as "unconfirmed — monitoring," route to the Rumors feed, don't fire a full-confidence alert. If a Tier 1/2 source or official filing corroborates it within a defined window (a few hours), upgrade confidence and re-trigger the full pipeline as confirmed. If no corroboration within the window, either drop it or keep it clearly labeled as rumor-only.

**Per-source reputation score (not just fixed tier):** Track each individual source's track record over time — how often has this specific outlet's early reporting later been confirmed vs proven false/retracted. A reliable source earns a higher weight even within its tier; an unreliable one gets discounted even if nominally a "known" outlet. This should self-correct as data accumulates.

**Independent corroboration vs syndication:** Detect when multiple sources are independently reporting the same fact (separate investigation/sourcing) vs just syndicating one original wire report. Only true independent corroboration should raise confidence — five outlets republishing one wire story is not five confirmations.

**Retraction/denial handling:** If a company officially denies a report, or a source retracts/corrects after an alert was already sent, the system needs a reversal mechanism — pull back or clearly flag the earlier alert as retracted, and notify anyone who received it.

**Exchange query as a signal:** NSE/BSE can issue formal clarification queries to companies on unusual price movement or unconfirmed rumor. A company's response (or refusal to respond) is itself a strong, verifiable signal — track as a distinct event type.

**Staleness check:** If verification takes long enough that the market has plausibly already reacted, mark the signal as stale and lower its priority.

**Human review (early stage):** Keep a lightweight manual review step for anything crossing a high-confidence threshold, especially in the first few months, to catch edge cases and validate confidence calibration before removing the human check. (See Section 12 for the full admin toggle/threshold design.)

---

## 9. RAG Cost & Speed Optimization Strategy

Important clarification made during planning: **analysis runs on ALL stocks, not just watchlisted ones.** Watchlist only controls which notifications get *delivered* to a given user (see Section 13) — so "only run RAG for watchlisted stocks" is NOT a valid optimization here. Instead:

1. **Pre-filter before any AI step** — cheap keyword/regex/ticker-mention filter to discard news unrelated to any tracked company before spending on classification or embedding. Applies at the whole-market level, not per-user.
2. **Deduplicate near-identical stories** — hash/fuzzy-match headlines; the same event is often reported by 10+ outlets within minutes. Only embed/process the first occurrence, link duplicates to the original event.
3. **Filter by materiality, not by watchlist** — run the cheap classification step (direction) on every relevant event for every stock. Only trigger the expensive RAG/historical-pattern-matching step for events that cross a materiality threshold (event-value-to-company-size ratio significant enough to matter). This keeps cost proportional to event significance, not to whether anyone happens to be watching that stock.
4. **Split fast alert from deep follow-up** — send an immediate basic alert from the fast classification step (direction + company), then run the RAG/pattern-match lookup asynchronously and send a short follow-up with historical context a bit later. Don't block the first alert on the slowest step.
5. **Optimize the embedding step itself** — use a smaller/cheaper embedding model, batch multiple texts per API call, use an approximate nearest-neighbor index (HNSW in pgvector) instead of brute-force comparison, and cache embeddings for any text already processed.

---

## 10. Notification & Delivery Logic

- **Analysis scope:** all stocks, always — not limited by any user's watchlist.
- **Delivery scope:** a user only receives notifications for stocks on their own watchlist/portfolio.
- **Rumors feed:** separate, opt-in feed of unconfirmed/low-confidence items (see Section 14) — distinct from the main confirmed-signal notification stream.

---

## 11. Rumors Feed (dedicated section)

- Shows unconfirmed news or events the system isn't confident about, distinct from the main confirmed-signal feed
- Each item displays: source tier, when first seen, whether corroboration is pending
- When an item later gets confirmed or denied, **update the same card in place** — don't leave stale unconfirmed items sitting indefinitely
- Long-term: could support a public trust-building stat like "X% of rumors in this feed were later confirmed"

---

## 12. Admin Panel — Full Section Breakdown

1. **Dashboard/Overview** — system health, pipeline status, active data source statuses, queue length, recent errors at a glance
2. **Data Sources Management** — list of configured sources (NSE/BSE, PIB, GeM, news APIs), enable/disable each, view last-fetch time/status per source
3. **LLM/Model Configuration**
   - Per-task model + provider selection (classification, entity resolution, RAG summary generation, high-stakes judgment calls)
   - API key management per provider (Anthropic, OpenAI, DeepSeek, etc.), stored encrypted
   - "Test connection" action before saving a new key
   - Fallback provider setting per task, in case a primary provider has an outage
4. **Notification Control**
   - Global and/or per-event-category toggle: auto-send vs require human review
   - Configurable confidence threshold (e.g. auto-send only if model confidence ≥ set %)
   - Review queue timer — if a queued item isn't reviewed within N minutes, auto-send anyway (avoids review bottleneck when admin is unavailable)
5. **Review Queue** — pending signals awaiting admin approval, showing confidence score, source(s), event details, with approve/reject/edit actions; confidence score visible during review so admin decisions also become tuning signal
6. **Source Reliability/Reputation Management** — view/adjust source tier assignments, view per-source reputation scores, manually override a tier if needed
7. **Track Record / Backtesting Dashboard** — historical accuracy, calibration metrics (stated confidence vs actual outcome), full signal logs (including every auto-send/auto-hold decision and its eventual outcome, per Section 7)
8. **Rumors Feed Management** — moderate/monitor unconfirmed items, manually confirm/deny/escalate to the main feed
9. **User Management** — manage registered users, view (not edit) portfolios/watchlists for support/oversight purposes
10. **System Logs/Monitoring** — ingestion pipeline logs, error alerts, uptime status per data source and per worker
11. **Cost/Usage Monitoring** — LLM API usage/cost tracking per provider and per task, embedding usage, Redis/queue usage — ties directly into the model cost-optimization strategy (Section 15)

---

## 13. Main (User-Facing) Panel — Full Section Breakdown

1. **Dashboard/Home** — summary of latest signals relevant to the user's watchlist, quick portfolio overview
2. **Watchlist/Portfolio Management** — add/remove stocks, view current holdings
3. **Live Signal Feed** — confirmed, notification-worthy events filtered to the user's watchlist: direction, confidence, historical range, source, traceability link
4. **Rumors Feed** — unconfirmed/low-confidence items, clearly labeled as such, opt-in
5. **Stock Detail View** — per-stock page with full historical signal log, matched historical patterns, corporate actions
6. **Notification Settings** — delivery channel preference (WhatsApp/push/web), language preference, frequency (real-time vs digest)
7. **Track Record / Transparency Page** — public accuracy log, past predictions vs actual outcomes
8. **Alerts History** — past notifications the user has received
9. **Profile/Account Settings** — language, region, and any subscription-tier settings

---

## 14. LLM Model Strategy

**Configurability requirement:** the platform must support switching between LLM providers (Anthropic, OpenAI, DeepSeek, etc.) via admin configuration, including API key management — not hardcoded to one vendor. See Section 12, item 3 for the admin panel design.

**Implementation approach:**
- Build an internal abstraction layer (e.g. a single `callLLM(task, prompt)` function) — pipeline code never calls a provider directly, always goes through this layer
- Consider adopting a routing library (e.g. LiteLLM) that provides one unified interface across providers, rather than building this abstraction fully from scratch

**Right-sizing model to task (cost control):**
- **Direction classification** — cheapest tier model (high-volume, well-defined, constrained-output task)
- **Entity resolution** — cheap-to-mid tier (needs slightly more reasoning than pure classification)
- **RAG historical-pattern summary generation** — mid tier (needs coherent, accurate synthesis of retrieved past events)
- **Rare high-stakes/ambiguous judgment calls** (crossing the confidence threshold for auto-send, or ambiguous event types like mergers) — reserve the top-tier model here only, since this is low-volume
- Consider a **complexity router**: try the cheap model first, escalate to a bigger model only when the cheap model's output looks uncertain
- **Validate, don't assume:** before locking in a model per task, test candidates against a labeled set of ~100–200 real examples and compare actual accuracy vs cost. Pick the cheapest model that clears the accuracy bar for that task.

---

## 15. WhatsApp Notification Delivery

- **Now (MVP phase):** use `whatsapp-web.js` (wwebjs) for WhatsApp delivery
- **Later:** migrate to Twilio (WhatsApp Business API) or another official provider once the product is validated and needs more reliable/scalable delivery
- Note for implementation: wwebjs relies on an unofficial WhatsApp Web session (not the official Business API), so treat it explicitly as a temporary/MVP-stage solution, not a long-term production dependency

---

## 16. Tech Stack

**Frontend**
- React + MUI (existing stack)
- Recharts or Chart.js for visualizations
- Socket.io-client (or native WebSocket) for live alert updates

**Backend**
- Node.js + Express (existing stack)
- Socket.io (server side) for pushing real-time alerts

**Database**
- PostgreSQL — users, portfolios, watchlists, signal history, track-record log
- pgvector extension on the same Postgres instance — historical pattern-matching (avoids running a separate vector DB while learning)

**AI/LLM layer**
- Anthropic Claude API / OpenAI API / DeepSeek API — configurable per Section 14
- Structured JSON output prompting (ask the model to return JSON, parse it) rather than free text

**Data ingestion**
- Node-cron or BullMQ (with Redis via Upstash) — scheduled polling and background job processing
- Puppeteer or Cheerio — scraping sources without a clean API
- A commercial news API (e.g. NewsAPI) to supplement scraping, alongside direct NSE/BSE filing feeds and PIB releases

**Notifications**
- whatsapp-web.js for now, Twilio later (Section 15)
- Web push / in-app via Socket.io

**Deployment**
- Render (web service + background workers) — free tier is fine for early learning/prototyping only: free web services spin down after 15 minutes of inactivity, no free Redis, free Postgres expires after 30–90 days. Budget roughly $25–50/month once live (Starter/Standard web service + worker + small Postgres + small Redis).
- Upstash for Redis/BullMQ — free tier (500K commands/month, 256MB) works for prototyping; officially supports BullMQ now (note: BullMQ did not support Upstash a few years ago, but Upstash added Redis Streams support and now ships documented BullMQ integration). Watch command volume as usage grows — Upstash recommends a Fixed plan (~$10/month starting) over pay-as-you-go once BullMQ traffic increases, since job queues are "chatty."
- Docker for containerization, consistent across local/deployed environments
- Basic uptime/log monitoring from day one (Render/Railway's built-in logs to start)

---

## 17. Learning Roadmap (for Mihir — new to AI domain)

Builds on existing Node/Express + React/MUI skills; sequence matters, get step 1 and step 6 working before the rest:

1. **LLM fundamentals and API usage** — how LLMs work conceptually (tokens, context window, temperature), practice calling Claude/OpenAI API from Node, prompt engineering for reliable classification and structured JSON output. Powers direction classification and entity resolution.
2. **NLP basics: NER and embeddings** — Named Entity Recognition concepts, what embeddings are. Can use an LLM for both rather than training custom models, but understanding the concepts helps judge when a plain LLM call isn't precise enough (e.g. need a dedicated NER library like spaCy).
3. **Data ingestion and pipelines** — fetching from APIs/RSS, scraping with Puppeteer/Cheerio, scheduling (cron/BullMQ + Redis), deduplication. This is the core differentiator — prioritize getting it reliable.
4. **Vector databases for pattern-matching** — how pgvector stores embeddings for similarity search; start with pgvector since it plugs into Postgres, which is already in the stack.
5. **Real-time backend architecture** — WebSockets/SSE for live alerts, background workers for async pipeline processing, WhatsApp/messaging API integration.
6. **Wire it together into an MVP** — one data source (start with NSE corporate announcements — structured and reliable) → LLM classification → entity resolution → store in DB → simple dashboard filtered by a hardcoded watchlist. Get this core loop working before adding personalization, multi-language, or the track-record page.
7. **Deployment for a real-time system** — Docker, Render/Railway deployment, managed Postgres (pgvector) + managed Redis (Upstash), basic monitoring/logging so silent data-source failures get noticed.

---

## 18. Open Questions / To Clarify Before/During Build

(Anything not explicitly covered above should be confirmed with Mihir before implementation — do not assume. Known open items as of this plan:)
- Exact list of initial data sources to integrate first (which news APIs, whether GeM/e-tender scraping is feasible at MVP stage)
- Exact confidence-threshold starting values, and whether they'll be global or per-event-category from day one (plan says start global, add per-category later)
- Monetization/pricing model — not yet decided
- Team composition — solo or with others — not yet decided
- Specific list of initial tracked stocks/universe for the MVP (all NSE/BSE listed, or a starting subset)
- Regional languages to prioritize first (Hindi confirmed as a target; others TBD)

---

*This document reflects all decisions made during planning conversations as of the latest update. If implementation surfaces a gap or ambiguity not addressed here, ask before proceeding rather than assuming.*
