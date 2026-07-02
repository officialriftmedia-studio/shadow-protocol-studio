"""Publishing interfaces for platform upload, scheduling, and analytics.

These provide abstract base classes defining the contract for future
publishing integrations. No API implementations are included yet.
"""

from shadow_protocol.lib.publishing.base import PlatformPublisher, PublishResult
from shadow_protocol.lib.publishing.youtube import YouTubePublisher
from shadow_protocol.lib.publishing.scheduler import PublishScheduler
from shadow_protocol.lib.publishing.analytics import AnalyticsCollector

__all__ = [
    "PlatformPublisher",
    "PublishResult",
    "YouTubePublisher",
    "PublishScheduler",
    "AnalyticsCollector",
]
