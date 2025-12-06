"""Fan engagement module for Papito Mamito.

Provides tools for managing fan relationships, tracking engagement,
and personalizing interactions.
"""

from .fan_engagement import (
    EngagementTier,
    EngagementScore,
    Sentiment,
    SentimentAnalyzer,
    FanProfile,
    FanEngagementManager,
)

__all__ = [
    "EngagementTier",
    "EngagementScore",
    "Sentiment",
    "SentimentAnalyzer",
    "FanProfile",
    "FanEngagementManager",
]
