from __future__ import annotations
import hashlib
import json
import os
import re
import time
import wave
from pathlib import Path
from typing import Any

from google import genai
from google.genai import types
from google.genai.errors import ClientError

from shadow_protocol.lib.providers.base import MediaProvider, ProviderResult


class GeminiVoiceProvider(MediaProvider):
    name = "gemini_voice"

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}
        api_key = os.environ.get("GEMINI_API_KEY", os.environ.get("GOOGLE_API_KEY"))
        self.client = genai.Client(api_key=api_key)

    def _call_with_retry(self, model: str, text: str, config) -> Any:
        max_attempts = 10
        for attempt in range(max_attempts):
            try:
                return self.client.models.generate_content(
                    model=model, contents=text, config=config,
                )
            except ClientError as e:
                msg = str(e)
                if "429" in msg or "RESOURCE_EXHAUSTED" in msg:
                    delay = 30
                    m = re.search(r'retryDelay["\']\s*:\s*(\d+)', msg)
                    if m:
                        delay = int(m.group(1)) + 2
                    print(f"    Rate limited, waiting {delay}s (attempt {attempt+1}/{max_attempts})")
                    time.sleep(delay)
                    continue
                raise
        raise RuntimeError(f"Failed after {max_attempts} retries")

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

        model = kwargs.get("model", "gemini-2.5-flash-preview-tts")

        config = types.GenerateContentConfig(
            response_modalities=["AUDIO"],
        )

        response = self._call_with_retry(model, text, config)

        audio_data = None
        mime_type = ""
        for part in response.candidates[0].content.parts:
            if hasattr(part, "inline_data") and part.inline_data:
                audio_data = part.inline_data.data
                mime_type = part.inline_data.mime_type
                break

        if not audio_data:
            return ProviderResult(
                success=False,
                error="No audio data in Gemini response",
            )

        filename = f"voice_scene{scene_id:04d}_seg{seg_idx:04d}.wav"
        output_path = Path(output_dir) / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if mime_type.startswith("audio/L16"):
            params = dict(p.split("=") for p in mime_type.split(";")[1:] if "=" in p)
            sample_rate = int(params.get("rate", "24000"))
            with wave.open(str(output_path), "w") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)
                wf.writeframes(audio_data)
            bytes_per_sec = sample_rate * 2
        else:
            output_path.write_bytes(audio_data)
            bytes_per_sec = 24000 * 2

        checksum = hashlib.sha256(output_path.read_bytes()).hexdigest()
        duration = round(len(audio_data) / bytes_per_sec, 2)

        return ProviderResult(
            success=True,
            asset_path=output_path,
            mime_type="audio/wav",
            metadata={
                "scene_id": scene_id,
                "segment_index": seg_idx,
                "checksum": checksum,
                "model": model,
                "duration_seconds": duration,
                "text_preview": text[:100],
            },
        )
