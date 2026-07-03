from __future__ import annotations
import hashlib
import os
from pathlib import Path
from typing import Any

import httpx

from shadow_protocol.lib.providers.base import MediaProvider, ProviderResult


class OpenAIImageProvider(MediaProvider):
    name = "openai_image"

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}
        self.api_key = os.environ.get("OPENAI_API_KEY") or self.config.get("api_key", "")
        self.timeout = self.config.get("timeout", 60)

    def generate(
        self, prompt: str | dict, output_dir: str | Path, **kwargs
    ) -> ProviderResult:
        if isinstance(prompt, dict):
            scene_id = prompt.get("scene_id", 0)
            prompt_text = prompt.get("prompt", str(prompt))
            aspect = prompt.get("aspect_ratio", "16:9")
        else:
            scene_id = 0
            prompt_text = prompt
            aspect = "16:9"

        size = "1792x1024" if aspect == "16:9" else "1024x1024"
        model = kwargs.get("model", "dall-e-3")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": model,
            "prompt": prompt_text,
            "n": 1,
            "size": size,
            "response_format": "b64_json",
        }

        resp = httpx.post(
            "https://api.openai.com/v1/images/generations",
            json=body,
            headers=headers,
            timeout=self.timeout,
        )
        if resp.status_code != 200:
            detail = resp.text[:300]
            return ProviderResult(
                success=False,
                error=f"OpenAI API error {resp.status_code}: {detail}",
            )

        data = resp.json()
        b64_json = data["data"][0]["b64_json"]

        import base64
        image_bytes = base64.b64decode(b64_json)

        filename = f"img_{scene_id:04d}.png"
        output_path = Path(output_dir) / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(image_bytes)

        checksum = hashlib.sha256(image_bytes).hexdigest()

        return ProviderResult(
            success=True,
            asset_path=output_path,
            mime_type="image/png",
            metadata={
                "scene_id": scene_id,
                "checksum": checksum,
                "model": model,
                "prompt_preview": prompt_text[:100],
            },
        )
