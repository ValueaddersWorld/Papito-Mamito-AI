"""Review queue for content approval workflow.

Implements the 80/20 auto-approve/manual review system for content
before it gets published to social media platforms.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import httpx

from ..settings import get_settings
from ..database import get_firebase_client, ContentQueueItem


class ContentCategory(str, Enum):
    """Categories of content with different approval requirements."""
    
    # Auto-approve categories (80%)
    DAILY_BLESSING = "daily_blessing"
    GRATITUDE = "gratitude"
    FAN_SHOUTOUT = "fan_shoutout"
    MUSIC_QUOTE = "music_quote"
    AFFIRMATION = "affirmation"
    
    # Manual review categories (20%)
    NEW_RELEASE = "new_release"
    COLLABORATION = "collaboration"
    ANNOUNCEMENT = "announcement"
    SENSITIVE_TOPIC = "sensitive_topic"
    USER_RESPONSE = "user_response"


class ReviewStatus(str, Enum):
    """Status of a content item in the review queue."""
    
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    PUBLISHED = "published"
    FAILED = "failed"
    EXPIRED = "expired"


@dataclass
class QueueStats:
    """Statistics about the review queue."""
    
    total: int = 0
    pending_review: int = 0
    approved: int = 0
    rejected: int = 0
    published: int = 0
    failed: int = 0
    
    auto_approved_today: int = 0
    manually_reviewed_today: int = 0
    
    @property
    def auto_approve_rate(self) -> float:
        """Calculate auto-approval rate."""
        total_processed = self.auto_approved_today + self.manually_reviewed_today
        if total_processed == 0:
            return 0.0
        return self.auto_approved_today / total_processed


class ReviewQueue:
    """Manage the content approval workflow.
    
    Implements the 80/20 auto-approve system:
    - 80% of content (daily blessings, gratitude posts, etc.) auto-approves
    - 20% of content (releases, collabs, announcements) requires manual review
    
    Sends notifications via Telegram or Discord when manual review is needed.
    """
    
    # Categories that auto-approve
    AUTO_APPROVE_CATEGORIES = {
        ContentCategory.DAILY_BLESSING,
        ContentCategory.GRATITUDE,
        ContentCategory.FAN_SHOUTOUT,
        ContentCategory.MUSIC_QUOTE,
        ContentCategory.AFFIRMATION,
    }
    
    def __init__(self):
        """Initialize the review queue."""
        self.settings = get_settings()
        self._client = httpx.Client(timeout=30.0)
    
    def add_to_queue(
        self,
        content_type: str,
        platform: str,
        title: str,
        body: str,
        category: Optional[ContentCategory] = None,
        media_urls: Optional[List[str]] = None,
        hashtags: Optional[List[str]] = None,
        scheduled_at: Optional[datetime] = None,
        formatted_content: Optional[Dict[str, Any]] = None,
        source_blog_id: Optional[str] = None,
        source_track_id: Optional[str] = None,
    ) -> str:
        """Add a new content item to the queue.
        
        Automatically determines if it should auto-approve based on category.
        
        Args:
            content_type: Type of content (blog, teaser, etc.)
            platform: Target platform (instagram, x, all)
            title: Content title
            body: Content body/caption
            category: Content category for approval routing
            media_urls: Attached media
            hashtags: Hashtags to include
            scheduled_at: When to publish (None = ASAP)
            formatted_content: Platform-specific formatted versions
            source_blog_id: Reference to source blog
            source_track_id: Reference to source track
            
        Returns:
            Queue item ID
        """
        # Determine if auto-approve
        auto_approve = self._should_auto_approve(category)
        
        # Create queue item
        item = ContentQueueItem(
            content_type=content_type,
            platform=platform,
            title=title,
            body=body,
            media_urls=media_urls or [],
            hashtags=hashtags or [],
            formatted=formatted_content or {},
            status=ReviewStatus.APPROVED.value if auto_approve else ReviewStatus.PENDING_REVIEW.value,
            auto_approve=auto_approve,
            requires_review=not auto_approve,
            scheduled_at=scheduled_at or datetime.utcnow(),
            source_blog_id=source_blog_id,
            source_track_id=source_track_id,
        )
        
        # Add to Firebase
        db = get_firebase_client()
        item_id = db.add_to_queue(item)
        
        # Send notification if manual review needed
        if not auto_approve:
            self._send_review_notification(item_id, title, platform, category)
        
        return item_id
    
    def _should_auto_approve(self, category: Optional[ContentCategory]) -> bool:
        """Determine if content should auto-approve."""
        if category is None:
            # Default to requiring review for unknown categories
            return False
        
        return category in self.AUTO_APPROVE_CATEGORIES
    
    def get_pending_items(self, limit: int = 50) -> List[ContentQueueItem]:
        """Get items pending manual review.
        
        Args:
            limit: Maximum items to return
            
        Returns:
            List of pending ContentQueueItems
        """
        db = get_firebase_client()
        return db.get_pending_queue_items(limit=limit)
    
    def get_ready_to_publish(self, limit: int = 20) -> List[ContentQueueItem]:
        """Get approved items ready for publishing.
        
        Args:
            limit: Maximum items to return
            
        Returns:
            List of approved items where scheduled_at <= now
        """
        db = get_firebase_client()
        return db.get_approved_ready_to_publish(limit=limit)
    
    def approve(
        self,
        item_id: str,
        reviewer: str = "system",
        reschedule_at: Optional[datetime] = None
    ) -> bool:
        """Approve a content item.
        
        Args:
            item_id: Queue item ID
            reviewer: Who approved (username or 'system')
            reschedule_at: Optional new schedule time
            
        Returns:
            True if successful
        """
        db = get_firebase_client()
        
        # Get item to update
        item = db.get_queue_item(item_id)
        if not item:
            return False
        
        # Approve the item
        db.approve_queue_item(item_id, reviewed_by=reviewer)
        
        # Update schedule if provided
        if reschedule_at:
            db.db.collection("content_queue").document(item_id).update({
                "scheduled_at": reschedule_at
            })
        
        return True
    
    def reject(
        self,
        item_id: str,
        reason: str,
        reviewer: str = "system"
    ) -> bool:
        """Reject a content item.
        
        Args:
            item_id: Queue item ID
            reason: Reason for rejection
            reviewer: Who rejected
            
        Returns:
            True if successful
        """
        db = get_firebase_client()
        return db.reject_queue_item(item_id, reason=reason, reviewed_by=reviewer)
    
    def mark_published(
        self,
        item_id: str,
        platform_post_id: str,
        platform_url: str
    ) -> str:
        """Mark an item as published.
        
        Args:
            item_id: Queue item ID
            platform_post_id: ID of the post on the platform
            platform_url: URL to the published post
            
        Returns:
            Published content record ID
        """
        db = get_firebase_client()
        return db.mark_as_published(item_id, platform_post_id, platform_url)
    
    def mark_failed(self, item_id: str, error: str) -> bool:
        """Mark an item as failed to publish.
        
        Args:
            item_id: Queue item ID
            error: Error message
            
        Returns:
            True if successful
        """
        db = get_firebase_client()
        db.db.collection("content_queue").document(item_id).update({
            "status": ReviewStatus.FAILED.value,
            "error_message": error,
            "updated_at": datetime.utcnow()
        })
        return True
    
    def get_stats(self) -> QueueStats:
        """Get queue statistics.
        
        Returns:
            QueueStats with counts and rates
        """
        db = get_firebase_client()
        raw_stats = db.get_queue_stats()
        
        return QueueStats(
            total=sum(raw_stats.values()),
            pending_review=raw_stats.get("pending_review", 0),
            approved=raw_stats.get("approved", 0),
            rejected=raw_stats.get("rejected", 0),
            published=raw_stats.get("published", 0),
            failed=raw_stats.get("failed", 0),
        )
    
    def _send_review_notification(
        self,
        item_id: str,
        title: str,
        platform: str,
        category: Optional[ContentCategory]
    ) -> None:
        """Send notification that content needs review.
        
        Sends to configured Telegram or Discord webhook.
        """
        message = f"""🔔 **New Content Needs Review**

📝 **Title:** {title}
📱 **Platform:** {platform}
🏷 **Category:** {category.value if category else 'unknown'}
🆔 **ID:** {item_id}

Reply with:
- `/approve {item_id}` to approve
- `/reject {item_id} <reason>` to reject"""

        # Try Telegram first
        if self.settings.telegram_bot_token and self.settings.telegram_chat_id:
            self._send_telegram(message)
        
        # Then Discord
        elif self.settings.discord_webhook_url:
            self._send_discord(message)
    
    def _send_telegram(self, message: str) -> bool:
        """Send notification via Telegram bot."""
        try:
            response = self._client.post(
                f"https://api.telegram.org/bot{self.settings.telegram_bot_token}/sendMessage",
                json={
                    "chat_id": self.settings.telegram_chat_id,
                    "text": message,
                    "parse_mode": "Markdown"
                }
            )
            return response.status_code == 200
        except Exception:
            return False
    
    def _send_discord(self, message: str) -> bool:
        """Send notification via Discord webhook."""
        try:
            response = self._client.post(
                self.settings.discord_webhook_url,
                json={
                    "content": message
                }
            )
            return response.status_code in (200, 204)
        except Exception:
            return False
