"""Tests for Phase 3 predictive analytics module."""

import pytest
from datetime import datetime, timedelta

from papito_core.analytics import (
    ContentFormat,
    EngagementData,
    PeakTimeSlot,
    ABTest,
    EngagementTracker,
    ABTestManager,
    ContentStrategyOptimizer,
)


class TestEngagementData:
    """Tests for EngagementData dataclass."""
    
    def test_create_engagement_data(self):
        """Test creating engagement data."""
        data = EngagementData(
            post_id="test_123",
            platform="instagram",
            content_type="morning_blessing",
            content_format=ContentFormat.IMAGE,
            posted_at=datetime.utcnow(),
            hour_of_day=8,
            day_of_week=1,
            likes=100,
            comments=20,
        )
        assert data.post_id == "test_123"
        assert data.likes == 100
    
    def test_calculate_engagement_rate(self):
        """Test engagement rate calculation."""
        data = EngagementData(
            post_id="test",
            platform="x",
            content_type="track_snippet",
            content_format=ContentFormat.VIDEO,
            posted_at=datetime.utcnow(),
            hour_of_day=12,
            day_of_week=3,
            likes=100,
            comments=20,
            shares=10,
            saves=5,
        )
        
        rate = data.calculate_engagement_rate(follower_count=1000)
        # (100 + 20 + 10 + 5) / 1000 * 100 = 13.5%
        assert rate == 13.5
    
    def test_to_dict(self):
        """Test serialization to dict."""
        data = EngagementData(
            post_id="test",
            platform="x",
            content_type="test",
            content_format=ContentFormat.TEXT,
            posted_at=datetime.utcnow(),
            hour_of_day=12,
            day_of_week=3,
        )
        d = data.to_dict()
        assert d["post_id"] == "test"
        assert d["content_format"] == "text"


class TestPeakTimeSlot:
    """Tests for PeakTimeSlot."""
    
    def test_day_name(self):
        """Test day name property."""
        slot = PeakTimeSlot(
            hour=14,
            day_of_week=2,  # Wednesday
            avg_engagement_rate=5.5,
            sample_count=10,
            platform="instagram"
        )
        assert slot.day_name == "Wednesday"
    
    def test_all_days_name(self):
        """Test all days indicator."""
        slot = PeakTimeSlot(
            hour=18,
            day_of_week=-1,
            avg_engagement_rate=4.0,
            sample_count=20,
            platform="x"
        )
        assert slot.day_name == "All Days"


class TestEngagementTracker:
    """Tests for EngagementTracker."""
    
    @pytest.fixture
    def tracker(self):
        return EngagementTracker()
    
    @pytest.fixture
    def sample_data(self):
        """Generate sample engagement data."""
        data = []
        base_time = datetime.utcnow()
        
        # Morning posts (8am) with high engagement
        for i in range(5):
            d = EngagementData(
                post_id=f"morning_{i}",
                platform="instagram",
                content_type="morning_blessing",
                content_format=ContentFormat.IMAGE,
                posted_at=base_time - timedelta(days=i),
                hour_of_day=8,
                day_of_week=i % 7,
                likes=150 + i * 10,
                comments=30 + i * 5,
            )
            d.calculate_engagement_rate(1000)
            data.append(d)
        
        # Evening posts (19:00) with medium engagement
        for i in range(5):
            d = EngagementData(
                post_id=f"evening_{i}",
                platform="instagram",
                content_type="fan_appreciation",
                content_format=ContentFormat.TEXT,
                posted_at=base_time - timedelta(days=i),
                hour_of_day=19,
                day_of_week=i % 7,
                likes=80 + i * 5,
                comments=15,
            )
            d.calculate_engagement_rate(1000)
            data.append(d)
        
        return data
    
    def test_record_data(self, tracker):
        """Test recording engagement data."""
        data = EngagementData(
            post_id="test",
            platform="x",
            content_type="test",
            content_format=ContentFormat.TEXT,
            posted_at=datetime.utcnow(),
            hour_of_day=12,
            day_of_week=3,
        )
        tracker.record(data)
        assert len(tracker._data) == 1
    
    def test_get_peak_times(self, tracker, sample_data):
        """Test peak time detection."""
        for d in sample_data:
            tracker.record(d)
        
        peaks = tracker.get_peak_times(top_n=3)
        assert len(peaks) > 0
        # Morning should be peak
        assert peaks[0].hour == 8
    
    def test_get_best_content_types(self, tracker, sample_data):
        """Test best content type detection."""
        for d in sample_data:
            tracker.record(d)
        
        best = tracker.get_best_content_types(top_n=3)
        assert len(best) >= 2
        # Morning blessing should be top
        assert best[0][0] == "morning_blessing"
    
    def test_get_trend_insufficient_data(self, tracker):
        """Test trend with insufficient data."""
        trend = tracker.get_trend()
        assert trend["direction"] == "insufficient_data"
    
    def test_get_trend(self, tracker, sample_data):
        """Test trend calculation."""
        for d in sample_data:
            tracker.record(d)
        
        trend = tracker.get_trend(days=30)
        assert trend["direction"] in ["up", "down", "stable"]
        assert "change" in trend


