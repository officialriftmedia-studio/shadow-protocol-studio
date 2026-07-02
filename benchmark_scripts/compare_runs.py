#!/usr/bin/env python3
"""Compare two benchmark runs and produce a diff report.

Usage:
    python benchmark_scripts/compare_runs.py benchmark_results/ baseline/benchmark_results/

Compares:
    - Total cost, tokens, duration
    - Per-stage cost, tokens, duration (absolute and % change)
    - Per-episode metrics
    - Flags regressions (>10% increase in cost or duration)
"""

from __future__ import annotations
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent


def _pct_change(old: float, new: float) -> str:
    if old == 0:
        return "—"
    change = (new - old) / old * 100
    sign = "+" if change > 0 else ""
    return f"{sign}{change:.1f}%"


def _cost_usd(v: float) -> str:
    return f"${v:.6f}"


def _regression_badge(change_str: str) -> str:
    if change_str in ("—", ""):
        return ""
    try:
        val = float(change_str.replace("%", "").replace("+", ""))
        if val > 10:
            return " 🔴"
        elif val > 5:
            return " 🟡"
        elif val < -10:
            return " 🟢"
        elif val < -5:
            return " 🔵"
    except ValueError:
        pass
    return ""


def main() -> int:
    if len(sys.argv) < 3:
        print("Usage: compare_runs.py <run_a_dir> <run_b_dir>")
        print("Example: compare_runs.py benchmark_results/ baseline/benchmark_results/")
        return 1

    run_a_dir = Path(sys.argv[1])
    run_b_dir = Path(sys.argv[2])

    agg_a_path = run_a_dir / "aggregate.json"
    agg_b_path = run_b_dir / "aggregate.json"

    if not agg_a_path.exists():
        print(f"Not found: {agg_a_path}")
        return 1
    if not agg_b_path.exists():
        print(f"Not found: {agg_b_path}")
        return 1

    agg_a = json.loads(agg_a_path.read_text())
    agg_b = json.loads(agg_b_path.read_text())

    lines: list[str] = []
    lines.append("# Benchmark Run Comparison\n")
    lines.append(f"| | Run A | Run B | Change |")
    lines.append(f"|---|-------|-------|--------|")

    s_a = agg_a["summary"]
    s_b = agg_b["summary"]
    lines.append(f"| **Total Tokens** | {s_a['total_tokens']} | {s_b['total_tokens']} | {_pct_change(s_a['total_tokens'], s_b['total_tokens'])} |")
    lines.append(f"| **Total Cost** | {_cost_usd(s_a['total_cost_usd'])} | {_cost_usd(s_b['total_cost_usd'])} | {_pct_change(s_a['total_cost_usd'], s_b['total_cost_usd'])} |")
    lines.append(f"| **Total Duration** | {s_a['total_duration_seconds']:.1f}s | {s_b['total_duration_seconds']:.1f}s | {_pct_change(s_a['total_duration_seconds'], s_b['total_duration_seconds'])} |")
    lines.append(f"| **Total LLM Calls** | {s_a['total_llm_calls']} | {s_b['total_llm_calls']} | {_pct_change(s_a['total_llm_calls'], s_b['total_llm_calls'])} |")
    lines.append("")

    # Per-stage comparison
    lines.append("## Stage Comparison\n")
    lines.append("| Stage | A Cost | B Cost | Cost Δ | A Duration | B Duration | Duration Δ |")
    lines.append("|-------|--------|--------|--------|------------|------------|------------|")
    all_stages = sorted(set(list(agg_a["per_stage"].keys()) + list(agg_b["per_stage"].keys())))
    for stage in all_stages:
        a_data = agg_a["per_stage"].get(stage, {})
        b_data = agg_b["per_stage"].get(stage, {})
        a_cost = a_data.get("total_cost_usd", 0)
        b_cost = b_data.get("total_cost_usd", 0)
        a_dur = a_data.get("total_duration_seconds", 0)
        b_dur = b_data.get("total_duration_seconds", 0)
        cost_change = _pct_change(a_cost, b_cost)
        dur_change = _pct_change(a_dur, b_dur)
        badge = _regression_badge(cost_change) or _regression_badge(dur_change)
        lines.append(
            f"| `{stage}`{badge} "
            f"| {_cost_usd(a_cost)} | {_cost_usd(b_cost)} | {cost_change} "
            f"| {a_dur:.1f}s | {b_dur:.1f}s | {dur_change} |"
        )
    lines.append("")

    # Per-episode comparison
    lines.append("## Episode Comparison\n")
    lines.append("| Episode | A Cost | B Cost | Cost Δ | A Duration | B Duration | Duration Δ |")
    lines.append("|---------|--------|--------|--------|------------|------------|------------|")
    all_eps = sorted(set(list(agg_a["per_episode"].keys()) + list(agg_b["per_episode"].keys())))
    for ep in all_eps:
        a_data = agg_a["per_episode"].get(ep, {})
        b_data = agg_b["per_episode"].get(ep, {})
        a_cost = a_data.get("total_cost_usd", 0)
        b_cost = b_data.get("total_cost_usd", 0)
        a_dur = a_data.get("total_duration_seconds", 0)
        b_dur = b_data.get("total_duration_seconds", 0)
        cost_change = _pct_change(a_cost, b_cost)
        dur_change = _pct_change(a_dur, b_dur)
        badge = _regression_badge(cost_change) or _regression_badge(dur_change)
        lines.append(
            f"| {ep}{badge} "
            f"| {_cost_usd(a_cost)} | {_cost_usd(b_cost)} | {cost_change} "
            f"| {a_dur:.1f}s | {b_dur:.1f}s | {dur_change} |"
        )
    lines.append("")

    report_text = "\n".join(lines)

    output_path = REPO_ROOT / "benchmark_results" / "comparison_report.md"
    output_path.write_text(report_text)
    print(f"  WROTE: {output_path.relative_to(REPO_ROOT)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
