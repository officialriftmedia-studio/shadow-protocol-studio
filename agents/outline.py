#!/usr/bin/env python3
"""Agent 5: Outline — produces a 3-act structured outline."""

from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from agents.lib.agent_base import AgentBase
from shadow_protocol.lib.file_utils import write_json, read_json


class OutlineAgent(AgentBase):
    name = "outline"

    def run(self) -> int:
        pkg_path = self.input_dir / "production_package.json"
        if not pkg_path.exists():
            return self.fail("PKG_NOT_FOUND", "production_package.json is required")

        pkg = read_json(pkg_path)
        outline = self._build_outline(pkg)
        out_path = self.output_dir / "outline.json"
        write_json(out_path, outline)
        print(f"[Outline] Written to {out_path}")
        return 0

    def _build_outline(self, pkg: dict) -> dict:
        return {
            "episode_id": pkg.get("episode_id"),
            "title": pkg.get("title"),
            "acts": [
                {
                    "act": 1,
                    "name": "The Inciting Collapse",
                    "scenes": [{"scene": 1, "summary": "", "beats": []}],
                },
                {
                    "act": 2,
                    "name": "Descent Into the System",
                    "scenes": [{"scene": 2, "summary": "", "beats": []}],
                },
                {
                    "act": 3,
                    "name": "The Truth That Changes Nothing",
                    "scenes": [{"scene": 3, "summary": "", "beats": []}],
                },
            ],
        }


def run(input_dir: str, output_dir: str, config: dict) -> int:
    agent = OutlineAgent(input_dir, output_dir, config)
    return agent.run()


if __name__ == "__main__":
    import json
    _, input_dir, output_dir, config_path = sys.argv
    config = json.load(open(config_path))
    sys.exit(run(input_dir, output_dir, config))
