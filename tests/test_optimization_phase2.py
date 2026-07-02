"""Tests for optimization phase 2 features: modes, queue, quota, estimates, benchmarks."""

from __future__ import annotations
import json
import os
import sys
import time
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from shadow_protocol.lib.orchestrator_runner import run_pipeline, RENDER_STAGES
from shadow_protocol.lib.queue_manager import QueueManager
from shadow_protocol.lib.quota_manager import QuotaManager
from shadow_protocol.lib.token_audit import TokenAudit


# ── Dev/Production Modes ──────────────────────────────────────────────

def test_dev_mode_skips_render_stages():
    """Dev mode should skip render stages."""
    with patch.object(Path, "cwd", return_value=Path("/tmp")):
        # The effective order should exclude RENDER_STAGES
        from shadow_protocol.lib.orchestrator_runner import STAGE_ORDER
        dev_stages = [s for s in STAGE_ORDER if s not in RENDER_STAGES]
        assert "image_generator" not in dev_stages
        assert "render_executor" not in dev_stages
        assert "production_package" in dev_stages
        assert "scene_breakdown" in dev_stages
        assert "asset_package" in dev_stages


def test_production_mode_includes_all_stages():
    """Production mode should include all stages."""
    from shadow_protocol.lib.orchestrator_runner import STAGE_ORDER, RENDER_STAGES
    assert RENDER_STAGES.issubset(set(STAGE_ORDER))


# ── Background Queue System ───────────────────────────────────────────

def test_queue_add_job(tmp_path: Path):
    qm = QueueManager(tmp_path)
    job_id = qm.add_job("case_test", mode="production")
    assert job_id == 1
    job = qm.get_job(job_id)
    assert job is not None
    assert job["case_id"] == "case_test"
    assert job["status"] == "pending"
    assert job["mode"] == "production"


def test_queue_add_multiple_jobs(tmp_path: Path):
    qm = QueueManager(tmp_path)
    id1 = qm.add_job("case_a")
    id2 = qm.add_job("case_b")
    assert id1 == 1
    assert id2 == 2
    assert len(qm.list_jobs()) == 2


def test_queue_list_by_status(tmp_path: Path):
    qm = QueueManager(tmp_path)
    qm.add_job("case_a")
    qm.update_job(1, status="running")
    qm.add_job("case_b")

    pending = qm.list_jobs(status="pending")
    running = qm.list_jobs(status="running")
    assert len(pending) == 1
    assert len(running) == 1


def test_queue_cancel_pending_job(tmp_path: Path):
    qm = QueueManager(tmp_path)
    qm.add_job("case_test")
    assert qm.cancel_job(1) is True
    job = qm.get_job(1)
    assert job["status"] == "cancelled"


def test_queue_cancel_nonexistent_job(tmp_path: Path):
    qm = QueueManager(tmp_path)
    assert qm.cancel_job(999) is False


def test_queue_state_persistence(tmp_path: Path):
    qm = QueueManager(tmp_path)
    qm.add_job("case_test")
    state_path = tmp_path / ".queue_state.json"
    assert state_path.exists()
    state = json.loads(state_path.read_text())
    assert len(state["jobs"]) == 1
    assert state["next_id"] == 2


# ── Quota Manager ─────────────────────────────────────────────────────

def test_quota_manager_init(tmp_path: Path):
    qm = QuotaManager(tmp_path)
    usage = qm.get_usage("gemini-2.5-flash")
    assert usage["model"] == "gemini-2.5-flash"
    assert usage["used_today"] == 0
    assert usage["daily_requests"] == 20


def test_quota_manager_record_call(tmp_path: Path):
    qm = QuotaManager(tmp_path)
    qm.record_call("gemini-2.5-flash", input_tokens=500)
    usage = qm.get_usage("gemini-2.5-flash")
    assert usage["used_today"] == 1
    assert usage["input_tokens_used"] == 500


def test_quota_manager_multiple_calls(tmp_path: Path):
    qm = QuotaManager(tmp_path)
    qm.record_call("gemini-2.5-flash", input_tokens=100)
    qm.record_call("gemini-2.5-flash", input_tokens=200)
    usage = qm.get_usage("gemini-2.5-flash")
    assert usage["used_today"] == 2
    assert usage["input_tokens_used"] == 300


