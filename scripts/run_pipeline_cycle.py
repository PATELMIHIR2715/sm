"""
Manual Pipeline Execution Runner.
Polls all 6 live exchange & regulatory data streams, classifies catalysts,
computes Two-Tier targets, checks tradability & circuits, and archives signals.
"""

import os
import sys
import io
import json
from datetime import datetime

if sys.stdout and hasattr(sys.stdout, 'buffer'):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass

PROJECT_ROOT = os.environ.get("PROJECT_ROOT", os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(PROJECT_ROOT)

from services.ingestion.auto_live_stream_worker import AutoLiveStreamWorker

def main():
    print("=" * 70)
    print("⚡ INSTITUTIONAL MARKET INTELLIGENCE PIPELINE RUNNER")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}")
    print("Feeds: NSE Announcements, BSE Corporate Disclosures, PIT Insider Trading,")
    print("       Bulk & Block Deals, Credit Ratings, PIB & GeM Tender Awards")
    print("=" * 70, flush=True)

    worker = AutoLiveStreamWorker()
    count = worker.poll_cycle()
    print(f"\n[PIPELINE EXECUTION COMPLETE] Ingested & processed: {count} new events", flush=True)

    stream_file = os.path.join(PROJECT_ROOT, "data/live_signals_stream.json")
    if os.path.exists(stream_file):
        with open(stream_file, "r", encoding="utf-8") as f:
            signals = json.load(f)

        print("\n" + "=" * 70)
        print(f"LATEST 5 DISPATCHED LIVE SIGNALS (Total in DB: {len(signals)}):")
        print("=" * 70)
        for s in signals[:5]:
            sym = s.get("symbol", "UNKNOWN")
            p_dir = s.get("predicted_direction", "NEUTRAL")
            conv = s.get("conviction_score_pct", 0)
            ltp = s.get("current_base_price_inr")
            ltp_str = f"₹{ltp:,.2f}" if ltp else "N/A"
            ver = s.get("model_version", "v3.0")
            status = s.get("actionability_status", "ACTIVE")

            tt = s.get("two_tier_targets") or {}
            t1 = tt.get("t1_safe", {}).get("price")
            t2 = tt.get("t2_runner", {}).get("price")
            t1_str = f"₹{t1:,.2f}" if t1 else "TBD"
            t2_str = f"₹{t2:,.2f}" if t2 else "TBD"

            print(f"• {sym:<12} | {p_dir:<8} ({conv}%) | LTP: {ltp_str:<10} | T1: {t1_str} | T2: {t2_str} | Version: {ver} | Status: {status}")
            head = s.get("headline", "")
            if len(head) > 95:
                head = head[:92] + "..."
            print(f"  Reason: {head}")
            print("-" * 70)

if __name__ == "__main__":
    main()
