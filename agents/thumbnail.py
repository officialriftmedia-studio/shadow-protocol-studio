#!/usr/bin/env python3
"""Agent 12: Thumbnail — designs the YouTube thumbnail prompt."""

from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from agents.lib.agent_base import AgentBase
from shadow_protocol.lib.file_utils import write_text, read_json


class ThumbnailAgent(AgentBase):
    name = "thumbnail"

    def run(self) -> int:
        breakdown_path = self.input_dir / "scene_breakdown.json"
        if not breakdown_path.exists():
            return self.fail("BREAKDOWN_NOT_FOUND", "scene_breakdown.json required")

        breakdown = read_json(breakdown_path)
        prompt = self._build_prompt(breakdown)
        out_path = self.output_dir / "thumbnail_prompt.txt"
        write_text(out_path, prompt)
        print(f"[Thumbnail] Written to {out_path}")
        return 0

    def _build_prompt(self, breakdown: dict) -> str:
        return (
            "Cinematic YouTube thumbnail for a psychological thriller documentary. "
            "Dark and moody atmosphere, high contrast lighting, mysterious figure in shadows. "
            "Style: Sicario meets True Detective. 16:9 aspect ratio. "
            "[LLM will generate the final prompt]"
        )


def run(input_dir: str, output_dir: str, config: dict) -> int:
    agent = ThumbnailAgent(input_dir, output_dir, config)
    return agent.run()


if __name__ == "__main__":
    import json
    _, input_dir, output_dir, config_path = sys.argv
    config = json.load(open(config_path))
    sys.exit(run(input_dir, output_dir, config))
