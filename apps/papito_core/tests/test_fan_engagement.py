"""Tests for fan engagement module."""

import pytest
from datetime import datetime

from papito_core.engagement import (
    EngagementTier,
    EngagementScore,
    Sentiment,
    SentimentAnalyzer,
    FanProfile,
    FanEngagementManager,
)


class TestEngagementTier:
    """Tests for EngagementTier enum."""
    
    def test_tier_values(self):
        """Verify tier values are correct strings."""
        assert EngagementTier.CASUAL.value == "casual"
        assert EngagementTier.ENGAGED.value == "engaged"
        assert EngagementTier.CORE.value == "core"
        assert EngagementTier.SUPER_FAN.value == "super_fan"


class TestEngagementScore:
    """Tests for EngagementScore calculation."""
    
    def test_casual_tier_for_new_fan(self):
        """New fans should be casual tier."""
        score = EngagementScore(total_interactions=1)
        assert score.tier == EngagementTier.CASUAL
    
    def test_engaged_tier_threshold(self):
        """Fans with 3+ interactions should be engaged."""
        score = EngagementScore(total_interactions=3)
        assert score.tier == EngagementTier.ENGAGED
    
    def test_core_tier_threshold(self):
        """Fans with 10+ interactions and good sentiment should be core."""
        score = EngagementScore(
            total_interactions=10,
            avg_sentiment_score=0.6
        )
        assert score.tier == EngagementTier.CORE
    
    def test_super_fan_tier_threshold(self):
        """Highly engaged fans with great sentiment are super fans."""
        score = EngagementScore(
            total_interactions=25,
            avg_sentiment_score=0.8
        )
        assert score.tier == EngagementTier.SUPER_FAN
    
    def test_tier_progress_calculation(self):
        """Verify tier progress is calculated correctly."""
        score = EngagementScore(total_interactions=2)
        # 2/3 = 0.66 progress toward Engaged tier
        assert 0.6 <= score.tier_progress <= 0.7


class TestSentimentAnalyzer:
    """Tests for SentimentAnalyzer."""
    
    @pytest.fixture
    def analyzer(self):
        return SentimentAnalyzer()
    
    def test_positive_message(self, analyzer):
        """Test detection of positive messages."""
        sentiment, score = analyzer.analyze("I love this music! Amazing vibes 🔥")
        assert sentiment in (Sentiment.POSITIVE, Sentiment.VERY_POSITIVE)
        assert score > 0.5
    
    def test_negative_message(self, analyzer):
        """Test detection of negative messages."""
        sentiment, score = analyzer.analyze("This is terrible, I hate it")
        assert sentiment in (Sentiment.NEGATIVE, Sentiment.VERY_NEGATIVE)
        assert score < 0.5
    
    def test_neutral_message(self, analyzer):
        """Test detection of neutral messages."""
        sentiment, score = analyzer.analyze("Just checking out the new track")
        assert sentiment == Sentiment.NEUTRAL
    
    def test_emoji_positive(self, analyzer):
        """Test emoji sentiment detection."""
        sentiment, score = analyzer.analyze("🔥🔥🔥 💯")
        assert sentiment in (Sentiment.POSITIVE, Sentiment.VERY_POSITIVE)
    
    def test_emoji_negative(self, analyzer):
        """Test negative emoji detection."""
        sentiment, score = analyzer.analyze("👎 😡")
        assert sentiment in (Sentiment.NEGATIVE, Sentiment.VERY_NEGATIVE)


class TestFanProfile:
    """Tests for FanProfile model."""
    
    def test_create_profile(self):
        """Test creating a basic profile."""
        fan = FanProfile(
            username="test_fan",
            platform="instagram"
        )
        assert fan.username == "test_fan"
        assert fan.tier == EngagementTier.CASUAL.value
    
    def test_update_tier(self):
        """Test tier updates based on interactions."""
        fan = FanProfile(
            username="engaged_fan",
            platform="x",
            total_interactions=5,
            positive_interactions=4
        )
        fan.update_tier()
        assert fan.tier == EngagementTier.ENGAGED.value


class TestFanEngagementManager:
    """Tests for FanEngagementManager."""
    
    @pytest.fixture
    def manager(self):
        return FanEngagementManager()
    
    def test_get_or_create_fan(self, manager):
        """Test fan creation."""
        fan = manager.get_or_create_fan("new_fan", "instagram")
        assert fan.username == "new_fan"
        assert fan.platform == "instagram"
    
    def test_existing_fan_returned(self, manager):
        """Test that same fan is returned on second call."""
        fan1 = manager.get_or_create_fan("test", "x")
        fan2 = manager.get_or_create_fan("test", "x")
        assert fan1 is fan2
    
    def test_record_interaction(self, manager):
        """Test recording an interaction updates metrics."""
        fan, sentiment = manager.record_interaction(
            username="active_fan",
            platform="instagram",
            message="Love this track! 🔥"
        )
        
        assert fan.total_interactions == 1
        assert sentiment in (Sentiment.POSITIVE, Sentiment.VERY_POSITIVE)
    
    def test_tier_progress_with_interactions(self, manager):
        """Test tier progression through interactions."""
        # Record multiple positive interactions
        for i in range(5):
            fan, _ = manager.record_interaction(
                username="growing_fan",
                platform="x",
                message="Amazing music! Love it! 🔥"
            )
        
        assert fan.total_interactions == 5
        assert fan.tier == EngagementTier.ENGAGED.value
    
    def test_welcome_message_contains_username(self, manager):
        """Test welcome message includes username."""
        message = manager.generate_welcome_message("new_follower")
        assert "new_follower" in message
    
    def test_personalized_greeting_by_tier(self, manager):
        """Test different greetings for different tiers."""
        # Create super fan
        fan = manager.get_or_create_fan("super", "x")
        fan.tier = EngagementTier.SUPER_FAN.value
        
        greeting = manager.get_personalized_greeting(fan)
        # Super fans get special greetings
        assert "super" in greeting.lower() or any(
            word in greeting.lower() 
            for word in ["champion", "treasured", "valued"]
        )
    
    def test_response_urgency_negative_sentiment(self, manager):
        """Test high urgency for negative messages."""
        fan = manager.get_or_create_fan("upset_fan", "instagram")
        urgency = manager.get_response_urgency(fan, Sentiment.VERY_NEGATIVE)
        assert urgency == 5  # Maximum urgency
    
    def test_response_urgency_super_fan(self, manager):
        """Test higher urgency for super fans."""
        fan = manager.get_or_create_fan("vip", "x")
        fan.tier = EngagementTier.SUPER_FAN.value
        
        urgency = manager.get_response_urgency(fan, Sentiment.NEUTRAL)
        assert urgency >= 4
    
    def test_get_tier_stats(self, manager):
        """Test tier statistics calculation."""
        # Add some fans
        manager.record_interaction("fan1", "x", "hello")
        for i in range(5):
            manager.record_interaction("fan2", "x", "great!")
        
        stats = manager.get_tier_stats()
        assert stats["casual"] >= 1
        assert stats["engaged"] >= 1
