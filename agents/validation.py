#!/usr/bin/env python3
"""Agent 15: Validation — validates all episode outputs against schemas."""

from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from agents.lib.agent_base import AgentBase
from shadow_protocol.lib.schema_validator import validate_output_file
from shadow_protocol.lib.file_utils import write_json


class ValidationAgent(AgentBase):
    name = "validation"

    SCHEMA_MAP = {
        "production_package.json": "templates/schemas/production_package.json",
        "outline.json": "templates/schemas/outline.json",
        "scene_breakdown.json": "templates/schemas/scene_breakdown.json",
        "image_prompts.json": "templates/schemas/image_prompts.json",
        "video_prompts.json": "templates/schemas/video_prompts.json",
        "voiceover_segments.json": "templates/schemas/voiceover_segments.json",
        "youtube_metadata.json": "templates/schemas/youtube_metadata.json",
    }

    def run(self) -> int:
        results = {}
        all_pass = True

        for filename, schema_rel in self.SCHEMA_MAP.items():
            data_path = self.input_dir / filename
            schema_path = self.config.get("root", ".") / schema_rel

            if not data_path.exists():
                results[filename] = {"status": "SKIPPED", "errors": ["File not found"]}
                continue

            errors = validate_output_file(data_path, schema_path)
            if errors:
                results[filename] = {"status": "FAIL", "errors": errors}
                all_pass = False
            else:
                results[filename] = {"status": "PASS", "errors": []}

        report = {
            "episode": self.input_dir.name,
            "timestamp": None,
            "overall": "PASS" if all_pass else "FAIL",
            "results": results,
        }

        out_path = self.output_dir / "validation_report.json"
        write_json(out_path, report)
        print(f"[Validation] Report written to {out_path}")
        return 0 if all_pass else 1


def run(input_dir: str, output_dir: str, config: dict) -> int:
    agent = ValidationAgent(input_dir, output_dir, config)
    return agent.run()


if __name__ == "__main__":
    import json
    _, input_dir, output_dir, config_path = sys.argv
    config = json.load(open(config_path))
    sys.exit(run(input_dir, output_dir, config))
