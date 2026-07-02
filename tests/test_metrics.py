"""Tests for metrics collection and reporting."""

import json
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).parent.parent))

from shadow_protocol.lib.metrics import MetricsCollector, StageMetrics, PipelineMetrics


def test_metrics_collector_creates_dir():
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp) / "metrics"
        c = MetricsCollector("case_001", d)
        assert d.exists()


def test_stage_lifecycle():
    with tempfile.TemporaryDirectory() as tmp:
        c = MetricsCollector("case_001", Path(tmp))
        c.start_pipeline()
        c.start_stage("test_stage")
        c.end_stage("test_stage", status="success", prompt_tokens=100, completion_tokens=50, llm_calls=2, cost_usd=0.005)

        m = c.load_stage("test_stage")
        assert m is not None
        assert m.stage == "test_stage"
        assert m.status == "success"
        assert m.prompt_tokens == 100
        assert m.completion_tokens == 50
        assert m.total_tokens == 150
        assert m.llm_calls == 2
        assert m.cost_usd == 0.005
        assert m.duration_seconds >= 0


def test_skip_stage():
    with tempfile.TemporaryDirectory() as tmp:
        c = MetricsCollector("case_001", Path(tmp))
        c.start_pipeline()
        c.skip_stage("skipped_stage")

        m = c.load_stage("skipped_stage")
        assert m is not None
        assert m.status == "skipped"


def test_failed_stage():
    with tempfile.TemporaryDirectory() as tmp:
        c = MetricsCollector("case_001", Path(tmp))
        c.start_pipeline()
        c.start_stage("fail_stage")
        c.end_stage("fail_stage", status="failed", error="Something broke")

        m = c.load_stage("fail_stage")
        assert m is not None
        assert m.status == "failed"
        assert m.error == "Something broke"


def test_pipeline_summary_success():
    with tempfile.TemporaryDirectory() as tmp:
        c = MetricsCollector("case_001", Path(tmp))
        c.start_pipeline()
        c.start_stage("s1")
        c.end_stage("s1", status="success", prompt_tokens=100, completion_tokens=50, llm_calls=1, cost_usd=0.003)
        c.start_stage("s2")
        c.end_stage("s2", status="success", prompt_tokens=50, completion_tokens=25, llm_calls=1, cost_usd=0.0015)

        summary = c.pipeline_summary()
        assert summary.case_id == "case_001"
        assert summary.overall_status == "success"
        assert summary.total_tokens == 225
        assert summary.total_llm_calls == 2
        assert summary.total_cost_usd == 0.0045
        assert len(summary.stages) == 2


def test_pipeline_summary_failure():
    with tempfile.TemporaryDirectory() as tmp:
        c = MetricsCollector("case_001", Path(tmp))
        c.start_pipeline()
        c.start_stage("s1")
        c.end_stage("s1", status="success")
        c.start_stage("s2")
        c.end_stage("s2", status="failed", error="fail")

        summary = c.pipeline_summary()
        assert summary.overall_status == "failed"


def test_metrics_persisted_to_disk():
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        c = MetricsCollector("case_001", d)
        c.start_pipeline()
        c.start_stage("disk_stage")
        c.end_stage("disk_stage", status="success")

        # Verify file exists and is valid JSON
        path = d / "disk_stage.json"
        assert path.exists()
        data = json.loads(path.read_text())
        assert data["stage"] == "disk_stage"
        assert data["status"] == "success"


def test_stage_metrics_to_dict():
    m = StageMetrics(stage="test", status="success", prompt_tokens=10, total_tokens=10)
    d = m.to_dict()
    assert d["stage"] == "test"
    assert d["prompt_tokens"] == 10


def test_stage_metrics_from_dict():
    d = {"stage": "test", "status": "success", "prompt_tokens": 10}
    m = StageMetrics.from_dict(d)
    assert m.stage == "test"
    assert m.prompt_tokens == 10
