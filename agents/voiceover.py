#!/usr/bin/env python3
"""Agent: Voiceover — splits script NARRATOR text into voiceover segments per scene.

Processes scenes grouped by script section. For each section, reads the script file,
extracts NARRATOR blocks, and generates segments via LLM.
"""

from __future__ import annotations
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent))
from agents.lib.agent_base import AgentBase, AgentError
from shadow_protocol.lib.llm import llm_call, get_usage
from shadow_protocol.lib.checkpoint import is_stage_complete, mark_stage_complete
from shadow_protocol.lib.prompt_cache import get_cached, set_cache
from shadow_protocol.lib.file_utils import write_json


SCRIPT_SECTIONS = ["hook", "act1", "act2", "act3", "ending", "cliffhanger"]


class VoiceoverAgent(AgentBase):
    name = "voiceover"

    def run(self) -> int:
        stage = self.name
        if self.is_done(stage):
            print(f"  SKIP: {stage} already completed")
            return 0

        breakdown = self._load_breakdown()
        if breakdown is None:
            return self.fail("BREAKDOWN_NOT_FOUND", "scene_breakdown.json required")

        script_dir = self.episode_dir / "script"
        prompt = self.load_prompt("voiceover")

        all_segments: list[dict[str, Any]] = []
        total_calls = 0

        # Group scenes by section for section-based processing
        scenes_by_section: dict[str, list[dict[str, Any]]] = {}
        for scene in breakdown:
            sec = scene.get("section", "hook")
            scenes_by_section.setdefault(sec, []).append(scene)

        for section in SCRIPT_SECTIONS:
            section_scenes = scenes_by_section.get(section, [])
            if not section_scenes:
                continue

            script_path = script_dir / f"{section}.md"
            if not script_path.exists():
                print(f"  WARN: script/{section}.md not found, skipping")
                continue

            section_stage = f"voiceover_{section}"
            if self.is_done(section_stage):
                # Load cached segments for this section
                cached_data = self._load_cached_segments(section)
                if cached_data:
                    all_segments.extend(cached_data)
                    print(f"    SKIP: {section} already completed ({len(cached_data)} segments)")
                continue

            section_text = script_path.read_text()
            input_contents = [section_text, json.dumps(section_scenes, indent=2), prompt]

            cached_hit, cached_data = get_cached(self.episode_dir, stage, section, *input_contents)
            if cached_hit and cached_data is not None:
                print(f"    Cache hit: {section}")
                section_segments = cached_data
            else:
                user_prompt = (
                    f"Section: {section}\n\n"
                    f"## Script Text\n{section_text}\n\n"
                    f"## Scenes in this section\n{json.dumps(section_scenes, indent=2)}\n\n"
                    f"Extract NARRATOR text and split into voiceover segments per scene. "
                    f"Return a JSON object with a 'segments' array."
                )

                try:
                    result = self.run_with_retry(
                        lambda: self._call_llm_with_validation(
                            system_prompt=prompt,
                            user_prompt=user_prompt,
                        ),
                        label=f"Voiceover '{section}'",
                    )
                except AgentError as e:
                    print(f"    FAILED: {section} — {e}")
                    return self.fail(e.code, f"Voiceover section '{section}' failed: {e}")

                section_segments = result
                set_cache(self.episode_dir, stage, section, section_segments, *input_contents)

            all_segments.extend(section_segments)
            mark_stage_complete(self.episode_dir, section_stage)
            total_calls += 1
            print(f"    {section}: {len(section_segments)} segments")

        output = {"segments": all_segments}
        self.write_json("voiceover_segments.json", output)
        self.save_checkpoint(stage)
        print(f"  Wrote voiceover_segments.json ({len(all_segments)} total segments)")
        return 0

    def _load_breakdown(self) -> list[dict[str, Any]] | None:
        path = self.episode_dir / "scene_breakdown.json"
        if not path.exists():
            return None
        data = json.loads(path.read_text())
        if isinstance(data, list):
            return data
        return data.get("scenes", data.get("entries", []))

    def _load_cached_segments(self, section: str) -> list[dict[str, Any]] | None:
        segments_path = self.episode_dir / ".cache" / self.name / f"{self.name}_{section}.json"
        from shadow_protocol.lib.checkpoint import is_stage_complete
        if segments_path.exists():
            entry = json.loads(segments_path.read_text())
            return entry.get("data", [])
        return None

    def _call_llm_with_validation(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> list[dict[str, Any]]:
        text, _usage = llm_call(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.7,
            max_tokens=4096,
            response_format="json",
            stage=self.name,
        )

        parsed = json.loads(text)
        segments = parsed.get("segments", parsed.get("entries", parsed if isinstance(parsed, list) else []))

        if not isinstance(segments, list):
            raise AgentError("INVALID_LLM_OUTPUT", f"Expected array, got {type(segments).__name__}")

        schema_path = self.root_dir / "templates" / "schemas" / "voiceover_segments.json"
        from shadow_protocol.lib.schema_validator import validate_output
        errors = validate_output({"segments": segments}, schema_path)
        if errors:
            raise AgentError("SCHEMA_VALIDATION_FAILED", "; ".join(errors))

        return segments


def run(input_dir: str, output_dir: str, config: dict) -> int:
    agent = VoiceoverAgent(input_dir, config)
    return agent.run()


if __name__ == "__main__":
    _, input_dir, output_dir, config_path = sys.argv
    config = json.load(open(config_path))
    config["root"] = str(Path(config_path).parent.parent.parent)
    sys.exit(run(input_dir, output_dir, config))
