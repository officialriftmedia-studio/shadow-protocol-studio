#!/usr/bin/env python3
"""Agent: Publish Package Builder — collects final assets into upload_package/.

Reads render output, YouTube metadata, and thumbnail to build a publishable
package at publish/upload_package/ with publish_manifest.json.
"""

from __future__ import annotations
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent))
from agents.lib.agent_base import AgentBase, AgentError
from shadow_protocol.lib.file_utils import read_json, write_json
from shadow_protocol.lib.schema_validator import validate_output


ASSET_DEFINITIONS: list[dict[str, Any]] = [
    {
        "name": "final_video.mp4",
        "source": "render/final_video.mp4",
        "required": True,
    },
    {
        "name": "title.txt",
        "source": None,  # generated from metadata
        "required": True,
    },
    {
        "name": "description.txt",
        "source": None,
        "required": True,
    },
    {
        "name": "tags.txt",
        "source": None,
        "required": True,
    },
    {
        "name": "chapters.txt",
        "source": "render/chapters.txt",
        "required": False,
    },
    {
        "name": "metadata.json",
        "source": None,
        "required": True,
    },
    {
        "name": "thumbnail.png",
        "source": "assets/images/thumbnail.png",
        "required": False,
    },
]


class PublishPackageBuilderAgent(AgentBase):
    name = "publish_package_builder"

    def run(self) -> int:
        stage = self.name
        if self.is_done(stage):
            print(f"  SKIP: {stage} already completed")
            return 0

        youtube_meta = self._load_youtube_metadata()
        if not youtube_meta:
            return self.fail("META_NOT_FOUND", "youtube_metadata.json required")

        publish_dir = self.episode_dir / "publish"
        package_dir = publish_dir / "upload_package"
        package_dir.mkdir(parents=True, exist_ok=True)

        warnings: list[str] = []
        assets: list[dict[str, Any]] = []

        for asset_def in ASSET_DEFINITIONS:
            name = asset_def["name"]
            source_rel = asset_def["source"]
            required = asset_def["required"]

            if source_rel:
                src = self.episode_dir / source_rel
                if src.exists():
                    dst = package_dir / name
                    shutil.copy2(str(src), str(dst))
                    size = dst.stat().st_size
                    checksum = self._sha256(dst)
                    assets.append({
                        "name": name,
                        "source": source_rel,
                        "size_bytes": size,
                        "exists": True,
                        "checksum": checksum,
                    })
                elif required:
                    warnings.append(f"Required asset missing: {source_rel}")
                    assets.append({
                        "name": name,
                        "source": source_rel,
                        "size_bytes": 0,
                        "exists": False,
                    })
                else:
                    assets.append({
                        "name": name,
                        "source": source_rel,
                        "size_bytes": 0,
                        "exists": False,
                    })
            else:
                self._generate_derived_asset(name, youtube_meta, package_dir, assets)

        meta_out = {
            "title": youtube_meta.get("title", ""),
            "description": youtube_meta.get("description", ""),
            "tags": youtube_meta.get("tags", []),
            "visibility": youtube_meta.get("visibility", "unlisted"),
            "language": youtube_meta.get("language", "en"),
            "category": youtube_meta.get("category", "Entertainment"),
        }

        (package_dir / "metadata.json").write_text(json.dumps(meta_out, indent=2) + "\n")
        assets.append({
            "name": "metadata.json",
            "source": "generated",
            "size_bytes": (package_dir / "metadata.json").stat().st_size,
            "exists": True,
        })

        manifest = {
            "case_id": self.episode_dir.name,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "package_path": str(package_dir.relative_to(self.episode_dir)),
            "assets": assets,
            "metadata": meta_out,
            "warnings": warnings,
        }

        self._validate(manifest)
        write_json(publish_dir / "publish_manifest.json", manifest)

        self.save_checkpoint(stage)
        print(f"  Wrote publish/publish_manifest.json ({len(assets)} assets)")
        if warnings:
            for w in warnings:
                print(f"  WARNING: {w}")
        return 0

    def _load_youtube_metadata(self) -> dict[str, Any] | None:
        path = self.episode_dir / "youtube_metadata.json"
        if path.exists():
            return read_json(path)
        return None

    def _generate_derived_asset(
        self,
        name: str,
        meta: dict[str, Any],
        package_dir: Path,
        assets: list[dict[str, Any]],
    ) -> None:
        if name == "title.txt":
            content = meta.get("title", "Untitled Episode")
            dst = package_dir / "title.txt"
            dst.write_text(content + "\n")
        elif name == "description.txt":
            content = meta.get("description", "")
            dst = package_dir / "description.txt"
            dst.write_text(content + "\n")
        elif name == "tags.txt":
            tags = meta.get("tags", [])
            dst = package_dir / "tags.txt"
            dst.write_text("\n".join(tags) + "\n")
        else:
            return

        assets.append({
            "name": name,
            "source": "generated",
            "size_bytes": dst.stat().st_size,
            "exists": True,
        })

    def _sha256(self, path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def _validate(self, manifest: dict[str, Any]) -> None:
        schema_path = self.root_dir / "templates" / "schemas" / "publish_manifest.json"
        errors = validate_output(manifest, schema_path)
        if errors:
            raise AgentError("SCHEMA_VALIDATION_FAILED", "; ".join(errors))


def run(input_dir: str, output_dir: str, config: dict) -> int:
    agent = PublishPackageBuilderAgent(input_dir, config)
    return agent.run()


if __name__ == "__main__":
    _, input_dir, output_dir, config_path = sys.argv
    config = json.load(open(config_path))
    config["root"] = str(Path(config_path).parent.parent.parent)
    sys.exit(run(input_dir, output_dir, config))
