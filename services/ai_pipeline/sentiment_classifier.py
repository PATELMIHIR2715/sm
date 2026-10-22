import sys
import os
import re
import json
from typing import Dict, Any, Optional

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from services.ai_pipeline.llm_router import LLMRouter
from services.ai_pipeline.rag_engine import CPUHistoricalRAGEngine

class CalibratedSentimentScorer:
    """
    Quantitative Event Archetype & Materiality Engine (Audit Mandate 3):
    - Enforces hard materiality hurdles:
        * Contract / Order size must be >= 3.0% of Annual Revenue (or >= ₹50 Cr if revenue unknown).
        * Re-classifies immaterial orders (< 3.0%) to NEUTRAL (Zero False Breakout alerts).
    - Eliminates "Sell-The-News" Dividend Traps:
        * Routine interim dividends re-classified to NEUTRAL / NON-ACTIONABLE unless special payout/buyback.
    - Eliminates Naked Microcap Short Traps:
        * Operational closures in microcap / non-F&O equities re-classified to NON_EXECUTABLE_SHORT.
    - Discounts Long-Gestation Capex:
        * Capacity expansions without near-term revenue visibility capped to +1.5% alpha.
    """

    def __init__(self):
        self.llm_router = LLMRouter()
        self.rag_engine = CPUHistoricalRAGEngine()

    def _extract_order_value_cr(self, text: str) -> float:
        """
        Robust multi-currency and multi-unit order value extraction:
        Extracts contract/order/tender value in Crores from headline text using regex.
        Supports Crores, Lakhs (converted to Cr), USD/EUR Millions (converted to Cr), and Billions.
        """
        # 1. Crores pattern: ₹ / Rs / INR / numeric + cr / crore
        patterns_cr = [
            r'(?:₹|Rs\.?|INR)?\s*([\d,]+(?:\.\d+)?)\s*(?:cr|crore|crores)\b',
            r'([\d,]+(?:\.\d+)?)\s*(?:cr|crore|crores)\s*(?:order|contract|tender|project|work)\b'
        ]
        for p in patterns_cr:
            match = re.search(p, text, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1).replace(',', ''))
                except ValueError:
                    pass

        # 2. Lakhs pattern (convert to Crores: 1 Cr = 100 Lakhs)
        match_lakh = re.search(r'(?:₹|Rs\.?|INR)?\s*([\d,]+(?:\.\d+)?)\s*(?:lakh|lac|lakhs)\b', text, re.IGNORECASE)
        if match_lakh:
            try:
                val_lakh = float(match_lakh.group(1).replace(',', ''))
                return round(val_lakh / 100.0, 4)
            except ValueError:
                pass

        # 3. USD/EUR Millions pattern (convert to INR Crores: ~$1M = ~₹8.5 Cr)
        match_fx = re.search(r'(?:USD|\$|EUR|€)\s*([\d,]+(?:\.\d+)?)\s*(?:mn|million|m)\b', text, re.IGNORECASE)
        if match_fx:
            try:
                val_mn = float(match_fx.group(1).replace(',', ''))
                return round(val_mn * 8.5, 2)
            except ValueError:
                pass

        # 4. Billions pattern (convert to INR Crores: 1 Billion INR = 100 Cr)
        match_bn = re.search(r'(?:₹|Rs\.?|INR)?\s*([\d,]+(?:\.\d+)?)\s*(?:billion|bn)\b', text, re.IGNORECASE)
        if match_bn:
            try:
                val_bn = float(match_bn.group(1).replace(',', ''))
                return round(val_bn * 100.0, 2)
            except ValueError:
                pass

        return 0.0

    def evaluate_catalyst_archetype_and_materiality(
        self,
        headline: str,
        company: dict = None,
        candidate_direction: str = "BULLISH"
    ) -> Dict[str, Any]:
        """
        Strict Quantitative Archetype & Materiality Hurdle Gatekeeper:
        Evaluates the headline against institutional market microstructure failure modes.
        """
        company = company or {}
        annual_rev_cr = company.get("annual_revenue_cr")
        tier = str(company.get("tier", "MID_CAP")).upper()
        is_fno = company.get("is_fno_eligible", False) or (company.get("fno_lot_size") is not None and company.get("fno_lot_size") > 0)

        order_val_cr = self._extract_order_value_cr(headline)

        # -------------------------------------------------------------
        # Archetype 1: Routine Dividend ("Sell-The-News" / Ex-Date Trap)
        # -------------------------------------------------------------
        # Routine interim/final dividend announcements in Indian markets trigger profit-taking
        # or ex-date price drops unless accompanied by special payouts or buybacks.
        is_dividend_event = bool(re.search(r"\bdividend\b", headline, re.I))
        is_special_or_buyback = bool(re.search(r"special dividend|bonus issue|buyback|bonus share", headline, re.I))

        if is_dividend_event and not is_special_or_buyback:
            return {
                "is_actionable": False,
                "direction": "NEUTRAL",
                "category": "ROUTINE_DIVIDEND_SELL_THE_NEWS",
                "materiality_ratio": 0.00,
                "order_value_cr": 0.0,
                "alpha_cap_pct": 0.0,
                "reasoning": "Routine dividend declaration subject to Indian market sell-the-news profit booking and ex-date price drop. Not a directional breakout catalyst."
            }

        # -------------------------------------------------------------
        # Archetype 2: Microcap Operational Closure (Non-F&O Short Squeeze Trap)
        # -------------------------------------------------------------
        # Branch/unit closures on microcaps cannot be shorted overnight (cash equity shorting prohibited)
        # and frequently trigger unpredictable speculative squeezes.
        is_closure_event = bool(re.search(r"closure of operations?|closure of (?:branch|unit|plant|office)|discontinuance of (?:business|operations?)", headline, re.I))
        if is_closure_event and (tier in ["MICRO_CAP", "SMALL_CAP"] or not is_fno):
            return {
                "is_actionable": False,
                "direction": "NEUTRAL",
                "category": "NON_EXECUTABLE_SHORT",
                "materiality_ratio": 0.00,
                "order_value_cr": 0.0,
                "alpha_cap_pct": 0.0,
                "reasoning": "Microcap / non-F&O operational closure. Cash equities cannot be shorted overnight and microcaps are prone to speculative squeezes. Non-actionable."
            }

        # -------------------------------------------------------------
        # Archetype 3: Order / Contract Win Materiality Hurdle
        # -------------------------------------------------------------
        # Order must be >= 3.0% of Annual Revenue (or >= ₹50 Cr if revenue unknown).
        is_order_event = bool(re.search(r"\b(?:order|contract|tender|bags|wins|awarded|secures|loi|loa|p\.o\.|purchase order)\b", headline, re.I))

        if is_order_event and order_val_cr > 0:
            if annual_rev_cr and annual_rev_cr > 0:
                mat_ratio = round(order_val_cr / annual_rev_cr, 4)
                if mat_ratio < 0.03:
                    return {
                        "is_actionable": False,
                        "direction": "NEUTRAL",
                        "category": "IMMATERIAL_ORDER_VALUE",
                        "materiality_ratio": mat_ratio,
                        "order_value_cr": order_val_cr,
                        "alpha_cap_pct": 0.0,
                        "reasoning": f"Immaterial order size (INR {order_val_cr:,.1f} Cr is {mat_ratio*100:.2f}% of annual revenue, below 3.0% hurdle). Non-actionable."
                    }
                else:
                    return {
                        "is_actionable": True,
                        "direction": "BULLISH",
                        "category": "ORDER_WIN",
                        "materiality_ratio": mat_ratio,
                        "order_value_cr": order_val_cr,
                        "alpha_cap_pct": None,
                        "reasoning": f"Material order win: INR {order_val_cr:,.1f} Cr represents {mat_ratio*100:.1f}% of annual revenue."
                    }
            else:
                # Revenue unknown: require at least ₹50 Cr minimum
                if order_val_cr < 50.0:
                    return {
                        "is_actionable": False,
                        "direction": "NEUTRAL",
                        "category": "IMMATERIAL_ORDER_VALUE",
                        "materiality_ratio": 0.01,
                        "order_value_cr": order_val_cr,
                        "alpha_cap_pct": 0.0,
                        "reasoning": f"Order value INR {order_val_cr:,.1f} Cr is below the INR 50 Cr minimum materiality threshold for unverified revenue. Non-actionable."
                    }
                else:
                    return {
                        "is_actionable": True,
                        "direction": "BULLISH",
                        "category": "ORDER_WIN",
                        "materiality_ratio": 0.05,
                        "order_value_cr": order_val_cr,
                        "alpha_cap_pct": None,
                        "reasoning": f"Substantial order win of INR {order_val_cr:,.1f} Cr exceeding standard minimum threshold."
                    }

        # -------------------------------------------------------------
        # Archetype 4: Capex & Capacity Additions (Discount Long Gestation)
        # -------------------------------------------------------------
        is_capex_event = bool(re.search(r"\b(?:capex|capacity addition|capacity expansion|setting up new plant|brownfield expansion|greenfield)\b", headline, re.I))
        if is_capex_event:
            rev_val = annual_rev_cr or 10000.0
            mat_ratio = min(0.04, round(order_val_cr / rev_val, 4) if order_val_cr > 0 else 0.02)
            return {
                "is_actionable": True,
                "direction": "BULLISH",
                "category": "LONG_GESTATION_CAPEX",
                "materiality_ratio": mat_ratio,
                "order_value_cr": order_val_cr,
                "alpha_cap_pct": 1.50, # Alpha capped to +1.50%
                "reasoning": "Long gestation capex. Capacity expansion requires heavy capital outlay without near-term earnings accretion. Target alpha capped to +1.5%."
            }

        # -------------------------------------------------------------
        # Archetype 5: Routine Administrative / ESOP Filings
        # -------------------------------------------------------------
        if re.search(r"(?:allotment of|allotment under) (?:esop|esps|shares under esop)", headline, re.I):
            return {
                "is_actionable": False,
                "direction": "NEUTRAL",
                "category": "ROUTINE_COMPLIANCE",
                "materiality_ratio": 0.00,
                "order_value_cr": 0.0,
                "alpha_cap_pct": 0.0,
                "reasoning": "Routine ESOP allotment with zero company valuation impact."
            }

        # Default: Pass through to standard NLP/LLM routing
        rev_val = annual_rev_cr or 10000.0
        mat_ratio = round(order_val_cr / rev_val, 4) if order_val_cr > 0 else 0.05
        return {
            "is_actionable": True,
            "direction": candidate_direction,
            "category": "CORPORATE_CATALYST",
            "materiality_ratio": mat_ratio,
            "order_value_cr": order_val_cr,
            "alpha_cap_pct": None,
            "reasoning": "Passed archetype materiality gatekeeper."
        }

    def analyze_event(self, headline: str, company: dict) -> dict:
        company = company or {}
        annual_rev_cr = company.get("annual_revenue_cr")

        # 1. First Pass: Archetype & Materiality Hurdle Gatekeeper
        gate_res = self.evaluate_catalyst_archetype_and_materiality(headline, company)

        if not gate_res.get("is_actionable", True):
            # Immaterial or non-actionable catalyst: Terminate immediately without burning LLM calls
            return {
                "symbol": company.get("symbol", "STOCK"),
                "company_name": company.get("company_name", "UNKNOWN"),
                "headline": headline,
                "direction": "NEUTRAL",
                "direction_confidence": 50.0,
                "magnitude_range": "0.0% to 0.0%",
                "materiality_ratio": gate_res.get("materiality_ratio", 0.0),
                "order_value_cr": gate_res.get("order_value_cr", 0.0),
                "category": gate_res.get("category", "IMMATERIAL_CATALYST"),
                "top_historical_match": "None",
                "historical_move_pct": 0.0,
                "is_actionable": False,
                "reasoning": gate_res.get("reasoning", "Immaterial catalyst below quantitative hurdle."),
                "is_rumor": False
            }

        materiality_ratio = gate_res["materiality_ratio"]
        order_val_cr = gate_res["order_value_cr"]
        alpha_cap = gate_res.get("alpha_cap_pct")

        # 2. Get LLM Direction & Confidence Score
        llm_resp = self.llm_router.call_llm(
            f"Analyze headline for company {company.get('company_name', 'COMPANY')} ({company.get('symbol', 'STOCK')}): '{headline}'",
            system_prompt="Return JSON with fields: direction (BULLISH/BEARISH/NEUTRAL), confidence (0.0 to 100.0), reasoning."
        )
        try:
            llm_data = json.loads(llm_resp)
        except Exception:
            llm_data = {"direction": gate_res["direction"], "confidence": 75.0, "reasoning": gate_res["reasoning"]}

        direction = llm_data.get("direction", gate_res["direction"])
        confidence = float(llm_data.get("confidence", 75.0))

        # Adjust confidence upward if materiality is high (>10% of revenue)
        if materiality_ratio > 0.10:
            confidence = min(98.0, confidence + 10.0)

        # 3. Retrieve Historical Pattern via RAG Engine
        rag_matches = self.rag_engine.search_similar_patterns(headline, sector=company.get("sector"))
        top_match = rag_matches[0] if rag_matches else None

        # 4. Calculate Conservative Price Impact Range based on ATR
        atr_pct = float(company.get("atr_percentage", 2.5))
        if direction == "BULLISH":
            base_min = round(atr_pct * 0.8, 2)
            base_max = round(atr_pct * 1.8 + (materiality_ratio * 5.0), 2)
            if alpha_cap:
                base_max = min(base_max, alpha_cap)
        elif direction == "BEARISH":
            base_min = -round(atr_pct * 1.8 + (materiality_ratio * 5.0), 2)
            base_max = -round(atr_pct * 0.8, 2)
        else:
            base_min, base_max = 0.0, 0.0

        # 5. Abstain Rule: Route to Rumors Feed if confidence < 65%
        is_rumor = confidence < 65.0
        if is_rumor:
            direction = "NEUTRAL / UNCONFIRMED"

        return {
            "symbol": company.get("symbol", "STOCK"),
            "company_name": company.get("company_name", "UNKNOWN"),
            "headline": headline,
            "direction": direction,
            "direction_confidence": round(confidence, 1),
            "magnitude_range": f"{base_min}% to {base_max}%",
            "materiality_ratio": materiality_ratio,
            "order_value_cr": order_val_cr,
            "category": gate_res.get("category", "CORPORATE_CATALYST"),
            "top_historical_match": top_match["pattern"]["title"] if top_match else "None",
            "historical_move_pct": top_match["pattern"]["actual_move_pct"] if top_match else 0.0,
            "is_actionable": direction in ["BULLISH", "BEARISH"] and not is_rumor,
            "reasoning": gate_res.get("reasoning", llm_data.get("reasoning", "")),
            "is_rumor": is_rumor
        }

if __name__ == "__main__":
    scorer = CalibratedSentimentScorer()
    mock_co = {"symbol": "MAZDOCK", "company_name": "Mazagon Dock", "annual_revenue_cr": 9400.0}
    res = scorer.analyze_event("Mazagon Dock bags ₹4000 crore defense contract", mock_co)
    print("Mazagon Dock Test:")
    print(json.dumps(res, indent=2))
