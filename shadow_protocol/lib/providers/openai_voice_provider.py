from __future__ import annotations
import hashlib
import os
from pathlib import Path
from typing import Any

import httpx

from shadow_protocol.lib.providers.base import MediaProvider, ProviderResult


class OpenAIVoiceProvider(MediaProvider):
    name = "openai_voice"

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}
        self.api_key = os.environ.get("OPENAI_API_KEY") or self.config.get("api_key", "")
        self.timeout = self.config.get("timeout", 120)

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

        voice = kwargs.get("voice", "onyx")
        model = kwargs.get("model", "tts-1")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": model,
            "input": text,
            "voice": voice,
            "response_format": "mp3",
        }

        resp = httpx.post(
            "https://api.openai.com/v1/audio/speech",
            json=body,
            headers=headers,
            timeout=self.timeout,
        )
        if resp.status_code != 200:
            detail = resp.text[:300]
            return ProviderResult(
                success=False,
                error=f"OpenAI TTS API error {resp.status_code}: {detail}",
            )

        filename = f"voice_scene{scene_id:04d}_seg{seg_idx:04d}.mp3"
        output_path = Path(output_dir) / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(resp.content)

        checksum = hashlib.sha256(resp.content).hexdigest()

        return ProviderResult(
            success=True,
            asset_path=output_path,
            mime_type="audio/mpeg",
            metadata={
                "scene_id": scene_id,
                "segment_index": seg_idx,
                "checksum": checksum,
                "model": model,
                "voice": voice,
                "text_preview": text[:100],
            },
        )
