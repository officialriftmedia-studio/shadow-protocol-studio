"""Tests for pipeline summary reporting."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from shadow_protocol.lib.metrics import MetricsCollector, PipelineMetrics, StageMetrics
from shadow_protocol.lib.reporting import generate_pipeline_summary


def test_generate_summary_creates_markdown():
    metrics = PipelineMetrics(
        case_id="case_001",
        pipeline_start="2026-01-01T00:00:00",
        pipeline_end="2026-01-01T00:01:00",
        pipeline_duration_seconds=60.0,
        total_tokens=500,
        total_cost_usd=0.015,
        total_llm_calls=3,
        overall_status="success",
        stages=[
            StageMetrics(stage="s1", status="success", duration_seconds=30.0, prompt_tokens=200, completion_tokens=100, total_tokens=300, llm_calls=2, cost_usd=0.01),
            StageMetrics(stage="s2", status="success", duration_seconds=30.0, prompt_tokens=100, completion_tokens=100, total_tokens=200, llm_calls=1, cost_usd=0.005),
        ],
    )

    report = generate_pipeline_summary(metrics)
    assert "# Pipeline Summary" in report
    assert "case_001" in report
    assert "500" in report
    assert "$0.015" in report
    assert "3" in report
    assert "s1" in report
    assert "s2" in report
    assert "✅" in report


def test_generate_summary_failed():
    metrics = PipelineMetrics(
        case_id="case_002",
        overall_status="failed",
        stages=[
            StageMetrics(stage="s1", status="failed", error="crash"),
        ],
    )

    report = generate_pipeline_summary(metrics)
    assert "❌" in report
    assert "crash" in report


def test_generate_summary_empty_stages():
    metrics = PipelineMetrics(case_id="empty")
    report = generate_pipeline_summary(metrics)
    assert "# Pipeline Summary" in report
    assert "❓" in report  # unknown status badge
