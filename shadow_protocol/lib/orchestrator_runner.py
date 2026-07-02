"""Runs the pipeline by delegating to each agent sequentially with metrics and timing."""

from __future__ import annotations
import json
import sys
from pathlib import Path
from typing import Any

from shadow_protocol.lib.file_utils import load_config
from shadow_protocol.lib.checkpoint import get_completed_stages, clear_checkpoint, get_stage_metadata
from shadow_protocol.lib.metrics import MetricsCollector
from shadow_protocol.lib.reporting import generate_pipeline_summary
from shadow_protocol.lib.quota_manager import QuotaManager


RENDER_STAGES = {
    "image_generator",
    "voice_generator",
    "timeline_builder",
    "render_builder",
    "render_executor",
    "publish_package_builder",
    "quality_control",
    "release_manager",
}

STAGE_ORDER = [
    "production_package",
    "outline",
    "script",
    "script_review",
    "scene_breakdown",
    "asset_package",
    "voiceover",
    "image_generator",
    "voice_generator",
    "timeline_builder",
    "render_builder",
    "render_executor",
    "publish_package_builder",
    "quality_control",
    "release_manager",
]

AGENT_SCRIPT_MAP = {
    "production_package": "agents/production_package.py",
    "outline": "agents/outline.py",
    "script": "agents/script.py",
    "script_review": "agents/script_review.py",
    "scene_breakdown": "agents/scene_breakdown.py",
    "asset_package": "agents/asset_package.py",
    "voiceover": "agents/voiceover.py",
    "image_generator": "agents/image_generator.py",
    "voice_generator": "agents/voice_generator.py",
    "timeline_builder": "agents/timeline_builder.py",
    "render_builder": "agents/render_builder.py",
    "render_executor": "agents/render_executor.py",
    "publish_package_builder": "agents/publish_package_builder.py",
    "quality_control": "agents/quality_control.py",
    "release_manager": "agents/release_manager.py",
}


def run_pipeline(
    case_id: str,
    dry_run: bool = False,
    resume_step: str | None = None,
    force: bool = False,
    mode: str = "production",
) -> int:
    root_dir = Path.cwd()
    config = load_config(root_dir / "config" / "default.json")
    config["root"] = str(root_dir)
    config["mode"] = mode

    episode_dir = root_dir / "projects" / case_id
    episode_dir.mkdir(parents=True, exist_ok=True)

    logs_dir = episode_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    metrics_dir = episode_dir / "metrics"
    metrics_dir.mkdir(parents=True, exist_ok=True)

    reports_dir = episode_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    if force:
        clear_checkpoint(episode_dir)
        _clean_dir(metrics_dir)

    collector = MetricsCollector(case_id, metrics_dir)
    completed = get_completed_stages(episode_dir)

    if resume_step:
        if resume_step not in STAGE_ORDER:
            print(f"Unknown step: {resume_step}", file=sys.stderr)
            return 1
        start_idx = STAGE_ORDER.index(resume_step)
    else:
        start_idx = 0
        while start_idx < len(STAGE_ORDER) and STAGE_ORDER[start_idx] in completed:
            start_idx += 1

    if start_idx >= len(STAGE_ORDER):
        print(f"All stages already completed for {case_id}")
        _generate_summary(collector, reports_dir)
        return 0

    collector.start_pipeline()

    # Pre-flight quota check — warn if quota is low
    _check_quota_before_pipeline(episode_dir)

    # Determine effective stage order based on mode
    effective_order = [s for s in STAGE_ORDER if mode == "production" or s not in RENDER_STAGES]

    for stage in effective_order[start_idx:]:
        print(f"\n{'='*60}")
        print(f"Stage: {stage}")
        print(f"{'='*60}")

        agent_script = root_dir / AGENT_SCRIPT_MAP[stage]
        if not agent_script.exists():
            print(f"  SKIP: {agent_script} not found")
            collector.skip_stage(stage)
            continue

        collector.start_stage(stage)

        if dry_run:
            print(f"  DRY-RUN: would execute {agent_script}")
            collector.end_stage(stage, status="skipped")
            continue

        exit_code = _run_agent(agent_script, episode_dir, config, logs_dir, stage)

        stage_meta = get_stage_metadata(episode_dir, stage) or {}

        if exit_code == 0:
            output_files = _list_output_files(episode_dir, stage)
            collector.end_stage(
                stage=stage,
                status="success",
                prompt_tokens=stage_meta.get("tokens", 0),
                completion_tokens=0,
                llm_calls=stage_meta.get("calls", 0),
                cost_usd=stage_meta.get("cost", 0.0),
                output_files=output_files,
            )
            print("  OK")
        else:
            collector.end_stage(
                stage=stage,
                status="failed",
                error=f"Agent exited with code {exit_code}",
            )
            print(f"  FAILED: {stage} exited with code {exit_code}")
            _generate_summary(collector, reports_dir)
            return exit_code

    _log_llm_summary(collector)
    _generate_summary(collector, reports_dir)
    print(f"\nPipeline complete for {case_id}")
    return 0


