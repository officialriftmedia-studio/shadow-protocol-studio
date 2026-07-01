#!/usr/bin/env python3
"""Agent 13: Metadata — generates YouTube metadata (title, description, tags)."""

from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from agents.lib.agent_base import AgentBase
from shadow_protocol.lib.file_utils import write_json, read_json


class MetadataAgent(AgentBase):
    name = "metadata"

    def run(self) -> int:
        breakdown_path = self.input_dir / "scene_breakdown.json"
        pkg_path = self.input_dir / "production_package.json"
        if not breakdown_path.exists() or not pkg_path.exists():
            return self.fail("MISSING_INPUT", "scene_breakdown.json and production_package.json required")

        breakdown = read_json(breakdown_path)
        pkg = read_json(pkg_path)
        meta = self._build_metadata(pkg, breakdown)
        out_path = self.output_dir / "youtube_metadata.json"
        write_json(out_path, meta)
        print(f"[Metadata] Written to {out_path}")
        return 0

    def _build_metadata(self, pkg: dict, breakdown: dict) -> dict:
        return {
            "title": pkg.get("title", ""),
            "description": "",
            "tags": ["ShadowProtocol", "psychological thriller", "conspiracy", "documentary"],
            "category": "Entertainment",
            "language": "en",
            "visibility": "unlisted",
        }


def run(input_dir: str, output_dir: str, config: dict) -> int:
    agent = MetadataAgent(input_dir, output_dir, config)
    return agent.run()


if __name__ == "__main__":
    import json
    _, input_dir, output_dir, config_path = sys.argv
    config = json.load(open(config_path))
    sys.exit(run(input_dir, output_dir, config))
