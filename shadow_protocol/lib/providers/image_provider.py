"""Google Imagen provider (mock) — generates placeholder PNG images."""

from __future__ import annotations
import hashlib
import struct
import zlib
from pathlib import Path

from shadow_protocol.lib.providers.base import MediaProvider, ProviderResult


class GoogleImagenProvider(MediaProvider):
    name = "google_imagen"

    def generate(
        self, prompt: str | dict, output_dir: str | Path, **kwargs
    ) -> ProviderResult:
        if isinstance(prompt, dict):
            scene_id = prompt.get("scene_id", 0)
            prompt_text = prompt.get("prompt", str(prompt))
        else:
            scene_id = hash(prompt) % 100000
            prompt_text = prompt

        filename = f"img_{scene_id:04d}.png"
        output_path = Path(output_dir) / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)

        r = (scene_id * 37) % 256
        g = (scene_id * 73) % 256
        b = (scene_id * 151) % 256

        width, height = 64, 64
        raw_data = bytearray()
        for _ in range(height):
            raw_data.append(0)
            for _ in range(width):
                raw_data.extend(struct.pack("BBB", r, g, b))

        def _make_chunk(chunk_type: bytes, data: bytes) -> bytes:
            chunk = chunk_type + data
            crc = struct.pack(">I", zlib.crc32(chunk) & 0xFFFFFFFF)
            return struct.pack(">I", len(data)) + chunk + crc

        signature = b"\x89PNG\r\n\x1a\n"
        ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
        ihdr = _make_chunk(b"IHDR", ihdr_data)
        compressed = zlib.compress(bytes(raw_data))
        idat = _make_chunk(b"IDAT", compressed)
        iend = _make_chunk(b"IEND", b"")

        png_data = signature + ihdr + idat + iend
        output_path.write_bytes(png_data)

        checksum = hashlib.sha256(png_data).hexdigest()

        return ProviderResult(
            success=True,
            asset_path=output_path,
            mime_type="image/png",
            metadata={
                "scene_id": scene_id,
                "checksum": checksum,
                "width": width,
                "height": height,
                "prompt_preview": prompt_text[:100],
            },
        )
