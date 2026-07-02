"""YouTube Data API publisher interface (stub — no implementation).

This module defines the YouTubePublisher class following the PlatformPublisher
interface. Implementation requires OAuth 2.0 setup and google-api-python-client.

Usage (future):
    publisher = YouTubePublisher(api_key=..., client_secret=...)
    publisher.authenticate()
    result = publisher.upload(video_path, title="...", description="...", tags=[...])
"""

from __future__ import annotations
from pathlib import Path
from typing import Any

from shadow_protocol.lib.publishing.base import PlatformPublisher, PublishResult


class YouTubePublisher(PlatformPublisher):
    name = "youtube"

    def __init__(self, **kwargs: Any):
        self.config = kwargs

    def authenticate(self) -> bool:
        raise NotImplementedError("YouTubePublisher.authenticate() not implemented")

    def upload(
        self,
        video_path: Path,
        title: str,
        description: str,
        tags: list[str],
        thumbnail_path: Path | None = None,
        **kwargs: Any,
    ) -> PublishResult:
        raise NotImplementedError("YouTubePublisher.upload() not implemented")

    def update_metadata(
        self,
        video_id: str,
        title: str | None = None,
        description: str | None = None,
        tags: list[str] | None = None,
        **kwargs: Any,
    ) -> PublishResult:
        raise NotImplementedError("YouTubePublisher.update_metadata() not implemented")

    def delete(self, video_id: str) -> PublishResult:
        raise NotImplementedError("YouTubePublisher.delete() not implemented")
