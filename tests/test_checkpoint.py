"""Tests for checkpoint manager."""

from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).parent.parent))

from shadow_protocol.lib.checkpoint import (
    get_completed_stages,
    mark_stage_complete,
    is_stage_complete,
    clear_checkpoint,
)


def test_checkpoint_cycle():
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)

        assert get_completed_stages(d) == []
        assert is_stage_complete(d, "foo") is False

        mark_stage_complete(d, "foo")
        assert get_completed_stages(d) == ["foo"]
        assert is_stage_complete(d, "foo") is True
        assert is_stage_complete(d, "bar") is False

        mark_stage_complete(d, "bar", {"tokens": 500})
        assert get_completed_stages(d) == ["foo", "bar"]

        clear_checkpoint(d)
        assert get_completed_stages(d) == []


def test_checkpoint_metadata():
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        mark_stage_complete(d, "test", {"tokens": 100, "cost": 0.05})
        from shadow_protocol.lib.checkpoint import get_stage_metadata
        meta = get_stage_metadata(d, "test")
        assert meta == {"tokens": 100, "cost": 0.05}

        assert get_stage_metadata(d, "nonexistent") is None
