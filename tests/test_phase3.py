"""Tests for Phase 3 modules: providers, manifest, provider_cache, agents."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from shadow_protocol.lib.providers.base import MediaProvider, ProviderResult
from shadow_protocol.lib.providers import (
    resolve_provider,
    list_providers,
    register_provider,
)
from shadow_protocol.lib.providers.image_provider import GoogleImagenProvider
from shadow_protocol.lib.providers.voice_provider import GoogleTTSProvider
from shadow_protocol.lib.providers.magnific_provider import MagnificProvider
from shadow_protocol.lib.manifest import (
    create_manifest,
    load_manifest,
    save_manifest,
    add_asset,
    update_asset,
    finalize_manifest,
    get_assets_by_type,
    get_asset_count,
)
from shadow_protocol.lib.provider_cache import (
    get_cached,
    set_cache,
    invalidate,
    clear_all,
    get_cache_metrics,
)


# ── Provider Base ───────────────────────────────────────────────────


def test_provider_base_abstract():
    class ConcreteProvider(MediaProvider):
        name = "test"

        def generate(self, prompt, output_dir, **kwargs):
            return ProviderResult(success=True)

    p = ConcreteProvider({"key": "val"})
    assert p.name == "test"
    assert p.config == {"key": "val"}
    assert p.validate_config() == []
    result = p.generate("test", "/tmp")
    assert result.success is True


def test_provider_result_defaults():
    r = ProviderResult(success=True)
    assert r.asset_path is None
    assert r.mime_type == ""
    assert r.metadata == {}


def test_provider_result_full():
    r = ProviderResult(
        success=True,
        asset_path=Path("/tmp/test.png"),
        mime_type="image/png",
        metadata={"key": "val"},
    )
    assert r.asset_path == Path("/tmp/test.png")
    assert r.mime_type == "image/png"


# ── Provider Registry ────────────────────────────────────────────────


def test_resolve_google_imagen():
    p = resolve_provider("google_imagen")
    assert isinstance(p, GoogleImagenProvider)


def test_resolve_google_tts():
    p = resolve_provider("google_tts")
    assert isinstance(p, GoogleTTSProvider)


def test_resolve_magnific():
    p = resolve_provider("magnific")
    assert isinstance(p, MagnificProvider)


def test_resolve_unknown():
    import pytest

    with pytest.raises(ValueError, match="Unknown provider"):
        resolve_provider("nonexistent")


def test_list_providers():
    providers = list_providers()
    assert "google_imagen" in providers
    assert "google_tts" in providers
    assert "magnific" in providers


def test_register_provider():
    class FakeProvider(MediaProvider):
        name = "fake"

        def generate(self, prompt, output_dir, **kwargs):
            return ProviderResult(success=True)

    register_provider("fake_test", FakeProvider)
    assert "fake_test" in list_providers()
    p = resolve_provider("fake_test")
    assert isinstance(p, FakeProvider)


# ── Google Imagen Provider ──────────────────────────────────────────


def test_imagen_generates_png(tmp_path: Path):
    provider = GoogleImagenProvider()
    result = provider.generate(
        {"scene_id": 42, "prompt": "A dark room"},
        output_dir=tmp_path / "images",
    )
    assert result.success is True
    assert result.asset_path.exists()
    assert result.mime_type == "image/png"
    assert result.asset_path.suffix == ".png"
    assert b"img_0042" in result.asset_path.name.encode()
    # Verify it's a valid PNG (header signature)
    data = result.asset_path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"


def test_imagen_accepts_string_prompt(tmp_path: Path):
    provider = GoogleImagenProvider()
    result = provider.generate("Just a string prompt", output_dir=tmp_path)
    assert result.success is True
    assert result.asset_path.exists()


def test_imagen_metadata(tmp_path: Path):
    provider = GoogleImagenProvider()
    result = provider.generate(
        {"scene_id": 7, "prompt": "Test prompt"},
        output_dir=tmp_path,
    )
    assert result.metadata["scene_id"] == 7
    assert result.metadata["width"] == 64
    assert result.metadata["height"] == 64
    assert "checksum" in result.metadata


# ── Google TTS Provider ──────────────────────────────────────────────


def test_tts_generates_wav(tmp_path: Path):
    provider = GoogleTTSProvider()
    result = provider.generate(
        {"scene_id": 1, "segment_index": 0, "text": "Hello world"},
        output_dir=tmp_path / "voice",
    )
    assert result.success is True
    assert result.asset_path.exists()
    assert result.mime_type == "audio/wav"
    assert result.asset_path.suffix == ".wav"
    # Verify WAV header (RIFF)
    data = result.asset_path.read_bytes()
    assert data[:4] == b"RIFF"


def test_tts_accepts_string(tmp_path: Path):
    provider = GoogleTTSProvider()
    result = provider.generate("Plain text segment", output_dir=tmp_path)
    assert result.success is True


def test_tts_metadata(tmp_path: Path):
    provider = GoogleTTSProvider()
    result = provider.generate(
        {"scene_id": 3, "segment_index": 1, "text": "Test narration"},
        output_dir=tmp_path,
    )
    assert result.metadata["scene_id"] == 3
    assert result.metadata["segment_index"] == 1
    assert result.metadata["duration_seconds"] > 0
    assert "checksum" in result.metadata


# ── Magnific Provider ────────────────────────────────────────────────


def test_magnific_upscales_image(tmp_path: Path):
    src = tmp_path / "input.png"
    src.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 20)

    provider = MagnificProvider()
    result = provider.generate(src, output_dir=tmp_path / "upscaled")
    assert result.success is True
    assert result.asset_path.exists()
    assert result.asset_path.name.startswith("upscaled_")
    assert result.mime_type == "image/png"


def test_magnific_missing_input(tmp_path: Path):
    provider = MagnificProvider()
    result = provider.generate(
        tmp_path / "nonexistent.png", output_dir=tmp_path
    )
    assert result.success is False
    assert "not found" in (result.error or "")


# ── Manifest ─────────────────────────────────────────────────────────


def test_create_manifest():
    m = create_manifest("case_001")
    assert m["case_id"] == "case_001"
    assert m["assets"] == []
    assert m["generated_at"] == ""
    assert m["version"] == "1.0.0"


def test_add_asset():
    m = create_manifest("case_001")
    asset_id = add_asset(m, {"asset_id": "img_0001", "type": "image"})
    assert asset_id == "img_0001"
    assert len(m["assets"]) == 1
    assert "created_at" in m["assets"][0]


def test_add_asset_auto_id():
    m = create_manifest("case_001")
    add_asset(m, {"type": "image"})
    assert m["assets"][0]["asset_id"] == "asset_0000"


def test_update_asset():
    m = create_manifest("case_001")
    add_asset(m, {"asset_id": "img_0001", "type": "image", "status": "pending"})
    result = update_asset(m, "img_0001", {"status": "completed"})
    assert result is True
    assert m["assets"][0]["status"] == "completed"


def test_update_asset_not_found():
    m = create_manifest("case_001")
    result = update_asset(m, "nonexistent", {"status": "completed"})
    assert result is False


def test_finalize_manifest():
    m = create_manifest("case_001")
    assert m["generated_at"] == ""
    finalize_manifest(m)
    assert m["generated_at"] != ""


def test_get_assets_by_type():
    m = create_manifest("case_001")
    add_asset(m, {"asset_id": "a1", "type": "image"})
    add_asset(m, {"asset_id": "a2", "type": "voice"})
    add_asset(m, {"asset_id": "a3", "type": "image"})
    images = get_assets_by_type(m, "image")
    assert len(images) == 2
    voices = get_assets_by_type(m, "voice")
    assert len(voices) == 1


def test_get_asset_count():
    m = create_manifest("case_001")
    assert get_asset_count(m) == 0
    add_asset(m, {"type": "image"})
    assert get_asset_count(m) == 1


def test_save_and_load_manifest(tmp_path: Path):
    m = create_manifest("case_001")
    add_asset(m, {"asset_id": "img_0001", "type": "image"})
    path = tmp_path / "manifest.json"
    save_manifest(path, m)

    loaded = load_manifest(path)
    assert loaded["case_id"] == "case_001"
    assert len(loaded["assets"]) == 1


def test_load_manifest_nonexistent(tmp_path: Path):
    m = load_manifest(tmp_path / "nonexistent.json")
    assert m["case_id"] == ""
    assert m["assets"] == []


# ── Provider Cache ───────────────────────────────────────────────────


def test_provider_cache_set_and_get(tmp_path: Path):
    episode_dir = tmp_path / "episode"
    episode_dir.mkdir(parents=True)

    data = {"asset_id": "img_0001", "type": "image"}
    set_cache(episode_dir, "google_imagen", "imagen-3.0", "img_0", data)

    hit, cached = get_cached(episode_dir, "google_imagen", "imagen-3.0", "img_0")
    assert hit is True
    assert cached == data


def test_provider_cache_miss(tmp_path: Path):
    episode_dir = tmp_path / "episode"
    hit, cached = get_cached(episode_dir, "google_imagen", "imagen-3.0", "nonexistent")
    assert hit is False
    assert cached is None


def test_provider_cache_different_key(tmp_path: Path):
    episode_dir = tmp_path / "episode"
    episode_dir.mkdir(parents=True)

    set_cache(episode_dir, "google_imagen", "imagen-3.0", "img_0", {"id": 0})
    hit, cached = get_cached(episode_dir, "google_imagen", "imagen-3.0", "img_1")
    assert hit is False


def test_provider_cache_invalidate_all(tmp_path: Path):
    episode_dir = tmp_path / "episode"
    episode_dir.mkdir(parents=True)

    set_cache(episode_dir, "google_imagen", "imagen-3.0", "img_0", {"id": 0})
    set_cache(episode_dir, "google_tts", "wavesynth", "voice_0", {"id": 1})

    invalidate(episode_dir)  # clear all
    metrics = get_cache_metrics(episode_dir)
    assert metrics["total_entries"] == 0


def test_provider_cache_invalidate_by_provider(tmp_path: Path):
    episode_dir = tmp_path / "episode"
    episode_dir.mkdir(parents=True)

    set_cache(episode_dir, "google_imagen", "imagen-3.0", "img_0", {"id": 0})
    set_cache(episode_dir, "google_tts", "wavesynth", "voice_0", {"id": 1})

    invalidate(episode_dir, provider="google_imagen")
    metrics = get_cache_metrics(episode_dir)
    assert metrics["total_entries"] == 1
    assert metrics["providers"].get("google_tts") == 1


def test_provider_cache_clear_all(tmp_path: Path):
    episode_dir = tmp_path / "episode"
    episode_dir.mkdir(parents=True)

    set_cache(episode_dir, "google_imagen", "imagen-3.0", "img_0", {"id": 0})
    clear_all(episode_dir)
    metrics = get_cache_metrics(episode_dir)
    assert metrics["total_entries"] == 0


def test_provider_cache_metrics(tmp_path: Path):
    episode_dir = tmp_path / "episode"
    episode_dir.mkdir(parents=True)

    metrics = get_cache_metrics(episode_dir)
    assert metrics["total_entries"] == 0

    set_cache(episode_dir, "google_imagen", "imagen-3.0", "img_0", {"id": 0})
    set_cache(episode_dir, "google_imagen", "imagen-3.0", "img_1", {"id": 1})
    set_cache(episode_dir, "google_tts", "wavesynth", "voice_0", {"id": 2})

    metrics = get_cache_metrics(episode_dir)
    assert metrics["total_entries"] == 3
    assert metrics["providers"]["google_imagen"] == 2
    assert metrics["providers"]["google_tts"] == 1


# ── Image Generator Agent ────────────────────────────────────────────


def test_image_generator_agent_with_prompts(tmp_path: Path):
    from agents.image_generator import ImageGeneratorAgent

    # Setup: write image_prompts.json
    prompts = {
        "prompts": [
            {"scene_id": 1, "prompt": "A dark room", "style": "cinematic", "aspect_ratio": "16:9"},
            {"scene_id": 2, "prompt": "A bright sky", "style": "cinematic", "aspect_ratio": "16:9"},
        ]
    }
    (tmp_path / "image_prompts.json").write_text(json.dumps(prompts))

    config = {"root": str(tmp_path.parent.parent)}

    agent = ImageGeneratorAgent(str(tmp_path), config)
    exit_code = agent.run()

    assert exit_code == 0
    assert (tmp_path / "assets" / "images" / "img_0001.png").exists()
    assert (tmp_path / "assets" / "images" / "img_0002.png").exists()
    assert (tmp_path / "assets" / "manifests" / "asset_manifest.json").exists()

    manifest = json.loads((tmp_path / "assets" / "manifests" / "asset_manifest.json").read_text())
    assert len(manifest["assets"]) == 2
    assert manifest["assets"][0]["asset_id"] == "img_0001"


def test_image_generator_agent_no_prompts(tmp_path: Path):
    from agents.image_generator import ImageGeneratorAgent

    (tmp_path / "image_prompts.json").write_text(json.dumps({"prompts": []}))

    config = {"root": str(tmp_path.parent.parent)}
    agent = ImageGeneratorAgent(str(tmp_path), config)
    exit_code = agent.run()
    assert exit_code == 1  # No prompts


def test_image_generator_agent_missing_file(tmp_path: Path):
    from agents.image_generator import ImageGeneratorAgent

    config = {"root": str(tmp_path.parent.parent)}
    agent = ImageGeneratorAgent(str(tmp_path), config)
    exit_code = agent.run()
    assert exit_code == 1  # Missing prompts file


def test_image_generator_agent_caching(tmp_path: Path):
    from agents.image_generator import ImageGeneratorAgent

    prompts = {
        "prompts": [
            {"scene_id": 1, "prompt": "A dark room", "style": "cinematic", "aspect_ratio": "16:9"},
        ]
    }
    (tmp_path / "image_prompts.json").write_text(json.dumps(prompts))

    config = {"root": str(tmp_path.parent.parent)}

    # First run should generate
    agent1 = ImageGeneratorAgent(str(tmp_path), config)
    exit_code1 = agent1.run()
    assert exit_code1 == 0

    # Verify cache was populated
    from shadow_protocol.lib.provider_cache import get_cached
    hit, _ = get_cached(str(tmp_path), "google_imagen", "imagen-3.0", "img_1")
    assert hit is True


# ── Voice Generator Agent ────────────────────────────────────────────


def test_voice_generator_agent_with_segments(tmp_path: Path):
    from agents.voice_generator import VoiceGeneratorAgent

    segments = {
        "segments": [
            {"scene_id": 1, "segment_index": 0, "text": "Hello world", "estimated_duration_seconds": 2.0},
            {"scene_id": 1, "segment_index": 1, "text": "Second segment", "estimated_duration_seconds": 1.5},
        ]
    }
    (tmp_path / "voiceover_segments.json").write_text(json.dumps(segments))

    config = {"root": str(tmp_path.parent.parent)}

    agent = VoiceGeneratorAgent(str(tmp_path), config)
    exit_code = agent.run()

    assert exit_code == 0
    assert (tmp_path / "assets" / "voice" / "voice_scene0001_seg0000.wav").exists()
    assert (tmp_path / "assets" / "voice" / "voice_scene0001_seg0001.wav").exists()
    assert (tmp_path / "assets" / "manifests" / "asset_manifest.json").exists()

    manifest = json.loads(
        (tmp_path / "assets" / "manifests" / "asset_manifest.json").read_text()
    )
    assert len(manifest["assets"]) == 2
    assert manifest["assets"][0]["type"] == "voice"


def test_voice_generator_agent_no_segments(tmp_path: Path):
    from agents.voice_generator import VoiceGeneratorAgent

    (tmp_path / "voiceover_segments.json").write_text(json.dumps({"segments": []}))

    config = {"root": str(tmp_path.parent.parent)}
    agent = VoiceGeneratorAgent(str(tmp_path), config)
    exit_code = agent.run()
    assert exit_code == 1


def test_voice_generator_agent_missing_file(tmp_path: Path):
    from agents.voice_generator import VoiceGeneratorAgent

    config = {"root": str(tmp_path.parent.parent)}
    agent = VoiceGeneratorAgent(str(tmp_path), config)
    exit_code = agent.run()
    assert exit_code == 1


# ── Orchestrator Integration ──────────────────────────────────────────


def test_orchestrator_stage_order_includes_new_stages():
    from shadow_protocol.lib.orchestrator_runner import STAGE_ORDER, AGENT_SCRIPT_MAP

    assert "image_generator" in STAGE_ORDER
    assert "voice_generator" in STAGE_ORDER
    assert "image_generator" in AGENT_SCRIPT_MAP
    assert "voice_generator" in AGENT_SCRIPT_MAP
    assert AGENT_SCRIPT_MAP["image_generator"] == "agents/image_generator.py"
    assert AGENT_SCRIPT_MAP["voice_generator"] == "agents/voice_generator.py"


def test_orchestrator_list_output_files():
    from shadow_protocol.lib.orchestrator_runner import _list_output_files

    import tempfile
    with tempfile.TemporaryDirectory() as d:
        episode_dir = Path(d)
        (episode_dir / "assets" / "images").mkdir(parents=True)
        (episode_dir / "assets" / "images" / "img_0001.png").write_bytes(b"\x00")
        (episode_dir / "assets" / "manifests").mkdir(parents=True)
        (episode_dir / "assets" / "manifests" / "asset_manifest.json").write_text("{}")

        files = _list_output_files(episode_dir, "image_generator")
        assert any("img_0001.png" in f for f in files)
        assert any("asset_manifest.json" in f for f in files)

        # voice_generator with no files yet
        files2 = _list_output_files(episode_dir, "voice_generator")
        assert "assets/manifests/asset_manifest.json" in files2


# ── Config files validation ──────────────────────────────────────────


def test_providers_config_valid_json():
    path = Path("config/providers.json")
    assert path.exists()
    data = json.loads(path.read_text())
    assert "providers" in data
    assert "google_imagen" in data["providers"]
    assert "google_tts" in data["providers"]
    assert "magnific" in data["providers"]


def test_paths_config_includes_new_stages():
    path = Path("config/paths.json")
    assert path.exists()
    data = json.loads(path.read_text())
    stages = data.get("stages", {})
    assert "image_generator" in stages
    assert "voice_generator" in stages
    assert stages["image_generator"]["output"] == "assets/images/"
    assert stages["voice_generator"]["output"] == "assets/voice/"
