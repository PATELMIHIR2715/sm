import sys
import os
import json
import time
import hashlib
import math
import re
from datetime import datetime
from typing import Optional, Dict, Any, List
import yfinance as yf

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

PROJECT_ROOT = os.environ.get("PROJECT_ROOT", os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from services.ai_pipeline.sentiment_classifier import CalibratedSentimentScorer
from services.ai_pipeline.jev_classifier import jev_classifier
from services.ai_pipeline.scaled_rag_engine import ScaledVectorRAGEngine
from services.ai_pipeline.kelly_position_sizer import KellyPositionSizer
from services.ai_pipeline.market_regime_confluence import MarketRegimeConfluenceEngine
from services.market_data.company_intelligence_provider import CompanyIntelligenceProvider
from services.market_data.live_price_provider import LivePriceProvider
from services.market_data.circuit_detector import CircuitFreezeDetector
from services.ingestion.nse_announcements import NSEAnnouncementsFetcher
from services.ingestion.bse_announcements import BSEAnnouncementsFetcher
from services.ingestion.insider_trading_pit import InsiderTradingPITFetcher
from services.ingestion.bulk_block_deals import BulkBlockDealsFetcher
from services.ingestion.credit_ratings_fetcher import CreditRatingsFetcher
from services.ingestion.pib_gem_fetcher import PIBGEMFetcher
from services.storage.signals_retention_manager import signals_retention_manager
from services.evaluation.model_version_manager import ModelVersionManager

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
        self.rag_engine = ScaledVectorRAGEngine()
        self.kelly_sizer = KellyPositionSizer(portfolio_capital=100000.0)
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
        tmp_file = f"{STREAM_FILE}.tmp.{os.getpid()}"
        try:
            with open(tmp_file, "w", encoding="utf-8") as f:
                json.dump(self.live_stream, f, indent=2, ensure_ascii=False)
            os.replace(tmp_file, STREAM_FILE)
        except Exception:
            try:
                if os.path.exists(tmp_file):
                    os.remove(tmp_file)
            except Exception:
                pass

    def _hash_event(self, text: str) -> str:
        return hashlib.sha256(text.lower().strip().encode('utf-8')).hexdigest()

    def fetch_live_price(self, symbol: str, force_fresh: bool = True) -> Optional[float]:
        try:
            from services.market_data.live_price_provider import LivePriceProvider
            quote = LivePriceProvider.get_live_quote(symbol, force_fresh=force_fresh)
            if quote and quote.get("ltp") and quote["ltp"] > 0:
                return float(quote["ltp"])
        except Exception:
            pass

        clean = symbol.upper().replace(".NS", "").replace(".BO", "")
        for suffix in [".NS", ".BO"]:
            ticker = f"{clean}{suffix}"
            try:
                tk = yf.Ticker(ticker)
                hist = tk.history(period="5d", interval="1d", timeout=5.0)
                if not hist.empty:
                    return round(float(hist.iloc[-1]["Close"]), 2)
            except Exception:
                pass
        return None

    def _find_milestone_supply_wall(self, base_price: float, direction: str) -> Optional[float]:
        """Identifies nearest institutional round-number resistance/support wall"""
        if base_price >= 10000: step = 1000.0  # ₹15k, ₹16k, ₹17k, ₹18k
        elif base_price >= 2000: step = 500.0   # ₹2,500, ₹3,000, ₹3,500
        elif base_price >= 500: step = 100.0    # ₹600, ₹700, ₹800
        elif base_price >= 100: step = 25.0     # ₹125, ₹150, ₹175, ₹200
        else: step = 10.0

        if direction == "BULLISH":
            next_wall = math.ceil(base_price / step) * step
            # If base_price is already right at the wall, look at next wall
            if (next_wall - base_price) / base_price < 0.002:
                next_wall += step
            return next_wall
        else:
            prev_wall = math.floor(base_price / step) * step
            if (base_price - prev_wall) / base_price < 0.002:
                prev_wall -= step
            return prev_wall

    @classmethod
    def preopen_execution_gate(cls, signal: dict, preopen_price: float, prev_close: float) -> dict:
        """
        NSE Pre-Open Auction Verification Gate (evaluated at 09:08 AM):
        If overnight signal experiences an adverse auction gap >= min(ATR_pct, 0.75 * Stop_Loss_pct),
        the theoretical edge is destroyed. Terminal suppression is enforced.
        """
        if not preopen_price or not prev_close or prev_close <= 0:
            return {"approved": False, "reason": "UNVERIFIED_PREOPEN_PRICE"}

        direction = signal.get("predicted_direction", "BULLISH").upper()
        gap_pct = ((preopen_price - prev_close) / prev_close) * 100.0

        atr_pct = 2.5
        stop_loss_pct = 3.2
        sl_str = str(signal.get("recommended_stop_loss", ""))
        nums = re.findall(r"[\d]+\.?\d*", sl_str)
        if nums:
            stop_loss_pct = float(nums[-1])

        adverse_hurdle = min(atr_pct, 0.75 * stop_loss_pct)

        if direction in ["BULLISH", "BUY"]:
            if gap_pct <= -adverse_hurdle:
                return {
                    "approved": False,
                    "reason": f"ADVERSE_PREOPEN_GAP_DOWN ({gap_pct:+.2f}% vs hurdle -{adverse_hurdle:.2f}%)",
                    "preopen_price": preopen_price,
                    "gap_pct": round(gap_pct, 2)
                }
            t1_low = signal.get("t1_target", {}).get("price_low")
            if t1_low and preopen_price >= t1_low:
                return {
                    "approved": False,
                    "reason": f"PREOPEN_GAP_EXHAUSTED_TARGET ({gap_pct:+.2f}%, open INR {preopen_price} >= target low INR {t1_low})",
                    "preopen_price": preopen_price,
                    "gap_pct": round(gap_pct, 2)
                }
        elif direction in ["BEARISH", "SELL", "SHORT"]:
            if gap_pct >= adverse_hurdle:
                return {
                    "approved": False,
                    "reason": f"ADVERSE_PREOPEN_GAP_UP ({gap_pct:+.2f}% vs hurdle +{adverse_hurdle:.2f}%)",
                    "preopen_price": preopen_price,
                    "gap_pct": round(gap_pct, 2)
                }
            t1_high = signal.get("t1_target", {}).get("price_high")
            if t1_high and preopen_price <= t1_high:
                return {
                    "approved": False,
                    "reason": f"PREOPEN_GAP_EXHAUSTED_TARGET ({gap_pct:+.2f}%, open INR {preopen_price} <= target high INR {t1_high})",
                    "preopen_price": preopen_price,
                    "gap_pct": round(gap_pct, 2)
                }

        return {
            "approved": True,
            "preopen_price": preopen_price,
            "gap_pct": round(gap_pct, 2),
            "reason": None
        }

    def compute_forward_targets(
        self,
        ltp: float,
        direction: str,
        atr_pct: float,
        materiality: float,
        tier: str = "MID_CAP",
        historical_return_1d: float = None,
        is_after_market: bool = False,
        symbol: str = "STOCK",
        nifty_change_pct: float = 0.0,
        india_vix: float = 14.5,
        vix_sl_padding_mult: float = 1.0,
        stock_beta: float = None,
        nifty_return_3d: float = None,
        sector_return_1d: float = 0.0,
        vix_change_pct: float = 0.0,
        sector_beta: float = 1.0,
        is_fno_eligible: bool = True
    ) -> dict:
        if ltp is None or not math.isfinite(float(ltp)) or float(ltp) <= 0:
            return {"dispatchable": False, "reason": "UNVERIFIED_LIVE_PRICE"}
        safe_ltp = float(ltp)
        sign = 1.0 if direction == "BULLISH" else -1.0

        # Market Cap Tier Constraints (Prevents Large/Mega Caps from having unrealistic wide targets)
        tier_limits = {
            "MEGA_CAP": {"min_move": 0.50, "max_move": 1.20},
            "LARGE_CAP": {"min_move": 0.80, "max_move": 1.80},
            "MID_CAP": {"min_move": 1.40, "max_move": 3.00},
            "SMALL_CAP": {"min_move": 2.00, "max_move": 4.50}
        }
        limits = tier_limits.get(tier, tier_limits["MID_CAP"])

        # Order Materiality Scaling: Orders <3% of annual revenue are non-material incremental updates
        mat_mult = 1.0
        if materiality > 0 and materiality < 0.03:
            mat_mult = 0.45  # <3% of annual sales has low single-day impact
        elif materiality >= 0.08:
            mat_mult = 1.25  # >8% of annual sales is a transformative catalyst

        raw_min = atr_pct * 0.55 * mat_mult
        raw_max = (atr_pct * 1.10 + materiality * 3.5) * mat_mult

        # Clamped by Market Cap Tier
        t1_min_mag = max(limits["min_move"], min(raw_min, limits["max_move"]))
        t1_max_mag = max(t1_min_mag + 0.30, min(raw_max, limits["max_move"]))

        # Blend RAG Historical Memory if verified match exists
        if historical_return_1d is not None and abs(historical_return_1d) > 0.1 and abs(historical_return_1d) < 30.0:
            hist_mag = abs(historical_return_1d)
            t1_min_mag = round(0.6 * t1_min_mag + 0.4 * (hist_mag * 0.7), 2)
            t1_max_mag = round(0.6 * t1_max_mag + 0.4 * hist_mag, 2)

        # Beta-Adjusted Market Regime Integration: Deduct Beta Drag on Longs, Boost Shorts
        regime_eval = MarketRegimeConfluenceEngine.calculate_beta_adjusted_target(
            symbol=symbol,
            ltp=safe_ltp,
            raw_target_pct=t1_min_mag,
            direction=direction,
            nifty_change_pct=nifty_change_pct,
            india_vix=india_vix,
            stock_beta=stock_beta,
            nifty_return_3d=nifty_return_3d,
            sector_return_1d=sector_return_1d,
            vix_change_pct=vix_change_pct,
            sector_beta=sector_beta,
            is_fno_eligible=is_fno_eligible
        )

        if not regime_eval.get("dispatchable", True):
            return {
                "dispatchable": False,
                "reason": regime_eval.get("reason", "REGIME_VETO"),
                "recommended_strategy": regime_eval.get("recommended_execution_strategy"),
                "target_confidence_note": regime_eval.get("target_confidence_note"),
                "market_drag_contribution_pct": regime_eval.get("market_drag_contribution_pct", 0.0),
                "conviction_delta": regime_eval.get("conviction_delta", -20.0),
            }

        t1_min_mag = regime_eval["t1_safe_pct"]
        t1_max_mag = regime_eval["t1_runner_pct"]
        rec_strategy = regime_eval["recommended_execution_strategy"]
        target_note = regime_eval["target_confidence_note"]
        suppress_chase = regime_eval["suppress_chase_alert"]

        # Two-Tier Architecture:
        # T1 Safe Target (Conservative Profit-Lock) front-runs the nearest round institutional wall
        milestone_wall = self._find_milestone_supply_wall(safe_ltp, direction)
        t1_safe_price = round(safe_ltp * (1 + (t1_min_mag * sign) / 100), 2)
        t1_runner_price = round(safe_ltp * (1 + (t1_max_mag * sign) / 100), 2)

        clamped_to_wall = False
        if milestone_wall:
            if direction == "BULLISH" and safe_ltp < milestone_wall <= t1_runner_price:
                # Clamp T1 Safe to front-run the wall by 0.25% to guarantee execution
                front_run_price = round(milestone_wall * 0.9975, 2)
                if front_run_price > safe_ltp * 1.004:
                    t1_safe_price = min(t1_safe_price, front_run_price)
                    clamped_to_wall = True
            elif direction == "BEARISH" and t1_runner_price <= milestone_wall < safe_ltp:
                front_run_price = round(milestone_wall * 1.0025, 2)
                if front_run_price < safe_ltp * 0.996:
                    t1_safe_price = max(t1_safe_price, front_run_price)
                    clamped_to_wall = True

        t1_safe_pct = round(((t1_safe_price - safe_ltp) / safe_ltp) * 100, 2)
        t1_runner_pct = round(((t1_runner_price - safe_ltp) / safe_ltp) * 100, 2)

        t5_min = round(t1_min_mag * sign * 1.4, 2)
        t5_max = round(t1_max_mag * sign * 1.6, 2)

        t10_min = round(t1_min_mag * sign * 1.8, 2)
        t10_max = round(t1_max_mag * sign * 2.2, 2)

        p_t5_low = round(safe_ltp * (1 + min(t5_min, t5_max) / 100), 2)
        p_t5_high = round(safe_ltp * (1 + max(t5_min, t5_max) / 100), 2)
        p_t10_low = round(safe_ltp * (1 + min(t10_min, t10_max) / 100), 2)
        p_t10_high = round(safe_ltp * (1 + max(t10_min, t10_max) / 100), 2)

        # Dynamic Volatility-Adaptive Stop Loss:
        # Incorporates 1.5x intraday ATR + VIX Volatility Padding (prevents morning wick stop-outs)
        base_sl_pct = max(3.20, atr_pct * 1.50)
        padded_sl_pct = base_sl_pct * vix_sl_padding_mult
        stop_loss_pct = round(min(5.50, max(3.20, padded_sl_pct)), 2)
        sl_price = round(safe_ltp * (1 - stop_loss_pct / 100), 2) if direction == "BULLISH" else round(safe_ltp * (1 + stop_loss_pct / 100), 2)

        # Predicted Opening Price Range for Post-Market News
        predicted_open_range = None
        if is_after_market:
            gap_center = round(t1_min_mag * 0.75 * sign, 2)
            p_open_lo = round(safe_ltp * (1 + (gap_center - 0.25) / 100), 2)
            p_open_hi = round(safe_ltp * (1 + (gap_center + 0.35) / 100), 2)
            predicted_open_range = f"₹{min(p_open_lo, p_open_hi):,.2f} - ₹{max(p_open_lo, p_open_hi):,.2f} ({gap_center:+.2f}%)"

        return {
            "dispatchable": True,
            "reason": None,
            "t1": {
                "range_pct": f"{min(t1_safe_pct, t1_runner_pct):+.2f}% to {max(t1_safe_pct, t1_runner_pct):+.2f}%",
                "price_target": f"₹{min(t1_safe_price, t1_runner_price):,.2f} - ₹{max(t1_safe_price, t1_runner_price):,.2f}",
                "price_low": min(t1_safe_price, t1_runner_price),
                "price_high": max(t1_safe_price, t1_runner_price),
                "deadline": "Tomorrow 09:15 AM Open" if is_after_market else "Tomorrow (T+1)"
            },
            "two_tier": {
                "t1_safe": {
                    "label": "T1 Safe Profit-Lock",
                    "price": t1_safe_price,
                    "percentage": f"{t1_safe_pct:+.2f}%",
                    "action_advice": "Book 70% profit here to secure green gains before resistance",
                    "clamped_to_milestone": clamped_to_wall
                },
                "t2_runner": {
                    "label": "T2 Breakout Runner",
                    "price": t1_runner_price,
                    "percentage": f"{t1_runner_pct:+.2f}%",
                    "action_advice": "Trail stop-loss to entry cost and ride breakout extension"
                }
            },
            "t5": {
                "range_pct": f"{min(t5_min, t5_max):+.2f}% to {max(t5_min, t5_max):+.2f}%",
                "price_target": f"₹{p_t5_low:,.2f} - ₹{p_t5_high:,.2f}",
                "deadline": "1-Week (T+5)"
            },
            "t10": {
                "range_pct": f"{min(t10_min, t10_max):+.2f}% to {max(t10_min, t10_max):+.2f}%",
                "price_target": f"₹{p_t10_low:,.2f} - ₹{p_t10_high:,.2f}",
                "deadline": "2-Weeks (T+10)"
            },
            "stop_loss": f"₹{sl_price:,.2f} ({'-' if direction == 'BULLISH' else '+'}{stop_loss_pct}%)",
            "stop_loss_pct": stop_loss_pct,
            "stop_loss_price": sl_price,
            "t1_mag": abs(t1_safe_pct),
            "predicted_open_range": predicted_open_range,
            "recommended_strategy": rec_strategy,
            "target_confidence_note": target_note,
            "suppress_chase_alert": suppress_chase,
            "conviction_delta": regime_eval.get("conviction_delta", 0.0),
            "market_drag_contribution_pct": regime_eval.get("market_drag_contribution_pct", 0.0)
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

            # Dynamic Company Intelligence & Tier
            intel = CompanyIntelligenceProvider.get_company_intelligence(symbol)
            tier = intel.get("tier", "MID_CAP")
            annual_rev = intel.get("annual_revenue_cr", 20000.0)
            atr_val = intel.get("atr_14_pct", 2.5)

            # Check Market Timing (After-Hours vs Market Hours)
            now = datetime.now()
            minute_of_day = now.hour * 60 + now.minute
            is_after_market = (minute_of_day < (9 * 60 + 15) or minute_of_day >= (15 * 60 + 30))

            # Audit Mandate 5: Fail closed when fundamentals are unknown. Never invent synthetic fundamentals.
            if intel.get("profile_verified") is False or not intel.get("dispatchable", True):
                reason = intel.get("suppression_reason", "UNVERIFIED_COMPANY_FUNDAMENTALS")
                print(f"[UNVERIFIED COMPANY INTEL] {symbol}: Filtered due to {reason}. Suppressing alerts.", flush=True)
                signal_record = {
                    "id": f"AUTO_{int(time.time())}_{symbol}",
                    "symbol": symbol,
                    "company_name": intel.get("company_name", symbol),
                    "sector": "Unverified",
                    "tier": "UNVERIFIED",
                    "source_type": source,
                    "headline": headline,
                    "published_at": item.get("published_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                    "processed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "market_session": "AFTER_HOURS_CLOSED" if is_after_market else "MARKET_HOURS_ACTIVE",
                    "is_after_hours": is_after_market,
                    "current_base_price_inr": None,
                    "predicted_direction": "NEUTRAL",
                    "conviction_score_pct": 0.0,
                    "is_useful": False,
                    "dispatchable": False,
                    "actionability_status": f"SUPPRESSED_{reason}",
                    "suppression_reason": reason,
                    "recommended_strategy": f"SUPPRESSED_{reason}",
                    "ai_model": "UNVERIFIED_FILTER"
                }
                self.live_stream.insert(0, signal_record)
                self._save_stream()
                signals_retention_manager.store_signal(signal_record)
                return signal_record

            company_meta = {
                "symbol": symbol,
                "company_name": item.get("company_name") or intel.get("company_name", symbol),
                "sector": intel.get("sector", item.get("sector", "Diversified")),
                "annual_revenue_cr": annual_rev,
                "market_cap_cr": intel.get("market_cap_cr", 15000.0),
                "tier": tier,
                "atr_percentage": atr_val
            }

            # AI Prediction (uses Jev Model API if configured, otherwise calibrated institutional ensemble)
            pred = jev_classifier.classify_event(headline, company_meta)
            pred_dir = pred.get("direction", "NEUTRAL")
            is_useful = pred_dir in ["BULLISH", "BEARISH"] and pred.get("is_actionable", True)
            conviction = pred.get("conviction_pct", pred.get("confidence", 75.0))
            
            # Query Vector RAG Engine for Historical Event Analogs
            top_rag_match = None
            historical_return_1d = None
            try:
                rag_matches = self.rag_engine.search_similar_patterns(headline, sector=company_meta["sector"], top_k=2)
                if rag_matches:
                    top_rag_match = rag_matches[0]
                    historical_return_1d = top_rag_match.get("pattern", {}).get("actual_1d_return_pct")
            except Exception as e:
                print(f"[RAG ENGINE] Query note: {e}", flush=True)

            # Real-time LTP & Active Stock Tradability Verification Gatekeeper
            quote = LivePriceProvider.get_live_quote(symbol, force_fresh=True)
            ltp = float(quote.get("ltp") or 0.0) if quote else None
            if ltp is None or ltp <= 0:
                ltp = self.fetch_live_price(symbol, force_fresh=True)

            # Audit Mandate 4: Strict Tradability Rejection (OR Rule)
            minimum_price = 50.0
            minimum_median_20d_adtv_cr = 2.0
            maximum_spread_bps = 25.0

            lower_head = headline.lower()
            is_cirp = any(term in lower_head for term in [
                "insolvency resolution process", "cirp", "liquidation", 
                "resolution professional", "compulsory delisting", "bifr", "nclt liquidation"
            ])
            circuit_locked = quote.get("is_circuit_locked", False) if quote else False
            surveillance = quote.get("is_under_surveillance", False) if quote else False
            is_fno_eligible = intel.get("fno_lot_size") is not None and intel.get("fno_lot_size") > 0

            is_untradeable = any((
                quote is None,
                ltp is None or not math.isfinite(float(ltp)) or float(ltp) <= 0,
                (quote.get("quote_age_seconds", float("inf")) > 5 if not is_after_market else False) if quote else True,
                (ltp < minimum_price) if (ltp and math.isfinite(float(ltp))) else True,
                (quote.get("median_20d_adtv_cr", 0.0) < minimum_median_20d_adtv_cr) if quote else True,
                (quote.get("bid", 0.0) <= 0) if quote else True,
                (quote.get("ask", 0.0) <= 0) if quote else True,
                (quote.get("spread_bps", float("inf")) > maximum_spread_bps) if quote else True,
                circuit_locked,
                surveillance,
                is_cirp,
                (pred_dir == "BEARISH" and not is_fno_eligible)
            ))

            if is_untradeable:
                if ltp is None or float(ltp or 0) <= 0: untradeable_reason = "UNVERIFIED_LIVE_PRICE"
                elif is_cirp: untradeable_reason = "CIRP_INSOLVENCY"
                elif ltp < minimum_price: untradeable_reason = "PENNY_PRICE_UNDER_50"
                elif (pred_dir == "BEARISH" and not is_fno_eligible): untradeable_reason = "SHORT_NOT_FNO_ELIGIBLE"
                elif circuit_locked: untradeable_reason = "CIRCUIT_LOCKED"
                elif surveillance: untradeable_reason = "UNDER_SURVEILLANCE"
                elif quote and quote.get("spread_bps", 0) > maximum_spread_bps: untradeable_reason = "SPREAD_TOO_WIDE"
                elif quote and quote.get("median_20d_adtv_cr", 0.0) < minimum_median_20d_adtv_cr: untradeable_reason = "LOW_ADTV_TURNOVER"
                else: untradeable_reason = "UNTRADABLE_QUOTE_QUALITY"

                print(f"[UNTRADABLE/RISK FILTER] {symbol}: Filtered due to {untradeable_reason} (LTP: {ltp}). Suppressing alerts.", flush=True)
                signal_record = {
                    "id": f"AUTO_{int(time.time())}_{symbol}",
                    "symbol": symbol,
                    "company_name": company_meta["company_name"],
                    "sector": company_meta["sector"],
                    "tier": tier,
                    "source_type": source,
                    "headline": headline,
                    "published_at": item.get("published_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                    "processed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "market_session": "AFTER_HOURS_CLOSED" if is_after_market else "MARKET_HOURS_ACTIVE",
                    "is_after_hours": is_after_market,
                    "current_base_price_inr": ltp,
                    "predicted_direction": "NEUTRAL",
                    "conviction_score_pct": 0.0,
                    "is_useful": False,
                    "dispatchable": False,
                    "actionability_status": f"SUPPRESSED_{untradeable_reason}",
                    "suppression_reason": untradeable_reason,
                    "recommended_strategy": f"UNTRADABLE_{untradeable_reason}",
                    "ai_model": pred.get("model_engine", "JEV_AI_CLASSIFIER")
                }
                self.live_stream.insert(0, signal_record)
                self._save_stream()
                signals_retention_manager.store_signal(signal_record)
                return signal_record

            # Live Market Regime & India VIX Fetch for Dynamic Confluence
            regime_data = LivePriceProvider.get_market_regime()
            if not regime_data.get("source_healthy", True) or not regime_data.get("dispatchable", True):
                reason = regime_data.get("reason", "MARKET_REGIME_UNAVAILABLE")
                print(f"[REGIME UNAVAILABLE] {symbol}: Regime source unhealthy ({reason}). Suppressing alert.", flush=True)
                signal_record = {
                    "id": f"AUTO_{int(time.time())}_{symbol}",
                    "symbol": symbol,
                    "company_name": company_meta["company_name"],
                    "sector": company_meta["sector"],
                    "tier": tier,
                    "source_type": source,
                    "headline": headline,
                    "published_at": item.get("published_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                    "processed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "market_session": "AFTER_HOURS_CLOSED" if is_after_market else "MARKET_HOURS_ACTIVE",
                    "is_after_hours": is_after_market,
                    "current_base_price_inr": ltp,
                    "predicted_direction": "NEUTRAL",
                    "conviction_score_pct": 0.0,
                    "is_useful": False,
                    "dispatchable": False,
                    "actionability_status": f"SUPPRESSED_{reason}",
                    "suppression_reason": reason,
                    "recommended_strategy": f"SUPPRESSED_{reason}",
                    "ai_model": pred.get("model_engine", "JEV_AI_CLASSIFIER")
                }
                self.live_stream.insert(0, signal_record)
                self._save_stream()
                signals_retention_manager.store_signal(signal_record)
                return signal_record

            nifty_change = float(regime_data.get("nifty_change_pct", 0.0))
            nifty_3d = float(regime_data.get("nifty_return_3d", nifty_change))
            india_vix = float(regime_data.get("india_vix", 16.0))
            vix_change = float(regime_data.get("vix_change_pct", 0.0))
            vix_sl_mult = float(regime_data.get("vix_sl_padding_multiplier", 1.0))
            stock_beta = float(intel.get("nifty_beta", 1.10))
            sector_beta = float(intel.get("sector_beta", 1.0))

            # Upper / Lower Circuit Freeze Check
            circuit_info = CircuitFreezeDetector.detect_circuit_status(quote)

            # Calculate Materiality Ratio
            materiality_ratio = pred.get("materiality_ratio", 0.0)
            
            targets = self.compute_forward_targets(
                ltp=ltp,
                direction=pred_dir,
                atr_pct=company_meta["atr_percentage"],
                materiality=materiality_ratio,
                tier=tier,
                historical_return_1d=historical_return_1d,
                is_after_market=is_after_market,
                symbol=symbol,
                nifty_change_pct=nifty_change,
                india_vix=india_vix,
                vix_sl_padding_mult=vix_sl_mult,
                stock_beta=stock_beta,
                nifty_return_3d=nifty_3d,
                sector_return_1d=0.0,
                vix_change_pct=vix_change,
                sector_beta=sector_beta,
                is_fno_eligible=is_fno_eligible
            )

            # Audit Mandate 1: Terminal Regime/Alpha Veto
            if not targets.get("dispatchable", True):
                sup_reason = targets.get("reason", "REGIME_VETO")
                print(f"[REGIME/ALPHA VETO] {symbol}: Terminal veto ({sup_reason}). Suppressing alert.", flush=True)
                signal_record = {
                    "id": f"AUTO_{int(time.time())}_{symbol}",
                    "symbol": symbol,
                    "company_name": company_meta["company_name"],
                    "sector": company_meta["sector"],
                    "tier": tier,
                    "source_type": source,
                    "headline": headline,
                    "published_at": item.get("published_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                    "processed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "market_session": "AFTER_HOURS_CLOSED" if is_after_market else "MARKET_HOURS_ACTIVE",
                    "is_after_hours": is_after_market,
                    "current_base_price_inr": ltp,
                    "predicted_direction": "NEUTRAL",
                    "conviction_score_pct": 0.0,
                    "is_useful": False,
                    "dispatchable": False,
                    "actionability_status": f"SUPPRESSED_{sup_reason}",
                    "suppression_reason": sup_reason,
                    "recommended_strategy": f"SUPPRESSED_{sup_reason}",
                    "ai_model": pred.get("model_engine", "JEV_AI_CLASSIFIER")
                }
                self.live_stream.insert(0, signal_record)
                self._save_stream()
                signals_retention_manager.store_signal(signal_record)
                return signal_record

            # Apply Regime Confluence Conviction Adjustment (Boosts shorts in falling market, penalizes long breakouts)
            conviction = max(50.0, min(98.0, round(conviction + targets.get("conviction_delta", 0.0), 1)))

            # Institutional Risk-to-Reward (R:R) & Kelly Criterion Position Sizing
            t1_mag = targets.get("t1_mag", company_meta["atr_percentage"])
            sl_mag = targets.get("stop_loss_pct", 2.0)
            sizing = self.kelly_sizer.calculate_sizing(
                ltp=ltp,
                win_prob=conviction / 100.0,
                target_pct=t1_mag,
                stop_loss_pct=sl_mag
            )
            rr_ratio_str = f"1 : {sizing['reward_risk_ratio_b']:.1f}"

            rec_strat = targets.get("recommended_strategy") or ("STRONG BUY ACCUMULATION" if pred_dir == "BULLISH" else ("TACTICAL SHORT / HEDGE" if pred_dir == "BEARISH" else "NEUTRAL WATCH"))
            order_type = "ACCUMULATE_ON_DIP_ONLY" if targets.get("suppress_chase_alert") else ("ACCUMULATE_BEFORE_MOVE" if pred_dir == "BULLISH" else "TACTICAL_SHORT")

            signal_record = {
                "id": f"AUTO_{int(time.time())}_{symbol}",
                "symbol": symbol,
                "company_name": company_meta["company_name"],
                "sector": company_meta["sector"],
                "tier": tier,
                "source_type": source,
                "headline": headline,
                "published_at": item.get("published_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                "processed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "market_session": "AFTER_HOURS_CLOSED" if is_after_market else "MARKET_HOURS_ACTIVE",
                "is_after_hours": is_after_market,
                "predicted_open_price_inr": targets.get("predicted_open_range"),
                "current_base_price_inr": ltp,
                "predicted_direction": pred_dir,
                "conviction_score_pct": conviction,
                "materiality_ratio": materiality_ratio,
                "circuit_info": circuit_info,
                "is_circuit_locked": circuit_info.get("is_circuit_locked", False),
                "circuit_warning": circuit_info.get("warning_badge"),
                "risk_reward_ratio": rr_ratio_str,
                "reward_risk_ratio_val": sizing["reward_risk_ratio_b"],
                "position_sizing": {
                    "risk_reward_ratio": rr_ratio_str,
                    "optimal_allocation_pct": sizing["optimal_allocation_pct"],
                    "allocated_capital_inr": sizing["allocated_capital_inr"],
                    "shares_quantity": sizing["shares_quantity"],
                    "max_stop_loss_risk_inr": sizing["max_stop_loss_risk_inr"],
                    "target_profit_inr": sizing["target_profit_inr"],
                    "risk_profile": sizing["risk_profile"]
                },
                "allocated_capital_inr": sizing["allocated_capital_inr"],
                "shares_qty": sizing["shares_quantity"],
                "historical_rag_match": {
                    "matched_title": top_rag_match["pattern"]["title"] if top_rag_match else None,
                    "similarity_score": round(top_rag_match["score"], 4) if top_rag_match else None,
                    "historical_1d_return": historical_return_1d,
                    "historical_direction": top_rag_match["pattern"]["actual_direction"] if top_rag_match else None
                } if top_rag_match else None,
                "ai_model": pred.get("model_engine", "JEV_AI_CLASSIFIER"),
                "model_version": ModelVersionManager.get_active_version(),
                "engine_version": ModelVersionManager.get_active_version(),
                "is_useful": is_useful,
                "dispatchable": False if is_after_market else True,
                "actionability_status": "PENDING_PREOPEN_VERIFICATION" if is_after_market else "DISPATCHABLE_ACTIVE",
                "preopen_status": "PENDING" if is_after_market else "NOT_APPLICABLE",
                "t1_target": {
                    "percentage_range": targets["t1"]["range_pct"],
                    "price_target_range_inr": targets["t1"]["price_target"],
                    "price_low": targets["t1"]["price_low"],
                    "price_high": targets["t1"]["price_high"],
                    "target_date_horizon": targets["t1"]["deadline"]
                },
                "two_tier_targets": targets.get("two_tier"),
                "t1_safe_target": targets.get("two_tier", {}).get("t1_safe"),
                "t2_runner_target": targets.get("two_tier", {}).get("t2_runner"),
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
                "recommended_strategy": rec_strat,
                "execution_order_type": order_type,
                "target_confidence_note": targets.get("target_confidence_note"),
                "market_drag_contribution_pct": targets.get("market_drag_contribution_pct", 0.0),
                "india_vix": india_vix,
                "nifty_change_pct": nifty_change
            }

            self.live_stream.insert(0, signal_record)
            self._save_stream()

            # Strict 90-Day Retention Archive
            signals_retention_manager.store_signal(signal_record)
            print(f"[NEW EVENT PROCESSED] {symbol} ({tier}) | {pred_dir} ({conviction}%) | LTP: INR {ltp} | Session: {signal_record['market_session']}", flush=True)

            # Cloud Bridge: Real-Time Supabase Upsert
            self._sync_to_supabase(signal_record)

            # Automatic Multi-Channel Alert Dispatch (WhatsApp & Email)
            if (
                signal_record.get("dispatchable", True) is True
                and signal_record.get("is_useful", True) is True
                and signal_record.get("conviction_score_pct", 0) >= 70
            ):
                self._dispatch_instant_alert(signal_record)
            elif is_after_market and is_useful and conviction >= 70:
                print(f"[OVERNIGHT SIGNAL QUEUED] {symbol}: Queued for 09:08 AM Pre-Open Auction Verification (live dispatch deferred).", flush=True)

            return signal_record
        except Exception as e:
            print(f"[ERROR PROCESSING ITEM] {item.get('symbol', 'UNKNOWN')}: {e}", flush=True)
            return None

    def _dispatch_instant_alert(self, signal: dict):
        # Strict Tradability, Veto & Inactive Stock Guard
        ltp = signal.get("current_base_price_inr")
        if (
            signal.get("dispatchable", True) is not True
            or signal.get("is_useful", True) is not True
            or signal.get("conviction_score_pct", 0) < 70
            or not ltp
            or float(ltp) <= 0
            or str(signal.get("actionability_status", "")).startswith("SUPPRESSED")
        ):
            print(f"[ALERT SUPPRESSED] Suppressing notification for {signal.get('symbol')} (Untradable/Suppressed/Inactive).", flush=True)
            return

        # Target verification check (informational only - do NOT suppress alert per user preference)
        try:
            t1 = signal.get("t1_target", {})
            dir_text = signal.get("predicted_direction", "")
            ltp = signal.get("current_base_price_inr")
            t1_lo = t1.get("price_low")
            t1_hi = t1.get("price_high")

            if t1_lo is None or t1_hi is None:
                price_str = t1.get("price_target_range_inr", "")
                nums = re.findall(r"[\d]+\.?\d*", price_str.replace(",", ""))
                if len(nums) >= 2:
                    t1_lo, t1_hi = float(nums[0]), float(nums[1])

            if ltp and t1_lo and t1_hi:
                if dir_text == "BULLISH" and ltp >= t1_lo:
                    signal["target_already_exhausted"] = True
                    signal["execution_note"] = "HIGH_MOMENTUM_LTP_NEAR_TARGET"
                    print(f"[LIVE DISPATCH NOTICE] High velocity move underway for {signal['symbol']} (LTP ₹{ltp} already reached target low ₹{t1_lo}). Dispatching immediate alert with momentum tag.", flush=True)
                elif dir_text == "BEARISH" and ltp <= t1_hi:
                    signal["target_already_exhausted"] = True
                    signal["execution_note"] = "HIGH_MOMENTUM_LTP_NEAR_TARGET"
                    print(f"[LIVE DISPATCH NOTICE] High velocity move underway for {signal['symbol']} (LTP ₹{ltp} already reached target high ₹{t1_hi}). Dispatching immediate alert with momentum tag.", flush=True)
        except Exception as filter_err:
            print(f"[DISPATCH CHECK NOTE] {filter_err}", flush=True)

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
            with urllib.request.urlopen(req, timeout=12) as resp:
                if resp.status == 200:
                    print(f"[AUTO-ALERT BROADCAST] Successfully sent WhatsApp, Email & Telegram for {signal['symbol']}", flush=True)
                    dispatched_hub = True
        except Exception as e:
            # Hub offline or error
            pass

        # Direct Python Fallback (always delivers even on cloud/Render without Node hub)
        if not dispatched_hub:
            self._dispatch_direct_email(signal)
            self._dispatch_direct_telegram(signal)

    def _dispatch_direct_email(self, signal: dict):
        if os.environ.get("ENABLE_EMAIL_NOTIFICATIONS", "").lower() == "false" or os.environ.get("EMAIL_NOTIFICATIONS_PAUSED", "").lower() == "true":
            return
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
            tt = signal.get("two_tier_targets") or {}
            t1_safe = tt.get("t1_safe", {})
            t2_runner = tt.get("t2_runner", {})
            safe_str = f"₹{t1_safe.get('price'):,.2f} ({t1_safe.get('percentage')})" if t1_safe.get('price') else t1
            runner_str = f"₹{t2_runner.get('price'):,.2f} ({t2_runner.get('percentage')})" if t2_runner.get('price') else "Trailing Extension"

            is_bull = dir_text.upper() == "BULLISH"
            action_text = "BUY" if is_bull else "SELL"
            action_color = "#10b981" if is_bull else "#ef4444"
            formatted_ltp = f"₹{ltp:,.2f}" if ltp > 0 else "N/A"
            when_wait_t2 = (
                f"Hold remaining 30% only if price sustains above T1 ({safe_str}) with strong volume. Move Stop-Loss to entry price ({formatted_ltp})."
                if is_bull else
                f"Hold remaining 30% only if selling momentum continues below T1 ({safe_str}). Trail Stop-Loss to entry price ({formatted_ltp})."
            )
            if signal.get("preopen_status") == "APPROVED_FOR_EXECUTION":
                subject = f"🎯 {symbol} — {action_text} ALERT (🔔 PRE-OPEN VERIFIED) | Entry {formatted_ltp}"
            else:
                subject = f"🎯 {symbol} — {action_text} ALERT | LTP {formatted_ltp}"
            circuit_warn = signal.get("circuit_warning")
            circuit_html = f'<div style="margin-bottom: 12px; padding: 8px 12px; background: #7f1d1d; color: #fecaca; border-radius: 6px; font-weight: bold; font-size: 13px;">{circuit_warn}</div>' if circuit_warn else ""

            headline_text = signal.get("headline", "")
            import re
            cleaned_reason = re.sub(r"\s*-\s*\d{5,6}\s*-\s*", " - ", headline_text).strip()
            if len(cleaned_reason) > 200:
                cleaned_reason = cleaned_reason[:197] + "..."

            html_content = f"""
            <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 500px; margin: auto; padding: 20px; background: #0f172a; color: #f8fafc; border-radius: 12px; border: 1px solid #334155;">
              <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #334155; padding-bottom: 12px; margin-bottom: 16px;">
                <h2 style="margin: 0; color: #ffffff; font-size: 20px;">🎯 {symbol}</h2>
                <span style="background: {action_color}; color: #ffffff; padding: 4px 10px; border-radius: 6px; font-weight: bold; font-size: 13px;">{action_text}</span>
              </div>
              {circuit_html}
              <div style="display: flex; justify-content: space-between; margin-bottom: 10px; font-size: 14px;">
                <span style="color: #94a3b8;">Current Price:</span>
                <strong style="color: #ffffff;">{formatted_ltp}</strong>
              </div>
              <div style="display: flex; justify-content: space-between; margin-bottom: 14px; font-size: 14px;">
                <span style="color: #94a3b8;">Stop-Loss:</span>
                <strong style="color: #ef4444;">{sl}</strong>
              </div>

              <div style="background: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 12px 14px; margin-bottom: 14px;">
                <div style="margin-bottom: 6px; font-size: 13px;">
                  <strong style="color: #10b981;">• T1 (Safe Exit):</strong> {safe_str} — <span style="font-size: 11px; color: #94a3b8;">Book 70% Profit</span>
                </div>
                <div style="font-size: 13px;">
                  <strong style="color: #38bdf8;">• T2 (Runner):</strong> {runner_str}
                </div>
              </div>

              <div style="background: rgba(56, 189, 248, 0.08); border-left: 3px solid #38bdf8; padding: 10px 12px; border-radius: 0 6px 6px 0; font-size: 12px; color: #e2e8f0; margin-bottom: 14px; line-height: 1.4;">
                <strong style="color: #38bdf8;">💡 When to wait for T2:</strong><br/>
                {when_wait_t2}
              </div>

              <div style="background: #1e293b; border-radius: 6px; padding: 10px 12px; font-size: 12px; color: #cbd5e1; line-height: 1.4;">
                <strong style="color: #ffffff;">📌 Reason:</strong><br/>
                {cleaned_reason}
              </div>

              <div style="margin-top: 16px; font-size: 11px; color: #64748b; text-align: center;">
                Dispatched at {datetime.now().strftime('%I:%M %p IST')}
              </div>
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
    def _dispatch_direct_telegram(self, signal: dict):
        try:
            bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
            chat_id = os.environ.get("TELEGRAM_CHAT_ID", os.environ.get("TELEGRAM_CHANNEL_ID", "-1004309575686")).strip()
            if not bot_token:
                return

            sym = signal.get("symbol", "STOCK")
            dir_text = signal.get("predicted_direction", "BULLISH").upper()
            is_bull = dir_text == "BULLISH"
            action_title = "BUY" if is_bull else "SELL"
            action_text = "🟢 <b>BUY</b>" if is_bull else "🔴 <b>SELL</b>"
            ltp = float(signal.get("current_live_ltp_t0") or signal.get("current_base_price_inr") or 0.0)
            formatted_ltp = f"₹{ltp:,.2f}" if ltp > 0 else "N/A"
            sl = signal.get("recommended_stop_loss", "N/A")
            t1 = signal.get("t1_target", {}).get("price_target_range_inr", "N/A")
            t1_pct = signal.get("t1_target", {}).get("percentage_range", "")
            t1_pct_str = f" ({t1_pct})" if t1_pct else ""
            headline = signal.get("headline", "")

            preopen_badge = ""
            if signal.get("preopen_status") == "APPROVED_FOR_EXECUTION":
                gap_val = signal.get("preopen_gap_pct", 0.0)
                preopen_badge = f"\n🔔 <b>PRE-OPEN AUCTION VERIFIED (09:10 AM)</b>\n• <b>Auction Gap:</b> <code>{gap_val:+.2f}%</code>\n"

            drag_badge = ""
            drag_val = signal.get("market_drag_contribution_pct")
            if drag_val and abs(float(drag_val)) > 0:
                drag_badge = f"• <b>Market Beta Drag:</b> <code>{float(drag_val):+.2f}%</code>\n"

            msg_text = (
                f"🎯 <b>{sym} — {action_title} ALERT</b>{preopen_badge}\n"
                f"• <b>Action:</b> {action_text}\n"
                f"• <b>Current Price:</b> <code>{formatted_ltp}</code>\n"
                f"{drag_badge}"
                f"• <b>Stop-Loss:</b> <code>{sl}</code>\n\n"
                f"🎯 <b>Targets:</b>\n"
                f"• <b>T1 (Safe Exit):</b> <code>{t1}</code>{t1_pct_str} — [Book 70% Profit]\n\n"
                f"📌 <b>Reason:</b>\n{headline}\n\n"
                f"⏱️ {datetime.now().strftime('%I:%M %p IST')} • Engine v3.0"
            )

            req_data = json.dumps({
                "chat_id": chat_id,
                "text": msg_text,
                "parse_mode": "HTML",
                "disable_web_page_preview": True
            }).encode("utf-8")

            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            req = urllib.request.Request(url, data=req_data, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=5) as res:
                if res.status == 200:
                    print(f"[DIRECT-TELEGRAM DISPATCH] Delivered alert for {sym} to {chat_id}", flush=True)
        except Exception as e:
            print(f"[DIRECT-TELEGRAM ERROR] {e}", flush=True)


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
            with urllib.request.urlopen(req, timeout=12) as resp:
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

    def run_daemon(self, interval_seconds=None):
        print(f"[AUTO-STREAM DAEMON] Immediate Starter High-Frequency Poller Active (Sub-Second Market Hours / 10s After-Hours)...", flush=True)
        while True:
            try:
                now = datetime.now()
                # Check if currently active NSE/BSE market hours (09:15 - 15:30 IST, Mon-Fri)
                is_weekday = now.weekday() < 5
                minute_of_day = now.hour * 60 + now.minute
                is_market_active = is_weekday and ((9 * 60 + 15) <= minute_of_day <= (15 * 60 + 30))
                
                # Near-zero latency starter loop: 0.2s pause during market hours
                current_interval = interval_seconds if interval_seconds is not None else (0.2 if is_market_active else 10)
                
                new_count = self.poll_cycle()
                if new_count > 0:
                    print(f"[{now.strftime('%H:%M:%S')}] Ingested & Analyzed {new_count} new market events instantaneously.", flush=True)
            except Exception as e:
                print(f"[Daemon Error] {e}", flush=True)
                current_interval = 2
            time.sleep(current_interval)

if __name__ == "__main__":
    worker = AutoLiveStreamWorker()
    if "--daemon" in sys.argv:
        worker.run_daemon(interval_seconds=30)
    else:
        new_events = worker.poll_cycle()
        print(f"Single Poll Complete. Ingested {new_events} new events.")
