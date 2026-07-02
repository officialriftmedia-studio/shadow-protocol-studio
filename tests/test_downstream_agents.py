"""Tests for downstream agents (image_prompt, video_prompt, voiceover, metadata, thumbnail)."""

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from shadow_protocol.lib.schema_validator import validate_output

SCHEMA_DIR = Path("templates/schemas")


def _schema(name: str) -> Path:
    return SCHEMA_DIR / name


# ── Image Prompts Schema Tests ──────────────────────────────────

def test_image_prompts_schema_valid():
    data = {
        "prompts": [
            {
                "scene_id": 1,
                "prompt": "A dark room with a single monitor glow on a woman's face",
                "style": "cinematic",
                "aspect_ratio": "16:9",
            }
        ]
    }
    errors = validate_output(data, _schema("image_prompts.json"))
    assert errors == [], f"Expected no errors, got: {errors}"


def test_image_prompts_schema_missing_required():
    data = {"prompts": [{"scene_id": 1}]}
    errors = validate_output(data, _schema("image_prompts.json"))
    assert len(errors) > 0


def test_image_prompts_schema_invalid_aspect_ratio():
    data = {
        "prompts": [
            {"scene_id": 1, "prompt": "A dark room with a glowing monitor illuminating a figure", "style": "cinematic", "aspect_ratio": "3:2"}
        ]
    }
    errors = validate_output(data, _schema("image_prompts.json"))
    assert any("aspect_ratio" in e for e in errors)


def test_image_prompts_negative_prompt_optional():
    data = {
        "prompts": [
            {
                "scene_id": 1,
                "prompt": "A dark room with a single monitor glow",
                "negative_prompt": "No text, no people smiling",
                "style": "cinematic",
                "aspect_ratio": "16:9",
            }
        ]
    }
    errors = validate_output(data, _schema("image_prompts.json"))
    assert errors == []


# ── Video Prompts Schema Tests ──────────────────────────────────

def test_video_prompts_schema_valid():
    data = {
        "prompts": [
            {
                "scene_id": 1,
                "prompt": "Slow dolly into a server room as lights flicker",
                "duration_seconds": 10,
                "style": "cinematic",
            }
        ]
    }
    errors = validate_output(data, _schema("video_prompts.json"))
    assert errors == []


def test_video_prompts_missing_required():
    data = {"prompts": [{"scene_id": 1, "prompt": "test"}]}
    errors = validate_output(data, _schema("video_prompts.json"))
    assert len(errors) > 0


def test_video_prompts_duration_bounds():
    data = {
        "prompts": [
            {
                "scene_id": 1,
                "prompt": "Slow dolly into a server room as lights flicker and dim",
                "duration_seconds": 999,
                "style": "cinematic",
            }
        ]
    }
    errors = validate_output(data, _schema("video_prompts.json"))
    assert any("duration" in e for e in errors)


def test_video_prompts_camera_motion_optional():
    data = {
        "prompts": [
            {
                "scene_id": 1,
                "prompt": "Handheld following a figure through a corridor",
                "duration_seconds": 8,
                "style": "documentary",
                "camera_motion": "handheld",
            }
        ]
    }
    errors = validate_output(data, _schema("video_prompts.json"))
    assert errors == []


# ── Voiceover Segments Schema Tests ─────────────────────────────

def test_voiceover_segments_valid():
    data = {
        "segments": [
            {
                "scene_id": 1,
                "segment_index": 0,
                "text": "The first sign was invisible to anyone who wasn't looking.",
                "estimated_duration_seconds": 4.5,
            }
        ]
    }
    errors = validate_output(data, _schema("voiceover_segments.json"))
    assert errors == []


def test_voiceover_segments_missing_required():
    data = {"segments": [{"scene_id": 1}]}
    errors = validate_output(data, _schema("voiceover_segments.json"))
    assert len(errors) > 0


def test_voiceover_segments_with_optional():
    data = {
        "segments": [
            {
                "scene_id": 1,
                "segment_index": 0,
                "text": "Test voiceover text here.",
                "voice_id": "eleven_multilingual_v2",
                "estimated_duration_seconds": 3.2,
                "delivery_notes": "Clinical tone, steady pace",
            }
        ]
    }
    errors = validate_output(data, _schema("voiceover_segments.json"))
    assert errors == []


# ── YouTube Metadata Schema Tests ───────────────────────────────

def test_youtube_metadata_valid():
    data = {
        "title": "The Ghost in the Machine | Shadow Protocol",
        "description": "A cybersecurity analyst discovers her identity has been erased.",
        "tags": ["Shadow Protocol", "psychological thriller"],
        "category": "Entertainment",
        "visibility": "unlisted",
        "language": "en",
    }
    errors = validate_output(data, _schema("youtube_metadata.json"))
    assert errors == []


def test_youtube_metadata_missing_required():
    data = {"title": "test"}
    errors = validate_output(data, _schema("youtube_metadata.json"))
    assert len(errors) > 0


def test_youtube_metadata_invalid_visibility():
    data = {
        "title": "Test",
        "description": "Desc",
        "tags": ["a"],
        "category": "Entertainment",
        "visibility": "super_secret",
    }
    errors = validate_output(data, _schema("youtube_metadata.json"))
    assert any("visibility" in e for e in errors)


def test_youtube_metadata_title_max_length():
    data = {
        "title": "X" * 101,
        "description": "Desc",
        "tags": ["a"],
        "category": "Entertainment",
        "visibility": "public",
    }
    errors = validate_output(data, _schema("youtube_metadata.json"))
    assert any("title" in e for e in errors)


def test_youtube_metadata_tags_max_items():
    data = {
        "title": "Test",
        "description": "Desc",
        "tags": [f"tag{i}" for i in range(21)],
        "category": "Entertainment",
        "visibility": "public",
    }
    errors = validate_output(data, _schema("youtube_metadata.json"))
    assert any("tags" in e for e in errors)


# ── Thumbnail Prompt Schema Tests ───────────────────────────────

def test_thumbnail_prompt_valid():
    data = {"prompt": "A woman's silhouette reflected in a dark monitor, one eye visible"}
    errors = validate_output(data, _schema("thumbnail_prompt.json"))
    assert errors == []


def test_thumbnail_prompt_min_length():
    data = {"prompt": "short"}
    errors = validate_output(data, _schema("thumbnail_prompt.json"))
    assert any("prompt" in e for e in errors)


def test_thumbnail_prompt_missing():
    data = {}
    errors = validate_output(data, _schema("thumbnail_prompt.json"))
    assert any("prompt" in e for e in errors)
