#!/usr/bin/env python3
"""Generate a comprehensive benchmark report from collected metrics.

Reads aggregate.json from benchmark_results/ and produces:
    benchmark_results/benchmark_report.md    — Full report with tables, charts, analysis
"""

from __future__ import annotations
import json
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent


STAGE_WORKFLOW_MAP = {
    "production_package": "WF1: Script Generation",
    "outline": "WF1: Script Generation",
    "script": "WF1: Script Generation",
    "script_review": "WF1: Script Generation",
    "scene_breakdown": "WF2: Production Assets",
    "image_prompt": "WF2: Production Assets",
    "video_prompt": "WF2: Production Assets",
    "voiceover": "WF2: Production Assets",
    "metadata": "WF2: Production Assets",
    "thumbnail": "WF2: Production Assets",
    "image_generator": "WF3: Media Generation",
    "voice_generator": "WF3: Media Generation",
    "timeline_builder": "WF4: Video Assembly",
    "render_builder": "WF4: Video Assembly",
    "render_executor": "WF4: Video Assembly",
    "publish_package_builder": "WF5: Publishing",
    "quality_control": "WF5: Publishing",
    "release_manager": "WF5: Publishing",
}


def _bar(value: float, total: float, width: int = 30) -> str:
    if total == 0:
        return "▏" + "░" * (width - 1)
    filled = max(1, int(value / total * width))
    empty = width - filled
    return "█" * filled + "░" * empty


def _pct(value: float, total: float) -> str:
    if total == 0:
        return "—"
    return f"{value / total * 100:.1f}%"


def _cost_usd(v: float) -> str:
    return f"${v:.6f}"


