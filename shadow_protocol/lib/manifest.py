"""Asset manifest management for generated media assets.

Each episode has a single manifest file stored at:
  projects/{case_id}/assets/manifests/asset_manifest.json

The manifest tracks all generated assets (images, voice, video) with metadata
including provider, prompt, checksum, and file path.
"""

from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MANIFEST_VERSION = "1.0.0"


def create_manifest(case_id: str) -> dict[str, Any]:
    return {
        "case_id": case_id,
        "assets": [],
        "generated_at": "",
        "version": MANIFEST_VERSION,
    }


def load_manifest(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return create_manifest("")


def save_manifest(path: str | Path, manifest: dict[str, Any]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")


def add_asset(manifest: dict[str, Any], asset_data: dict[str, Any]) -> str:
    assets = manifest.setdefault("assets", [])
    asset_id = asset_data.get("asset_id", f"asset_{len(assets):04d}")
    asset_data["asset_id"] = asset_id
    asset_data.setdefault("created_at", datetime.now(timezone.utc).isoformat())
    assets.append(asset_data)
    return asset_id


def update_asset(
    manifest: dict[str, Any], asset_id: str, updates: dict[str, Any]
) -> bool:
    for asset in manifest.get("assets", []):
        if asset.get("asset_id") == asset_id:
            asset.update(updates)
            return True
    return False


def finalize_manifest(manifest: dict[str, Any]) -> None:
    manifest["generated_at"] = datetime.now(timezone.utc).isoformat()


def get_assets_by_type(
    manifest: dict[str, Any], asset_type: str
) -> list[dict[str, Any]]:
    return [a for a in manifest.get("assets", []) if a.get("type") == asset_type]


def get_asset_count(manifest: dict[str, Any]) -> int:
    return len(manifest.get("assets", []))


__all__ = [
    "create_manifest",
    "load_manifest",
    "save_manifest",
    "add_asset",
    "update_asset",
    "finalize_manifest",
    "get_assets_by_type",
    "get_asset_count",
]
