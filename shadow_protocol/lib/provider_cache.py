"""Provider cache — cache media generation results by provider+model+prompt hash.

Stores cached metadata at:
  projects/{case_id}/assets/.provider_cache/{hash}.json

Each entry stores the sha256 hash of provider:model:prompt_key as lookup.
"""

from __future__ import annotations
import hashlib
import json
from pathlib import Path
from typing import Any

PROVIDER_CACHE_DIR = ".provider_cache"


def _cache_dir(episode_dir: str | Path) -> Path:
    return Path(episode_dir) / "assets" / PROVIDER_CACHE_DIR


def _cache_key(provider: str, model: str, prompt_key: str) -> str:
    raw = f"{provider}:{model}:{prompt_key}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def get_cached(
    episode_dir: str | Path,
    provider: str,
    model: str,
    prompt_key: str,
) -> tuple[bool, dict[str, Any] | None]:
    cache_dir = _cache_dir(episode_dir)
    key = _cache_key(provider, model, prompt_key)
    cache_path = cache_dir / f"{key}.json"

    if not cache_path.exists():
        return False, None

    try:
        entry = json.loads(cache_path.read_text())
        if entry.get("hash") == key:
            return True, entry.get("data")
    except (json.JSONDecodeError, KeyError):
        pass

    return False, None


def set_cache(
    episode_dir: str | Path,
    provider: str,
    model: str,
    prompt_key: str,
    data: dict[str, Any],
) -> None:
    cache_dir = _cache_dir(episode_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)

    key = _cache_key(provider, model, prompt_key)
    cache_path = cache_dir / f"{key}.json"

    entry = {
        "hash": key,
        "provider": provider,
        "model": model,
        "data": data,
    }
    cache_path.write_text(json.dumps(entry, indent=2) + "\n")


def invalidate(
    episode_dir: str | Path,
    provider: str | None = None,
    model: str | None = None,
) -> None:
    cache_dir = _cache_dir(episode_dir)
    if not cache_dir.exists():
        return

    if provider is None and model is None:
        import shutil

        shutil.rmtree(cache_dir)
        return

    for f in list(cache_dir.iterdir()):
        if f.suffix != ".json":
            continue
        try:
            entry = json.loads(f.read_text())
            if provider and entry.get("provider") != provider:
                continue
            if model and entry.get("model") != model:
                continue
            f.unlink()
        except (json.JSONDecodeError, KeyError):
            continue


def clear_all(episode_dir: str | Path) -> None:
    invalidate(episode_dir)


def get_cache_metrics(episode_dir: str | Path) -> dict[str, Any]:
    cache_dir = _cache_dir(episode_dir)
    if not cache_dir.exists():
        return {"total_entries": 0, "providers": {}}

    entries = list(cache_dir.glob("*.json"))
    provider_counts: dict[str, int] = {}
    for f in entries:
        try:
            entry = json.loads(f.read_text())
            p = entry.get("provider", "unknown")
            provider_counts[p] = provider_counts.get(p, 0) + 1
        except (json.JSONDecodeError, KeyError):
            pass

    return {
        "total_entries": len(entries),
        "providers": provider_counts,
    }


__all__ = [
    "get_cached",
    "set_cache",
    "invalidate",
    "clear_all",
    "get_cache_metrics",
]
