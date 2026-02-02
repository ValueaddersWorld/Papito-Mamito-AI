"""
PAPITO MAMITO AI - PLATFORM BASE ABSTRACTIONS
==============================================
Core abstractions that allow Papito to operate on any platform.

The key insight: All social platforms share common patterns:
- Events happen (mentions, messages, comments)
- Actions are taken (post, reply, like, follow)
- Content is created (text, media, links)

By abstracting these patterns, Papito can:
1. React to events from any platform uniformly
2. Take actions across platforms consistently
3. Learn and improve across all platforms together

© 2026 Value Adders World - Entertainment Division
"Add value or don't act."
"""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set
import uuid

logger = logging.getLogger("papito.platforms.base")


class Platform(str, Enum):
    """Supported platforms."""
    X = "x"                    # Twitter/X
    DISCORD = "discord"        # Discord
    YOUTUBE = "youtube"        # YouTube
    INSTAGRAM = "instagram"    # Instagram
    TIKTOK = "tiktok"         # TikTok
    MOLTBOOK = "moltbook"     # Moltbook (decentralized)
    TELEGRAM = "telegram"      # Telegram
    THREADS = "threads"        # Meta Threads
    BLUESKY = "bluesky"       # Bluesky
    CUSTOM = "custom"          # Custom/webhook platforms


class PlatformCapability(str, Enum):
    """Capabilities a platform may support."""
    # Content types
    TEXT_POST = "text_post"
    IMAGE_POST = "image_post"
    VIDEO_POST = "video_post"
    AUDIO_POST = "audio_post"
    LINK_POST = "link_post"
    
    # Interactions
    REPLY = "reply"
    LIKE = "like"
    REPOST = "repost"
    QUOTE = "quote"
    BOOKMARK = "bookmark"
    
    # Engagement
    FOLLOW = "follow"
    UNFOLLOW = "unfollow"
    BLOCK = "block"
    MUTE = "mute"
    
    # Messaging
    DIRECT_MESSAGE = "direct_message"
    GROUP_MESSAGE = "group_message"
    
    # Real-time
    STREAMING = "streaming"
    WEBHOOKS = "webhooks"
    POLLING = "polling"
    
    # Discovery
    SEARCH = "search"
    TRENDING = "trending"
    RECOMMENDATIONS = "recommendations"
    
    # Analytics
    ANALYTICS = "analytics"
    INSIGHTS = "insights"


class EventCategory(str, Enum):
    """Categories of platform events."""
    MENTION = "mention"           # Someone mentioned Papito
    REPLY = "reply"               # Reply to Papito's content
    MESSAGE = "message"           # Direct/private message
    FOLLOW = "follow"             # New follower
    LIKE = "like"                 # Someone liked content
    REPOST = "repost"             # Someone reposted/shared
    COMMENT = "comment"           # Comment on content
    REACTION = "reaction"         # Reaction (emoji, etc.)
    TREND = "trend"               # Trending topic alert
    SCHEDULED = "scheduled"       # Scheduled event trigger
    SYSTEM = "system"             # System/admin event
    CUSTOM = "custom"             # Custom event type


@dataclass
class PlatformConfig:
    """Configuration for a platform adapter."""
    platform: Platform
    enabled: bool = True
    
    # Authentication
    api_key: str = ""
    api_secret: str = ""
    access_token: str = ""
    access_secret: str = ""
    bearer_token: str = ""
    
    # Rate limiting
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    requests_per_day: int = 10000
    
    # Features
    capabilities: Set[PlatformCapability] = field(default_factory=set)
    
    # Monitoring
    webhook_url: str = ""
    webhook_secret: str = ""
    
    # Custom settings
    custom_settings: Dict[str, Any] = field(default_factory=dict)
    
    def has_capability(self, capability: PlatformCapability) -> bool:
        """Check if platform has a capability."""
        return capability in self.capabilities
    
    def is_configured(self) -> bool:
        """Check if platform has required credentials."""
        return bool(self.api_key or self.bearer_token or self.access_token)


