import sys
import os
import json
import time
import hashlib
from datetime import datetime
import yfinance as yf

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

PROJECT_ROOT = os.environ.get("PROJECT_ROOT", os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from services.ai_pipeline.sentiment_classifier import CalibratedSentimentScorer
from services.ai_pipeline.jev_classifier import jev_classifier
from services.ingestion.nse_announcements import NSEAnnouncementsFetcher
from services.ingestion.bse_announcements import BSEAnnouncementsFetcher
from services.ingestion.insider_trading_pit import InsiderTradingPITFetcher
from services.ingestion.bulk_block_deals import BulkBlockDealsFetcher
from services.ingestion.credit_ratings_fetcher import CreditRatingsFetcher
from services.ingestion.pib_gem_fetcher import PIBGEMFetcher
from services.storage.signals_retention_manager import signals_retention_manager

STREAM_FILE = os.path.join(PROJECT_ROOT, "data/live_signals_stream.json")
SEEN_FILE = os.path.join(PROJECT_ROOT, "data/seen_filing_hashes.json")

class AutoLiveStreamWorker:
    """
    Automated Background Poller for NSE/BSE & Corporate Announcements.
    
    1. Continuously polls 5 live data streams (NSE, PIT Insider, Bulk Deals, Credit Ratings, PIB GeM).
    2. Uses SHA256 deduplication so no duplicate announcement is re-processed.
    3. Analyzes new events with Calibrated NLP, Materiality, and ATR Targets.
    4. Fetches real-time LTP from NSE / Yahoo Finance Tick API.
    5. Appends live actionable setups with forward target deadlines to the live stream.
    """

    def __init__(self):
        self.scorer = CalibratedSentimentScorer()
        self.nse_fetcher = NSEAnnouncementsFetcher()
        self.bse_fetcher = BSEAnnouncementsFetcher()
        self.pit_fetcher = InsiderTradingPITFetcher()
        self.bulk_fetcher = BulkBlockDealsFetcher()
        self.ratings_fetcher = CreditRatingsFetcher()
        self.pib_fetcher = PIBGEMFetcher()
        self.seen_hashes = self._load_seen_hashes()
        self.live_stream = self._load_stream()

    def _load_seen_hashes(self) -> set:
        if os.path.exists(SEEN_FILE):
            try:
                with open(SEEN_FILE, "r", encoding="utf-8") as f:
                    return set(json.load(f))
            except Exception:
                pass
        return set()

    def _save_seen_hashes(self):
        os.makedirs(os.path.dirname(SEEN_FILE), exist_ok=True)
        with open(SEEN_FILE, "w", encoding="utf-8") as f:
            json.dump(list(self.seen_hashes), f, indent=2)

    def _load_stream(self) -> list:
        if os.path.exists(STREAM_FILE):
            try:
                with open(STREAM_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def _save_stream(self):
        os.makedirs(os.path.dirname(STREAM_FILE), exist_ok=True)
        with open(STREAM_FILE, "w", encoding="utf-8") as f:
            json.dump(self.live_stream, f, indent=2, ensure_ascii=False)

    def _hash_event(self, text: str) -> str:
        return hashlib.sha256(text.lower().strip().encode('utf-8')).hexdigest()

    def fetch_live_price(self, symbol: str) -> float:
        clean = symbol.upper().replace(".NS", "").replace(".BO", "")
        for suffix in [".NS", ".BO"]:
            ticker = f"{clean}{suffix}"
            try:
                tk = yf.Ticker(ticker)
                hist = tk.history(period="1d", interval="1d")
                if not hist.empty:
                    return round(float(hist.iloc[-1]["Close"]), 2)
            except Exception:
                pass
        return 1000.0

    def compute_forward_targets(self, ltp: float, direction: str, atr_pct: float, materiality: float) -> dict:
        sign = 1.0 if direction == "BULLISH" else -1.0
        t1_min = round(atr_pct * 0.8 * sign, 2)
        t1_max = round((atr_pct * 1.8 + materiality * 5.0) * sign, 2)
        
        t5_min = round(t1_min * 1.6, 2)
        t5_max = round(t1_max * 1.8, 2)

        t10_min = round(t1_min * 2.2, 2)
        t10_max = round(t1_max * 2.6, 2)

        p_t1_low = round(ltp * (1 + t1_min / 100), 2)
        p_t1_high = round(ltp * (1 + t1_max / 100), 2)
        p_t5_low = round(ltp * (1 + t5_min / 100), 2)
        p_t5_high = round(ltp * (1 + t5_max / 100), 2)
        p_t10_low = round(ltp * (1 + t10_min / 100), 2)
        p_t10_high = round(ltp * (1 + t10_max / 100), 2)

        stop_loss_pct = round(atr_pct * 1.2, 2)
        sl_price = round(ltp * (1 - stop_loss_pct / 100), 2) if direction == "BULLISH" else round(ltp * (1 + stop_loss_pct / 100), 2)

        return {
            "t1": {
                "range_pct": f"{min(t1_min, t1_max):+.2f}% to {max(t1_min, t1_max):+.2f}%",
                "price_target": f"₹{min(p_t1_low, p_t1_high):,.2f} - ₹{max(p_t1_low, p_t1_high):,.2f}",
                "deadline": "Tomorrow (T+1)"
            },
            "t5": {
                "range_pct": f"{min(t5_min, t5_max):+.2f}% to {max(t5_min, t5_max):+.2f}%",
                "price_target": f"₹{min(p_t5_low, p_t5_high):,.2f} - ₹{max(p_t5_low, p_t5_high):,.2f}",
                "deadline": "1-Week (T+5)"
            },
            "t10": {
                "range_pct": f"{min(t10_min, t10_max):+.2f}% to {max(t10_min, t10_max):+.2f}%",
                "price_target": f"₹{min(p_t10_low, p_t10_high):,.2f} - ₹{max(p_t10_low, p_t10_high):,.2f}",
                "deadline": "2-Weeks (T+10)"
            },
            "stop_loss": f"₹{sl_price:,.2f} ({'-' if direction == 'BULLISH' else '+'}{stop_loss_pct}%)"
        }

    def process_incoming_item(self, item: dict) -> dict:
        try:
            headline = item.get("headline", "")
            symbol = item.get("symbol", "NIFTY500")
            source = item.get("source_type", "NSE_FILING")

            h = self._hash_event(headline)
            if h in self.seen_hashes:
                return None # Already processed

            self.seen_hashes.add(h)
            self._save_seen_hashes()

            # Company profile
            company_meta = {
                "symbol": symbol,
                "company_name": item.get("company_name", symbol),
                "sector": item.get("sector", "Diversified"),
                "annual_revenue_cr": item.get("annual_revenue_cr", 20000.0),
                "atr_percentage": item.get("atr_percentage", 2.5)
            }

            # AI Prediction (uses Jev Model API if configured, otherwise calibrated institutional ensemble)
            pred = jev_classifier.classify_event(headline, company_meta)
            pred_dir = pred.get("direction", "NEUTRAL")
            is_useful = pred_dir in ["BULLISH", "BEARISH"]
            conviction = pred.get("conviction_pct", pred.get("confidence", 75.0))
            
            # Real-time LTP
            ltp = self.fetch_live_price(symbol)
            
            targets = self.compute_forward_targets(
                ltp, pred_dir, company_meta["atr_percentage"], pred.get("materiality_ratio", 0.0)
            )

            signal_record = {
                "id": f"AUTO_{int(time.time())}_{symbol}",
                "symbol": symbol,
                "company_name": company_meta["company_name"],
                "sector": company_meta["sector"],
                "source_type": source,
                "headline": headline,
                "published_at": item.get("published_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                "processed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "current_base_price_inr": ltp,
                "predicted_direction": pred_dir,
                "conviction_score_pct": conviction,
                "materiality_ratio": pred.get("materiality_ratio", 0.0),
                "ai_model": pred.get("model_engine", "JEV_AI_CLASSIFIER"),
                "is_useful": is_useful,
                "t1_target": {
                    "percentage_range": targets["t1"]["range_pct"],
                    "price_target_range_inr": targets["t1"]["price_target"],
                    "target_date_horizon": targets["t1"]["deadline"]
                },
                "t5_target": {
                    "percentage_range": targets["t5"]["range_pct"],
                    "price_target_range_inr": targets["t5"]["price_target"],
                    "target_date_horizon": targets["t5"]["deadline"]
                },
                "t10_target": {
                    "percentage_range": targets["t10"]["range_pct"],
                    "price_target_range_inr": targets["t10"]["price_target"],
                    "target_date_horizon": targets["t10"]["deadline"]
                },
                "recommended_stop_loss": targets["stop_loss"],
                "recommended_strategy": "STRONG BUY ACCUMULATION" if pred_dir == "BULLISH" else ("TACTICAL SHORT / HEDGE" if pred_dir == "BEARISH" else "NEUTRAL WATCH")
            }

            self.live_stream.insert(0, signal_record)
            self._save_stream()

            # Strict 90-Day Retention Archive
            signals_retention_manager.store_signal(signal_record)
            print(f"[NEW EVENT PROCESSED] {symbol} | {pred_dir} ({conviction}%) | LTP: INR {ltp} | Retained: 90 Days", flush=True)

            # Cloud Bridge: Real-Time Supabase Upsert
            self._sync_to_supabase(signal_record)

            # Automatic Multi-Channel Alert Dispatch (WhatsApp & Email)
            if signal_record.get("conviction_score_pct", 0) >= 70 and signal_record.get("is_useful", True):
                self._dispatch_instant_alert(signal_record)

            return signal_record
        except Exception as e:
            print(f"[ERROR PROCESSING ITEM] {item.get('symbol', 'UNKNOWN')}: {e}", flush=True)
            return None

    def _dispatch_instant_alert(self, signal: dict):
        dispatched_hub = False
        try:
            import urllib.request
            admin_key = os.environ.get("ADMIN_SECRET_KEY", "admin@institutional2026")
            req = urllib.request.Request(
                "http://127.0.0.1:5001/api/notifications/broadcast-signal",
                data=json.dumps({"signal": signal}).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "x-admin-token": admin_key,
                    "Authorization": f"Bearer {admin_key}"
                }
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                if resp.status == 200:
                    print(f"[AUTO-ALERT BROADCAST] Successfully sent WhatsApp & Email for {signal['symbol']}", flush=True)
                    dispatched_hub = True
        except Exception as e:
            # Hub offline or error
            pass

        # Direct Python SMTP Fallback (always delivers even on cloud/Render without Node hub)
        if not dispatched_hub:
            self._dispatch_direct_email(signal)

    def _dispatch_direct_email(self, signal: dict):
        try:
            import smtplib
            from email.mime.multipart import MIMEMultipart
            from email.mime.text import MIMEText

            recipients = []
            sub_file = os.path.join(PROJECT_ROOT, "data/notification_subscribers.json")
            if os.path.exists(sub_file):
                try:
                    with open(sub_file, "r", encoding="utf-8") as f:
                        sub_data = json.load(f)
                    for s in sub_data.get("subscribers", []):
                        if s.get("active") is not False and s.get("email"):
                            recipients.append(s["email"].strip().lower())
                except Exception:
                    pass

            if not recipients:
                recipients = [os.environ.get("SMTP_USER", "mihirpqtel@gmail.com")]

            recipients = list(set(recipients))
            smtp_user = os.environ.get("SMTP_USER", "")
            smtp_pass = os.environ.get("SMTP_PASS", "")
            smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
            smtp_port = int(os.environ.get("SMTP_PORT", 465))

            if not smtp_user or not smtp_pass:
                return

            symbol = signal.get("symbol", "NIFTY")
            dir_text = signal.get("predicted_direction", "CATALYST")
            conv = signal.get("conviction_score_pct", 80)
            ltp = signal.get("current_base_price_inr", 0)
            t1 = signal.get("t1_target", {}).get("price_target_range_inr", "TBD")
            sl = signal.get("recommended_stop_loss", "TBD")

            subject = f"⚡ LIVE SIGNAL ALERT: {symbol} | {dir_text} ({conv}% Conviction) | LTP ₹{ltp}"
            html_content = f"""
            <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: auto; padding: 20px; background: #0f172a; color: #f8fafc; border-radius: 12px;">
              <h2 style="color: #38bdf8; margin-top: 0;">⚡ Institutional Market Catalyst Alert</h2>
              <div style="background: #1e293b; padding: 16px; border-radius: 8px; border-left: 4px solid {'#10b981' if dir_text == 'BULLISH' else '#ef4444'};">
                <h3 style="margin: 0 0 8px 0; color: #ffffff;">{symbol} — {signal.get('company_name', symbol)}</h3>
                <p style="margin: 0; color: #94a3b8; font-size: 14px;"><strong>Direction:</strong> <span style="color: {'#10b981' if dir_text == 'BULLISH' else '#ef4444'}; font-weight: bold;">{dir_text} ({conv}% Conviction)</span></p>
                <p style="margin: 4px 0 0 0; color: #94a3b8; font-size: 14px;"><strong>LTP:</strong> ₹{ltp:,.2f}</p>
              </div>
              <div style="margin-top: 16px; background: #1e293b; padding: 14px; border-radius: 8px;">
                <p style="margin: 0 0 8px 0; font-size: 13px; color: #cbd5e1;"><strong>Headline:</strong> {signal.get('headline')}</p>
                <p style="margin: 0 0 4px 0; font-size: 13px; color: #94a3b8;"><strong>T+1 Target:</strong> <span style="color: #38bdf8;">{t1}</span></p>
                <p style="margin: 0; font-size: 13px; color: #94a3b8;"><strong>Stop-Loss:</strong> <span style="color: #f87171;">{sl}</span></p>
              </div>
              <p style="margin-top: 20px; font-size: 11px; color: #64748b; text-align: center;">Institutional AI News Impact Engine • Rolling 90-Day Retention Archive</p>
            </div>
            """

            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"Institutional AI Alerts <{smtp_user}>"
            msg["To"] = ", ".join(recipients)
            msg.attach(MIMEText(html_content, "html"))

            with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=10) as server:
                server.login(smtp_user, smtp_pass)
                server.sendmail(smtp_user, recipients, msg.as_string())
            print(f"[DIRECT-EMAIL DISPATCH] Sent alert for {symbol} to {len(recipients)} subscribers ({', '.join(recipients)})", flush=True)
        except Exception as err:
            print(f"[DIRECT-EMAIL ERROR] Could not send direct email: {err}", flush=True)

    def _sync_to_supabase(self, signal_record: dict):
        try:
            import urllib.request
            from services.sync.supabase_nightly_sync import supabase_sync_manager
            supa_cfg = supabase_sync_manager.get_config()
            supa_url = (supa_cfg.get("supabase_url") or os.environ.get("SUPABASE_URL", "")).rstrip("/")
            supa_key = supa_cfg.get("supabase_key") or os.environ.get("SUPABASE_KEY", "")
            if not supa_url or not supa_key:
                return

            clean_rec = {
                "id": signal_record.get("id"),
                "symbol": signal_record.get("symbol"),
                "company_name": signal_record.get("company_name", signal_record.get("symbol")),
                "sector": signal_record.get("sector", "Diversified"),
                "source_type": signal_record.get("source_type", "NSE_FILING"),
                "headline": signal_record.get("headline", ""),
                "news_date": signal_record.get("news_date", datetime.now().strftime("%b %d, %Y (Today)")),
                "news_time": signal_record.get("news_time", datetime.now().strftime("%I:%M %p IST")),
                "current_base_price_inr": float(signal_record.get("current_base_price_inr", 0.0)),
                "predicted_direction": signal_record.get("predicted_direction", "NEUTRAL"),
                "conviction_score_pct": float(signal_record.get("conviction_score_pct", 75.0)),
                "materiality_ratio": float(signal_record.get("materiality_ratio", 0.0)),
                "ai_model": signal_record.get("ai_model", "JEV_AI_SYSTEMONE"),
                "is_useful": bool(signal_record.get("is_useful", True)),
                "t1_target": signal_record.get("t1_target", {}),
                "t5_target": signal_record.get("t5_target", {}),
                "t10_target": signal_record.get("t10_target", {}),
                "recommended_stop_loss": str(signal_record.get("recommended_stop_loss", "")),
                "recommended_strategy": str(signal_record.get("recommended_strategy", "ACCUMULATE")),
                "raw_metadata": signal_record,
                "updated_at": datetime.now().isoformat()
            }

            req = urllib.request.Request(
                f"{supa_url}/rest/v1/signals",
                data=json.dumps([clean_rec]).encode("utf-8"),
                headers={
                    "apikey": supa_key,
                    "Authorization": f"Bearer {supa_key}",
                    "Content-Type": "application/json",
                    "Prefer": "resolution=merge-duplicates"
                },
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                if resp.status in [200, 201]:
                    print(f"[SUPABASE LIVE SYNC] Upserted {signal_record['symbol']} to Supabase cloud warehouse.", flush=True)
        except Exception as e:
            pass

    def poll_cycle(self) -> int:
        raw_items = []
        try: raw_items.extend(self.nse_fetcher.fetch_live_announcements())
        except Exception as e: print(f"[NSE Fetch Warning] {e}", flush=True)
        try: raw_items.extend(self.bse_fetcher.fetch_live_announcements())
        except Exception as e: print(f"[BSE Fetch Warning] {e}", flush=True)
        try: raw_items.extend(self.pit_fetcher.fetch_insider_disclosures())
        except Exception: pass
        try: raw_items.extend(self.bulk_fetcher.fetch_bulk_deals())
        except Exception: pass
        try: raw_items.extend(self.ratings_fetcher.fetch_rating_updates())
        except Exception: pass
        try: raw_items.extend(self.pib_fetcher.fetch_pib_gem_releases())
        except Exception: pass

        new_count = 0
        for it in raw_items:
            res = self.process_incoming_item(it)
            if res:
                new_count += 1

        # Enforce rolling 90-day retention cleanup
        signals_retention_manager.prune_expired()
        return new_count

    def run_daemon(self, interval_seconds=30):
        print(f"[AUTO-STREAM DAEMON] Monitoring NSE, BSE & Regulatory Feeds every {interval_seconds}s...", flush=True)
        while True:
            try:
                new_count = self.poll_cycle()
                if new_count > 0:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Ingested & Analyzed {new_count} new market events.", flush=True)
            except Exception as e:
                print(f"[Daemon Error] {e}", flush=True)
            time.sleep(interval_seconds)

if __name__ == "__main__":
    worker = AutoLiveStreamWorker()
    if "--daemon" in sys.argv:
        worker.run_daemon(interval_seconds=30)
    else:
        new_events = worker.poll_cycle()
        print(f"Single Poll Complete. Ingested {new_events} new events.")
