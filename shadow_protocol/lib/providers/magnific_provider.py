"""Magnific upscaler provider (mock) — copies input file as placeholder upscale."""

from __future__ import annotations
from pathlib import Path

from shadow_protocol.lib.providers.base import MediaProvider, ProviderResult


class MagnificProvider(MediaProvider):
    name = "magnific"

    def generate(
        self, input_path: str | Path, output_dir: str | Path, **kwargs
    ) -> ProviderResult:
        input_path = Path(input_path)
        if not input_path.exists():
            return ProviderResult(
                success=False, error=f"Input file not found: {input_path}"
            )

        output_path = Path(output_dir) / f"upscaled_{input_path.name}"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        output_path.write_bytes(input_path.read_bytes())

        return ProviderResult(
            success=True,
            asset_path=output_path,
            mime_type=_guess_mime(input_path),
            metadata={
                "original": str(input_path),
                "upscale_factor": 1,
                "original_size_bytes": input_path.stat().st_size,
            },
        )


def _guess_mime(path: Path) -> str:
    suffix = path.suffix.lower()
    mapping = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".wav": "audio/wav",
    }
    return mapping.get(suffix, "application/octet-stream")