@dataclass
class PlatformEvent:
    """
    A platform-agnostic event.
    
    This represents any event from any platform in a unified format.
    Adapters convert platform-specific events to this format.
    """
    event_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    platform: Platform = Platform.CUSTOM
    category: EventCategory = EventCategory.CUSTOM
    
    # Who triggered the event
    user_id: str = ""
    user_name: str = ""
    user_display_name: str = ""
    
    # Content
    content: str = ""
    content_type: str = "text"  # text, image, video, etc.
    
    # References
    source_id: str = ""        # Original content ID on platform
    reply_to_id: str = ""      # ID of content being replied to
    conversation_id: str = ""   # Thread/conversation ID
    
    # Context
    metadata: Dict[str, Any] = field(default_factory=dict)
    raw_event: Any = None      # Original platform event data
    
    # Timing
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    received_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "event_id": self.event_id,
            "platform": self.platform.value,
            "category": self.category.value,
            "user_id": self.user_id,
            "user_name": self.user_name,
            "content": self.content[:200] if self.content else "",
            "source_id": self.source_id,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
        }
    
    @property
    def is_mention(self) -> bool:
        return self.category == EventCategory.MENTION
    
    @property
    def is_reply(self) -> bool:
        return self.category == EventCategory.REPLY
    
    @property
    def is_dm(self) -> bool:
        return self.category == EventCategory.MESSAGE


@dataclass
class PlatformAction:
    """
    A platform-agnostic action to take.
    
    This represents any action Papito wants to take, in unified format.
    Adapters convert this to platform-specific API calls.
    """
    action_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    platform: Platform = Platform.CUSTOM
    action_type: str = "post"  # post, reply, like, follow, dm, etc.
    
    # Content
    content: str = ""
    media_urls: List[str] = field(default_factory=list)
    
    # Target
    target_user_id: str = ""
    target_content_id: str = ""
    reply_to_id: str = ""
    
    # Options
    options: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    triggered_by_event: str = ""  # Event ID that triggered this
    value_score: float = 0.0       # Score from value calculator
    
    # Timing
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    execute_at: datetime | None = None  # For scheduled actions
    
    # Status
    executed: bool = False
    execution_result: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "action_id": self.action_id,
            "platform": self.platform.value,
            "action_type": self.action_type,
            "content": self.content[:200] if self.content else "",
            "target_user_id": self.target_user_id,
            "value_score": self.value_score,
            "executed": self.executed,
        }


@dataclass
class ActionResult:
    """Result of executing a platform action."""
    success: bool
    action_id: str
    platform: Platform
    
    # Result data
    result_id: str = ""        # ID of created content (if any)
    result_url: str = ""       # URL of created content
    
    # Error info
    error_code: str = ""
    error_message: str = ""
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    executed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "action_id": self.action_id,
            "platform": self.platform.value,
            "result_id": self.result_id,
            "error_message": self.error_message if not self.success else "",
        }


