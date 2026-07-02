"""Abstract base class for media providers and result dataclass."""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ProviderResult:
    success: bool
    asset_path: Path | None = None
    mime_type: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


class MediaProvider(ABC):
    name: str = ""

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}

    @abstractmethod
    def generate(self, prompt: Any, output_dir: str | Path, **kwargs) -> ProviderResult:
        ...

    def validate_config(self) -> list[str]:
        return []
