"""Provider registry — resolve providers by name."""

from __future__ import annotations
from typing import Any

from shadow_protocol.lib.providers.base import MediaProvider, ProviderResult
from shadow_protocol.lib.providers.image_provider import GoogleImagenProvider
from shadow_protocol.lib.providers.voice_provider import GoogleTTSProvider
from shadow_protocol.lib.providers.magnific_provider import MagnificProvider
from shadow_protocol.lib.providers.openai_image_provider import OpenAIImageProvider
from shadow_protocol.lib.providers.elevenlabs_voice_provider import ElevenLabsVoiceProvider
from shadow_protocol.lib.providers.openai_voice_provider import OpenAIVoiceProvider
from shadow_protocol.lib.providers.magnific_image_provider import MagnificImageProvider
from shadow_protocol.lib.providers.gemini_voice_provider import GeminiVoiceProvider
from shadow_protocol.lib.providers.piper_voice_provider import PiperVoiceProvider

_REGISTRY: dict[str, type[MediaProvider]] = {
    "google_imagen": GoogleImagenProvider,
    "google_tts": GoogleTTSProvider,
    "magnific": MagnificProvider,
    "openai_image": OpenAIImageProvider,
    "elevenlabs": ElevenLabsVoiceProvider,
    "openai_voice": OpenAIVoiceProvider,
    "magnific_image": MagnificImageProvider,
    "gemini_voice": GeminiVoiceProvider,
    "piper_voice": PiperVoiceProvider,
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