def generate_report(aggregate: dict) -> str:
    lines: list[str] = []

    meta = aggregate["meta"]
    summary = aggregate["summary"]
    per_stage = aggregate["per_stage"]
    per_episode = aggregate["per_episode"]

    lines.append("# Benchmark Report\n")
    lines.append(f"**Generated:** {meta['generated_at']}")
    lines.append(f"**Episodes:** {meta['total_episodes']} ({meta['episodes_with_metrics']} with metrics, {meta['episodes_with_failures']} with failures)")
    lines.append("")
    lines.append("---\n")

    # ── Executive Summary ────────────────────────────────────────────
    lines.append("## Executive Summary\n")
    lines.append(f"| Metric | Value |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Total Tokens | {summary['total_tokens']} |")
    lines.append(f"| Total Cost | {_cost_usd(summary['total_cost_usd'])} |")
    lines.append(f"| Total Duration | {summary['total_duration_seconds']:.1f}s ({summary['total_duration_seconds']/3600:.2f}h) |")
    lines.append(f"| Total LLM Calls | {summary['total_llm_calls']} |")
    lines.append(f"| Avg Tokens/Episode | {summary['token_stats']['mean']:.0f} |")
    lines.append(f"| Avg Cost/Episode | {_cost_usd(summary['cost_stats']['mean'])} |")
    lines.append(f"| Avg Duration/Episode | {summary['duration_stats']['mean']:.1f}s |")
    lines.append(f"| Max Cost/Episode | {_cost_usd(summary['cost_stats']['max'])} |")
    lines.append(f"| Min Cost/Episode | {_cost_usd(summary['cost_stats']['min'])} |")
    lines.append("")

    # ── Cost Distribution ────────────────────────────────────────────
    lines.append("### Cost Distribution\n")
    cost_total = summary["total_cost_usd"]
    for stage_name, data in sorted(per_stage.items()):
        stage_cost = data["total_cost_usd"]
        if stage_cost > 0:
            lines.append(f"- **{stage_name}**: {_cost_usd(stage_cost)} {_bar(stage_cost, cost_total)} {_pct(stage_cost, cost_total)}")
    lines.append(f"\n**Total:** {_cost_usd(cost_total)}\n")

    # ── Token Distribution ───────────────────────────────────────────
    lines.append("### Token Distribution\n")
    token_total = summary["total_tokens"]
    for stage_name, data in sorted(per_stage.items()):
        stage_tokens = data["total_tokens"]
        if stage_tokens > 0:
            lines.append(f"- **{stage_name}**: {stage_tokens} tokens {_bar(stage_tokens, token_total)} {_pct(stage_tokens, token_total)}")
    lines.append(f"\n**Total:** {token_total} tokens\n")

    # ── Per-Workflow Summary ─────────────────────────────────────────
    lines.append("## By Workflow\n")
    wf_totals: dict[str, dict] = {}
    for stage_name, data in per_stage.items():
        wf = STAGE_WORKFLOW_MAP.get(stage_name, "Other")
        if wf not in wf_totals:
            wf_totals[wf] = {"tokens": 0, "cost": 0.0, "duration": 0.0, "calls": 0}
        wf_totals[wf]["tokens"] += data["total_tokens"]
        wf_totals[wf]["cost"] += data["total_cost_usd"]
        wf_totals[wf]["duration"] += data["total_duration_seconds"]
        wf_totals[wf]["calls"] += data["total_llm_calls"]

    lines.append("| Workflow | Tokens | Cost | Duration | LLM Calls |")
    lines.append("|----------|--------|------|----------|-----------|")
    for wf, data in sorted(wf_totals.items()):
        lines.append(f"| {wf} | {data['tokens']} | {_cost_usd(data['cost'])} | {data['duration']:.1f}s | {data['calls']} |")
    lines.append("")

    # ── Per-Stage Statistics ─────────────────────────────────────────
    lines.append("## Stage Statistics\n")
    lines.append("| Stage | WF | Mean Tokens | Mean Cost | Mean Duration | p95 Duration | Failure Rate | Calls |")
    lines.append("|-------|----|-------------|-----------|---------------|--------------|--------------|-------|")
    for stage_name, data in sorted(per_stage.items()):
        wf = STAGE_WORKFLOW_MAP.get(stage_name, "?")
        s = data
        lines.append(
            f"| `{stage_name}` | {wf} "
            f"| {s['token_stats']['mean']:.0f} "
            f"| {_cost_usd(s['cost_stats']['mean'])} "
            f"| {s['duration_stats']['mean']:.1f}s "
            f"| {s['duration_stats']['p95']:.1f}s "
            f"| {s['failure_rate']*100:.1f}% "
            f"| {s['call_stats']['mean']:.1f} |"
        )
    lines.append("")

    # ── Per-Episode Comparison ───────────────────────────────────────
    lines.append("## Episode Comparison\n")
    lines.append("| Episode | Tokens | Cost | Duration | Stages | Failures |")
    lines.append("|---------|--------|------|----------|--------|----------|")
    for ep in sorted(per_episode.keys()):
        e = per_episode[ep]
        lines.append(
            f"| {ep} | {e['total_tokens']} "
            f"| {_cost_usd(e['total_cost_usd'])} "
            f"| {e['total_duration_seconds']:.1f}s "
            f"| {e['stage_count']} "
            f"| {e['stages_failed']} |"
        )
    lines.append("")

    # ── Variance Analysis (Top 5 most variable stages) ───────────────
    lines.append("## Variance Analysis\n")
    lines.append("Stages with the highest duration variance — potential optimization targets:\n")
    by_variance = sorted(
        per_stage.items(),
        key=lambda x: x[1]["duration_stats"]["stddev"],
        reverse=True,
    )
    lines.append("| Stage | Mean Duration | Std Dev | CV (%) |")
    lines.append("|-------|--------------|---------|--------|")
    for stage_name, data in by_variance[:5]:
        mean_d = data["duration_stats"]["mean"]
        std_d = data["duration_stats"]["stddev"]
        cv = (std_d / mean_d * 100) if mean_d > 0 else 0
        lines.append(f"| `{stage_name}` | {mean_d:.1f}s | {std_d:.1f}s | {cv:.1f}% |")
    lines.append("")

    # ── Failure Analysis ─────────────────────────────────────────────
    lines.append("## Failures\n")
    failures = [(s, d) for s, d in per_stage.items() if d["failure_count"] > 0]
    if failures:
        lines.append("| Stage | Failure Count | Failure Rate |")
        lines.append("|-------|--------------|--------------|")
        for stage_name, data in failures:
            lines.append(f"| `{stage_name}` | {data['failure_count']} | {data['failure_rate']*100:.1f}% |")
    else:
        lines.append("_No failures recorded across all episodes._")
    lines.append("")

    # ── Recommendations ──────────────────────────────────────────────
    lines.append("## Optimization Recommendations\n")

    # Find the most expensive stages
    by_cost = sorted(per_stage.items(), key=lambda x: x[1]["total_cost_usd"], reverse=True)
    top_cost_stage = by_cost[0][0] if by_cost else "N/A"
    top_cost_data = by_cost[0][1] if by_cost else None

    if top_cost_data:
        lines.append(f"1. **Reduce {top_cost_stage} costs** ({_cost_usd(top_cost_data['total_cost_usd'])})")
        lines.append(f"   - Consider: prompt compression, shorter outputs, cheaper model variant.")
        lines.append(f"   - Potential savings: ~{_pct(top_cost_data['total_cost_usd'], summary['total_cost_usd'])} of total cost.\n")

    # Slowest stages
    by_duration = sorted(per_stage.items(), key=lambda x: x[1]["duration_stats"]["mean"], reverse=True)
    if by_duration:
        slow_stage = by_duration[0][0]
        slow_data = by_duration[0][1]
        lines.append(f"2. **Optimize {slow_stage} duration** (mean {slow_data['duration_stats']['mean']:.1f}s)")
        lines.append(f"   - Consider: parallel execution, timeout tuning, LLM response streaming.")
        lines.append(f"   - Impact: reduces per-episode pipeline time.\n")

    # High-variance stages
    if by_variance and by_variance[0][1]["duration_stats"]["stddev"] > 0:
        var_stage = by_variance[0][0]
        var_data = by_variance[0][1]
        lines.append(f"3. **Stabilize {var_stage} duration** (CV={var_data['duration_stats']['stddev']/max(var_data['duration_stats']['mean'], 0.01)*100:.0f}%)")
        lines.append(f"   - High variance suggests dependency on input complexity or LLM variability.")
        lines.append(f"   - Consider: fixed iteration limits, timeout floors, retry budget caps.\n")

    lines.append("## Raw Data\n")
    lines.append("- `benchmark_results/aggregate.json` — Full metrics")
    lines.append("- `benchmark_results/per_episode.json` — Per-episode summaries")
    lines.append("- `benchmark_results/per_stage.json` — Per-stage statistics")
    lines.append("- `benchmark_results/durations.csv` — Duration CSV for external analysis")
    lines.append("- `benchmark_results/environment.json` — Runtime environment metadata")
    lines.append("")

    return "\n".join(lines)


def main() -> int:
    aggregate_path = REPO_ROOT / "benchmark_results" / "aggregate.json"
    if not aggregate_path.exists():
        print("No aggregate.json found. Run collect_metrics.py first.")
        return 1

    aggregate = json.loads(aggregate_path.read_text())
    report = generate_report(aggregate)

    output_path = REPO_ROOT / "benchmark_results" / "benchmark_report.md"
    output_path.write_text(report)
    print(f"  WROTE: {output_path.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
