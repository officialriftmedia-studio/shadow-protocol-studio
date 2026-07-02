"""Abstract base class for platform publishing interfaces."""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class PublishResult:
    success: bool
    platform: str = ""
    video_id: str | None = None
    url: str | None = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class PlatformPublisher(ABC):
    """Interface for publishing to a video platform (YouTube, Vimeo, etc.)."""

    name: str = ""

    @abstractmethod
    def authenticate(self) -> bool:
        ...

    @abstractmethod
    def upload(
        self,
        video_path: Path,
        title: str,
        description: str,
        tags: list[str],
        thumbnail_path: Path | None = None,
        **kwargs: Any,
    ) -> PublishResult:
        ...

    @abstractmethod
    def update_metadata(
        self,
        video_id: str,
        title: str | None = None,
        description: str | None = None,
        tags: list[str] | None = None,
        **kwargs: Any,
    ) -> PublishResult:
        ...

    @abstractmethod
    def delete(self, video_id: str) -> PublishResult:
        ...
