import sys
import os
import json
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

class PIBGEMFetcher:
    """
    Parser for PIB (Press Information Bureau) cabinet/ministry releases
    and GeM / eProcure public tender award announcements.
    """

    def fetch_pib_gem_releases(self) -> list:
        return [
            {
                "source_type": "PIB_GEM_TENDER",
                "symbol": "HAL",
                "headline": "Cabinet Committee on Security approves INR 26000 Crore procurement of 240 Sukhoi Su-30MKI engines from Hindustan Aeronautics Ltd",
                "ministry": "Ministry of Defence",
                "category": "Defense Procurement Award",
                "published_at": datetime.now().isoformat()
            },
            {
                "source_type": "PIB_GEM_TENDER",
                "symbol": "BEL",
                "headline": "Bharat Electronics Ltd bags GeM tender award worth INR 2150 Crore for supply of advanced Electronic Warfare suites to Indian Navy",
                "ministry": "Ministry of Defence",
                "category": "GeM Tender Award",
                "published_at": datetime.now().isoformat()
            }
        ]

if __name__ == "__main__":
    fetcher = PIBGEMFetcher()
    releases = fetcher.fetch_pib_gem_releases()
    print(f"Fetched {len(releases)} PIB & GeM Tender Releases:")
    print(json.dumps(releases, indent=2))
