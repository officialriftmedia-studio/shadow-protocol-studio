"""Tests for Workflow #4: Video Assembly Engine."""

import json
import sys
import wave
import struct
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))

PROJECT_ROOT = Path(__file__).resolve().parent.parent

from shadow_protocol.lib.schema_validator import validate_output  # noqa: E402

SCHEMA_DIR = Path("templates/schemas")


def _schema(name: str) -> Path:
    return SCHEMA_DIR / name


# ── Schema Tests ────────────────────────────────────────────────────


def test_timeline_schema_valid():
    data = {
        "scenes": [
            {
                "scene_number": 1,
                "image": "assets/images/img_0001.png",
                "voiceover": ["assets/voice/voice_scene0001_seg0000.wav"],
                "duration_seconds": 20.0,
                "transition": "fade",
                "camera_motion": "slow_zoom_in",
                "music": None,
            }
        ]
    }
    errors = validate_output(data, _schema("timeline.json"))
    assert errors == [], f"Expected no errors, got: {errors}"


def test_timeline_schema_missing_required():
    data = {"scenes": [{"scene_number": 1}]}
    errors = validate_output(data, _schema("timeline.json"))
    assert len(errors) > 0


def test_timeline_schema_invalid_transition():
    data = {
        "scenes": [
            {
                "scene_number": 1,
                "image": "img.png",
                "voiceover": "voice.wav",
                "duration_seconds": 10,
                "transition": "invalid_transition",
                "camera_motion": "static",
            }
        ]
    }
    errors = validate_output(data, _schema("timeline.json"))
    assert any("transition" in e for e in errors)


def test_timeline_schema_invalid_motion():
    data = {
        "scenes": [
            {
                "scene_number": 1,
                "image": "img.png",
                "voiceover": "voice.wav",
                "duration_seconds": 10,
                "transition": "cut",
                "camera_motion": "teleport",
            }
        ]
    }
    errors = validate_output(data, _schema("timeline.json"))
    assert any("camera_motion" in e for e in errors)


def test_timeline_schema_voiceover_as_string():
    data = {
        "scenes": [
            {
                "scene_number": 1,
                "image": "img.png",
                "voiceover": "assets/voice/single_segment.wav",
                "duration_seconds": 10,
                "transition": "cut",
                "camera_motion": "static",
            }
        ]
    }
    errors = validate_output(data, _schema("timeline.json"))
    assert errors == []


def test_timeline_schema_duration_bounds():
    data = {
        "scenes": [
            {
                "scene_number": 1,
                "image": "img.png",
                "voiceover": "voice.wav",
                "duration_seconds": 0.5,
                "transition": "cut",
                "camera_motion": "static",
            }
        ]
    }
    errors = validate_output(data, _schema("timeline.json"))
    assert len(errors) > 0


def test_ffmpeg_commands_schema_valid():
    data = {
        "scenes": [
            {
                "scene_number": 1,
                "commands": [
                    {
                        "type": "generate_video",
                        "description": "Scene 1",
                        "command": ["ffmpeg", "-y", "-i", "input.png", "out.mp4"],
                    }
                ],
            }
        ],
        "concat_command": {
            "type": "concat",
            "description": "Concat all",
            "command": ["ffmpeg", "-f", "concat", "-i", "list.txt", "-c", "copy", "final.mp4"],
        },
        "final_output": "render/final_video.mp4",
    }
    errors = validate_output(data, _schema("ffmpeg_commands.json"))
    assert errors == [], f"Expected no errors, got: {errors}"


def test_ffmpeg_commands_schema_missing_scenes():
    data = {
        "concat_command": {"type": "concat", "description": "Concat", "command": ["ffmpeg"]},
        "final_output": "out.mp4",
    }
    errors = validate_output(data, _schema("ffmpeg_commands.json"))
    assert len(errors) > 0


def test_render_manifest_schema_valid():
    data = {
        "render_time": "2026-01-01T00:00:00",
        "input_assets": {
            "images": ["img_0001.png"],
            "voiceover": ["voice.wav"],
        },
        "errors": [],
        "scene_count": 5,
        "succeeded_scenes": 5,
        "failed_scenes": 0,
    }
    errors = validate_output(data, _schema("render_manifest.json"))
    assert errors == [], f"Expected no errors, got: {errors}"


