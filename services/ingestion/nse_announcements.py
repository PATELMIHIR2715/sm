import sys
import os
import json
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

class NSEAnnouncementsFetcher:
    """
    Fetcher for NSE Corporate Announcements.
    Employs TLS fingerprint impersonation (curl_cffi chrome120) to bypass 
    WAF blocking and cookie handshake checks.
    """

    def __init__(self):
        self.use_curl_cffi = False
        try:
            import curl_cffi.requests
            self.use_curl_cffi = True
        except ImportError:
            self.use_curl_cffi = False

        self.cookie_primed = False
        self.session = None
        self._init_session()

    def _init_session(self):
        if self.use_curl_cffi:
            from curl_cffi import requests as c_requests
            self.session = c_requests.Session(impersonate='chrome120')
        else:
            import requests
            self.session = requests.Session()
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
            })
        self.cookie_primed = False

    def _prime_cookies(self):
        """Initializes session by visiting NSE homepage"""
        try:
            headers = {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Referer': 'https://www.google.com/'
            }
            r = self.session.get("https://www.nseindia.com", headers=headers, timeout=10)
            if r.status_code == 200:
                self.cookie_primed = True
        except Exception as e:
            self.cookie_primed = False

    def fetch_live_announcements(self) -> list:
        """Fetches live corporate announcements from official NSE API endpoint"""
        if not self.cookie_primed:
            self._prime_cookies()

        url = "https://www.nseindia.com/api/corporate-announcements?index=equities"
        api_headers = {
            'Accept': 'application/json, text/plain, */*',
            'Referer': 'https://www.nseindia.com/'
        }

        try:
            resp = self.session.get(url, headers=api_headers, timeout=12)
            if resp.status_code == 200:
                data = resp.json()
                raw_list = data if isinstance(data, list) else data.get("data", [])
                events = []
                for item in raw_list[:40]:
                    symbol = item.get("symbol", "").strip()
                    desc = item.get("desc", "").strip()
                    company = item.get("companyName", "").strip()
                    an_dt = item.get("an_dt", "")
                    
                    if symbol and desc:
                        events.append({
                            "source_type": "NSE_FILING",
                            "symbol": symbol,
                            "company_name": company or symbol,
                            "headline": f"{company}: {desc}" if company else f"{symbol}: {desc}",
                            "published_at": an_dt or datetime.now().isoformat(),
                            "raw_payload": item
                        })
                if events:
                    return events
            else:
                self.cookie_primed = False
        except Exception as e:
            self.cookie_primed = False
            # Re-init session on error
            self._init_session()

        return []

if __name__ == "__main__":
    fetcher = NSEAnnouncementsFetcher()
    announcements = fetcher.fetch_live_announcements()
    print(f"Fetched {len(announcements)} NSE Corporate Announcements:")
    if announcements:
        print(json.dumps(announcements[:2], indent=2))
