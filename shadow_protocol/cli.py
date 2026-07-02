"""CLI entrypoint for Shadow Protocol Studio."""

from dotenv import load_dotenv

load_dotenv(override=True)
import json
import os
import sys
from pathlib import Path

import click


def _show_quota_status():
    """Print quota status across all project directories."""
    projects_dir = Path.cwd() / "projects"
    if not projects_dir.exists():
        click.echo("No projects directory found.")
        return

    quota_files = sorted(projects_dir.glob("*/quota_status.json"))
    if not quota_files:
        click.echo("No quota exhaustion events recorded.")
        return

    click.echo("Quota Status")
    click.echo("============")
    click.echo("")

    for qf in quota_files:
        status = json.loads(qf.read_text())
        case_id = qf.parent.name
        click.echo(f"Episode:  {case_id}")
        click.echo(f"Provider: {status.get('provider', '?')}")
        click.echo(f"Error:    {status.get('error', '?')}")
        click.echo(f"Stage:    {status.get('failed_stage', '?')}")
        click.echo(f"Time:     {status.get('failed_at', '?')}")
        click.echo(f"Resume:   {status.get('resume_command', '?')}")
        click.echo("")

    # Count pending vs resumable
    pending = [p.name for p in sorted(projects_dir.glob("case_*")) if not (p / "publish" / "publishing_report.md").exists()]
    resumable = [qf.parent.name for qf in quota_files]
    if pending:
        click.echo(f"Pending episodes:  {', '.join(pending)}")
    if resumable:
        click.echo(f"Resumable episodes: {', '.join(resumable)}")


def _show_estimate():
    """Show per-model quota estimate for running a new episode."""
    from shadow_protocol.lib.quota_manager import QuotaManager

    projects_dir = Path.cwd() / "projects"
    if not projects_dir.exists():
        click.echo("No projects directory found.")
        return

    qm = QuotaManager(projects_dir)

    # Auto-detect scene count from existing breakdowns
    scene_count = 15
    breakdowns = sorted(projects_dir.glob("*/scene_breakdown.json"))
    if breakdowns:
        import json as _json
        data = _json.loads(breakdowns[-1].read_text())
        scenes = data if isinstance(data, list) else data.get("scenes", [])
        if scenes:
            scene_count = max(len(scenes), 12)

    estimate = qm.estimate_episode(scene_count)

    click.echo("Episode Cost Estimate (Hybrid Routing)")
    click.echo("======================================")
    click.echo(f"Scene count:       {scene_count}")
    click.echo(f"Total calls:       {estimate['total_estimated_requests']}")
    click.echo("")
    click.echo("Per-Model Breakdown:")
    click.echo("--------------------")
    for model, data in estimate["by_model"].items():
        status = "OK" if data["can_run"] else "INSUFFICIENT"
        click.echo(f"  {model}:")
        click.echo(f"    Calls:         {data['estimated_requests']}")
        click.echo(f"    Stages:        {', '.join(data['stages'])}")
        click.echo(f"    Remaining:     {data['remaining_requests']}/{data['rpd']} RPD")
        click.echo(f"    Status:        {status}")
    click.echo("")
    click.echo(f"Can run episode:   {'YES' if estimate['can_run_full_episode'] else 'NO'}")
    click.echo(f"Recommendation:    {estimate['recommendation']}")


def _handle_benchmark_models(args: list[str]):
    """Run dry-run pipeline and report per-model benchmark metrics."""
    if not args:
        click.echo("Usage: create-video benchmark-models CASE_ID")
        return
    case_id = args[0]
    click.echo(f"Benchmarking models with case: {case_id}")
    click.echo("")

    # Run pipeline in dry-run mode
    from shadow_protocol.lib.orchestrator_runner import run_pipeline
    exit_code = run_pipeline(
        case_id=case_id,
        dry_run=True,
        force=True,
        mode="production",
    )
    click.echo("")
    click.echo(f"Pipeline exit code: {exit_code}")

    # Show per-model quota status
    from shadow_protocol.lib.quota_manager import QuotaManager, display_quota_status
    projects_dir = Path.cwd() / "projects"
    qm = QuotaManager(projects_dir)
    click.echo("")
    click.echo(display_quota_status(projects_dir))


