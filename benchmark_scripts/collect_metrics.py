#!/usr/bin/env python3
"""Collect and aggregate metrics from all benchmark episodes.

Outputs:
    benchmark_results/aggregate.json       — Full aggregated metrics
    benchmark_results/per_episode.json     — Per-episode summary
    benchmark_results/per_stage.json       — Per-stage statistics across episodes
    benchmark_results/durations.csv        — Stage duration CSV for analysis
"""

from __future__ import annotations
import csv
import json
import statistics
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
EPISODES = [f"case_{i:03d}" for i in range(1, 11)]


def load_metrics(episode: str) -> dict[str, dict]:
    """Load all stage metrics for an episode. Returns {stage_name: metrics_dict}."""
    metrics_dir = REPO_ROOT / "projects" / episode / "metrics"
    results: dict[str, dict] = {}
    if not metrics_dir.exists():
        return results
    for f in sorted(metrics_dir.glob("*.json")):
        data = json.loads(f.read_text())
        results[data.get("stage", f.stem)] = data
    return results


def _safe(values: list[float]) -> dict:
    if not values:
        return {"min": 0, "max": 0, "mean": 0, "median": 0, "p95": 0, "stddev": 0, "count": 0}
    sorted_v = sorted(values)
    return {
        "min": round(min(values), 4),
        "max": round(max(values), 4),
        "mean": round(statistics.mean(values), 4),
        "median": round(statistics.median(values), 4),
        "p95": round(sorted_v[int(len(sorted_v) * 0.95)], 4) if len(sorted_v) > 1 else sorted_v[0],
        "stddev": round(statistics.stdev(values), 4) if len(values) > 1 else 0,
        "count": len(values),
    }


def collect() -> dict:
    stage_data: dict[str, list[dict]] = {}
    episode_summaries: dict[str, dict] = {}

    for ep in EPISODES:
        metrics = load_metrics(ep)
        if not metrics:
            continue

        total_tokens = 0
        total_cost = 0.0
        total_duration = 0.0
        total_llm_calls = 0
        stages_failed = 0
        stages_ok = 0

        for stage_name, data in metrics.items():
            stage_data.setdefault(stage_name, []).append(data)
            total_tokens += data.get("total_tokens", 0)
            total_cost += data.get("cost_usd", 0.0)
            total_duration += data.get("duration_seconds", 0.0)
            total_llm_calls += data.get("llm_calls", 0)

            if data.get("status") == "success":
                stages_ok += 1
            elif data.get("status") == "failed":
                stages_failed += 1

        episode_summaries[ep] = {
            "total_tokens": total_tokens,
            "total_cost_usd": round(total_cost, 6),
            "total_duration_seconds": round(total_duration, 2),
            "total_llm_calls": total_llm_calls,
            "stages_completed": stages_ok,
            "stages_failed": stages_failed,
            "stage_count": len(metrics),
        }

    # Per-stage statistics
    per_stage: dict[str, dict] = {}
    for stage_name, metrics_list in sorted(stage_data.items()):
        tokens = [m.get("total_tokens", 0) for m in metrics_list]
        costs = [m.get("cost_usd", 0.0) for m in metrics_list]
        durations = [m.get("duration_seconds", 0.0) for m in metrics_list]
        calls = [m.get("llm_calls", 0) for m in metrics_list]
        failures = sum(1 for m in metrics_list if m.get("status") == "failed")

        per_stage[stage_name] = {
            "total_tokens": sum(tokens),
            "total_cost_usd": round(sum(costs), 6),
            "total_duration_seconds": round(sum(durations), 2),
            "total_llm_calls": sum(calls),
            "token_stats": _safe(tokens),
            "cost_stats": _safe(costs),
            "duration_stats": _safe(durations),
            "call_stats": _safe(calls),
            "failure_count": failures,
            "failure_rate": round(failures / len(metrics_list), 4) if metrics_list else 0,
        }

    # Overall totals
    all_tokens = [s["total_tokens"] for s in episode_summaries.values()]
    all_costs = [s["total_cost_usd"] for s in episode_summaries.values()]
    all_durations = [s["total_duration_seconds"] for s in episode_summaries.values()]
    total_failures = sum(1 for s in episode_summaries.values() if s["stages_failed"] > 0)

    aggregate = {
        "meta": {
            "generated_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
            "total_episodes": len(EPISODES),
            "episodes_with_metrics": len(episode_summaries),
            "episodes_with_failures": total_failures,
        },
        "summary": {
            "total_tokens": sum(all_tokens),
            "total_cost_usd": round(sum(all_costs), 6),
            "total_duration_seconds": round(sum(all_durations), 2),
            "total_llm_calls": sum(s["total_llm_calls"] for s in episode_summaries.values()),
            "token_stats": _safe(all_tokens),
            "cost_stats": _safe(all_costs),
            "duration_stats": _safe(all_durations),
        },
        "per_stage": per_stage,
        "per_episode": episode_summaries,
    }

    return aggregate


def write_csv(aggregate: dict, output_dir: Path) -> None:
    """Write stage durations as CSV."""
    rows = []
    for ep, summary in aggregate["per_episode"].items():
        metrics = load_metrics(ep)
        for stage_name, data in metrics.items():
            rows.append({
                "episode": ep,
                "stage": stage_name,
                "duration_seconds": data.get("duration_seconds", 0),
                "total_tokens": data.get("total_tokens", 0),
                "llm_calls": data.get("llm_calls", 0),
                "cost_usd": data.get("cost_usd", 0.0),
                "status": data.get("status", "unknown"),
            })

    if rows:
        path = output_dir / "durations.csv"
        with open(path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=rows[0].keys())
            w.writeheader()
            w.writerows(rows)
        print(f"  CSV: {path.relative_to(REPO_ROOT)} ({len(rows)} rows)")


def main() -> int:
    output_dir = REPO_ROOT / "benchmark_results"
    output_dir.mkdir(parents=True, exist_ok=True)

    print("Collecting metrics...")
    aggregate = collect()

    aggregate_path = output_dir / "aggregate.json"
    aggregate_path.write_text(json.dumps(aggregate, indent=2) + "\n")
    print(f"  WROTE: {aggregate_path.relative_to(REPO_ROOT)}")

    per_episode = aggregate["per_episode"]
    per_episode_path = output_dir / "per_episode.json"
    per_episode_path.write_text(json.dumps(per_episode, indent=2) + "\n")
    print(f"  WROTE: {per_episode_path.relative_to(REPO_ROOT)}")

    per_stage = {k: v for k, v in aggregate["per_stage"].items()}
    per_stage_path = output_dir / "per_stage.json"
    per_stage_path.write_text(json.dumps(per_stage, indent=2) + "\n")
    print(f"  WROTE: {per_stage_path.relative_to(REPO_ROOT)}")

    write_csv(aggregate, output_dir)

    # Print quick summary
    s = aggregate["summary"]
    print(f"\nSummary:")
    print(f"  Episodes with metrics: {aggregate['meta']['episodes_with_metrics']}")
    print(f"  Total tokens: {s['total_tokens']}")
    print(f"  Total cost:   ${s['total_cost_usd']:.6f}")
    print(f"  Total time:   {s['total_duration_seconds']:.1f}s")
    print(f"  Total calls:  {s['total_llm_calls']}")

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
