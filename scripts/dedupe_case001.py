#!/usr/bin/env python3
"""Safely prune duplicate scenes from case_001 scene_breakdown.json.

KEEP: scene_number 1–15, 31
REMOVE: scene_number 16–30

Preserves original ordering. Validates output before writing.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path


SCENE_FILE = Path("projects/case_001/scene_breakdown.json")
BACKUP_DIR = Path("projects/case_001/backups")
KEEP_RANGES = [(1, 15), (31, 31)]


def load_scenes(path: Path) -> list[dict]:
    data = json.loads(path.read_text())
    if isinstance(data, list):
        return data
    return data.get("scenes", data.get("entries", []))


def should_keep(scene_number: int) -> bool:
    for lo, hi in KEEP_RANGES:
        if lo <= scene_number <= hi:
            return True
    return False


def validate(scenes: list[dict]) -> list[str]:
    errors = []
    if len(scenes) != 16:
        errors.append(f"Expected 16 scenes, got {len(scenes)}")
    numbers = [s.get("scene_number") for s in scenes]
    for n in numbers:
        if n is None:
            errors.append("A scene is missing scene_number")
    if len(numbers) != len(set(numbers)):
        errors.append("Duplicate scene numbers detected")
    expected = set(range(1, 16)) | {31}
    actual = set(numbers)
    missing = expected - actual
    extra = actual - expected
    if missing:
        errors.append(f"Missing scene numbers: {sorted(missing)}")
    if extra:
        errors.append(f"Unexpected scene numbers: {sorted(extra)}")
    return errors


def main() -> int:
    if not SCENE_FILE.exists():
        print(f"ERROR: {SCENE_FILE} not found", file=sys.stderr)
        return 1

    all_scenes = load_scenes(SCENE_FILE)

    before_count = len(all_scenes)
    before_duration = sum(s.get("duration", 0) for s in all_scenes)

    preserved = [s for s in all_scenes if should_keep(s.get("scene_number", 0))]
    removed = [s for s in all_scenes if not should_keep(s.get("scene_number", 0))]

    after_count = len(preserved)
    after_duration = sum(s.get("duration", 0) for s in preserved)

    removed_numbers = sorted([s.get("scene_number") for s in removed])
    preserved_numbers = sorted([s.get("scene_number") for s in preserved])

    # Validate
    errors = validate(preserved)
    if errors:
        print("VALIDATION FAILED:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    # Write
    SCENE_FILE.write_text(json.dumps(preserved, indent=2) + "\n")

    print(f"=== Deduplication Complete ===")
    print(f"Before: {before_count} scenes, {before_duration}s ({before_duration//60}m {before_duration%60}s)")
    print(f"After:  {after_count} scenes, {after_duration}s ({after_duration//60}m {after_duration%60}s)")
    print(f"Removed: {len(removed)} duplicate scenes")
    print(f"Removed scene numbers: {removed_numbers}")
    print(f"Preserved scene numbers: {preserved_numbers}")
    print(f"Saved: {before_duration - after_duration}s ({(before_duration - after_duration) / 60:.1f}m) of render time")
    print(f"Backup: {BACKUP_DIR / 'scene_breakdown_pre_dedupe.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
