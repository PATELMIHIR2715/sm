import json
import os
import math
import re

class CPUHistoricalRAGEngine:
    """
    CPU-optimized 10-Year Historical Macro RAG Engine.
    Queries the persistent embedded database containing verified price outcomes (2015-2025).
    """

    def __init__(self, database_file="d:/sm/data/historical_10yr_embedded_database.json", fallback_file="d:/sm/data/macro_patterns_master.json"):
        self.database_file = database_file
        self.fallback_file = fallback_file
        self.records = self._load_records()

    def _load_records(self):
        if os.path.exists(self.database_file):
            try:
                with open(self.database_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass

        if os.path.exists(self.fallback_file):
            try:
                with open(self.fallback_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def _text_to_vector(self, text: str) -> dict:
        words = re.findall(r'\w+', text.lower())
        vec = {}
        for w in words:
            if len(w) > 2 and w not in ["the", "and", "for", "with", "from", "that", "this"]:
                vec[w] = vec.get(w, 0) + 1
        norm = math.sqrt(sum(v**2 for v in vec.values()))
        if norm > 0:
            return {k: round(v / norm, 4) for k, v in vec.items()}
        return vec

    def _cosine_similarity(self, vec1: dict, vec2: dict) -> float:
        intersection = set(vec1.keys()) & set(vec2.keys())
        if not intersection:
            return 0.0
        return sum(vec1[x] * vec2[x] for x in intersection)

    def search_similar_patterns(self, headline: str, sector: str = None, top_k: int = 3) -> list:
        """
        Retrieves top-K most similar historical market events from the 10-year embedded dataset.
        """
        query_vec = self._text_to_vector(headline + " " + (sector or ""))
        results = []

        for r in self.records:
            target_vec = r.get("embedding")
            if not target_vec:
                combined_text = f"{r.get('headline', '')} {r.get('description', '')} {r.get('sector', '')} {r.get('macro_regime', '')}"
                target_vec = self._text_to_vector(combined_text)

            sim_score = self._cosine_similarity(query_vec, target_vec)

            # Boost if exact sector matches
            if sector and r.get("sector") and sector.lower() in r.get("sector", "").lower():
                sim_score += 0.25

            results.append({
                "score": round(sim_score, 4),
                "pattern": {
                    "pattern_uuid": r.get("event_uuid", r.get("pattern_uuid", "")),
                    "event_date": r.get("event_date", ""),
                    "title": r.get("headline", r.get("title", "")),
                    "description": r.get("description", ""),
                    "sector": r.get("sector", ""),
                    "macro_regime": r.get("macro_regime", ""),
                    "actual_direction": r.get("actual_direction", "NEUTRAL"),
                    "actual_move_pct": r.get("actual_1d_return_pct", r.get("actual_move_pct", 0.0)),
                    "actual_5d_return_pct": r.get("actual_5d_return_pct", 0.0),
                    "actual_20d_return_pct": r.get("actual_20d_return_pct", 0.0)
                }
            })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

if __name__ == "__main__":
    rag = CPUHistoricalRAGEngine()
    matches = rag.search_similar_patterns("Cabinet approves mega fighter jet procurement for defense force", sector="Defense & Aerospace")
    print("Top Historical Matches from 10-Year Vector Database:")
    print(json.dumps(matches, indent=2))
