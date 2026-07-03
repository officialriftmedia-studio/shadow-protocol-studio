from __future__ import annotations
import hashlib
import os
from pathlib import Path
from typing import Any

from google import genai
from google.genai import types

from shadow_protocol.lib.providers.base import MediaProvider, ProviderResult


class GoogleImagenProvider(MediaProvider):
    name = "google_imagen"

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}
        api_key = os.environ.get("GEMINI_API_KEY", os.environ.get("GOOGLE_API_KEY"))
        self.client = genai.Client(api_key=api_key)

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

        model = kwargs.get("model", "imagen-3.0-generate-001")
        aspect_ratio = aspect if aspect in ("1:1", "3:4", "4:3", "9:16", "16:9") else "16:9"

        config = types.GenerateImagesConfig(
            aspect_ratio=aspect_ratio,
            number_of_images=1,
        )

        response = self.client.models.generate_images(
            model=model,
            prompt=prompt_text,
            config=config,
        )

        if not response.generated_images:
            return ProviderResult(
                success=False,
                error="No images returned by Imagen",
            )

        gen_image = response.generated_images[0]
        image = gen_image.image

        if not image or not image.image_bytes:
            return ProviderResult(
                success=False,
                error="No image data in response",
            )

        mime_type = image.mime_type or "image/png"
        ext = ".png"
        if mime_type == "image/jpeg":
            ext = ".jpg"
        elif mime_type == "image/webp":
            ext = ".webp"

        filename = f"img_{scene_id:04d}{ext}"
        output_path = Path(output_dir) / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(image.image_bytes)

        checksum = hashlib.sha256(image.image_bytes).hexdigest()

        return ProviderResult(
            success=True,
            asset_path=output_path,
            mime_type=mime_type,
            metadata={
                "scene_id": scene_id,
                "checksum": checksum,
                "model": model,
                "prompt_preview": prompt_text[:100],
                "enhanced_prompt": gen_image.enhanced_prompt or "",
            },
        )
