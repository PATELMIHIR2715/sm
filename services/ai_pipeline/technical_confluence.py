import math
from typing import Dict, Any

class TechnicalConfluenceEngine:
    """
    Multi-Timeframe Technical Confluence Engine:
    Validates fundamental/news signals against technical trend filters (200 EMA, 50 EMA, 14 RSI).
    Prevents false breakouts and chasers (e.g. buying good news into a downtrending stock).
    """

    def analyze_confluence(self, ltp: float, direction: str, news_confidence: float, technical_meta: Dict[str, Any] = None) -> Dict[str, Any]:
        tech = technical_meta or {}
        ema_200 = tech.get("ema_200", ltp * 0.95 if direction == "BULLISH" else ltp * 1.05)
        ema_50 = tech.get("ema_50", ltp * 0.98 if direction == "BULLISH" else ltp * 1.02)
        rsi_14 = tech.get("rsi_14", 55.0)
        nifty_day_chg = tech.get("nifty_change_pct", 0.20)

        confluence_points = 0
        max_points = 100
        flags = []

        is_bull = direction == "BULLISH"
        is_bear = direction == "BEARISH"

        # 1. Long-term Trend Alignment (200 EMA) - 30 Points
        if is_bull:
            if ltp >= ema_200:
                confluence_points += 30
                flags.append("Above 200 EMA (Structural Bull Market)")
            else:
                confluence_points += 5
                flags.append("WARNING: Trading Below 200 EMA (Counter-Trend Long)")
        elif is_bear:
            if ltp <= ema_200:
                confluence_points += 30
                flags.append("Below 200 EMA (Structural Downtrend)")
            else:
                confluence_points += 5
                flags.append("WARNING: Trading Above 200 EMA (Counter-Trend Short)")

        # 2. Medium-term Momentum (50 EMA) - 30 Points
        if is_bull:
            if ltp >= ema_50:
                confluence_points += 30
                flags.append("Above 50 EMA (Short-term Momentum Intact)")
            else:
                confluence_points += 10
        elif is_bear:
            if ltp <= ema_50:
                confluence_points += 30
                flags.append("Below 50 EMA (Short-term Weakness Intact)")
            else:
                confluence_points += 10

        # 3. Momentum Oscillator (14 RSI) - 20 Points
        if is_bull:
            if 40.0 <= rsi_14 <= 70.0:
                confluence_points += 20
                flags.append("Healthy RSI Range (40-70)")
            elif rsi_14 > 75.0:
                confluence_points += 5
                flags.append("CAUTION: RSI Overbought (>75) - Risk of Mean Reversion")
            else:
                confluence_points += 15
        elif is_bear:
            if 30.0 <= rsi_14 <= 60.0:
                confluence_points += 20
                flags.append("Healthy Bearish RSI (30-60)")
            elif rsi_14 < 25.0:
                confluence_points += 5
                flags.append("CAUTION: RSI Oversold (<25) - Risk of Short Squeeze")
            else:
                confluence_points += 15

        # 4. Market Breadth / Index Alignment - 20 Points
        if is_bull:
            if nifty_day_chg >= 0.0:
                confluence_points += 20
                flags.append("Broad Market Tailwinds (Nifty Positive)")
            else:
                confluence_points += 8
                flags.append("Nifty Headwind (Broader Market Selling)")
        elif is_bear:
            if nifty_day_chg <= 0.0:
                confluence_points += 20
                flags.append("Broad Market Selloff (Nifty Negative)")
            else:
                confluence_points += 8
                flags.append("Nifty Resilient (Counter-market Short)")

        # Calculate Confluence Multiplier & Adjusted Conviction
        confluence_pct = round(confluence_points, 1)
        multiplier = round(0.60 + (confluence_points / 100.0) * 0.50, 2) # 0.60x to 1.10x
        final_adjusted_conviction = min(98.0, round(news_confidence * multiplier, 1))

        # Trade Grade
        if confluence_pct >= 80:
            trade_grade = "A+ (HIGH CONFLUENCE)"
            size_recommendation = "100% STANDARD ALLOCATION"
        elif confluence_pct >= 60:
            trade_grade = "B (MODERATE CONFLUENCE)"
            size_recommendation = "75% ALLOCATION"
        else:
            trade_grade = "C (COUNTER-TREND CONFLICT)"
            size_recommendation = "50% DEFENSIVE ALLOCATION OR ABSTAIN"

        return {
            "confluence_score_pct": confluence_pct,
            "confluence_grade": trade_grade,
            "confluence_multiplier": multiplier,
            "final_adjusted_conviction": final_adjusted_conviction,
            "size_recommendation": size_recommendation,
            "technical_flags": flags,
            "indicators": {
                "ltp": ltp,
                "ema_200": round(ema_200, 2),
                "ema_50": round(ema_50, 2),
                "rsi_14": round(rsi_14, 1),
                "nifty_trend": "BULLISH" if nifty_day_chg >= 0 else "BEARISH"
            }
        }

if __name__ == "__main__":
    confluence = TechnicalConfluenceEngine()
    res = confluence.analyze_confluence(
        ltp=4741.80,
        direction="BULLISH",
        news_confidence=88.0,
        technical_meta={"ema_200": 4200.0, "ema_50": 4550.0, "rsi_14": 62.5, "nifty_change_pct": 0.35}
    )
    import json
    print("Technical Confluence Analysis for HAL:")
    print(json.dumps(res, indent=2))
