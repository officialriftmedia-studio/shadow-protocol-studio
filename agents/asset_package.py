#!/usr/bin/env python3
"""Agent: Asset Package — generates image/video prompts, metadata, and thumbnail in one LLM call.

Replaces: image_prompt, video_prompt, metadata, thumbnail (4 calls → 1 call).
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


class AssetPackageAgent(AgentBase):
    name = "asset_package"

    def run(self) -> int:
        stage = self.name
        if self.is_done(stage):
            print(f"  SKIP: {stage} already completed")
            return 0

        breakdown = self._load_breakdown()
        if breakdown is None:
            return self.fail("BREAKDOWN_NOT_FOUND", "scene_breakdown.json required")

        pkg_path = self.episode_dir / "production_package.json"
        if not pkg_path.exists():
            return self.fail("PKG_NOT_FOUND", "production_package.json required")

        pkg = json.loads(pkg_path.read_text())
        prompt = self.load_prompt("asset_package")

        context = json.dumps({"production_package": pkg, "scenes": breakdown}, indent=2)
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
                        user_prompt=f"Generate all assets and metadata for this episode:\n\n{context}",
                    ),
                    label="Asset package generation",
                )
            except AgentError as e:
                return self.fail(e.code, e.args[0])

            set_cache(self.episode_dir, stage, "all", result, *input_contents)

        # Write all four output files from the single LLM response
        self.write_json("image_prompts.json", {"prompts": result.get("image_prompts", [])})
        self.write_json("video_prompts.json", {"prompts": result.get("video_prompts", [])})
        self.write_json("youtube_metadata.json", result.get("youtube_metadata", {}))
        self.write_json("thumbnail_prompt.json", result.get("thumbnail_prompt", {}))

        thumb_text = result.get("thumbnail_prompt", {}).get("prompt", "")
        self.write_text("thumbnail_prompt.txt", thumb_text)

        self.save_checkpoint(stage)
        image_count = len(result.get("image_prompts", []))
        video_count = len(result.get("video_prompts", []))
        print(f"  Wrote asset outputs ({image_count} image prompts, {video_count} video prompts, metadata, thumbnail)")
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
    ) -> dict[str, Any]:
        text, _usage = llm_call(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.7,
            max_tokens=8192,
            response_format="json",
            stage=self.name,
        )

        parsed = json.loads(text)

        schema_path = self.root_dir / "templates" / "schemas" / "asset_package.json"
        from shadow_protocol.lib.schema_validator import validate_output
        errors = validate_output(parsed, schema_path)
        if errors:
            raise AgentError("SCHEMA_VALIDATION_FAILED", "; ".join(errors))

        return parsed


def run(input_dir: str, output_dir: str, config: dict) -> int:
    agent = AssetPackageAgent(input_dir, config)
    return agent.run()


if __name__ == "__main__":
    _, input_dir, output_dir, config_path = sys.argv
    config = json.load(open(config_path))
    config["root"] = str(Path(config_path).parent.parent.parent)
    sys.exit(run(input_dir, output_dir, config))
