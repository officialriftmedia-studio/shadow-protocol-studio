from __future__ import annotations
import hashlib
import os
import time
from pathlib import Path
from typing import Any

import httpx

from shadow_protocol.lib.providers.base import MediaProvider, ProviderResult


class MagnificImageProvider(MediaProvider):
    name = "magnific"

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}
        self.api_key = (
            os.environ.get("MAGNIFIC_API_KEY")
            or self.config.get("api_key", "")
        )
        self.base_url = "https://api.magnific.com"
        self.timeout = self.config.get("timeout", 120)
        self.poll_interval = self.config.get("poll_interval", 3)
        self.max_poll_time = self.config.get("max_poll_time", 120)

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

        model = kwargs.get("model", "realism")

        aspect_map = {
            "16:9": "widescreen_16_9",
            "9:16": "social_story_9_16",
            "1:1": "square_1_1",
            "4:3": "classic_4_3",
            "3:4": "traditional_3_4",
            "3:2": "standard_3_2",
            "2:3": "portrait_2_3",
        }
        aspect_ratio = aspect_map.get(aspect, "widescreen_16_9")

        headers = {
            "x-magnific-api-key": self.api_key,
            "Content-Type": "application/json",
        }

        body = {
            "prompt": prompt_text,
            "model": model,
            "aspect_ratio": aspect_ratio,
            "resolution": "2k",
        }

        resp = httpx.post(
            f"{self.base_url}/v1/ai/mystic",
            json=body,
            headers=headers,
            timeout=self.timeout,
        )
        if resp.status_code != 200:
            detail = resp.text[:300]
            return ProviderResult(
                success=False,
                error=f"Magnific API error {resp.status_code}: {detail}",
            )

        data = resp.json().get("data", {})
        task_id = data.get("task_id")
        if not task_id:
            return ProviderResult(
                success=False,
                error=f"No task_id in response: {resp.text[:300]}",
            )

        status = data.get("status", "")
        deadline = time.time() + self.max_poll_time

        while status not in ("COMPLETED", "FAILED") and time.time() < deadline:
            time.sleep(self.poll_interval)
            poll_resp = httpx.get(
                f"{self.base_url}/v1/ai/mystic/{task_id}",
                headers=headers,
                timeout=self.timeout,
            )
            if poll_resp.status_code != 200:
                return ProviderResult(
                    success=False,
                    error=f"Poll error {poll_resp.status_code}: {poll_resp.text[:300]}",
                )
            poll_data = poll_resp.json().get("data", {})
            status = poll_data.get("status", "")

        if status == "FAILED":
            return ProviderResult(
                success=False,
                error=f"Magnific task {task_id} failed",
            )
        if status != "COMPLETED":
            return ProviderResult(
                success=False,
                error=f"Magnific task {task_id} timed out after {self.max_poll_time}s",
            )

        generated_urls = poll_data.get("generated", [])
        if not generated_urls:
            return ProviderResult(
                success=False,
                error=f"Task completed but no image URLs: {poll_data}",
            )

        image_url = generated_urls[0]
        image_resp = httpx.get(image_url, timeout=self.timeout)
        if image_resp.status_code != 200:
            return ProviderResult(
                success=False,
                error=f"Failed to download image: {image_resp.status_code}",
            )

        image_bytes = image_resp.content

        filename = f"img_{scene_id:04d}.jpg"
        output_path = Path(output_dir) / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(image_bytes)

        checksum = hashlib.sha256(image_bytes).hexdigest()

        return ProviderResult(
            success=True,
            asset_path=output_path,
            mime_type="image/jpeg",
            metadata={
                "scene_id": scene_id,
                "checksum": checksum,
                "model": model,
                "task_id": task_id,
                "prompt_preview": prompt_text[:100],
            },
        )
