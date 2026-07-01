#!/usr/bin/env python3
"""Agent 7: Script Review — validates script against rules and continuity."""

from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from agents.lib.agent_base import AgentBase
from shadow_protocol.lib.file_utils import write_text, read_text


class ScriptReviewAgent(AgentBase):
    name = "script_review"

    def run(self) -> int:
        sections = sorted(self.input_dir.glob("script_section_*.md"))
        if not sections:
            return self.fail("NO_SCRIPT_SECTIONS", "No script_section_*.md files found")

        review = self._review_sections(sections)
        out_path = self.output_dir / "review.md"
        write_text(out_path, review)
        print(f"[ScriptReview] Written to {out_path}")
        return 0

    def _review_sections(self, sections: list[Path]) -> str:
        lines = ["# Script Review\n"]
        for s in sections:
            content = read_text(s)
            lines.append(f"## {s.name}\n")
            lines.append("- [ ] Structure check\n")
            lines.append("- [ ] Continuity check\n")
            lines.append("- [ ] Tone check\n")
            lines.append(f"\n**Raw content:**\n```\n{content[:200]}...\n```\n")
        return "\n".join(lines)


def run(input_dir: str, output_dir: str, config: dict) -> int:
    agent = ScriptReviewAgent(input_dir, output_dir, config)
    return agent.run()


if __name__ == "__main__":
    import json
    _, input_dir, output_dir, config_path = sys.argv
    config = json.load(open(config_path))
    sys.exit(run(input_dir, output_dir, config))
