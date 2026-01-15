"""Unit tests for the review queue."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock, patch
import pytest


class TestContentCategory:
    """Tests for ContentCategory enum."""
    
    def test_auto_approve_categories(self):
        """Test that auto-approve categories are defined."""
        from papito_core.queue.review_queue import ContentCategory
        
        # These should exist as auto-approve categories
        assert ContentCategory.DAILY_BLESSING.value == "daily_blessing"
        assert ContentCategory.GRATITUDE.value == "gratitude"
        assert ContentCategory.FAN_SHOUTOUT.value == "fan_shoutout"
    
    def test_manual_review_categories(self):
        """Test that manual review categories are defined."""
        from papito_core.queue.review_queue import ContentCategory
        
        assert ContentCategory.NEW_RELEASE.value == "new_release"
        assert ContentCategory.COLLABORATION.value == "collaboration"
        assert ContentCategory.ANNOUNCEMENT.value == "announcement"


class TestReviewStatus:
    """Tests for ReviewStatus enum."""
    
    def test_review_status_values(self):
        """Test ReviewStatus enum values."""
        from papito_core.queue.review_queue import ReviewStatus
        
        assert ReviewStatus.PENDING_REVIEW.value == "pending_review"
        assert ReviewStatus.APPROVED.value == "approved"
        assert ReviewStatus.REJECTED.value == "rejected"
        assert ReviewStatus.PUBLISHED.value == "published"


class TestQueueStats:
    """Tests for QueueStats dataclass."""
    
    def test_queue_stats_creation(self):
        """Test creating QueueStats."""
        from papito_core.queue.review_queue import QueueStats
        
        stats = QueueStats(
            total=100,
            pending_review=10,
            approved=50,
            rejected=5,
            published=30,
            failed=5,
            auto_approved_today=40,
            manually_reviewed_today=10,
        )
        
        assert stats.total == 100
        assert stats.pending_review == 10
    
    def test_auto_approve_rate(self):
        """Test auto-approve rate calculation."""
        from papito_core.queue.review_queue import QueueStats
        
        stats = QueueStats(
            auto_approved_today=80,
            manually_reviewed_today=20,
        )
        
        assert stats.auto_approve_rate == 0.8
    
    def test_auto_approve_rate_zero(self):
        """Test auto-approve rate when no items processed."""
        from papito_core.queue.review_queue import QueueStats
        
        stats = QueueStats()
        
        assert stats.auto_approve_rate == 0.0


class TestReviewQueue:
    """Tests for ReviewQueue class."""
    
    @patch("papito_core.queue.review_queue.get_settings")
    def test_should_auto_approve_blessing(self, mock_settings):
        """Test auto-approve for daily blessing."""
        mock_settings.return_value = MagicMock(
            telegram_bot_token=None,
            telegram_chat_id=None,
            discord_webhook_url=None,
        )
        
        from papito_core.queue.review_queue import ReviewQueue, ContentCategory
        
        queue = ReviewQueue()
        
        assert queue._should_auto_approve(ContentCategory.DAILY_BLESSING) is True
        assert queue._should_auto_approve(ContentCategory.GRATITUDE) is True
        assert queue._should_auto_approve(ContentCategory.FAN_SHOUTOUT) is True
    
    @patch("papito_core.queue.review_queue.get_settings")
    def test_should_not_auto_approve_release(self, mock_settings):
        """Test that releases require manual review."""
        mock_settings.return_value = MagicMock(
            telegram_bot_token=None,
            telegram_chat_id=None,
            discord_webhook_url=None,
        )
        
        from papito_core.queue.review_queue import ReviewQueue, ContentCategory
        
        queue = ReviewQueue()
        
        assert queue._should_auto_approve(ContentCategory.NEW_RELEASE) is False
        assert queue._should_auto_approve(ContentCategory.COLLABORATION) is False
        assert queue._should_auto_approve(ContentCategory.ANNOUNCEMENT) is False
    
    @patch("papito_core.queue.review_queue.get_settings")
    def test_should_auto_approve_none_for_autonomy(self, mock_settings):
        """Test that None category auto-approves for autonomous operation."""
        mock_settings.return_value = MagicMock(
            telegram_bot_token=None,
            telegram_chat_id=None,
            discord_webhook_url=None,
        )
        
        from papito_core.queue.review_queue import ReviewQueue
        
        queue = ReviewQueue()
        
        # For autonomous operation, None defaults to auto-approve
        assert queue._should_auto_approve(None) is True
    
    @patch("papito_core.queue.review_queue.get_settings")
    @patch("papito_core.queue.review_queue.get_firebase_client")
    def test_add_to_queue_auto_approve(self, mock_db, mock_settings):
        """Test adding auto-approve content to queue."""
        mock_settings.return_value = MagicMock(
            telegram_bot_token=None,
            telegram_chat_id=None,
            discord_webhook_url=None,
        )
        
        mock_client = MagicMock()
        mock_client.add_to_queue.return_value = "test-queue-id"
        mock_db.return_value = mock_client
        
        from papito_core.queue.review_queue import ReviewQueue, ContentCategory
        
        queue = ReviewQueue()
        
        item_id = queue.add_to_queue(
            content_type="morning_blessing",
            platform="instagram",
            title="Morning Blessing",
            body="May your day be blessed!",
            category=ContentCategory.DAILY_BLESSING,
        )
        
        assert item_id == "test-queue-id"
        
        # Verify the item was created with approved status
        call_args = mock_client.add_to_queue.call_args
        item = call_args[0][0]
        assert item.status == "approved"
        assert item.auto_approve is True
    
    @patch("papito_core.queue.review_queue.get_settings")
    @patch("papito_core.queue.review_queue.get_firebase_client")
    def test_add_to_queue_manual_review(self, mock_db, mock_settings):
        """Test adding manual review content to queue."""
        mock_settings.return_value = MagicMock(
            telegram_bot_token=None,
            telegram_chat_id=None,
            discord_webhook_url=None,
        )
        
        mock_client = MagicMock()
        mock_client.add_to_queue.return_value = "test-queue-id"
        mock_db.return_value = mock_client
        
        from papito_core.queue.review_queue import ReviewQueue, ContentCategory
        
        queue = ReviewQueue()
        
        item_id = queue.add_to_queue(
            content_type="new_release",
            platform="instagram",
            title="New Track",
            body="Check out my new track!",
            category=ContentCategory.NEW_RELEASE,
        )
        
        # Verify the item was created with pending_review status
        call_args = mock_client.add_to_queue.call_args
        item = call_args[0][0]
        assert item.status == "pending_review"
        assert item.requires_review is True
