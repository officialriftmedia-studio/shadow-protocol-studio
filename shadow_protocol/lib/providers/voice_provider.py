"""Google TTS provider (mock) — generates placeholder WAV audio files."""

from __future__ import annotations
import hashlib
import math
import struct
import wave
from pathlib import Path

from shadow_protocol.lib.providers.base import MediaProvider, ProviderResult


class GoogleTTSProvider(MediaProvider):
    name = "google_tts"

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

        duration = max(1.0, len(text) * 0.05)
        sample_rate = 22050
        num_samples = int(duration * sample_rate)

        with wave.open(str(output_path), "w") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)

            samples = []
            for i in range(num_samples):
                t = i / sample_rate
                val = int(800 * math.sin(2 * math.pi * 100 * t))
                samples.append(struct.pack("<h", val))

            wf.writeframes(b"".join(samples))

        checksum = hashlib.sha256(output_path.read_bytes()).hexdigest()

        return ProviderResult(
            success=True,
            asset_path=output_path,
            mime_type="audio/wav",
            metadata={
                "scene_id": scene_id,
                "segment_index": seg_idx,
                "duration_seconds": round(duration, 2),
                "checksum": checksum,
                "text_preview": text[:100],
            },
        )
