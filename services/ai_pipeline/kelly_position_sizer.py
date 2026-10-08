import math
from typing import Dict, Any

class KellyPositionSizer:
    """
    Volatility-Adjusted Fractional Kelly Criterion Position Sizer:
    
    Dynamically scales position capital between INR 5,000 and INR 25,000 based on:
    1. Historical Win Probability (p) from RAG Vector Archetype
    2. Reward-to-Risk Payoff Ratio (b = Target Gain / Stop Loss Risk)
    3. Fractional Half-Kelly factor (0.5x) for draw-down protection
    """

    def __init__(self, portfolio_capital: float = 100000.0, max_trade_cap_pct: float = 25.0, min_trade_inr: float = 5000.0):
        self.portfolio_capital = portfolio_capital
        self.max_trade_cap_pct = max_trade_cap_pct
        self.min_trade_inr = min_trade_inr

    def calculate_sizing(self, ltp: float, win_prob: float, target_pct: float, stop_loss_pct: float, confluence_multiplier: float = 1.0) -> Dict[str, Any]:
        p = max(0.51, min(0.95, win_prob))
        q = 1.0 - p

        # Reward to risk ratio (b)
        t_gain = max(0.5, abs(target_pct))
        sl_risk = max(0.5, abs(stop_loss_pct))
        b = t_gain / sl_risk

        # Full Kelly Formula: f* = (p*b - q) / b
        raw_kelly = (p * b - q) / b if b > 0 else 0.10
        raw_kelly = max(0.05, min(0.40, raw_kelly))

        # Half-Kelly for Institutional Risk Safety (prevents over-betting)
        half_kelly = raw_kelly * 0.5 * confluence_multiplier

        # Optimal Allocation in INR
        target_allocation_pct = min(self.max_trade_cap_pct, max(5.0, half_kelly * 100.0))
        optimal_capital_inr = round(self.portfolio_capital * (target_allocation_pct / 100.0), 2)
        optimal_capital_inr = max(self.min_trade_inr, optimal_capital_inr)

        # Calculate exact number of shares
        shares_qty = max(1, math.floor(optimal_capital_inr / ltp))
        actual_invested_inr = round(shares_qty * ltp, 2)
        
        # Max Rupee Risk on Stop-Loss
        max_loss_inr = round(actual_invested_inr * (sl_risk / 100.0), 2)
        target_profit_inr = round(actual_invested_inr * (t_gain / 100.0), 2)

        return {
            "portfolio_capital_inr": self.portfolio_capital,
            "optimal_allocation_pct": round(target_allocation_pct, 2),
            "allocated_capital_inr": actual_invested_inr,
            "shares_quantity": shares_qty,
            "win_probability_p": round(p, 2),
            "reward_risk_ratio_b": round(b, 2),
            "target_profit_inr": target_profit_inr,
            "max_stop_loss_risk_inr": max_loss_inr,
            "risk_profile": "AGGRESSIVE SIZE (HIGH CONVICTION)" if target_allocation_pct >= 18.0 else ("BALANCED SIZE" if target_allocation_pct >= 12.0 else "DEFENSIVE SIZE")
        }

if __name__ == "__main__":
    sizer = KellyPositionSizer(portfolio_capital=100000.0)
    sizing = sizer.calculate_sizing(
        ltp=4741.80,
        win_prob=0.88,
        target_pct=5.39,
        stop_loss_pct=3.84,
        confluence_multiplier=1.1
    )
    import json
    print("Kelly Position Sizing Output for HAL:")
    print(json.dumps(sizing, indent=2))
