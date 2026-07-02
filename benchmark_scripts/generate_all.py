#!/usr/bin/env python3
"""Generate all 10 benchmark episodes through the full pipeline.

Usage:
    python benchmark_scripts/generate_all.py [--mode sequential|parallel] [--parallel N]
    python benchmark_scripts/generate_all.py [--dry-run] [--force] [--from STAGE]

Behavior:
    - Creates blueprints for episodes 2–10 if missing.
    - Runs each episode through the full pipeline.
    - Records environment metadata before starting.
    - Archives metrics after each successful run.
    - Generates aggregate benchmark report at the end.

Flags:
    --mode {sequential,parallel}  Run mode (default: sequential)
    --parallel N                  Run up to N episodes concurrently (default: 4 in parallel mode)
    --dry-run                     Run pipeline with --dry-run (no LLM calls, no rendering)
    --force                       Pass --force to each pipeline run
    --from STAGE                  Resume from a specific stage for all episodes
    --benchmark-dir PATH          Output directory for benchmark artifacts (default: benchmark_results)
"""

from __future__ import annotations
import argparse
import json
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
PROJECTS_DIR = REPO_ROOT / "projects"
EPISODES = [f"case_{i:03d}" for i in range(1, 11)]


def _run(args: list[str], **kwargs) -> subprocess.CompletedProcess:
    print(f"  RUN: {' '.join(args[:8])}{'...' if len(args) > 8 else ''}")
    return subprocess.run(args, capture_output=True, text=True, **kwargs)


def _try_run(args: list[str], cwd: Path, default: str = "") -> str:
    try:
        result = subprocess.run(args, capture_output=True, text=True, cwd=cwd, timeout=10)
        return result.stdout.strip()[:200] or default
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return default


def record_environment(benchmark_dir: Path) -> dict:
    env = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "git_commit": _try_run(["git", "rev-parse", "HEAD"], REPO_ROOT),
        "python_version": _try_run([sys.executable, "--version"], REPO_ROOT),
        "os": _try_run(["uname", "-a"], REPO_ROOT),
        "cpu_cores": _try_run(["nproc"], REPO_ROOT),
        "memory": _try_run(["free", "-g"], REPO_ROOT),
        "ffmpeg_version": _try_run(["ffmpeg", "-version"], REPO_ROOT, "not installed"),
        "llm_provider": _get_env_or_config("LLM_PROVIDER"),
        "llm_model": _get_env_or_config("LLM_MODEL"),
    }
    path = benchmark_dir / "environment.json"
    path.write_text(json.dumps(env, indent=2) + "\n")
    print(f"  ENV: {path}")
    return env


def _get_env_or_config(key: str) -> str:
    import os
    val = os.environ.get(key)
    if val:
        return val
    config_path = REPO_ROOT / "config" / "default.json"
    if config_path.exists():
        data = json.loads(config_path.read_text())
        if key.lower() == "llm_provider":
            return data.get("llm", {}).get("provider", "unknown")
        if key.lower() == "llm_model":
            return data.get("llm", {}).get("model", "unknown")
    return "unknown"


def archive_metrics(episode: str, benchmark_dir: Path) -> None:
    src = PROJECTS_DIR / episode / "metrics"
    dst = benchmark_dir / "metrics" / episode
    if src.exists():
        dst.mkdir(parents=True, exist_ok=True)
        for f in src.glob("*.json"):
            shutil.copy2(str(f), str(dst / f.name))
        print(f"  ARCHIVE: {episode}/metrics -> {dst.relative_to(REPO_ROOT)}")


def archive_reports(episode: str, benchmark_dir: Path) -> None:
    src = PROJECTS_DIR / episode / "reports"
    dst = benchmark_dir / "reports" / episode
    if src.exists():
        dst.mkdir(parents=True, exist_ok=True)
        for f in src.glob("*.md"):
            shutil.copy2(str(f), str(dst / f.name))


