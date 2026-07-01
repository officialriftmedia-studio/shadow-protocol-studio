#!/usr/bin/env python3
"""Agent 8: Scene Breakdown — decomposes script into producible scenes."""

from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from agents.lib.agent_base import AgentBase
from shadow_protocol.lib.file_utils import write_json, read_text


class SceneBreakdownAgent(AgentBase):
    name = "scene_breakdown"

    def run(self) -> int:
        sections = sorted(self.input_dir.glob("script_section_*.md"))
        if not sections:
            return self.fail("NO_SCRIPT_SECTIONS", "script_section_*.md files required")

        breakdown = self._build_breakdown(sections)
        out_path = self.output_dir / "scene_breakdown.json"
        write_json(out_path, breakdown)
        print(f"[SceneBreakdown] Written to {out_path}")
        return 0

    def _build_breakdown(self, sections: list[Path]) -> dict:
        scenes = []
        for i, s in enumerate(sections, 1):
            scenes.append({
                "scene_id": i,
                "source_file": s.name,
                "description": "",
                "location": "",
                "characters": [],
                "duration_seconds": 120,
                "visual_style": "",
                "audio_style": "",
            })
        return {"scenes": scenes}


def run(input_dir: str, output_dir: str, config: dict) -> int:
    agent = SceneBreakdownAgent(input_dir, output_dir, config)
    return agent.run()


if __name__ == "__main__":
    import json
    _, input_dir, output_dir, config_path = sys.argv
    config = json.load(open(config_path))
    sys.exit(run(input_dir, output_dir, config))