class PlatformAdapter(ABC):
    """
    Abstract base class for platform adapters.
    
    Each platform (X, Discord, YouTube, etc.) implements this interface.
    This allows Papito to interact with any platform through a unified API.
    
    Implementing a new adapter:
        1. Subclass PlatformAdapter
        2. Implement all abstract methods
        3. Define supported capabilities
        4. Register with the coordinator
    
    Example:
        class MyPlatformAdapter(PlatformAdapter):
            platform = Platform.CUSTOM
            
            async def connect(self) -> bool:
                # Connect to platform API
                return True
            
            async def listen(self, callback):
                # Listen for events
                pass
            
            async def execute(self, action) -> ActionResult:
                # Execute action
                return ActionResult(success=True, ...)
    """
    
    # Platform identifier
    platform: Platform = Platform.CUSTOM
    
    # Supported capabilities
    capabilities: Set[PlatformCapability] = set()
    
    def __init__(self, config: PlatformConfig):
        """Initialize adapter with configuration.
        
        Args:
            config: Platform configuration
        """
        self.config = config
        self._connected = False
        self._event_callbacks: List[Callable] = []
        
        logger.info(f"Initialized {self.platform.value} adapter")
    
    @property
    def is_connected(self) -> bool:
        """Check if adapter is connected."""
        return self._connected
    
    @abstractmethod
    async def connect(self) -> bool:
        """
        Connect to the platform.
        
        Returns:
            True if connected successfully
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the platform."""
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """
        Check platform connection health.
        
        Returns:
            Health status dictionary
        """
        pass
    
    @abstractmethod
    async def listen(self, callback: Callable[[PlatformEvent], None]) -> None:
        """
        Start listening for platform events.
        
        Args:
            callback: Function to call with each event
        """
        pass
    
    @abstractmethod
    async def stop_listening(self) -> None:
        """Stop listening for events."""
        pass
    
    @abstractmethod
    async def execute(self, action: PlatformAction) -> ActionResult:
        """
        Execute an action on the platform.
        
        Args:
            action: The action to execute
            
        Returns:
            Result of the action
        """
        pass
    
    @abstractmethod
    async def get_user(self, user_id: str) -> Dict[str, Any]:
        """
        Get user information.
        
        Args:
            user_id: Platform user ID
            
        Returns:
            User data dictionary
        """
        pass
    
    @abstractmethod
    async def get_content(self, content_id: str) -> Dict[str, Any]:
        """
        Get content by ID.
        
        Args:
            content_id: Platform content ID
            
        Returns:
            Content data dictionary
        """
        pass
    
    # Optional methods with default implementations
    
    async def search(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search for content.
        
        Args:
            query: Search query
            limit: Maximum results
            
        Returns:
            List of search results
        """
        if PlatformCapability.SEARCH not in self.capabilities:
            logger.warning(f"{self.platform.value} does not support search")
            return []
        return []
    
    async def get_trending(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get trending topics.
        
        Args:
            limit: Maximum results
            
        Returns:
            List of trending topics
        """
        if PlatformCapability.TRENDING not in self.capabilities:
            logger.warning(f"{self.platform.value} does not support trending")
            return []
        return []
    
    async def get_analytics(self, content_id: str) -> Dict[str, Any]:
        """Get analytics for content.
        
        Args:
            content_id: Content ID
            
        Returns:
            Analytics data
        """
        if PlatformCapability.ANALYTICS not in self.capabilities:
            return {}
        return {}
    
    def has_capability(self, capability: PlatformCapability) -> bool:
        """Check if adapter supports a capability."""
        return capability in self.capabilities
    
    def register_callback(self, callback: Callable[[PlatformEvent], None]) -> None:
        """Register an event callback."""
        self._event_callbacks.append(callback)
    
    async def _emit_event(self, event: PlatformEvent) -> None:
        """Emit an event to all callbacks."""
        for callback in self._event_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                logger.error(f"Error in event callback: {e}")
    
    def __repr__(self) -> str:
        status = "connected" if self._connected else "disconnected"
        return f"<{self.__class__.__name__}({self.platform.value}, {status})>"


class MockPlatformAdapter(PlatformAdapter):
    """
    Mock adapter for testing without real API connections.
    
    Useful for:
    - Development and testing
    - Simulating platform behavior
    - Testing cross-platform coordination
    """
    
    platform = Platform.CUSTOM
    capabilities = {
        PlatformCapability.TEXT_POST,
        PlatformCapability.REPLY,
        PlatformCapability.LIKE,
        PlatformCapability.FOLLOW,
        PlatformCapability.SEARCH,
    }
    
    def __init__(self, config: PlatformConfig, platform_name: str = "mock"):
        super().__init__(config)
        self.platform = Platform.CUSTOM
        self._platform_name = platform_name
        self._events: List[PlatformEvent] = []
        self._actions: List[PlatformAction] = []
    
    async def connect(self) -> bool:
        logger.info(f"Mock adapter {self._platform_name} connected")
        self._connected = True
        return True
    
    async def disconnect(self) -> None:
        logger.info(f"Mock adapter {self._platform_name} disconnected")
        self._connected = False
    
    async def health_check(self) -> Dict[str, Any]:
        return {
            "status": "healthy" if self._connected else "disconnected",
            "platform": self._platform_name,
            "events_received": len(self._events),
            "actions_executed": len(self._actions),
        }
    
    async def listen(self, callback: Callable[[PlatformEvent], None]) -> None:
        self.register_callback(callback)
        logger.info(f"Mock adapter {self._platform_name} listening")
    
    async def stop_listening(self) -> None:
        self._event_callbacks.clear()
        logger.info(f"Mock adapter {self._platform_name} stopped listening")
    
    async def execute(self, action: PlatformAction) -> ActionResult:
        self._actions.append(action)
        logger.info(f"Mock adapter executed: {action.action_type}")
        
        return ActionResult(
            success=True,
            action_id=action.action_id,
            platform=self.platform,
            result_id=f"mock_{action.action_id}",
            metadata={"mock": True},
        )
    
    async def get_user(self, user_id: str) -> Dict[str, Any]:
        return {
            "id": user_id,
            "username": f"mock_user_{user_id}",
            "display_name": f"Mock User {user_id}",
            "followers": 100,
        }
    
    async def get_content(self, content_id: str) -> Dict[str, Any]:
        return {
            "id": content_id,
            "content": f"Mock content {content_id}",
            "likes": 10,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
    
    async def inject_event(self, event: PlatformEvent) -> None:
        """Inject a test event (for testing)."""
        self._events.append(event)
        await self._emit_event(event)
