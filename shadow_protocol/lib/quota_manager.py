"""Quota Manager — track daily provider quota usage and estimate remaining capacity."""

from __future__ import annotations
import json
import os
from datetime import datetime, date, timezone
from pathlib import Path
from typing import Any


STATE_FILE = ".quota_state.json"


class QuotaManager:
    def __init__(self, projects_dir: str | Path):
        self.projects_dir = Path(projects_dir)

    # ── Provider quota definitions ──────────────────────────────────

    _PROVIDER_LIMITS: dict[str, dict[str, int]] = {
        "gemini": {"daily_requests": 20, "daily_input_tokens": 100000},
        "openai": {"daily_requests": 500, "daily_input_tokens": 1000000},
        "anthropic": {"daily_requests": 500, "daily_input_tokens": 1000000},
        "ollama": {"daily_requests": 999999, "daily_input_tokens": 999999999},
    }

    @classmethod
    def get_provider_limits(cls, provider: str) -> dict[str, int]:
        return cls._PROVIDER_LIMITS.get(provider, {"daily_requests": 0, "daily_input_tokens": 0})

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

    def reset_if_new_day(self, provider: str) -> bool:
        state = self.load_state()
        today = date.today().isoformat()
        provider_state = state.setdefault(provider, {})
        if provider_state.get("date") != today:
            provider_state["date"] = today
            provider_state["requests_used"] = 0
            provider_state["input_tokens_used"] = 0
            self.save_state(state)
            return True
        return False

    # ── Tracking ───────────────────────────────────────────────────

    def record_call(self, provider: str, input_tokens: int = 0) -> None:
        self.reset_if_new_day(provider)
        state = self.load_state()
        ps = state.setdefault(provider, {})
        ps["requests_used"] = ps.get("requests_used", 0) + 1
        ps["input_tokens_used"] = ps.get("input_tokens_used", 0) + input_tokens
        ps["last_call"] = datetime.now(timezone.utc).isoformat()
        self.save_state(state)

    def get_usage(self, provider: str) -> dict[str, Any]:
        self.reset_if_new_day(provider)
        state = self.load_state()
        ps = state.get(provider, {})
        limits = self.get_provider_limits(provider)

        used_req = ps.get("requests_used", 0)
        used_tokens = ps.get("input_tokens_used", 0)

        return {
            "provider": provider,
            "date": ps.get("date", date.today().isoformat()),
            "daily_requests": limits["daily_requests"],
            "used_today": used_req,
            "estimated_remaining": max(0, limits["daily_requests"] - used_req),
            "input_tokens_used": used_tokens,
            "input_tokens_remaining": max(0, limits["daily_input_tokens"] - used_tokens),
            "last_call": ps.get("last_call"),
        }

    # ── Estimate for a new episode ─────────────────────────────────

    def estimate_episode(self, provider: str, scene_count: int = 15) -> dict[str, Any]:
        limits = self.get_provider_limits(provider)
        usage = self.get_usage(provider)

        per_scene_req = 2
        base_req = {
            "production_package": 1,
            "outline": 1,
            "script": 6,
            "script_review": 1,
            "scene_breakdown": 6,
            "image_prompt": 1,
            "video_prompt": 1,
            "metadata": 1,
            "thumbnail": 1,
            "voiceover": scene_count,
        }

        estimated_requests = sum(base_req.values())
        estimated_input_tokens = estimated_requests * 3000
        estimated_output_tokens = estimated_requests * 1500

        can_run = (
            usage["estimated_remaining"] >= estimated_requests
            and usage["input_tokens_remaining"] >= estimated_input_tokens
        )

        return {
            "provider": provider,
            "estimated_requests": estimated_requests,
            "estimated_input_tokens": estimated_input_tokens,
            "estimated_output_tokens": estimated_output_tokens,
            "estimated_tokens": estimated_input_tokens + estimated_output_tokens,
            "remaining_requests": usage["estimated_remaining"],
            "remaining_input_tokens": usage["input_tokens_remaining"],
            "can_run_full_episode": can_run,
            "recommendation": (
                f"{provider} has enough quota" if can_run
                else f"Insufficient quota. Need ~{estimated_requests} requests, have {usage['estimated_remaining']}"
            ),
        }


def display_quota_status(projects_dir: str | Path) -> str:
    qm = QuotaManager(projects_dir)
    lines: list[str] = []
    lines.append("# Quota Status\n")

    for provider in ["gemini", "openai", "anthropic", "ollama"]:
        usage = qm.get_usage(provider)
        limits = QuotaManager.get_provider_limits(provider)
        if limits["daily_requests"] == 0:
            continue
        pct = (usage["used_today"] / limits["daily_requests"] * 100) if limits["daily_requests"] else 0
        bar = "█" * int(pct / 10) + "░" * (10 - int(pct / 10))
        lines.append(f"## {provider}")
        lines.append(f"- Limit: {limits['daily_requests']} req/day")
        lines.append(f"- Used: {usage['used_today']} ({pct:.0f}%) `{bar}`")
        lines.append(f"- Remaining: {usage['estimated_remaining']}")
        lines.append(f"- Last call: {usage.get('last_call', 'never')}")
        lines.append("")

    return "\n".join(lines)
