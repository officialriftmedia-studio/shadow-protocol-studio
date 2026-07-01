#!/usr/bin/env python3
"""Agent 9: Image Prompt — generates image generation prompts per scene."""

from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from agents.lib.agent_base import AgentBase
from shadow_protocol.lib.file_utils import write_json, read_json


class ImagePromptAgent(AgentBase):
    name = "image_prompt"

    def run(self) -> int:
        breakdown_path = self.input_dir / "scene_breakdown.json"
        if not breakdown_path.exists():
            return self.fail("BREAKDOWN_NOT_FOUND", "scene_breakdown.json required")

        breakdown = read_json(breakdown_path)
        prompts = self._generate_prompts(breakdown)
        out_path = self.output_dir / "image_prompts.json"
        write_json(out_path, prompts)
        print(f"[ImagePrompt] Written to {out_path}")
        return 0

    def _generate_prompts(self, breakdown: dict) -> dict:
        return {
            "prompts": [
                {
                    "scene_id": s["scene_id"],
                    "prompt": "",
                    "negative_prompt": "",
                    "style": "cinematic",
                    "aspect_ratio": "16:9",
                }
                for s in breakdown.get("scenes", [])
            ]
        }


def run(input_dir: str, output_dir: str, config: dict) -> int:
    agent = ImagePromptAgent(input_dir, output_dir, config)
    return agent.run()


if __name__ == "__main__":
    import json
    _, input_dir, output_dir, config_path = sys.argv
    config = json.load(open(config_path))
    sys.exit(run(input_dir, output_dir, config))
