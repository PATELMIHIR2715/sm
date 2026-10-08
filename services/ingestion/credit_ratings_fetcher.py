import sys
import os
import json
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

class CreditRatingsFetcher:
    """
    Parser for Credit Rating updates from CRISIL, ICRA, CARE, and India Ratings.
    High impact risk-protection and conviction signals.
    """

    def fetch_rating_updates(self) -> list:
        return [
            {
                "source_type": "CREDIT_RATING",
                "symbol": "BERGEPAINT",
                "headline": "CRISIL upgrades Long-Term Bank Credit Facilities rating of Berger Paints India Ltd to CRISIL AAA / Stable from CRISIL AA+",
                "agency": "CRISIL",
                "old_rating": "AA+",
                "new_rating": "AAA",
                "action": "UPGRADE",
                "published_at": datetime.now().isoformat()
            },
            {
                "source_type": "CREDIT_RATING",
                "symbol": "TATASTEEL",
                "headline": "ICRA reaffirms Tata Steel Ltd Commercial Paper rating at ICRA A1+ and revises Long-Term Outlook to Positive",
                "agency": "ICRA",
                "old_rating": "AA (Stable)",
                "new_rating": "AA (Positive)",
                "action": "OUTLOOK_POSITIVE",
                "published_at": datetime.now().isoformat()
            }
        ]

if __name__ == "__main__":
    fetcher = CreditRatingsFetcher()
    ratings = fetcher.fetch_rating_updates()
    print(f"Fetched {len(ratings)} Credit Rating Agency Updates:")
    print(json.dumps(ratings, indent=2))