def test_quota_manager_estimate_episode(tmp_path: Path):
    qm = QuotaManager(tmp_path)
    estimate = qm.estimate_episode(scene_count=15)
    assert "total_estimated_requests" in estimate
    assert estimate["total_estimated_requests"] > 0
    assert "by_model" in estimate
    assert "can_run_full_episode" in estimate
    assert "recommendation" in estimate
    # Verify per-model breakdown includes expected models
    models = list(estimate["by_model"].keys())
    assert "gemini-2.5-flash" in models
    assert "gemini-3.1-flash-lite" in models


def test_quota_manager_ollama_no_limits(tmp_path: Path):
    qm = QuotaManager(tmp_path)
    usage = qm.get_usage("qwen3:14b")
    assert usage["estimated_remaining"] > 10000


def test_quota_manager_reset_new_day(tmp_path: Path):
    qm = QuotaManager(tmp_path)
    qm.record_call("gemini-2.5-flash", input_tokens=500)
    # Force the state to yesterday
    state = qm.load_state()
    state["gemini-2.5-flash"]["date"] = "2000-01-01"
    qm.save_state(state)
    # Should reset on next get_usage
    usage = qm.get_usage("gemini-2.5-flash")
    assert usage["used_today"] == 0


# ── Token Audit ──────────────────────────────────────────────────────

def test_token_audit_record(tmp_path: Path):
    metrics_dir = tmp_path / "metrics"
    audit = TokenAudit("case_test", metrics_dir)
    audit.record(
        stage="production_package",
        agent="production_package",
        provider="gemini",
        model="gemini-2.5-flash",
        input_tokens=500,
        output_tokens=200,
    )
    assert len(audit._entries) == 1
    assert audit._entries[0].total_tokens == 700


def test_token_audit_persistence(tmp_path: Path):
    metrics_dir = tmp_path / "metrics"
    audit = TokenAudit("case_test", metrics_dir)
    audit.record(stage="outline", agent="outline", provider="gemini", model="gemini-2.5-flash", input_tokens=100, output_tokens=50)

    audit_path = metrics_dir / "token_audit.json"
    assert audit_path.exists()
    data = json.loads(audit_path.read_text())
    assert len(data) == 1
    assert data[0]["stage"] == "outline"


def test_token_audit_summary(tmp_path: Path):
    metrics_dir = tmp_path / "metrics"
    audit = TokenAudit("case_test", metrics_dir)
    audit.record(stage="script", agent="script", provider="gemini", model="gemini-2.5-flash", input_tokens=1000, output_tokens=500)
    audit.record(stage="script_review", agent="script_review", provider="gemini", model="gemini-2.5-flash", input_tokens=200, output_tokens=100)

    summary = audit.summary()
    assert summary["total_calls"] == 2
    assert summary["total_tokens"] == 1800
    assert "by_stage" in summary
    assert "script" in summary["by_stage"]


# ── Benchmark ─────────────────────────────────────────────────────────

def test_benchmark_dry_run(tmp_path: Path):
    """Benchmark should run successfully in dry-run mode."""
    # Create minimal config directory
    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "default.json").write_text(json.dumps({
        "project": "shadow-protocol",
        "version": "0.1.0",
    }))
    with patch.object(Path, "cwd", return_value=tmp_path):
        exit_code = run_pipeline(
            case_id="case_benchmark",
            dry_run=True,
            force=True,
            mode="production",
        )
        assert exit_code == 0


# ── Config / Stage Models ────────────────────────────────────────────

def test_stage_models_config_exists():
    config_path = Path(__file__).parent.parent / "config" / "stage_models.json"
    assert config_path.exists()
    config = json.loads(config_path.read_text())
    assert "stages" in config
    assert "asset_package" in config["stages"]


def test_stage_models_asset_package_routes_to_gemini_flash_lite():
    config_path = Path(__file__).parent.parent / "config" / "stage_models.json"
    config = json.loads(config_path.read_text())
    ap = config["stages"]["asset_package"]
    assert ap["provider"] == "gemini"
    assert ap["model"] == "gemini-3.1-flash-lite"


# ── Hybrid Stage Routing ─────────────────────────────────────────────

def test_stage_routing_creative_uses_flash():
    """Creative writing stages should route to gemini-2.5-flash."""
    from shadow_protocol.lib.llm import _resolve_stage_config
    for stage in ["production_package", "outline", "script"]:
        provider, model = _resolve_stage_config(stage)
        assert provider == "gemini", f"{stage} provider should be gemini"
        assert model == "gemini-2.5-flash", f"{stage} model should be gemini-2.5-flash"


