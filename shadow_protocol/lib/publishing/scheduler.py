"""Publishing scheduler interface (stub — no implementation).

Defines the contract for scheduling video publication at a future time.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class ScheduleResult:
    success: bool
    scheduled_time: datetime | None = None
    job_id: str | None = None
    error: str | None = None


class PublishScheduler(ABC):
    """Interface for scheduling future video publication."""

    @abstractmethod
    def schedule(
        self,
        publish_time: datetime,
        video_id: str,
        **kwargs: Any,
    ) -> ScheduleResult:
        ...

    @abstractmethod
    def cancel(self, job_id: str) -> ScheduleResult:
        ...

    @abstractmethod
    def list_scheduled(self) -> list[ScheduleResult]:
        ...
