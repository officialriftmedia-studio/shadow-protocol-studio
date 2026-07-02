"""Analytics ingestion interface (stub — no implementation).

Defines the contract for collecting and querying video performance data.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class VideoAnalytics:
    video_id: str
    views: int = 0
    likes: int = 0
    comments: int = 0
    watch_time_minutes: float = 0.0
    period_start: datetime | None = None
    period_end: datetime | None = None
    raw: dict[str, Any] = field(default_factory=dict)


class AnalyticsCollector(ABC):
    """Interface for collecting video analytics from platforms."""

    @abstractmethod
    def get_analytics(
        self,
        video_id: str,
        start_date: datetime,
        end_date: datetime,
    ) -> VideoAnalytics:
        ...

    @abstractmethod
    def get_lifetime_analytics(self, video_id: str) -> VideoAnalytics:
        ...