def run_episode(
    episode: str,
    dry_run: bool = False,
    force: bool = False,
    resume_from: str | None = None,
    timeout_minutes: int = 60,
) -> int:
    cmd = [sys.executable, "-m", "shadow_protocol.cli", episode]
    if dry_run:
        cmd.append("--dry-run")
    if force:
        cmd.append("--force")
    if resume_from:
        cmd.extend(["--from", resume_from])

    print(f"\n{'='*70}")
    print(f"  EPISODE: {episode}")
    if dry_run:
        print(f"  MODE: dry-run")
    print(f"{'='*70}")

    start = time.time()
    result = _run(cmd, cwd=REPO_ROOT, timeout=timeout_minutes * 60)
    elapsed = time.time() - start

    if result.stdout:
        print(result.stdout[-2000:] if len(result.stdout) > 2000 else result.stdout)
    if result.stderr:
        print(result.stderr[-1000:] if len(result.stderr) > 1000 else result.stderr)

    status = "OK" if result.returncode == 0 else f"FAILED (code={result.returncode})"
    print(f"\n  RESULT: {episode} {status} in {elapsed:.1f}s")
    return result.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate all 10 benchmark episodes")
    parser.add_argument("--mode", choices=["sequential", "parallel"], default="sequential",
                        help="Run mode: sequential (one at a time) or parallel (concurrent)")
    parser.add_argument("--parallel", type=int, default=4,
                        help="Max concurrent episodes when --mode=parallel (default: 4)")
    parser.add_argument("--dry-run", action="store_true", help="Run pipeline with --dry-run")
    parser.add_argument("--force", action="store_true", help="Pass --force to each pipeline run")
    parser.add_argument("--from", dest="resume_from", help="Resume from a specific stage for all episodes")
    parser.add_argument("--benchmark-dir", default="benchmark_results", help="Output directory for benchmark artifacts")
    args = parser.parse_args()

    parallel_workers = args.parallel if args.mode == "parallel" else 1

    benchmark_dir = REPO_ROOT / args.benchmark_dir
    benchmark_dir.mkdir(parents=True, exist_ok=True)

    # Create blueprints if missing
    print("Step 1: Creating blueprints...")
    subprocess.run(
        [sys.executable, str(REPO_ROOT / "benchmark_scripts" / "create_blueprints.py")],
        cwd=REPO_ROOT,
    )

    # Record environment
    print("\nStep 2: Recording environment...")
    record_environment(benchmark_dir)

    # Run episodes
    print(f"\nStep 3: Running {len(EPISODES)} episodes (mode={args.mode}, workers={parallel_workers})...")
    exit_codes: dict[str, int] = {}

    if parallel_workers > 1:
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=parallel_workers) as pool:
            futures = {}
            for ep in EPISODES:
                future = pool.submit(
                    run_episode, ep, args.dry_run, args.force, args.resume_from
                )
                futures[future] = ep

            from concurrent.futures import as_completed
            for future in as_completed(futures):
                ep = futures[future]
                try:
                    exit_codes[ep] = future.result()
                except Exception as e:
                    print(f"\n  EXCEPTION: {ep} — {e}")
                    exit_codes[ep] = -1
    else:
        for ep in EPISODES:
            exit_codes[ep] = run_episode(ep, args.dry_run, args.force, args.resume_from)
            archive_metrics(ep, benchmark_dir)
            archive_reports(ep, benchmark_dir)

    # Generate aggregate report
    print("\nStep 4: Generating benchmark report...")
    subprocess.run(
        [sys.executable, str(REPO_ROOT / "benchmark_scripts" / "benchmark_report.py")],
        cwd=REPO_ROOT,
    )

    # Print summary
    print(f"\n{'='*70}")
    print("  BENCHMARK SUMMARY")
    print(f"{'='*70}")
    successes = sum(1 for c in exit_codes.values() if c == 0)
    failures = sum(1 for c in exit_codes.values() if c != 0)
    print(f"  Episodes: {len(EPISODES)}  Success: {successes}  Failures: {failures}")
    for ep, code in exit_codes.items():
        print(f"    {ep}: {'OK' if code == 0 else f'FAIL (code={code})'}")
    print(f"\n  Benchmark artifacts: {benchmark_dir.relative_to(REPO_ROOT)}/")
    print()

    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
