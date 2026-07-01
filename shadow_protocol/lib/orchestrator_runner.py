"""Runs the pipeline by delegating to each agent sequentially."""

from __future__ import annotations
import importlib.util
import sys
from pathlib import Path
from typing import Any

from shadow_protocol.lib.file_utils import read_json, load_config


STAGE_ORDER = [
    "memory_resolver",
    "story_idea",
    "production_package",
    "outline",
    "script",
    "script_review",
    "scene_breakdown",
    "image_prompt",
    "video_prompt",
    "voiceover",
    "thumbnail",
    "metadata",
    "validation",
    "memory_update",
]

AGENT_SCRIPT_MAP = {
    "memory_resolver": "agents/memory_resolver.py",
    "story_idea": "agents/story_idea.py",
    "production_package": "agents/production_package.py",
    "outline": "agents/outline.py",
    "script": "agents/script.py",
    "script_review": "agents/script_review.py",
    "scene_breakdown": "agents/scene_breakdown.py",
    "image_prompt": "agents/image_prompt.py",
    "video_prompt": "agents/video_prompt.py",
    "voiceover": "agents/voiceover.py",
    "thumbnail": "agents/thumbnail.py",
    "metadata": "agents/metadata.py",
    "validation": "agents/validation.py",
    "memory_update": "agents/memory_update.py",
}


def run_pipeline(
    case_id: str,
    dry_run: bool = False,
    resume_step: str | None = None,
) -> int:
    root_dir = Path.cwd()
    config = load_config(root_dir / "config" / "default.json")
    config["root"] = root_dir

    projects_dir = root_dir / config["storage"]["projects_dir"]
    episode_dir = projects_dir / case_id
    episode_dir.mkdir(parents=True, exist_ok=True)

    resume_idx = 0
    if resume_step:
        if resume_step in STAGE_ORDER:
            resume_idx = STAGE_ORDER.index(resume_step)
        else:
            print(f"Unknown step: {resume_step}", file=sys.stderr)
            return 1

    for stage in STAGE_ORDER[resume_idx:]:
        print(f"\n{'='*60}")
        print(f"Stage: {stage}")
        print(f"{'='*60}")

        agent_script = root_dir / AGENT_SCRIPT_MAP[stage]
        if not agent_script.exists():
            print(f"  SKIP: {agent_script} not found")
            continue

        if dry_run:
            print(f"  DRY-RUN: would execute {agent_script}")
            continue

        exit_code = _run_agent(agent_script, episode_dir, episode_dir, config)
        if exit_code != 0:
            print(f"  FAILED: {stage} exited with code {exit_code}")
            return exit_code

        print(f"  OK")

    print(f"\nPipeline complete for {case_id}")
    return 0


def _run_agent(
    script_path: Path,
    input_dir: Path,
    output_dir: Path,
    config: dict[str, Any],
) -> int:
    import json
    import subprocess

    config_path = output_dir / f".agent_config_{script_path.stem}.json"
    with open(config_path, "w") as f:
        json.dump(config, f)

    result = subprocess.run(
        [sys.executable, str(script_path), str(input_dir), str(output_dir), str(config_path)],
        capture_output=False,
    )

    if config_path.exists():
        config_path.unlink()

    return result.returncode
