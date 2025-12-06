"""Analytics module for Papito Mamito.

Provides predictive analytics, engagement tracking,
A/B testing, and content strategy optimization.
"""

from .predictive import (
    ContentFormat,
    EngagementMetric,
    EngagementData,
    PeakTimeSlot,
    ABTest,
    EngagementTracker,
    ABTestManager,
    ContentStrategyOptimizer,
)

__all__ = [
    "ContentFormat",
    "EngagementMetric",
    "EngagementData",
    "PeakTimeSlot",
    "ABTest",
    "EngagementTracker",
    "ABTestManager",
    "ContentStrategyOptimizer",
]
