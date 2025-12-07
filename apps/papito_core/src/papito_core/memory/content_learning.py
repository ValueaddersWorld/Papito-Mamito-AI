"""Content Learning System for Papito AI.

This module handles:
- Tracking content performance metrics
- Learning what content resonates with audience
- Generating insights and recommendations
- Optimizing content strategy over time
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import random

logger = logging.getLogger(__name__)


class ContentType(str, Enum):
    """Types of content Papito posts."""
    
    PROMOTIONAL = "promotional"
    PHILOSOPHICAL = "philosophical"
    ENGAGEMENT = "engagement"
    MUSIC_UPDATE = "music_update"
    FAN_APPRECIATION = "fan_appreciation"
    INTERVIEW = "interview"
    QUOTE = "quote"
    QUESTION = "question"
    ANNOUNCEMENT = "announcement"
    PERSONAL = "personal"


class TimeSlot(str, Enum):
    """Time slots for posting."""
    
    EARLY_MORNING = "early_morning"  # 5-8 AM
    MORNING = "morning"  # 8-11 AM
    MIDDAY = "midday"  # 11 AM-2 PM
    AFTERNOON = "afternoon"  # 2-5 PM
    EVENING = "evening"  # 5-8 PM
    NIGHT = "night"  # 8-11 PM
    LATE_NIGHT = "late_night"  # 11 PM-5 AM


@dataclass
class ContentPerformance:
    """Tracks performance of a single piece of content."""
    
    id: str
    content_type: ContentType
    content_preview: str  # First 100 chars
    posted_at: datetime
    time_slot: TimeSlot
    hashtags: List[str] = field(default_factory=list)
    topics: List[str] = field(default_factory=list)
    
    # Engagement metrics
    likes: int = 0
    retweets: int = 0
    replies: int = 0
    quotes: int = 0
    impressions: int = 0
    
    # Derived metrics
    engagement_rate: float = 0.0
    virality_score: float = 0.0
    
    def calculate_metrics(self) -> None:
        """Calculate derived metrics."""
        total_engagement = self.likes + self.retweets + self.replies + self.quotes
        
        if self.impressions > 0:
            self.engagement_rate = (total_engagement / self.impressions) * 100
        else:
            self.engagement_rate = 0.0
        
        # Virality score (retweets and quotes indicate sharing)
        if total_engagement > 0:
            self.virality_score = ((self.retweets + self.quotes) / total_engagement) * 100
        else:
            self.virality_score = 0.0
    
    @property
    def total_engagement(self) -> int:
        """Get total engagement count."""
        return self.likes + self.retweets + self.replies + self.quotes
    
    @property
    def engagement_score(self) -> float:
        """Calculate weighted engagement score."""
        return (
            self.likes * 1 +
            self.retweets * 3 +
            self.replies * 2 +
            self.quotes * 4
        )


@dataclass
class ContentInsight:
    """An insight derived from content analysis."""
    
    category: str
    insight: str
    confidence: float  # 0-1
    recommendation: str
    data_points: int


class ContentLearner:
    """Learns from content performance to optimize strategy.
    
    Tracks what works, identifies patterns, and provides
    recommendations for better content.
    """
    
    def __init__(self):
        """Initialize the content learner."""
        # Performance tracking
        self.content_history: List[ContentPerformance] = []
        
        # Aggregated learnings
        self.type_performance: Dict[ContentType, List[float]] = {ct: [] for ct in ContentType}
        self.timeslot_performance: Dict[TimeSlot, List[float]] = {ts: [] for ts in TimeSlot}
        self.hashtag_performance: Dict[str, List[float]] = {}
        self.topic_performance: Dict[str, List[float]] = {}
        
        # Best performers
        self.best_content: List[ContentPerformance] = []
        
        # Stats
        self.total_content_tracked = 0
        
    def _generate_id(self) -> str:
        """Generate a unique content ID."""
        import uuid
        return f"CNT-{str(uuid.uuid4())[:12]}"
    
    def _get_time_slot(self, time: datetime) -> TimeSlot:
        """Determine time slot from datetime.
        
        Args:
            time: Datetime to categorize
            
        Returns:
            Appropriate TimeSlot
        """
        hour = time.hour
        
        if 5 <= hour < 8:
            return TimeSlot.EARLY_MORNING
        elif 8 <= hour < 11:
            return TimeSlot.MORNING
        elif 11 <= hour < 14:
            return TimeSlot.MIDDAY
        elif 14 <= hour < 17:
            return TimeSlot.AFTERNOON
        elif 17 <= hour < 20:
            return TimeSlot.EVENING
        elif 20 <= hour < 23:
            return TimeSlot.NIGHT
        else:
            return TimeSlot.LATE_NIGHT
    
    def record_content(
        self,
        content_type: str,
        content_preview: str,
        posted_at: datetime,
        hashtags: Optional[List[str]] = None,
        topics: Optional[List[str]] = None,
    ) -> ContentPerformance:
        """Record a new piece of content.
        
        Args:
            content_type: Type of content
            content_preview: First 100 chars of content
            posted_at: When it was posted
            hashtags: Hashtags used
            topics: Topics covered
            
        Returns:
            Created ContentPerformance
        """
        ctype = ContentType(content_type) if content_type in [e.value for e in ContentType] else ContentType.ENGAGEMENT
        
        performance = ContentPerformance(
            id=self._generate_id(),
            content_type=ctype,
            content_preview=content_preview[:100],
            posted_at=posted_at,
            time_slot=self._get_time_slot(posted_at),
            hashtags=hashtags or [],
            topics=topics or [],
        )
        
        self.content_history.append(performance)
        self.total_content_tracked += 1
        
        logger.info(f"Recorded content: {performance.id} ({ctype.value})")
        return performance
    
    def update_metrics(
        self,
        content_id: str,
        likes: int = 0,
        retweets: int = 0,
        replies: int = 0,
        quotes: int = 0,
        impressions: int = 0,
    ) -> Optional[ContentPerformance]:
        """Update metrics for a piece of content.
        
        Args:
            content_id: ID of the content
            likes: Number of likes
            retweets: Number of retweets
            replies: Number of replies
            quotes: Number of quote tweets
            impressions: Number of impressions
            
        Returns:
            Updated ContentPerformance or None
        """
        content = next((c for c in self.content_history if c.id == content_id), None)
        
        if not content:
            return None
        
        content.likes = likes
        content.retweets = retweets
        content.replies = replies
        content.quotes = quotes
        content.impressions = impressions
        content.calculate_metrics()
        
        # Update aggregated data
        score = content.engagement_score
        
        # Type performance
        self.type_performance[content.content_type].append(score)
        
        # Time slot performance
        self.timeslot_performance[content.time_slot].append(score)
        
        # Hashtag performance
        for hashtag in content.hashtags:
            if hashtag not in self.hashtag_performance:
                self.hashtag_performance[hashtag] = []
            self.hashtag_performance[hashtag].append(score)
        
        # Topic performance
        for topic in content.topics:
            if topic not in self.topic_performance:
                self.topic_performance[topic] = []
            self.topic_performance[topic].append(score)
        
        # Track best performers
        if score > 0:
            self.best_content.append(content)
            self.best_content = sorted(
                self.best_content,
                key=lambda x: x.engagement_score,
                reverse=True
            )[:50]  # Keep top 50
        
        logger.info(f"Updated metrics for {content_id}: score={score}")
        return content
    
    def get_best_content_type(self) -> Tuple[ContentType, float]:
        """Get the best performing content type.
        
        Returns:
            Tuple of (ContentType, average_score)
        """
        best_type = ContentType.ENGAGEMENT
        best_avg = 0.0
        
        for ctype, scores in self.type_performance.items():
            if scores:
                avg = sum(scores) / len(scores)
                if avg > best_avg:
                    best_avg = avg
                    best_type = ctype
        
        return best_type, best_avg
    
    def get_best_time_slot(self) -> Tuple[TimeSlot, float]:
        """Get the best performing time slot.
        
        Returns:
            Tuple of (TimeSlot, average_score)
        """
        best_slot = TimeSlot.EVENING
        best_avg = 0.0
        
        for slot, scores in self.timeslot_performance.items():
            if scores:
                avg = sum(scores) / len(scores)
                if avg > best_avg:
                    best_avg = avg
                    best_slot = slot
        
        return best_slot, best_avg
    
    def get_best_hashtags(self, limit: int = 5) -> List[Tuple[str, float]]:
        """Get best performing hashtags.
        
        Args:
            limit: Max hashtags to return
            
        Returns:
            List of (hashtag, average_score) tuples
        """
        hashtag_avgs = []
        
        for hashtag, scores in self.hashtag_performance.items():
            if len(scores) >= 3:  # Minimum data points
                avg = sum(scores) / len(scores)
                hashtag_avgs.append((hashtag, avg))
        
        return sorted(hashtag_avgs, key=lambda x: x[1], reverse=True)[:limit]
    
    def get_best_topics(self, limit: int = 5) -> List[Tuple[str, float]]:
        """Get best performing topics.
        
        Args:
            limit: Max topics to return
            
        Returns:
            List of (topic, average_score) tuples
        """
        topic_avgs = []
        
        for topic, scores in self.topic_performance.items():
            if len(scores) >= 3:
                avg = sum(scores) / len(scores)
                topic_avgs.append((topic, avg))
        
        return sorted(topic_avgs, key=lambda x: x[1], reverse=True)[:limit]
    
    def generate_insights(self) -> List[ContentInsight]:
        """Generate insights from content performance data.
        
        Returns:
            List of ContentInsight objects
        """
        insights = []
        
        # Content type insight
        if sum(len(s) for s in self.type_performance.values()) >= 10:
            best_type, best_score = self.get_best_content_type()
            
            type_data = len(self.type_performance[best_type])
            if type_data >= 3:
                insights.append(ContentInsight(
                    category="content_type",
                    insight=f"{best_type.value.replace('_', ' ').title()} content performs best",
                    confidence=min(type_data / 20, 1.0),
                    recommendation=f"Consider posting more {best_type.value} content",
                    data_points=type_data,
                ))
        
        # Time slot insight
        if sum(len(s) for s in self.timeslot_performance.values()) >= 10:
            best_slot, best_score = self.get_best_time_slot()
            
            slot_data = len(self.timeslot_performance[best_slot])
            if slot_data >= 3:
                insights.append(ContentInsight(
                    category="timing",
                    insight=f"Best engagement during {best_slot.value.replace('_', ' ')}",
                    confidence=min(slot_data / 20, 1.0),
                    recommendation=f"Prioritize posting during {best_slot.value.replace('_', ' ')}",
                    data_points=slot_data,
                ))
        
        # Hashtag insight
        best_hashtags = self.get_best_hashtags(3)
        if best_hashtags:
            hashtag_str = ", ".join(h[0] for h in best_hashtags)
            insights.append(ContentInsight(
                category="hashtags",
                insight=f"Top performing hashtags: {hashtag_str}",
                confidence=0.7,
                recommendation=f"Use hashtags like {best_hashtags[0][0]} more often",
                data_points=sum(len(self.hashtag_performance.get(h[0], [])) for h in best_hashtags),
            ))
        
        # Topic insight
        best_topics = self.get_best_topics(3)
        if best_topics:
            topic_str = ", ".join(t[0] for t in best_topics)
            insights.append(ContentInsight(
                category="topics",
                insight=f"Audience engages most with: {topic_str}",
                confidence=0.7,
                recommendation=f"Focus content on {best_topics[0][0]}",
                data_points=sum(len(self.topic_performance.get(t[0], [])) for t in best_topics),
            ))
        
        return insights
    
    def get_content_recommendations(self) -> Dict[str, Any]:
        """Get recommendations for next content.
        
        Returns:
            Dictionary of recommendations
        """
        recommendations = {
            "recommended_type": None,
            "recommended_time": None,
            "recommended_hashtags": [],
            "recommended_topics": [],
            "insights": [],
        }
        
        # Best type
        if any(self.type_performance.values()):
            best_type, _ = self.get_best_content_type()
            recommendations["recommended_type"] = best_type.value
        
        # Best time
        if any(self.timeslot_performance.values()):
            best_slot, _ = self.get_best_time_slot()
            recommendations["recommended_time"] = best_slot.value
        
        # Best hashtags
        recommendations["recommended_hashtags"] = [h[0] for h in self.get_best_hashtags(5)]
        
        # Best topics
        recommendations["recommended_topics"] = [t[0] for t in self.get_best_topics(5)]
        
        # Insights
        recommendations["insights"] = [
            {
                "category": i.category,
                "insight": i.insight,
                "recommendation": i.recommendation,
                "confidence": i.confidence,
            }
            for i in self.generate_insights()
        ]
        
        return recommendations
    
    def get_stats(self) -> Dict[str, Any]:
        """Get content learning statistics."""
        return {
            "total_content_tracked": self.total_content_tracked,
            "best_performers_count": len(self.best_content),
            "hashtags_tracked": len(self.hashtag_performance),
            "topics_tracked": len(self.topic_performance),
            "insights_available": len(self.generate_insights()),
        }


# Singleton instance
_content_learner: Optional[ContentLearner] = None


def get_content_learner() -> ContentLearner:
    """Get or create the singleton ContentLearner instance."""
    global _content_learner
    if _content_learner is None:
        _content_learner = ContentLearner()
    return _content_learner
