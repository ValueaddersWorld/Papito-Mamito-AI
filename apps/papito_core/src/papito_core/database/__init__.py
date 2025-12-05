"""Database module for Firebase/Firestore integration."""

from .firebase_client import (
    FirebaseClient,
    get_firebase_client,
    ContentQueueItem,
    PublishedContent,
    FanInteraction,
    ScheduledPost,
    PlatformConnection,
    AgentLog,
)

__all__ = [
    "FirebaseClient",
    "get_firebase_client",
    "ContentQueueItem",
    "PublishedContent",
    "FanInteraction",
    "ScheduledPost",
    "PlatformConnection",
    "AgentLog",
]
