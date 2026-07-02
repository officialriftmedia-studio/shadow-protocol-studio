"""Pipeline summary report generation."""

from __future__ import annotations
from pathlib import Path

from shadow_protocol.lib.metrics import PipelineMetrics, StageMetrics


def generate_pipeline_summary(metrics: PipelineMetrics) -> str:
    """Generate a Markdown pipeline summary report from collected metrics."""

    lines: list[str] = []
    _add(lines, "# Pipeline Summary")
    _add(lines, f"**Case:** `{metrics.case_id}`")
    _add(lines, f"**Status:** {_status_badge(metrics.overall_status)}")
    _add(lines, f"**Duration:** {metrics.pipeline_duration_seconds:.1f}s")
    _add(lines, f"**Total LLM calls:** {metrics.total_llm_calls}")
    _add(lines, f"**Total tokens:** {metrics.total_tokens}")
    _add(lines, f"**Total cost:** ${metrics.total_cost_usd:.6f}")
    _add(lines, "")

    _add(lines, "---")
    _add(lines, "## Stage Breakdown")
    _add(lines, "")
    _add(lines, "| Stage | Status | Duration | LLM Calls | Prompt Tokens | Completion Tokens | Total Tokens | Cost |")
    _add(lines, "|-------|--------|----------|-----------|---------------|-------------------|--------------|------|")

    for s in metrics.stages:
        _add(lines, _stage_row(s))

    _add(lines, "")
    summary_row = (
        f"| **Total** | | **{metrics.pipeline_duration_seconds:.1f}s** | "
        f"{metrics.total_llm_calls} | | | {metrics.total_tokens} | ${metrics.total_cost_usd:.6f} |"
    )
    _add(lines, summary_row)
    _add(lines, "")

    _add(lines, "---")
    _add(lines, "## Token Usage by Stage")
    _add(lines, "")
    for s in metrics.stages:
        if s.total_tokens > 0:
            bar = _bar(s.total_tokens, metrics.total_tokens, 40)
            _add(lines, f"- **{s.stage}**: {s.total_tokens} tokens `{bar}`")

    _add(lines, "")
    _add(lines, "---")
    _add(lines, "## Cost Breakdown")
    _add(lines, "")
    for s in metrics.stages:
        if s.cost_usd > 0:
            _add(lines, f"- **{s.stage}**: ${s.cost_usd:.6f}")
    _add(lines, f"\n**Total:** ${metrics.total_cost_usd:.6f}")
    _add(lines, "")

    _add(lines, "---")
    _add(lines, "## Stage Details")
    _add(lines, "")
    for s in metrics.stages:
        _add(lines, f"### {s.stage}")
        _add(lines, f"- **Status:** {_status_badge(s.status)}")
        _add(lines, f"- **Duration:** {s.duration_seconds:.1f}s")
        _add(lines, f"- **LLM calls:** {s.llm_calls}")
        _add(lines, f"- **Tokens:** {s.total_tokens} (prompt={s.prompt_tokens} + completion={s.completion_tokens})")
        _add(lines, f"- **Cost:** ${s.cost_usd:.6f}")
        if s.output_files:
            _add(lines, "- **Output files:**")
            for f in s.output_files:
                _add(lines, f"  - `{f}`")
        if s.error:
            _add(lines, f"- **Error:** {s.error}")
        _add(lines, "")

    return "\n".join(lines)


def _add(lines: list[str], text: str) -> None:
    lines.append(text)


def _status_badge(status: str) -> str:
    badges = {
        "success": "✅ Success",
        "failed": "❌ Failed",
        "skipped": "⏭️ Skipped",
        "unknown": "❓ Unknown",
    }
    return badges.get(status, status)


def _stage_row(s: StageMetrics) -> str:
    dur = f"{s.duration_seconds:.1f}s" if s.duration_seconds else "-"
    calls = str(s.llm_calls) if s.llm_calls else "-"
    prompt_t = str(s.prompt_tokens) if s.prompt_tokens else "-"
    comp_t = str(s.completion_tokens) if s.completion_tokens else "-"
    total_t = str(s.total_tokens) if s.total_tokens else "-"
    cost = f"${s.cost_usd:.6f}" if s.cost_usd else "-"
    badge = _status_badge(s.status)
    return f"| `{s.stage}` | {badge} | {dur} | {calls} | {prompt_t} | {comp_t} | {total_t} | {cost} |"


def _bar(value: int, total: int, width: int = 40) -> str:
    if total == 0:
        return "▏" + " " * (width - 1)
    filled = max(1, int(value / total * width))
    empty = width - filled
    return "█" * filled + "░" * empty
