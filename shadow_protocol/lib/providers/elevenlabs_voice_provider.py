from __future__ import annotations
import hashlib
import os
from pathlib import Path
from typing import Any

import httpx

from shadow_protocol.lib.providers.base import MediaProvider, ProviderResult


class ElevenLabsVoiceProvider(MediaProvider):
    name = "elevenlabs"

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}
        self.api_key = os.environ.get("ELEVENLABS_API_KEY") or self.config.get("api_key", "")
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

        voice_id = (
            os.environ.get("VOICE_ID")
            or self.config.get("voice_id")
            or "21m00Tcm4TlvDq8ikWAM"
        )
        model = kwargs.get("model", "eleven_multilingual_v2")

        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json",
        }
        body = {
            "text": text,
            "model_id": model,
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
            },
        }

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

        resp = httpx.post(url, json=body, headers=headers, timeout=self.timeout)
        if resp.status_code != 200:
            detail = resp.text[:300]
            return ProviderResult(
                success=False,
                error=f"ElevenLabs API error {resp.status_code}: {detail}",
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
                "voice_id": voice_id,
                "text_preview": text[:100],
            },
        )
