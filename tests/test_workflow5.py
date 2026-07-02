"""Tests for Workflow #5: Publishing & Operations."""

import json
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))

PROJECT_ROOT = Path(__file__).resolve().parent.parent
from shadow_protocol.lib.schema_validator import validate_output  # noqa: E402

SCHEMA_DIR = Path("templates/schemas")


def _schema(name: str) -> Path:
    return SCHEMA_DIR / name


# ── Helper: create a minimal youtube_metadata.json ──────────────────


def _create_metadata(tmp_path: Path, **overrides: str | list[str]) -> dict:
    meta = {
        "title": "Test Episode",
        "description": "A test description for the episode.",
        "tags": ["test", "shadow_protocol"],
        "category": "Entertainment",
        "visibility": "unlisted",
        "language": "en",
    }
    meta.update(overrides)
    path = tmp_path / "youtube_metadata.json"
    path.write_text(json.dumps(meta))
    return meta


def _create_render_manifest(tmp_path: Path, **overrides: int | list[str]) -> dict:
    data = {
        "render_time": "2026-01-01T00:00:00",
        "duration_seconds": 120.0,
        "input_assets": {"images": ["img_0001.png"], "voiceover": ["voice.wav"]},
        "output_size_bytes": 50000000,
        "output_path": "render/final_video.mp4",
        "errors": [],
        "scene_count": 5,
        "succeeded_scenes": 5,
        "failed_scenes": 0,
    }
    data.update(overrides)
    (tmp_path / "render").mkdir(parents=True, exist_ok=True)
    (tmp_path / "render" / "render_manifest.json").write_text(json.dumps(data))
    return data


def _create_checkpoint(tmp_path: Path, completed: list[str] | None = None) -> dict:
    stages = completed or [
        "production_package", "outline", "script", "script_review",
        "scene_breakdown", "image_prompt", "voiceover", "metadata",
        "thumbnail", "image_generator", "voice_generator",
        "timeline_builder", "render_builder", "render_executor",
    ]
    data = {"completed": stages, "metadata": {}}
    (tmp_path / ".checkpoint.json").write_text(json.dumps(data))
    return data


def _create_metrics(tmp_path: Path) -> None:
    metrics_dir = tmp_path / "metrics"
    metrics_dir.mkdir(exist_ok=True)
    for stage in ["production_package", "outline", "script", "render_executor"]:
        (metrics_dir / f"{stage}.json").write_text(json.dumps({
            "stage": stage,
            "status": "success",
            "total_tokens": 1000,
            "cost_usd": 0.01,
            "duration_seconds": 5.0,
            "llm_calls": 2,
        }))


# ── Schema Tests ────────────────────────────────────────────────────


def test_publish_manifest_schema_valid():
    data = {
        "case_id": "case_001",
        "created_at": "2026-01-01T00:00:00",
        "package_path": "publish/upload_package",
        "assets": [
            {"name": "final_video.mp4", "source": "render/final_video.mp4", "size_bytes": 50000000, "exists": True},
        ],
        "metadata": {"title": "Test", "description": "Desc", "tags": ["a"], "visibility": "unlisted", "language": "en", "category": "Entertainment"},
        "warnings": [],
    }
    errors = validate_output(data, _schema("publish_manifest.json"))
    assert errors == [], f"Expected no errors, got: {errors}"


def test_publish_manifest_schema_missing_required():
    data = {"case_id": "case_001"}
    errors = validate_output(data, _schema("publish_manifest.json"))
    assert len(errors) > 0


def test_quality_report_schema_valid():
    data = {
        "passed": True,
        "checks": [
            {"name": "video_exists", "passed": True, "message": "OK", "severity": "info"},
        ],
        "summary": {"total": 1, "passed": 1, "failed": 0, "warnings": 0},
        "warnings": [],
    }
    errors = validate_output(data, _schema("quality_report.json"))
    assert errors == [], f"Expected no errors, got: {errors}"


def test_quality_report_schema_invalid_severity():
    data = {
        "passed": True,
        "checks": [
            {"name": "test", "passed": False, "message": "bad", "severity": "critical"},
        ],
        "summary": {"total": 1, "passed": 0, "failed": 1, "warnings": 0},
        "warnings": [],
    }
    errors = validate_output(data, _schema("quality_report.json"))
    assert any("severity" in e for e in errors)


def test_quality_report_schema_missing_summary():
    data = {"passed": True, "checks": [], "warnings": []}
    errors = validate_output(data, _schema("quality_report.json"))
    assert len(errors) > 0


