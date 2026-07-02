#!/usr/bin/env python3
"""Agent: Image Generator — generates image assets from image prompts.

Reads image_prompts.json, generates placeholder images using the configured
image provider, updates the asset manifest with provider cache integration.
"""

from __future__ import annotations
import json
import os
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent))
from agents.lib.agent_base import AgentBase
from shadow_protocol.lib.providers import resolve_provider
from shadow_protocol.lib.manifest import (
    load_manifest,
    save_manifest,
    add_asset,
    finalize_manifest,
)
from shadow_protocol.lib.provider_cache import (
    get_cached as get_provider_cache,
    set_cache as set_provider_cache,
)
from shadow_protocol.lib.file_utils import read_json


class ImageGeneratorAgent(AgentBase):
    name = "image_generator"

    def run(self) -> int:
        stage = self.name
        if self.is_done(stage):
            print(f"  SKIP: {stage} already completed")
            return 0

        prompts_path = self.episode_dir / "image_prompts.json"
        if not prompts_path.exists():
            return self.fail("PROMPTS_NOT_FOUND", "image_prompts.json required")

        prompts_data = read_json(prompts_path)
        prompts = prompts_data.get("prompts", prompts_data.get("entries", []))
        if not isinstance(prompts, list) or not prompts:
            return self.fail("NO_PROMPTS", "No image prompts found")

        provider_name = os.getenv("IMAGE_PROVIDER", "google_imagen")
        model = os.getenv("IMAGE_MODEL", "imagen-3.0")

        provider_config = self._load_provider_config().get("providers", {}).get(provider_name, {})
        provider = resolve_provider(provider_name, provider_config)

        images_dir = self.episode_dir / "assets" / "images"
        manifest_path = self.episode_dir / "assets" / "manifests" / "asset_manifest.json"

        manifest = load_manifest(manifest_path)
        if not manifest.get("case_id"):
            manifest["case_id"] = self.episode_dir.name

        generated = 0
        cached = 0
        failed = 0

        for entry in prompts:
            scene_id = entry.get("scene_id", 0)
            prompt_text = entry.get("prompt", "")
            prompt_key = f"img_{scene_id}"

            cached_hit, cached_data = get_provider_cache(
                self.episode_dir, provider_name, model, prompt_key
            )
            if cached_hit and cached_data is not None:
                print(f"    Cache hit: scene {scene_id}")
                add_asset(manifest, cached_data)
                cached += 1
                continue

            result = provider.generate(entry, output_dir=images_dir, model=model)

            if not result.success:
                print(f"    FAILED: scene {scene_id} — {result.error}")
                failed += 1
                continue

            asset_data = {
                "asset_id": f"img_{scene_id:04d}",
                "type": "image",
                "source_stage": self.name,
                "provider": provider_name,
                "model": model,
                "prompt": prompt_text[:200],
                "file_path": str(result.asset_path.relative_to(self.episode_dir)),
                "mime_type": result.mime_type,
                "status": "completed",
                "metadata": result.metadata,
            }

            add_asset(manifest, asset_data)
            set_provider_cache(self.episode_dir, provider_name, model, prompt_key, asset_data)
            generated += 1
            print(f"    Generated: scene {scene_id} -> {result.asset_path.name}")

        finalize_manifest(manifest)
        save_manifest(manifest_path, manifest)

        self.save_checkpoint(stage)
        print(f"  Generated {generated} images, {cached} cached, {failed} failed")
        print(f"  Manifest: {manifest_path}")
        return 0 if failed == 0 else 1

    def _load_provider_config(self) -> dict[str, Any]:
        path = self.root_dir / "config" / "providers.json"
        if path.exists():
            return read_json(path)
        return {}


def run(input_dir: str, output_dir: str, config: dict) -> int:
    agent = ImageGeneratorAgent(input_dir, config)
    return agent.run()


if __name__ == "__main__":
    _, input_dir, output_dir, config_path = sys.argv
    config = json.load(open(config_path))
    config["root"] = str(Path(config_path).parent.parent.parent)
    sys.exit(run(input_dir, output_dir, config))
