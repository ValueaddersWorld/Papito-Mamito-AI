"""Automation utilities for Papito Mamito."""

from .analytics import (
    AnalyticsSummary,
    PlatformSnapshot,
    StreamingAnalyticsService,
)
from .scheduler import ReleaseAction, ReleaseSchedule, ReleaseScheduler
from .autonomous_agent import AutonomousAgent
from .content_scheduler import ContentScheduler, ContentType, PostingSlot, SchedulingConfig
from .autonomous_scheduler import (
    AutonomousScheduler,
    get_scheduler,
    start_scheduler,
    stop_scheduler,
)

__all__ = [
    "PlatformSnapshot",
    "AnalyticsSummary",
    "StreamingAnalyticsService",
    "ReleaseAction",
    "ReleaseSchedule",
    "ReleaseScheduler",
    "AutonomousAgent",
    "ContentScheduler",
    "ContentType",
    "PostingSlot",
    "SchedulingConfig",
    "AutonomousScheduler",
    "get_scheduler",
    "start_scheduler",
    "stop_scheduler",
]