# ── Publish Package Builder Tests ────────────────────────────────────


def test_publish_package_builder_happy_path(tmp_path: Path):
    from agents.publish_package_builder import PublishPackageBuilderAgent

    _create_metadata(tmp_path)
    (tmp_path / "render").mkdir(parents=True)
    (tmp_path / "render" / "final_video.mp4").write_bytes(b"\x00" * 1000)
    (tmp_path / "render" / "chapters.txt").write_text("00:00 Intro\n")

    config = {"root": str(PROJECT_ROOT)}
    agent = PublishPackageBuilderAgent(str(tmp_path), config)
    exit_code = agent.run()

    assert exit_code == 0
    assert (tmp_path / "publish" / "publish_manifest.json").exists()
    assert (tmp_path / "publish" / "upload_package" / "final_video.mp4").exists()
    assert (tmp_path / "publish" / "upload_package" / "title.txt").exists()
    assert (tmp_path / "publish" / "upload_package" / "description.txt").exists()
    assert (tmp_path / "publish" / "upload_package" / "tags.txt").exists()
    assert (tmp_path / "publish" / "upload_package" / "chapters.txt").exists()
    assert (tmp_path / "publish" / "upload_package" / "metadata.json").exists()

    manifest = json.loads((tmp_path / "publish" / "publish_manifest.json").read_text())
    assert manifest["case_id"] == tmp_path.name
    assert len(manifest["assets"]) >= 6
    assert manifest["metadata"]["title"] == "Test Episode"


def test_publish_package_builder_missing_video(tmp_path: Path):
    from agents.publish_package_builder import PublishPackageBuilderAgent

    _create_metadata(tmp_path)

    config = {"root": str(PROJECT_ROOT)}
    agent = PublishPackageBuilderAgent(str(tmp_path), config)
    exit_code = agent.run()

    assert exit_code == 0  # should not fail, just warn
    manifest = json.loads((tmp_path / "publish" / "publish_manifest.json").read_text())
    video_asset = [a for a in manifest["assets"] if a["name"] == "final_video.mp4"]
    assert video_asset
    assert video_asset[0]["exists"] is False
    assert len(manifest["warnings"]) > 0


def test_publish_package_builder_missing_metadata(tmp_path: Path):
    from agents.publish_package_builder import PublishPackageBuilderAgent

    config = {"root": str(PROJECT_ROOT)}
    agent = PublishPackageBuilderAgent(str(tmp_path), config)
    exit_code = agent.run()
    assert exit_code == 1


def test_publish_package_builder_content(tmp_path: Path):
    from agents.publish_package_builder import PublishPackageBuilderAgent

    _create_metadata(tmp_path, title="My Title", tags=["tag1", "tag2"], description="My desc")
    (tmp_path / "render").mkdir(parents=True)
    (tmp_path / "render" / "final_video.mp4").write_bytes(b"\x00" * 100)

    config = {"root": str(PROJECT_ROOT)}
    agent = PublishPackageBuilderAgent(str(tmp_path), config)
    exit_code = agent.run()

    assert exit_code == 0
    title = (tmp_path / "publish" / "upload_package" / "title.txt").read_text().strip()
    assert title == "My Title"

    tags = (tmp_path / "publish" / "upload_package" / "tags.txt").read_text().strip().split("\n")
    assert "tag1" in tags

    desc = (tmp_path / "publish" / "upload_package" / "description.txt").read_text().strip()
    assert desc == "My desc"


# ── Quality Control Agent Tests ──────────────────────────────────────


@patch("agents.quality_control.QualityControlAgent._get_video_duration")
def test_quality_control_all_pass(mock_duration, tmp_path: Path):
    from agents.quality_control import QualityControlAgent

    mock_duration.return_value = 120.0

    (tmp_path / "render").mkdir(parents=True)
    (tmp_path / "render" / "final_video.mp4").write_bytes(b"\x00" * 100)
    _create_render_manifest(tmp_path)

    (tmp_path / "publish").mkdir(parents=True)
    (tmp_path / "publish" / "publish_manifest.json").write_text(json.dumps({
        "assets": [{"name": "final_video.mp4", "required": True, "exists": True}],
    }))
    _create_checkpoint(tmp_path)
    _create_metadata(tmp_path)

    config = {"root": str(PROJECT_ROOT)}
    agent = QualityControlAgent(str(tmp_path), config)
    exit_code = agent.run()

    assert exit_code == 0
    assert (tmp_path / "publish" / "quality_report.json").exists()

    report = json.loads((tmp_path / "publish" / "quality_report.json").read_text())
    assert report["passed"] is True
    assert report["summary"]["passed"] > 0


