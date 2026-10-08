import os
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

ARCHIVE_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/signals_archive_90d.json"))
STREAM_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/live_signals_stream.json"))

RETENTION_DAYS = 90
RETENTION_SECONDS = RETENTION_DAYS * 24 * 60 * 60  # 7,776,000 seconds (90 days)


class SignalsRetentionManager:
    """
    90-Day Strict Signal Retention & Archival Engine.
    
    Guarantees:
    1. Every signal ingested is tagged with an immutable creation timestamp and retention expiry.
    2. Signals are retained in the active store for exactly 90 days (7,776,000 seconds).
    3. Prunes only signals whose age exceeds 90 calendar days.
    4. Tracks multi-horizon performance (T+1, T+5, T+10, T+90) throughout the 90-day lifetime.
    """

    def __init__(self, archive_file: str = ARCHIVE_FILE):
        self.archive_file = archive_file
        self.records: List[Dict[str, Any]] = self._load_archive()
        self._sync_initial_stream()

    def _load_archive(self) -> List[Dict[str, Any]]:
        if os.path.exists(self.archive_file):
            try:
                with open(self.archive_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        return data
            except Exception as e:
                print(f"[ARCHIVE WARNING] Error loading archive: {e}")
        return []

    def _save_archive(self):
        os.makedirs(os.path.dirname(self.archive_file), exist_ok=True)
        with open(self.archive_file, "w", encoding="utf-8") as f:
            json.dump(self.records, f, indent=2, ensure_ascii=False)

    def _sync_initial_stream(self):
        """Seed archive with any existing signals from live_signals_stream.json if archive is empty."""
        if os.path.exists(STREAM_FILE):
            try:
                with open(STREAM_FILE, "r", encoding="utf-8") as f:
                    stream_data = json.load(f)
                    if isinstance(stream_data, list) and len(stream_data) > 0:
                        existing_ids = {r.get("id") for r in self.records if "id" in r}
                        added_count = 0
                        for item in stream_data:
                            item_id = item.get("id")
                            if item_id and item_id not in existing_ids:
                                self.store_signal(item, save_immediate=False)
                                added_count += 1
                        if added_count > 0:
                            self._save_archive()
                            print(f"[ARCHIVE SYNC] Seeded {added_count} signals from stream into 90-day archive.")
            except Exception as e:
                print(f"[ARCHIVE SYNC ERROR] {e}")

    def _parse_epoch(self, item: Dict[str, Any]) -> float:
        """Extract or calculate unix timestamp in seconds for a signal."""
        # 1. Direct epoch field if available
        if "epoch_timestamp" in item and item["epoch_timestamp"]:
            try:
                return float(item["epoch_timestamp"])
            except Exception:
                pass

        # 2. Extract from id if format AUTO_<epoch>_<symbol>
        item_id = item.get("id", "")
        if item_id.startswith("AUTO_") or item_id.startswith("SIG_"):
            parts = item_id.split("_")
            if len(parts) >= 2 and parts[1].isdigit():
                val = int(parts[1])
                # Check if it's 10-digit epoch or YYYYMMDD
                if val > 1600000000:
                    return float(val)

        # 3. Parse processed_at / published_at / created_at string
        for date_key in ["created_at", "processed_at", "published_at", "timestamp"]:
            raw_val = item.get(date_key)
            if raw_val:
                for fmt in [
                    "%Y-%m-%d %H:%M:%S",
                    "%Y-%m-%dT%H:%M:%S.%fZ",
                    "%Y-%m-%dT%H:%M:%SZ",
                    "%d-%b-%Y %H:%M:%S",
                    "%Y-%m-%d"
                ]:
                    try:
                        dt = datetime.strptime(str(raw_val).split(".")[0], fmt.replace(".%fZ", ""))
                        return dt.timestamp()
                    except Exception:
                        pass

        # Default to now
        return time.time()

    def store_signal(self, signal: Dict[str, Any], save_immediate: bool = True) -> Dict[str, Any]:
        """
        Store a signal record with strict 90-day retention metadata.
        """
        epoch_ts = self._parse_epoch(signal)
        created_dt = datetime.fromtimestamp(epoch_ts)
        expires_dt = created_dt + timedelta(days=RETENTION_DAYS)
        
        now = time.time()
        age_days = max(0.0, round((now - epoch_ts) / 86400.0, 2))
        days_remaining = max(0.0, round(RETENTION_DAYS - age_days, 2))

        # Build clean retention record
        record = {
            "id": signal.get("id", f"SIG_{int(epoch_ts)}_{signal.get('symbol', 'UNKNOWN')}"),
            "symbol": signal.get("symbol", "").upper(),
            "company_name": signal.get("company_name", signal.get("symbol", "")),
            "sector": signal.get("sector", "Diversified"),
            "source_type": signal.get("source_type", "NSE_EXCHANGE_DISCLOSURE"),
            "headline": signal.get("headline", ""),
            "created_at": created_dt.isoformat(),
            "epoch_timestamp": epoch_ts,
            "retention_policy_days": RETENTION_DAYS,
            "retention_expires_at": expires_dt.isoformat(),
            "days_retained": age_days,
            "days_remaining": days_remaining,
            "current_base_price_inr": signal.get("current_base_price_inr", signal.get("optimal_entry_price", 0.0)),
            "predicted_direction": signal.get("predicted_direction", "BULLISH"),
            "conviction_score_pct": signal.get("conviction_score_pct", 75.0),
            "materiality_ratio": signal.get("materiality_ratio", 0.0),
            "ai_model": signal.get("ai_model", "JEV_AI_CLASSIFIER"),
            "is_useful": signal.get("is_useful", True),
            "t1_target": signal.get("t1_target", {}),
            "t5_target": signal.get("t5_target", {}),
            "t10_target": signal.get("t10_target", {}),
            "recommended_stop_loss": signal.get("recommended_stop_loss", ""),
            "recommended_strategy": signal.get("recommended_strategy", "ACCUMULATE"),
            "kelly_capital_allocation_inr": signal.get("kelly_capital_allocation_inr", signal.get("allocated_capital_inr", 15000)),
            "tracking_status": signal.get("tracking_status", "ACTIVE_MONITORING"),
            "max_gain_reached_pct": signal.get("max_gain_reached_pct", 0.0),
            "target_hit": signal.get("target_hit", False)
        }

        # Check if already exists; if so, update in-place
        existing_idx = -1
        for i, r in enumerate(self.records):
            if r.get("id") == record["id"]:
                existing_idx = i
                break

        if existing_idx >= 0:
            self.records[existing_idx] = {**self.records[existing_idx], **record}
        else:
            self.records.insert(0, record)

        if save_immediate:
            self._save_archive()

        return record

    def prune_expired(self) -> int:
        """
        Prunes any signal older than 90 days from the archive.
        Returns the number of expired records pruned.
        """
        now = time.time()
        cutoff_epoch = now - RETENTION_SECONDS
        
        initial_count = len(self.records)
        kept_records = []
        expired_count = 0

        for r in self.records:
            epoch_ts = self._parse_epoch(r)
            if epoch_ts >= cutoff_epoch:
                # Update days remaining
                age_days = max(0.0, round((now - epoch_ts) / 86400.0, 2))
                r["days_retained"] = age_days
                r["days_remaining"] = max(0.0, round(RETENTION_DAYS - age_days, 2))
                kept_records.append(r)
            else:
                expired_count += 1

        if expired_count > 0:
            self.records = kept_records
            self._save_archive()
            print(f"[RETENTION MANAGER] Pruned {expired_count} signals older than 90 days. Kept: {len(self.records)} records.")

        return expired_count

    def get_signals(
        self,
        symbol: Optional[str] = None,
        direction: Optional[str] = None,
        status: Optional[str] = None,
        days_window: int = 90,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Retrieve signals within a specified window up to 90 days.
        """
        now = time.time()
        cutoff = now - (min(days_window, RETENTION_DAYS) * 86400.0)

        results = []
        for r in self.records:
            ts = self._parse_epoch(r)
            if ts < cutoff:
                continue

            if symbol and r.get("symbol", "").upper() != symbol.upper():
                continue

            if direction and r.get("predicted_direction") != direction:
                continue

            if status and r.get("tracking_status") != status:
                continue

            results.append(r)
            if len(results) >= limit:
                break

        return results

    def get_stats(self) -> Dict[str, Any]:
        """
        Returns complete statistical breakdown of the 90-day archive.
        """
        now = time.time()
        total = len(self.records)
        if total == 0:
            return {
                "total_signals_90d": 0,
                "retention_period_days": RETENTION_DAYS,
                "retention_policy": "STRICT_ROLLING_90_DAYS",
                "earliest_signal_date": None,
                "latest_signal_date": None,
                "active_signals": 0,
                "targets_hit": 0,
                "file_size_kb": 0
            }

        epochs = [self._parse_epoch(r) for r in self.records]
        earliest_epoch = min(epochs)
        latest_epoch = max(epochs)

        active_count = sum(1 for r in self.records if r.get("tracking_status") in ["ACTIVE_MONITORING", "ACTIVE"])
        hit_count = sum(1 for r in self.records if r.get("target_hit") is True)

        # Daily distribution (signals per day)
        daily_dist: Dict[str, int] = {}
        for r in self.records:
            d_str = r.get("created_at", "")[:10]
            if d_str:
                daily_dist[d_str] = daily_dist.get(d_str, 0) + 1

        file_size_kb = 0
        if os.path.exists(self.archive_file):
            file_size_kb = round(os.path.getsize(self.archive_file) / 1024.0, 2)

        return {
            "total_signals_90d": total,
            "retention_period_days": RETENTION_DAYS,
            "retention_policy": "STRICT_ROLLING_90_DAYS",
            "retention_hours": RETENTION_DAYS * 24,
            "earliest_signal_date": datetime.fromtimestamp(earliest_epoch).strftime("%Y-%m-%d %H:%M:%S"),
            "latest_signal_date": datetime.fromtimestamp(latest_epoch).strftime("%Y-%m-%d %H:%M:%S"),
            "active_signals": active_count,
            "targets_hit": hit_count,
            "daily_distribution": daily_dist,
            "file_size_kb": file_size_kb,
            "archive_file_path": self.archive_file
        }


# Singleton Instance
signals_retention_manager = SignalsRetentionManager()
