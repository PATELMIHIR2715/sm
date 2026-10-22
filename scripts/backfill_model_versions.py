"""
Database Migration Script: Backfill Model & Engine Versions on Past Signals.

Categorizes all existing records across:
- data/live_signals_stream.json
- data/signals_archive_90d.json

Uses ModelVersionManager logic to tag:
- v3.0: Two-tier milestone wall front-running & circuit protection
- v2.0: Dynamic ATR corridor, RAG & Kelly sizing
- v1.0: Baseline NLP sentiment scoring
"""

import os
import sys
import json

PROJECT_ROOT = os.environ.get("PROJECT_ROOT", os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(PROJECT_ROOT)
from services.evaluation.model_version_manager import ModelVersionManager

def backfill_file(file_path: str):
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        records = json.load(f)

    counts = {"v1.0": 0, "v2.0": 0, "v3.0": 0}
    updated = 0

    for r in records:
        ver = ModelVersionManager.determine_signal_version(r)
        counts[ver] = counts.get(ver, 0) + 1
        r["model_version"] = ver
        r["engine_version"] = ver
        updated += 1

    tmp_path = file_path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

    os.replace(tmp_path, file_path)
    print(f"Backfilled {updated} records in {os.path.basename(file_path)}:")
    print(f"  Breakdown: {counts}")

if __name__ == "__main__":
    stream_file = os.path.join(PROJECT_ROOT, "data/live_signals_stream.json")
    archive_file = os.path.join(PROJECT_ROOT, "data/signals_archive_90d.json")

    backfill_file(stream_file)
    backfill_file(archive_file)
    print("ALL PAST DATABASE RECORDS SUCCESSFULLY MIGRATED WITH MODEL VERSIONS!")
