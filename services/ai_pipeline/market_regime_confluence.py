from dataclasses import dataclass
from typing import Dict, Any, Optional

@dataclass(frozen=True)
class MarketState:
    nifty_return_1d: float
    nifty_return_3d: float
    sector_return_1d: float
    india_vix: float
    vix_change_pct: float

class MarketRegimeConfluenceEngine:
    """
    Beta-Adjusted Market Regime & Microstructure Engine:
    
    Prevents false breakouts and unrealistic single-day target projections by:
    1. Measuring live NIFTY 50 index momentum and market breadth.
    2. Adjusting single-day catalyst Alpha for Stock Beta:
       Net Expected T+1 Return = News_Alpha + (Beta * Nifty_Delta)
    3. Terminal Long Veto: Blocks long alerts under risk-off conditions unless
       idiosyncratic alpha exceeds the 4.0% confidence hurdle.
    4. Amplifies Short Alpha when Market is falling (Short Bias Confluence).
    5. F&O Check: Disallows overnight short signals on cash equities without F&O / locate.
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
        "SRF": 1.25,
        "GRASIM": 1.10,
        "LMW": 1.15,
        "ADOR": 1.10,
        "ADVAIT": 1.30,
        "CEIGALL": 1.20,
        "REFEX": 1.40,
        "SEAMECLTD": 1.20,
        "NURECA": 1.25,
        "ALKEM": 0.85,
        "DEFAULT": 1.10
    }

    @classmethod
    def get_stock_beta(cls, symbol: str) -> float:
        clean = symbol.upper().replace(".NS", "").replace(".BO", "")
        return cls.STOCK_BETAS.get(clean, cls.STOCK_BETAS["DEFAULT"])

    @staticmethod
    def assess_long(
        event_alpha_lcb_pct: float,
        beta_nifty: float,
        beta_sector: float,
        state: MarketState,
        required_target_pct: float = 1.20,
        execution_cost_pct: float = 0.30,
    ) -> Dict[str, Any]:
        """
        Terminal Long-Veto Engine based on Quantitative Audit Mandate 2:
        Under broad risk-off conditions (Nifty -0.8% 1D, -1.8% 3D, or VIX > 16 + 10% jump),
        no long signal may dispatch unless event_alpha >= 4.0% and net return covers hurdle.
        """
        market_contribution = beta_nifty * state.nifty_return_1d
        sector_contribution = beta_sector * state.sector_return_1d
        vix_penalty = max(0.0, state.india_vix - 16.0) * 0.08
        net_expected_pct = (
            event_alpha_lcb_pct
            + market_contribution
            + sector_contribution
            - vix_penalty
        )
        risk_off = (
            state.nifty_return_1d <= -0.80
            or state.nifty_return_3d <= -1.80
            or (state.india_vix >= 16.0 and state.vix_change_pct >= 10.0)
        )
        minimum_return = max(required_target_pct, 1.5 * execution_cost_pct)
        veto = risk_off and (
            event_alpha_lcb_pct < 4.0 or net_expected_pct < minimum_return
        )
        return {
            "dispatchable": not veto,
            "reason": "RISK_OFF_INSUFFICIENT_ALPHA" if veto else None,
            "net_expected_pct": round(net_expected_pct, 2),
            "market_drag_pct": round(market_contribution + sector_contribution, 2),
            "risk_off": risk_off,
        }

    @staticmethod
    def assess_short(
        event_alpha_lcb_pct: float,
        beta_nifty: float,
        beta_sector: float,
        state: MarketState,
        required_target_pct: float = 1.20,
        execution_cost_pct: float = 0.30,
        is_fno_eligible: bool = True,
    ) -> Dict[str, Any]:
        """
        Short-Bias Assessment Engine:
        Cash equity cannot be shorted overnight on Indian exchanges without F&O eligibility.
        In a falling market, short trades benefit from market tailwind.
        """
        if not is_fno_eligible:
            return {
                "dispatchable": False,
                "reason": "SHORT_NOT_FNO_ELIGIBLE",
                "net_expected_pct": 0.0,
                "market_drag_pct": 0.0,
                "strong_bull_market": False,
            }

        # Market selling provides tailwind to short trades
        market_contribution = beta_nifty * (-state.nifty_return_1d)
        sector_contribution = beta_sector * (-state.sector_return_1d)
        net_expected_pct = (
            event_alpha_lcb_pct
            + market_contribution
            + sector_contribution
        )
        strong_bull_market = (
            state.nifty_return_1d >= 0.80
            or state.nifty_return_3d >= 1.80
        )
        minimum_return = max(required_target_pct, 1.5 * execution_cost_pct)
        veto = strong_bull_market and (
            event_alpha_lcb_pct < 3.5 or net_expected_pct < minimum_return
        )
        return {
            "dispatchable": not veto,
            "reason": "STRONG_BULL_MARKET_SHORT_VETO" if veto else None,
            "net_expected_pct": round(net_expected_pct, 2),
            "market_drag_pct": round(market_contribution + sector_contribution, 2),
            "strong_bull_market": strong_bull_market,
        }

    @classmethod
    def calculate_beta_adjusted_target(
        cls,
        symbol: str,
        ltp: float,
        raw_target_pct: float,
        direction: str,
        nifty_change_pct: float,
        india_vix: float = 14.5,
        stock_beta: float = None,
        nifty_return_3d: float = None,
        sector_return_1d: float = 0.0,
        vix_change_pct: float = 0.0,
        sector_beta: float = 1.0,
        is_fno_eligible: bool = True,
    ) -> Dict[str, Any]:
        beta = stock_beta if (stock_beta and stock_beta > 0) else cls.get_stock_beta(symbol)
        is_bull = direction.upper() in ["BULLISH", "BUY"]
        n3d = nifty_return_3d if nifty_return_3d is not None else nifty_change_pct

        market_state = MarketState(
            nifty_return_1d=nifty_change_pct,
            nifty_return_3d=n3d,
            sector_return_1d=sector_return_1d,
            india_vix=india_vix,
            vix_change_pct=vix_change_pct,
        )

        dispatchable = True
        veto_reason = None

        if is_bull:
            assessment = cls.assess_long(
                event_alpha_lcb_pct=raw_target_pct,
                beta_nifty=beta,
                beta_sector=sector_beta,
                state=market_state,
                required_target_pct=1.20,
                execution_cost_pct=0.30,
            )
            net_t1_pct = assessment["net_expected_pct"]
            market_drag_pct = assessment["market_drag_pct"]
            dispatchable = assessment["dispatchable"]
            veto_reason = assessment["reason"]

            if not dispatchable:
                strategy = "SUPPRESSED (RISK-OFF INSUFFICIENT ALPHA)"
                target_confidence_note = f"Signal suppressed: Net expected move {net_t1_pct:+.2f}% is below required hurdle under risk-off conditions."
                conviction_delta = -20.0
                suppress_chase_alert = True
            elif nifty_change_pct < -0.40:
                strategy = "ACCUMULATE ON INTRADAY DIP (MARKET HEADWIND - T+5 SWING)"
                target_confidence_note = f"1-Day move suppressed by {market_drag_pct:.2f}% broad market drag. Do not chase opening auction. Accumulate on dip."
                conviction_delta = -round(min(15.0, abs(nifty_change_pct) * 8.0), 1)
                suppress_chase_alert = True if (net_t1_pct < 0.80 or nifty_change_pct < -1.0) else False
            elif nifty_change_pct >= 0.20:
                strategy = "STRONG MOMENTUM BREAKOUT (CONFLUENCE ALIGNED)"
                target_confidence_note = "Bullish catalyst backed by green market tailwinds."
                conviction_delta = +round(min(8.0, nifty_change_pct * 5.0), 1)
                suppress_chase_alert = False
            else:
                strategy = "STANDARD ACCUMULATION"
                target_confidence_note = "Neutral market backdrop."
                conviction_delta = 0.0
                suppress_chase_alert = False
        else:
            assessment = cls.assess_short(
                event_alpha_lcb_pct=raw_target_pct,
                beta_nifty=beta,
                beta_sector=sector_beta,
                state=market_state,
                required_target_pct=1.20,
                execution_cost_pct=0.30,
                is_fno_eligible=is_fno_eligible,
            )
            net_t1_pct = assessment["net_expected_pct"]
            market_drag_pct = assessment["market_drag_pct"]
            dispatchable = assessment["dispatchable"]
            veto_reason = assessment["reason"]

            if not dispatchable:
                strategy = f"SUPPRESSED ({veto_reason})"
                target_confidence_note = f"Short signal suppressed: {veto_reason}."
                conviction_delta = -20.0
                suppress_chase_alert = True
            elif nifty_change_pct < 0:
                strategy = "HIGH CONVICTION TACTICAL SHORT (MARKET TAILWIND ALIGNED)"
                target_confidence_note = f"Bearish catalyst amplified by +{market_drag_pct:.2f}% broader market selling wave."
                conviction_delta = +round(min(12.0, abs(nifty_change_pct) * 6.0), 1)
                suppress_chase_alert = False
            else:
                strategy = "CONTRARIAN TACTICAL SHORT"
                target_confidence_note = "Short setup faces green market headwind. Maintain tight discipline."
                conviction_delta = -round(min(10.0, nifty_change_pct * 6.0), 1)
                suppress_chase_alert = True if (net_t1_pct < 0.80 or nifty_change_pct > 1.0) else False

        # Microstructure Two-Tier Target Corridors
        mult = 1.0 if is_bull else -1.0
        abs_net = max(0.20, abs(net_t1_pct))
        safe_mag = max(0.40, round(abs_net * 0.75, 2))
        runner_mag = max(safe_mag + 0.30, round(abs_net * 1.25, 2))

        t1_safe_price = round(ltp * (1 + (mult * safe_mag) / 100), 2)
        t1_runner_price = round(ltp * (1 + (mult * runner_mag) / 100), 2)

        return {
            "symbol": symbol.upper(),
            "stock_beta": beta,
            "nifty_change_pct": nifty_change_pct,
            "india_vix": india_vix,
            "dispatchable": dispatchable,
            "reason": veto_reason,
            "market_drag_contribution_pct": market_drag_pct,
            "raw_catalyst_alpha_pct": raw_target_pct,
            "net_beta_adjusted_t1_pct": net_t1_pct if is_bull else -abs(net_t1_pct),
            "t1_safe_pct": safe_mag,
            "t1_runner_pct": runner_mag,
            "t1_safe_price": t1_safe_price,
            "t1_runner_price": t1_runner_price,
            "conviction_delta": conviction_delta,
            "suppress_chase_alert": suppress_chase_alert,
            "recommended_execution_strategy": strategy,
            "target_confidence_note": target_confidence_note,
            "adjusted_t1_corridor_inr": f"₹{min(t1_safe_price, t1_runner_price):,.2f} - ₹{max(t1_safe_price, t1_runner_price):,.2f}",
        }
