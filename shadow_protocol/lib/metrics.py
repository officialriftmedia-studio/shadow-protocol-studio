"""Structured metrics collection for pipeline stages."""

from __future__ import annotations
import json
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class StageMetrics:
    stage: str
    status: str = "unknown"
    start_time: str = ""
    end_time: str = ""
    duration_seconds: float = 0.0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    llm_calls: int = 0
    cost_usd: float = 0.0
    output_files: list[str] = field(default_factory=list)
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> StageMetrics:
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class PipelineMetrics:
    case_id: str
    stages: list[StageMetrics] = field(default_factory=list)
    pipeline_start: str = ""
    pipeline_end: str = ""
    pipeline_duration_seconds: float = 0.0
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    total_llm_calls: int = 0
    overall_status: str = "unknown"

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "pipeline_start": self.pipeline_start,
            "pipeline_end": self.pipeline_end,
            "pipeline_duration_seconds": round(self.pipeline_duration_seconds, 2),
            "total_tokens": self.total_tokens,
            "total_cost_usd": round(self.total_cost_usd, 6),
            "total_llm_calls": self.total_llm_calls,
            "overall_status": self.overall_status,
            "stages": [s.to_dict() for s in self.stages],
        }


class MetricsCollector:
    """Collects and persists per-stage metrics during pipeline execution."""

    def __init__(self, case_id: str, metrics_dir: str | Path):
        self.case_id = case_id
        self.metrics_dir = Path(metrics_dir)
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        self._stages: dict[str, StageMetrics] = {}
        self._pipeline_start: str | None = None

    def start_pipeline(self) -> None:
        self._pipeline_start = _now()

    def start_stage(self, stage: str) -> None:
        m = StageMetrics(stage=stage, start_time=_now())
        self._stages[stage] = m

    def end_stage(
        self,
        stage: str,
        status: str = "success",
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        llm_calls: int = 0,
        cost_usd: float = 0.0,
        output_files: list[str] | None = None,
        error: str | None = None,
    ) -> StageMetrics:
        m = self._stages.get(stage)
        if m is None:
            m = StageMetrics(stage=stage)
            self._stages[stage] = m
        m.end_time = _now()
        m.status = status
        m.prompt_tokens = prompt_tokens
        m.completion_tokens = completion_tokens
        m.total_tokens = prompt_tokens + completion_tokens
        m.llm_calls = llm_calls
        m.cost_usd = round(cost_usd, 6)
        m.output_files = output_files or []
        m.error = error
        dur = _parse_time(m.end_time) - _parse_time(m.start_time)
        m.duration_seconds = round(max(dur, 0.0), 2)
        self._save_stage(m)
        return m

    def skip_stage(self, stage: str) -> StageMetrics:
        m = StageMetrics(
            stage=stage,
            status="skipped",
            start_time=_now(),
            end_time=_now(),
        )
        self._stages[stage] = m
        self._save_stage(m)
        return m

    def pipeline_summary(self) -> PipelineMetrics:
        end = _now()
        start = self._pipeline_start or end
        dur = max(_parse_time(end) - _parse_time(start), 0.0)

        total_tokens = sum(s.total_tokens for s in self._stages.values())
        total_cost = sum(s.cost_usd for s in self._stages.values())
        total_calls = sum(s.llm_calls for s in self._stages.values())
        has_failure = any(s.status == "failed" for s in self._stages.values())

        return PipelineMetrics(
            case_id=self.case_id,
            stages=list(self._stages.values()),
            pipeline_start=start,
            pipeline_end=end,
            pipeline_duration_seconds=round(dur, 2),
            total_tokens=total_tokens,
            total_cost_usd=round(total_cost, 6),
            total_llm_calls=total_calls,
            overall_status="failed" if has_failure else "success",
        )

    def _save_stage(self, m: StageMetrics) -> None:
        path = self.metrics_dir / f"{m.stage}.json"
        with open(path, "w") as f:
            json.dump(m.to_dict(), f, indent=2)
            f.write("\n")

    def load_stage(self, stage: str) -> StageMetrics | None:
        path = self.metrics_dir / f"{stage}.json"
        if path.exists():
            with open(path) as f:
                return StageMetrics.from_dict(json.load(f))
        return None


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_time(ts: str) -> float:
    try:
        return datetime.fromisoformat(ts).timestamp()
    except Exception:
        return 0.0
