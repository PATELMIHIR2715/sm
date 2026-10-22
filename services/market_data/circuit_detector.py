"""
Circuit Breaker & Freeze Detector for Indian Equities (NSE/BSE).

Detects whether a stock is currently locked at its Upper Circuit (UC) or Lower Circuit (LC)
price band (2%, 5%, 10%, 20%). When locked, zero counterparty liquidity exists in the order book,
preventing execution.
"""
from typing import Dict, Any, Optional

class CircuitFreezeDetector:
    CIRCUIT_BANDS = [2.0, 5.0, 10.0, 20.0]

    @classmethod
    def detect_circuit_status(cls, quote: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        if not quote:
            return {
                "is_circuit_locked": False,
                "circuit_type": "NORMAL",
                "circuit_band_pct": None,
                "warning_badge": None,
                "trading_advice": "Normal market liquidity."
            }

        ltp = float(quote.get("ltp") or 0.0)
        day_high = float(quote.get("day_high") or quote.get("high") or ltp)
        day_low = float(quote.get("day_low") or quote.get("low") or ltp)
        chg_pct = float(quote.get("day_change_pct") or quote.get("change_pct") or 0.0)

        # Upper Circuit Detection
        if chg_pct > 0 and ltp > 0:
            is_pinned_at_high = abs(ltp - day_high) <= (ltp * 0.0015)
            for band in cls.CIRCUIT_BANDS:
                if abs(chg_pct - band) <= 0.25 and is_pinned_at_high:
                    return {
                        "is_circuit_locked": True,
                        "circuit_type": "UPPER_CIRCUIT",
                        "circuit_band_pct": band,
                        "warning_badge": f"⚠️ LOCKED AT UPPER CIRCUIT (+{band:.1f}%)",
                        "trading_advice": f"Stock is locked at +{band:.1f}% Upper Circuit. No sellers available; do not chase with market orders. Watch for circuit unlock or tomorrow's opening auction."
                    }

        # Lower Circuit Detection
        if chg_pct < 0 and ltp > 0:
            is_pinned_at_low = abs(ltp - day_low) <= (ltp * 0.0015)
            for band in cls.CIRCUIT_BANDS:
                if abs(abs(chg_pct) - band) <= 0.25 and is_pinned_at_low:
                    return {
                        "is_circuit_locked": True,
                        "circuit_type": "LOWER_CIRCUIT",
                        "circuit_band_pct": band,
                        "warning_badge": f"⚠️ LOCKED AT LOWER CIRCUIT (-{band:.1f}%)",
                        "trading_advice": f"Stock is locked at -{band:.1f}% Lower Circuit. No buyers available; execution blocked until circuit band expands."
                    }

        return {
            "is_circuit_locked": False,
            "circuit_type": "NORMAL",
            "circuit_band_pct": None,
            "warning_badge": None,
            "trading_advice": "Normal market liquidity active."
        }
