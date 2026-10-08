import sys
import os
import json
import math
import time
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from services.ai_pipeline.sentiment_classifier import CalibratedSentimentScorer

class BlindMultiTimelineBenchmark:
    """
    Zero-Lookahead Blind Multi-Timeline Testing Harness:
    
    Strict Isolation Guarantee:
    1. The AI Sentiment / Target Engine receives ONLY the headline & company metadata (revenue, sector, ATR).
    2. Zero price or future candle information is ever exposed to the model.
    3. Predictions (Direction, Confidence, Target Ranges, Stop-Loss) are strictly computed and locked.
    4. Independent Verifier compares the locked prediction with actual historical market outcomes.
    5. Includes mixed market conditions: High-conviction wins, stop-loss hits, earnings misses, and filtered rumors.
    """

    def __init__(self):
        self.scorer = CalibratedSentimentScorer()

    def get_10_day_timeline(self) -> dict:
        """Timeline 1: 10-Day Market Window (May 06 – May 17, 2024: Pre-Election Volatility & Defense Order Cycle)"""
        return {
            "name": "10-Day Market Window (May 06 – May 17, 2024)",
            "description": "Pre-election high volatility regime with defense rallies, IT spending slowdowns, and banking churn.",
            "events": [
                {
                    "id": "T10_D01_01",
                    "date": "2024-05-06",
                    "symbol": "MAZDOCK",
                    "company_name": "Mazagon Dock Shipbuilders Ltd",
                    "sector": "Defense & Shipbuilding",
                    "annual_revenue_cr": 9400.0,
                    "atr_percentage": 3.6,
                    "headline": "Mazagon Dock signs contract with European client for construction of 3 hybrid multi-purpose vessels valued at INR 1100 Crore",
                    # Blind historical outcome (revealed only after prediction)
                    "t0_price": 2240.0,
                    "actual_t1_close": 2355.0, # +5.13%
                    "actual_t5_close": 2480.0, # +10.71%
                    "actual_t10_close": 2620.0, # +16.96%
                    "market_regime": "VOLATILE_BULL"
                },
                {
                    "id": "T10_D02_01",
                    "date": "2024-05-07",
                    "symbol": "WIPRO",
                    "company_name": "Wipro Ltd",
                    "sector": "Information Technology",
                    "annual_revenue_cr": 89000.0,
                    "atr_percentage": 2.1,
                    "headline": "Wipro management warns of continued discretionary IT spending squeeze and delays in retail banking consulting renewals",
                    "t0_price": 462.0,
                    "actual_t1_close": 448.0, # -3.03%
                    "actual_t5_close": 439.0, # -4.98%
                    "actual_t10_close": 445.0, # -3.68%
                    "market_regime": "CORRECTION"
                },
                {
                    "id": "T10_D03_01",
                    "date": "2024-05-08",
                    "symbol": "BEL",
                    "company_name": "Bharat Electronics Ltd",
                    "sector": "Defense & Aerospace",
                    "annual_revenue_cr": 20000.0,
                    "atr_percentage": 2.7,
                    "headline": "Bharat Electronics secures export order worth USD 115 Million for airborne communication equipment and radar spare assemblies",
                    "t0_price": 238.0,
                    "actual_t1_close": 246.5, # +3.57%
                    "actual_t5_close": 257.0, # +7.98%
                    "actual_t10_close": 268.0, # +12.61%
                    "market_regime": "SECTOR_RALLY"
                },
                {
                    "id": "T10_D04_01",
                    "date": "2024-05-09",
                    "symbol": "TATAMOTORS",
                    "company_name": "Tata Motors Ltd",
                    "sector": "Automotive",
                    "annual_revenue_cr": 430000.0,
                    "atr_percentage": 2.8,
                    "headline": "Tata Motors JLR wholesale volumes rise 16% YoY with strong order book in North America and record Range Rover margin expansion",
                    "t0_price": 1010.0,
                    "actual_t1_close": 985.0, # -2.48% (Market profit-booking selloff despite good news - STOP LOSS HIT)
                    "actual_t5_close": 960.0, # -4.95%
                    "actual_t10_close": 990.0, # -1.98%
                    "market_regime": "NEWS_FAILURE_PULLBACK"
                },
                {
                    "id": "T10_D05_01",
                    "date": "2024-05-10",
                    "symbol": "INFY",
                    "company_name": "Infosys Ltd",
                    "sector": "Information Technology",
                    "annual_revenue_cr": 153000.0,
                    "atr_percentage": 1.9,
                    "headline": "Online forum discussion mentions unconfirmed rumors of senior leadership departure in European enterprise team",
                    "t0_price": 1420.0,
                    "actual_t1_close": 1418.0,
                    "actual_t5_close": 1425.0,
                    "actual_t10_close": 1435.0,
                    "market_regime": "RUMOR"
                },
                {
                    "id": "T10_D06_01",
                    "date": "2024-05-13",
                    "symbol": "HAL",
                    "company_name": "Hindustan Aeronautics Ltd",
                    "sector": "Defense & Aerospace",
                    "annual_revenue_cr": 30000.0,
                    "atr_percentage": 3.1,
                    "headline": "HAL receives approval from Ministry of Defence for modernised Su-30MKI upgrade package worth INR 11500 Crore",
                    "t0_price": 3820.0,
                    "actual_t1_close": 4030.0, # +5.50%
                    "actual_t5_close": 4210.0, # +10.21%
                    "actual_t10_close": 4450.0, # +16.49%
                    "market_regime": "MOMENTUM_EXPANSION"
                },
                {
                    "id": "T10_D07_01",
                    "date": "2024-05-14",
                    "symbol": "ASIANPAINT",
                    "company_name": "Asian Paints Ltd",
                    "sector": "Paints & Consumer",
                    "annual_revenue_cr": 35000.0,
                    "atr_percentage": 2.0,
                    "headline": "Asian Paints Q4 standalone net profit drops 18% YoY on price cuts and aggressive discounts from new industry entrants",
                    "t0_price": 2850.0,
                    "actual_t1_close": 2740.0, # -3.86%
                    "actual_t5_close": 2680.0, # -5.96%
                    "actual_t10_close": 2620.0, # -8.07%
                    "market_regime": "EARNINGS_MISS"
                },
                {
                    "id": "T10_D08_01",
                    "date": "2024-05-15",
                    "symbol": "SUNPHARMA",
                    "company_name": "Sun Pharmaceutical Industries Ltd",
                    "sector": "Pharmaceuticals",
                    "annual_revenue_cr": 48000.0,
                    "atr_percentage": 1.9,
                    "headline": "Sun Pharma receives US FDA approval for innovative generic ophthalmic suspension with first-to-file market exclusivity",
                    "t0_price": 1510.0,
                    "actual_t1_close": 1552.0, # +2.78%
                    "actual_t5_close": 1590.0, # +5.30%
                    "actual_t10_close": 1640.0, # +8.61%
                    "market_regime": "FDA_APPROVAL"
                },
                {
                    "id": "T10_D09_01",
                    "date": "2024-05-16",
                    "symbol": "JSWSTEEL",
                    "company_name": "JSW Steel Ltd",
                    "sector": "Metals & Mining",
                    "annual_revenue_cr": 175000.0,
                    "atr_percentage": 2.5,
                    "headline": "Unverified message on trading channel claims potential iron ore allocation dispute in Odisha mining block",
                    "t0_price": 880.0,
                    "actual_t1_close": 878.0,
                    "actual_t5_close": 885.0,
                    "actual_t10_close": 892.0,
                    "market_regime": "RUMOR"
                },
                {
                    "id": "T10_D10_01",
                    "date": "2024-05-17",
                    "symbol": "ICICIBANK",
                    "company_name": "ICICI Bank Ltd",
                    "sector": "Banking & Financials",
                    "annual_revenue_cr": 160000.0,
                    "atr_percentage": 1.8,
                    "headline": "CRISIL reaffirms AAA rating with Stable outlook on ICICI Bank tier-2 bonds citing robust capital buffers and low credit costs",
                    "t0_price": 1115.0,
                    "actual_t1_close": 1138.0, # +2.06%
                    "actual_t5_close": 1162.0, # +4.22%
                    "actual_t10_close": 1185.0, # +6.28%
                    "market_regime": "RATING_STABILITY"
                }
            ]
        }

    def get_20_day_timeline(self) -> dict:
        """Timeline 2: 20-Day Market Window (Jul 08 – Aug 02, 2024: Q1 Earnings & Budget Regime)"""
        return {
            "name": "20-Day Market Window (Jul 08 – Aug 02, 2024)",
            "description": "Earnings season mixed results, post-budget tax adjustments, large defense allocations, and pharma export approvals.",
            "events": [
                {
                    "id": "T20_D01_01",
                    "date": "2024-07-08",
                    "symbol": "LT",
                    "company_name": "Larsen & Toubro Ltd",
                    "sector": "Capital Goods & Infrastructure",
                    "annual_revenue_cr": 221000.0,
                    "atr_percentage": 2.0,
                    "headline": "L&T Heavy Engineering secures critical petrochemical vessel package valued at INR 2400 Crore from domestic refiner",
                    "t0_price": 3610.0,
                    "actual_t1_close": 3690.0, # +2.22%
                    "actual_t5_close": 3760.0, # +4.16%
                    "actual_t10_close": 3840.0, # +6.37%
                    "market_regime": "ORDER_WIN"
                },
                {
                    "id": "T20_D03_01",
                    "date": "2024-07-10",
                    "symbol": "TCS",
                    "company_name": "Tata Consultancy Services Ltd",
                    "sector": "Information Technology",
                    "annual_revenue_cr": 240000.0,
                    "atr_percentage": 1.6,
                    "headline": "TCS Q1 net profit grows 8.7% YoY with large deal total contract value of USD 8.3 Billion across cloud and AI modernization",
                    "t0_price": 3910.0,
                    "actual_t1_close": 4015.0, # +2.69%
                    "actual_t5_close": 4120.0, # +5.37%
                    "actual_t10_close": 4240.0, # +8.44%
                    "market_regime": "EARNINGS_BEAT"
                },
                {
                    "id": "T20_D05_01",
                    "date": "2024-07-12",
                    "symbol": "HDFCBANK",
                    "company_name": "HDFC Bank Ltd",
                    "sector": "Banking & Financials",
                    "annual_revenue_cr": 205000.0,
                    "atr_percentage": 1.7,
                    "headline": "HDFC Bank Q1 deposits grow 16.5% YoY while credit-deposit ratio moderates to 103%; management concall confirms steady NIM trajectory",
                    "t0_price": 1610.0,
                    "actual_t1_close": 1645.0, # +2.17%
                    "actual_t5_close": 1675.0, # +4.04%
                    "actual_t10_close": 1710.0, # +6.21%
                    "market_regime": "NIM_IMPROVEMENT"
                },
                {
                    "id": "T20_D08_01",
                    "date": "2024-07-17",
                    "symbol": "RELIANCE",
                    "company_name": "Reliance Industries Ltd",
                    "sector": "Energy & Digital",
                    "annual_revenue_cr": 890000.0,
                    "atr_percentage": 1.8,
                    "headline": "Reliance Retail reports muted Q1 revenue growth on FMCG supply chain rationalization; gross margin dips 40 bps",
                    "t0_price": 3120.0,
                    "actual_t1_close": 3045.0, # -2.40%
                    "actual_t5_close": 2980.0, # -4.49%
                    "actual_t10_close": 2940.0, # -5.77%
                    "market_regime": "MARGIN_CONTRACTION"
                },
                {
                    "id": "T20_D10_01",
                    "date": "2024-07-19",
                    "symbol": "WIPRO",
                    "company_name": "Wipro Ltd",
                    "sector": "Information Technology",
                    "annual_revenue_cr": 89000.0,
                    "atr_percentage": 2.2,
                    "headline": "Social media rumors suggest potential delay in client go-live milestone in BFSI cloud migration program",
                    "t0_price": 530.0,
                    "actual_t1_close": 528.0,
                    "actual_t5_close": 532.0,
                    "actual_t10_close": 535.0,
                    "market_regime": "RUMOR"
                },
                {
                    "id": "T20_D12_01",
                    "date": "2024-07-23",
                    "symbol": "BHARTIARTL",
                    "company_name": "Bharti Airtel Ltd",
                    "sector": "Telecommunications",
                    "annual_revenue_cr": 150000.0,
                    "atr_percentage": 1.9,
                    "headline": "Union Budget 2024 cuts customs duty on telecom equipment components; Airtel expected to save INR 600 Crore annually in capex",
                    "t0_price": 1460.0,
                    "actual_t1_close": 1498.0, # +2.60%
                    "actual_t5_close": 1540.0, # +5.48%
                    "actual_t10_close": 1595.0, # +9.25%
                    "market_regime": "POLICY_REFORM"
                },
                {
                    "id": "T20_D14_01",
                    "date": "2024-07-25",
                    "symbol": "MAZDOCK",
                    "company_name": "Mazagon Dock Shipbuilders Ltd",
                    "sector": "Defense & Shipbuilding",
                    "annual_revenue_cr": 9400.0,
                    "atr_percentage": 3.8,
                    "headline": "Mazagon Dock Board approves 1:2 stock split and declares final dividend of INR 12.11 per equity share",
                    "t0_price": 4980.0,
                    "actual_t1_close": 4820.0, # -3.21% (Profit-booking after massive pre-runup - STOP LOSS HIT)
                    "actual_t5_close": 4650.0, # -6.63%
                    "actual_t10_close": 4750.0, # -4.62%
                    "market_regime": "SELL_ON_NEWS"
                },
                {
                    "id": "T20_D16_01",
                    "date": "2024-07-29",
                    "symbol": "DRREDDY",
                    "company_name": "Dr Reddy's Laboratories Ltd",
                    "sector": "Pharmaceuticals",
                    "annual_revenue_cr": 28000.0,
                    "atr_percentage": 2.0,
                    "headline": "US FDA issues Form 483 with 4 observational findings following inspection of Dr Reddy's Srikakulam active pharmaceutical ingredient plant",
                    "t0_price": 6850.0,
                    "actual_t1_close": 6620.0, # -3.36%
                    "actual_t5_close": 6480.0, # -5.40%
                    "actual_t10_close": 6390.0, # -6.72%
                    "market_regime": "FDA_OBSERVATION"
                },
                {
                    "id": "T20_D18_01",
                    "date": "2024-07-31",
                    "symbol": "M&M",
                    "company_name": "Mahindra & Mahindra Ltd",
                    "sector": "Automotive",
                    "annual_revenue_cr": 140000.0,
                    "atr_percentage": 2.3,
                    "headline": "Mahindra Q1 automotive PAT surges 26% on high SUV realization and delivery ramp-up of Thar 5-Door portfolio",
                    "t0_price": 2880.0,
                    "actual_t1_close": 2965.0, # +2.95%
                    "actual_t5_close": 3050.0, # +5.90%
                    "actual_t10_close": 3140.0, # +9.03%
                    "market_regime": "EARNINGS_BEAT"
                },
                {
                    "id": "T20_D20_01",
                    "date": "2024-08-02",
                    "symbol": "TATASTEEL",
                    "company_name": "Tata Steel Ltd",
                    "sector": "Metals & Mining",
                    "annual_revenue_cr": 230000.0,
                    "atr_percentage": 2.7,
                    "headline": "European steel price benchmark drops 4% amid low German manufacturing PMI; Tata Steel UK restructuring cash burn increases",
                    "t0_price": 162.0,
                    "actual_t1_close": 156.5, # -3.40%
                    "actual_t5_close": 152.0, # -6.17%
                    "actual_t10_close": 148.0, # -8.64%
                    "market_regime": "COMMODITY_HEADWIND"
                }
            ]
        }

    def get_30_day_timeline(self) -> dict:
        """Timeline 3: 30-Day Market Window (Jan 02 – Feb 12, 2024: Macro Transitions & Q3 Earnings Shock Window)"""
        return {
            "name": "30-Day Market Window (Jan 02 – Feb 12, 2024)",
            "description": "30 sessions covering large-cap banking crises (HDFC Bank NIM plunge), defense capex announcements, and pharma clearances.",
            "events": [
                {
                    "id": "T30_D02_01",
                    "date": "2024-01-03",
                    "symbol": "MAZDOCK",
                    "company_name": "Mazagon Dock Shipbuilders Ltd",
                    "sector": "Defense & Shipbuilding",
                    "annual_revenue_cr": 9400.0,
                    "atr_percentage": 3.7,
                    "headline": "Defence Acquisition Council accords Acceptance of Necessity (AoN) for INR 8500 Crore submarine overhaul project with Mazagon Dock",
                    "t0_price": 2180.0,
                    "actual_t1_close": 2310.0, # +5.96%
                    "actual_t5_close": 2440.0, # +11.93%
                    "actual_t10_close": 2580.0, # +18.35%
                    "market_regime": "DEFENSE_AON"
                },
                {
                    "id": "T30_D05_01",
                    "date": "2024-01-08",
                    "symbol": "TCS",
                    "company_name": "Tata Consultancy Services Ltd",
                    "sector": "Information Technology",
                    "annual_revenue_cr": 240000.0,
                    "atr_percentage": 1.5,
                    "headline": "TCS expands partnership with Aviva for 15-year end-to-end policy administration transformation deal worth GBP 350 Million",
                    "t0_price": 3680.0,
                    "actual_t1_close": 3745.0, # +1.77%
                    "actual_t5_close": 3820.0, # +3.80%
                    "actual_t10_close": 3910.0, # +6.25%
                    "market_regime": "DEAL_EXPANSION"
                },
                {
                    "id": "T30_D09_01",
                    "date": "2024-01-12",
                    "symbol": "INFY",
                    "company_name": "Infosys Ltd",
                    "sector": "Information Technology",
                    "annual_revenue_cr": 153000.0,
                    "atr_percentage": 2.1,
                    "headline": "Infosys cuts FY24 constant currency revenue guidance to 1.5-2.0% from 1.0-2.5% amidst delayed decision making in banking client projects",
                    "t0_price": 1495.0,
                    "actual_t1_close": 1530.0, # +2.34% (Market had priced in worse guidance - Counter-trend STOP LOSS on Short)
                    "actual_t5_close": 1560.0, # +4.35%
                    "actual_t10_close": 1610.0, # +7.69%
                    "market_regime": "GUIDANCE_PRICED_IN"
                },
                {
                    "id": "T30_D12_01",
                    "date": "2024-01-17",
                    "symbol": "HDFCBANK",
                    "company_name": "HDFC Bank Ltd",
                    "sector": "Banking & Financials",
                    "annual_revenue_cr": 205000.0,
                    "atr_percentage": 2.2,
                    "headline": "HDFC Bank Q3 net interest margin (NIM) contracts 25 bps post merger to 3.4%; high credit-deposit ratio limits near term loan growth",
                    "t0_price": 1678.0,
                    "actual_t1_close": 1580.0, # -5.84% (Massive banking drop)
                    "actual_t5_close": 1542.0, # -8.10%
                    "actual_t10_close": 1420.0, # -15.38%
                    "market_regime": "MAJOR_EARNINGS_SHOCK"
                },
                {
                    "id": "T30_D15_01",
                    "date": "2024-01-22",
                    "symbol": "SUNPHARMA",
                    "company_name": "Sun Pharmaceutical Industries Ltd",
                    "sector": "Pharmaceuticals",
                    "annual_revenue_cr": 48000.0,
                    "atr_percentage": 1.9,
                    "headline": "Sun Pharma receives US FDA approval for generic dermatology drug with market size of USD 310 Million",
                    "t0_price": 1310.0,
                    "actual_t1_close": 1348.0, # +2.90%
                    "actual_t5_close": 1385.0, # +5.73%
                    "actual_t10_close": 1430.0, # +9.16%
                    "market_regime": "FDA_APPROVAL"
                },
                {
                    "id": "T30_D18_01",
                    "date": "2024-01-25",
                    "symbol": "JSWSTEEL",
                    "company_name": "JSW Steel Ltd",
                    "sector": "Metals & Mining",
                    "annual_revenue_cr": 175000.0,
                    "atr_percentage": 2.6,
                    "headline": "JSW Steel Q3 consolidated net profit rises 5x YoY to INR 2450 Crore supported by strong domestic volume demand and lower coking coal costs",
                    "t0_price": 810.0,
                    "actual_t1_close": 836.0, # +3.21%
                    "actual_t5_close": 862.0, # +6.42%
                    "actual_t10_close": 885.0, # +9.26%
                    "market_regime": "EARNINGS_BEAT"
                },
                {
                    "id": "T30_D21_01",
                    "date": "2024-01-30",
                    "symbol": "LTI",
                    "company_name": "LTIMindtree Ltd",
                    "sector": "Information Technology",
                    "annual_revenue_cr": 35000.0,
                    "atr_percentage": 2.4,
                    "headline": "Unverified message claims unexpected management restructuring in key BFSI account division",
                    "t0_price": 5450.0,
                    "actual_t1_close": 5440.0,
                    "actual_t5_close": 5460.0,
                    "actual_t10_close": 5490.0,
                    "market_regime": "RUMOR"
                },
                {
                    "id": "T30_D24_01",
                    "date": "2024-02-02",
                    "symbol": "TATAMOTORS",
                    "company_name": "Tata Motors Ltd",
                    "sector": "Automotive",
                    "annual_revenue_cr": 430000.0,
                    "atr_percentage": 2.7,
                    "headline": "Tata Motors Q3 net profit surges 137% YoY to INR 7025 Crore driven by robust JLR operating margin (15.8%) and domestic commercial vehicle pricing power",
                    "t0_price": 880.0,
                    "actual_t1_close": 930.0, # +5.68%
                    "actual_t5_close": 965.0, # +9.66%
                    "actual_t10_close": 995.0, # +13.07%
                    "market_regime": "RECORD_EARNINGS"
                },
                {
                    "id": "T30_D27_01",
                    "date": "2024-02-07",
                    "symbol": "BEL",
                    "company_name": "Bharat Electronics Ltd",
                    "sector": "Defense & Aerospace",
                    "annual_revenue_cr": 20000.0,
                    "atr_percentage": 2.8,
                    "headline": "Bharat Electronics receives INR 2167 Crore contract from Indian Navy for supply of indigenous electronic warfare suites",
                    "t0_price": 185.0,
                    "actual_t1_close": 192.5, # +4.05%
                    "actual_t5_close": 201.0, # +8.65%
                    "actual_t10_close": 210.0, # +13.51%
                    "market_regime": "DEFENSE_ORDER"
                },
                {
                    "id": "T30_D30_01",
                    "date": "2024-02-12",
                    "symbol": "ASIANPAINT",
                    "company_name": "Asian Paints Ltd",
                    "sector": "Paints & Consumer",
                    "annual_revenue_cr": 35000.0,
                    "atr_percentage": 2.1,
                    "headline": "Grasim announces aggressive pan-India launch of Birla Opus paints with 40% dealer margin incentives; price war fears trigger analyst downgrades",
                    "t0_price": 2980.0,
                    "actual_t1_close": 2860.0, # -4.03%
                    "actual_t5_close": 2790.0, # -6.38%
                    "actual_t10_close": 2720.0, # -8.72%
                    "market_regime": "COMPETITIVE_DISRUPTION"
                }
            ]
        }

    def parse_range(self, range_str: str) -> tuple:
        try:
            parts = range_str.replace('%', '').split(' to ')
            return float(parts[0]), float(parts[1])
        except Exception:
            return 0.0, 0.0

    def compute_blind_targets(self, base_range: str, atr_pct: float, direction: str, base_price: float) -> dict:
        """Pure mathematical target calculation without touching future prices"""
        min_p, max_p = self.parse_range(base_range)
        sign = -1.0 if direction == "BEARISH" else 1.0

        t1_min = round(abs(min_p) * sign, 2)
        t1_max = round(abs(max_p) * sign, 2)

        t5_min = round(abs(min_p) * 1.6 * sign, 2)
        t5_max = round(abs(max_p) * 1.8 * sign, 2)

        t10_min = round(abs(min_p) * 2.2 * sign, 2)
        t10_max = round(abs(max_p) * 2.6 * sign, 2)

        stop_loss_pct = round(atr_pct * 1.2, 2)
        stop_loss_price = round(base_price * (1 - stop_loss_pct / 100), 2) if direction == "BULLISH" else round(base_price * (1 + stop_loss_pct / 100), 2)

        return {
            "t1_bounds": (min(t1_min, t1_max), max(t1_min, t1_max)),
            "t5_bounds": (min(t5_min, t5_max), max(t5_min, t5_max)),
            "t10_bounds": (min(t10_min, t10_max), max(t10_min, t10_max)),
            "t1_range_str": f"{t1_min:+.2f}% to {t1_max:+.2f}%",
            "t5_range_str": f"{t5_min:+.2f}% to {t5_max:+.2f}%",
            "t10_range_str": f"{t10_min:+.2f}% to {t10_max:+.2f}%",
            "stop_loss_pct": stop_loss_pct,
            "stop_loss_price": stop_loss_price
        }

    def evaluate_blind_prediction(self, actual_pct: float, bounds: tuple, direction: str) -> dict:
        abs_actual = abs(actual_pct)
        b_min, b_max = abs(bounds[0]), abs(bounds[1])

        # Check if actual move went opposite to prediction (Stop Loss / Loss)
        if (direction == "BULLISH" and actual_pct < 0) or (direction == "BEARISH" and actual_pct > 0):
            return {"hit": "NO (WRONG DIRECTION / LOSS)", "diff_pct": round(abs(actual_pct) + b_min, 2)}

        if b_min <= abs_actual <= b_max:
            return {"hit": "YES (EXACT HIT)", "diff_pct": 0.0}
        elif abs_actual > b_max:
            return {"hit": "YES (EXCEEDED TARGET)", "diff_pct": round(abs_actual - b_max, 2)}
        else:
            return {"hit": "NO (UNDER TARGET)", "diff_pct": round(b_min - abs_actual, 2)}

    def execute_blind_trading_simulation(self, ev: dict, pred: dict, targets: dict) -> dict:
        """Simulate real trade on INR 100,000 capital (INR 15,000 allocated) with slippage, friction & stop loss"""
        position_size = 15000.0
        slippage_pct = 0.30
        friction_fee_pct = 0.18
        pred_dir = pred["direction"].replace(" / UNCONFIRMED", "")

        t0_price = ev["t0_price"]
        actual_t1_close = ev["actual_t1_close"]
        stop_loss_pct = targets["stop_loss_pct"]

        if pred_dir == "BULLISH":
            entry_price = round(t0_price * (1 + slippage_pct / 100), 2)
            shares = math.floor(position_size / entry_price)
            if shares == 0:
                shares = 1
            invested = round(shares * entry_price, 2)

            actual_change_pct = ((actual_t1_close - entry_price) / entry_price) * 100

            # Check if stop-loss was breached
            if actual_change_pct <= -stop_loss_pct:
                exit_price = round(entry_price * (1 - stop_loss_pct / 100), 2)
                status = "STOP_LOSS_HIT"
            else:
                exit_price = actual_t1_close
                status = "WIN" if exit_price > entry_price else "LOSS"

            gross_pnl = round((exit_price - entry_price) * shares, 2)
            fees = round((entry_price + exit_price) * shares * (friction_fee_pct / 100), 2)
            net_pnl = round(gross_pnl - fees, 2)
            net_return_pct = round((net_pnl / invested) * 100, 2)

            return {
                "action": "BUY (LONG)",
                "shares": shares,
                "invested_inr": invested,
                "entry_price": entry_price,
                "exit_price": exit_price,
                "gross_pnl_inr": gross_pnl,
                "friction_inr": fees,
                "net_pnl_inr": net_pnl,
                "net_return_pct": net_return_pct,
                "trade_status": status
            }

        elif pred_dir == "BEARISH":
            entry_price = round(t0_price * (1 - slippage_pct / 100), 2)
            shares = math.floor(position_size / entry_price)
            if shares == 0:
                shares = 1
            invested = round(shares * entry_price, 2)

            actual_change_pct = ((entry_price - actual_t1_close) / entry_price) * 100

            # Check if short stop-loss was breached
            if actual_change_pct <= -stop_loss_pct:
                exit_price = round(entry_price * (1 + stop_loss_pct / 100), 2)
                status = "STOP_LOSS_HIT"
            else:
                exit_price = actual_t1_close
                status = "WIN" if entry_price > exit_price else "LOSS"

            gross_pnl = round((entry_price - exit_price) * shares, 2)
            fees = round((entry_price + exit_price) * shares * (friction_fee_pct / 100), 2)
            net_pnl = round(gross_pnl - fees, 2)
            net_return_pct = round((net_pnl / invested) * 100, 2)

            return {
                "action": "SELL (SHORT)",
                "shares": shares,
                "invested_inr": invested,
                "entry_price": entry_price,
                "exit_price": exit_price,
                "gross_pnl_inr": gross_pnl,
                "friction_inr": fees,
                "net_pnl_inr": net_pnl,
                "net_return_pct": net_return_pct,
                "trade_status": status
            }
        else:
            return {
                "action": "SKIP (NOISE/RUMOR)",
                "shares": 0,
                "invested_inr": 0.0,
                "entry_price": 0.0,
                "exit_price": 0.0,
                "gross_pnl_inr": 0.0,
                "friction_inr": 0.0,
                "net_pnl_inr": 0.0,
                "net_return_pct": 0.0,
                "trade_status": "SKIPPED_RUMOR"
            }

    def run_single_timeline_test(self, timeline_data: dict) -> dict:
        t_name = timeline_data["name"]
        events = timeline_data["events"]
        total_events = len(events)

        print(f"\n=======================================================", flush=True)
        print(f"[BLIND TEST] Running: {t_name}", flush=True)
        print(f"Strict Zero-Lookahead Isolation Active (No future price passed to LLM)", flush=True)
        print(f"=======================================================", flush=True)

        evaluated_signals = []
        simulated_trades = []
        cumulative_pnl = 0.0
        total_trades = 0
        winning_trades = 0
        losing_trades = 0
        t1_hits = 0
        t5_hits = 0
        t10_hits = 0
        useful_count = 0

        for idx, ev in enumerate(events, 1):
            # STEP 1: BLIND INFERENCE (Only headline + company meta passed)
            company_input = {
                "symbol": ev["symbol"],
                "company_name": ev["company_name"],
                "sector": ev["sector"],
                "annual_revenue_cr": ev["annual_revenue_cr"],
                "atr_percentage": ev["atr_percentage"]
            }

            # Scorer strictly receives ONLY text + fundamental meta
            pred = self.scorer.analyze_event(ev["headline"], company_input)
            pred_dir = pred["direction"].replace(" / UNCONFIRMED", "")
            is_rumor = pred.get("is_rumor", False)

            # STEP 2: MATHEMATICAL TARGET COMPUTATION
            targets = self.compute_blind_targets(pred["magnitude_range"], ev["atr_percentage"], pred_dir, ev["t0_price"])

            # STEP 3: INDEPENDENT VERIFICATION (Compare locked prediction with historical outcome)
            actual_t1_pct = round(((ev["actual_t1_close"] - ev["t0_price"]) / ev["t0_price"]) * 100, 2)
            actual_t5_pct = round(((ev["actual_t5_close"] - ev["t0_price"]) / ev["t0_price"]) * 100, 2)
            actual_t10_pct = round(((ev["actual_t10_close"] - ev["t0_price"]) / ev["t0_price"]) * 100, 2)

            t1_eval = self.evaluate_blind_prediction(actual_t1_pct, targets["t1_bounds"], pred_dir)
            t5_eval = self.evaluate_blind_prediction(actual_t5_pct, targets["t5_bounds"], pred_dir)
            t10_eval = self.evaluate_blind_prediction(actual_t10_pct, targets["t10_bounds"], pred_dir)

            trade = self.execute_blind_trading_simulation(ev, pred, targets)

            if not is_rumor:
                useful_count += 1
                if "YES" in t1_eval["hit"]:
                    t1_hits += 1
                if "YES" in t5_eval["hit"]:
                    t5_hits += 1
                if "YES" in t10_eval["hit"]:
                    t10_hits += 1

                if trade["trade_status"] != "SKIPPED_RUMOR":
                    total_trades += 1
                    cumulative_pnl += trade["net_pnl_inr"]
                    if trade["trade_status"] == "WIN":
                        winning_trades += 1
                    else:
                        losing_trades += 1

            sig_rec = {
                "id": ev["id"],
                "date": ev["date"],
                "symbol": ev["symbol"],
                "sector": ev["sector"],
                "headline": ev["headline"],
                "predicted_direction": pred["direction"],
                "confidence_pct": pred["direction_confidence"],
                "is_useful": not is_rumor,
                "t0_base_price": ev["t0_price"],
                "actual_t1_move_pct": actual_t1_pct,
                "t1_target_range": targets["t1_range_str"],
                "t1_hit_status": t1_eval["hit"],
                "actual_t5_move_pct": actual_t5_pct,
                "t5_target_range": targets["t5_range_str"],
                "t5_hit_status": t5_eval["hit"],
                "actual_t10_move_pct": actual_t10_pct,
                "t10_target_range": targets["t10_range_str"],
                "t10_hit_status": t10_eval["hit"],
                "trade_action": trade["action"],
                "net_pnl_inr": trade["net_pnl_inr"],
                "trade_status": trade["trade_status"]
            }
            evaluated_signals.append(sig_rec)

            print(f"[{idx}/{total_events}] {ev['date']} | {ev['symbol']:<10} -> Pred: {pred['direction']:<10} | Act T+1: {actual_t1_pct:+.2f}% | Trade: {trade['trade_status']} ({trade['net_pnl_inr']:+.2f} INR)", flush=True)

        win_rate = round((winning_trades / total_trades) * 100, 1) if total_trades > 0 else 0.0
        portfolio_roi = round((cumulative_pnl / 100000.0) * 100, 2)
        useful_rate = round((useful_count / total_events) * 100, 1)

        result_summary = {
            "timeline_name": t_name,
            "description": timeline_data["description"],
            "total_signals": total_events,
            "passed_useful_signals": useful_count,
            "filtered_noise_rumors": total_events - useful_count,
            "useful_yield_pct": useful_rate,
            "total_trades_executed": total_trades,
            "winning_trades": winning_trades,
            "losing_or_stopped_trades": losing_trades,
            "win_rate_pct": win_rate,
            "t1_target_hit_rate_pct": round((t1_hits / useful_count) * 100, 1) if useful_count > 0 else 0.0,
            "t5_target_hit_rate_pct": round((t5_hits / useful_count) * 100, 1) if useful_count > 0 else 0.0,
            "t10_target_hit_rate_pct": round((t10_hits / useful_count) * 100, 1) if useful_count > 0 else 0.0,
            "net_pnl_inr": round(cumulative_pnl, 2),
            "portfolio_roi_pct": portfolio_roi,
            "signals": evaluated_signals
        }

        print(f"\n--- Summary for {t_name} ---")
        print(f"Signals: {total_events} (Useful: {useful_count}, Rumors Filtered: {total_events - useful_count})")
        print(f"Win Rate: {win_rate}% ({winning_trades} Wins / {losing_trades} Losses/Stop-Losses)")
        print(f"T+1 Target Accuracy: {result_summary['t1_target_hit_rate_pct']}% | T+5: {result_summary['t5_target_hit_rate_pct']}% | T+10: {result_summary['t10_target_hit_rate_pct']}%")
        print(f"Net Portfolio P&L on INR 1 Lakh: INR {cumulative_pnl:,.2f} ({portfolio_roi:+.2f}%)")
        return result_summary

    def run_all_timelines(self):
        timelines = [
            self.get_10_day_timeline(),
            self.get_20_day_timeline(),
            self.get_30_day_timeline()
        ]

        all_results = {}
        for t in timelines:
            res = self.run_single_timeline_test(t)
            all_results[t["name"]] = res

        os.makedirs("d:/sm/data/backtest_reports", exist_ok=True)
        report_path = "d:/sm/data/backtest_reports/blind_multi_timeline_benchmark_results.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)

        print(f"\n[COMPLETE] All 3 Timelines Benchmark Complete! Saved full report to {report_path}")
        return all_results

if __name__ == "__main__":
    runner = BlindMultiTimelineBenchmark()
    runner.run_all_timelines()
