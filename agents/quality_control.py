#!/usr/bin/env python3
"""Agent: Quality Control — validates all assets and pipeline integrity.

Checks video file existence and duration, thumbnail, metadata, render success,
and manifest integrity. Produces quality_report.json.
"""

from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent))
from agents.lib.agent_base import AgentBase, AgentError
from shadow_protocol.lib.file_utils import read_json, write_json
from shadow_protocol.lib.schema_validator import validate_output


class QualityControlAgent(AgentBase):
    name = "quality_control"

    def run(self) -> int:
        stage = self.name
        if self.is_done(stage):
            print(f"  SKIP: {stage} already completed")
            return 0

        checks: list[dict[str, Any]] = []
        warnings: list[str] = []

        self._check_video_exists(checks)
        self._check_video_duration(checks)
        self._check_thumbnail(checks)
        self._check_render_manifest(checks)
        self._check_publish_manifest(checks)
        self._check_youtube_metadata(checks)
        self._check_render_errors(checks, warnings)
        self._check_pipeline_status(checks, warnings)

        total = len(checks)
        passed_count = sum(1 for c in checks if c["passed"])
        failed_count = sum(1 for c in checks if not c["passed"])
        warning_count = len(warnings)

        report = {
            "passed": failed_count == 0,
            "checks": checks,
            "summary": {
                "total": total,
                "passed": passed_count,
                "failed": failed_count,
                "warnings": warning_count,
            },
            "warnings": warnings,
        }

        self._validate(report)
        write_json(self.episode_dir / "publish" / "quality_report.json", report)

        self.save_checkpoint(stage)
        status = "PASS" if report["passed"] else "FAIL"
        print(f"  Quality: {status} ({passed_count}/{total} checks passed)")
        if warnings:
            for w in warnings:
                print(f"  WARNING: {w}")
        return 0 if report["passed"] else 1

    def _check_video_exists(self, checks: list[dict]) -> None:
        path = self.episode_dir / "render" / "final_video.mp4"
        exists = path.exists()
        checks.append({
            "name": "video_exists",
            "passed": exists,
            "message": "final_video.mp4 exists" if exists else "final_video.mp4 not found",
            "severity": "error",
        })

    def _check_video_duration(self, checks: list[dict]) -> None:
        path = self.episode_dir / "render" / "final_video.mp4"
        if not path.exists():
            checks.append({
                "name": "video_duration",
                "passed": False,
                "message": "Cannot check duration: video not found",
                "severity": "error",
            })
            return

        duration = self._get_video_duration(path)
        if duration is not None and duration > 0:
            checks.append({
                "name": "video_duration",
                "passed": True,
                "message": f"Video duration: {duration:.1f}s",
                "severity": "info",
            })
        else:
            checks.append({
                "name": "video_duration",
                "passed": False,
                "message": "Video duration could not be determined or is zero",
                "severity": "error",
            })

    def _check_thumbnail(self, checks: list[dict]) -> None:
        candidates = [
            self.episode_dir / "assets" / "thumbnail" / "thumbnail.png",
            self.episode_dir / "assets" / "images" / "thumbnail.png",
            self.episode_dir / "publish" / "upload_package" / "thumbnail.png",
        ]
        found = False
        for c in candidates:
            if c.exists():
                found = True
                break

        if found:
            checks.append({
                "name": "thumbnail_exists",
                "passed": True,
                "message": "Thumbnail found",
                "severity": "info",
            })
        else:
            checks.append({
                "name": "thumbnail_exists",
                "passed": True,
                "message": "No thumbnail.png found (optional — upload without thumbnail)",
                "severity": "warning",
            })

    def _check_render_manifest(self, checks: list[dict]) -> None:
        path = self.episode_dir / "render" / "render_manifest.json"
        if path.exists():
            data = read_json(path)
            failed = data.get("failed_scenes", 0)
            checks.append({
                "name": "render_manifest",
                "passed": failed == 0,
                "message": (
                    f"Render manifest OK ({data.get('succeeded_scenes', 0)} scenes)"
                    if failed == 0
                    else f"Render manifest: {failed} failed scenes"
                ),
                "severity": "error",
            })
        else:
            checks.append({
                "name": "render_manifest",
                "passed": False,
                "message": "render_manifest.json not found",
                "severity": "error",
            })

    def _check_publish_manifest(self, checks: list[dict]) -> None:
        path = self.episode_dir / "publish" / "publish_manifest.json"
        if path.exists():
            data = read_json(path)
            missing_req = [
                a["name"]
                for a in data.get("assets", [])
                if a.get("required", False) and not a.get("exists") and a["name"] not in ("thumbnail.png",)
            ]
            checks.append({
                "name": "publish_manifest",
                "passed": len(missing_req) == 0,
                "message": (
                    "Publish manifest valid"
                    if not missing_req
                    else f"Missing required assets: {', '.join(missing_req)}"
                ),
                "severity": "error",
            })
        else:
            checks.append({
                "name": "publish_manifest",
                "passed": False,
                "message": "publish_manifest.json not found",
                "severity": "error",
            })

    def _check_youtube_metadata(self, checks: list[dict]) -> None:
        path = self.episode_dir / "youtube_metadata.json"
        if path.exists():
            data = read_json(path)
            has_title = bool(data.get("title", ""))
            checks.append({
                "name": "youtube_metadata",
                "passed": has_title,
                "message": "YouTube metadata OK" if has_title else "YouTube metadata missing title",
                "severity": "error",
            })
        else:
            checks.append({
                "name": "youtube_metadata",
                "passed": False,
                "message": "youtube_metadata.json not found",
                "severity": "error",
            })

    def _check_render_errors(self, checks: list[dict], warnings: list[str]) -> None:
        path = self.episode_dir / "render" / "render_manifest.json"
        if path.exists():
            data = read_json(path)
            errors = data.get("errors", [])
            if errors:
                for e in errors[:5]:
                    warnings.append(f"Render error: {e}")
            checks.append({
                "name": "render_errors",
                "passed": len(errors) == 0,
                "message": "No render errors" if not errors else f"{len(errors)} render error(s)",
                "severity": "error",
            })
        else:
            checks.append({
                "name": "render_errors",
                "passed": False,
                "message": "Cannot check render errors: manifest not found",
                "severity": "error",
            })

    def _check_pipeline_status(self, checks: list[dict], warnings: list[str]) -> None:
        path = self.episode_dir / ".checkpoint.json"
        if path.exists():
            data = read_json(path)
            completed = data.get("completed", [])
            stages = [
                "production_package",
                "outline",
                "script",
                "script_review",
                "scene_breakdown",
                "image_prompt",
                "voiceover",
                "metadata",
                "thumbnail",
                "image_generator",
                "voice_generator",
                "timeline_builder",
                "render_builder",
                "render_executor",
            ]
            missing = [s for s in stages if s not in completed]
            if missing:
                for m in missing:
                    warnings.append(f"Stage not completed: {m}")
            checks.append({
                "name": "pipeline_completeness",
                "passed": len(missing) == 0,
                "message": "All stages completed" if not missing else f"Missing stages: {', '.join(missing)}",
                "severity": "warning",
            })
        else:
            warnings.append("No checkpoint file found — pipeline may not have run")

    def _get_video_duration(self, path: Path) -> float | None:
        try:
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v", "error",
                    "-show_entries", "format=duration",
                    "-of", "csv=p=0",
                    str(path.resolve()),
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0 and result.stdout.strip():
                return float(result.stdout.strip())
        except Exception:
            pass
        return None

    def _validate(self, report: dict[str, Any]) -> None:
        schema_path = self.root_dir / "templates" / "schemas" / "quality_report.json"
        errors = validate_output(report, schema_path)
        if errors:
            raise AgentError("SCHEMA_VALIDATION_FAILED", "; ".join(errors))


def run(input_dir: str, output_dir: str, config: dict) -> int:
    agent = QualityControlAgent(input_dir, config)
    return agent.run()


if __name__ == "__main__":
    _, input_dir, output_dir, config_path = sys.argv
    config = json.load(open(config_path))
    config["root"] = str(Path(config_path).parent.parent.parent)
    sys.exit(run(input_dir, output_dir, config))
