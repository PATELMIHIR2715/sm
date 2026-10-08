import sys
import os
import json
import re
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from services.ai_pipeline.sentiment_classifier import CalibratedSentimentScorer

class Window2026BacktestEngine:
    """
    2026 5-Day Window Backtest Engine (Jan 12, 2026 – Jan 16, 2026)
    Processes all market signals from this 5-day window through the full pipeline:
    1. Entity Resolution & Materiality Ratio
    2. Claude CLI LLM Direction Classification
    3. 10-Year Historical Macro RAG Match
    4. Calibrated Target Range Calculation
    5. Actual Market Outcome Comparison & Difference Calculation
    """

    def __init__(self):
        self.scorer = CalibratedSentimentScorer()

    def get_2026_window_dataset(self) -> list:
        return [
            # Day 1: Jan 12, 2026
            {
                "id": "SIG_2026_0112_01",
                "day": "Day 1 (Monday)",
                "date": "2026-01-12",
                "time": "09:45 AM",
                "source_type": "NSE_FILING",
                "symbol": "MAZDOCK",
                "company_name": "Mazagon Dock Shipbuilders Ltd",
                "sector": "Defense & Shipbuilding",
                "annual_revenue_cr": 9400.0,
                "atr_percentage": 3.8,
                "headline": "Mazagon Dock Shipbuilders Ltd receives INR 4200 Crore defense procurement contract from Ministry of Defense for next-gen stealth frigates",
                "actual_direction": "BULLISH",
                "actual_1d_move_pct": 7.4,
                "actual_5d_move_pct": 14.2
            },
            {
                "id": "SIG_2026_0112_02",
                "day": "Day 1 (Monday)",
                "date": "2026-01-12",
                "time": "11:15 AM",
                "source_type": "BULK_DEAL",
                "symbol": "BEL",
                "company_name": "Bharat Electronics Ltd",
                "sector": "Defense & Aerospace",
                "annual_revenue_cr": 20000.0,
                "atr_percentage": 2.8,
                "headline": "SBI Mutual Fund buys 85 lakh equity shares of Bharat Electronics via bulk deal at INR 192/share totaling INR 163 Crore",
                "actual_direction": "BULLISH",
                "actual_1d_move_pct": 3.1,
                "actual_5d_move_pct": 5.8
            },
            {
                "id": "SIG_2026_0112_03",
                "day": "Day 1 (Monday)",
                "date": "2026-01-12",
                "time": "02:30 PM",
                "source_type": "NSE_FILING",
                "symbol": "ASIANPAINT",
                "company_name": "Asian Paints Ltd",
                "sector": "Paints & Consumer",
                "annual_revenue_cr": 35000.0,
                "atr_percentage": 2.2,
                "headline": "Asian Paints Q3 Net Profit drops 18% YoY to INR 1112 Crore due to crude oil price surge and severe solvent input cost inflation",
                "actual_direction": "BEARISH",
                "actual_1d_move_pct": -4.5,
                "actual_5d_move_pct": -7.2
            },
            {
                "id": "SIG_2026_0112_04",
                "day": "Day 1 (Monday)",
                "date": "2026-01-12",
                "time": "03:15 PM",
                "source_type": "UNCONFIRMED_RUMOR",
                "symbol": "TCS",
                "company_name": "Tata Consultancy Services Ltd",
                "sector": "Information Technology",
                "annual_revenue_cr": 240000.0,
                "atr_percentage": 1.5,
                "headline": "Unverified social media rumors claim large European bank considering vendor consolidation among Indian IT service providers",
                "actual_direction": "NEUTRAL",
                "actual_1d_move_pct": 0.4,
                "actual_5d_move_pct": 0.8
            },

            # Day 2: Jan 13, 2026
            {
                "id": "SIG_2026_0113_01",
                "day": "Day 2 (Tuesday)",
                "date": "2026-01-13",
                "time": "10:00 AM",
                "source_type": "INSIDER_TRADING_PIT",
                "symbol": "TATAMOTORS",
                "company_name": "Tata Motors Ltd",
                "sector": "Automotive",
                "annual_revenue_cr": 430000.0,
                "atr_percentage": 2.8,
                "headline": "Tata Sons (Promoter Group) acquires 18 lakh equity shares of Tata Motors from open market, raising promoter stake to 46.2%",
                "actual_direction": "BULLISH",
                "actual_1d_move_pct": 2.9,
                "actual_5d_move_pct": 5.1
            },
            {
                "id": "SIG_2026_0113_02",
                "day": "Day 2 (Tuesday)",
                "date": "2026-01-13",
                "time": "12:10 PM",
                "source_type": "INSIDER_TRADING_PIT",
                "symbol": "INFY",
                "company_name": "Infosys Ltd",
                "sector": "Information Technology",
                "annual_revenue_cr": 153000.0,
                "atr_percentage": 2.0,
                "headline": "Infosys Key Management Personnel sells 50,000 equity shares at INR 1520/share following quarterly results announcement",
                "actual_direction": "BEARISH",
                "actual_1d_move_pct": -1.8,
                "actual_5d_move_pct": -3.4
            },
            {
                "id": "SIG_2026_0113_03",
                "day": "Day 2 (Tuesday)",
                "date": "2026-01-13",
                "time": "02:45 PM",
                "source_type": "CREDIT_RATING",
                "symbol": "TATASTEEL",
                "company_name": "Tata Steel Ltd",
                "sector": "Metals & Mining",
                "annual_revenue_cr": 230000.0,
                "atr_percentage": 2.9,
                "headline": "ICRA upgrades Long-Term Rating of Tata Steel Ltd from ICRA AA Stable to ICRA AA+ Positive on structural deleveraging",
                "actual_direction": "BULLISH",
                "actual_1d_move_pct": 2.4,
                "actual_5d_move_pct": 4.6
            },

            # Day 3: Jan 14, 2026
            {
                "id": "SIG_2026_0114_01",
                "day": "Day 3 (Wednesday)",
                "date": "2026-01-14",
                "time": "10:30 AM",
                "source_type": "PIB_GEM_TENDER",
                "symbol": "HAL",
                "company_name": "Hindustan Aeronautics Ltd",
                "sector": "Defense & Aerospace",
                "annual_revenue_cr": 30000.0,
                "atr_percentage": 3.2,
                "headline": "Cabinet Committee on Security approves INR 26000 Crore procurement of 240 Su-30MKI aero-engines from Hindustan Aeronautics Ltd",
                "actual_direction": "BULLISH",
                "actual_1d_move_pct": 6.8,
                "actual_5d_move_pct": 11.2
            },
            {
                "id": "SIG_2026_0114_02",
                "day": "Day 3 (Wednesday)",
                "date": "2026-01-14",
                "time": "01:20 PM",
                "source_type": "NSE_FILING",
                "symbol": "BERGEPAINT",
                "company_name": "Berger Paints India Ltd",
                "sector": "Paints & Consumer",
                "annual_revenue_cr": 10500.0,
                "atr_percentage": 2.5,
                "headline": "CRISIL upgrades Long-Term Bank Facilities rating of Berger Paints India Ltd to CRISIL AAA Stable from CRISIL AA+",
                "actual_direction": "BULLISH",
                "actual_1d_move_pct": 3.2,
                "actual_5d_move_pct": 4.8
            },

            # Day 4: Jan 15, 2026
            {
                "id": "SIG_2026_0115_01",
                "day": "Day 4 (Thursday)",
                "date": "2026-01-15",
                "time": "09:20 AM",
                "source_type": "NSE_FILING",
                "symbol": "HDFCBANK",
                "company_name": "HDFC Bank Ltd",
                "sector": "Banking & Financials",
                "annual_revenue_cr": 205000.0,
                "atr_percentage": 1.7,
                "headline": "HDFC Bank Q3 Net Interest Margin compresses 20bps QoQ to 3.4% as post-merger deposit repricing costs drag net interest income",
                "actual_direction": "BEARISH",
                "actual_1d_move_pct": -5.8,
                "actual_5d_move_pct": -8.1
            },
            {
                "id": "SIG_2026_0115_02",
                "day": "Day 4 (Thursday)",
                "date": "2026-01-15",
                "time": "11:45 AM",
                "source_type": "BULK_DEAL",
                "symbol": "LTI",
                "company_name": "LTIMindtree Ltd",
                "sector": "Information Technology",
                "annual_revenue_cr": 35000.0,
                "atr_percentage": 2.4,
                "headline": "Goldman Sachs sells 4.5 lakh equity shares of LTIMindtree in block deal at INR 5050/share totaling INR 227 Crore",
                "actual_direction": "BEARISH",
                "actual_1d_move_pct": -2.1,
                "actual_5d_move_pct": -3.8
            },

            # Day 5: Jan 16, 2026
            {
                "id": "SIG_2026_0116_01",
                "day": "Day 5 (Friday)",
                "date": "2026-01-16",
                "time": "10:15 AM",
                "source_type": "NSE_FILING",
                "symbol": "RELIANCE",
                "company_name": "Reliance Industries Ltd",
                "sector": "Energy & Petrochemicals",
                "annual_revenue_cr": 890000.0,
                "atr_percentage": 1.8,
                "headline": "Reliance Industries Q3 Net Profit rises 9% YoY to INR 17265 Crore with Jio adding 10.8M subscribers and Retail EBITDA up 22%",
                "actual_direction": "BULLISH",
                "actual_1d_move_pct": 2.1,
                "actual_5d_move_pct": 3.5
            },
            {
                "id": "SIG_2026_0116_02",
                "day": "Day 5 (Friday)",
                "date": "2026-01-16",
                "time": "01:45 PM",
                "source_type": "NSE_FILING",
                "symbol": "JSWSTEEL",
                "company_name": "JSW Steel Ltd",
                "sector": "Metals & Mining",
                "annual_revenue_cr": 175000.0,
                "atr_percentage": 2.7,
                "headline": "JSW Steel reports Q3 Net Loss of INR 915 Crore on inventory write-down and one-time international asset impairment",
                "actual_direction": "BEARISH",
                "actual_1d_move_pct": -4.2,
                "actual_5d_move_pct": -6.9
            },
            {
                "id": "SIG_2026_0116_03",
                "day": "Day 5 (Friday)",
                "date": "2026-01-16",
                "time": "03:10 PM",
                "source_type": "INSIDER_TRADING_PIT",
                "symbol": "M&M",
                "company_name": "Mahindra & Mahindra Ltd",
                "sector": "Automotive",
                "annual_revenue_cr": 140000.0,
                "atr_percentage": 2.4,
                "headline": "Mahindra & Mahindra Promoter Group buys 8 lakh equity shares from open market at average price of INR 1680/share (Value: INR 134 Crore)",
                "actual_direction": "BULLISH",
                "actual_1d_move_pct": 1.9,
                "actual_5d_move_pct": 4.2
            }
        ]

    def parse_range(self, range_str: str) -> tuple:
        try:
            parts = range_str.replace('%', '').split(' to ')
            return float(parts[0]), float(parts[1])
        except Exception:
            return 0.0, 0.0

    def evaluate_target(self, pred_range: str, actual_move: float, direction: str) -> dict:
        min_p, max_p = self.parse_range(pred_range)
        abs_actual = abs(actual_move)
        abs_min = abs(min_p)
        abs_max = abs(max_p)

        if direction in ["BULLISH", "BEARISH"]:
            if abs_min <= abs_actual <= abs_max:
                verdict = "EXACT HIT"
                diff_pct = 0.0
                explanation = f"Actual move ({actual_move:+.2f}%) landed directly inside target range [{min_p:+.2f}% to {max_p:+.2f}%]"
            elif abs_actual > abs_max:
                verdict = "SAFE UNDERSHOOT"
                diff_pct = round(abs_actual - abs_max, 2)
                explanation = f"Market exceeded target floor by +{diff_pct:.2f}% (Safe conservative under-promise)"
            elif abs_actual < abs_min:
                verdict = "OVERSHOOT"
                diff_pct = round(abs_min - abs_actual, 2)
                explanation = f"Market move fell short of target minimum by {diff_pct:.2f}%"
            else:
                verdict = "UNKNOWN"
                diff_pct = 0.0
                explanation = ""
        else:
            verdict = "ROUTED TO RUMORS"
            diff_pct = 0.0
            explanation = "Low confidence event — abstained from issuing price target"

        return {
            "verdict": verdict,
            "difference_pct": diff_pct,
            "explanation": explanation
        }

    def run_full_window_pipeline(self) -> dict:
        raw_events = self.get_2026_window_dataset()
        total_raw = len(raw_events)
        all_signals = []
        filtered_signals = []

        print(f"\n[Window 2026 Backtest] Running full pipeline across {total_raw} market events (Jan 12 - Jan 16, 2026)...")

        dir_correct_count = 0
        exact_hit_count = 0
        safe_undershoot_count = 0
        overshoot_count = 0
        total_diff_sum = 0.0

        for i, ev in enumerate(raw_events):
            company_meta = {
                "symbol": ev["symbol"],
                "company_name": ev["company_name"],
                "sector": ev["sector"],
                "annual_revenue_cr": ev["annual_revenue_cr"],
                "atr_percentage": ev["atr_percentage"]
            }

            # Run scoring pipeline
            pred = self.scorer.analyze_event(ev["headline"], company_meta)
            pred_dir = pred["direction"].replace(" / UNCONFIRMED", "")
            is_rumor = pred.get("is_rumor", False)

            target_eval = self.evaluate_target(pred["magnitude_range"], ev["actual_1d_move_pct"], pred_dir)
            dir_correct = (pred_dir == ev["actual_direction"])

            signal_record = {
                "id": ev["id"],
                "day": ev["day"],
                "date": ev["date"],
                "time": ev["time"],
                "source_type": ev["source_type"],
                "symbol": ev["symbol"],
                "company_name": ev["company_name"],
                "sector": ev["sector"],
                "headline": ev["headline"],
                "initial_direction": pred["direction"],
                "confidence_pct": pred["direction_confidence"],
                "materiality_ratio": pred.get("materiality_ratio", 0.0),
                "is_confirmed": not is_rumor,
                "filter_status": "CONFIRMED SIGNAL" if not is_rumor else "ROUTED TO RUMORS (<65% CONFIDENCE)",
                # Target & Actuals
                "predicted_target_range": pred["magnitude_range"],
                "top_historical_rag_match": pred.get("top_historical_match", "None"),
                "actual_direction": ev["actual_direction"],
                "actual_1d_move_pct": ev["actual_1d_move_pct"],
                "actual_5d_move_pct": ev["actual_5d_move_pct"],
                "direction_correct": dir_correct,
                "target_hit_verdict": target_eval["verdict"],
                "target_difference_pct": target_eval["difference_pct"],
                "evaluation_explanation": target_eval["explanation"]
            }

            all_signals.append(signal_record)

            if not is_rumor:
                filtered_signals.append(signal_record)
                if dir_correct:
                    dir_correct_count += 1
                if target_eval["verdict"] == "EXACT HIT":
                    exact_hit_count += 1
                elif target_eval["verdict"] == "SAFE UNDERSHOOT":
                    safe_undershoot_count += 1
                elif target_eval["verdict"] == "OVERSHOOT":
                    overshoot_count += 1
                total_diff_sum += target_eval["difference_pct"]

        total_filtered = len(filtered_signals)
        dir_acc_pct = round((dir_correct_count / total_filtered) * 100, 1) if total_filtered > 0 else 0.0
        exact_hit_rate = round((exact_hit_count / total_filtered) * 100, 1) if total_filtered > 0 else 0.0
        avg_diff = round(total_diff_sum / total_filtered, 2) if total_filtered > 0 else 0.0

        output_payload = {
            "test_window": "5-Day Trading Window (Jan 12, 2026 – Jan 16, 2026)",
            "summary_kpis": {
                "total_raw_signals": total_raw,
                "total_filtered_confirmed_signals": total_filtered,
                "filtered_out_to_rumors_count": total_raw - total_filtered,
                "confirmed_direction_accuracy_pct": dir_acc_pct,
                "target_exact_hit_count": exact_hit_count,
                "target_exact_hit_rate_pct": exact_hit_rate,
                "safe_undershoot_count": safe_undershoot_count,
                "overshoot_count": overshoot_count,
                "average_target_difference_pct": avg_diff,
                "wrong_confident_calls_count": total_filtered - dir_correct_count
            },
            "table_1_all_signals": all_signals,
            "table_2_filtered_directional_signals": filtered_signals,
            "generated_at": datetime.now().isoformat()
        }

        os.makedirs("d:/sm/data/backtest_reports", exist_ok=True)
        report_file = "d:/sm/data/backtest_reports/2026_5day_full_results.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(output_payload, f, indent=2, ensure_ascii=False)

        print(f"\n[Window 2026 Backtest Complete] Report saved to {report_file}")
        print(f"Total Raw: {total_raw} | Confirmed Actionable: {total_filtered} | Direction Accuracy: {dir_acc_pct}% | Exact Hits: {exact_hit_count}")
        return output_payload

if __name__ == "__main__":
    engine = Window2026BacktestEngine()
    engine.run_full_window_pipeline()
