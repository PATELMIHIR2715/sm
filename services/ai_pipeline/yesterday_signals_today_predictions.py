import sys
import os
import json
import math
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from services.ai_pipeline.sentiment_classifier import CalibratedSentimentScorer
from services.ai_pipeline.scaled_rag_engine import ScaledVectorRAGEngine
from services.ai_pipeline.technical_confluence import TechnicalConfluenceEngine
from services.ai_pipeline.kelly_position_sizer import KellyPositionSizer

class YesterdaySignalsTodayPredictor:
    """
    Strict Forward Prediction Test:
    Ingests ONLY Yesterday's Corporate Signals & Predicts Today's Stock Price (T+1).
    
    Strict Isolation Guarantee:
    - Zero live market price is fetched during prediction.
    - Base price is strictly Yesterday's closing price at the moment the signal arrived (T-0).
    - Uses full 7-Pillar Analyst Framework: NLP Materiality, RAG Analogs, Technical Confluence, Kelly Sizing.
    """

    def __init__(self):
        self.scorer = CalibratedSentimentScorer()
        self.rag = ScaledVectorRAGEngine()
        self.confluence = TechnicalConfluenceEngine()
        self.sizer = KellyPositionSizer(portfolio_capital=100000.0)

    def get_yesterday_signals(self) -> list:
        """Yesterday's & Pre-Market Corporate Announcement Stream (Sep 25 – Sep 27, 2026)"""
        return [
            {
                "id": "YEST_01_HAL",
                "symbol": "HAL",
                "company_name": "Hindustan Aeronautics Ltd",
                "sector": "Defense & Aerospace",
                "source_type": "PIB_GEM_TENDER",
                "signal_arrival_date": "Sep 25, 2026 (Friday)",
                "signal_arrival_time": "10:20 AM IST",
                "timing_type": "INTRADAY",
                "headline": "Cabinet clears landmark INR 14,200 Crore defense procurement contract for 240 indigenous AL-31FP aero-engines for Sukhoi Su-30MKI fighters with HAL",
                "yesterday_base_price_t0": 4450.00,
                "annual_revenue_cr": 30000.0,
                "atr_percentage": 3.2,
                "technical_meta": {"ema_200": 4050.0, "ema_50": 4320.0, "rsi_14": 62.0, "nifty_change_pct": 0.30}
            },
            {
                "id": "YEST_02_ASIANPAINT",
                "symbol": "ASIANPAINT",
                "company_name": "Asian Paints Ltd",
                "sector": "Paints & Consumer",
                "source_type": "NSE_FILING",
                "signal_arrival_date": "Sep 25, 2026 (Friday)",
                "signal_arrival_time": "02:10 PM IST",
                "timing_type": "INTRADAY",
                "headline": "Brent crude spikes 4.5% alongside aggressive festive dealer rebate schemes; analysts estimate 120-150 bps operating margin contraction for paint manufacturers",
                "yesterday_base_price_t0": 2540.00,
                "annual_revenue_cr": 35000.0,
                "atr_percentage": 2.2,
                "technical_meta": {"ema_200": 2720.0, "ema_50": 2610.0, "rsi_14": 42.0, "nifty_change_pct": -0.15}
            },
            {
                "id": "YEST_03_JSWSTEEL",
                "symbol": "JSWSTEEL",
                "company_name": "JSW Steel Ltd",
                "sector": "Metals & Mining",
                "source_type": "NSE_FILING",
                "signal_arrival_date": "Sep 26, 2026 (Saturday)",
                "signal_arrival_time": "11:30 AM IST",
                "timing_type": "WEEKEND_DISCLOSURE",
                "headline": "JSW Steel announces successful commissioning of 5 MTPA hot strip mill expansion at Dolvi facility one month ahead of schedule to meet domestic auto demand",
                "yesterday_base_price_t0": 945.00,
                "annual_revenue_cr": 175000.0,
                "atr_percentage": 2.7,
                "technical_meta": {"ema_200": 890.0, "ema_50": 925.0, "rsi_14": 58.5, "nifty_change_pct": 0.20}
            },
            {
                "id": "YEST_04_BEL",
                "symbol": "BEL",
                "company_name": "Bharat Electronics Ltd",
                "sector": "Defense & Aerospace",
                "source_type": "NSE_FILING",
                "signal_arrival_date": "Sep 25, 2026 (Friday)",
                "signal_arrival_time": "03:45 PM IST",
                "timing_type": "POST_MARKET",
                "headline": "Bharat Electronics receives INR 1850 Crore contract for supply of indigenous tactical radar suites and battlefield communication systems for Indian Armed Forces",
                "yesterday_base_price_t0": 365.00,
                "annual_revenue_cr": 20000.0,
                "atr_percentage": 2.8,
                "technical_meta": {"ema_200": 330.0, "ema_50": 352.0, "rsi_14": 64.0, "nifty_change_pct": 0.35}
            },
            {
                "id": "YEST_05_WIPRO",
                "symbol": "WIPRO",
                "company_name": "Wipro Ltd",
                "sector": "Information Technology",
                "source_type": "UNCONFIRMED_RUMOR",
                "signal_arrival_date": "Sep 26, 2026 (Saturday)",
                "signal_arrival_time": "04:15 PM IST",
                "timing_type": "WEEKEND_DISCLOSURE",
                "headline": "Social media message claims unverified restructuring in North American BFSI business unit with possible key account deferrals",
                "yesterday_base_price_t0": 540.00,
                "annual_revenue_cr": 90000.0,
                "atr_percentage": 2.1,
                "technical_meta": {"ema_200": 525.0, "ema_50": 535.0, "rsi_14": 50.0, "nifty_change_pct": 0.00}
            },
            {
                "id": "YEST_06_TATASTEEL",
                "symbol": "TATASTEEL",
                "company_name": "Tata Steel Ltd",
                "sector": "Metals & Mining",
                "source_type": "CREDIT_RATING",
                "signal_arrival_date": "Sep 27, 2026 (Sunday)",
                "signal_arrival_time": "02:30 PM IST",
                "timing_type": "WEEKEND_DISCLOSURE",
                "headline": "CARE Ratings assigns CARE AA+ Positive outlook to Tata Steel on Kalinganagar phase-2 commissioning and structural debt reduction",
                "yesterday_base_price_t0": 180.00,
                "annual_revenue_cr": 230000.0,
                "atr_percentage": 2.8,
                "technical_meta": {"ema_200": 165.0, "ema_50": 174.0, "rsi_14": 56.0, "nifty_change_pct": 0.10}
            }
        ]

    def run_prediction_engine(self) -> dict:
        signals = self.get_yesterday_signals()
        predictions = []

        print("\n=======================================================", flush=True)
        print("[TEST RUN] PREDICTING TODAY'S PRICES (T+1) FROM YESTERDAY'S SIGNALS", flush=True)
        print("Strict Zero-Live Price Rule Active: Base Price strictly locked at T-0", flush=True)
        print("=======================================================\n", flush=True)

        for s in signals:
            symbol = s["symbol"]
            headline = s["headline"]
            base_p = s["yesterday_base_price_t0"]
            atr_pct = s["atr_percentage"]

            # 1. NLP & Materiality
            comp_input = {
                "symbol": symbol,
                "company_name": s["company_name"],
                "sector": s["sector"],
                "annual_revenue_cr": s["annual_revenue_cr"],
                "atr_percentage": atr_pct
            }
            pred = self.scorer.analyze_event(headline, comp_input)
            pred_dir = pred["direction"].replace(" / UNCONFIRMED", "")
            is_rumor = pred.get("is_rumor", False)
            mat_ratio = pred.get("materiality_ratio", 0.0)

            if is_rumor:
                print(f"[FILTERED NOISE] {symbol} | Arrival: {s['signal_arrival_date']} {s['signal_arrival_time']} | Conviction: {pred['direction_confidence']}% (<65%) -> Abstaining (INR 0 Risk)", flush=True)
                predictions.append({
                    "id": s["id"],
                    "symbol": symbol,
                    "company_name": s["company_name"],
                    "signal_arrival_date": s["signal_arrival_date"],
                    "signal_arrival_time": s["signal_arrival_time"],
                    "source_type": s["source_type"],
                    "yesterday_base_price_inr": base_p,
                    "pipeline_status": "FILTERED_UNVERIFIED_RUMOR",
                    "conviction_score_pct": pred["direction_confidence"],
                    "recommendation": "NO TRADE (CAPITAL PROTECTED)",
                    "catalyst": headline
                })
                continue

            # 2. Vector RAG Match
            rag_matches = self.rag.search_similar_patterns(headline, sector=s["sector"])
            top_rag = rag_matches[0]["pattern"] if rag_matches else {}
            win_prob = top_rag.get("win_probability", 0.85)

            # 3. Technical Confluence
            conf = self.confluence.analyze_confluence(
                ltp=base_p,
                direction=pred_dir,
                news_confidence=pred["direction_confidence"],
                technical_meta=s["technical_meta"]
            )

            # 4. Multi-Horizon Mathematical Targets for TODAY (T+1), T+5, and T+10
            is_bull = pred_dir == "BULLISH"
            sign = 1.0 if is_bull else -1.0

            t1_min_pct = round(atr_pct * 0.8 * sign, 2)
            t1_max_pct = round((atr_pct * 1.8 + mat_ratio * 5.0) * sign, 2)
            t5_min_pct = round(t1_min_pct * 1.6, 2)
            t5_max_pct = round(t1_max_pct * 1.8, 2)
            t10_min_pct = round(t1_min_pct * 2.2, 2)
            t10_max_pct = round(t1_max_pct * 2.6, 2)

            # Predicted Exact Rupee Target Bounds for TODAY (Sep 28)
            today_low_inr = round(base_p * (1 + min(t1_min_pct, t1_max_pct) / 100.0), 2)
            today_high_inr = round(base_p * (1 + max(t1_min_pct, t1_max_pct) / 100.0), 2)

            # Stop Loss
            sl_pct = round(atr_pct * 1.2, 2)
            sl_price = round(base_p * (1 - sl_pct / 100.0), 2) if is_bull else round(base_p * (1 + sl_pct / 100.0), 2)

            # 5. Dynamic Kelly Sizing
            sizing = self.sizer.calculate_sizing(
                ltp=base_p,
                win_prob=win_prob,
                target_pct=abs(t1_max_pct),
                stop_loss_pct=sl_pct,
                confluence_multiplier=conf["confluence_multiplier"]
            )

            pred_record = {
                "id": s["id"],
                "symbol": symbol,
                "company_name": s["company_name"],
                "sector": s["sector"],
                "source_type": s["source_type"],
                "signal_arrival_date": s["signal_arrival_date"],
                "signal_arrival_time": s["signal_arrival_time"],
                "headline": headline,
                "yesterday_base_price_t0": base_p,
                "predicted_direction": pred_dir,
                "conviction_score_pct": pred["direction_confidence"],
                "adjusted_confluence_conviction": conf["final_adjusted_conviction"],
                "confluence_grade": conf["confluence_grade"],
                "materiality_ratio": mat_ratio,
                "predicted_todays_price_range": {
                    "target_horizon": "TODAY (Sep 28, 2026 Close)",
                    "expected_move_pct": f"{min(t1_min_pct, t1_max_pct):+.2f}% to {max(t1_min_pct, t1_max_pct):+.2f}%",
                    "predicted_price_bounds_inr": f"INR {today_low_inr:,.2f} - INR {today_high_inr:,.2f}"
                },
                "forward_5day_target_t5": {
                    "target_horizon": "Next 5 Days (Oct 05, 2026)",
                    "expected_move_pct": f"{min(t5_min_pct, t5_max_pct):+.2f}% to {max(t5_min_pct, t5_max_pct):+.2f}%",
                    "predicted_price_bounds_inr": f"INR {round(base_p*(1+min(t5_min_pct, t5_max_pct)/100.0), 2):,.2f} - INR {round(base_p*(1+max(t5_min_pct, t5_max_pct)/100.0), 2):,.2f}"
                },
                "forward_10day_target_t10": {
                    "target_horizon": "Next 10 Days (Oct 12, 2026)",
                    "expected_move_pct": f"{min(t10_min_pct, t10_max_pct):+.2f}% to {max(t10_min_pct, t10_max_pct):+.2f}%",
                    "predicted_price_bounds_inr": f"INR {round(base_p*(1+min(t10_min_pct, t10_max_pct)/100.0), 2):,.2f} - INR {round(base_p*(1+max(t10_min_pct, t10_max_pct)/100.0), 2):,.2f}"
                },
                "recommended_stop_loss": f"INR {sl_price:,.2f} ({'-' if is_bull else '+'}{sl_pct}%)",
                "kelly_capital_allocation_inr": sizing["allocated_capital_inr"],
                "recommended_shares_quantity": sizing["shares_quantity"],
                "max_risk_inr": sizing["max_stop_loss_risk_inr"],
                "top_historical_rag_match": top_rag.get("title", "Foundational Industry Template")
            }
            predictions.append(pred_record)

            print(f"[PREDICTION GENERATED] {symbol:<10} | Arrival: {s['signal_arrival_date']} {s['signal_arrival_time']} | Yest Price: INR {base_p:,.2f} -> TODAY PREDICTION: {today_low_inr:,.2f} - {today_high_inr:,.2f} ({min(t1_min_pct, t1_max_pct):+.2f}% to {max(t1_min_pct, t1_max_pct):+.2f}%)", flush=True)

        output_payload = {
            "test_run_name": "Yesterday's Signal Test Run -> Today's Forward Price Predictions",
            "run_timestamp": datetime.now().isoformat(),
            "total_yesterday_signals_ingested": len(signals),
            "actionable_useful_signals": len([p for p in predictions if p.get("pipeline_status") != "FILTERED_UNVERIFIED_RUMOR"]),
            "filtered_noise_signals": len([p for p in predictions if p.get("pipeline_status") == "FILTERED_UNVERIFIED_RUMOR"]),
            "predictions": predictions
        }

        os.makedirs("d:/sm/data/backtest_reports", exist_ok=True)
        report_file = "d:/sm/data/backtest_reports/yesterday_signals_today_predictions.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(output_payload, f, indent=2, ensure_ascii=False)

        print(f"\n[COMPLETE] Generated predictions for {len(predictions)} setups. Saved to {report_file}")
        return output_payload

if __name__ == "__main__":
    predictor = YesterdaySignalsTodayPredictor()
    predictor.run_prediction_engine()
