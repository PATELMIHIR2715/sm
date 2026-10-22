"""
NSE Pre-Open Auction Equilibrium Runner Daemon (09:08 AM IST)
=============================================================
Audit Mandate Compliance:
- Evaluates indicative pre-open equilibrium auction price (09:08 - 09:12 AM IST) for all overnight candidate signals.
- Executes AutoLiveStreamWorker.preopen_execution_gate(signal, preopen_price, prev_close).
- Enforces terminal suppression on adverse gaps: gap >= min(ATR, 0.75 * SL) or target-exhausted gaps.
- Re-anchors targets & stop-loss to verified pre-open entry price.
- Dispatches approved signals via multi-channel alerts at 09:10 AM before the 09:15 AM market opening bell.
- Standalone CLI support:
    --once: Execute single verification pass and exit.
    --daemon: Run as standing daily daemon scheduled for 09:08 AM IST (Mon-Fri).
    --dry-run: Test evaluation logic without broadcasting actual alerts.
    --all-pending: Evaluate all pending overnight signals in the stream.
"""

import os
import sys
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
import json
import time
import math
import argparse
from datetime import datetime, timedelta, timezone

# Ensure project root in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from services.market_data.live_price_provider import LivePriceProvider
from services.ingestion.auto_live_stream_worker import AutoLiveStreamWorker

IST_OFFSET = timezone(timedelta(hours=5, minutes=30))