@patch("agents.quality_control.QualityControlAgent._get_video_duration")
def test_quality_control_missing_video(mock_duration, tmp_path: Path):
    from agents.quality_control import QualityControlAgent

    mock_duration.return_value = None

    (tmp_path / "render").mkdir(parents=True)
    _create_render_manifest(tmp_path)
    (tmp_path / "publish").mkdir(parents=True)
    (tmp_path / "publish" / "publish_manifest.json").write_text(json.dumps({"assets": []}))
    _create_checkpoint(tmp_path)
    _create_metadata(tmp_path)

    config = {"root": str(PROJECT_ROOT)}
    agent = QualityControlAgent(str(tmp_path), config)
    exit_code = agent.run()

    assert exit_code == 1  # QC should fail
    report = json.loads((tmp_path / "publish" / "quality_report.json").read_text())
    assert report["passed"] is False


@patch("agents.quality_control.QualityControlAgent._get_video_duration")
def test_quality_control_render_errors(mock_duration, tmp_path: Path):
    from agents.quality_control import QualityControlAgent

    mock_duration.return_value = 120.0

    (tmp_path / "render").mkdir(parents=True)
    (tmp_path / "render" / "final_video.mp4").write_bytes(b"\x00" * 100)
    _create_render_manifest(tmp_path, failed_scenes=2, errors=["Scene 2 failed"])
    (tmp_path / "publish").mkdir(parents=True)
    (tmp_path / "publish" / "publish_manifest.json").write_text(json.dumps({
        "assets": [{"name": "final_video.mp4", "required": True, "exists": True}],
    }))
    _create_checkpoint(tmp_path)
    _create_metadata(tmp_path)

    config = {"root": str(PROJECT_ROOT)}
    agent = QualityControlAgent(str(tmp_path), config)
    exit_code = agent.run()

    assert exit_code == 1
    report = json.loads((tmp_path / "publish" / "quality_report.json").read_text())
    assert report["passed"] is False


@patch("agents.quality_control.QualityControlAgent._get_video_duration")
def test_quality_control_missing_stages(mock_duration, tmp_path: Path):
    from agents.quality_control import QualityControlAgent

    mock_duration.return_value = 120.0

    (tmp_path / "render").mkdir(parents=True)
    (tmp_path / "render" / "final_video.mp4").write_bytes(b"\x00" * 100)
    _create_render_manifest(tmp_path)
    (tmp_path / "publish").mkdir(parents=True)
    (tmp_path / "publish" / "publish_manifest.json").write_text(json.dumps({"assets": []}))
    _create_checkpoint(tmp_path, completed=["production_package", "outline"])
    _create_metadata(tmp_path)

    config = {"root": str(PROJECT_ROOT)}
    agent = QualityControlAgent(str(tmp_path), config)
    agent.run()

    report = json.loads((tmp_path / "publish" / "quality_report.json").read_text())
    # Should have warnings about missing stages but not fail everything
    assert len(report.get("warnings", [])) > 0


# ── Release Manager Agent Tests ──────────────────────────────────────


def test_release_manager_with_full_data(tmp_path: Path):
    from agents.release_manager import ReleaseManagerAgent

    (tmp_path / "render").mkdir(parents=True)
    (tmp_path / "render" / "final_video.mp4").write_bytes(b"\x00" * 50000000)
    _create_render_manifest(tmp_path)
    _create_metadata(tmp_path)
    _create_metrics(tmp_path)

    (tmp_path / "publish").mkdir(parents=True)
    (tmp_path / "publish" / "publish_manifest.json").write_text(json.dumps({
        "assets": [
            {"name": "final_video.mp4", "size_bytes": 50000000, "exists": True},
            {"name": "title.txt", "size_bytes": 20, "exists": True},
        ],
        "warnings": [],
    }))
    (tmp_path / "publish" / "quality_report.json").write_text(json.dumps({
        "passed": True,
        "checks": [
            {"name": "video_exists", "passed": True, "message": "OK", "severity": "info"},
        ],
        "summary": {"total": 1, "passed": 1, "failed": 0, "warnings": 0},
        "warnings": [],
    }))

    config = {"root": str(PROJECT_ROOT)}
    agent = ReleaseManagerAgent(str(tmp_path), config)
    exit_code = agent.run()

    assert exit_code == 0
    report_path = tmp_path / "publish" / "publishing_report.md"
    assert report_path.exists()

    content = report_path.read_text()
    assert "# Publishing Report" in content
    assert "Test Episode" in content
    assert "final_video.mp4" in content
    assert "Pipeline Costs" in content
    assert "Quality Checks" in content
    assert "Render Details" in content