class TestABTestManager:
    """Tests for ABTestManager."""
    
    @pytest.fixture
    def manager(self):
        return ABTestManager()
    
    def test_create_test(self, manager):
        """Test creating an A/B test."""
        test = manager.create_test(
            name="Hashtag Test",
            description="Test different hashtag strategies",
            variant_a={"hashtags": 5},
            variant_b={"hashtags": 10},
        )
        assert test.name == "Hashtag Test"
        assert test.status == "running"
    
    def test_get_variant_balanced(self, manager):
        """Test balanced variant assignment."""
        test = manager.create_test(
            name="Test",
            description="Test",
            variant_a={},
            variant_b={},
        )
        
        # First call should be random
        v1 = manager.get_variant(test.test_id)
        assert v1 in ["A", "B"]
        
        # Record result for that variant
        manager.record_result(test.test_id, v1, "post_1", 5.0)
        
        # Next should be the other variant  
        v2 = manager.get_variant(test.test_id)
        assert v2 != v1  # Should balance
    
    def test_record_result(self, manager):
        """Test recording test results."""
        test = manager.create_test(
            name="Test",
            description="Test",
            variant_a={},
            variant_b={},
        )
        
        manager.record_result(test.test_id, "A", "post_1", 5.0)
        manager.record_result(test.test_id, "A", "post_2", 7.0)
        
        assert len(test.variant_a_posts) == 2
        assert test.variant_a_engagement == 6.0  # Average
    
    def test_check_completion(self, manager):
        """Test test completion check."""
        test = manager.create_test(
            name="Test",
            description="Test",
            variant_a={},
            variant_b={},
        )
        
        # Add enough samples
        for i in range(10):
            manager.record_result(test.test_id, "A", f"a_{i}", 5.0)
            manager.record_result(test.test_id, "B", f"b_{i}", 8.0)  # B wins clearly
        
        winner = manager.check_completion(test.test_id, min_samples=20)
        assert winner == "B"
        assert test.status == "completed"


class TestContentStrategyOptimizer:
    """Tests for ContentStrategyOptimizer."""
    
    @pytest.fixture
    def optimizer(self):
        tracker = EngagementTracker()
        ab_manager = ABTestManager()
        return ContentStrategyOptimizer(tracker, ab_manager)
    
    @pytest.fixture
    def optimizer_with_data(self, optimizer):
        """Optimizer with sample data."""
        base_time = datetime.utcnow()
        
        for i in range(10):
            d = EngagementData(
                post_id=f"post_{i}",
                platform="instagram",
                content_type="morning_blessing" if i % 2 == 0 else "track_snippet",
                content_format=ContentFormat.IMAGE,
                posted_at=base_time - timedelta(days=i),
                hour_of_day=8 if i % 2 == 0 else 14,
                day_of_week=i % 7,
            )
            d.engagement_rate = 10.0 if i % 2 == 0 else 5.0
            optimizer.tracker.record(d)
        
        return optimizer
    
    def test_analyze_and_recommend(self, optimizer_with_data):
        """Test generating recommendations."""
        recommendations = optimizer_with_data.analyze_and_recommend()
        
        assert "peak_times" in recommendations
        assert "best_content_types" in recommendations
        assert "suggested_actions" in recommendations
    
    def test_update_weights(self, optimizer_with_data):
        """Test weight calculation."""
        weights = optimizer_with_data.update_weights()
        
        assert len(weights) > 0
        # Morning blessing should have higher weight
        assert weights.get("morning_blessing", 0) > weights.get("track_snippet", 0)
    
    def test_suggest_next_content_type(self, optimizer_with_data):
        """Test content type suggestion."""
        # Run several times to check weighted selection
        suggestions = [
            optimizer_with_data.suggest_next_content_type() 
            for _ in range(20)
        ]
        
        # Should suggest morning_blessing more often (higher engagement)
        assert "morning_blessing" in suggestions
