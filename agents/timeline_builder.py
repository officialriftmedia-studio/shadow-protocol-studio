#!/usr/bin/env python3
"""Agent: Timeline Builder — matches scene breakdown with assets into a render timeline.

Reads scene_breakdown.json, scans asset directories for matching images and
voiceover files, determines timing and motion, produces render/timeline.json.
"""

from __future__ import annotations
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent))
from agents.lib.agent_base import AgentBase, AgentError
from shadow_protocol.lib.file_utils import read_json
from shadow_protocol.lib.schema_validator import validate_output


DEFAULT_DURATION = 15.0
DEFAULT_TRANSITION = "fade"
DEFAULT_CAMERA_MOTION = "slow_zoom_in"
SUPPORTED_IMAGE_EXTS = {".png", ".jpg", ".jpeg"}
SUPPORTED_AUDIO_EXTS = {".wav", ".mp3", ".m4a", ".aac"}


class TimelineBuilderAgent(AgentBase):
    name = "timeline_builder"

    def run(self) -> int:
        stage = self.name
        if self.is_done(stage):
            print(f"  SKIP: {stage} already completed")
            return 0

        breakdown = self._load_breakdown()
        if not breakdown:
            return self.fail("BREAKDOWN_NOT_FOUND", "scene_breakdown.json required")

        manifest = self._load_asset_manifest()

        images_dir = self.episode_dir / "assets" / "images"
        voice_dir = self.episode_dir / "assets" / "voice"

        scenes = []
        for entry in breakdown:
            scene_num = entry.get("scene_number") or entry.get("scene_id") or 0
            if scene_num <= 0:
                continue

            image = self._resolve_image(manifest, images_dir, scene_num)
            voiceover = self._resolve_voiceover(manifest, voice_dir, scene_num)
            duration = self._calc_duration(voiceover, entry)
            transition = entry.get("transition", DEFAULT_TRANSITION)
            camera_motion = entry.get("camera_motion", DEFAULT_CAMERA_MOTION)

            scenes.append({
                "scene_number": scene_num,
                "image": image,
                "voiceover": voiceover,
                "duration_seconds": duration,
                "transition": transition,
                "camera_motion": camera_motion,
                "music": None,
            })

        if not scenes:
            return self.fail("NO_SCENES", "No valid scenes produced")

        timeline = {"scenes": scenes}
        self._validate(timeline)

        render_dir = self.episode_dir / "render"
        render_dir.mkdir(parents=True, exist_ok=True)
        self.write_json("render/timeline.json", timeline)

        self._write_chapters(scenes, render_dir)

        self.save_checkpoint(stage)
        print(f"  Wrote render/timeline.json ({len(scenes)} scenes)")
        print("  Wrote render/chapters.txt")
        return 0

    def _load_breakdown(self) -> list[dict[str, Any]] | None:
        path = self.episode_dir / "scene_breakdown.json"
        if not path.exists():
            return None
        data = read_json(path)
        if isinstance(data, list):
            return data
        return data.get("scenes", data.get("entries", []))

    def _load_asset_manifest(self) -> dict[str, Any]:
        path = self.episode_dir / "assets" / "manifests" / "asset_manifest.json"
        if path.exists():
            return read_json(path)
        return {}

    def _resolve_image(
        self, manifest: dict[str, Any], images_dir: Path, scene_num: int
    ) -> str:
        candidates = [
            f"img_{scene_num:04d}.png",
            f"img_{scene_num:04d}.jpg",
            f"img_{scene_num:04d}.jpeg",
        ]
        for candidate in candidates:
            full = images_dir / candidate
            if full.exists():
                return str(full.relative_to(self.episode_dir))
        return ""

    def _resolve_voiceover(
        self, manifest: dict[str, Any], voice_dir: Path, scene_num: int
    ) -> list[str]:
        prefix = f"voice_scene{scene_num:04d}_seg"
        files = sorted(voice_dir.glob(f"{prefix}*"))
        if not files:
            return []
        return [str(f.relative_to(self.episode_dir)) for f in files]

    def _calc_duration(
        self, voiceover: list[str], scene_entry: dict[str, Any]
    ) -> float:
        if scene_entry.get("duration_seconds"):
            return float(scene_entry["duration_seconds"])
        if voiceover:
            total = 0.0
            for v_path in voiceover:
                seg_path = self.episode_dir / v_path
                if seg_path.exists():
                    if seg_path.suffix == ".wav":
                        import wave
                        try:
                            with wave.open(str(seg_path), "r") as wf:
                                frames = wf.getnframes()
                                rate = wf.getframerate()
                                if rate > 0:
                                    total += frames / rate
                        except Exception:
                            total += 2.0
                    else:
                        total += 2.0
            if total > 0:
                return round(max(total, 1.0), 1)
        return DEFAULT_DURATION

    def _validate(self, timeline: dict[str, Any]) -> None:
        schema_path = self.root_dir / "templates" / "schemas" / "timeline.json"
        errors = validate_output(timeline, schema_path)
        if errors:
            raise AgentError("SCHEMA_VALIDATION_FAILED", "; ".join(errors))

    def _write_chapters(self, scenes: list[dict], render_dir: Path) -> None:
        lines = []
        cumulative = 0.0
        for i, scene in enumerate(scenes):
            minutes = int(cumulative // 60)
            seconds = int(cumulative % 60)
            label = scene.get("title", f"Scene {scene['scene_number']}")
            lines.append(f"{minutes:02d}:{seconds:02d} {label}")
            cumulative += scene["duration_seconds"]
        chapters_path = render_dir / "chapters.txt"
        chapters_path.write_text("\n".join(lines) + "\n")


def run(input_dir: str, output_dir: str, config: dict) -> int:
    agent = TimelineBuilderAgent(input_dir, config)
    return agent.run()


if __name__ == "__main__":
    _, input_dir, output_dir, config_path = sys.argv
    config = json.load(open(config_path))
    config["root"] = str(Path(config_path).parent.parent.parent)
    sys.exit(run(input_dir, output_dir, config))
