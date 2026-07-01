#!/usr/bin/env python3
"""Agent 11: Voiceover — splits script into voiceover segments."""

from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from agents.lib.agent_base import AgentBase
from shadow_protocol.lib.file_utils import write_json, read_text, read_json


class VoiceoverAgent(AgentBase):
    name = "voiceover"

    def run(self) -> int:
        sections = sorted(self.input_dir.glob("script_section_*.md"))
        breakdown_path = self.input_dir / "scene_breakdown.json"
        if not sections or not breakdown_path.exists():
            return self.fail("MISSING_INPUT", "script sections + scene_breakdown.json required")

        breakdown = read_json(breakdown_path)
        segments = self._build_segments(sections, breakdown)
        out_path = self.output_dir / "voiceover_segments.json"
        write_json(out_path, segments)
        print(f"[Voiceover] Written to {out_path}")
        return 0

    def _build_segments(self, sections: list[Path], breakdown: dict) -> dict:
        return {
            "segments": [
                {"scene_id": s["scene_id"], "text": "", "voice_id": "", "duration_seconds": 30}
                for s in breakdown.get("scenes", [])
            ]
        }


def run(input_dir: str, output_dir: str, config: dict) -> int:
    agent = VoiceoverAgent(input_dir, output_dir, config)
    return agent.run()


if __name__ == "__main__":
    import json
    _, input_dir, output_dir, config_path = sys.argv
    config = json.load(open(config_path))
    sys.exit(run(input_dir, output_dir, config))
