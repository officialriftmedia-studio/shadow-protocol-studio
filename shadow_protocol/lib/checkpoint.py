"""Checkpoint manager — save/resume pipeline state per episode."""

from __future__ import annotations
import json
from pathlib import Path
from typing import Any


COMPLETED_FILE = ".checkpoint.json"


def get_completed_stages(episode_dir: str | Path) -> list[str]:
    """Return list of stage names already completed."""
    path = Path(episode_dir) / COMPLETED_FILE
    if not path.exists():
        return []
    data = json.loads(path.read_text())
    return data.get("completed", [])


def mark_stage_complete(episode_dir: str | Path, stage: str, metadata: dict | None = None) -> None:
    """Record a stage as completed with optional metadata."""
    path = Path(episode_dir) / COMPLETED_FILE
    if path.exists():
        data = json.loads(path.read_text())
    else:
        data = {"completed": [], "metadata": {}}

    if stage not in data["completed"]:
        data["completed"].append(stage)
    if metadata:
        data["metadata"][stage] = metadata

    path.write_text(json.dumps(data, indent=2) + "\n")


def is_stage_complete(episode_dir: str | Path, stage: str) -> bool:
    """Check if a stage has been completed."""
    return stage in get_completed_stages(episode_dir)


def get_stage_metadata(episode_dir: str | Path, stage: str) -> dict[str, Any] | None:
    """Return metadata for a completed stage, or None."""
    path = Path(episode_dir) / COMPLETED_FILE
    if not path.exists():
        return None
    data = json.loads(path.read_text())
    return data.get("metadata", {}).get(stage)


def clear_checkpoint(episode_dir: str | Path) -> None:
    """Remove checkpoint file (for full re-run)."""
    path = Path(episode_dir) / COMPLETED_FILE
    if path.exists():
        path.unlink()
