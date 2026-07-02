#!/usr/bin/env python3
"""Agent: Render Executor — executes FFmpeg commands to produce final video.

Reads render/ffmpeg_commands.json, runs FFmpeg per scene in parallel,
concatenates results, and writes render/final_video.mp4 with
render/render_manifest.json.
"""

from __future__ import annotations
import json
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent))
from agents.lib.agent_base import AgentBase, AgentError
from shadow_protocol.lib.file_utils import read_json, write_json
from shadow_protocol.lib.schema_validator import validate_output

MAX_WORKERS = 4


class RenderExecutorAgent(AgentBase):
    name = "render_executor"

    def run(self) -> int:
        stage = self.name
        if self.is_done(stage):
            print(f"  SKIP: {stage} already completed")
            return 0

        cmds_path = self.episode_dir / "render" / "ffmpeg_commands.json"
        if not cmds_path.exists():
            return self.fail("CMDS_NOT_FOUND", "render/ffmpeg_commands.json required")

        ffmpeg_cmds = read_json(cmds_path)
        scenes_data = ffmpeg_cmds.get("scenes", [])
        if not scenes_data:
            return self.fail("NO_SCENES", "No scenes in ffmpeg_commands.json")

        render_dir = self.episode_dir / "render"
        render_dir.mkdir(parents=True, exist_ok=True)

        start_time = time.time()

        late_errors: list[str] = []
        scene_results: dict[int, bool] = {}
        completed_scenes = self._load_completed_scenes()

        def _run_scene(scene_cmds: dict) -> tuple[int, bool, list[str]]:
            sn = scene_cmds["scene_number"]
            if sn in completed_scenes:
                return sn, True, []
            errs = []
            success = True
            for cmd_entry in scene_cmds.get("commands", []):
                cmd = cmd_entry.get("command", [])
                if not cmd:
                    continue
                ok, err = self._exec_ffmpeg(cmd)
                if not ok:
                    errs.append(f"Scene {sn}: {cmd_entry.get('type', 'unknown')}: {err}")
                    success = False
            return sn, success, errs

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
            futures = {
                pool.submit(_run_scene, sd): sd["scene_number"]
                for sd in scenes_data
            }
            for future in as_completed(futures):
                sn, success, errs = future.result()
                scene_results[sn] = success
                late_errors.extend(errs)
                if success:
                    self._mark_scene_complete(sn)
                    print(f"    Scene {sn}: OK")
                else:
                    print(f"    Scene {sn}: FAILED")

        succeeded = sum(1 for v in scene_results.values() if v)
        failed = sum(1 for v in scene_results.values() if not v)

        concat_cmd = ffmpeg_cmds.get("concat_command", {})
        if concat_cmd.get("command"):
            if succeeded > 0:
                ok, err = self._exec_ffmpeg(concat_cmd["command"])
                if not ok:
                    late_errors.append(f"Concat: {err}")
            else:
                late_errors.append("No scenes succeeded, skipping concat")

        final_output_rel = ffmpeg_cmds.get("final_output", "render/final_video.mp4")
        final_path = self.episode_dir / final_output_rel

        render_time = time.time() - start_time
        output_size = final_path.stat().st_size if final_path.exists() else 0

        manifest = {
            "render_time": datetime.now(timezone.utc).isoformat(),
            "duration_seconds": round(render_time, 2),
            "input_assets": self._collect_input_assets(scenes_data),
            "output_size_bytes": output_size,
            "output_path": final_output_rel,
            "errors": late_errors,
            "scene_count": len(scenes_data),
            "succeeded_scenes": succeeded,
            "failed_scenes": failed,
        }

        self._validate_manifest(manifest)
        write_json(self.episode_dir / "render" / "render_manifest.json", manifest)

        self.save_checkpoint(stage, {"render_time": round(render_time, 2)})
        print(f"  Final video: {final_output_rel} ({output_size} bytes)")
        print(f"  Scenes: {succeeded} succeeded, {failed} failed")
        print(f"  Errors: {len(late_errors)}")
        return 0 if failed == 0 else 1

    def _exec_ffmpeg(self, cmd: list[str]) -> tuple[bool, str]:
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,
            )
            if result.returncode != 0:
                stderr_preview = result.stderr[:500] if result.stderr else "no stderr"
                return False, f"exit={result.returncode}: {stderr_preview}"
            return True, ""
        except FileNotFoundError:
            return False, "ffmpeg not found on system PATH"
        except subprocess.TimeoutExpired:
            return False, "ffmpeg timed out after 600s"
        except Exception as e:
            return False, str(e)

    def _load_completed_scenes(self) -> set[int]:
        path = self.episode_dir / ".checkpoint_render.json"
        if path.exists():
            try:
                data = json.loads(path.read_text())
                return set(data.get("completed_scenes", []))
            except Exception:
                pass
        return set()

    def _mark_scene_complete(self, scene_num: int) -> None:
        path = self.episode_dir / ".checkpoint_render.json"
        data = {"completed_scenes": []}
        if path.exists():
            try:
                data = json.loads(path.read_text())
            except Exception:
                pass
        if scene_num not in data["completed_scenes"]:
            data["completed_scenes"].append(scene_num)
        data["completed_scenes"].sort()
        path.write_text(json.dumps(data, indent=2) + "\n")

    def _collect_input_assets(
        self, scenes_data: list[dict]
    ) -> dict[str, list[str]]:
        images: set[str] = set()
        voiceover: set[str] = set()
        timeline_path = self.episode_dir / "render" / "timeline.json"
        if timeline_path.exists():
            timeline = read_json(timeline_path)
            for sc in timeline.get("scenes", []):
                img = sc.get("image", "")
                if img:
                    images.add(img)
                vo = sc.get("voiceover", [])
                if isinstance(vo, str):
                    vo = [vo]
                for v in vo:
                    if v:
                        voiceover.add(v)
        return {
            "images": sorted(images),
            "voiceover": sorted(voiceover),
        }

    def _validate_manifest(self, manifest: dict[str, Any]) -> None:
        schema_path = self.root_dir / "templates" / "schemas" / "render_manifest.json"
        errors = validate_output(manifest, schema_path)
        if errors:
            raise AgentError("SCHEMA_VALIDATION_FAILED", "; ".join(errors))


def run(input_dir: str, output_dir: str, config: dict) -> int:
    agent = RenderExecutorAgent(input_dir, config)
    return agent.run()


if __name__ == "__main__":
    _, input_dir, output_dir, config_path = sys.argv
    config = json.load(open(config_path))
    config["root"] = str(Path(config_path).parent.parent.parent)
    sys.exit(run(input_dir, output_dir, config))
