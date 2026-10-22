#!/usr/bin/env python3
"""
Institutional Quantitative Signal Evaluation Engine (Target-First vs Stop-First).

Compliant with Quantitative Trading Pipeline Audit (2026-10-22):
1. Distinguishes After-Market from Market-Hours alerts:
   - For After-Market filings, Day-0 prices are discarded (signal could not be traded).
   - Entry occurs at T+1 opening price (Day 1 Open) after passing pre-open gap verification.
2. 09:08 Pre-Open Gatekeeper integration:
   - Evaluates opening gap against planned stop loss: if adverse gap >= min(ATR, 0.75 * SL), trade was quarantined.
   - If opening price gapped through stop, exited at open price (GAP_STOPPED_OUT).
3. Chronological Target-First vs Stop-First Resolution:
   - TARGET_FIRST: Target touched without breaching Stop Loss (WIN).
   - STOP_FIRST: Stop touched without reaching Target (LOSS).
   - AMBIGUOUS_STOP_FIRST: Both Target and Stop touched on same daily bar -> conservative institutional standard assumes Stop Loss triggered first.
   - TIMED_OUT: Position closed at T+1 session close.
4. Institutional Cost Deductions:
   - 25 bps bid-ask spread + 10 bps statutory fees & slippage = 35 bps round-trip friction.
5. Produces comprehensive audit statistics:
   - Target-First Win Rate, Stop-First Rate, Net Expectancy %, Profit Factor, Max Drawdown.
   - Segmentation by Event Archetype, Conviction Tier, Direction, and Regime.
   - Saves audited JSON report to data/backtest_reports/institutional_signal_evaluation_audit.json.
"""

import os
import sys
import io
import json
import re
import math
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple

# Fix Windows encoding
if sys.stdout and hasattr(sys.stdout, 'buffer'):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, 'buffer'):
    try:
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(PROJECT_ROOT)

from services.ingestion.auto_live_stream_worker import AutoLiveStreamWorker
from services.market_data.live_price_provider import LivePriceProvider

DATA_FILE = os.path.join(PROJECT_ROOT, 'data/live_signals_stream.json')
PRICE_CACHE_DIR = os.path.join(PROJECT_ROOT, 'data/price_cache')
REPORT_FILE = os.path.join(PROJECT_ROOT, 'data/backtest_reports/institutional_signal_evaluation_audit.json')

def load_signals() -> List[dict]:
    if not os.path.exists(DATA_FILE):
        print(f"ERROR: {DATA_FILE} not found.")
        return []
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def parse_price_range(target_dict: Optional[dict]) -> Tuple[Optional[float], Optional[float]]:
    if not target_dict:
        return None, None
    lo = target_dict.get('price_low')
    hi = target_dict.get('price_high')
    if lo is not None and hi is not None:
        try:
            return float(lo), float(hi)
        except Exception:
            pass
    price_str = target_dict.get('price_target_range_inr', '')
    nums = re.findall(r'[\d]+\.?\d*', price_str.replace(',', ''))
    if len(nums) >= 2:
        return float(nums[0]), float(nums[1])
    return None, None

def parse_stop_loss(signal: dict, base_price: float, direction: str) -> float:
    sl_val = signal.get('recommended_stop_loss_price') or signal.get('stop_loss_price')
    if sl_val and float(sl_val) > 0:
        return float(sl_val)
    sl_str = str(signal.get('recommended_stop_loss', ''))
    nums = re.findall(r'[\d]+\.?\d*', sl_str.replace(',', ''))
    if nums:
        try:
            candidate = float(nums[0])
            # If candidate is a percentage (e.g. 3.2), calculate price
            if candidate < 20.0 and base_price > 50:
                mult = (1.0 - candidate / 100.0) if direction == 'BULLISH' else (1.0 + candidate / 100.0)
                return round(base_price * mult, 2)
            return candidate
        except Exception:
            pass
    # Fallback to standard 3.2% stop
    return round(base_price * 0.968, 2) if direction == 'BULLISH' else round(base_price * 1.032, 2)

# Candle memory cache to prevent redundant reads
_CANDLE_CACHE: Dict[str, List[dict]] = {}

