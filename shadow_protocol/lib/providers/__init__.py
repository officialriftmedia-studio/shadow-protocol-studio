"""Provider registry — resolve providers by name."""

from __future__ import annotations
from typing import Any

from shadow_protocol.lib.providers.base import MediaProvider, ProviderResult
from shadow_protocol.lib.providers.image_provider import GoogleImagenProvider
from shadow_protocol.lib.providers.voice_provider import GoogleTTSProvider
from shadow_protocol.lib.providers.magnific_provider import MagnificProvider

_REGISTRY: dict[str, type[MediaProvider]] = {
    "google_imagen": GoogleImagenProvider,
    "google_tts": GoogleTTSProvider,
    "magnific": MagnificProvider,
}


def resolve_provider(name: str, config: dict[str, Any] | None = None) -> MediaProvider:
    cls = _REGISTRY.get(name)
    if cls is None:
        raise ValueError(
            f"Unknown provider: {name}. "
            f"Available: {', '.join(sorted(_REGISTRY))}"
        )
    return cls(config or {})


def list_providers() -> list[str]:
    return list(_REGISTRY.keys())


def register_provider(name: str, cls: type[MediaProvider]) -> None:
    _REGISTRY[name] = cls


__all__ = [
    "MediaProvider",
    "ProviderResult",
    "resolve_provider",
    "list_providers",
    "register_provider",
]
