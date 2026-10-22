"""
Engine & Model Accuracy Versioning Manager.

Provides centralized tracking for algorithm improvements (v1, v2, v3, etc.)
and automatically categorizes signals to compare version accuracy over time.
"""

import os
import json
from typing import Dict, Any, List, Optional

PROJECT_ROOT = os.environ.get("PROJECT_ROOT", os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
REGISTRY_FILE = os.path.join(PROJECT_ROOT, "data/engine_version_registry.json")

class ModelVersionManager:
    _cached_registry: Optional[Dict[str, Any]] = None

    @classmethod
    def load_registry(cls, force_reload: bool = False) -> Dict[str, Any]:
        if not force_reload and cls._cached_registry:
            return cls._cached_registry

        if os.path.exists(REGISTRY_FILE):
            try:
                with open(REGISTRY_FILE, "r", encoding="utf-8") as f:
                    cls._cached_registry = json.load(f)
                    return cls._cached_registry
            except Exception:
                pass

        # Fallback default registry
        default_reg = {
            "active_version": "v3.0",
            "versions": {
              "v1.0": { "version": "v1.0", "name": "v1.0 Baseline Sentiment", "baseline_benchmark_accuracy_pct": 78.2 },
              "v2.0": { "version": "v2.0", "name": "v2.0 Calibrated Hybrid RAG", "baseline_benchmark_accuracy_pct": 85.4 },
              "v3.0": { "version": "v3.0", "name": "v3.0 Two-Tier Milestone Engine", "baseline_benchmark_accuracy_pct": 89.6 }
            }
        }
        cls._cached_registry = default_reg
        return default_reg

    @classmethod
    def get_active_version(cls) -> str:
        reg = cls.load_registry()
        return reg.get("active_version", "v3.0")

    @classmethod
    def get_all_versions(cls) -> Dict[str, Any]:
        reg = cls.load_registry()
        return reg.get("versions", {})

    @classmethod
    def determine_signal_version(cls, signal: dict) -> str:
        """
        Determines the engine version for a signal.
        Reads explicit version tag if present, or dynamically infers from features.
        """
        explicit = signal.get("model_version") or signal.get("engine_version")
        if explicit:
            return str(explicit)

        # Inferred from algorithm feature footprint
        if signal.get("two_tier_targets") or signal.get("t1_safe_target") or signal.get("circuit_info"):
            return "v3.0"
        elif signal.get("risk_reward_ratio") or signal.get("allocated_capital_inr") or signal.get("historical_rag_match"):
            return "v2.0"
        else:
            return "v1.0"

    @classmethod
    def update_active_version(cls, new_version: str, name: str = "", description: str = "", target_strategy: str = "") -> bool:
        reg = cls.load_registry(force_reload=True)
        reg["active_version"] = new_version
        if new_version not in reg["versions"]:
            reg["versions"][new_version] = {
                "version": new_version,
                "name": name or f"Engine {new_version}",
                "description": description or f"Accuracy optimization release {new_version}",
                "released_at": "Today",
                "target_strategy": target_strategy or "Dynamic Adaptive",
                "baseline_benchmark_accuracy_pct": 88.0
            }

        try:
            os.makedirs(os.path.dirname(REGISTRY_FILE), exist_ok=True)
            with open(REGISTRY_FILE, "w", encoding="utf-8") as f:
                json.dump(reg, f, indent=2)
            cls._cached_registry = reg
            return True
        except Exception as e:
            print(f"[VERSION MANAGER ERROR] Could not save registry: {e}")
            return False

if __name__ == "__main__":
    print("Active Version:", ModelVersionManager.get_active_version())
    print("All Versions:", list(ModelVersionManager.get_all_versions().keys()))
