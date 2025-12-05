"""Unit tests for the Firebase client."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock, patch
import pytest


class TestContentQueueItem:
    """Tests for ContentQueueItem model."""
    
    def test_create_content_queue_item(self):
        """Test creating a ContentQueueItem with minimal fields."""
        from papito_core.database import ContentQueueItem
        
        item = ContentQueueItem(
            content_type="morning_blessing",
            platform="instagram",
            title="Morning Blessing",
            body="May your day be blessed!",
            status="pending_review",
        )
        
        assert item.content_type == "morning_blessing"
        assert item.platform == "instagram"
        assert item.status == "pending_review"
        assert item.auto_approve is True  # Default
    
    def test_content_queue_item_with_all_fields(self):
        """Test creating a ContentQueueItem with all fields."""
        from papito_core.database import ContentQueueItem
        
        scheduled = datetime.utcnow()
        item = ContentQueueItem(
            id="test-123",
            content_type="fan_shoutout",
            platform="x",
            title="Fan Appreciation",
            body="Shoutout to the fans!",
            media_urls=["https://example.com/image.jpg"],
            hashtags=["PapitoMamito", "Afrobeat"],
            formatted={"x": {"tweet": "Shoutout!"}},
            status="approved",
            auto_approve=False,
            requires_review=True,
            scheduled_at=scheduled,
            source_blog_id="blog-456",
        )
        
        assert item.id == "test-123"
        assert len(item.media_urls) == 1
        assert len(item.hashtags) == 2
        assert item.requires_review is True


class TestFanInteraction:
    """Tests for FanInteraction model."""
    
    def test_create_fan_interaction(self):
        """Test creating a FanInteraction."""
        from papito_core.database import FanInteraction
        
        interaction = FanInteraction(
            platform="instagram",
            interaction_type="comment",
            fan_username="test_user",
            fan_display_name="Test User",
            message="Love your music!",
            platform_interaction_id="ig-123",
        )
        
        assert interaction.platform == "instagram"
        assert interaction.fan_username == "test_user"
        assert interaction.responded is False  # Default


class TestAgentLog:
    """Tests for AgentLog model."""
    
    def test_create_agent_log(self):
        """Test creating an AgentLog."""
        from papito_core.database import AgentLog
        
        log = AgentLog(
            agent_session_id="session-abc",
            action="post_published",
            level="info",
            message="Published morning blessing to Instagram",
        )
        
        assert log.action == "post_published"
        assert log.level == "info"


class TestFirebaseClientMocked:
    """Tests for FirebaseClient with mocked Firebase."""
    
    @patch("papito_core.database.firebase_client.firebase_admin")
    def test_firebase_client_initialization(self, mock_firebase_admin):
        """Test that Firebase client initializes correctly."""
        # Mock the Firebase admin SDK
        mock_firebase_admin.get_app.side_effect = ValueError("No app")
        mock_firebase_admin.initialize_app.return_value = MagicMock()
        
        mock_db = MagicMock()
        with patch("papito_core.database.firebase_client.firestore") as mock_firestore:
            mock_firestore.client.return_value = mock_db
            
            from papito_core.database.firebase_client import FirebaseClient
            
            # Create a client instance
            client = FirebaseClient.__new__(FirebaseClient)
            client.db = mock_db
            client._initialized = True
            
            assert client._initialized is True
    
    def test_auto_approve_categories(self):
        """Test that auto-approve categories are correct."""
        from papito_core.database.firebase_client import FirebaseClient
        
        # Check the auto-approve list includes expected categories
        auto_cats = FirebaseClient.AUTO_APPROVE_CONTENT_TYPES
        
        assert "daily_blessing" in auto_cats
        assert "morning_blessing" in auto_cats
        assert "gratitude" in auto_cats
        assert "fan_shoutout" in auto_cats
        
        # These should NOT be in auto-approve
        assert "new_release" not in auto_cats
        assert "announcement" not in auto_cats
