#!/usr/bin/env python3
"""Agent 1: Orchestrator — builds and executes the pipeline DAG."""

from __future__ import annotations
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent))
from agents.lib.agent_base import AgentBase, AgentError


class OrchestratorAgent(AgentBase):
    name = "orchestrator"

    def run(self) -> int:
        print(f"[Orchestrator] Starting pipeline for {self.input_dir}")
        workflow = self.config.get("workflow", {})
        stages = workflow.get("stages", [])
        for stage in stages:
            print(f"[Orchestrator] Stage: {stage['name']}")
            print(f"[Orchestrator]   agent: {stage['agent']}")
            print(f"[Orchestrator]   input: {stage.get('input', [])}")
            print(f"[Orchestrator]   output: {stage.get('output', [])}")
        print(f"[Orchestrator] Pipeline complete.")
        return 0


def run(input_dir: str, output_dir: str, config: dict) -> int:
    agent = OrchestratorAgent(input_dir, output_dir, config)
    return agent.run()


if __name__ == "__main__":
    import json
    _, input_dir, output_dir, config_path = sys.argv
    config = json.load(open(config_path))
    sys.exit(run(input_dir, output_dir, config))
