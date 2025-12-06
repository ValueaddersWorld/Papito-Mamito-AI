"""Social media publishers module for Papito Mamito AI."""

from .base import BasePublisher, PublishResult
from .instagram_publisher import InstagramPublisher
from .x_publisher import XPublisher
from .buffer_publisher import BufferPublisher
from .trending_detector import TrendingDetector, TrendingTopic, TopicRelevance

__all__ = [
    "BasePublisher",
    "PublishResult",
    "InstagramPublisher",
    "XPublisher",
    "BufferPublisher",
    "TrendingDetector",
    "TrendingTopic",
    "TopicRelevance",
]
