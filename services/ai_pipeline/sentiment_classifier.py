import sys
import os
import re
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from services.ai_pipeline.llm_router import LLMRouter
from services.ai_pipeline.rag_engine import CPUHistoricalRAGEngine

class CalibratedSentimentScorer:
    """
    Combines Materiality Calculation, LLM Direction Classification, 
    10-Year Historical RAG Pattern Matching, and Conservative ATR Magnitude Range.
    """

    def __init__(self):
        self.llm_router = LLMRouter()
        self.rag_engine = CPUHistoricalRAGEngine()

    def _extract_order_value_cr(self, text: str) -> float:
        """Extracts contract/tender value in Crores from headline text using regex"""
        patterns = [
            r'₹\s*([\d,]+)\s*(?:cr|crore|crores)',
            r'Rs\.?\s*([\d,]+)\s*(?:cr|crore|crores)',
            r'INR\s*([\d,]+)\s*(?:cr|crore|crores)',
            r'([\d,]+)\s*(?:cr|crore|crores)\s*(?:order|contract|tender)'
        ]
        for p in patterns:
            match = re.search(p, text, re.IGNORECASE)
            if match:
                val_str = match.group(1).replace(',', '')
                try:
                    return float(val_str)
                except ValueError:
                    pass
        return 0.0

    def analyze_event(self, headline: str, company: dict) -> dict:
        # 1. Extract Order Value & Calculate Materiality Ratio
        order_val_cr = self._extract_order_value_cr(headline)
        annual_rev_cr = company.get("annual_revenue_cr") or 10000.0
        materiality_ratio = round(order_val_cr / annual_rev_cr, 4) if order_val_cr > 0 else 0.0

        # 2. Get LLM Direction & Confidence Score
        llm_resp = self.llm_router.call_llm(
            f"Analyze headline for company {company['company_name']} ({company['symbol']}): '{headline}'",
            system_prompt="Return JSON with fields: direction (BULLISH/BEARISH/NEUTRAL), confidence (0.0 to 100.0), reasoning."
        )
        try:
            llm_data = json.loads(llm_resp)
        except Exception:
            llm_data = {"direction": "NEUTRAL", "confidence": 50.0, "reasoning": "Unstructured output"}

        direction = llm_data.get("direction", "NEUTRAL")
        confidence = float(llm_data.get("confidence", 50.0))

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
            "symbol": company["symbol"],
            "company_name": company["company_name"],
            "headline": headline,
            "direction": direction,
            "direction_confidence": round(confidence, 1),
            "magnitude_range": f"{base_min}% to {base_max}%",
            "materiality_ratio": materiality_ratio,
            "order_value_cr": order_val_cr,
            "top_historical_match": top_match["pattern"]["title"] if top_match else "None",
            "historical_move_pct": top_match["pattern"]["actual_move_pct"] if top_match else 0.0,
            "is_rumor": is_rumor
        }

if __name__ == "__main__":
    scorer = CalibratedSentimentScorer()
    mock_company = {"symbol": "MAZDOCK", "company_name": "Mazagon Dock Shipbuilders Ltd", "sector": "Defense & Shipbuilding", "annual_revenue_cr": 9400.0, "atr_percentage": 3.8}
    result = scorer.analyze_event("Mazagon Dock bags ₹4000 crore defense contract for naval vessels", mock_company)
    print("Calibrated Analysis Result:")
    print(json.dumps(result, indent=2))