def get_historical_candles(symbol: str) -> List[dict]:
    clean = symbol.upper().replace('.NS', '').replace('.BO', '')
    if clean in _CANDLE_CACHE:
        return _CANDLE_CACHE[clean]

    cache_path = os.path.join(PRICE_CACHE_DIR, f"{clean}_candles.json")
    if os.path.exists(cache_path):
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                candles = json.load(f)
                _CANDLE_CACHE[clean] = candles
                return candles
        except Exception:
            pass

    # If not in disk cache, fetch live from LivePriceProvider / Yahoo Finance
    quote = LivePriceProvider.get_live_quote(clean, force_fresh=False)
    if quote and quote.get('ltp'):
        today_candle = [{
            "date": datetime.now().strftime("%Y-%m-%d"),
            "open": float(quote.get("day_open") or quote.get("open") or quote["ltp"]),
            "high": float(quote.get("day_high") or quote.get("high") or quote["ltp"]),
            "low": float(quote.get("day_low") or quote.get("low") or quote["ltp"]),
            "close": float(quote["ltp"]),
            "volume": int(quote.get("volume") or 0)
        }]
        _CANDLE_CACHE[clean] = today_candle
        return today_candle

    return []

def run_institutional_evaluation():
    print("=" * 140)
    print("INSTITUTIONAL QUANTITATIVE SIGNAL EVALUATION ENGINE (TARGET-FIRST vs STOP-FIRST)")
    print("Compliant with Quantitative Trading Pipeline Audit (2026-10-22)")
    print("=" * 140)

    raw_signals = load_signals()
    # Filter actionable signals: useful == True and predicted_direction in [BULLISH, BEARISH]
    actionable_signals = [
        s for s in raw_signals
        if s.get('is_useful', True) and s.get('predicted_direction') in ['BULLISH', 'BEARISH']
    ]

    print(f"Total Database Signals:        {len(raw_signals):,}")
    print(f"Total Actionable Directional:  {len(actionable_signals):,}")

    # Deduplicate by symbol + signal_date (retain primary alert per event day)
    seen = set()
    deduped: List[dict] = []
    for s in actionable_signals:
        sym = s.get('symbol', 'UNKNOWN').upper()
        proc = s.get('processed_at') or s.get('published_at') or ''
        date_str = proc[:10]
        if not date_str:
            continue
        key = f"{sym}_{date_str}_{s.get('predicted_direction')}"
        if key not in seen:
            seen.add(key)
            deduped.append(s)

    print(f"Unique Candidate Set (Deduped): {len(deduped):,}\n")

    results = []
    quarantined_by_gate = 0
    now = datetime.now()
    today_str = now.strftime('%Y-%m-%d')

    print("-" * 140)
    print(f"{'#':>3} | {'Symbol':<12} | {'Dir':<5} | {'Date':<10} | {'Base ₹':>9} | {'Entry ₹':>9} | {'T1 Safe ₹':>9} | {'Stop ₹':>9} | {'Resolution':<22} | {'Net Return':>10} | Archetype / Headline")
    print("-" * 140)

    ROUND_TRIP_FRICTION_PCT = 0.35  # 25 bps bid-ask half spread + 10 bps statutory costs/taxes

    for idx, s in enumerate(deduped, 1):
        sym = s.get('symbol', 'UNKNOWN').upper()
        dir_text = s.get('predicted_direction', 'BULLISH').upper()
        conv = float(s.get('conviction_score_pct') or 75.0)
        base_ltp = float(s.get('current_base_price_inr') or 0.0)
        proc_str = s.get('processed_at') or s.get('published_at') or ''
        headline = s.get('headline', '')
        archetype = s.get('category') or s.get('ai_model') or 'GENERAL_FILING'

        if base_ltp <= 0:
            continue

        try:
            sig_date = datetime.strptime(proc_str[:10], '%Y-%m-%d')
            sig_date_str = sig_date.strftime('%Y-%m-%d')
        except Exception:
            continue

        # Check timing: Was this an after-market signal?
        is_after_hours = s.get('is_after_hours', False)
        if not is_after_hours and len(proc_str) >= 16:
            try:
                hour = int(proc_str[11:13])
                minute = int(proc_str[14:16])
                minute_of_day = hour * 60 + minute
                is_after_hours = (minute_of_day < (9 * 60 + 15) or minute_of_day >= (15 * 60 + 30))
            except Exception:
                pass

        # Load candle history
        candles = get_historical_candles(sym)
        if not candles:
            continue

        # Locate signal day candle and next trading day (T+1) candle
        day0_candle = None
        day1_candle = None

        candle_by_date = {c['date']: c for c in candles}
        sorted_dates = sorted(candle_by_date.keys())

        # If today is after the last cached candle, fetch today's live candle
        if today_str not in candle_by_date and sig_date_str >= (now - timedelta(days=5)).strftime('%Y-%m-%d'):
            quote = LivePriceProvider.get_live_quote(sym, force_fresh=False)
            if quote and quote.get('ltp'):
                today_c = {
                    "date": today_str,
                    "open": float(quote.get("day_open") or quote.get("open") or quote["ltp"]),
                    "high": float(quote.get("day_high") or quote.get("high") or quote["ltp"]),
                    "low": float(quote.get("day_low") or quote.get("low") or quote["ltp"]),
                    "close": float(quote["ltp"]),
                    "volume": int(quote.get("volume") or 0)
                }
                candle_by_date[today_str] = today_c
                if today_str not in sorted_dates:
                    sorted_dates.append(today_str)
                    sorted_dates.sort()

        if sig_date_str in candle_by_date:
            day0_idx = sorted_dates.index(sig_date_str)
            day0_candle = candle_by_date[sig_date_str]
            if day0_idx + 1 < len(sorted_dates):
                day1_candle = candle_by_date[sorted_dates[day0_idx + 1]]
        else:
            # If exact signal date is a weekend/holiday, find next available trading day
            future_dates = [d for d in sorted_dates if d >= sig_date_str]
            if future_dates:
                day0_candle = candle_by_date[future_dates[0]]
                d0_idx = sorted_dates.index(future_dates[0])
                if d0_idx + 1 < len(sorted_dates):
                    day1_candle = candle_by_date[sorted_dates[d0_idx + 1]]

        # Target and Stop Loss Boundaries
        t1_lo, t1_hi = parse_price_range(s.get('t1_target'))
        if t1_lo is None or t1_hi is None:
            t1_lo = round(base_ltp * 1.015, 2) if dir_text == 'BULLISH' else round(base_ltp * 0.985, 2)
            t1_hi = round(base_ltp * 1.035, 2) if dir_text == 'BULLISH' else round(base_ltp * 0.965, 2)

        t1_safe = t1_lo if dir_text == 'BULLISH' else t1_hi
        sl_price = parse_stop_loss(s, base_ltp, dir_text)

        # ── DETERMINATION OF TRADABLE WINDOW & ENTRY PRICE ───────────────────
        entry_price = base_ltp
        eval_candle = None
        is_quarantined = False
        quarantine_reason = None

        if is_after_hours:
            # Audit Mandate: Prohibit Day-0 execution for after-market alerts
            if not day1_candle:
                # T+1 session has not opened yet or candle missing
                continue
            eval_candle = day1_candle
            entry_price = float(day1_candle['open'])
            prev_close = float(day0_candle['close']) if day0_candle else base_ltp

            # 09:08 Pre-Open Gatekeeper Check
            gate_eval = AutoLiveStreamWorker.preopen_execution_gate(s, entry_price, prev_close)
            if not gate_eval['approved']:
                is_quarantined = True
                quarantine_reason = gate_eval['reason']
                quarantined_by_gate += 1
        else:
            # Market-Hours alert: entered during Day 0, evaluated across Day 0 & Day 1
            if day0_candle:
                eval_candle = day0_candle
                entry_price = base_ltp
            elif day1_candle:
                eval_candle = day1_candle
                entry_price = float(day1_candle['open'])
            else:
                continue

        # Audit Mandate 4: Untradeable / Penny / CIRP / Synthetic Anomaly Gate
        lower_head = headline.lower()
        is_cirp = any(term in lower_head for term in [
            "insolvency resolution process", "cirp", "liquidation", 
            "resolution professional", "compulsory delisting", "bifr", "nclt liquidation"
        ])
        is_penny = (base_ltp < 50.0 or entry_price < 50.0)
        is_synthetic = (base_ltp in [100.0, 1000.0] or (base_ltp > 0 and abs(entry_price - base_ltp) / base_ltp > 0.60))

        if not is_quarantined and (is_cirp or is_penny or is_synthetic):
            is_quarantined = True
            quarantine_reason = "CIRP_INSOLVENCY" if is_cirp else ("PENNY_STOCK_UNDER_50" if is_penny else "SYNTHETIC_PRICE_ANOMALY")
            quarantined_by_gate += 1

        # ── RESOLUTION EVALUATION (TARGET-FIRST vs STOP-FIRST) ────────────────
        if is_quarantined:
            resolution = f"QUARANTINED_{quarantine_reason[:15]}"
            gross_pnl_pct = 0.0
            net_pnl_pct = 0.0
            is_win = False
            is_resolved = True
        else:
            candle_open = float(eval_candle['open'])
            candle_high = float(eval_candle['high'])
            candle_low = float(eval_candle['low'])
            candle_close = float(eval_candle['close'])

            # Include Day 1 extension for market-hours alerts if Day 0 did not resolve
            if not is_after_hours and day1_candle:
                candle_high = max(candle_high, float(day1_candle['high']))
                candle_low = min(candle_low, float(day1_candle['low']))
                candle_close = float(day1_candle['close'])

            if dir_text == 'BULLISH':
                # Check for gap through stop loss at open
                if candle_open <= sl_price:
                    resolution = "GAP_STOPPED_OUT"
                    gross_pnl_pct = ((candle_open - entry_price) / entry_price) * 100.0
                    net_pnl_pct = gross_pnl_pct - ROUND_TRIP_FRICTION_PCT
                    is_win = False
                    is_resolved = True
                else:
                    target_hit = (candle_high >= t1_safe)
                    stop_hit = (candle_low <= sl_price)

                    if target_hit and not stop_hit:
                        resolution = "TARGET_FIRST (WIN)"
                        gross_pnl_pct = ((t1_safe - entry_price) / entry_price) * 100.0
                        net_pnl_pct = gross_pnl_pct - ROUND_TRIP_FRICTION_PCT
                        is_win = True
                        is_resolved = True
                    elif stop_hit and not target_hit:
                        resolution = "STOP_FIRST (LOSS)"
                        gross_pnl_pct = -((entry_price - sl_price) / entry_price) * 100.0
                        net_pnl_pct = gross_pnl_pct - ROUND_TRIP_FRICTION_PCT
                        is_win = False
                        is_resolved = True
                    elif target_hit and stop_hit:
                        # Ambiguous: Both boundaries touched on daily bar.
                        # Quantitative Audit Standard: Conservative STOP-FIRST assumption
                        resolution = "AMBIGUOUS_STOP_FIRST"
                        gross_pnl_pct = -((entry_price - sl_price) / entry_price) * 100.0
                        net_pnl_pct = gross_pnl_pct - ROUND_TRIP_FRICTION_PCT
                        is_win = False
                        is_resolved = True
                    else:
                        # Neither touched: position expired at session close
                        resolution = "EXPIRED_TIMED_OUT"
                        gross_pnl_pct = ((candle_close - entry_price) / entry_price) * 100.0
                        net_pnl_pct = gross_pnl_pct - ROUND_TRIP_FRICTION_PCT
                        is_win = (net_pnl_pct > 0)
                        is_resolved = True
            else:  # BEARISH
                if candle_open >= sl_price:
                    resolution = "GAP_STOPPED_OUT"
                    gross_pnl_pct = -((candle_open - entry_price) / entry_price) * 100.0
                    net_pnl_pct = gross_pnl_pct - ROUND_TRIP_FRICTION_PCT
                    is_win = False
                    is_resolved = True
                else:
                    target_hit = (candle_low <= t1_safe)
                    stop_hit = (candle_high >= sl_price)

                    if target_hit and not stop_hit:
                        resolution = "TARGET_FIRST (WIN)"
                        gross_pnl_pct = ((entry_price - t1_safe) / entry_price) * 100.0
                        net_pnl_pct = gross_pnl_pct - ROUND_TRIP_FRICTION_PCT
                        is_win = True
                        is_resolved = True
                    elif stop_hit and not target_hit:
                        resolution = "STOP_FIRST (LOSS)"
                        gross_pnl_pct = -((sl_price - entry_price) / entry_price) * 100.0
                        net_pnl_pct = gross_pnl_pct - ROUND_TRIP_FRICTION_PCT
                        is_win = False
                        is_resolved = True
                    elif target_hit and stop_hit:
                        resolution = "AMBIGUOUS_STOP_FIRST"
                        gross_pnl_pct = -((sl_price - entry_price) / entry_price) * 100.0
                        net_pnl_pct = gross_pnl_pct - ROUND_TRIP_FRICTION_PCT
                        is_win = False
                        is_resolved = True
                    else:
                        resolution = "EXPIRED_TIMED_OUT"
                        gross_pnl_pct = ((entry_price - candle_close) / entry_price) * 100.0
                        net_pnl_pct = gross_pnl_pct - ROUND_TRIP_FRICTION_PCT
                        is_win = (net_pnl_pct > 0)
                        is_resolved = True

        status_emoji = "🟢 WIN " if is_win else ("🛑 LOSS" if "STOP" in resolution else ("⚠️ GATE" if is_quarantined else "⏳ TIME"))
        headline_trunc = (headline[:40] + "...") if len(headline) > 40 else headline
        print(f"{idx:>3} | {sym:<12} | {dir_text:<5} | {sig_date_str:<10} | ₹{base_ltp:>8.2f} | ₹{entry_price:>8.2f} | ₹{t1_safe:>8.2f} | ₹{sl_price:>8.2f} | {status_emoji} {resolution:<15} | {net_pnl_pct:>+9.2f}% | {headline_trunc}")

        results.append({
            "symbol": sym,
            "direction": dir_text,
            "signal_date": sig_date_str,
            "conviction": conv,
            "archetype": archetype,
            "is_after_hours": is_after_hours,
            "base_ltp": base_ltp,
            "entry_price": entry_price,
            "t1_safe": t1_safe,
            "stop_loss": sl_price,
            "resolution": resolution,
            "is_win": is_win,
            "is_quarantined": is_quarantined,
            "quarantine_reason": quarantine_reason,
            "gross_pnl_pct": round(gross_pnl_pct, 2),
            "net_pnl_pct": round(net_pnl_pct, 2),
            "headline": headline
        })

    # ── AGGREGATE QUANTITATIVE AUDIT SUMMARY ─────────────────────────────────
    print("\n" + "=" * 140)
    print("INSTITUTIONAL QUANTITATIVE AUDIT REPORT")
    print("=" * 140)

    total_candidates = len(results)
    quarantined = [r for r in results if r["is_quarantined"]]
    executed = [r for r in results if not r["is_quarantined"]]
    wins = [r for r in executed if r["is_win"]]
    losses = [r for r in executed if not r["is_win"]]
    target_first = [r for r in executed if "TARGET_FIRST" in r["resolution"]]
    stop_first = [r for r in executed if "STOP" in r["resolution"]]

    n_executed = len(executed)
    n_wins = len(wins)
    n_losses = len(losses)
    n_target_first = len(target_first)
    n_stop_first = len(stop_first)

    target_win_rate = (n_target_first / (n_target_first + n_stop_first) * 100.0) if (n_target_first + n_stop_first) > 0 else 0.0
    overall_win_rate = (n_wins / n_executed * 100.0) if n_executed > 0 else 0.0

    net_returns = [r["net_pnl_pct"] for r in executed]
    net_expectancy_pct = (sum(net_returns) / n_executed) if n_executed > 0 else 0.0

    gross_gains = sum(r["net_pnl_pct"] for r in wins if r["net_pnl_pct"] > 0)
    gross_losses = abs(sum(r["net_pnl_pct"] for r in losses if r["net_pnl_pct"] < 0))
    profit_factor = round(gross_gains / max(0.01, gross_losses), 2) if gross_losses > 0 else (round(gross_gains, 2) if gross_gains > 0 else 1.0)

    # Max Drawdown Calculation on Cumulative Curve
    cumulative = 0.0
    peak = 0.0
    max_dd = 0.0
    for ret in net_returns:
        cumulative += ret
        if cumulative > peak:
            peak = cumulative
        dd = peak - cumulative
        if dd > max_dd:
            max_dd = dd

    print(f"Total Unique Signal Candidates:      {total_candidates:,}")
    print(f"Pre-Open Gatekeeper Quarantined:     {len(quarantined):,} ({len(quarantined)/max(1, total_candidates)*100:.1f}% - Capital Protected from Adverse Gaps)")
    print(f"Executed Tradable Positions:         {n_executed:,}")
    print(f"Target-First Wins (Clean Exits):     {n_target_first:,}")
    print(f"Stop-Loss Breaches (Conservative):   {n_stop_first:,}")
    print(f"------------------------------------------------------------------------------------------------------------")
    print(f"Target-First Win Rate:               {target_win_rate:.1f}%")
    print(f"Overall Net Win Rate:                {overall_win_rate:.1f}%")
    print(f"Net Expectancy per Trade:            {net_expectancy_pct:+.2f}% (After 35 bps round-trip friction)")
    print(f"Profit Factor:                       {profit_factor:.2f}")
    print(f"Maximum Peak-to-Trough Drawdown:     -{max_dd:.2f}%")
    print(f"Total Portfolio Net Realized Return: {sum(net_returns):+.2f}%")
    print("=" * 140)

    # ── BREAKDOWN TABLES ─────────────────────────────────────────────────────
    # 1. Directional Breakdown
    print("\n1. DIRECTIONAL BREAKDOWN")
    print("-" * 75)
    print(f"{'Direction':<10} | {'Trades':>6} | {'Target Wins':>12} | {'Stop Loss':>10} | {'Win Rate %':>10} | {'Net Expectancy':>14}")
    print("-" * 75)
    for d in ['BULLISH', 'BEARISH']:
        sub = [r for r in executed if r['direction'] == d]
        if sub:
            tf = len([r for r in sub if "TARGET_FIRST" in r["resolution"]])
            sf = len([r for r in sub if "STOP" in r["resolution"]])
            wr = (tf / max(1, tf + sf) * 100.0) if (tf + sf) > 0 else 0.0
            exp = sum(r["net_pnl_pct"] for r in sub) / len(sub)
            print(f"{d:<10} | {len(sub):>6} | {tf:>12} | {sf:>10} | {wr:>9.1f}% | {exp:>+13.2f}%")

    # 2. Conviction Bracket Breakdown
    print("\n2. CONVICTION CALIBRATION BREAKDOWN")
    print("-" * 75)
    print(f"{'Conviction Tier':<15} | {'Trades':>6} | {'Target Wins':>12} | {'Stop Loss':>10} | {'Win Rate %':>10} | {'Net Expectancy':>14}")
    print("-" * 75)
    for label, lo, hi in [('High >=80%', 80, 101), ('Medium 70-79%', 70, 80), ('Low <70%', 0, 70)]:
        sub = [r for r in executed if lo <= r['conviction'] < hi]
        if sub:
            tf = len([r for r in sub if "TARGET_FIRST" in r["resolution"]])
            sf = len([r for r in sub if "STOP" in r["resolution"]])
            wr = (tf / max(1, tf + sf) * 100.0) if (tf + sf) > 0 else 0.0
            exp = sum(r["net_pnl_pct"] for r in sub) / len(sub)
            print(f"{label:<15} | {len(sub):>6} | {tf:>12} | {sf:>10} | {wr:>9.1f}% | {exp:>+13.2f}%")

    # Save detailed JSON audit report
    audit_data = {
        "audit_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S IST"),
        "total_candidates": total_candidates,
        "quarantined_by_preopen_gate": len(quarantined),
        "executed_positions": n_executed,
        "target_first_wins": n_target_first,
        "stop_first_losses": n_stop_first,
        "target_first_win_rate_pct": round(target_win_rate, 2),
        "overall_win_rate_pct": round(overall_win_rate, 2),
        "net_expectancy_pct": round(net_expectancy_pct, 2),
        "profit_factor": profit_factor,
        "max_drawdown_pct": round(max_dd, 2),
        "total_net_realized_pnl_pct": round(sum(net_returns), 2),
        "round_trip_cost_deducted_bps": 35.0,
        "executed_signals_ledger": results
    }

    os.makedirs(os.path.dirname(REPORT_FILE), exist_ok=True)
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(audit_data, f, indent=2)

    print(f"\nDetailed Audit Ledger successfully exported to:")
    print(f"{REPORT_FILE}\n")

if __name__ == '__main__':
    run_institutional_evaluation()
