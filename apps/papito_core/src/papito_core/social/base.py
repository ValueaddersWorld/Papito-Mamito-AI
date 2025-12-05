"""Base classes for social media publishers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class Platform(str, Enum):
    """Supported social media platforms."""
    INSTAGRAM = "instagram"
    X = "x"
    TIKTOK = "tiktok"
    BUFFER = "buffer"


class PostType(str, Enum):
    """Types of posts that can be published."""
    SINGLE_IMAGE = "single_image"
    CAROUSEL = "carousel"
    VIDEO = "video"
    STORY = "story"
    REEL = "reel"
    TEXT = "text"
    THREAD = "thread"


@dataclass
class PublishResult:
    """Result of a publish operation."""
    
    success: bool
    platform: Platform
    post_id: Optional[str] = None
    post_url: Optional[str] = None
    error: Optional[str] = None
    rate_limit_remaining: Optional[int] = None
    rate_limit_reset: Optional[datetime] = None
    raw_response: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "platform": self.platform.value,
            "post_id": self.post_id,
            "post_url": self.post_url,
            "error": self.error,
            "rate_limit_remaining": self.rate_limit_remaining,
            "rate_limit_reset": self.rate_limit_reset.isoformat() if self.rate_limit_reset else None,
        }


@dataclass
class Interaction:
    """A social media interaction (comment, mention, DM)."""
    
    platform: Platform
    interaction_id: str
    interaction_type: str  # "comment", "mention", "dm", "reply"
    
    post_id: Optional[str]
    username: str
    display_name: str
    profile_url: str
    
    message: str
    media_urls: List[str]
    
    created_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "platform": self.platform.value,
            "interaction_id": self.interaction_id,
            "interaction_type": self.interaction_type,
            "post_id": self.post_id,
            "username": self.username,
            "display_name": self.display_name,
            "profile_url": self.profile_url,
            "message": self.message,
            "media_urls": self.media_urls,
            "created_at": self.created_at.isoformat(),
        }


class BasePublisher(ABC):
    """Abstract base class for social media publishers.
    
    All platform-specific publishers should inherit from this class
    and implement the abstract methods.
    """
    
    platform: Platform
    
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if the publisher is connected and authenticated."""
        pass
    
    @abstractmethod
    def connect(self) -> bool:
        """Establish connection/authenticate with the platform."""
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from the platform."""
        pass
    
    @abstractmethod
    def publish_post(
        self,
        content: str,
        media_urls: Optional[List[str]] = None,
        post_type: PostType = PostType.TEXT,
        **kwargs
    ) -> PublishResult:
        """Publish a post to the platform.
        
        Args:
            content: The text content/caption for the post
            media_urls: Optional list of media URLs to attach
            post_type: Type of post (text, image, carousel, etc.)
            **kwargs: Platform-specific options
            
        Returns:
            PublishResult with success status and post details
        """
        pass
    
    @abstractmethod
    def reply_to_post(
        self,
        post_id: str,
        content: str,
        **kwargs
    ) -> PublishResult:
        """Reply to an existing post or comment.
        
        Args:
            post_id: ID of the post/comment to reply to
            content: Reply text content
            **kwargs: Platform-specific options
            
        Returns:
            PublishResult with success status
        """
        pass
    
    @abstractmethod
    def get_interactions(
        self,
        since: Optional[datetime] = None,
        limit: int = 50
    ) -> List[Interaction]:
        """Fetch recent interactions (comments, mentions, DMs).
        
        Args:
            since: Only fetch interactions after this time
            limit: Maximum number of interactions to fetch
            
        Returns:
            List of Interaction objects
        """
        pass
    
    @abstractmethod
    def like_post(self, post_id: str) -> bool:
        """Like a post.
        
        Args:
            post_id: ID of the post to like
            
        Returns:
            True if successful
        """
        pass
    
    @abstractmethod
    def follow_user(self, username: str) -> bool:
        """Follow a user.
        
        Args:
            username: Username to follow
            
        Returns:
            True if successful
        """
        pass
    
    @abstractmethod
    def get_metrics(self) -> Dict[str, Any]:
        """Get account and content metrics.
        
        Returns:
            Dictionary with followers, engagement, etc.
        """
        pass
    
    def get_rate_limit_status(self) -> Dict[str, Any]:
        """Get current rate limit status.
        
        Default implementation returns empty status.
        Override in subclasses if platform provides rate limit info.
        """
        return {
            "remaining": None,
            "reset_at": None,
        }
