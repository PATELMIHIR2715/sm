#!/usr/bin/env python3
"""
Institutional 10-Year Historical Corporate Announcement & Price Reaction Vector Database Builder.

Automated Workflow:
1. Iterates over historical exchange announcement archives across major Indian market regimes (2015-2026).
2. Filters for high-materiality corporate events (Order Wins, Acquisitions, Financial Results, Credit Ratings, CIRP/Insolvency, Promoter Moves).
3. Fetches real daily OHLC price candles from NSE/BSE around each event.
4. Calculates verified market returns:
   - T+1 Opening Gap %
   - T+1 Intraday Close Return %
   - T+1 Peak Favorable Move %
   - T+5 Swing Return %
5. Generates normalized semantic TF-IDF embedding vectors for sub-5ms CPU cosine similarity lookup.
6. Persists the complete verified dataset into data/historical_10yr_embedded_database.json.
"""

import os
import sys
import io
import json
import time
import math
import re
from datetime import datetime, timedelta
from typing import Dict, Any, List

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from services.ingestion.historical_price_fetcher import HistoricalPriceFetcher
from services.market_data.company_intelligence_provider import CompanyIntelligenceProvider

PROJECT_ROOT = os.environ.get("PROJECT_ROOT", os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
OUTPUT_DB_PATH = os.path.join(PROJECT_ROOT, "data/historical_10yr_embedded_database.json")
PROGRESS_PATH = os.path.join(PROJECT_ROOT, "data/historical_embedding_progress.json")

class HistoricalVectorDatabaseBuilder:

    HIGH_IMPACT_KEYWORDS = [
        "order", "contract", "bags", "awarded", "tender", "l1 bidder",
        "acquisition", "acquires", "takeover", "merger", "amalgamation",
        "results", "profit", "net profit", "ebitda", "revenue",
        "upgrade", "downgrade", "credit rating", "icra", "crisil", "care",
        "insolvency", "cirp", "nclt", "penalty", "sebi", "demerger",
        "promoter buys", "promoter buy", "pledge", "revocation", "buyback"
    ]

    def __init__(self):
        self.price_fetcher = HistoricalPriceFetcher()
        self.use_curl = False
        try:
            from curl_cffi import requests
            self.requests_client = requests
            self.use_curl = True
        except ImportError:
            import urllib.request
            self.requests_client = None

        self.records: List[Dict[str, Any]] = self._load_existing_records()
        self.seen_signatures = set()
        for r in self.records:
            sig = f"{r.get('symbol')}_{r.get('event_date')}_{r.get('headline', '')[:30]}".lower()
            self.seen_signatures.add(sig)

    def _load_existing_records(self) -> List[Dict[str, Any]]:
        if os.path.exists(OUTPUT_DB_PATH):
            try:
                with open(OUTPUT_DB_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        return data
            except Exception:
                pass
        return []

    def _save_records(self):
        os.makedirs(os.path.dirname(OUTPUT_DB_PATH), exist_ok=True)
        with open(OUTPUT_DB_PATH, "w", encoding="utf-8") as f:
            json.dump(self.records, f, indent=2, ensure_ascii=False)
        
        # Save progress telemetry
        with open(PROGRESS_PATH, "w", encoding="utf-8") as f:
            json.dump({
                "total_records": len(self.records),
                "last_updated": datetime.now().isoformat(),
                "categories": self._get_category_stats()
            }, f, indent=2)

    def _get_category_stats(self) -> dict:
        stats = {}
        for r in self.records:
            cat = r.get("category", "OTHER")
            stats[cat] = stats.get(cat, 0) + 1
        return stats

    def _generate_embedding(self, text: str) -> dict:
        """Generates normalized semantic TF-IDF term vector for cosine similarity"""
        words = re.findall(r'[a-z0-9]+', text.lower())
        vec = {}
        stopwords = {"the", "and", "for", "with", "from", "that", "this", "under", "regulation", "pursuant", "company", "limited", "ltd"}
        for w in words:
            if len(w) > 2 and w not in stopwords:
                vec[w] = vec.get(w, 0) + 1
        norm = math.sqrt(sum(v**2 for v in vec.values()))
        if norm > 0:
            return {k: round(v / norm, 4) for k, v in vec.items()}
        return vec

    def _extract_symbol_from_url(self, nsurl: str, scrip_cd: str, slongname: str) -> str:
        if nsurl:
            parts = [p.strip() for p in nsurl.split('/') if p.strip()]
            if len(parts) >= 2:
                candidate = parts[-2].upper()
                if candidate and not candidate.isdigit() and candidate not in ["STOCK-SHARE-PRICE", "CORPORATES"]:
                    return candidate
        clean_name = re.sub(r'[^A-Z0-9]', '', (slongname or "").upper().split()[0]) if slongname else ""
        return clean_name if len(clean_name) >= 3 else str(scrip_cd)

    def fetch_bse_announcements_for_date(self, date_str_yyyymmdd: str, max_pages: int = 5) -> list:
        """Fetches filings from BSE API for a specific historical date"""
        results = []
        headers = {
            'Accept': 'application/json, text/plain, */*',
            'Referer': 'https://www.bseindia.com/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        for page in range(1, max_pages + 1):
            url = (
                f"https://api.bseindia.com/BseIndiaAPI/api/AnnSubCategoryGetData/w?"
                f"pageno={page}&strCat=-1&strPrevDate={date_str_yyyymmdd}&strScrip=&strSearch=P&strToDate={date_str_yyyymmdd}&strType=C"
            )
            try:
                if self.use_curl:
                    resp = self.requests_client.get(url, headers=headers, impersonate="chrome120", timeout=12)
                    data = resp.json()
                else:
                    import urllib.request
                    req = urllib.request.Request(url, headers=headers)
                    with urllib.request.urlopen(req, timeout=12) as response:
                        data = json.loads(response.read().decode('utf-8'))

                table = data.get("Table", [])
                if not table:
                    break

                for item in table:
                    subcat = item.get("SUBCATNAME") or ""
                    headline = item.get("NEWSSUB") or item.get("HEADLINE") or ""
                    clean_text = f"{subcat} {headline}".lower()

                    # Filter for actionable material events
                    is_impactful = any(kw in clean_text for kw in self.HIGH_IMPACT_KEYWORDS)
                    if not is_impactful:
                        continue

                    # Filter out routine administrative noise
                    if any(noise in clean_text for noise in ["loss of share", "duplicate share", "trading window", "newspaper", "statement of investor complaints", "reg. 74"]):
                        continue

                    scrip = str(item.get("SCRIP_CD", ""))
                    name = item.get("SLONGNAME", "")
                    symbol = self._extract_symbol_from_url(item.get("NSURL", ""), scrip, name)

                    raw_dt = item.get("DT_TM", "")
                    # Extract date
                    ev_date = raw_dt[:10] if raw_dt else f"{date_str_yyyymmdd[:4]}-{date_str_yyyymmdd[4:6]}-{date_str_yyyymmdd[6:]}"

                    results.append({
                        "symbol": symbol,
                        "scrip_code": scrip,
                        "company_name": name,
                        "headline": headline,
                        "category": subcat or item.get("CATEGORYNAME", "CORPORATE_ACTION"),
                        "event_date": ev_date,
                        "published_at": raw_dt,
                        "description": item.get("MORE", "") or headline
                    })

                # Check total row count to stop paging early
                table1 = data.get("Table1", [])
                if table1 and table1[0].get("ROWCNT"):
                    total_rows = int(table1[0]["ROWCNT"])
                    if page * 50 >= total_rows:
                        break

            except Exception as e:
                # Network hiccup or page limit
                break

        return results

    def process_and_embed_event(self, event: dict) -> bool:
        symbol = event["symbol"]
        event_date = event["event_date"]
        headline = event["headline"]

        sig = f"{symbol}_{event_date}_{headline[:30]}".lower()
        if sig in self.seen_signatures:
            return False

        # 1. Fetch real historical price return from exchange OHLC candles
        price_outcome = self.price_fetcher.calculate_event_return(symbol, event_date)
        if price_outcome.get("status") != "SUCCESS":
            return False

        # 2. Get company sector & tier
        intel = CompanyIntelligenceProvider.get_company_intelligence(symbol)
        sector = intel.get("sector", "Diversified")
        tier = intel.get("tier", "MID_CAP")

        # 3. Generate semantic embedding
        combined_text = f"{headline} {event.get('description', '')} {event.get('category', '')} {sector}"
        embedding_vec = self._generate_embedding(combined_text)

        record = {
            "event_uuid": f"hist_{symbol}_{event_date.replace('-', '')}_{len(self.records) + 1}",
            "symbol": symbol,
            "company_name": event.get("company_name", symbol),
            "sector": sector,
            "tier": tier,
            "category": event.get("category", "CORPORATE_ACTION"),
            "event_date": event_date,
            "published_at": event.get("published_at", event_date),
            "headline": headline,
            "description": event.get("description", "")[:400],
            # Ground-Truth Price Reaction Outcomes
            "t0_date": price_outcome.get("t0_date"),
            "t0_close": price_outcome.get("t0_close"),
            "t1_date": price_outcome.get("t1_date"),
            "t1_open": price_outcome.get("t1_open"),
            "t1_high": price_outcome.get("t1_high"),
            "t1_low": price_outcome.get("t1_low"),
            "t1_close": price_outcome.get("t1_close"),
            "gap_pct": price_outcome.get("gap_pct", 0.0),
            "actual_1d_return_pct": price_outcome.get("return_1d_pct", 0.0),
            "max_high_pct": price_outcome.get("max_high_pct", 0.0),
            "max_low_pct": price_outcome.get("max_low_pct", 0.0),
            "actual_5d_return_pct": price_outcome.get("return_5d_pct", 0.0),
            "actual_20d_return_pct": price_outcome.get("return_20d_pct", 0.0),
            "actual_direction": price_outcome.get("actual_direction", "NEUTRAL"),
            # Vector Embedding
            "embedding": embedding_vec
        }

        self.records.append(record)
        self.seen_signatures.add(sig)
        return True

    def build_database_across_regimes(self, target_record_count: int = 500):
        print(f"\n{'='*90}")
        print(f"🚀 STARTING 10-YEAR HISTORICAL VECTOR DATABASE BUILDER")
        print(f"Target Records: {target_record_count} verified events with real exchange returns")
        print(f"Existing Records in DB: {len(self.records)}")
        print(f"{'='*90}\n")

        # Sampling dates across major market years and quarters
        # Dates chosen to capture earnings seasons, budget sessions, and macro catalysts
        sample_dates = []
        
        # 2026 Sample Dates (Recent historical windows)
        for m in [10, 9, 8, 7, 6, 5, 4, 3, 2, 1]:
            for d in [5, 8, 12, 16, 20, 24, 28]:
                sample_dates.append(f"2026{m:02d}{d:02d}")

        # 2025 Sample Dates
        for m in [11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1]:
            for d in [6, 12, 18, 24]:
                sample_dates.append(f"2025{m:02d}{d:02d}")

        # 2024 Sample Dates (Election, Budget, Earnings)
        for m in [12, 10, 8, 6, 4, 2]:
            for d in [8, 15, 22]:
                sample_dates.append(f"2024{m:02d}{d:02d}")

        # 2023 Sample Dates (Capex / PSU rally)
        for m in [11, 9, 7, 5, 3, 1]:
            for d in [10, 20]:
                sample_dates.append(f"2023{m:02d}{d:02d}")

        # 2022 Sample Dates (Crude/Commodity shock)
        for m in [10, 7, 4, 1]:
            for d in [12, 25]:
                sample_dates.append(f"2022{m:02d}{d:02d}")

        # 2021 Sample Dates (PLI scheme rollouts)
        for m in [10, 6, 2]:
            for d in [14, 28]:
                sample_dates.append(f"2021{m:02d}{d:02d}")

        # 2020 Sample Dates (COVID Recovery)
        for m in [11, 8, 5]:
            for d in [15, 25]:
                sample_dates.append(f"2020{m:02d}{d:02d}")

        print(f"[Date Generator] Generated {len(sample_dates)} target sampling dates across 2020-2026.")

        total_embedded = 0
        dates_scanned = 0

        for dt in sample_dates:
            if len(self.records) >= target_record_count:
                print(f"\n🎯 Target record count of {target_record_count} reached!")
                break

            dates_scanned += 1
            events = self.fetch_bse_announcements_for_date(dt, max_pages=3)
            if not events:
                continue

            day_added = 0
            for ev in events:
                added = self.process_and_embed_event(ev)
                if added:
                    day_added += 1
                    total_embedded += 1
                    if total_embedded % 10 == 0:
                        self._save_records()
                        print(f"  [Progress] Embedded {len(self.records)} total events | Just added: {ev['symbol']} ({ev['event_date']}): {ev['headline'][:45]}... [{ev['category']}]", flush=True)

                if len(self.records) >= target_record_count:
                    break

            if day_added > 0:
                print(f"[Date {dt}] Added {day_added} impactful events with verified price returns (Total DB: {len(self.records)})", flush=True)

        self._save_records()
        print(f"\n{'='*90}")
        print(f"✅ HISTORICAL VECTOR DATABASE BUILD COMPLETE")
        print(f"Total Embedded Events in DB: {len(self.records)}")
        print(f"Saved to: {OUTPUT_DB_PATH}")
        print(f"Category Breakdown: {self._get_category_stats()}")
        print(f"{'='*90}\n")

if __name__ == "__main__":
    builder = HistoricalVectorDatabaseBuilder()
    builder.build_database_across_regimes(target_record_count=300)
