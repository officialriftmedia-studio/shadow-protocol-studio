"""Tests for Scene Breakdown agent."""

import json
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).parent.parent))

from shadow_protocol.lib.schema_validator import validate_output


SCHEMA = Path("templates/schemas/scene_breakdown.json")


def _valid_scene(overrides: dict | None = None) -> dict:
    scene = {
        "scene_number": 1,
        "section": "hook",
        "title": "The First Crack",
        "duration": 45,
        "narrative_purpose": "Establish protagonist and the anomaly",
        "location": "OmniCorp headquarters - cybersecurity operations center",
        "characters": ["Elena Vasquez"],
        "emotion": "clinical unease",
        "camera_style": "slow push on Elena's monitor",
        "color_palette": "cold blues, clinical white, screen glow",
        "lighting": "fluorescent overhead with monitor key light",
        "visual_motif": "reflections in glass",
        "music": "low drone ambient",
        "sound_effects": ["keyboard clicks", "server hum", "distant phone"],
        "transition_in": "hard cut from black",
        "transition_out": "dissolve",
    }
    if overrides:
        scene.update(overrides)
    return scene


def test_valid_scene_passes_schema():
    scene = _valid_scene()
    errors = validate_output([scene], SCHEMA)
    assert errors == [], f"Expected no errors, got: {errors}"


def test_multiple_valid_scenes():
    scenes = [
        _valid_scene({"scene_number": 1}),
        _valid_scene({"scene_number": 2, "title": "Second Scene"}),
    ]
    errors = validate_output(scenes, SCHEMA)
    assert errors == [], f"Expected no errors, got: {errors}"


def test_missing_required_fields():
    scene = {"scene_number": 1}
    errors = validate_output([scene], SCHEMA)
    assert len(errors) > 0
    # Schema validates one required field at a time; at least one should be flagged
    required = ["section", "title", "duration", "narrative_purpose", "location", "characters"]
    assert any(any(f in e for f in required) for e in errors)


def test_invalid_duration_zero():
    scene = _valid_scene({"duration": 0})
    errors = validate_output([scene], SCHEMA)
    assert any("duration" in e for e in errors)


def test_invalid_duration_over_limit():
    scene = _valid_scene({"duration": 999})
    errors = validate_output([scene], SCHEMA)
    assert any("duration" in e for e in errors)


def test_empty_scenes_array():
    errors = validate_output([], SCHEMA)
    assert errors == []


def test_additional_properties_rejected():
    scene = _valid_scene({"unknown_field": "should be rejected"})
    errors = validate_output([scene], SCHEMA)
    assert any("unknown_field" in e for e in errors)


def test_scene_number_must_be_positive():
    scene = _valid_scene({"scene_number": 0})
    errors = validate_output([scene], SCHEMA)
    assert any("scene_number" in e for e in errors)


def test_section_values():
    for section in ["hook", "act1", "act2", "act3", "ending", "cliffhanger"]:
        scene = _valid_scene({"section": section})
        errors = validate_output([scene], SCHEMA)
        assert errors == [], f"Section '{section}' should pass: {errors}"


def test_schema_file_is_valid_json():
    with open(SCHEMA) as f:
        schema = json.load(f)
    assert "$schema" in schema
    assert schema["title"] == "SceneBreakdown"
    assert schema["type"] == "array"
