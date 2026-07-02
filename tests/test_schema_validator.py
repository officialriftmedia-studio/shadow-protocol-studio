"""Tests for JSON Schema validation."""

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from shadow_protocol.lib.schema_validator import validate_output


SCHEMA_DIR = Path("templates/schemas")


def _schema(name: str) -> Path:
    return SCHEMA_DIR / name


def test_production_package_schema_valid():
    data = {
        "episode_id": "case_001",
        "title": "Test Episode",
        "logline": "A test logline",
        "estimated_duration_seconds": 600,
        "scenes": 5,
        "tone": "psychological thriller",
    }
    errors = validate_output(data, _schema("production_package.json"))
    assert errors == [], f"Expected no errors, got: {errors}"


def test_production_package_schema_missing_required():
    data = {"episode_id": "case_001"}
    errors = validate_output(data, _schema("production_package.json"))
    assert len(errors) > 0


def test_outline_schema_valid():
    data = {
        "episode_id": "case_001",
        "acts": [
            {
                "act": 1,
                "name": "Test Act 1",
                "summary": "First act",
                "scenes": [
                    {
                        "scene": 1,
                        "summary": "Scene summary",
                        "beats": [{"beat": 1, "description": "Beat", "duration_seconds": 60}],
                    }
                ],
            },
            {
                "act": 2,
                "name": "Test Act 2",
                "summary": "Second act",
                "scenes": [
                    {
                        "scene": 2,
                        "summary": "Scene summary",
                        "beats": [{"beat": 1, "description": "Beat", "duration_seconds": 60}],
                    }
                ],
            },
        ],
    }
    errors = validate_output(data, _schema("outline.json"))
    assert errors == [], f"Expected no errors, got: {errors}"


def test_outline_schema_too_few_acts():
    data = {"episode_id": "case_001", "acts": []}
    errors = validate_output(data, _schema("outline.json"))
    assert any("acts" in e for e in errors)


def test_review_schema_valid():
    data = {
        "overall": "APPROVED",
        "sections": [
            {"section": "hook.md", "status": "PASS", "issues": [], "strengths": ["Great hook"]}
        ],
        "summary": "Good script",
        "recommendations": [],
    }
    errors = validate_output(data, _schema("review.json"))
    assert errors == [], f"Expected no errors, got: {errors}"
