#!/usr/bin/env python3
"""Agent: Script Review — validates script against rules, quality, and continuity."""

from __future__ import annotations
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from agents.lib.agent_base import AgentBase, AgentError
from shadow_protocol.lib import context_manager


class ScriptReviewAgent(AgentBase):
    name = "script_review"

    def run(self) -> int:
        stage = "script_review"
        if self.is_done(stage):
            print(f"  SKIP: {stage} already completed")
            return 0

        prompt = self.load_prompt("script_review")

        script_dir = self.episode_dir / "script"
        if not script_dir.exists():
            return self.fail("SCRIPT_DIR_NOT_FOUND", "script/ directory not found")

        sections = {}
        for f in sorted(script_dir.glob("*.md")):
            if f.name != "script.md":
                sections[f.name] = f.read_text()

        if not sections:
            return self.fail("NO_SCRIPT_SECTIONS", "No script sections found")

        # Build minimal bible context — only entities mentioned in the script
        script_text = "\n".join(sections.values())
        bible_dir = self.root_dir / "bible"
        bible_data = context_manager.load_bible(bible_dir)
        bible_context = context_manager.build_context(script_text, bible_data)

        pkg = self.read_json("production_package.json")

        context = json.dumps({
            "script_sections": sections,
            "production_package": pkg,
            "bible": bible_context,
        }, indent=2)

        try:
            result = self.run_with_retry(
                lambda: self.call_llm(
                    system_prompt=prompt,
                    user_prompt=f"Review the following script sections against the production package and bible:\n\n{context}",
                    schema_rel_path="review.json",
                    response_format="json",
                ),
                label="Script review",
            )
        except AgentError as e:
            return self.fail(e.code, e.args[0])

        self.write_json("review.json", result)
        review_md = self._to_markdown(result)
        self.write_text("review.md", review_md)
        self.save_checkpoint(stage)
        print(f"  Wrote review.json and review.md")
        return 0

    def _to_markdown(self, review: dict) -> str:
        lines = ["# Script Review\n"]
        lines.append(f"**Overall:** {review.get('overall', 'UNKNOWN')}\n")
        lines.append(f"**Summary:** {review.get('summary', '')}\n\n")
        lines.append("## Section Reviews\n")
        for s in review.get("sections", []):
            lines.append(f"### {s.get('section')} — {s.get('status')}\n")
            for issue in s.get("issues", []):
                lines.append(f"- :warning: {issue}")
            for strength in s.get("strengths", []):
                lines.append(f"- :white_check_mark: {strength}")
            lines.append("")
        if review.get("recommendations"):
            lines.append("## Recommendations\n")
            for rec in review["recommendations"]:
                lines.append(f"- {rec}")
        return "\n".join(lines)


def run(input_dir: str, output_dir: str, config: dict) -> int:
    agent = ScriptReviewAgent(input_dir, config)
    return agent.run()


if __name__ == "__main__":
    _, input_dir, output_dir, config_path = sys.argv
    config = json.load(open(config_path))
    config["root"] = str(Path(config_path).parent.parent.parent)
    sys.exit(run(input_dir, output_dir, config))