class PreOpenAuctionRunner:
    """
    Automated Pre-Market Execution Gatekeeper:
    Verifies overnight signals against the real 09:08 AM NSE auction discovery price.
    Prevents buying adverse gap-downs (e.g. LMW -4.5%, ADOR -3.5%) or chasing target-exhausted gap-ups.
    """

    def __init__(self, stream_path: str = None, dry_run: bool = False):
        self.stream_path = stream_path or os.path.join(PROJECT_ROOT, "data/live_signals_stream.json")
        self.dry_run = dry_run
        self.worker = AutoLiveStreamWorker()

    @staticmethod
    def get_current_ist_time() -> datetime:
        return datetime.now(IST_OFFSET)

    def load_stream_signals(self) -> list:
        if not os.path.exists(self.stream_path):
            print(f"[PRE-OPEN RUNNER] Stream file not found: {self.stream_path}")
            return []
        try:
            with open(self.stream_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[PRE-OPEN RUNNER ERROR] Failed to load stream: {e}")
            return []

    def save_stream_signals(self, signals: list) -> bool:
        tmp_path = f"{self.stream_path}.tmp_{int(time.time())}"
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(signals, f, indent=2, ensure_ascii=False)
            os.replace(tmp_path, self.stream_path)
            return True
        except Exception as e:
            print(f"[PRE-OPEN RUNNER ERROR] Failed to save stream: {e}")
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
            return False

    def find_overnight_candidates(
        self,
        signals: list,
        lookback_hours: float = 24.0,
        all_pending: bool = False,
        target_symbol: str = None
    ) -> list:
        """
        Filters candidate overnight signals generated after the previous session's close.
        Excludes signals that have already been evaluated or are terminally suppressed by upstream rules.
        """
        candidates = []
        now_ist = self.get_current_ist_time()
        cutoff_dt = now_ist - timedelta(hours=lookback_hours)

        for s in signals:
            sym = s.get("symbol", "").upper().strip()
            if target_symbol and sym != target_symbol.upper().strip():
                continue

            # Must have a directional forecast
            direction = s.get("predicted_direction", "NEUTRAL").upper()
            if direction not in ["BULLISH", "BEARISH", "BUY", "SELL", "SHORT"]:
                continue

            # Check if it was generated after-hours or flagged pending
            is_after_hours = s.get("is_after_hours") is True
            is_closed_session = s.get("market_session") == "AFTER_HOURS_CLOSED"
            is_pending_status = s.get("actionability_status") == "PENDING_PREOPEN_VERIFICATION"
            is_preopen_pending = s.get("preopen_status") == "PENDING"

            if not (is_after_hours or is_closed_session or is_pending_status or is_preopen_pending):
                continue

            # Skip if already evaluated today (unless pending explicitly)
            preopen_status = s.get("preopen_status")
            if preopen_status in ["APPROVED_FOR_EXECUTION", "QUARANTINED", "REJECTED"]:
                continue

            # Check publication timestamp within lookback window (unless all_pending is True)
            if not all_pending:
                pub_str = s.get("published_at") or s.get("processed_at")
                if pub_str:
                    try:
                        # Attempt standard ISO or DD-Mon-YYYY format parse
                        clean_pub = pub_str.replace(" IST", "").strip()
                        pub_dt = None
                        for fmt in ("%Y-%m-%d %H:%M:%S", "%d-%b-%Y %H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"):
                            try:
                                pub_dt = datetime.strptime(clean_pub.split("+")[0], fmt).replace(tzinfo=IST_OFFSET)
                                break
                            except Exception:
                                pass
                        if pub_dt and pub_dt < cutoff_dt:
                            continue
                    except Exception:
                        pass

            # Exclude upstream terminal suppressions (e.g. CIRP, Penny Stock, Market Drag Veto)
            action_status = str(s.get("actionability_status", ""))
            if action_status.startswith("SUPPRESSED_") and not action_status.startswith("SUPPRESSED_ADVERSE_PREOPEN"):
                continue

            candidates.append(s)

        return candidates

    def reanchor_targets_to_preopen_entry(self, signal: dict, preopen_price: float) -> dict:
        """
        Institutional Target Re-Anchoring:
        Recalibrates absolute price targets and stop-loss levels to the verified execution open price.
        Preserves original risk-reward percentage profile.
        """
        prev_base = float(signal.get("current_base_price_inr") or preopen_price)
        signal["entry_anchor_price_inr"] = preopen_price
        signal["current_base_price_inr"] = preopen_price

        # Extract stop loss percentage
        sl_pct = 3.2
        import re
        sl_str = str(signal.get("recommended_stop_loss", ""))
        nums = re.findall(r"[\d]+\.?\d*", sl_str)
        if nums:
            sl_pct = float(nums[-1])

        direction = signal.get("predicted_direction", "BULLISH").upper()
        is_bullish = direction in ["BULLISH", "BUY"]

        # Recalculate Stop-Loss
        if is_bullish:
            new_sl_price = round(preopen_price * (1.0 - (sl_pct / 100.0)), 2)
            signal["recommended_stop_loss"] = f"₹{new_sl_price:,.2f} (-{sl_pct:.2f}%)"
        else:
            new_sl_price = round(preopen_price * (1.0 + (sl_pct / 100.0)), 2)
            signal["recommended_stop_loss"] = f"₹{new_sl_price:,.2f} (+{sl_pct:.2f}%)"

        # Recalculate Two-Tier Targets
        tt = signal.get("two_tier_targets") or {}
        t1_safe = tt.get("t1_safe") or {}
        t2_runner = tt.get("t2_runner") or {}

        t1_pct = 1.8
        t2_pct = 3.5
        if t1_safe.get("percentage"):
            t1_nums = re.findall(r"[\d]+\.?\d*", str(t1_safe.get("percentage")))
            if t1_nums:
                t1_pct = float(t1_nums[0])
        if t2_runner.get("percentage"):
            t2_nums = re.findall(r"[\d]+\.?\d*", str(t2_runner.get("percentage")))
            if t2_nums:
                t2_pct = float(t2_nums[0])

        if is_bullish:
            new_t1_safe_price = round(preopen_price * (1.0 + (t1_pct / 100.0)), 2)
            new_t2_runner_price = round(preopen_price * (1.0 + (t2_pct / 100.0)), 2)
        else:
            new_t1_safe_price = round(preopen_price * (1.0 - (t1_pct / 100.0)), 2)
            new_t2_runner_price = round(preopen_price * (1.0 - (t2_pct / 100.0)), 2)

        signal["two_tier_targets"] = {
            "t1_safe": {
                "label": "T1 Safe Profit-Lock",
                "price": new_t1_safe_price,
                "percentage": f"{t1_pct:+.2f}%",
                "allocation_pct": 70,
                "action": "LOCK_70_PCT_PROFIT"
            },
            "t2_runner": {
                "label": "T2 Extended Target",
                "price": new_t2_runner_price,
                "percentage": f"{t2_pct:+.2f}%",
                "allocation_pct": 30,
                "action": "TRAIL_STOP_TO_ENTRY"
            }
        }
        signal["t1_safe_target"] = signal["two_tier_targets"]["t1_safe"]
        signal["t2_runner_target"] = signal["two_tier_targets"]["t2_runner"]

        # Update t1_target range
        low_t1 = min(new_t1_safe_price, new_t2_runner_price)
        high_t1 = max(new_t1_safe_price, new_t2_runner_price)
        signal["t1_target"] = {
            "percentage_range": f"{t1_pct:.2f}% - {t2_pct:.2f}%",
            "price_target_range_inr": f"₹{low_t1:,.2f} - ₹{high_t1:,.2f}",
            "price_low": low_t1,
            "price_high": high_t1,
            "target_date_horizon": "Today 09:15 AM Open to 15:30 PM (T+1)"
        }

        return signal

    def evaluate_candidate(
        self,
        signal: dict,
        mock_preopen_quote: dict = None
    ) -> dict:
        """
        Runs the pre-open auction verification gate for a single candidate signal.
        """
        sym = signal.get("symbol", "").upper().strip()
        prev_close = float(signal.get("current_base_price_inr") or 0.0)

        # Retrieve verified auction quote
        if mock_preopen_quote:
            quote = mock_preopen_quote
        else:
            quote = LivePriceProvider.get_preopen_auction_quote(sym, prev_close_override=prev_close)

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if not quote or not quote.get("preopen_price") or quote.get("preopen_price") <= 0:
            print(f"[PRE-OPEN VERIFICATION FAILED] {sym}: Missing or unverified pre-open auction price. Terminally suppressing.")
            signal["preopen_status"] = "UNVERIFIED_PRICE_QUARANTINED"
            signal["preopen_verified_at"] = now_str
            signal["dispatchable"] = False
            signal["is_useful"] = False
            signal["actionability_status"] = "SUPPRESSED_UNVERIFIED_PREOPEN_PRICE"
            signal["suppression_reason"] = "UNVERIFIED_PREOPEN_PRICE"
            return {
                "symbol": sym,
                "approved": False,
                "reason": "UNVERIFIED_PREOPEN_PRICE",
                "preopen_price": None,
                "prev_close": prev_close,
                "gap_pct": 0.0
            }

        preopen_price = float(quote["preopen_price"])
        effective_prev_close = float(quote.get("prev_close") or prev_close or preopen_price)

        # Execute AutoLiveStreamWorker preopen gate
        gate_res = AutoLiveStreamWorker.preopen_execution_gate(
            signal=signal,
            preopen_price=preopen_price,
            prev_close=effective_prev_close
        )

        gap_pct = gate_res.get("gap_pct", round(((preopen_price - effective_prev_close) / effective_prev_close) * 100.0, 2))

        if not gate_res.get("approved", False):
            # Terminally Quarantine Adverse Gap
            reason = gate_res.get("reason", "ADVERSE_PREOPEN_GAP")
            print(f"[QUARANTINE ENFORCED] {sym}: REJECTED at 09:08 AM Pre-Open! Reason: {reason}")
            signal["preopen_status"] = "QUARANTINED"
            signal["preopen_verified_at"] = now_str
            signal["preopen_verified_entry_inr"] = preopen_price
            signal["preopen_gap_pct"] = gap_pct
            signal["dispatchable"] = False
            signal["is_useful"] = False
            signal["actionability_status"] = f"SUPPRESSED_{reason}"
            signal["suppression_reason"] = reason

            return {
                "symbol": sym,
                "approved": False,
                "reason": reason,
                "preopen_price": preopen_price,
                "prev_close": effective_prev_close,
                "gap_pct": gap_pct
            }
        else:
            # Approved for 09:10 AM Execution Dispatch
            print(f"[PRE-OPEN APPROVED] {sym}: Discovered open INR {preopen_price:,.2f} ({gap_pct:+.2f}% gap). Re-anchoring targets.")
            signal["preopen_status"] = "APPROVED_FOR_EXECUTION"
            signal["preopen_verified_at"] = now_str
            signal["preopen_verified_entry_inr"] = preopen_price
            signal["preopen_gap_pct"] = gap_pct
            signal["dispatchable"] = True
            signal["is_useful"] = True
            signal["actionability_status"] = "DISPATCHABLE_ACTIVE"
            signal["suppression_reason"] = None

            # Re-anchor targets to actual preopen entry
            self.reanchor_targets_to_preopen_entry(signal, preopen_price)

            return {
                "symbol": sym,
                "approved": True,
                "reason": None,
                "preopen_price": preopen_price,
                "prev_close": effective_prev_close,
                "gap_pct": gap_pct
            }

    def dispatch_approved_signal(self, signal: dict):
        """
        Dispatches multi-channel execution alert for approved pre-open signals at 09:10 AM.
        """
        if self.dry_run:
            print(f"[DRY-RUN] Skipping alert broadcast for {signal.get('symbol')}")
            return

        try:
            print(f"[PRE-BELL DISPATCH 09:10 AM] Broadcasting alert for {signal.get('symbol')}...")
            self.worker._dispatch_instant_alert(signal)
            self.worker._sync_to_supabase(signal)
        except Exception as e:
            print(f"[DISPATCH ERROR] Failed to broadcast alert for {signal.get('symbol')}: {e}")

    def run_cycle(
        self,
        lookback_hours: float = 24.0,
        all_pending: bool = False,
        target_symbol: str = None,
        mock_quotes: dict = None
    ) -> dict:
        """
        Executes a single pre-open auction verification pass across all candidate signals.
        """
        now_ist = self.get_current_ist_time()
        print(f"\n=======================================================")
        print(f"🚀 PRE-OPEN AUCTION VERIFICATION CYCLE: {now_ist.strftime('%Y-%m-%d %H:%M:%S IST')}")
        print(f"=======================================================")

        all_signals = self.load_stream_signals()
        candidates = self.find_overnight_candidates(
            all_signals,
            lookback_hours=lookback_hours,
            all_pending=all_pending,
            target_symbol=target_symbol
        )

        print(f"[CANDIDATES FOUND] {len(candidates)} overnight candidate signal(s) pending pre-open auction verification.")

        approved_signals = []
        quarantined_signals = []
        cycle_results = []

        # Create quick index mapping for updates
        id_to_idx = {s.get("id"): idx for idx, s in enumerate(all_signals) if s.get("id")}

        for cand in candidates:
            sym = cand.get("symbol")
            mock_quote = mock_quotes.get(sym) if mock_quotes else None
            res = self.evaluate_candidate(cand, mock_preopen_quote=mock_quote)
            cycle_results.append(res)

            # Update in-memory stream signals
            s_id = cand.get("id")
            if s_id in id_to_idx:
                all_signals[id_to_idx[s_id]] = cand

            if res["approved"]:
                approved_signals.append(cand)
            else:
                quarantined_signals.append(cand)

        # Persist updated signals atomically
        if candidates:
            self.save_stream_signals(all_signals)
            print(f"[PERSISTENCE] Successfully updated {len(candidates)} signal records in live stream.")

        # Pre-Bell 09:10 AM Dispatch for Approved Signals
        for approved_cand in approved_signals:
            self.dispatch_approved_signal(approved_cand)

        summary = {
            "timestamp": now_ist.strftime("%Y-%m-%d %H:%M:%S IST"),
            "total_candidates": len(candidates),
            "approved_count": len(approved_signals),
            "quarantined_count": len(quarantined_signals),
            "approved_symbols": [s.get("symbol") for s in approved_signals],
            "quarantined_symbols": [s.get("symbol") for s in quarantined_signals],
            "results": cycle_results
        }

        print(f"📊 SUMMARY: {len(approved_signals)} Approved | {len(quarantined_signals)} Quarantined")
        print(f"=======================================================\n")
        return summary

    @classmethod
    def get_seconds_until_next_run(cls, target_hour: int = 9, target_minute: int = 8) -> tuple:
        """
        Calculates seconds until the next 09:08:00 AM IST on a Monday-Friday trading day.
        """
        now = cls.get_current_ist_time()
        # Today target
        target = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)

        # If already past 09:08 AM today, schedule for tomorrow
        if now >= target:
            target += timedelta(days=1)

        # If target lands on Saturday (weekday 5) -> advance to Monday (weekday 0)
        while target.weekday() >= 5:
            target += timedelta(days=1)

        delta = (target - now).total_seconds()
        return max(0.0, delta), target

    def run_daemon(self):
        """
        Standing Daemon Mode:
        Calculates time until next 09:08 AM IST on weekdays, sleeps safely,
        executes auction verification at 09:08 AM, broadcasts at 09:10 AM, and repeats.
        """
        print("🤖 [PRE-OPEN AUCTION RUNNER DAEMON LAUNCHED]")
        print("Scheduled to verify overnight equilibrium prices daily at 09:08 AM IST (Mon-Fri).\n")

        while True:
            seconds_to_wait, next_run = self.get_seconds_until_next_run(target_hour=9, target_minute=8)
            hours = int(seconds_to_wait // 3600)
            mins = int((seconds_to_wait % 3600) // 60)
            secs = int(seconds_to_wait % 60)

            print(f"⏳ Sleeping {hours}h {mins}m {secs}s until next trading pre-market session: {next_run.strftime('%Y-%m-%d %H:%M:%S IST')}")

            # Sleep in intervals for clean interruptibility
            while seconds_to_wait > 0:
                sleep_chunk = min(60.0, seconds_to_wait)
                time.sleep(sleep_chunk)
                seconds_to_wait -= sleep_chunk

            # At 09:08 AM IST: Run verification cycle
            try:
                self.run_cycle(lookback_hours=24.0)
            except Exception as e:
                print(f"[DAEMON CYCLE ERROR] {e}")

            # Sleep for 15 minutes to guarantee past 09:08 AM today before calculating next run
            time.sleep(900)


def main():
    parser = argparse.ArgumentParser(description="NSE 09:08 AM Pre-Open Auction Runner")
    parser.add_argument("--once", action="store_true", help="Run a single verification pass immediately and exit")
    parser.add_argument("--daemon", action="store_true", help="Run as standing daemon scheduled for 09:08 AM IST daily")
    parser.add_argument("--dry-run", action="store_true", help="Evaluate without broadcasting live alerts")
    parser.add_argument("--all-pending", action="store_true", help="Evaluate all pending overnight candidates in the stream")
    parser.add_argument("--lookback-hours", type=float, default=24.0, help="Candidate lookback window in hours (default 24)")
    parser.add_argument("--symbol", type=str, default=None, help="Target specific symbol")

    args = parser.parse_args()

    runner = PreOpenAuctionRunner(dry_run=args.dry_run)

    if args.daemon:
        runner.run_daemon()
    else:
        # Default to single pass if neither specified
        runner.run_cycle(
            lookback_hours=args.lookback_hours,
            all_pending=args.all_pending,
            target_symbol=args.symbol
        )

if __name__ == "__main__":
    main()
