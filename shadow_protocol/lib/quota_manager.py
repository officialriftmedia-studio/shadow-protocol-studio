"""Quota Manager — track daily provider+model quota usage and estimate remaining capacity."""

from __future__ import annotations
import json
import os
from datetime import datetime, date, timezone
from pathlib import Path
from typing import Any


STATE_FILE = ".quota_state.json"

# Built-in model→quota map (overridden by config/quota_limits.json if it exists)
_DEFAULT_MODEL_QUOTAS: dict[str, dict[str, int]] = {
    "gemini-2.5-flash": {"rpd": 20, "rpm": 5, "tpm": 250000},
    "gemini-2.5-pro": {"rpd": 20, "rpm": 5, "tpm": 250000},
    "gemini-3.1-flash-lite": {"rpd": 500, "rpm": 15, "tpm": 250000},
    "gemini-2.0-flash": {"rpd": 1500, "rpm": 10, "tpm": 1000000},
    "qwen3:8b": {"rpd": 999999, "rpm": 9999, "tpm": 999999999},
    "qwen3:14b": {"rpd": 999999, "rpm": 9999, "tpm": 999999999},
    "deepseek-r1:14b": {"rpd": 999999, "rpm": 9999, "tpm": 999999999},
}

_QUOTA_CACHE: dict[str, dict[str, int]] | None = None


def _load_quota_limits() -> dict[str, dict[str, int]]:
    """Load per-model quota limits from config/quota_limits.json, falling back to built-ins."""
    global _QUOTA_CACHE
    if _QUOTA_CACHE is not None:
        return _QUOTA_CACHE

    search_dirs = [Path(__file__).resolve().parent.parent.parent, Path.cwd()]
    for base in search_dirs:
        path = base / "config" / "quota_limits.json"
        if path.exists():
            try:
                raw = json.loads(path.read_text())
                result: dict[str, dict[str, int]] = {}
                for provider, models in raw.items():
                    for model, limits in models.items():
                        result[model] = {
                            "rpd": limits.get("rpd", 999999),
                            "rpm": limits.get("rpm", 9999),
                            "tpm": limits.get("tpm", 999999999),
                        }
                _QUOTA_CACHE = result
                return result
            except Exception:
                pass

    _QUOTA_CACHE = dict(_DEFAULT_MODEL_QUOTAS)
    return _QUOTA_CACHE


def get_model_limits(model: str) -> dict[str, int]:
    """Return quota limits for a given model."""
    quotas = _load_quota_limits()
    return quotas.get(model, {"rpd": 999999, "rpm": 9999, "tpm": 999999999})