def test_render_manifest_schema_missing_required():
    data = {"render_time": "test"}
    errors = validate_output(data, _schema("render_manifest.json"))
    assert len(errors) > 0


# ── Timeline Builder Agent Tests ────────────────────────────────────


def create_scene_breakdown(tmp_path: Path, scenes: list[dict]) -> Path:
    path = tmp_path / "scene_breakdown.json"
    path.write_text(json.dumps(scenes))
    return path


def create_fake_image(tmp_path: Path, scene_num: int) -> Path:
    img_dir = tmp_path / "assets" / "images"
    img_dir.mkdir(parents=True, exist_ok=True)
    path = img_dir / f"img_{scene_num:04d}.png"
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 20)
    return path


def create_fake_voice(tmp_path: Path, scene_num: int, seg_idx: int = 0, duration: float = 2.0) -> Path:
    voice_dir = tmp_path / "assets" / "voice"
    voice_dir.mkdir(parents=True, exist_ok=True)
    path = voice_dir / f"voice_scene{scene_num:04d}_seg{seg_idx:04d}.wav"
    sample_rate = 22050
    num_samples = int(duration * sample_rate)
    with wave.open(str(path), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        samples = []
        for i in range(num_samples):
            val = int(800 * __import__("math").sin(2 * __import__("math").pi * 100 * i / sample_rate))
            samples.append(struct.pack("<h", val))
        wf.writeframes(b"".join(samples))
    return path


def test_timeline_builder_with_assets(tmp_path: Path):
    from agents.timeline_builder import TimelineBuilderAgent

    create_scene_breakdown(tmp_path, [
        {"scene_number": 1, "title": "Intro"},
        {"scene_number": 2, "title": "Investigation"},
    ])
    create_fake_image(tmp_path, 1)
    create_fake_image(tmp_path, 2)
    create_fake_voice(tmp_path, 1, 0, 2.0)
    create_fake_voice(tmp_path, 2, 0, 3.0)

    config = {"root": str(PROJECT_ROOT)}
    agent = TimelineBuilderAgent(str(tmp_path), config)
    exit_code = agent.run()

    assert exit_code == 0
    timeline_path = tmp_path / "render" / "timeline.json"
    assert timeline_path.exists()

    timeline = json.loads(timeline_path.read_text())
    assert len(timeline["scenes"]) == 2
    assert timeline["scenes"][0]["scene_number"] == 1
    assert timeline["scenes"][0]["image"] == "assets/images/img_0001.png"
    assert len(timeline["scenes"][0]["voiceover"]) == 1
    assert timeline["scenes"][0]["duration_seconds"] >= 2.0
    assert timeline["scenes"][0]["transition"] == "fade"

    chapters_path = tmp_path / "render" / "chapters.txt"
    assert chapters_path.exists()
    chapters = chapters_path.read_text()
    assert "Scene 1" in chapters
    assert "Scene 2" in chapters


def test_timeline_builder_no_voiceover(tmp_path: Path):
    from agents.timeline_builder import TimelineBuilderAgent

    create_scene_breakdown(tmp_path, [
        {"scene_number": 1, "title": "Intro"},
    ])
    create_fake_image(tmp_path, 1)

    config = {"root": str(PROJECT_ROOT)}
    agent = TimelineBuilderAgent(str(tmp_path), config)
    exit_code = agent.run()

    assert exit_code == 0
    timeline = json.loads((tmp_path / "render" / "timeline.json").read_text())
    assert timeline["scenes"][0]["image"] == "assets/images/img_0001.png"
    assert timeline["scenes"][0]["voiceover"] == []
    assert timeline["scenes"][0]["duration_seconds"] == 15.0  # default


def test_timeline_builder_missing_breakdown(tmp_path: Path):
    from agents.timeline_builder import TimelineBuilderAgent

    config = {"root": str(PROJECT_ROOT)}
    agent = TimelineBuilderAgent(str(tmp_path), config)
    exit_code = agent.run()
    assert exit_code == 1


def test_timeline_builder_multiple_voice_segments(tmp_path: Path):
    from agents.timeline_builder import TimelineBuilderAgent

    create_scene_breakdown(tmp_path, [
        {"scene_number": 1, "title": "Intro"},
    ])
    create_fake_image(tmp_path, 1)
    create_fake_voice(tmp_path, 1, 0, 1.5)
    create_fake_voice(tmp_path, 1, 1, 2.5)

    config = {"root": str(PROJECT_ROOT)}
    agent = TimelineBuilderAgent(str(tmp_path), config)
    exit_code = agent.run()

    assert exit_code == 0
    timeline = json.loads((tmp_path / "render" / "timeline.json").read_text())
    assert len(timeline["scenes"][0]["voiceover"]) == 2


# ── Render Builder Agent Tests ──────────────────────────────────────


def test_render_builder_with_timeline(tmp_path: Path):
    from agents.render_builder import RenderBuilderAgent

    render_dir = tmp_path / "render"
    render_dir.mkdir()

    create_fake_image(tmp_path, 1)
    create_fake_voice(tmp_path, 1, 0, 2.0)

    timeline = {
        "scenes": [
            {
                "scene_number": 1,
                "image": "assets/images/img_0001.png",
                "voiceover": ["assets/voice/voice_scene0001_seg0000.wav"],
                "duration_seconds": 5.0,
                "transition": "fade",
                "camera_motion": "slow_zoom_in",
                "music": None,
            }
        ]
    }
    (render_dir / "timeline.json").write_text(json.dumps(timeline))

    config = {"root": str(PROJECT_ROOT)}
    agent = RenderBuilderAgent(str(tmp_path), config)
    exit_code = agent.run()

    assert exit_code == 0
    cmds_path = tmp_path / "render" / "ffmpeg_commands.json"
    assert cmds_path.exists()

    cmds = json.loads(cmds_path.read_text())
    assert len(cmds["scenes"]) == 1
    assert cmds["scenes"][0]["scene_number"] == 1
    assert len(cmds["scenes"][0]["commands"]) == 1
    assert cmds["scenes"][0]["commands"][0]["type"] == "generate_video"
    assert "ffmpeg" in cmds["scenes"][0]["commands"][0]["command"]
    assert cmds["scenes"][0]["commands"][0]["command"][0] == "ffmpeg"
    assert "concat_command" in cmds
    assert cmds["final_output"] == "render/final_video.mp4"


def test_render_builder_camera_motion_filter(tmp_path: Path):
    from agents.render_builder import RenderBuilderAgent

    render_dir = tmp_path / "render"
    render_dir.mkdir()
    create_fake_image(tmp_path, 1)

    timeline = {
        "scenes": [
            {
                "scene_number": 1,
                "image": "assets/images/img_0001.png",
                "voiceover": [],
                "duration_seconds": 3.0,
                "transition": "fade",
                "camera_motion": "pan_left",
                "music": None,
            }
        ]
    }
    (render_dir / "timeline.json").write_text(json.dumps(timeline))

    config = {"root": str(PROJECT_ROOT)}
    agent = RenderBuilderAgent(str(tmp_path), config)
    agent.run()

    cmds = json.loads((tmp_path / "render" / "ffmpeg_commands.json").read_text())
    cmd = " ".join(cmds["scenes"][0]["commands"][0]["command"])
    assert "pan_left" in cmd or "zoompan" in cmd


def test_render_builder_no_audio(tmp_path: Path):
    from agents.render_builder import RenderBuilderAgent

    render_dir = tmp_path / "render"
    render_dir.mkdir()
    create_fake_image(tmp_path, 1)

    timeline = {
        "scenes": [
            {
                "scene_number": 1,
                "image": "assets/images/img_0001.png",
                "voiceover": [],
                "duration_seconds": 5.0,
                "transition": "cut",
                "camera_motion": "static",
                "music": None,
            }
        ]
    }
    (render_dir / "timeline.json").write_text(json.dumps(timeline))

    config = {"root": str(PROJECT_ROOT)}
    agent = RenderBuilderAgent(str(tmp_path), config)
    exit_code = agent.run()

    assert exit_code == 0
    cmds = json.loads((tmp_path / "render" / "ffmpeg_commands.json").read_text())
    scene_cmd = " ".join(cmds["scenes"][0]["commands"][0]["command"])
    assert "-shortest" not in scene_cmd  # no audio input


def test_render_builder_missing_timeline(tmp_path: Path):
    from agents.render_builder import RenderBuilderAgent

    config = {"root": str(PROJECT_ROOT)}
    agent = RenderBuilderAgent(str(tmp_path), config)
    exit_code = agent.run()
    assert exit_code == 1


# ── Render Executor Agent Tests ─────────────────────────────────────


@patch("agents.render_executor.RenderExecutorAgent._exec_ffmpeg")
def test_render_executor_happy_path(mock_exec, tmp_path: Path):
    from agents.render_executor import RenderExecutorAgent

    mock_exec.return_value = (True, "")

    render_dir = tmp_path / "render"
    render_dir.mkdir(parents=True)

    ffmpeg_cmds = {
        "scenes": [
            {
                "scene_number": 1,
                "commands": [
                    {
                        "type": "generate_video",
                        "description": "Scene 1",
                        "command": ["ffmpeg", "-y", "-i", "dummy", "out.mp4"],
                    }
                ],
            }
        ],
        "concat_command": {
            "type": "concat",
            "description": "Concat all",
            "command": ["ffmpeg", "-f", "concat", "-i", "list.txt", "-c", "copy", str(render_dir / "final_video.mp4")],
        },
        "final_output": "render/final_video.mp4",
    }
    (render_dir / "ffmpeg_commands.json").write_text(json.dumps(ffmpeg_cmds))

    # Create a fake final video so stat works
    (render_dir / "final_video.mp4").write_bytes(b"\x00" * 100)

    config = {"root": str(PROJECT_ROOT)}
    agent = RenderExecutorAgent(str(tmp_path), config)
    exit_code = agent.run()

    assert exit_code == 0
    assert (render_dir / "render_manifest.json").exists()

    manifest = json.loads((render_dir / "render_manifest.json").read_text())
    assert manifest["scene_count"] == 1
    assert manifest["succeeded_scenes"] == 1
    assert manifest["failed_scenes"] == 0
    assert manifest["output_size_bytes"] == 100


@patch("agents.render_executor.RenderExecutorAgent._exec_ffmpeg")
def test_render_executor_scene_failure(mock_exec, tmp_path: Path):
    from agents.render_executor import RenderExecutorAgent

    render_dir = tmp_path / "render"
    render_dir.mkdir(parents=True)

    def _mock_exec(cmd):
        if "fail_scene" in " ".join(cmd):
            return (False, "simulated failure")
        return (True, "")

    mock_exec.side_effect = _mock_exec

    ffmpeg_cmds = {
        "scenes": [
            {
                "scene_number": 1,
                "commands": [
                    {
                        "type": "generate_video",
                        "description": "Scene 1",
                        "command": ["ffmpeg", "-y", "scene1.mp4"],
                    }
                ],
            },
            {
                "scene_number": 2,
                "commands": [
                    {
                        "type": "generate_video",
                        "description": "Scene 2",
                        "command": ["ffmpeg", "-y", "fail_scene", "scene2.mp4"],
                    }
                ],
            },
        ],
        "concat_command": {
            "type": "concat",
            "description": "Concat all",
            "command": ["ffmpeg", "-f", "concat", "-i", "list.txt", "-c", "copy", str(render_dir / "final_video.mp4")],
        },
        "final_output": "render/final_video.mp4",
    }
    (render_dir / "ffmpeg_commands.json").write_text(json.dumps(ffmpeg_cmds))
    (render_dir / "final_video.mp4").write_bytes(b"\x00" * 100)

    config = {"root": str(PROJECT_ROOT)}
    agent = RenderExecutorAgent(str(tmp_path), config)
    exit_code = agent.run()

    assert exit_code == 1  # has failures
    manifest = json.loads((render_dir / "render_manifest.json").read_text())
    assert manifest["succeeded_scenes"] == 1
    assert manifest["failed_scenes"] == 1
    assert len(manifest["errors"]) >= 1


@patch("agents.render_executor.RenderExecutorAgent._exec_ffmpeg")
def test_render_executor_ffmpeg_not_found(mock_exec, tmp_path: Path):
    from agents.render_executor import RenderExecutorAgent

    mock_exec.return_value = (False, "ffmpeg not found on system PATH")

    render_dir = tmp_path / "render"
    render_dir.mkdir(parents=True)

    ffmpeg_cmds = {
        "scenes": [
            {
                "scene_number": 1,
                "commands": [
                    {
                        "type": "generate_video",
                        "description": "Scene 1",
                        "command": ["ffmpeg", "-y", "dummy"],
                    }
                ],
            }
        ],
        "concat_command": {
            "type": "concat",
            "description": "Concat all",
            "command": ["ffmpeg"],
        },
        "final_output": "render/final_video.mp4",
    }
    (render_dir / "ffmpeg_commands.json").write_text(json.dumps(ffmpeg_cmds))

    config = {"root": str(PROJECT_ROOT)}
    agent = RenderExecutorAgent(str(tmp_path), config)
    exit_code = agent.run()
    assert exit_code == 1


@patch("agents.render_executor.RenderExecutorAgent._exec_ffmpeg")
def test_render_executor_missing_commands(mock_exec, tmp_path: Path):
    from agents.render_executor import RenderExecutorAgent

    config = {"root": str(PROJECT_ROOT)}
    agent = RenderExecutorAgent(str(tmp_path), config)
    exit_code = agent.run()
    assert exit_code == 1


# ── Orchestrator Integration Tests ──────────────────────────────────


def test_orchestrator_includes_wf4_stages():
    from shadow_protocol.lib.orchestrator_runner import STAGE_ORDER, AGENT_SCRIPT_MAP

    assert "timeline_builder" in STAGE_ORDER
    assert "render_builder" in STAGE_ORDER
    assert "render_executor" in STAGE_ORDER

    assert AGENT_SCRIPT_MAP["timeline_builder"] == "agents/timeline_builder.py"
    assert AGENT_SCRIPT_MAP["render_builder"] == "agents/render_builder.py"
    assert AGENT_SCRIPT_MAP["render_executor"] == "agents/render_executor.py"

    # Check ordering
    assert STAGE_ORDER.index("timeline_builder") < STAGE_ORDER.index("render_builder")
    assert STAGE_ORDER.index("render_builder") < STAGE_ORDER.index("render_executor")


# ── Camera Motion Filter Tests ──────────────────────────────────────


def test_all_camera_motions_produce_valid_filters():
    from agents.render_builder import CAMERA_MOTION_FILTERS

    assert "slow_zoom_in" in CAMERA_MOTION_FILTERS
    assert "slow_zoom_out" in CAMERA_MOTION_FILTERS
    assert "pan_left" in CAMERA_MOTION_FILTERS
    assert "pan_right" in CAMERA_MOTION_FILTERS
    assert "static" in CAMERA_MOTION_FILTERS

    for name, tmpl in CAMERA_MOTION_FILTERS.items():
        result = tmpl.format(frames=75, res="1920x1080", fps=25)
        assert "zoompan" in result
        assert "1920x1080" in result
        assert "25" in result or "fps" in result


# ── Config Tests ────────────────────────────────────────────────────


def test_paths_config_has_wf4_stages():
    path = Path("config/paths.json")
    assert path.exists()
    data = json.loads(path.read_text())
    stages = data.get("stages", {})
    assert "timeline_builder" in stages
    assert "render_builder" in stages
    assert "render_executor" in stages
    assert stages["timeline_builder"]["output"] == "render/timeline.json"
    assert stages["render_builder"]["output"] == "render/ffmpeg_commands.json"
    assert stages["render_executor"]["output"] == "render/final_video.mp4"


def test_schema_files_exist():
    assert _schema("timeline.json").exists()
    assert _schema("ffmpeg_commands.json").exists()
    assert _schema("render_manifest.json").exists()
