#!/usr/bin/env python3
"""Agent: Scene Breakdown — decomposes each script section into producible scenes.

Processes script sections individually (hook, act1-3, ending, cliffhanger).
For each section: loads inputs → checks prompt cache → calls LLM →
validates → saves partial → merges into final scene_breakdown.json.
If a section fails, completed sections are preserved for resume.
"""

from __future__ import annotations
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent))
from agents.lib.agent_base import AgentBase, AgentError
from shadow_protocol.lib.file_utils import write_json
from shadow_protocol.lib.checkpoint import mark_stage_complete, is_stage_complete, get_completed_stages
from shadow_protocol.lib.llm import llm_call, get_usage, reset_usage
from shadow_protocol.lib.prompt_cache import get_cached, set_cache, invalidate
from shadow_protocol.lib.schema_validator import validate_output
from shadow_protocol.lib import context_manager


SCRIPT_SECTIONS = ["hook", "act1", "act2", "act3", "ending", "cliffhanger"]

# Maps script sections to the outline act they correspond to
SECTION_TO_ACT = {
    "hook": 1,
    "act1": 1,
    "act2": 2,
    "act3": 3,
    "ending": 3,
    "cliffhanger": 3,
}

PARTIAL_PREFIX = ".scene_breakdown_partial_"
FINAL_OUTPUT = "scene_breakdown.json"