def test_release_manager_minimal_data(tmp_path: Path):
    from agents.release_manager import ReleaseManagerAgent

    (tmp_path / "publish").mkdir(parents=True)

    config = {"root": str(PROJECT_ROOT)}
    agent = ReleaseManagerAgent(str(tmp_path), config)
    exit_code = agent.run()

    assert exit_code == 0
    report_path = tmp_path / "publish" / "publishing_report.md"
    assert report_path.exists()
    content = report_path.read_text()
    assert "# Publishing Report" in content


# ── Publishing Interfaces Tests ──────────────────────────────────────


def test_platform_publisher_abstract():
    from shadow_protocol.lib.publishing.base import PlatformPublisher, PublishResult

    r = PublishResult(success=True, platform="youtube", video_id="abc123")
    assert r.success
    assert r.video_id == "abc123"

    # Cannot instantiate ABC directly
    import pytest
    with pytest.raises(TypeError):
        PlatformPublisher()


def test_youtube_publisher_stub():
    from shadow_protocol.lib.publishing.youtube import YouTubePublisher

    pub = YouTubePublisher()
    assert pub.name == "youtube"
    import pytest
    with pytest.raises(NotImplementedError):
        pub.authenticate()
    with pytest.raises(NotImplementedError):
        pub.upload(Path("/dev/null"), "t", "d", [])
    with pytest.raises(NotImplementedError):
        pub.update_metadata("id")
    with pytest.raises(NotImplementedError):
        pub.delete("id")


def test_youtube_publisher_config():
    from shadow_protocol.lib.publishing.youtube import YouTubePublisher

    pub = YouTubePublisher(api_key="test_key")
    assert pub.config["api_key"] == "test_key"


def test_publish_scheduler_abstract():
    from shadow_protocol.lib.publishing.scheduler import PublishScheduler, ScheduleResult

    r = ScheduleResult(success=True)
    assert r.success

    import pytest
    with pytest.raises(TypeError):
        PublishScheduler()


def test_analytics_collector_abstract():
    from shadow_protocol.lib.publishing.analytics import AnalyticsCollector, VideoAnalytics

    a = VideoAnalytics(video_id="abc", views=100)
    assert a.views == 100

    import pytest
    with pytest.raises(TypeError):
        AnalyticsCollector()


# ── Orchestrator Integration ─────────────────────────────────────────


def test_orchestrator_includes_wf5_stages():
    from shadow_protocol.lib.orchestrator_runner import STAGE_ORDER, AGENT_SCRIPT_MAP

    assert "publish_package_builder" in STAGE_ORDER
    assert "quality_control" in STAGE_ORDER
    assert "release_manager" in STAGE_ORDER

    assert AGENT_SCRIPT_MAP["publish_package_builder"] == "agents/publish_package_builder.py"
    assert AGENT_SCRIPT_MAP["quality_control"] == "agents/quality_control.py"
    assert AGENT_SCRIPT_MAP["release_manager"] == "agents/release_manager.py"

    # Verify ordering
    assert STAGE_ORDER.index("release_manager") == len(STAGE_ORDER) - 1


# ── Config Tests ────────────────────────────────────────────────────


def test_paths_config_has_wf5_stages():
    path = Path("config/paths.json")
    assert path.exists()
    data = json.loads(path.read_text())
    stages = data.get("stages", {})
    assert "publish_package_builder" in stages
    assert "quality_control" in stages
    assert "release_manager" in stages
    assert stages["publish_package_builder"]["output"] == "publish/upload_package/"
    assert stages["quality_control"]["output"] == "publish/quality_report.json"
    assert stages["release_manager"]["output"] == "publish/publishing_report.md"


def test_schema_files_exist():
    assert _schema("publish_manifest.json").exists()
    assert _schema("quality_report.json").exists()


# ── Formatting helper tests ──────────────────────────────────────────


def test_format_size():
    from agents.release_manager import ReleaseManagerAgent

    agent = ReleaseManagerAgent.__new__(ReleaseManagerAgent)
    assert agent._format_size(500) == "500 B"
    assert agent._format_size(1500) == "1.5 KB"
    assert agent._format_size(2000000) == "2.0 MB"
