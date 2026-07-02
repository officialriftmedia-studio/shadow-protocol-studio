#!/usr/bin/env python3
"""Benchmark — measure pipeline performance and generate comparison reports.

Usage:
    python scripts/benchmark.py --mode before   # Snapshot baseline
    python scripts/benchmark.py --mode after    # Snapshot after optimization
    python scripts/benchmark.py --mode compare  # Generate comparison report
"""
from __future__ import annotations
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from shadow_protocol.lib.orchestrator_runner import run_pipeline


BENCHMARK_DIR = Path(__file__).parent.parent / "benchmarks"
BENCHMARK_DIR.mkdir(parents=True, exist_ok=True)

BENCHMARK_CASE = "case_benchmark"
BENCHMARK_FILE = BENCHMARK_DIR / "benchmark_results.json"
COMPARISON_FILE = BENCHMARK_DIR / "comparison_report.md"


def create_blueprint() -> Path:
    """Create a minimal blueprint for the benchmark case."""
    episode_dir = Path.cwd() / "projects" / BENCHMARK_CASE
    episode_dir.mkdir(parents=True, exist_ok=True)
    blueprint = {
        "episode_id": BENCHMARK_CASE,
        "title": "Benchmark Episode",
        "logline": "A test episode for benchmarking pipeline performance.",
        "protagonist": {"name": "Bench User", "role": "tester", "flaw": "impatience"},
        "antagonist_system": "the test suite",
        "central_mystery": "Why is the pipeline slow?",
        "larger_mystery": "Can we make it faster?",
        "themes": ["optimization", "testing"],
        "tone": "clinical",
        "inspirations": [],
    }
    path = episode_dir / "blueprint.json"
    path.write_text(json.dumps(blueprint, indent=2) + "\n")
    return episode_dir


def measure(mode_label: str) -> dict:
    """Run the pipeline in dry-run mode and collect metrics."""
    print(f"\n{'='*60}")
    print(f"Benchmark: {mode_label}")
    print(f"{'='*60}")

    create_blueprint()

    start = time.time()
    exit_code = run_pipeline(
        case_id=BENCHMARK_CASE,
        dry_run=True,
        force=True,
        mode="production",
    )
    elapsed = time.time() - start

    # Collect stage-level metrics from checkpoint metadata
    from shadow_protocol.lib.checkpoint import get_completed_stages, get_stage_metadata

    episode_dir = Path.cwd() / "projects" / BENCHMARK_CASE
    completed = get_completed_stages(episode_dir)
    stages = {}
    for stage in completed:
        meta = get_stage_metadata(episode_dir, stage) or {}
        stages[stage] = {
            "tokens": meta.get("tokens", 0),
            "calls": meta.get("calls", 0),
            "cost": meta.get("cost", 0.0),
        }

    result = {
        "mode": mode_label,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "exit_code": exit_code,
        "elapsed_seconds": round(elapsed, 2),
        "total_stages": len(completed),
        "stages": stages,
    }

    # Save to benchmark file
    results = []
    if BENCHMARK_FILE.exists():
        results = json.loads(BENCHMARK_FILE.read_text())
    results.append(result)
    BENCHMARK_FILE.write_text(json.dumps(results, indent=2) + "\n")

    print(f"\nElapsed: {elapsed:.2f}s | Stages: {len(completed)} | Exit: {exit_code}")
    return result


def compare() -> dict:
    """Compare the two most recent benchmark runs."""
    if not BENCHMARK_FILE.exists():
        print("No benchmark data found. Run --mode before and --mode after first.")
        return {}

    results = json.loads(BENCHMARK_FILE.read_text())
    if len(results) < 2:
        print("Need at least 2 benchmark runs to compare.")
        return {}

    before = results[-2]
    after = results[-1]

    lines = []
    lines.append("# Benchmark Comparison Report\n")
    lines.append(f"**Generated:** {datetime.now(timezone.utc).isoformat()}\n")
    lines.append(f"| Metric | Before | After | Change |")
    lines.append(f"|--------|--------|-------|--------|")

    def pct(b, a):
        if b == 0:
            return "N/A"
        return f"{((a - b) / b * 100):+.1f}%"

    elapsed_b = before.get("elapsed_seconds", 0)
    elapsed_a = after.get("elapsed_seconds", 0)
    lines.append(f"| Pipeline time (s) | {elapsed_b:.2f} | {elapsed_a:.2f} | {pct(elapsed_b, elapsed_a)} |")

    stages_b = before.get("total_stages", 0)
    stages_a = after.get("total_stages", 0)
    lines.append(f"| Stages executed | {stages_b} | {stages_a} | {pct(stages_b, stages_a)} |")

    calls_b = sum(s.get("calls", 0) for s in before.get("stages", {}).values())
    calls_a = sum(s.get("calls", 0) for s in after.get("stages", {}).values())
    lines.append(f"| LLM calls | {calls_b} | {calls_a} | {pct(calls_b, calls_a)} |")

    tokens_b = sum(s.get("tokens", 0) for s in before.get("stages", {}).values())
    tokens_a = sum(s.get("tokens", 0) for s in after.get("stages", {}).values())
    lines.append(f"| Total tokens | {tokens_b} | {tokens_a} | {pct(tokens_b, tokens_a)} |")

    cost_b = sum(s.get("cost", 0.0) for s in before.get("stages", {}).values())
    cost_a = sum(s.get("cost", 0.0) for s in after.get("stages", {}).values())
    lines.append(f"| Total cost (USD) | ${cost_b:.6f} | ${cost_a:.6f} | {pct(cost_b, cost_a)} |")

    lines.append("")
    lines.append("## Per-Stage Comparison\n")
    all_stages = sorted(set(list(before.get("stages", {}).keys()) + list(after.get("stages", {}).keys())))
    lines.append("| Stage | Before calls | After calls | Before tokens | After tokens |")
    lines.append("|-------|-------------|-------------|---------------|--------------|")
    for stage in all_stages:
        sb = before.get("stages", {}).get(stage, {})
        sa = after.get("stages", {}).get(stage, {})
        lines.append(f"| {stage} | {sb.get('calls', 0)} | {sa.get('calls', 0)} | {sb.get('tokens', 0)} | {sa.get('tokens', 0)} |")

    report = "\n".join(lines)
    COMPARISON_FILE.write_text(report)
    print(report)
    return {"before": before, "after": after}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Benchmark pipeline performance")
    parser.add_argument("--mode", choices=["before", "after", "compare"], required=True)
    args = parser.parse_args()

    if args.mode == "compare":
        compare()
    else:
        measure(args.mode)
