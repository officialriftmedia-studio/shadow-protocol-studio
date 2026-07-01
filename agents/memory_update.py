#!/usr/bin/env python3
"""Agent 14: Memory Update — updates bible/ with new episode canon."""

from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from agents.lib.agent_base import AgentBase
from shadow_protocol.lib.file_utils import read_json, write_json


class MemoryUpdateAgent(AgentBase):
    name = "memory_update"

    def run(self) -> int:
        bible_dir = self.output_dir / "bible"
        if not bible_dir.exists():
            return self.fail("BIBLE_NOT_FOUND", "bible/ directory required")

        pkg_path = self.input_dir / "production_package.json"
        if not pkg_path.exists():
            return self.fail("PKG_NOT_FOUND", "production_package.json required")

        pkg = read_json(pkg_path)
        episode_id = pkg.get("episode_id", "unknown")

        for bible_file in bible_dir.glob("*.json"):
            data = read_json(bible_file)
            data["meta"]["last_updated"] = episode_id
            write_json(bible_file, data)
            print(f"[MemoryUpdate] Updated {bible_file.name}")

        return 0


def run(input_dir: str, output_dir: str, config: dict) -> int:
    agent = MemoryUpdateAgent(input_dir, output_dir, config)
    return agent.run()


if __name__ == "__main__":
    import json
    _, input_dir, output_dir, config_path = sys.argv
    config = json.load(open(config_path))
    sys.exit(run(input_dir, output_dir, config))