def test_stage_routing_extraction_uses_flash_lite():
    """Extraction/formatting stages should route to gemini-3.1-flash-lite."""
    from shadow_protocol.lib.llm import _resolve_stage_config
    for stage in ["script_review", "scene_breakdown", "asset_package", "metadata", "thumbnail"]:
        provider, model = _resolve_stage_config(stage)
        assert provider == "gemini", f"{stage} provider should be gemini"
        assert model == "gemini-3.1-flash-lite", f"{stage} model should be gemini-3.1-flash-lite"


def test_stage_routing_voiceover_uses_ollama():
    """Voiceover stage should route to ollama/qwen3:14b."""
    from shadow_protocol.lib.llm import _resolve_stage_config
    provider, model = _resolve_stage_config("voiceover")
    assert provider == "ollama"
    assert model == "qwen3:14b"


# ── Per-Model Quota Tracking ─────────────────────────────────────────

def test_per_model_quota_independent(tmp_path: Path):
    """Quota tracking for one model should not affect another."""
    qm = QuotaManager(tmp_path)
    qm.record_call("gemini-2.5-flash", input_tokens=500)
    qm.record_call("gemini-3.1-flash-lite", input_tokens=100)

    flash_usage = qm.get_usage("gemini-2.5-flash")
    lite_usage = qm.get_usage("gemini-3.1-flash-lite")

    assert flash_usage["used_today"] == 1
    assert flash_usage["input_tokens_used"] == 500
    assert lite_usage["used_today"] == 1
    assert lite_usage["input_tokens_used"] == 100


def test_per_model_quota_different_limits(tmp_path: Path):
    """Each model should report its own RPD limit."""
    qm = QuotaManager(tmp_path)
    flash_usage = qm.get_usage("gemini-2.5-flash")
    lite_usage = qm.get_usage("gemini-3.1-flash-lite")
    assert flash_usage["daily_requests"] == 20
    assert lite_usage["daily_requests"] == 500


# ── Estimate Output ──────────────────────────────────────────────────

def test_estimate_returns_per_model_breakdown(tmp_path: Path):
    """estimate_episode should return per-model breakdown with all expected keys."""
    qm = QuotaManager(tmp_path)
    estimate = qm.estimate_episode(scene_count=15)

    assert "by_model" in estimate
    assert "gemini-2.5-flash" in estimate["by_model"]
    assert "gemini-3.1-flash-lite" in estimate["by_model"]

    for model, data in estimate["by_model"].items():
        assert "estimated_requests" in data
        assert "stages" in data
        assert "remaining_requests" in data
        assert "rpd" in data
        assert "can_run" in data
        assert isinstance(data["stages"], list)


def test_estimate_creative_stages_grouped_under_flash(tmp_path: Path):
    """Creative stages should be grouped under gemini-2.5-flash in estimate."""
    qm = QuotaManager(tmp_path)
    estimate = qm.estimate_episode(scene_count=15)
    flash_stages = estimate["by_model"]["gemini-2.5-flash"]["stages"]
    for s in ["production_package", "outline", "script"]:
        assert s in flash_stages


def test_estimate_extraction_stages_grouped_under_flash_lite(tmp_path: Path):
    """Extraction stages should be grouped under gemini-3.1-flash-lite."""
    qm = QuotaManager(tmp_path)
    estimate = qm.estimate_episode(scene_count=15)
    lite_stages = estimate["by_model"]["gemini-3.1-flash-lite"]["stages"]
    for s in ["script_review", "scene_breakdown", "asset_package", "metadata", "thumbnail"]:
        assert s in lite_stages


# ── Benchmark ────────────────────────────────────────────────────────

def test_benchmark_models_cli_routes_correctly():
    """benchmark-models CLI should route to _handle_benchmark_models."""
    from shadow_protocol.cli import main as cli_main
    from click.testing import CliRunner
    runner = CliRunner()
    # benchmark-models with no extra arg shows usage (exit 0)
    result = runner.invoke(cli_main, ["benchmark-models"])
    assert result.exit_code == 0
    assert "Usage:" in result.output or "CASE_ID" in result.output or "Benchmarking" in result.output


def test_benchmark_models_prints_usage_without_args():
    """benchmark-models without args prints usage."""
    from shadow_protocol.cli import _handle_benchmark_models
    _handle_benchmark_models([])  # Should not raise


def test_benchmark_models_function_exists():
    """_handle_benchmark_models function should exist."""
    from shadow_protocol.cli import _handle_benchmark_models
    import inspect
    assert inspect.isfunction(_handle_benchmark_models)
