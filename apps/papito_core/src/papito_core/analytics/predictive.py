"""Predictive Analytics & Self-Optimization for Papito Mamito.

Phase 3 features:
- Engagement pattern tracking (time, format, topic)
- Peak activity time detection per platform
- A/B testing framework for content types
- Autonomous content strategy adjustment
- Performance benchmarking
"""

from __future__ import annotations

import random
import statistics
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict

from pydantic import BaseModel


class ContentFormat(str, Enum):
    """Content format types for tracking."""
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    CAROUSEL = "carousel"
    STORY = "story"
    REEL = "reel"
    THREAD = "thread"


class EngagementMetric(str, Enum):
    """Types of engagement metrics."""
    LIKES = "likes"
    COMMENTS = "comments"
    SHARES = "shares"
    SAVES = "saves"
    VIEWS = "views"
    REACH = "reach"
    CLICKS = "clicks"


@dataclass
class EngagementData:
    """Engagement data for a single post."""
    post_id: str
    platform: str
    content_type: str
    content_format: ContentFormat
    posted_at: datetime
    hour_of_day: int
    day_of_week: int  # 0=Monday, 6=Sunday
    
    # Metrics
    likes: int = 0
    comments: int = 0
    shares: int = 0
    saves: int = 0
    views: int = 0
    reach: int = 0
    clicks: int = 0
    
    # Computed
    engagement_rate: float = 0.0
    
    def calculate_engagement_rate(self, follower_count: int) -> float:
        """Calculate engagement rate as percentage of followers."""
        if follower_count <= 0:
            return 0.0
        
        total_engagement = self.likes + self.comments + self.shares + self.saves
        self.engagement_rate = (total_engagement / follower_count) * 100
        return self.engagement_rate
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "post_id": self.post_id,
            "platform": self.platform,
            "content_type": self.content_type,
            "content_format": self.content_format.value,
            "posted_at": self.posted_at.isoformat(),
            "hour_of_day": self.hour_of_day,
            "day_of_week": self.day_of_week,
            "likes": self.likes,
            "comments": self.comments,
            "shares": self.shares,
            "saves": self.saves,
            "views": self.views,
            "reach": self.reach,
            "clicks": self.clicks,
            "engagement_rate": self.engagement_rate,
        }


@dataclass
class PeakTimeSlot:
    """A peak engagement time slot."""
    hour: int
    day_of_week: int  # 0=Monday, 6=Sunday, -1=all days
    avg_engagement_rate: float
    sample_count: int
    platform: str
    
    @property
    def day_name(self) -> str:
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        return days[self.day_of_week] if 0 <= self.day_of_week <= 6 else "All Days"


@dataclass
class ABTest:
    """An A/B test configuration."""
    test_id: str
    name: str
    description: str
    
    # Variants
    variant_a: Dict[str, Any]  # Control
    variant_b: Dict[str, Any]  # Treatment
    
    # Results
    variant_a_posts: List[str] = field(default_factory=list)
    variant_b_posts: List[str] = field(default_factory=list)
    variant_a_engagement: float = 0.0
    variant_b_engagement: float = 0.0
    
    # Status
    status: str = "running"  # "running", "completed", "paused"
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    winner: Optional[str] = None
    
    @property
    def sample_size(self) -> int:
        return len(self.variant_a_posts) + len(self.variant_b_posts)
    
    def get_winner(self, min_samples: int = 10) -> Optional[str]:
        """Determine winner if sample size is sufficient."""
        if self.sample_size < min_samples:
            return None
        
        if self.variant_a_engagement > self.variant_b_engagement * 1.1:
            return "A"
        elif self.variant_b_engagement > self.variant_a_engagement * 1.1:
            return "B"
        else:
            return "tie"


