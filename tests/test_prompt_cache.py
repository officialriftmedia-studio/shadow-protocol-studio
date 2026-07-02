"""Tests for prompt caching module."""

import json
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).parent.parent))

from shadow_protocol.lib.prompt_cache import get_cached, set_cache, invalidate


def test_cache_miss():
    with tempfile.TemporaryDirectory() as tmp:
        hit, data = get_cached(tmp, "test_stage", "section_1", "input content")
        assert hit is False
        assert data is None


def test_cache_hit():
    with tempfile.TemporaryDirectory() as tmp:
        input_text = "hello world"
        expected = [{"scene_number": 1, "title": "Test"}]

        set_cache(tmp, "test_stage", "section_1", expected, input_text)
        hit, data = get_cached(tmp, "test_stage", "section_1", input_text)

        assert hit is True
        assert data == expected


def test_cache_miss_on_different_input():
    with tempfile.TemporaryDirectory() as tmp:
        set_cache(tmp, "test_stage", "section_1", [{"scene": 1}], "original input")

        hit, data = get_cached(tmp, "test_stage", "section_1", "different input")
        assert hit is False
        assert data is None


def test_invalidate_section():
    with tempfile.TemporaryDirectory() as tmp:
        set_cache(tmp, "s", "a", [1], "x")
        set_cache(tmp, "s", "b", [2], "y")

        invalidate(tmp, "s", "a")

        hit_a, _ = get_cached(tmp, "s", "a", "x")
        assert hit_a is False

        hit_b, data_b = get_cached(tmp, "s", "b", "y")
        assert hit_b is True
        assert data_b == [2]


def test_invalidate_all():
    with tempfile.TemporaryDirectory() as tmp:
        set_cache(tmp, "s", "a", [1], "x")
        set_cache(tmp, "s", "b", [2], "y")

        invalidate(tmp, "s")

        hit_a, _ = get_cached(tmp, "s", "a", "x")
        hit_b, _ = get_cached(tmp, "s", "b", "y")
        assert hit_a is False
        assert hit_b is False


def test_cache_file_structure():
    with tempfile.TemporaryDirectory() as tmp:
        set_cache(tmp, "stage_x", "sec_1", [{"k": "v"}], "input")

        cache_file = Path(tmp) / ".cache" / "stage_x" / "stage_x_sec_1.json"
        assert cache_file.exists()

        entry = json.loads(cache_file.read_text())
        assert entry["stage"] == "stage_x"
        assert entry["section"] == "sec_1"
        assert entry["data"] == [{"k": "v"}]
        assert "hash" in entry
