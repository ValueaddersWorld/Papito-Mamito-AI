"""Fan Interaction Module for Papito AI.

This module provides tools for direct fan interactions including:
- DM management and responses
- New follower welcome system
- Fan recognition and appreciation
"""

from .dm_manager import (
    DMManager,
    DMIntent,
    DirectMessage,
    ConversationThread,
    get_dm_manager,
)

from .follower_manager import (
    FollowerManager,
    Follower,
    get_follower_manager,
)

from .fan_recognition import (
    FanRecognitionManager,
    FanEngagement,
    FanOfWeek,
    get_fan_recognition_manager,
)

__all__ = [
    # DM Management
    "DMManager",
    "DMIntent",
    "DirectMessage",
    "ConversationThread",
    "get_dm_manager",
    # Follower Management
    "FollowerManager",
    "Follower",
    "get_follower_manager",
    # Fan Recognition
    "FanRecognitionManager",
    "FanEngagement",
    "FanOfWeek",
    "get_fan_recognition_manager",
]
