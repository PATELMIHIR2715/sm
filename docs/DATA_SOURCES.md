# Comprehensive Data Sources & Ingestion Architecture

This document specifies all trusted, verified data sources for the Stock Market News Impact Platform, categorized by trust tier and signal type.

---

## Tier 1: Regulatory & Exchange Statutory Feeds (Near-Certain Trust)

| Source Name | Data Type / Content | Impact Signal & Frequency |
| :--- | :--- | :--- |
| **NSE & BSE Corporate Announcements** | XBRL disclosures, board meeting outcomes, earnings results, order wins, capacity expansions, executive exits. | Real-time (15s polling + WebSocket). High directional move. |
| **NSE/BSE Insider Trading Disclosures (PIT & SAST)** | Regulation 7(2) disclosures: Key Management Personnel (KMP) & Promoter share buys/sells/pledges. | Real-time. High conviction for promoter buying/pledging. |
| **NSE & BSE Bulk / Block Deals** | Daily block deals window & market-end bulk trade reports (HNI, FII, DII trades > 0.5% equity). | Daily end-of-day & intraday block window. |
| **SEBI Orders & Circulars** | Penalty notices, debarment orders, regulatory policy changes, investigation updates. | Immediate risk alert / protection for holdings. |
| **Exchange Clarification Queries & Responses** | NSE/BSE price/volume movement queries & official company responses to rumors. | High signal clarity on rumor confirmation/denial. |
| **ASM / GSM Surveillance Lists** | Additions/removals of stocks in Additional / Graded Surveillance Measures by NSE/BSE. | Circuit limit & margin requirement impact. |

---

## Tier 2: Government Tenders, Policy & Credit Ratings

| Source Name | Data Type / Content | Impact Signal & Frequency |
| :--- | :--- | :--- |
| **PIB (Press Information Bureau)** | Cabinet approvals, PLI scheme releases, ministry sector allocations, defense contract awards. | High macro & sector-wide impact. |
| **GeM & CPPP (eProcure) Tenders** | Government e-Marketplace awards & central public procurement tender wins. | Materiality ratio (`Order Size / Revenue`) evaluation. |
| **Credit Rating Agencies (CRISIL, ICRA, CARE, India Ratings)** | Debt rating upgrades, downgrades, default warnings, watchlist changes. | Direct impact on borrowing cost & creditworthiness. |
| **RBI Notifications & MPC Press Releases** | Monetary Policy Committee rate decisions, banking/NBFC liquidity circulars. | Sector impact (Banks, NBFCs, Housing Finance, Auto). |
| **Ministry of Corporate Affairs (MCA / ROC)** | Filings on director resignations, capital structure changes, charge creations. | Corporate governance monitoring. |

---

## Tier 3: Institutional Research, Concalls & Financial Media

| Source Name | Data Type / Content | Impact Signal & Frequency |
| :--- | :--- | :--- |
| **Analyst Earnings Call Transcripts & Presentations** | Management growth guidance, capex plans, margin outlook, order book pipeline. | Post-earnings reaction & multi-quarter guidance shifts. |
| **Institutional Broker Reports & Revisions** | Upgrades/downgrades and target price changes from major brokerages (Motilal Oswal, ICICI Direct, HDFC Sec, Nuvama, Jefferies). | Market sentiment & analyst consensus shift. |
| **Financial Media News (ET, BS, Moneycontrol, Reuters)** | Curated financial headlines, sector updates, international commodity news. | Deduplicated via Redis SHA256 before scoring. |

---

## Ingestion Architecture & Deduplication Rules

1. **Source Tier Weighting:** Tier 1 sources bypass human review if confidence is high; Tier 3 sources default to lower weight unless corroborated by Tier 1/2.
2. **Canonical Clustering:** SHA256 content signature + 15-minute sliding window prevents duplicate alerts across multiple news outlets reporting the same filing.
3. **Materiality Filter:** Skip routine non-material filings (e.g. loss of share certificate notices) before running AI classification.
