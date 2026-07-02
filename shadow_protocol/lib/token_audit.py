"""Token Audit — per-call LLM token tracking with persistence and reporting."""

from __future__ import annotations
import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class AuditEntry:
    stage: str = ""
    agent: str = ""
    provider: str = ""
    model: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    context_files: list[str] = field(default_factory=list)
    prompt_size_bytes: int = 0
    duration_seconds: float = 0.0
    timestamp: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class TokenAudit:
    def __init__(self, case_id: str, metrics_dir: str | Path):
        self.case_id = case_id
        self.metrics_dir = Path(metrics_dir)
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        self._entries: list[AuditEntry] = []

    def record(
        self,
        stage: str,
        agent: str,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        context_files: list[str] | None = None,
        prompt_size_bytes: int = 0,
        duration_seconds: float = 0.0,
    ) -> None:
        entry = AuditEntry(
            stage=stage,
            agent=agent,
            provider=provider,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            context_files=context_files or [],
            prompt_size_bytes=prompt_size_bytes,
            duration_seconds=round(duration_seconds, 2),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        self._entries.append(entry)
        self._save()

    def _save(self) -> None:
        path = self.metrics_dir / "token_audit.json"
        data = [e.to_dict() for e in self._entries]
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
            f.write("\n")

    def summary(self) -> dict[str, Any]:
        if not self._entries:
            return {}
        total_in = sum(e.input_tokens for e in self._entries)
        total_out = sum(e.output_tokens for e in self._entries)
        return {
            "total_calls": len(self._entries),
            "total_input_tokens": total_in,
            "total_output_tokens": total_out,
            "total_tokens": total_in + total_out,
            "avg_input_per_call": round(total_in / len(self._entries), 1),
            "avg_output_per_call": round(total_out / len(self._entries), 1),
            "by_stage": self._by_stage(),
        }

    def _by_stage(self) -> dict[str, dict[str, int]]:
        stages: dict[str, dict[str, int]] = {}
        for e in self._entries:
            s = stages.setdefault(e.stage, {"calls": 0, "input_tokens": 0, "output_tokens": 0, "total_tokens": 0})
            s["calls"] += 1
            s["input_tokens"] += e.input_tokens
            s["output_tokens"] += e.output_tokens
            s["total_tokens"] += e.total_tokens
        return stages


def generate_token_report(audit: TokenAudit, output_path: str | Path) -> str:
    summary = audit.summary()
    if not summary:
        report = "# Token Audit Report\n\nNo LLM calls recorded.\n"
        Path(output_path).write_text(report)
        return report

    lines: list[str] = []
    lines.append("# Token Audit Report\n")
    lines.append(f"**Generated:** {datetime.now(timezone.utc).isoformat()}")
    lines.append(f"**Total LLM Calls:** {summary['total_calls']}")
    lines.append(f"**Total Input Tokens:** {summary['total_input_tokens']}")
    lines.append(f"**Total Output Tokens:** {summary['total_output_tokens']}")
    lines.append(f"**Total Tokens:** {summary['total_tokens']}")
    lines.append(f"**Avg Input per Call:** {summary['avg_input_per_call']}")
    lines.append(f"**Avg Output per Call:** {summary['avg_output_per_call']}")
    lines.append("")

    lines.append("## Per-Stage Breakdown\n")
    lines.append("| Stage | Calls | Input Tokens | Output Tokens | Total Tokens |")
    lines.append("|-------|-------|-------------|--------------|-------------|")
    for stage, data in sorted(summary["by_stage"].items()):
        lines.append(f"| {stage} | {data['calls']} | {data['input_tokens']} | {data['output_tokens']} | {data['total_tokens']} |")
    lines.append("")

    lines.append("## All Calls\n")
    lines.append("| # | Stage | Provider | Model | Input | Output | Total | Files |")
    lines.append("|---|-------|----------|-------|-------|--------|-------|-------|")
    for i, entry in enumerate(audit._entries, 1):
        files = ", ".join(entry.context_files[:3])
        if len(entry.context_files) > 3:
            files += f" (+{len(entry.context_files)-3})"
        lines.append(f"| {i} | {entry.stage} | {entry.provider} | {entry.model} | {entry.input_tokens} | {entry.output_tokens} | {entry.total_tokens} | {files} |")
    lines.append("")

    report = "\n".join(lines)
    Path(output_path).write_text(report)
    return report
