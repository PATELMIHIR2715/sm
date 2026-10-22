"""
Price Action & Chart Pattern Calibration Engine:
Validates AI/sentiment predictions against 20-30 day price action geometry,
candlestick rejection wicks, overhead resistance walls, and measured move ceilings.
Prevents over-optimistic target chasing and front-runs institutional supply zones.
"""

import time
import math
from typing import Dict, Any, Optional, List
import yfinance as yf
import pandas as pd

class PriceActionPatternCalibrator:
    CACHE_TTL_SECONDS = 300  # 5-minute cache for daily candles
    _history_cache: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def get_ticker_symbol(cls, symbol: str) -> str:
        clean = symbol.strip().upper().replace(".NS", "").replace(".BO", "")
        return f"{clean}.NS"

    @classmethod
    def fetch_historical_candles(cls, symbol: str, period: str = "1mo") -> Optional[pd.DataFrame]:
        """
        Fetches genuine daily historical OHLCV candles from Yahoo Finance.
        Caches in-memory to prevent repeated network calls within 5 minutes.
        """
        clean = symbol.strip().upper().replace(".NS", "").replace(".BO", "")
        now = time.time()

        if clean in cls._history_cache:
            entry = cls._history_cache[clean]
            if now - entry["cached_at"] < cls.CACHE_TTL_SECONDS:
                return entry["df"]

        # Try NSE (.NS) then BSE (.BO)
        for suffix in [".NS", ".BO"]:
            candidate = f"{clean}{suffix}"
            try:
                tk = yf.Ticker(candidate)
                df = tk.history(period=period, interval="1d", timeout=3.0)
                if df is not None and not df.empty and len(df) >= 5:
                    cls._history_cache[clean] = {
                        "cached_at": now,
                        "df": df
                    }
                    return df
            except Exception:
                continue

        # If expired cache exists, return as graceful fallback
        if clean in cls._history_cache:
            return cls._history_cache[clean]["df"]

        return None

    @classmethod
    def analyze_price_structure(cls, symbol: str, current_ltp: float) -> Dict[str, Any]:
        """
        Extracts key price action geometry:
        1. 20-Day Overhead Resistance (Swing High Wall)
        2. 20-Day Major Support (Swing Low Floor)
        3. Candlestick Rejection Patterns (Shooting Star, Hammer, Engulfing)
        4. Volume Confirmation (vs 20D SMA Volume)
        5. Consolidation Measured Move Ceiling
        """
        df = cls.fetch_historical_candles(symbol, period="2mo")

        # Fallback if market data is unreachable or insufficient
        if df is None or len(df) < 5:
            return {
                "status": "FALLBACK_DATA",
                "symbol": symbol.upper(),
                "overhead_resistance": round(current_ltp * 1.05, 2),
                "major_support": round(current_ltp * 0.95, 2),
                "pattern_signal": "NEUTRAL",
                "pattern_flags": [],
                "volume_expansion_ratio": 1.0,
                "measured_ceiling": round(current_ltp * 1.08, 2),
                "is_near_resistance": False,
                "resistance_distance_pct": 5.0
            }

        # Analyze past completed sessions (excluding in-flight live candle if present)
        hist = df.iloc[:-1] if len(df) > 10 else df
        recent_20 = hist.tail(20)

        overhead_resistance = float(recent_20["High"].max())
        major_support = float(recent_20["Low"].min())

        # Distance to resistance
        resistance_distance_pct = round(((overhead_resistance - current_ltp) / current_ltp) * 100, 2) if current_ltp > 0 else 0.0
        is_near_resistance = 0.0 <= resistance_distance_pct <= 1.5

        # Pattern Height & Measured Move
        pattern_height = max(1.0, overhead_resistance - major_support)
        measured_ceiling = round(overhead_resistance + (pattern_height * 0.618), 2)

        # Volume Confirmation Ratio
        avg_vol_20 = float(recent_20["Volume"].mean())
        latest_vol = float(df["Volume"].iloc[-1])
        volume_expansion_ratio = round(latest_vol / avg_vol_20, 2) if avg_vol_20 > 0 else 1.0

        # Candlestick Pattern Detection on latest completed candle
        last_candle = hist.iloc[-1]
        prev_candle = hist.iloc[-2] if len(hist) > 1 else last_candle

        o1, h1, l1, c1 = float(last_candle["Open"]), float(last_candle["High"]), float(last_candle["Low"]), float(last_candle["Close"])
        o0, h0, l0, c0 = float(prev_candle["Open"]), float(prev_candle["High"]), float(prev_candle["Low"]), float(prev_candle["Close"])

        candle_range = max(0.01, h1 - l1)
        body_size = abs(c1 - o1)
        upper_wick = h1 - max(o1, c1)
        lower_wick = min(o1, c1) - l1

        pattern_signal = "NEUTRAL"
        pattern_flags: List[str] = []

        # 1. Bearish Shooting Star / Upper Wick Rejection
        if upper_wick >= 0.50 * candle_range and body_size <= 0.35 * candle_range:
            pattern_signal = "BEARISH_EXHAUSTION_WICK"
            pattern_flags.append(f"Upper Wick Rejection ({upper_wick / candle_range * 100:.0f}% wick) signals heavy overhead selling.")

        # 2. Bullish Hammer / Pin Bar
        elif lower_wick >= 0.55 * candle_range and body_size <= 0.35 * candle_range:
            pattern_signal = "BULLISH_HAMMER"
            pattern_flags.append(f"Bullish Hammer Pin-Bar ({lower_wick / candle_range * 100:.0f}% lower wick) signals strong dip buying.")

        # 3. Bullish Engulfing
        elif c0 < o0 and c1 > o1 and c1 >= o0 and o1 <= c0:
            pattern_signal = "BULLISH_ENGULFING"
            pattern_flags.append("Bullish Engulfing pattern confirms sudden buyer dominance.")

        # 4. Bearish Engulfing
        elif c0 > o0 and c1 < o1 and o1 >= c0 and c1 <= o0:
            pattern_signal = "BEARISH_ENGULFING"
            pattern_flags.append("Bearish Engulfing candle indicates aggressive institutional distribution.")

        # 5. Check Double Top Near Resistance
        recent_peaks = hist["High"].nlargest(2).values
        if len(recent_peaks) >= 2 and abs(recent_peaks[0] - recent_peaks[1]) / recent_peaks[0] < 0.012:
            pattern_flags.append(f"Double Top Resistance structure confirmed near ₹{overhead_resistance:,.2f}.")

        return {
            "status": "SUCCESS",
            "symbol": symbol.upper(),
            "overhead_resistance": round(overhead_resistance, 2),
            "major_support": round(major_support, 2),
            "resistance_distance_pct": resistance_distance_pct,
            "is_near_resistance": is_near_resistance,
            "pattern_signal": pattern_signal,
            "pattern_flags": pattern_flags,
            "volume_expansion_ratio": volume_expansion_ratio,
            "measured_ceiling": measured_ceiling
        }

    @classmethod
    def calibrate_targets(
        cls,
        symbol: str,
        base_ltp: float,
        predicted_direction: str,
        raw_t1_target_inr: float,
        raw_t5_target_inr: float,
        sl_price_inr: float
    ) -> Dict[str, Any]:
        """
        Cross-checks raw targets against price action geometry.
        Clamps targets right below resistance walls and adjusts stop-losses.
        """
        pa = cls.analyze_price_structure(symbol, base_ltp)
        is_bull = predicted_direction == "BULLISH"

        calibrated_t1 = raw_t1_target_inr
        calibrated_t5 = raw_t5_target_inr
        calibrated_sl = sl_price_inr
        mitigations = []
        warnings = []

        overhead_res = pa["overhead_resistance"]
        major_supp = pa["major_support"]
        pattern_sig = pa["pattern_signal"]

        if is_bull:
            # 1. Resistance Wall Clamping: Front-run the resistance by 0.8%
            # If AI target attempts to shoot through the 20-day high without confirming a breakout
            if overhead_res > base_ltp and raw_t1_target_inr >= overhead_res:
                safe_target = round(overhead_res * 0.992, 2)
                if safe_target > base_ltp:
                    calibrated_t1 = safe_target
                    mitigations.append(f"Clamped T+1 target from ₹{raw_t1_target_inr:,.2f} to ₹{calibrated_t1:,.2f} (Front-running 20D Resistance at ₹{overhead_res:,.2f}).")
                    warnings.append(f"Overhead 20-Day Pattern Wall at ₹{overhead_res:,.2f}. High probability of seller reaction.")

            # 2. Upper Wick Exhaustion Rejection Discount
            if pattern_sig == "BEARISH_EXHAUSTION_WICK":
                gain = calibrated_t1 - base_ltp
                if gain > 0:
                    discounted_gain = gain * 0.80  # 20% friction discount
                    calibrated_t1 = round(base_ltp + discounted_gain, 2)
                    mitigations.append("Applied 20% target friction discount due to Upper-Wick Exhaustion Candle.")
                    warnings.append("Recent candle rejected higher prices with >50% upper wick.")

            # 3. Pattern Measured Move Clamping on T+5 Swing
            measured_ceiling = pa["measured_ceiling"]
            if calibrated_t5 > measured_ceiling:
                calibrated_t5 = measured_ceiling
                mitigations.append(f"Capped T+5 multi-day swing target to Pattern Measured Ceiling (₹{measured_ceiling:,.2f}).")

            # 4. Pattern-Anchored Stop Loss (Just below 20-day Support Floor)
            pattern_sl = round(major_supp * 0.995, 2)
            if pattern_sl > 0 and pattern_sl < base_ltp:
                # Use the tighter / more structural stop loss
                if abs(base_ltp - pattern_sl) / base_ltp <= 0.035:  # within 3.5%
                    calibrated_sl = max(calibrated_sl, pattern_sl)
                    mitigations.append(f"Anchored Stop-Loss to Structural Support Floor at ₹{calibrated_sl:,.2f}.")

        # Dual-Tier Targets
        t1_high_probability = calibrated_t1
        t2_expansion_runner = round(overhead_res * 1.025, 2) if is_bull and overhead_res > base_ltp else calibrated_t5

        return {
            "price_action_meta": pa,
            "raw_t1_target": raw_t1_target_inr,
            "calibrated_t1_target": calibrated_t1,
            "raw_t5_target": raw_t5_target_inr,
            "calibrated_t5_target": calibrated_t5,
            "dual_tier_targets": {
                "t1_conservative_frontrun": t1_high_probability,
                "t2_breakout_expansion": t2_expansion_runner
            },
            "calibrated_stop_loss": calibrated_sl,
            "is_calibrated": calibrated_t1 != raw_t1_target_inr or calibrated_t5 != raw_t5_target_inr,
            "mitigations": mitigations,
            "warnings": warnings
        }
