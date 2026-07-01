"""Tests for the orchestrator pipeline runner."""

from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).parent.parent))

from shadow_protocol.lib.orchestrator_runner import run_pipeline


def test_run_pipeline_dry_run():
    """Dry-run should succeed without LLM calls."""
    with tempfile.TemporaryDirectory() as tmp:
        result = run_pipeline(
            case_id="case_999",
            dry_run=True,
        )
        assert result == 0


def test_run_pipeline_unknown_step():
    """Unknown resume step should return error."""
    result = run_pipeline(
        case_id="case_999",
        dry_run=True,
        resume_step="nonexistent_step",
    )
    assert result == 1
