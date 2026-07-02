#!/usr/bin/env python3
"""Agent: Production Package — converts blueprint into structured production metadata."""

from __future__ import annotations
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from agents.lib.agent_base import AgentBase, AgentError
from shadow_protocol.lib import context_manager


class ProductionPackageAgent(AgentBase):
    name = "production_package"

    def run(self) -> int:
        stage = "production_package"
        if self.is_done(stage):
            print(f"  SKIP: {stage} already completed")
            return 0

        prompt = self.load_prompt("production_package")
        bible_dir = self.root_dir / "bible"
        bible_data = context_manager.load_bible(bible_dir)
        bible_summary = context_manager.get_bible_summary(bible_data)
        blueprint = self.read_json("blueprint.json")

        context = json.dumps({"blueprint": blueprint, "bible": bible_summary}, indent=2)

        try:
            result = self.run_with_retry(
                lambda: self.call_llm(
                    system_prompt=prompt,
                    user_prompt=f"Generate a production package from this blueprint and bible context:\n\n{context}",
                    schema_rel_path="production_package.json",
                    response_format="json",
                ),
                label="Production Package generation",
            )
        except AgentError as e:
            return self.fail(e.code, e.args[0])

        self.write_json("production_package.json", result)
        self.save_checkpoint(stage)
        print(f"  Wrote production_package.json")
        return 0


def run(input_dir: str, output_dir: str, config: dict) -> int:
    agent = ProductionPackageAgent(input_dir, config)
    return agent.run()


if __name__ == "__main__":
    _, input_dir, output_dir, config_path = sys.argv
    config = json.load(open(config_path))
    config["root"] = str(Path(config_path).parent.parent.parent)
    sys.exit(run(input_dir, output_dir, config))
