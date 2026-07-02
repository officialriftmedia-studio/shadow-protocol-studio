#!/usr/bin/env python3
"""Agent: Script — writes script sections (hook, acts, ending, cliffhanger)."""

from __future__ import annotations
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from agents.lib.agent_base import AgentBase, AgentError


SCRIPT_SECTIONS = [
    "hook",
    "act1",
    "act2",
    "act3",
    "ending",
    "cliffhanger",
]

SECTION_DESCRIPTIONS = {
    "hook": "The cold open (60-90 seconds). A compelling fragment from later in the story that grabs attention, then 'three days earlier...'",
    "act1": "Act 1: The Inciting Collapse. Establish normal world, first crack in reality, inciting incident.",
    "act2": "Act 2: Descent Into the System. Investigation, hidden layers, false leads, midpoint revelation.",
    "act3": "Act 3: The Truth That Changes Nothing. Final confrontation, mystery solved, larger mystery revealed.",
    "ending": "The closing sequence, final voiceover, thematic resolution.",
    "cliffhanger": "Post-credits or final image that sets up the larger mystery across episodes.",
}


class ScriptAgent(AgentBase):
    name = "script"

    def run(self) -> int:
        outline = self.read_json("outline.json")
        prompt = self.load_prompt("script")
        script_dir = self.episode_dir / "script"
        script_dir.mkdir(parents=True, exist_ok=True)

        context = json.dumps({"outline": outline}, indent=2)

        all_sections_done = all(
            (script_dir / f"{s}.md").exists() or self.is_done(f"script_{s}")
            for s in SCRIPT_SECTIONS
        )
        if all_sections_done:
            print(f"  SKIP: all script sections already generated")
            combined = self._combine_sections(script_dir)
            self.write_text("script/script.md", combined)
            return 0

        for section in SCRIPT_SECTIONS:
            section_stage = f"script_{section}"
            if self.is_done(section_stage):
                print(f"  SKIP: {section} already completed")
                continue

            section_prompt = (
                f"{prompt}\n\n"
                f"## Current Section\n"
                f"Write the **{section}** section.\n"
                f"{SECTION_DESCRIPTIONS[section]}\n\n"
                f"## Context\n{context}"
            )

            already_written = []
            for s in SCRIPT_SECTIONS:
                p = script_dir / f"{s}.md"
                if p.exists():
                    already_written.append(f"\n### {s}\n{p.read_text()[:200]}...")

            if already_written:
                section_prompt += "\n\n## Already Written Sections\n" + "\n".join(already_written)

            try:
                result = self.run_with_retry(
                    lambda sp=section_prompt: self.call_llm(
                        system_prompt=sp,
                        user_prompt=f"Write the {section} section of the script. Use the MARKDOWN FORMAT with NARRATOR/VISUAL/AUDIO/DIALOGUE markers.",
                        response_format=None,
                        max_tokens=4096,
                    ),
                    label=f"Script section '{section}'",
                )
            except AgentError as e:
                return self.fail(e.code, e.args[0])

            text_content, _usage = result

            self.write_text(f"script/{section}.md", text_content)
            self.save_checkpoint(section_stage)
            print(f"  Wrote script/{section}.md")

        combined = self._combine_sections(script_dir)
        self.write_text("script/script.md", combined)
        print(f"  Wrote script/script.md (combined)")
        return 0

    def _combine_sections(self, script_dir: Path) -> str:
        parts = ["# Script — The Ghost in the Machine\n"]
        for section in SCRIPT_SECTIONS:
            path = script_dir / f"{section}.md"
            if path.exists():
                parts.append(path.read_text())
                parts.append("\n\n---\n\n")
        return "".join(parts)


def run(input_dir: str, output_dir: str, config: dict) -> int:
    agent = ScriptAgent(input_dir, config)
    return agent.run()


if __name__ == "__main__":
    _, input_dir, output_dir, config_path = sys.argv
    config = json.load(open(config_path))
    config["root"] = str(Path(config_path).parent.parent.parent)
    sys.exit(run(input_dir, output_dir, config))
