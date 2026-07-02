#!/usr/bin/env python3
"""Agent: Render Builder — generates FFmpeg commands from timeline.

Reads render/timeline.json, generates per-scene FFmpeg commands with zoompan
camera motions, voiceover overlay, and transitions. Produces
render/ffmpeg_commands.json for execution by render_executor.py.

No FFmpeg execution happens here.
"""

from __future__ import annotations
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent))
from agents.lib.agent_base import AgentBase, AgentError
from shadow_protocol.lib.file_utils import read_json, write_json
from shadow_protocol.lib.schema_validator import validate_output

FPS = 25
RESOLUTION = "1920x1080"
FADE_DURATION = 1.0  # seconds

CAMERA_MOTION_FILTERS: dict[str, str] = {
    "slow_zoom_in": (
        "zoompan=z='min(zoom+0.001,1.5)'"
        ":x='iw/2-(iw/zoom/2)'"
        ":y='ih/2-(ih/zoom/2)'"
        ":d={frames}:s={res}:fps={fps}"
    ),
    "slow_zoom_out": (
        "zoompan=z='max(zoom-0.001,1.0)'"
        ":x='iw/2-(iw/zoom/2)'"
        ":y='ih/2-(ih/zoom/2)'"
        ":d={frames}:s={res}:fps={fps}"
    ),
    "pan_left": (
        "zoompan=z=1.3"
        ":x='iw/2-(iw/zoom/2)+200*({frames}-1-on)/({frames}-1)'"
        ":y='ih/2-(ih/zoom/2)'"
        ":d={frames}:s={res}:fps={fps}"
    ),
    "pan_right": (
        "zoompan=z=1.3"
        ":x='iw/2-(iw/zoom/2)-200*({frames}-1-on)/({frames}-1)'"
        ":y='ih/2-(ih/zoom/2)'"
        ":d={frames}:s={res}:fps={fps}"
    ),
    "static": (
        "zoompan=z=1"
        ":x='iw/2-(iw/zoom/2)'"
        ":y='ih/2-(ih/zoom/2)'"
        ":d={frames}:s={res}:fps={fps}"
    ),
}


