"""Tests for LLM abstraction layer."""

from pathlib import Path
import sys
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from shadow_protocol.lib.llm import get_usage, reset_usage, _estimate_cost  # noqa: E402


def test_estimate_cost_known_model():
    cost = _estimate_cost("gpt-4o", 1000, 500)
    assert cost == pytest.approx(0.0025 * 1 + 0.01 * 0.5)


def test_estimate_cost_unknown_model():
    cost = _estimate_cost("fake-model", 1000, 500)
    assert cost == 0.0


def test_usage_tracking():
    reset_usage()
    usage = get_usage()
    assert usage.calls == 0
    assert usage.total_tokens == 0
    assert usage.cost_usd == 0.0

    usage.add(500, 200, 0.005, "gpt-4o")
    assert usage.calls == 1
    assert usage.total_tokens == 700
    assert usage.cost_usd == 0.005
    assert len(usage.history) == 1
    assert usage.history[0]["model"] == "gpt-4o"

    usage.add(100, 50, 0.001, "gpt-4o-mini")
    assert usage.calls == 2
    assert usage.total_tokens == 850
    assert usage.cost_usd == 0.006