class SceneBreakdownAgent(AgentBase):
    name = "scene_breakdown"

    def run(self) -> int:
        stage = self.name
        episode_dir = self.episode_dir
        script_dir = episode_dir / "script"

        # ── Validate required inputs exist ────────────────────────
        missing = self._check_inputs(script_dir)
        if missing:
            return self.fail("MISSING_INPUTS", f"Required files not found: {', '.join(missing)}")

        outline = self.read_json("outline.json")

        # ── Determine which sections to process ───────────────────
        completed = get_completed_stages(episode_dir)
        sections_to_run = [s for s in SCRIPT_SECTIONS if f"scene_breakdown_{s}" not in completed]

        if not sections_to_run:
            print(f"  All sections already completed. Merging final output...")
            self._merge_final(stage)
            print(f"  Wrote {FINAL_OUTPUT}")
            return 0

        all_partials: list[dict[str, Any]] = []
        # Load any previously completed partials
        for ps in episode_dir.glob(f"{PARTIAL_PREFIX}*.json"):
            data = json.loads(ps.read_text())
            all_partials.extend(data if isinstance(data, list) else data.get("scenes", []))

        schema_path = self.root_dir / "templates" / "schemas" / "scene_breakdown.json"

        # Track cumulative scene numbering
        next_scene_number = max((s.get("scene_number", 0) for s in all_partials), default=0) + 1

        # ── Process each section ───────────────────────────────────
        for section in sections_to_run:
            section_stage = f"scene_breakdown_{section}"
            print(f"\n  Section: {section}")

            # Load section-specific inputs
            section_text = self._read_section(script_dir, section)
            section_beats = self._get_section_beats(outline, section)
            bible_dir = self.root_dir / "bible"
            bible_data = context_manager.load_bible(bible_dir)
            bible_context = context_manager.build_context(section_text, bible_data)

            input_contents = [section_text, json.dumps(section_beats, sort_keys=True), json.dumps(bible_context, sort_keys=True)]

            # Check prompt cache
            cached_hit, cached_data = get_cached(episode_dir, stage, section, *input_contents)
            if cached_hit and cached_data is not None:
                print(f"    Cache hit — using cached result")
                scenes = cached_data
            else:
                # Build prompt and call LLM
                prompt = self.load_prompt("scene_breakdown")

                user_prompt = (
                    f"Section: {section}\n\n"
                    f"## Script Section\n{section_text}\n\n"
                    f"## Relevant Outline Beats\n{json.dumps(section_beats, indent=2)}\n\n"
                    f"## Bible Context\n{json.dumps(bible_context, indent=2)}\n\n"
                    f"Generate scene entries starting from scene_number {next_scene_number}. "
                    f"Each scene must include all required fields."
                )

                try:
                    result = self.run_with_retry(
                        lambda: self._llm_call_with_validation(
                            system_prompt=prompt,
                            user_prompt=user_prompt,
                            schema_path=schema_path,
                        ),
                        label=f"Scene breakdown '{section}'",
                    )
                except AgentError as e:
                    print(f"    FAILED: {section} — {e}")
                    self._save_partial(all_partials, stage)
                    return self.fail(e.code, f"Section '{section}' failed: {e}")

                scenes = result if isinstance(result, list) else result.get("scenes", result)
                set_cache(episode_dir, stage, section, scenes, *input_contents)

            # Assign scene numbers sequentially
            for i, scene in enumerate(scenes):
                scene["scene_number"] = next_scene_number + i
                scene["section"] = section
            next_scene_number += len(scenes)

            all_partials.extend(scenes)

            # Save partial and checkpoint
            self._save_partial(all_partials, stage, section)
            mark_stage_complete(episode_dir, section_stage)
            usage = get_usage()
            print(f"    CHECKPOINT: {section_stage} — {len(scenes)} scenes, {usage.log_line()}")

        # ── Merge all partials into final output ───────────────────
        self._merge_final(stage)
        print(f"  Wrote {FINAL_OUTPUT} ({len(all_partials)} total scenes)")
        return 0

    # ── Input helpers ─────────────────────────────────────────────

    def _check_inputs(self, script_dir: Path) -> list[str]:
        missing = []
        for s in SCRIPT_SECTIONS:
            if not (script_dir / f"{s}.md").exists():
                missing.append(f"script/{s}.md")
        for req in ["outline.json"]:
            if not (self.episode_dir / req).exists():
                missing.append(req)
        return missing

    def _read_section(self, script_dir: Path, section: str) -> str:
        path = script_dir / f"{section}.md"
        if not path.exists():
            raise AgentError("SECTION_NOT_FOUND", f"{path} not found")
        return path.read_text()

    def _get_section_beats(self, outline: dict, section: str) -> list[dict[str, Any]]:
        """Extract outline beats relevant to this script section."""
        target_act = SECTION_TO_ACT.get(section, 1)
        for act in outline.get("acts", []):
            if act.get("act") == target_act:
                scenes = act.get("scenes", [])
                all_beats = []
                for sc in scenes:
                    for beat in sc.get("beats", []):
                        beat["scene_summary"] = sc.get("summary", "")
                        all_beats.append(beat)
                return all_beats
        return []

    # ── LLM call with validation ──────────────────────────────────

    def _llm_call_with_validation(
        self,
        system_prompt: str,
        user_prompt: str,
        schema_path: Path,
    ) -> list[dict[str, Any]]:
        text, _usage = llm_call(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.7,
            max_tokens=8192,
            response_format="json",
            stage=self.name,
        )

        text = text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[-1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()

        parsed = json.loads(text)

        # Handle both array and {"scenes": [...]} wrappers
        if isinstance(parsed, dict):
            scenes = parsed.get("scenes", parsed.get("entries", []))
        else:
            scenes = parsed

        if not isinstance(scenes, list):
            raise AgentError(
                "INVALID_LLM_OUTPUT",
                f"Expected list of scenes, got {type(scenes).__name__}",
            )

        errors = validate_output(scenes, schema_path)
        if errors:
            raise AgentError(
                "SCHEMA_VALIDATION_FAILED",
                f"scene_breakdown.json: {'; '.join(errors)}",
            )

        return scenes

    # ── Partial save and merge ────────────────────────────────────

    def _save_partial(
        self,
        scenes: list[dict[str, Any]],
        stage: str,
        section: str | None = None,
    ) -> None:
        """Save partial results. If section is given, saves to a section-specific file
        for resume support. Also always writes a merged partial to the final output path."""
        if section:
            partial_path = self.episode_dir / f"{PARTIAL_PREFIX}{section}.json"
            section_scenes = [s for s in scenes if s.get("section") == section]
            write_json(partial_path, section_scenes)

        # Always write merged partial to final output path
        write_json(self.episode_dir / FINAL_OUTPUT, scenes)

    def _merge_final(self, stage: str) -> None:
        """Merge all partial files into final scene_breakdown.json."""
        all_scenes: list[dict[str, Any]] = []
        for ps in sorted(self.episode_dir.glob(f"{PARTIAL_PREFIX}*.json")):
            data = json.loads(ps.read_text())
            if isinstance(data, list):
                all_scenes.extend(data)

        if not all_scenes:
            raise AgentError("NO_PARTIALS", "No partial scene breakdowns found to merge")

        write_json(self.episode_dir / FINAL_OUTPUT, all_scenes)
        usage = get_usage()
        mark_stage_complete(self.episode_dir, stage, {
            "tokens": usage.total_tokens,
            "cost": round(usage.cost_usd, 6),
            "calls": usage.calls,
            "sections_completed": len(SCRIPT_SECTIONS),
            "total_scenes": len(all_scenes),
        })


def run(input_dir: str, output_dir: str, config: dict) -> int:
    agent = SceneBreakdownAgent(input_dir, config)
    return agent.run()


if __name__ == "__main__":
    _, input_dir, output_dir, config_path = sys.argv
    config = json.load(open(config_path))
    config["root"] = str(Path(config_path).parent.parent.parent)
    sys.exit(run(input_dir, output_dir, config))