class RenderBuilderAgent(AgentBase):
    name = "render_builder"

    def run(self) -> int:
        stage = self.name
        if self.is_done(stage):
            print(f"  SKIP: {stage} already completed")
            return 0

        timeline_path = self.episode_dir / "render" / "timeline.json"
        if not timeline_path.exists():
            return self.fail("TIMELINE_NOT_FOUND", "render/timeline.json required")

        timeline = read_json(timeline_path)
        scenes_in = timeline.get("scenes", [])
        if not scenes_in:
            return self.fail("NO_SCENES", "Timeline has no scenes")

        render_dir = self.episode_dir / "render"
        temp_dir = render_dir / "temp"
        temp_dir.mkdir(parents=True, exist_ok=True)

        ffmpeg_scenes = []
        for scene in scenes_in:
            scene_num = scene["scene_number"]
            duration = scene["duration_seconds"]
            motion = scene["camera_motion"]
            transition = scene.get("transition", "fade")

            scene_commands = self._build_scene_commands(
                scene, duration, motion, transition, temp_dir
            )
            ffmpeg_scenes.append({
                "scene_number": scene_num,
                "commands": scene_commands,
            })

        concat_cmd = self._build_concat_command(scenes_in, temp_dir, render_dir)
        final_output = "render/final_video.mp4"

        ffmpeg_cmds = {
            "scenes": ffmpeg_scenes,
            "concat_command": concat_cmd,
            "final_output": final_output,
        }

        self._validate(ffmpeg_cmds)
        write_json(self.episode_dir / "render" / "ffmpeg_commands.json", ffmpeg_cmds)

        self.save_checkpoint(stage)
        print(f"  Wrote render/ffmpeg_commands.json ({len(ffmpeg_scenes)} scenes)")
        return 0

    def _build_scene_commands(
        self,
        scene: dict[str, Any],
        duration: float,
        motion: str,
        transition: str,
        temp_dir: Path,
    ) -> list[dict[str, Any]]:
        commands: list[dict[str, Any]] = []
        scene_num = scene["scene_number"]
        image_rel = scene["image"]
        voiceover_rel = scene.get("voiceover", [])
        if isinstance(voiceover_rel, str):
            voiceover_rel = [voiceover_rel]

        scene_temp = temp_dir / f"scene_{scene_num:04d}"
        scene_temp.mkdir(parents=True, exist_ok=True)

        image_path = self.episode_dir / image_rel

        merged_audio = scene_temp / "audio_merged.wav"
        voice_files = [self.episode_dir / v for v in voiceover_rel if v]

        if len(voice_files) > 1:
            merge_cmd = self._build_audio_merge_command(voice_files, merged_audio)
            commands.append({
                "type": "merge_audio",
                "description": f"Scene {scene_num}: merge {len(voice_files)} voice segments",
                "command": merge_cmd,
            })
            audio_input = merged_audio
        elif len(voice_files) == 1:
            audio_input = voice_files[0]
        else:
            audio_input = None

        video_out = scene_temp / "video.mp4"
        frames = int(duration * FPS)
        filter_expr = self._build_filter(motion, frames, duration, transition)

        video_cmd = self._build_video_command(
            image_path, audio_input, filter_expr, duration, video_out
        )
        commands.append({
            "type": "generate_video",
            "description": f"Scene {scene_num}: {motion}, {duration}s, {transition}",
            "command": video_cmd,
        })

        return commands

    def _build_filter(
        self, motion: str, frames: int, duration: float, transition: str
    ) -> str:
        tmpl = CAMERA_MOTION_FILTERS.get(motion, CAMERA_MOTION_FILTERS["static"])
        zoompan = tmpl.format(frames=frames, res=RESOLUTION, fps=FPS)

        fade_parts = [zoompan]
        if transition == "fade":
            fade_parts.append(f"fade=t=in:st=0:d={FADE_DURATION}")
            fade_parts.append(
                f"fade=t=out:st={duration - FADE_DURATION}:d={FADE_DURATION}"
            )

        return ",".join(fade_parts)

    def _build_audio_merge_command(
        self, audio_files: list[Path], output: Path
    ) -> list[str]:
        concat_file = output.parent / "audio_concat.txt"
        lines = [f"file '{f.resolve()}'" for f in audio_files]
        concat_file.write_text("\n".join(lines) + "\n")

        return [
            "ffmpeg",
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_file.resolve()),
            "-c", "copy",
            str(output.resolve()),
        ]

    def _build_video_command(
        self,
        image_path: Path,
        audio_path: Path | None,
        filter_expr: str,
        duration: float,
        output: Path,
    ) -> list[str]:
        cmd = ["ffmpeg", "-y", "-loop", "1", "-i", str(image_path.resolve())]
        if audio_path and audio_path.exists():
            cmd.extend(["-i", str(audio_path.resolve())])
            map_flags = ["-map", "0:v", "-map", "1:a", "-shortest"]
        else:
            map_flags = []
        cmd.extend([
            "-vf", filter_expr,
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-t", str(duration),
            *map_flags,
            "-c:a", "aac",
            "-b:a", "128k",
            str(output.resolve()),
        ])
        return cmd

    def _build_concat_command(
        self, scenes: list[dict], temp_dir: Path, render_dir: Path
    ) -> dict[str, Any]:
        concat_file = temp_dir / "concat_list.txt"
        lines = []
        for scene in scenes:
            scene_num = scene["scene_number"]
            video_path = temp_dir / f"scene_{scene_num:04d}" / "video.mp4"
            if video_path.exists():
                lines.append(f"file '{video_path.resolve()}'")
        concat_file.write_text("\n".join(lines) + "\n")

        final_out = render_dir / "final_video.mp4"

        command = [
            "ffmpeg",
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_file.resolve()),
            "-c", "copy",
            str(final_out.resolve()),
        ]
        return {
            "type": "concat",
            "description": "Concatenate all scene videos into final video",
            "command": command,
        }

    def _validate(self, cmds: dict[str, Any]) -> None:
        schema_path = self.root_dir / "templates" / "schemas" / "ffmpeg_commands.json"
        errors = validate_output(cmds, schema_path)
        if errors:
            raise AgentError("SCHEMA_VALIDATION_FAILED", "; ".join(errors))


def run(input_dir: str, output_dir: str, config: dict) -> int:
    agent = RenderBuilderAgent(input_dir, config)
    return agent.run()


if __name__ == "__main__":
    _, input_dir, output_dir, config_path = sys.argv
    config = json.load(open(config_path))
    config["root"] = str(Path(config_path).parent.parent.parent)
    sys.exit(run(input_dir, output_dir, config))
