#!/usr/bin/env python3
"""Agent: Outline — produces a 3-act structured outline from the production package."""

from __future__ import annotations
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from agents.lib.agent_base import AgentBase, AgentError


class OutlineAgent(AgentBase):
    name = "outline"

    def run(self) -> int:
        stage = "outline"
        if self.is_done(stage):
            print(f"  SKIP: {stage} already completed")
            return 0

        prompt = self.load_prompt("outline")
        pkg = self.read_json("production_package.json")

        context = json.dumps({"production_package": pkg}, indent=2)

        try:
            result = self.run_with_retry(
                lambda: self.call_llm(
                    system_prompt=prompt,
                    user_prompt=f"Generate a 3-act outline from this production package:\n\n{context}",
                    schema_rel_path="outline.json",
                    response_format="json",
                ),
                label="Outline generation",
            )
        except AgentError as e:
            return self.fail(e.code, e.args[0])

        self.write_json("outline.json", result)
        self.save_checkpoint(stage)
        print(f"  Wrote outline.json")
        return 0


def run(input_dir: str, output_dir: str, config: dict) -> int:
    agent = OutlineAgent(input_dir, config)
    return agent.run()


if __name__ == "__main__":
    _, input_dir, output_dir, config_path = sys.argv
    config = json.load(open(config_path))
    config["root"] = str(Path(config_path).parent.parent.parent)
    sys.exit(run(input_dir, output_dir, config))