class QuotaManager:
    def __init__(self, projects_dir: str | Path):
        self.projects_dir = Path(projects_dir)

    # ── State persistence ──────────────────────────────────────────

    def _state_path(self) -> Path:
        return self.projects_dir / STATE_FILE

    def load_state(self) -> dict[str, Any]:
        path = self._state_path()
        if path.exists():
            return json.loads(path.read_text())
        return {}

    def save_state(self, state: dict[str, Any]) -> None:
        path = self._state_path()
        path.write_text(json.dumps(state, indent=2) + "\n")

    def reset_if_new_day(self, model: str) -> bool:
        state = self.load_state()
        today = date.today().isoformat()
        model_state = state.setdefault(model, {})
        if model_state.get("date") != today:
            model_state["date"] = today
            model_state["requests_used"] = 0
            model_state["input_tokens_used"] = 0
            self.save_state(state)
            return True
        return False

    # ── Tracking (per model) ───────────────────────────────────────

    def record_call(self, model: str, input_tokens: int = 0) -> None:
        self.reset_if_new_day(model)
        state = self.load_state()
        ms = state.setdefault(model, {})
        ms["requests_used"] = ms.get("requests_used", 0) + 1
        ms["input_tokens_used"] = ms.get("input_tokens_used", 0) + input_tokens
        ms["last_call"] = datetime.now(timezone.utc).isoformat()
        self.save_state(state)

    def get_usage(self, model: str) -> dict[str, Any]:
        self.reset_if_new_day(model)
        state = self.load_state()
        ms = state.get(model, {})
        limits = get_model_limits(model)

        used_req = ms.get("requests_used", 0)
        used_tokens = ms.get("input_tokens_used", 0)

        return {
            "model": model,
            "date": ms.get("date", date.today().isoformat()),
            "daily_requests": limits["rpd"],
            "used_today": used_req,
            "estimated_remaining": max(0, limits["rpd"] - used_req),
            "input_tokens_used": used_tokens,
            "input_tokens_remaining": max(0, limits.get("tpm", 999999999) - used_tokens),
            "last_call": ms.get("last_call"),
        }

    # ── Estimate for a new episode ─────────────────────────────────

    @staticmethod
    def _get_stage_model_map() -> dict[str, str]:
        """Return {stage: model} from stage_models.json."""
        search_dirs = [Path.cwd(), Path(__file__).resolve().parent.parent.parent]
        for base in search_dirs:
            path = base / "config" / "stage_models.json"
            if path.exists():
                try:
                    raw = json.loads(path.read_text())
                    stages = raw.get("stages", {})
                    defaults = raw.get("defaults", {})
                    default_model = defaults.get("model", "gemini-2.5-flash")
                    return {
                        stage: cfg.get("model", default_model)
                        for stage, cfg in stages.items()
                        if cfg.get("provider") not in (None, "none")
                    }
                except Exception:
                    pass
        return {}

    def estimate_episode(self, scene_count: int = 15) -> dict[str, Any]:
        """Estimate hybrid model usage for a full episode. Returns per-model breakdown."""
        stage_models = self._get_stage_model_map()

        # Estimated calls per stage
        base_req = {
            "production_package": 1,
            "outline": 1,
            "script": 6,
            "script_review": 1,
            "scene_breakdown": 6,
            "asset_package": 1,
            "metadata": 1,
            "thumbnail": 1,
            "voiceover": scene_count,
        }

        # Aggregate by model
        per_model: dict[str, dict] = {}
        for stage, count in base_req.items():
            model = stage_models.get(stage, "gemini-2.5-flash")
            entry = per_model.setdefault(model, {"requests": 0, "stages": []})
            entry["requests"] += count
            entry["stages"].append(stage)

        by_model = {}
        total_requests = 0
        for model, data in sorted(per_model.items()):
            usage = self.get_usage(model)
            limits = get_model_limits(model)
            by_model[model] = {
                "estimated_requests": data["requests"],
                "stages": data["stages"],
                "remaining_requests": usage["estimated_remaining"],
                "rpd": limits["rpd"],
                "can_run": usage["estimated_remaining"] >= data["requests"],
            }
            total_requests += data["requests"]

        all_can_run = all(v["can_run"] for v in by_model.values())

        # Build recommendation
        if all_can_run:
            rec = "Hybrid routing: sufficient quota across all models"
        else:
            failing = [m for m, v in by_model.items() if not v["can_run"]]
            rec = f"Insufficient quota for: {', '.join(failing)}"

        return {
            "total_estimated_requests": total_requests,
            "by_model": by_model,
            "can_run_full_episode": all_can_run,
            "recommendation": rec,
        }


def display_quota_status(projects_dir: str | Path) -> str:
    qm = QuotaManager(projects_dir)
    lines: list[str] = []
    lines.append("# Quota Status (per model)\n")

    models = ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-3.1-flash-lite", "gemini-2.0-flash", "qwen3:8b", "qwen3:14b"]
    for model in models:
        usage = qm.get_usage(model)
        limits = get_model_limits(model)
        if limits["rpd"] >= 999999:
            continue
        pct = (usage["used_today"] / limits["rpd"] * 100) if limits["rpd"] else 0
        bar = "█" * int(pct / 10) + "░" * (10 - int(pct / 10))
        lines.append(f"## {model}")
        lines.append(f"- Limit: {limits['rpd']} req/day")
        lines.append(f"- Used: {usage['used_today']} ({pct:.0f}%) `{bar}`")
        lines.append(f"- Remaining: {usage['estimated_remaining']}")
        lines.append(f"- Last call: {usage.get('last_call', 'never')}")
        lines.append("")

    return "\n".join(lines)
