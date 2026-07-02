#!/usr/bin/env python3
"""Agent: Image Prompt — generates image generation prompts per scene.

Reads scene_breakdown.json (array of scene entries), generates batched
image prompts via LLM, validates against schema, saves with checkpoint.
"""

from __future__ import annotations
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent))
from agents.lib.agent_base import AgentBase, AgentError
from shadow_protocol.lib.llm import llm_call, get_usage
from shadow_protocol.lib.checkpoint import is_stage_complete
from shadow_protocol.lib.prompt_cache import get_cached, set_cache


class ImagePromptAgent(AgentBase):
    name = "image_prompt"

    def run(self) -> int:
        stage = self.name
        if self.is_done(stage):
            print(f"  SKIP: {stage} already completed")
            return 0

        breakdown = self._load_breakdown()
        if breakdown is None:
            return self.fail("BREAKDOWN_NOT_FOUND", "scene_breakdown.json required")

        prompt = self.load_prompt("image_prompt")
        context = json.dumps(breakdown, indent=2)
        input_contents = [context, prompt]

        cached_hit, cached_data = get_cached(self.episode_dir, stage, "all", *input_contents)
        if cached_hit and cached_data is not None:
            print(f"    Cache hit — using cached result")
            result = cached_data
        else:
            try:
                result = self.run_with_retry(
                    lambda: self._call_llm_with_validation(
                        system_prompt=prompt,
                        user_prompt=f"Generate image prompts for each scene:\n\n{context}",
                    ),
                    label="Image prompt generation",
                )
            except AgentError as e:
                return self.fail(e.code, e.args[0])

            set_cache(self.episode_dir, stage, "all", result, *input_contents)

        output = {"prompts": result}
        self.write_json("image_prompts.json", output)
        self.save_checkpoint(stage)
        print(f"  Wrote image_prompts.json ({len(result)} prompts)")
        return 0

    def _load_breakdown(self) -> list[dict[str, Any]] | None:
        path = self.episode_dir / "scene_breakdown.json"
        if not path.exists():
            return None
        data = json.loads(path.read_text())
        if isinstance(data, list):
            return data
        return data.get("scenes", data.get("entries", []))

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
        prompts = parsed.get("prompts", parsed.get("entries", parsed if isinstance(parsed, list) else []))

        if not isinstance(prompts, list):
            raise AgentError("INVALID_LLM_OUTPUT", f"Expected array, got {type(prompts).__name__}")

        schema_path = self.root_dir / "templates" / "schemas" / "image_prompts.json"
        from shadow_protocol.lib.schema_validator import validate_output
        errors = validate_output({"prompts": prompts}, schema_path)
        if errors:
            raise AgentError("SCHEMA_VALIDATION_FAILED", "; ".join(errors))

        return prompts


def run(input_dir: str, output_dir: str, config: dict) -> int:
    agent = ImagePromptAgent(input_dir, config)
    return agent.run()


if __name__ == "__main__":
    _, input_dir, output_dir, config_path = sys.argv
    config = json.load(open(config_path))
    config["root"] = str(Path(config_path).parent.parent.parent)
    sys.exit(run(input_dir, output_dir, config))
