import sys
import os
import json
import re
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

class BSEAnnouncementsFetcher:
    """
    Fetcher for BSE Corporate Announcements API.
    BSE provides continuous real-time corporate filings with lower WAF filtering 
    than NSE, acting as an optimal zero-cost cloud mirror for Indian equities.
    """

    def __init__(self):
        self.use_curl_cffi = False
        try:
            import curl_cffi.requests
            self.use_curl_cffi = True
        except ImportError:
            self.use_curl_cffi = False

    def _extract_symbol_from_url(self, nsurl: str, scrip_cd: str, slongname: str) -> str:
        """Extracts ticker symbol from BSE NSURL or defaults cleanly"""
        if nsurl:
            parts = [p.strip() for p in nsurl.split('/') if p.strip()]
            # Pattern: ['https:', 'www.bseindia.com', 'stock-share-price', 'company-name', 'ticker-symbol', '500123']
            if len(parts) >= 2:
                candidate = parts[-2].upper()
                if candidate and not candidate.isdigit() and candidate not in ["STOCK-SHARE-PRICE", "CORPORATES"]:
                    return candidate
        
        clean_name = re.sub(r'[^A-Z0-9]', '', (slongname or "").upper().split()[0]) if slongname else ""
        return clean_name if len(clean_name) >= 3 else str(scrip_cd)

    def fetch_live_announcements(self) -> list:
        """Fetches live corporate announcements for today from BSE API endpoint"""
        today_str = datetime.now().strftime('%Y%m%d')
        url = (
            f"https://api.bseindia.com/BseIndiaAPI/api/AnnSubCategoryGetData/w?"
            f"pageno=1&strCat=-1&strPrevDate={today_str}&strScrip=&strSearch=P&strToDate={today_str}&strType=C"
        )

        headers = {
            'Accept': 'application/json, text/plain, */*',
            'Referer': 'https://www.bseindia.com/'
        }

        try:
            if self.use_curl_cffi:
                from curl_cffi import requests as c_requests
                s = c_requests.Session(impersonate='chrome120')
                resp = s.get(url, headers=headers, timeout=12)
            else:
                import requests
                s = requests.Session()
                headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                resp = s.get(url, headers=headers, timeout=12)
            
            if resp.status_code == 200:
                data = resp.json()
                table = data.get('Table', [])
                events = []
                for item in table[:50]:
                    scrip_cd = str(item.get("SCRIP_CD", "")).strip()
                    company = str(item.get("SLONGNAME", "")).strip()
                    nsurl = str(item.get("NSURL", "")).strip()
                    headline = str(item.get("HEADLINE", "")).strip()
                    newssub = str(item.get("NEWSSUB", "")).strip()
                    dt_tm = item.get("DT_TM") or item.get("News_submission_dt") or datetime.now().isoformat()
                    
                    symbol = self._extract_symbol_from_url(nsurl, scrip_cd, company)
                    content_text = headline if headline and len(headline) > 5 else newssub

                    if symbol and content_text:
                        full_headline = f"{company}: {content_text}" if company and not content_text.startswith(company) else content_text
                        events.append({
                            "source_type": "BSE_FILING",
                            "symbol": symbol,
                            "company_name": company or symbol,
                            "headline": full_headline,
                            "published_at": dt_tm,
                            "bse_scrip": scrip_cd,
                            "category": item.get("CATEGORYNAME", "Corporate Filing"),
                            "raw_payload": item
                        })
                return events
            else:
                print(f"[BSE INGESTION WARNING] HTTP {resp.status_code} received from BSE API", flush=True)
        except Exception as e:
            print(f"[BSE INGESTION EXCEPTION] {e}", flush=True)

        return []

if __name__ == "__main__":
    fetcher = BSEAnnouncementsFetcher()
    announcements = fetcher.fetch_live_announcements()
    print(f"Fetched {len(announcements)} BSE Corporate Announcements for today:")
    if announcements:
        print(json.dumps(announcements[:2], indent=2))
