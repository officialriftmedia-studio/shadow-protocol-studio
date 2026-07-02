"""Prompt caching — cache LLM responses keyed by input hash.

Avoids redundant LLM calls when inputs haven't changed (e.g., on resume or
partial regeneration). Each cache entry stores the sha256 hash of concatenated
input file contents and the cached response data.
"""

from __future__ import annotations
import hashlib
import json
from pathlib import Path
from typing import Any


CACHE_DIR = ".cache"


def _cache_dir(episode_dir: str | Path) -> Path:
    return Path(episode_dir) / CACHE_DIR


def _cache_key(stage: str, section: str) -> str:
    return f"{stage}_{section}"


def _input_hash(*inputs: str) -> str:
    """Compute sha256 of concatenated input strings."""
    h = hashlib.sha256()
    for s in inputs:
        h.update(s.encode("utf-8"))
    return h.hexdigest()


def get_cached(
    episode_dir: str | Path,
    stage: str,
    section: str,
    *input_contents: str,
) -> tuple[bool, list[dict[str, Any]] | None]:
    """Check cache. Returns (hit, data).

    Args:
        episode_dir: Episode directory (where .cache/ lives)
        stage: Agent stage name
        section: Section identifier
        input_contents: File contents to hash for cache invalidation

    Returns:
        (True, cached_data) on hit, (False, None) on miss.
    """
    cache_dir = _cache_dir(episode_dir) / stage
    key = _cache_key(stage, section)
    cache_path = cache_dir / f"{key}.json"

    if not cache_path.exists():
        return False, None

    current_hash = _input_hash(*input_contents)

    try:
        entry = json.loads(cache_path.read_text())
        if entry.get("hash") == current_hash:
            return True, entry.get("data")
    except (json.JSONDecodeError, KeyError):
        pass

    return False, None


def set_cache(
    episode_dir: str | Path,
    stage: str,
    section: str,
    data: list[dict[str, Any]],
    *input_contents: str,
) -> None:
    """Store response in cache.

    Args:
        episode_dir: Episode directory
        stage: Agent stage name
        section: Section identifier
        data: Cached response data (list of scene dicts)
        input_contents: File contents to hash for invalidation
    """
    cache_dir = _cache_dir(episode_dir) / stage
    cache_dir.mkdir(parents=True, exist_ok=True)

    key = _cache_key(stage, section)
    cache_path = cache_dir / f"{key}.json"

    current_hash = _input_hash(*input_contents)

    entry = {
        "hash": current_hash,
        "stage": stage,
        "section": section,
        "data": data,
    }

    cache_path.write_text(json.dumps(entry, indent=2) + "\n")


def invalidate(episode_dir: str | Path, stage: str, section: str | None = None) -> None:
    """Clear cache entries.

    Args:
        episode_dir: Episode directory
        stage: Agent stage name
        section: If given, clear only that section. If None, clear all sections for stage.
    """
    cache_dir = _cache_dir(episode_dir) / stage
    if not cache_dir.exists():
        return

    if section:
        key = _cache_key(stage, section)
        path = cache_dir / f"{key}.json"
        if path.exists():
            path.unlink()
    else:
        import shutil
        shutil.rmtree(cache_dir)
