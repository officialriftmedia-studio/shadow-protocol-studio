from __future__ import annotations
import hashlib
import wave
from pathlib import Path
from typing import Any

from piper import PiperVoice

from shadow_protocol.lib.providers.base import MediaProvider, ProviderResult


class PiperVoiceProvider(MediaProvider):
    name = "piper_voice"

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}
        self.models_dir = Path(self.config.get("models_dir", "models/piper"))

    def _load_voice(self, model: str) -> PiperVoice:
        models_dir = self.models_dir
        voice_name = model or self.config.get("voice", "en_US-amy-medium")
        model_path = models_dir / f"{voice_name}.onnx"
        if not model_path.exists():
            raise FileNotFoundError(f"Piper model not found: {model_path}")
        return PiperVoice.load(str(model_path))

    def generate(
        self, segment: str | dict, output_dir: str | Path, **kwargs
    ) -> ProviderResult:
        if isinstance(segment, dict):
            scene_id = segment.get("scene_id", 0)
            seg_idx = segment.get("segment_index", 0)
            text = segment.get("text", "")
        else:
            scene_id = 0
            seg_idx = 0
            text = segment

        filename = f"voice_scene{scene_id:04d}_seg{seg_idx:04d}.wav"
        output_path = Path(output_dir) / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)

        voice_name = kwargs.get("model") or self.config.get("voice", "en_US-amy-medium")
        voice = self._load_voice(voice_name)
        audio_gen = voice.synthesize(text)
        frames = b"".join(chunk.audio_int16_bytes for chunk in audio_gen)
        sr = voice.config.sample_rate

        with wave.open(str(output_path), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sr)
            wf.writeframes(frames)

        checksum = hashlib.sha256(output_path.read_bytes()).hexdigest()
        duration = round(len(frames) / (sr * 2), 2)

        return ProviderResult(
            success=True,
            asset_path=output_path,
            mime_type="audio/wav",
            metadata={
                "scene_id": scene_id,
                "segment_index": seg_idx,
                "checksum": checksum,
                "model": "piper-en_US-amy-low",
                "duration_seconds": duration,
                "text_preview": text[:100],
            },
        )
