"""Trending topic detector for social media platforms.

Monitors trending hashtags and topics relevant to Afrobeat,
AI music, and Papito's brand for content participation.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
from enum import Enum


class TopicRelevance(str, Enum):
    """Relevance level of a trending topic to Papito."""
    HIGH = "high"      # Directly relevant (Afrobeat, AI music)
    MEDIUM = "medium"  # Related (music, creativity, Africa)
    LOW = "low"        # Tangential (general entertainment)
    NONE = "none"      # Not relevant


@dataclass
class TrendingTopic:
    """A trending topic or hashtag."""
    name: str
    platform: str
    volume: int  # Approximate post count
    velocity: float  # Growth rate
    relevance: TopicRelevance = TopicRelevance.NONE
    relevance_score: float = 0.0
    detected_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "platform": self.platform,
            "volume": self.volume,
            "velocity": self.velocity,
            "relevance": self.relevance.value,
            "relevance_score": self.relevance_score,
            "detected_at": self.detected_at.isoformat(),
        }


class TrendingDetector:
    """Detects and scores trending topics for Papito relevance.
    
    Monitors trending topics across platforms and identifies
    opportunities for Papito to participate in conversations.
    """
    
    # Core hashtags Papito always wants to participate in
    CORE_HASHTAGS: Set[str] = {
        "#Afrobeat", "#AfroMusic", "#AfrobeatMusic",
        "#AIMusic", "#AIArtist", "#MusicAI",
        "#MusicProduction", "#BeatMaker", "#Producer",
        "#NigerianMusic", "#AfricanMusic", "#Naija",
        "#NewMusic", "#MusicMonday", "#FreshMusic",
    }
    
    # Keywords that indicate relevance
    RELEVANT_KEYWORDS: Dict[str, float] = {
        "afrobeat": 1.0,
        "afro": 0.9,
        "naija": 0.95,
        "nigerian": 0.85,
        "african music": 0.9,
        "music production": 0.8,
        "ai music": 1.0,
        "ai artist": 1.0,
        "beat": 0.6,
        "rhythm": 0.6,
        "vibes": 0.5,
        "groove": 0.6,
        "producer": 0.7,
        "studio": 0.6,
        "new music": 0.7,
        "fela": 0.95,  # Fela Kuti reference
        "burna": 0.8,  # Burna Boy
        "wizkid": 0.8,
        "davido": 0.8,
        "inspire": 0.5,
        "blessing": 0.5,
        "motivat": 0.5,
    }
    
    # Keywords to avoid (controversies, politics, etc.)
    AVOID_KEYWORDS: Set[str] = {
        "politic", "election", "scandal", "death", "tragedy",
        "war", "violence", "hate", "controversy", "cancel",
    }
    
    def __init__(self):
        """Initialize the trending detector."""
        self._cache: Dict[str, List[TrendingTopic]] = {}
        self._cache_expiry = timedelta(minutes=30)
        self._last_fetch: Dict[str, datetime] = {}
    
    def score_topic_relevance(self, topic_name: str) -> tuple[TopicRelevance, float]:
        """Score how relevant a topic is to Papito's brand.
        
        Args:
            topic_name: The trending topic or hashtag
            
        Returns:
            Tuple of (relevance level, score 0-1)
        """
        lower_name = topic_name.lower()
        
        # Check for topics to avoid
        for avoid in self.AVOID_KEYWORDS:
            if avoid in lower_name:
                return TopicRelevance.NONE, 0.0
        
        # Check if it's a core hashtag
        if topic_name in self.CORE_HASHTAGS or f"#{topic_name}".lower() in {h.lower() for h in self.CORE_HASHTAGS}:
            return TopicRelevance.HIGH, 1.0
        
        # Calculate score based on keyword matches
        score = 0.0
        for keyword, weight in self.RELEVANT_KEYWORDS.items():
            if keyword in lower_name:
                score = max(score, weight)
        
        # Determine relevance level
        if score >= 0.8:
            return TopicRelevance.HIGH, score
        elif score >= 0.5:
            return TopicRelevance.MEDIUM, score
        elif score >= 0.3:
            return TopicRelevance.LOW, score
        else:
            return TopicRelevance.NONE, score
    
    def get_relevant_hashtags_for_content(
        self,
        content_type: str,
        max_hashtags: int = 5,
        include_core: bool = True,
    ) -> List[str]:
        """Get relevant hashtags for a piece of content.
        
        Args:
            content_type: Type of content being posted
            max_hashtags: Maximum number of hashtags to return
            include_core: Whether to always include core hashtags
            
        Returns:
            List of hashtag strings
        """
        hashtags = []
        
        # Content-specific hashtags
        content_hashtags = {
            "morning_blessing": ["#MorningMotivation", "#BlessedMorning", "#PositiveVibes"],
            "track_snippet": ["#NewMusic", "#MusicPreview", "#ComingSoon"],
            "behind_the_scenes": ["#BehindTheScenes", "#StudioLife", "#MusicProduction"],
            "lyrics_quote": ["#MusicQuotes", "#Lyrics", "#MusicWisdom"],
            "fan_appreciation": ["#FanLove", "#Grateful", "#Community"],
            "educational": ["#MusicEducation", "#LearnMusic", "#MusicTips"],
            "afrobeat_history": ["#AfrobeatHistory", "#MusicHistory", "#AfricanCulture"],
            "trending_topic": [],  # Will add from actual trends
            "music_wisdom": ["#MusicWisdom", "#LifeLessons", "#Inspiration"],
            "studio_update": ["#StudioFlow", "#MakingMusic", "#ProducerLife"],
        }
        
        # Start with content-specific tags
        specific = content_hashtags.get(content_type, [])
        hashtags.extend(specific[:2])
        
        # Add core Papito hashtags
        if include_core:
            core = ["#Afrobeat", "#PapitoMamito", "#AIMusic", "#AddValue"]
            for tag in core:
                if tag not in hashtags:
                    hashtags.append(tag)
        
        # Shuffle and limit
        if len(hashtags) > max_hashtags:
            # Keep first 2 (content-specific) and shuffle the rest
            fixed = hashtags[:2]
            rest = hashtags[2:]
            random.shuffle(rest)
            hashtags = fixed + rest[:max_hashtags - 2]
        
        return hashtags[:max_hashtags]
    
    async def fetch_trending_topics(
        self,
        platform: str,
        x_bearer_token: Optional[str] = None,
    ) -> List[TrendingTopic]:
        """Fetch trending topics from a platform.
        
        Note: Actual API calls would require platform credentials.
        This provides a framework + mock data for testing.
        
        Args:
            platform: Platform to fetch from (x, instagram, tiktok)
            x_bearer_token: Bearer token for X API
            
        Returns:
            List of TrendingTopic objects
        """
        # Check cache
        cache_key = f"{platform}_trends"
        if cache_key in self._cache:
            last_fetch = self._last_fetch.get(cache_key)
            if last_fetch and datetime.now() - last_fetch < self._cache_expiry:
                return self._cache[cache_key]
        
        topics = []
        
        if platform == "x" and x_bearer_token:
            # Would make actual X API call here
            # For now, return mock relevant topics
            topics = await self._fetch_x_trends(x_bearer_token)
        else:
            # Return commonly trending music topics
            topics = self._get_mock_music_trends(platform)
        
        # Score each topic
        for topic in topics:
            relevance, score = self.score_topic_relevance(topic.name)
            topic.relevance = relevance
            topic.relevance_score = score
        
        # Filter to only relevant topics
        topics = [t for t in topics if t.relevance != TopicRelevance.NONE]
        
        # Cache results
        self._cache[cache_key] = topics
        self._last_fetch[cache_key] = datetime.now()
        
        return topics
    
    async def _fetch_x_trends(self, bearer_token: str) -> List[TrendingTopic]:
        """Fetch trends from X API.
        
        Note: Requires X API v2 access.
        """
        try:
            import httpx
            
            async with httpx.AsyncClient() as client:
                # X API trends endpoint (would need WOEID for location)
                # Using global trends
                response = await client.get(
                    "https://api.twitter.com/2/tweets/search/stream/rules",
                    headers={"Authorization": f"Bearer {bearer_token}"}
                )
                
                if response.status_code == 200:
                    # Parse and return trends
                    # This is a placeholder - actual parsing depends on API response
                    pass
                    
        except Exception as e:
            print(f"Error fetching X trends: {e}")
        
        # Return mock data on error
        return self._get_mock_music_trends("x")
    
    def _get_mock_music_trends(self, platform: str) -> List[TrendingTopic]:
        """Get mock trending topics for testing."""
        mock_trends = [
            TrendingTopic(
                name="#Afrobeat2024",
                platform=platform,
                volume=50000,
                velocity=1.5,
            ),
            TrendingTopic(
                name="#NewMusicFriday",
                platform=platform,
                volume=120000,
                velocity=2.0,
            ),
            TrendingTopic(
                name="#AIMusic",
                platform=platform,
                volume=25000,
                velocity=1.8,
            ),
            TrendingTopic(
                name="#NigerianMusic",
                platform=platform,
                volume=45000,
                velocity=1.2,
            ),
            TrendingTopic(
                name="#MusicProducerLife",
                platform=platform,
                volume=30000,
                velocity=1.3,
            ),
        ]
        
        return mock_trends
    
    def get_best_trending_hashtag(
        self,
        topics: List[TrendingTopic],
        min_relevance: TopicRelevance = TopicRelevance.MEDIUM,
    ) -> Optional[str]:
        """Get the best trending hashtag to use.
        
        Args:
            topics: List of trending topics
            min_relevance: Minimum relevance level required
            
        Returns:
            Best hashtag to use, or None
        """
        # Filter by minimum relevance
        relevance_order = [TopicRelevance.HIGH, TopicRelevance.MEDIUM, TopicRelevance.LOW]
        min_index = relevance_order.index(min_relevance)
        allowed = set(relevance_order[:min_index + 1])
        
        eligible = [t for t in topics if t.relevance in allowed]
        
        if not eligible:
            return None
        
        # Sort by score and volume
        eligible.sort(key=lambda t: (t.relevance_score, t.volume), reverse=True)
        
        return eligible[0].name if eligible[0].name.startswith("#") else f"#{eligible[0].name}"