def _handle_queue(args: list[str]):
    """Handle queue subcommands: add, status, cancel."""
    from shadow_protocol.lib.queue_manager import QueueManager

    projects_dir = Path.cwd() / "projects"
    qm = QueueManager(projects_dir)

    if not args or args[0] == "status":
        jobs = qm.poll_all()
        if not jobs:
            click.echo("No jobs in queue.")
            return
        click.echo("Queue Status")
        click.echo("============")
        for job in reversed(jobs):
            status = job["status"]
            icon = {"pending": "⏳", "running": "▶", "completed": "✓", "failed": "✗", "cancelled": "—"}.get(status, "?")
            click.echo(f"  {icon} Job #{job['id']}: {job['case_id']} [{status}]")
            if job.get("started_at"):
                click.echo(f"     Started: {job['started_at']}")
            if job.get("finished_at"):
                click.echo(f"     Finished: {job['finished_at']}")
        return

    if args[0] == "add" and len(args) >= 2:
        case_id = args[1]
        mode = args[2] if len(args) >= 3 else "production"
        dry_run = "--dry-run" in args
        job_id = qm.add_job(case_id, mode=mode, dry_run=dry_run)
        click.echo(f"Added job #{job_id} for {case_id} (mode={mode})")
        started = qm.start_job(job_id)
        if started:
            click.echo(f"Job #{job_id} started in background.")
        else:
            click.echo(f"Job #{job_id} queued (will start when resources available).")
        return

    if args[0] == "cancel" and len(args) >= 2:
        try:
            job_id = int(args[1])
        except ValueError:
            click.echo("Usage: create-video queue cancel JOB_ID")
            return
        cancelled = qm.cancel_job(job_id)
        if cancelled:
            click.echo(f"Cancelled job #{job_id}.")
        else:
            click.echo(f"Job #{job_id} not found or already finished.")
        return

    click.echo("Usage: create-video queue add|status|cancel [args]")


@click.command(context_settings=dict(ignore_unknown_options=False, allow_extra_args=True))
@click.argument("case_id", required=True)
@click.option("--dry-run", is_flag=True, help="Simulate pipeline without LLM calls")
@click.option("--from", "resume_step", help="Resume from a specific pipeline stage")
@click.option("--force", is_flag=True, help="Clear checkpoints and re-run all stages")
@click.option("--mode", type=click.Choice(["dev", "production"]), default="production", help="Pipeline mode: dev (placeholders, no render) or production (full)")
def main(case_id: str, dry_run: bool, resume_step: str | None, force: bool, mode: str):
    """Create a Shadow Protocol video episode."""

    if case_id == "quota":
        _show_quota_status()
        return

    if case_id == "estimate":
        _show_estimate()
        return

    if case_id == "queue":
        _handle_queue(sys.argv[2:] if len(sys.argv) > 2 else [])
        return

    if case_id == "benchmark-models":
        _handle_benchmark_models(sys.argv[2:] if len(sys.argv) > 2 else [])
        return

    click.echo(f"Shadow Protocol Studio v0.1.0")
    click.echo(f"Case: {case_id}")
    click.echo(f"Mode: {mode}")
    if dry_run:
        click.echo("Mode: dry-run (simulation)")
    if resume_step:
        click.echo(f"Resume from: {resume_step}")
    if force:
        click.echo("Force: clearing checkpoints")

    from shadow_protocol.lib.orchestrator_runner import run_pipeline

    exit_code = run_pipeline(
        case_id=case_id,
        dry_run=dry_run,
        resume_step=resume_step,
        force=force,
        mode=mode,
    )
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
