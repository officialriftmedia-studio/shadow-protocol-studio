#!/usr/bin/env python3
"""Agent 4: Production Package — converts story idea into structured production metadata."""

from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from agents.lib.agent_base import AgentBase
from shadow_protocol.lib.file_utils import write_json, read_text


class ProductionPackageAgent(AgentBase):
    name = "production_package"

    def run(self) -> int:
        story_path = self.input_dir / "story_idea.md"
        if not story_path.exists():
            return self.fail("STORY_IDEA_NOT_FOUND", "story_idea.md is required")

        story = read_text(story_path)
        pkg = self._build_package(story)
        out_path = self.output_dir / "production_package.json"
        write_json(out_path, pkg)
        print(f"[ProductionPackage] Written to {out_path}")
        return 0

    def _build_package(self, story: str) -> dict:
        return {
            "episode_id": self.input_dir.name,
            "title": None,
            "logline": None,
            "estimated_duration_seconds": 600,
            "scenes": 5,
            "tone": "psychological thriller",
            "source_story": story,
        }


def run(input_dir: str, output_dir: str, config: dict) -> int:
    agent = ProductionPackageAgent(input_dir, output_dir, config)
    return agent.run()


if __name__ == "__main__":
    import json
    _, input_dir, output_dir, config_path = sys.argv
    config = json.load(open(config_path))
    sys.exit(run(input_dir, output_dir, config))
