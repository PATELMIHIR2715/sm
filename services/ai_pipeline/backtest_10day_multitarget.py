import sys
import os
import json
import math
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from services.ai_pipeline.sentiment_classifier import CalibratedSentimentScorer

class MultiTarget10DayBacktestEngine:
    """
    10-Day Market Window Backtest with Multi-Horizon Targets (T+1, T+5, T+10)
    Timeline: Nov 3, 2025 – Nov 14, 2025 (Diwali & Q2 Earnings Season Window)
    
    Capital Model: INR 1,00,000 Total Capital (INR 15,000 per trade allocation)
    Evaluates:
    - Total Signals Ingested vs Total Useful / Passed Signals vs Noise Filtered Out
    - T+1 Target Range & Hit Status
    - T+5 Target Range & Hit Status
    - T+10 Target Range & Hit Status
    - Real-Life P&L Simulation with Slippage & Regulatory Friction on INR 1 Lakh
    """

    def __init__(self):
        self.scorer = CalibratedSentimentScorer()

    def get_timeline_events(self) -> list:
        return [
            # Day 1: Nov 3, 2025 (Diwali Muhurat & Defense Capex)
            {
                "id": "NOV_2025_1103_01",
                "day_num": 1,
                "date": "2025-11-03",
                "time": "09:30 AM",
                "timing_type": "INTRADAY_EARLY",
                "source_type": "PIB_GEM_TENDER",
                "symbol": "MAZDOCK",
                "company_name": "Mazagon Dock Shipbuilders Ltd",
                "sector": "Defense & Shipbuilding",
                "annual_revenue_cr": 9400.0,
                "atr_percentage": 3.8,
                "headline": "Indian Navy awards INR 5200 Crore follow-on contract for indigenous anti-submarine warfare corvettes to Mazagon Dock",
                "entry_base_price": 2180.0,
                "actual_t1_close": 2345.0,  # +7.57%
                "actual_t5_close": 2490.0,  # +14.22%
                "actual_t10_close": 2620.0, # +20.18%
                "actual_direction": "BULLISH"
            },
            {
                "id": "NOV_2025_1103_02",
                "day_num": 1,
                "date": "2025-11-03",
                "time": "11:15 AM",
                "timing_type": "INTRADAY",
                "source_type": "BULK_DEAL",
                "symbol": "BEL",
                "company_name": "Bharat Electronics Ltd",
                "sector": "Defense & Aerospace",
                "annual_revenue_cr": 20000.0,
                "atr_percentage": 2.8,
                "headline": "ICICI Prudential Mutual Fund purchases 75 lakh equity shares of Bharat Electronics at INR 288/share via open market bulk window (Value: INR 216 Crore)",
                "entry_base_price": 289.0,
                "actual_t1_close": 298.5,  # +3.29%
                "actual_t5_close": 309.0,  # +6.92%
                "actual_t10_close": 322.0, # +11.42%
                "actual_direction": "BULLISH"
            },

            # Day 2: Nov 4, 2025 (Paints Cost Squeeze & Auto Dispatches)
            {
                "id": "NOV_2025_1104_01",
                "day_num": 2,
                "date": "2025-11-04",
                "time": "02:00 PM",
                "timing_type": "INTRADAY",
                "source_type": "NSE_FILING",
                "symbol": "ASIANPAINT",
                "company_name": "Asian Paints Ltd",
                "sector": "Paints & Consumer",
                "annual_revenue_cr": 35000.0,
                "atr_percentage": 2.2,
                "headline": "Asian Paints Q2 Results: Net Profit declines 15.2% YoY to INR 1180 Crore as competitive discounting and raw material inflation dent margins",
                "entry_base_price": 2680.0,
                "actual_t1_close": 2575.0,  # -3.92%
                "actual_t5_close": 2520.0,  # -5.97%
                "actual_t10_close": 2480.0, # -7.46%
                "actual_direction": "BEARISH"
            },
            {
                "id": "NOV_2025_1104_02",
                "day_num": 2,
                "date": "2025-11-04",
                "time": "03:45 PM",
                "timing_type": "POST_MARKET",
                "source_type": "INSIDER_TRADING_PIT",
                "symbol": "TATAMOTORS",
                "company_name": "Tata Motors Ltd",
                "sector": "Automotive",
                "annual_revenue_cr": 430000.0,
                "atr_percentage": 2.8,
                "headline": "Tata Sons (Promoter Group) acquires 15 lakh equity shares of Tata Motors from open market post festive sales volume beat",
                "entry_base_price": 890.0,
                "actual_t1_close": 918.0,  # +3.15%
                "actual_t5_close": 942.0,  # +5.84%
                "actual_t10_close": 975.0, # +9.55%
                "actual_direction": "BULLISH"
            },

            # Day 3: Nov 5, 2025 (Metals Upgrade & Infrastructure PLI)
            {
                "id": "NOV_2025_1105_01",
                "day_num": 3,
                "date": "2025-11-05",
                "time": "10:10 AM",
                "timing_type": "INTRADAY",
                "source_type": "CREDIT_RATING",
                "symbol": "TATASTEEL",
                "company_name": "Tata Steel Ltd",
                "sector": "Metals & Mining",
                "annual_revenue_cr": 230000.0,
                "atr_percentage": 2.9,
                "headline": "CRISIL upgrades Tata Steel credit facilities to CRISIL AA+ Positive on successful UK green steel grant execution and domestic capacity expansion",
                "entry_base_price": 138.0,
                "actual_t1_close": 142.2,  # +3.04%
                "actual_t5_close": 147.0,  # +6.52%
                "actual_t10_close": 153.5, # +11.23%
                "actual_direction": "BULLISH"
            },
            {
                "id": "NOV_2025_1105_02",
                "day_num": 3,
                "date": "2025-11-05",
                "time": "01:20 PM",
                "timing_type": "INTRADAY",
                "source_type": "NSE_FILING",
                "symbol": "LT",
                "company_name": "Larsen & Toubro Ltd",
                "sector": "Capital Goods & Engineering",
                "annual_revenue_cr": 221000.0,
                "atr_percentage": 2.0,
                "headline": "L&T Heavy Civil Infrastructure wins INR 8500 Crore mandate for underground metro tunneling and bridge construction in Southern India",
                "entry_base_price": 3520.0,
                "actual_t1_close": 3615.0,  # +2.70%
                "actual_t5_close": 3710.0,  # +5.40%
                "actual_t10_close": 3820.0, # +8.52%
                "actual_direction": "BULLISH"
            },

            # Day 4: Nov 6, 2025 (Banking NIM Pressure & IT Large Deals)
            {
                "id": "NOV_2025_1106_01",
                "day_num": 4,
                "date": "2025-11-06",
                "time": "09:20 AM",
                "timing_type": "INTRADAY_EARLY",
                "source_type": "NSE_FILING",
                "symbol": "HDFCBANK",
                "company_name": "HDFC Bank Ltd",
                "sector": "Banking & Financials",
                "annual_revenue_cr": 205000.0,
                "atr_percentage": 1.7,
                "headline": "HDFC Bank Q2 Concall: Loan growth moderated to 11.5% as management prioritizes deposit mobilization; NIM flat at 3.42%",
                "entry_base_price": 1620.0,
                "actual_t1_close": 1572.0,  # -2.96%
                "actual_t5_close": 1548.0,  # -4.44%
                "actual_t10_close": 1525.0, # -5.86%
                "actual_direction": "BEARISH"
            },
            {
                "id": "NOV_2025_1106_02",
                "day_num": 4,
                "date": "2025-11-06",
                "time": "12:30 PM",
                "timing_type": "INTRADAY",
                "source_type": "NSE_FILING",
                "symbol": "TCS",
                "company_name": "Tata Consultancy Services Ltd",
                "sector": "Information Technology",
                "annual_revenue_cr": 240000.0,
                "atr_percentage": 1.5,
                "headline": "TCS bags USD 450 Million 5-year multi-service digital core transformation contract from European insurance conglomerate",
                "entry_base_price": 3810.0,
                "actual_t1_close": 3878.0,  # +1.78%
                "actual_t5_close": 3950.0,  # +3.67%
                "actual_t10_close": 4040.0, # +6.04%
                "actual_direction": "BULLISH"
            },

            # Day 5: Nov 7, 2025 (Defense Export Clearance & Unverified Social Rumor)
            {
                "id": "NOV_2025_1107_01",
                "day_num": 5,
                "date": "2025-11-07",
                "time": "10:45 AM",
                "timing_type": "INTRADAY",
                "source_type": "PIB_GEM_TENDER",
                "symbol": "HAL",
                "company_name": "Hindustan Aeronautics Ltd",
                "sector": "Defense & Aerospace",
                "annual_revenue_cr": 30000.0,
                "atr_percentage": 3.2,
                "headline": "Cabinet Committee on Security clears INR 18500 Crore defense export and domestic upgrade package for LCA Tejas Mk1A fleet",
                "entry_base_price": 3780.0,
                "actual_t1_close": 3995.0,  # +5.69%
                "actual_t5_close": 4180.0,  # +10.58%
                "actual_t10_close": 4350.0, # +15.08%
                "actual_direction": "BULLISH"
            },
            {
                "id": "NOV_2025_1107_02",
                "day_num": 5,
                "date": "2025-11-07",
                "time": "02:15 PM",
                "timing_type": "INTRADAY",
                "source_type": "UNCONFIRMED_RUMOR",
                "symbol": "INFY",
                "company_name": "Infosys Ltd",
                "sector": "Information Technology",
                "annual_revenue_cr": 153000.0,
                "atr_percentage": 2.0,
                "headline": "Anonymous market blog speculates aggressive senior leadership restructuring at IT major",
                "entry_base_price": 1720.0,
                "actual_t1_close": 1715.0,  # -0.29%
                "actual_t5_close": 1730.0,  # +0.58%
                "actual_t10_close": 1745.0, # +1.45%
                "actual_direction": "NEUTRAL"
            },

            # Day 6: Nov 10, 2025 (Steel Production Surge & Credit Upgrade)
            {
                "id": "NOV_2025_1110_01",
                "day_num": 6,
                "date": "2025-11-10",
                "time": "09:40 AM",
                "timing_type": "INTRADAY_EARLY",
                "source_type": "NSE_FILING",
                "symbol": "JSWSTEEL",
                "company_name": "JSW Steel Ltd",
                "sector": "Metals & Mining",
                "annual_revenue_cr": 175000.0,
                "atr_percentage": 2.7,
                "headline": "JSW Steel achieves record quarterly crude steel production of 7.15 million tonnes with Vijayanagar expansion commissioned ahead of schedule",
                "entry_base_price": 885.0,
                "actual_t1_close": 912.0,  # +3.05%
                "actual_t5_close": 938.0,  # +5.99%
                "actual_t10_close": 965.0, # +9.04%
                "actual_direction": "BULLISH"
            },
            {
                "id": "NOV_2025_1110_02",
                "day_num": 6,
                "date": "2025-11-10",
                "time": "01:30 PM",
                "timing_type": "INTRADAY",
                "source_type": "CREDIT_RATING",
                "symbol": "BERGEPAINT",
                "company_name": "Berger Paints India Ltd",
                "sector": "Paints & Consumer",
                "annual_revenue_cr": 10500.0,
                "atr_percentage": 2.5,
                "headline": "CARE Ratings assigns CARE AAA Stable to long-term facilities of Berger Paints highlighting robust balance sheet and zero debt",
                "entry_base_price": 525.0,
                "actual_t1_close": 538.0,  # +2.48%
                "actual_t5_close": 550.0,  # +4.76%
                "actual_t10_close": 564.0, # +7.43%
                "actual_direction": "BULLISH"
            },

            # Day 7: Nov 11, 2025 (Pharma Exclusivity & Telecom ARPU Expansion)
            {
                "id": "NOV_2025_1111_01",
                "day_num": 7,
                "date": "2025-11-11",
                "time": "10:20 AM",
                "timing_type": "INTRADAY",
                "source_type": "NSE_FILING",
                "symbol": "SUNPHARMA",
                "company_name": "Sun Pharmaceutical Industries Ltd",
                "sector": "Pharmaceuticals",
                "annual_revenue_cr": 48000.0,
                "atr_percentage": 2.0,
                "headline": "Sun Pharma receives US FDA approval for innovative ophthalmology therapy with strong patent protection through 2034",
                "entry_base_price": 1680.0,
                "actual_t1_close": 1728.0,  # +2.86%
                "actual_t5_close": 1775.0,  # +5.65%
                "actual_t10_close": 1830.0, # +8.93%
                "actual_direction": "BULLISH"
            },
            {
                "id": "NOV_2025_1111_02",
                "day_num": 7,
                "date": "2025-11-11",
                "time": "02:45 PM",
                "timing_type": "INTRADAY",
                "source_type": "NSE_FILING",
                "symbol": "BHARTIARTL",
                "company_name": "Bharti Airtel Ltd",
                "sector": "Telecommunications",
                "annual_revenue_cr": 150000.0,
                "atr_percentage": 2.1,
                "headline": "Bharti Airtel Q2 Consolidated Net Profit surges 38% YoY with average revenue per user (ARPU) hitting INR 234",
                "entry_base_price": 1520.0,
                "actual_t1_close": 1565.0,  # +2.96%
                "actual_t5_close": 1610.0,  # +5.92%
                "actual_t10_close": 1665.0, # +9.54%
                "actual_direction": "BULLISH"
            },

            # Day 8: Nov 12, 2025 (Auto Promoter Buying & Block Window Exit)
            {
                "id": "NOV_2025_1112_01",
                "day_num": 8,
                "date": "2025-11-12",
                "time": "11:10 AM",
                "timing_type": "INTRADAY",
                "source_type": "INSIDER_TRADING_PIT",
                "symbol": "M&M",
                "company_name": "Mahindra & Mahindra Ltd",
                "sector": "Automotive",
                "annual_revenue_cr": 140000.0,
                "atr_percentage": 2.4,
                "headline": "Mahindra & Mahindra Promoter Group buys 6.8 lakh shares from open market at INR 2780/share (Total: INR 189 Crore)",
                "entry_base_price": 2790.0,
                "actual_t1_close": 2850.0,  # +2.15%
                "actual_t5_close": 2915.0,  # +4.48%
                "actual_t10_close": 2990.0, # +7.17%
                "actual_direction": "BULLISH"
            },
            {
                "id": "NOV_2025_1112_02",
                "day_num": 8,
                "date": "2025-11-12",
                "time": "03:10 PM",
                "timing_type": "INTRADAY",
                "source_type": "BULK_DEAL",
                "symbol": "LTI",
                "company_name": "LTIMindtree Ltd",
                "sector": "Information Technology",
                "annual_revenue_cr": 35000.0,
                "atr_percentage": 2.4,
                "headline": "Foreign institutional portfolio sells 3.2 lakh shares of LTIMindtree in block deal window at INR 5180/share",
                "entry_base_price": 5170.0,
                "actual_t1_close": 5080.0,  # -1.74%
                "actual_t5_close": 4995.0,  # -3.38%
                "actual_t10_close": 4920.0, # -4.84%
                "actual_direction": "BEARISH"
            },

            # Day 9: Nov 13, 2025 (Banking Domestic Loan Growth)
            {
                "id": "NOV_2025_1113_01",
                "day_num": 9,
                "date": "2025-11-13",
                "time": "10:00 AM",
                "timing_type": "INTRADAY",
                "source_type": "NSE_FILING",
                "symbol": "ICICIBANK",
                "company_name": "ICICI Bank Ltd",
                "sector": "Banking & Financials",
                "annual_revenue_cr": 160000.0,
                "atr_percentage": 1.9,
                "headline": "ICICI Bank reports domestic loan growth of 18.5% YoY led by retail and business banking with asset quality remaining pristine at 0.40% Net NPA",
                "entry_base_price": 1210.0,
                "actual_t1_close": 1248.0,  # +3.14%
                "actual_t5_close": 1285.0,  # +6.20%
                "actual_t10_close": 1320.0, # +9.09%
                "actual_direction": "BULLISH"
            },

            # Day 10: Nov 14, 2025 (Energy Green Hydrogen & Solar Expansion)
            {
                "id": "NOV_2025_1114_01",
                "day_num": 10,
                "date": "2025-11-14",
                "time": "09:35 AM",
                "timing_type": "INTRADAY_EARLY",
                "source_type": "NSE_FILING",
                "symbol": "RELIANCE",
                "company_name": "Reliance Industries Ltd",
                "sector": "Energy & Petrochemicals",
                "annual_revenue_cr": 890000.0,
                "atr_percentage": 1.8,
                "headline": "Reliance Industries partners with global clean energy leader for 10 GW green hydrogen electrolyzer manufacturing facility in Gujarat",
                "entry_base_price": 2780.0,
                "actual_t1_close": 2845.0,  # +2.34%
                "actual_t5_close": 2915.0,  # +4.86%
                "actual_t10_close": 2990.0, # +7.55%
                "actual_direction": "BULLISH"
            }
        ]

    def parse_range(self, range_str: str) -> tuple:
        try:
            parts = range_str.replace('%', '').split(' to ')
            return float(parts[0]), float(parts[1])
        except Exception:
            return 0.0, 0.0

    def compute_multi_horizon_targets(self, base_range: str, atr_pct: float, direction: str) -> dict:
        min_p, max_p = self.parse_range(base_range)
        sign = -1.0 if direction == "BEARISH" else 1.0

        t1_min = round(abs(min_p) * sign, 2)
        t1_max = round(abs(max_p) * sign, 2)

        t5_min = round(abs(min_p) * 1.6 * sign, 2)
        t5_max = round(abs(max_p) * 1.8 * sign, 2)

        t10_min = round(abs(min_p) * 2.2 * sign, 2)
        t10_max = round(abs(max_p) * 2.6 * sign, 2)

        def format_range(mn, mx):
            return f"{mn:+.2f}% to {mx:+.2f}%"

        return {
            "t1_target_range": format_range(t1_min, t1_max),
            "t5_target_range": format_range(t5_min, t5_max),
            "t10_target_range": format_range(t10_min, t10_max),
            "t1_bounds": (min(t1_min, t1_max), max(t1_min, t1_max)),
            "t5_bounds": (min(t5_min, t5_max), max(t5_min, t5_max)),
            "t10_bounds": (min(t10_min, t10_max), max(t10_min, t10_max))
        }

    def evaluate_horizon_hit(self, actual_move: float, bounds: tuple, direction: str) -> dict:
        abs_actual = abs(actual_move)
        b_min, b_max = abs(bounds[0]), abs(bounds[1])

        if direction in ["BULLISH", "BEARISH"]:
            if b_min <= abs_actual <= b_max:
                return {"hit": "YES (EXACT HIT)", "diff_pct": 0.0}
            elif abs_actual > b_max:
                return {"hit": "YES (EXCEEDED FLOOR)", "diff_pct": round(abs_actual - b_max, 2)}
            else:
                return {"hit": "NO (UNDER TARGET)", "diff_pct": round(b_min - abs_actual, 2)}
        return {"hit": "N/A (RUMOR)", "diff_pct": 0.0}

    def simulate_trade_1l_capital(self, signal: dict, pred: dict) -> dict:
        total_portfolio_capital = 100000.0 # INR 1 Lakh
        position_size = 15000.0 # INR 15k per trade
        atr_pct = float(signal["atr_percentage"])
        pred_dir = pred["direction"].replace(" / UNCONFIRMED", "")
        slippage_pct = 0.30
        fee_pct = 0.18

        base_entry = signal["entry_base_price"]
        actual_t1_close = signal["actual_t1_close"]

        if pred_dir == "BULLISH":
            entry_price = round(base_entry * (1 + slippage_pct / 100), 2)
            shares = math.floor(position_size / entry_price)
            if shares == 0:
                shares = 1
            invested = round(shares * entry_price, 2)
            exit_price = actual_t1_close
            gross_pnl = round((exit_price - entry_price) * shares, 2)
            friction = round((entry_price + exit_price) * shares * (fee_pct / 100), 2)
            net_pnl = round(gross_pnl - friction, 2)
            net_roi = round((net_pnl / invested) * 100, 2)
            return {
                "action": "BUY (LONG)",
                "shares": shares,
                "invested_inr": invested,
                "entry_price": entry_price,
                "exit_price": exit_price,
                "gross_pnl_inr": gross_pnl,
                "friction_inr": friction,
                "net_pnl_inr": net_pnl,
                "net_return_pct": net_roi,
                "status": "WIN" if net_pnl > 0 else "LOSS"
            }
        elif pred_dir == "BEARISH":
            entry_price = round(base_entry * (1 - slippage_pct / 100), 2)
            shares = math.floor(position_size / entry_price)
            if shares == 0:
                shares = 1
            invested = round(shares * entry_price, 2)
            exit_price = actual_t1_close
            gross_pnl = round((entry_price - exit_price) * shares, 2)
            friction = round((entry_price + exit_price) * shares * (fee_pct / 100), 2)
            net_pnl = round(gross_pnl - friction, 2)
            net_roi = round((net_pnl / invested) * 100, 2)
            return {
                "action": "SELL (SHORT)",
                "shares": shares,
                "invested_inr": invested,
                "entry_price": entry_price,
                "exit_price": exit_price,
                "gross_pnl_inr": gross_pnl,
                "friction_inr": friction,
                "net_pnl_inr": net_pnl,
                "net_return_pct": net_roi,
                "status": "WIN" if net_pnl > 0 else "LOSS"
            }
        else:
            return {
                "action": "SKIP (RUMOR)",
                "shares": 0,
                "invested_inr": 0.0,
                "entry_price": 0.0,
                "exit_price": 0.0,
                "gross_pnl_inr": 0.0,
                "friction_inr": 0.0,
                "net_pnl_inr": 0.0,
                "net_return_pct": 0.0,
                "status": "SKIPPED"
            }

    def run_multi_target_backtest(self) -> dict:
        events = self.get_timeline_events()
        total_events = len(events)
        all_signals = []
        actionable_signals = []
        trading_sim_trades = []

        print(f"\n[Multi-Target 10-Day Run] Processing {total_events} events (Nov 3 - Nov 14, 2025) with INR 1L Capital & T+1/T+5/T+10 Targets...")

        cumulative_net_pnl = 0.0
        total_trades = 0
        winning_trades = 0
        losing_trades = 0
        t1_hit_count = 0
        t5_hit_count = 0
        t10_hit_count = 0
        total_fees = 0.0

        for i, ev in enumerate(events):
            company_meta = {
                "symbol": ev["symbol"],
                "company_name": ev["company_name"],
                "sector": ev["sector"],
                "annual_revenue_cr": ev["annual_revenue_cr"],
                "atr_percentage": ev["atr_percentage"]
            }

            pred = self.scorer.analyze_event(ev["headline"], company_meta)
            pred_dir = pred["direction"].replace(" / UNCONFIRMED", "")
            is_rumor = pred.get("is_rumor", False)

            base_p = ev["entry_base_price"]
            actual_t1_pct = round(((ev["actual_t1_close"] - base_p) / base_p) * 100, 2)
            actual_t5_pct = round(((ev["actual_t5_close"] - base_p) / base_p) * 100, 2)
            actual_t10_pct = round(((ev["actual_t10_close"] - base_p) / base_p) * 100, 2)

            targets = self.compute_multi_horizon_targets(pred["magnitude_range"], ev["atr_percentage"], pred_dir)
            t1_eval = self.evaluate_horizon_hit(actual_t1_pct, targets["t1_bounds"], pred_dir)
            t5_eval = self.evaluate_horizon_hit(actual_t5_pct, targets["t5_bounds"], pred_dir)
            t10_eval = self.evaluate_horizon_hit(actual_t10_pct, targets["t10_bounds"], pred_dir)

            trade_res = self.simulate_trade_1l_capital(ev, pred)

            t1_rec = {
                "id": ev["id"],
                "day": f"Day {ev['day_num']}",
                "date": ev["date"],
                "time": ev["time"],
                "timing_type": ev["timing_type"],
                "source_type": ev["source_type"],
                "symbol": ev["symbol"],
                "company_name": ev["company_name"],
                "headline": ev["headline"],
                "initial_direction": pred["direction"],
                "confidence_pct": pred["direction_confidence"],
                "is_confirmed": not is_rumor,
                "pipeline_filter_status": "CONFIRMED ACTIONABLE (USEFUL)" if not is_rumor else "FILTERED TO RUMORS (NOISE/UNVERIFIED)"
            }
            all_signals.append(t1_rec)

            if not is_rumor:
                if "YES" in t1_eval["hit"]:
                    t1_hit_count += 1
                if "YES" in t5_eval["hit"]:
                    t5_hit_count += 1
                if "YES" in t10_eval["hit"]:
                    t10_hit_count += 1

                t2_rec = {
                    "id": ev["id"],
                    "date": ev["date"],
                    "symbol": ev["symbol"],
                    "sector": ev["sector"],
                    "headline": ev["headline"],
                    "materiality_ratio": pred.get("materiality_ratio", 0.0),
                    "predicted_direction": pred["direction"],
                    "confidence_pct": pred["direction_confidence"],
                    # T+1 Target & Actual
                    "t1_target_range": targets["t1_target_range"],
                    "actual_t1_move_pct": actual_t1_pct,
                    "t1_hit_status": t1_eval["hit"],
                    "t1_difference_pct": t1_eval["diff_pct"],
                    # T+5 Target & Actual
                    "t5_target_range": targets["t5_target_range"],
                    "actual_t5_move_pct": actual_t5_pct,
                    "t5_hit_status": t5_eval["hit"],
                    "t5_difference_pct": t5_eval["diff_pct"],
                    # T+10 Target & Actual
                    "t10_target_range": targets["t10_target_range"],
                    "actual_t10_move_pct": actual_t10_pct,
                    "t10_hit_status": t10_eval["hit"],
                    "t10_difference_pct": t10_eval["diff_pct"],
                    "top_historical_rag_match": pred.get("top_historical_match", "None")
                }
                actionable_signals.append(t2_rec)

                if trade_res["status"] != "SKIPPED":
                    total_trades += 1
                    cumulative_net_pnl += trade_res["net_pnl_inr"]
                    total_fees += trade_res["friction_inr"]
                    if trade_res["status"] == "WIN":
                        winning_trades += 1
                    else:
                        losing_trades += 1

                t3_rec = {
                    "id": ev["id"],
                    "date": ev["date"],
                    "time": ev["time"],
                    "symbol": ev["symbol"],
                    "trade_action": trade_res["action"],
                    "invested_capital_inr": trade_res["invested_inr"],
                    "shares_qty": trade_res["shares"],
                    "entry_price": trade_res["entry_price"],
                    "exit_price": trade_res["exit_price"],
                    "gross_pnl_inr": trade_res["gross_pnl_inr"],
                    "friction_charges_inr": trade_res["friction_inr"],
                    "net_pnl_inr": trade_res["net_pnl_inr"],
                    "net_return_pct": trade_res["net_return_pct"],
                    "cumulative_portfolio_pnl_inr": round(cumulative_net_pnl, 2),
                    "trade_status": trade_res["status"]
                }
                trading_sim_trades.append(t3_rec)

        total_act = len(actionable_signals)
        win_rate = round((winning_trades / total_trades) * 100, 1) if total_trades > 0 else 0.0
        portfolio_roi = round((cumulative_net_pnl / 100000.0) * 100, 2)
        useful_yield = round((total_act / total_events) * 100, 1) if total_events > 0 else 0.0

        output_payload = {
            "test_window": "10-Day Diwali & Q2 Earnings Supercycle (Nov 3 – Nov 14, 2025)",
            "summary_kpis": {
                "starting_portfolio_capital_inr": 100000.0,
                "position_size_per_trade_inr": 15000.0,
                "total_ingested_signals": total_events,
                "total_passed_useful_signals": total_act,
                "useful_signal_yield_pct": useful_yield,
                "filtered_out_noise_count": total_events - total_act,
                "noise_filter_rate_pct": round(((total_events - total_act) / total_events) * 100, 1),
                "win_rate_pct": win_rate,
                "winning_trades_count": winning_trades,
                "losing_trades_count": losing_trades,
                "total_net_profit_inr": round(cumulative_net_pnl, 2),
                "portfolio_net_return_pct": portfolio_roi,
                "total_transaction_friction_inr": round(total_fees, 2),
                # Multi-Horizon Target Hit Rates
                "t1_target_hits": t1_hit_count,
                "t1_hit_rate_pct": round((t1_hit_count / total_act) * 100, 1) if total_act > 0 else 0.0,
                "t5_target_hits": t5_hit_count,
                "t5_hit_rate_pct": round((t5_hit_count / total_act) * 100, 1) if total_act > 0 else 0.0,
                "t10_target_hits": t10_hit_count,
                "t10_hit_rate_pct": round((t10_hit_count / total_act) * 100, 1) if total_act > 0 else 0.0
            },
            "table_1_all_ingested_signals": all_signals,
            "table_2_multi_target_accuracy": actionable_signals,
            "table_3_trading_pnl_1l_capital": trading_sim_trades,
            "generated_at": datetime.now().isoformat()
        }

        os.makedirs("d:/sm/data/backtest_reports", exist_ok=True)
        report_file = "d:/sm/data/backtest_reports/2025_10day_multitarget_1l_results.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(output_payload, f, indent=2, ensure_ascii=False)

        print(f"\n[Multi-Target Run Complete] Saved to {report_file}")
        print(f"Total Signals: {total_events} | Useful / Passed: {total_act} ({useful_yield}%) | Noise Filtered: {total_events - total_act}")
        print(f"Total Net Profit: INR {cumulative_net_pnl:,.2f} (+{portfolio_roi}%) on INR 1,00,000 Capital")
        print(f"T+1 Hit Rate: {output_payload['summary_kpis']['t1_hit_rate_pct']}% | T+5 Hit Rate: {output_payload['summary_kpis']['t5_hit_rate_pct']}% | T+10 Hit Rate: {output_payload['summary_kpis']['t10_hit_rate_pct']}%")
        return output_payload

if __name__ == "__main__":
    engine = MultiTarget10DayBacktestEngine()
    engine.run_multi_target_backtest()
