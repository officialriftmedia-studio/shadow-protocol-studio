#!/usr/bin/env python3
"""Agent: Voice Generator — generates voiceover audio assets.

Reads voiceover_segments.json, generates placeholder WAV files using the
configured voice provider, updates the asset manifest with provider cache.
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


class VoiceGeneratorAgent(AgentBase):
    name = "voice_generator"

    def run(self) -> int:
        stage = self.name
        if self.is_done(stage):
            print(f"  SKIP: {stage} already completed")
            return 0

        segments_path = self.episode_dir / "voiceover_segments.json"
        if not segments_path.exists():
            return self.fail("SEGMENTS_NOT_FOUND", "voiceover_segments.json required")

        segments_data = read_json(segments_path)
        segments = segments_data.get("segments", segments_data.get("entries", []))
        if not isinstance(segments, list) or not segments:
            return self.fail("NO_SEGMENTS", "No voiceover segments found")

        provider_name = os.getenv("VOICE_PROVIDER", "google_tts")
        model = os.getenv("VOICE_MODEL", "wavesynth")

        provider_config = self._load_provider_config().get("providers", {}).get(provider_name, {})
        provider = resolve_provider(provider_name, provider_config)

        voice_dir = self.episode_dir / "assets" / "voice"
        manifest_path = self.episode_dir / "assets" / "manifests" / "asset_manifest.json"

        manifest = load_manifest(manifest_path)
        if not manifest.get("case_id"):
            manifest["case_id"] = self.episode_dir.name

        generated = 0
        cached = 0
        failed = 0

        for segment in segments:
            scene_id = segment.get("scene_id", 0)
            seg_idx = segment.get("segment_index", 0)
            prompt_key = f"voice_scene{scene_id}_seg{seg_idx}"

            cached_hit, cached_data = get_provider_cache(
                self.episode_dir, provider_name, model, prompt_key
            )
            if cached_hit and cached_data is not None:
                print(f"    Cache hit: scene {scene_id} seg {seg_idx}")
                add_asset(manifest, cached_data)
                cached += 1
                continue

            result = provider.generate(segment, output_dir=voice_dir, model=model)

            if not result.success:
                print(f"    FAILED: scene {scene_id} seg {seg_idx} — {result.error}")
                failed += 1
                continue

            asset_data = {
                "asset_id": f"voice_scene{scene_id:04d}_seg{seg_idx:04d}",
                "type": "voice",
                "source_stage": self.name,
                "provider": provider_name,
                "model": model,
                "prompt": segment.get("text", "")[:200],
                "file_path": str(result.asset_path.relative_to(self.episode_dir)),
                "mime_type": result.mime_type,
                "status": "completed",
                "metadata": result.metadata,
            }

            add_asset(manifest, asset_data)
            set_provider_cache(
                self.episode_dir, provider_name, model, prompt_key, asset_data
            )
            generated += 1
            print(f"    Generated: scene {scene_id} seg {seg_idx} -> {result.asset_path.name}")

        finalize_manifest(manifest)
        save_manifest(manifest_path, manifest)

        self.save_checkpoint(stage)
        print(f"  Generated {generated} voice segments, {cached} cached, {failed} failed")
        print(f"  Manifest: {manifest_path}")
        return 0 if failed == 0 else 1

    def _load_provider_config(self) -> dict[str, Any]:
        path = self.root_dir / "config" / "providers.json"
        if path.exists():
            return read_json(path)
        return {}


def run(input_dir: str, output_dir: str, config: dict) -> int:
    agent = VoiceGeneratorAgent(input_dir, config)
    return agent.run()


if __name__ == "__main__":
    _, input_dir, output_dir, config_path = sys.argv
    config = json.load(open(config_path))
    config["root"] = str(Path(config_path).parent.parent.parent)
    sys.exit(run(input_dir, output_dir, config))