class EngagementTracker:
    """Tracks engagement patterns across posts.
    
    Features:
    - Records engagement by time, format, and topic
    - Identifies peak activity times
    - Calculates trends over time
    """
    
    def __init__(self):
        """Initialize the engagement tracker."""
        self._data: List[EngagementData] = []
        self._by_platform: Dict[str, List[EngagementData]] = defaultdict(list)
        self._by_hour: Dict[int, List[EngagementData]] = defaultdict(list)
        self._by_content_type: Dict[str, List[EngagementData]] = defaultdict(list)
    
    def record(self, data: EngagementData) -> None:
        """Record engagement data for a post."""
        self._data.append(data)
        self._by_platform[data.platform].append(data)
        self._by_hour[data.hour_of_day].append(data)
        self._by_content_type[data.content_type].append(data)
    
    def get_peak_times(
        self, 
        platform: str = "all",
        top_n: int = 5
    ) -> List[PeakTimeSlot]:
        """Get peak engagement times.
        
        Args:
            platform: Platform to analyze or "all"
            top_n: Number of peak slots to return
            
        Returns:
            List of peak time slots sorted by engagement
        """
        # Group by hour
        hourly_engagement: Dict[int, List[float]] = defaultdict(list)
        
        data = self._data if platform == "all" else self._by_platform.get(platform, [])
        
        for post in data:
            hourly_engagement[post.hour_of_day].append(post.engagement_rate)
        
        # Calculate averages
        peaks = []
        for hour, rates in hourly_engagement.items():
            if len(rates) >= 3:  # Require minimum samples
                peaks.append(PeakTimeSlot(
                    hour=hour,
                    day_of_week=-1,  # All days
                    avg_engagement_rate=statistics.mean(rates),
                    sample_count=len(rates),
                    platform=platform
                ))
        
        # Sort by engagement rate
        peaks.sort(key=lambda x: x.avg_engagement_rate, reverse=True)
        return peaks[:top_n]
    
    def get_best_content_types(
        self, 
        platform: str = "all",
        top_n: int = 5
    ) -> List[Tuple[str, float, int]]:
        """Get best performing content types.
        
        Returns:
            List of (content_type, avg_engagement_rate, sample_count)
        """
        type_engagement: Dict[str, List[float]] = defaultdict(list)
        
        data = self._data if platform == "all" else self._by_platform.get(platform, [])
        
        for post in data:
            type_engagement[post.content_type].append(post.engagement_rate)
        
        results = []
        for content_type, rates in type_engagement.items():
            if len(rates) >= 2:
                results.append((
                    content_type,
                    statistics.mean(rates),
                    len(rates)
                ))
        
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_n]
    
    def get_trend(self, days: int = 30) -> Dict[str, Any]:
        """Get engagement trend over time.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Trend data with direction and percentage change
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        recent = [d for d in self._data if d.posted_at >= cutoff]
        
        if len(recent) < 4:
            return {"direction": "insufficient_data", "change": 0.0}
        
        # Split into halves
        recent.sort(key=lambda x: x.posted_at)
        mid = len(recent) // 2
        first_half = recent[:mid]
        second_half = recent[mid:]
        
        avg_first = statistics.mean([d.engagement_rate for d in first_half])
        avg_second = statistics.mean([d.engagement_rate for d in second_half])
        
        if avg_first == 0:
            change = 100.0 if avg_second > 0 else 0.0
        else:
            change = ((avg_second - avg_first) / avg_first) * 100
        
        return {
            "direction": "up" if change > 5 else "down" if change < -5 else "stable",
            "change": round(change, 2),
            "first_half_avg": round(avg_first, 2),
            "second_half_avg": round(avg_second, 2),
            "sample_count": len(recent)
        }


class ABTestManager:
    """Manages A/B tests for content optimization.
    
    Features:
    - Create and manage content tests
    - Track variant performance
    - Determine statistical winners
    """
    
    def __init__(self):
        """Initialize the A/B test manager."""
        self._tests: Dict[str, ABTest] = {}
        self._active_tests: List[str] = []
    
    def create_test(
        self,
        name: str,
        description: str,
        variant_a: Dict[str, Any],
        variant_b: Dict[str, Any],
    ) -> ABTest:
        """Create a new A/B test.
        
        Args:
            name: Test name
            description: What we're testing
            variant_a: Control variant config
            variant_b: Treatment variant config
            
        Returns:
            Created ABTest
        """
        test_id = f"test_{len(self._tests) + 1}_{datetime.utcnow().strftime('%Y%m%d')}"
        
        test = ABTest(
            test_id=test_id,
            name=name,
            description=description,
            variant_a=variant_a,
            variant_b=variant_b,
        )
        
        self._tests[test_id] = test
        self._active_tests.append(test_id)
        
        return test
    
    def get_variant(self, test_id: str) -> str:
        """Get which variant to use for next post.
        
        Uses balanced random assignment.
        """
        test = self._tests.get(test_id)
        if not test or test.status != "running":
            return "A"
        
        # Balance assignment
        if len(test.variant_a_posts) > len(test.variant_b_posts):
            return "B"
        elif len(test.variant_b_posts) > len(test.variant_a_posts):
            return "A"
        else:
            return random.choice(["A", "B"])
    
    def record_result(
        self, 
        test_id: str, 
        variant: str, 
        post_id: str,
        engagement_rate: float
    ) -> None:
        """Record a test result."""
        test = self._tests.get(test_id)
        if not test:
            return
        
        if variant == "A":
            test.variant_a_posts.append(post_id)
            # Rolling average
            n = len(test.variant_a_posts)
            test.variant_a_engagement = (
                (test.variant_a_engagement * (n - 1) + engagement_rate) / n
            )
        else:
            test.variant_b_posts.append(post_id)
            n = len(test.variant_b_posts)
            test.variant_b_engagement = (
                (test.variant_b_engagement * (n - 1) + engagement_rate) / n
            )
    
    def check_completion(self, test_id: str, min_samples: int = 20) -> Optional[str]:
        """Check if test has enough data to determine winner."""
        test = self._tests.get(test_id)
        if not test:
            return None
        
        winner = test.get_winner(min_samples)
        
        if winner and winner != "tie":
            test.status = "completed"
            test.completed_at = datetime.utcnow()
            test.winner = winner
            self._active_tests.remove(test_id)
        
        return winner
    
    def get_active_tests(self) -> List[ABTest]:
        """Get all active tests."""
        return [self._tests[tid] for tid in self._active_tests]


class ContentStrategyOptimizer:
    """Autonomous content strategy adjustment.
    
    Analyzes performance data and recommends/implements
    strategy changes automatically.
    """
    
    def __init__(
        self,
        engagement_tracker: EngagementTracker,
        ab_test_manager: ABTestManager,
    ):
        """Initialize the optimizer."""
        self.tracker = engagement_tracker
        self.ab_tests = ab_test_manager
        
        # Strategy weights
        self._content_type_weights: Dict[str, float] = {}
        self._time_slot_weights: Dict[int, float] = {}
    
    def analyze_and_recommend(self) -> Dict[str, Any]:
        """Analyze performance and generate recommendations.
        
        Returns:
            Dict with recommendations for content strategy
        """
        recommendations = {
            "generated_at": datetime.utcnow().isoformat(),
            "peak_times": [],
            "best_content_types": [],
            "trend": {},
            "suggested_actions": [],
        }
        
        # Get peak times
        peak_times = self.tracker.get_peak_times(top_n=3)
        recommendations["peak_times"] = [
            {"hour": p.hour, "engagement": round(p.avg_engagement_rate, 2)}
            for p in peak_times
        ]
        
        # Get best content types
        best_types = self.tracker.get_best_content_types(top_n=3)
        recommendations["best_content_types"] = [
            {"type": t[0], "engagement": round(t[1], 2), "samples": t[2]}
            for t in best_types
        ]
        
        # Get trend
        trend = self.tracker.get_trend(days=14)
        recommendations["trend"] = trend
        
        # Generate action suggestions
        actions = []
        
        if trend["direction"] == "down":
            actions.append({
                "priority": "high",
                "action": "increase_posting_frequency",
                "reason": f"Engagement down {abs(trend['change'])}% over last 2 weeks"
            })
        
        if peak_times:
            best_hour = peak_times[0].hour
            actions.append({
                "priority": "medium",
                "action": "optimize_posting_times",
                "reason": f"Best engagement at {best_hour}:00",
                "details": {"optimal_hour": best_hour}
            })
        
        if best_types:
            top_type = best_types[0][0]
            actions.append({
                "priority": "medium",
                "action": "prioritize_content_type",
                "reason": f"{top_type} content performs best",
                "details": {"content_type": top_type}
            })
        
        recommendations["suggested_actions"] = actions
        
        return recommendations
    
    def update_weights(self) -> Dict[str, float]:
        """Update content type weights based on performance.
        
        Returns:
            Updated weight distribution for content types
        """
        best_types = self.tracker.get_best_content_types(top_n=10)
        
        if not best_types:
            return {}
        
        # Normalize to weights that sum to 1
        total_engagement = sum(t[1] for t in best_types)
        
        if total_engagement == 0:
            # Equal weights
            self._content_type_weights = {
                t[0]: 1.0 / len(best_types) for t in best_types
            }
        else:
            self._content_type_weights = {
                t[0]: t[1] / total_engagement for t in best_types
            }
        
        return self._content_type_weights
    
    def suggest_next_content_type(self) -> str:
        """Suggest what type of content to post next.
        
        Uses weighted random selection based on performance.
        """
        if not self._content_type_weights:
            self.update_weights()
        
        if not self._content_type_weights:
            # Default to morning_blessing
            return "morning_blessing"
        
        # Weighted random choice
        types = list(self._content_type_weights.keys())
        weights = list(self._content_type_weights.values())
        
        return random.choices(types, weights=weights, k=1)[0]
