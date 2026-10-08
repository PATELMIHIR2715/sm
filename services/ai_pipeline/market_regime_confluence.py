from typing import Dict, Any

class MarketRegimeConfluenceEngine:
    """
    Beta-Adjusted Market Regime & Microstructure Engine:
    
    Prevents false breakouts and unrealistic single-day target projections by:
    1. Measuring live NIFTY 50 index momentum and market breadth.
    2. Adjusting single-day catalyst Alpha for Stock Beta:
       Net Expected T+1 Return = News_Alpha + (Beta * Nifty_Delta)
    3. If Market Drag is negative (Nifty in pullback), automatically switches strategy
       from 'Immediate Market Buy' to 'Intraday Dip Accumulation / T+5 Horizon'.
    """

    STOCK_BETAS = {
        "HAL": 1.45,
        "BEL": 1.30,
        "JSWSTEEL": 1.35,
        "TATASTEEL": 1.40,
        "ASIANPAINT": 0.85,
        "WIPRO": 0.90,
        "INFY": 0.95,
        "TCS": 0.75,
        "M&M": 1.20,
        "ICICIBANK": 1.15,
        "HDFCBANK": 0.95,
        "DEFAULT": 1.10
    }

    @classmethod
    def calculate_beta_adjusted_target(
        cls,
        symbol: str,
        ltp: float,
        raw_target_pct: float,
        direction: str,
        nifty_change_pct: float
    ) -> Dict[str, Any]:
        beta = cls.STOCK_BETAS.get(symbol.upper(), cls.STOCK_BETAS["DEFAULT"])
        is_bull = direction == "BULLISH"
        
        # Beta Market Effect on 1-Day Move
        market_drag_pct = round(beta * nifty_change_pct, 2)
        
        # Net Adjusted T+1 Return %
        if is_bull:
            net_t1_pct = round(raw_target_pct + market_drag_pct, 2)
        else:
            # For shorts, a falling market helps the trade!
            net_t1_pct = round(raw_target_pct + abs(market_drag_pct), 2)

        # Microstructure Strategy Recommendation
        if is_bull and nifty_change_pct < -0.40:
            strategy = "ACCUMULATE ON INTRADAY DIP (MARKET HEADWIND - T+5 SWING)"
            target_confidence_note = "1-Day move suppressed by broad market selling. Target delayed to T+5 horizon."
            # Floor net move to realistic bounds under market drag
            net_t1_pct = max(0.20, net_t1_pct)
        elif is_bull and nifty_change_pct >= 0.20:
            strategy = "STRONG MOMENTUM BREAKOUT (CONFLUENCE ALIGNED)"
            target_confidence_note = "Bullish catalyst backed by green market tailwinds."
        elif not is_bull and nifty_change_pct < 0:
            strategy = "HIGH CONVICTION TACTICAL SHORT (MARKET TAILWIND FOR SHORT)"
            target_confidence_note = "Bearish stock fundamental headwind amplified by broader market selling."
        else:
            strategy = "STANDARD EXECUTION"
            target_confidence_note = "Neutral market backdrop."

        # Calculate exact price corridor
        mult = 1.0 if is_bull else -1.0
        t1_min_price = round(ltp * (1 + (mult * max(0.5, net_t1_pct * 0.7)) / 100), 2)
        t1_max_price = round(ltp * (1 + (mult * max(1.2, net_t1_pct * 1.3)) / 100), 2)

        return {
            "symbol": symbol.upper(),
            "stock_beta": beta,
            "nifty_change_pct": nifty_change_pct,
            "market_drag_contribution_pct": market_drag_pct,
            "raw_catalyst_alpha_pct": raw_target_pct,
            "net_beta_adjusted_t1_pct": net_t1_pct,
            "recommended_execution_strategy": strategy,
            "target_confidence_note": target_confidence_note,
            "adjusted_t1_corridor_inr": f"₹{min(t1_min_price, t1_max_price):,.2f} - ₹{max(t1_min_price, t1_max_price):,.2f}"
        }

if __name__ == "__main__":
    print("Testing MarketRegimeConfluenceEngine...")
    # Test case: HAL with +4.5% news, but Nifty down -1.2%
    res = MarketRegimeConfluenceEngine.calculate_beta_adjusted_target(
        symbol="HAL",
        ltp=4800.0,
        raw_target_pct=4.5,
        direction="BULLISH",
        nifty_change_pct=-1.29
    )
    import json
    print(json.dumps(res, indent=2))