def _run_agent(
    script_path: Path,
    episode_dir: Path,
    config: dict[str, Any],
    logs_dir: Path,
    stage: str,
) -> int:
    import subprocess

    config_path = episode_dir / f".agent_config_{script_path.stem}.json"
    with open(config_path, "w") as f:
        json.dump(config, f)

    log_path = logs_dir / f"{stage}.log"
    with open(log_path, "w") as log_f:
        proc = subprocess.run(
            [sys.executable, str(script_path), str(episode_dir), str(episode_dir), str(config_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )

    if proc.stdout:
        output = proc.stdout.decode("utf-8", errors="replace")
        print(output, end="")
        with open(log_path, "a") as log_f:
            log_f.write(output)

    if config_path.exists():
        config_path.unlink()

    return proc.returncode


def _list_output_files(episode_dir: Path, stage: str) -> list[str]:
    patterns = {
        "production_package": ["production_package.json"],
        "outline": ["outline.json"],
        "script": ["script/"],
        "script_review": ["review.json", "review.md"],
        "scene_breakdown": ["scene_breakdown.json"],
        "asset_package": ["image_prompts.json", "video_prompts.json", "youtube_metadata.json", "thumbnail_prompt.json", "thumbnail_prompt.txt"],
        "voiceover": ["voiceover_segments.json"],
        "image_generator": ["assets/images/", "assets/manifests/asset_manifest.json"],
        "voice_generator": ["assets/voice/", "assets/manifests/asset_manifest.json"],
        "timeline_builder": ["render/timeline.json", "render/chapters.txt"],
        "render_builder": ["render/ffmpeg_commands.json"],
        "render_executor": ["render/final_video.mp4", "render/render_manifest.json"],
        "publish_package_builder": ["publish/publish_manifest.json", "publish/upload_package/"],
        "quality_control": ["publish/quality_report.json"],
        "release_manager": ["publish/publishing_report.md"],
    }
    results = []
    for p in patterns.get(stage, []):
        full = episode_dir / p
        if full.exists():
            if full.is_dir():
                results.extend(str(f.relative_to(episode_dir)) for f in sorted(full.rglob("*")) if f.is_file())
            else:
                results.append(p)
    return results


def _log_llm_summary(collector: MetricsCollector) -> None:
    summary = collector.pipeline_summary()
    print(f"\n{'='*60}")
    print("LLM Usage Summary")
    print(f"{'='*60}")
    print(f"  Total calls:  {summary.total_llm_calls}")
    print(f"  Total tokens: {summary.total_tokens}")
    print(f"  Total cost:   ${summary.total_cost_usd:.6f}")


def _generate_summary(collector: MetricsCollector, reports_dir: Path) -> None:
    metrics = collector.pipeline_summary()
    report = generate_pipeline_summary(metrics)
    path = reports_dir / "pipeline_summary.md"
    path.write_text(report)


def _check_quota_before_pipeline(episode_dir: Path) -> None:
    """Check remaining quota before starting the pipeline. Warns if low."""
    try:
        qm = QuotaManager(episode_dir.parent)
        provider = __import__("os").getenv("LLM_PROVIDER", "gemini")
        usage = qm.get_usage(provider)
        remaining = usage.get("estimated_remaining", 0)
        if remaining < 10:
            print(f"  WARN: Only {remaining} {provider} requests remaining today.")
            print(f"  Resume tomorrow or use a different provider.")
        elif remaining < 5:
            print(f"  CRITICAL: Only {remaining} {provider} requests left. Pipeline may pause.")
    except Exception:
        pass  # Non-fatal


def write_quota_status(episode_dir: Path, provider: str, failed_stage: str, failed_label: str) -> None:
    """Write quota_status.json for clean resume."""
    from datetime import datetime, timezone
    case_id = episode_dir.name
    status = {
        "provider": provider,
        "error": "daily_quota_exceeded",
        "failed_stage": failed_stage,
        "failed_section": failed_label,
        "failed_at": datetime.now(timezone.utc).isoformat(),
        "resume_command": f"create-video --from {failed_stage} {case_id}",
    }
    path = episode_dir / "quota_status.json"
    path.write_text(json.dumps(status, indent=2) + "\n")
    print(f"\nDaily {provider} quota exhausted.", file=__import__("sys").stderr)
    print(f"Resume tomorrow with:\n", file=__import__("sys").stderr)
    print(f"  {status['resume_command']}\n", file=__import__("sys").stderr)


def _clean_dir(d: Path) -> None:
    if d.exists():
        for f in d.iterdir():
            if f.is_file():
                f.unlink()
