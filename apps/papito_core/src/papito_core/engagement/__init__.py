"""Fan engagement module for Papito Mamito.

Provides tools for managing fan relationships, tracking engagement,
personalizing interactions, and active social media engagement.
"""

from .fan_engagement import (
    EngagementTier,
    EngagementScore,
    Sentiment,
    SentimentAnalyzer,
    FanProfile,
    FanEngagementManager,
)

from .mention_monitor import (
    MentionMonitor,
    MentionIntent,
    Mention,
    get_mention_monitor,
)

from .afrobeat_engagement import (
    AfrobeatEngager,
    DiscoveredTweet,
    get_afrobeat_engager,
    AFROBEAT_HASHTAGS,
)

__all__ = [
    # Fan engagement
    "EngagementTier",
    "EngagementScore",
    "Sentiment",
    "SentimentAnalyzer",
    "FanProfile",
    "FanEngagementManager",
    # Active engagement
    "MentionMonitor",
    "MentionIntent",
    "Mention",
    "get_mention_monitor",
    "AfrobeatEngager",
    "DiscoveredTweet",
    "get_afrobeat_engager",
    "AFROBEAT_HASHTAGS",
]
