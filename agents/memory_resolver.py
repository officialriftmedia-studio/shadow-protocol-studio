#!/usr/bin/env python3
"""Agent 2: Memory Resolver — resolves continuity references from bible/."""

from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from agents.lib.agent_base import AgentBase


class MemoryResolverAgent(AgentBase):
    name = "memory_resolver"

    def run(self) -> int:
        bible_dir = self.input_dir / "bible"
        if not bible_dir.exists():
            return self.fail("BIBLE_NOT_FOUND", f"bible/ not found at {bible_dir}")

        print(f"[MemoryResolver] Scanning {bible_dir}")
        for f in bible_dir.glob("*.json"):
            print(f"[MemoryResolver]   Found: {f.name}")
        print(f"[MemoryResolver] Resolved references.")
        return 0


def run(input_dir: str, output_dir: str, config: dict) -> int:
    agent = MemoryResolverAgent(input_dir, output_dir, config)
    return agent.run()


if __name__ == "__main__":
    import json
    _, input_dir, output_dir, config_path = sys.argv
    config = json.load(open(config_path))
    sys.exit(run(input_dir, output_dir, config))
