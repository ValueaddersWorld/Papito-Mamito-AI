"""Fan Engagement Manager for Papito Mamito.

Advanced fan management with:
- Engagement tiers (Casual → Engaged → Core → Super Fan)
- Sentiment analysis for interactions
- Personalized interaction memory
- Automated new follower welcome
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

try:
    import openai
except ImportError:
    openai = None


class EngagementTier(str, Enum):
    """Fan engagement tiers based on interaction frequency and quality."""
    CASUAL = "casual"           # Occasional interactions
    ENGAGED = "engaged"         # Regular interactions  
    CORE = "core"               # High engagement, loyal supporter
    SUPER_FAN = "super_fan"     # Top tier, brand advocates


class Sentiment(str, Enum):
    """Sentiment classification for fan messages."""
    VERY_POSITIVE = "very_positive"
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    VERY_NEGATIVE = "very_negative"


@dataclass
class EngagementScore:
    """Calculated engagement metrics for a fan."""
    total_interactions: int = 0
    positive_interactions: int = 0
    negative_interactions: int = 0
    avg_sentiment_score: float = 0.5  # 0-1 scale
    days_since_first_interaction: int = 0
    days_since_last_interaction: int = 0
    platforms_active: List[str] = field(default_factory=list)
    
    @property
    def tier(self) -> EngagementTier:
        """Calculate tier based on engagement metrics."""
        if self.total_interactions >= 20 and self.avg_sentiment_score >= 0.7:
            return EngagementTier.SUPER_FAN
        elif self.total_interactions >= 10 and self.avg_sentiment_score >= 0.5:
            return EngagementTier.CORE
        elif self.total_interactions >= 3:
            return EngagementTier.ENGAGED
        else:
            return EngagementTier.CASUAL
    
    @property
    def tier_progress(self) -> float:
        """Progress toward next tier (0-1)."""
        current = self.tier
        if current == EngagementTier.SUPER_FAN:
            return 1.0
        
        thresholds = {
            EngagementTier.CASUAL: 3,
            EngagementTier.ENGAGED: 10,
            EngagementTier.CORE: 20,
        }
        
        next_threshold = thresholds.get(current, 3)
        return min(self.total_interactions / next_threshold, 1.0)


class FanProfile(BaseModel):
    """Enhanced fan profile with engagement tracking."""
    
    # Identity
    username: str
    display_name: str = ""
    platform: str
    profile_url: str = ""
    
    # Engagement metrics
    total_interactions: int = 0
    positive_interactions: int = 0
    negative_interactions: int = 0
    first_interaction_at: Optional[datetime] = None
    last_interaction_at: Optional[datetime] = None
    
    # Preferences (learned over time)
    favorite_content_types: List[str] = []
    mentioned_tracks: List[str] = []
    preferred_greeting: str = ""
    
    # Notes and context
    notes: str = ""
    tags: List[str] = []
    
    # Computed
    tier: str = EngagementTier.CASUAL.value
    
    def update_tier(self) -> None:
        """Recalculate tier based on current metrics."""
        score = EngagementScore(
            total_interactions=self.total_interactions,
            positive_interactions=self.positive_interactions,
            negative_interactions=self.negative_interactions,
        )
        self.tier = score.tier.value
    
    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


class SentimentAnalyzer:
    """Analyzes sentiment of fan messages.
    
    Uses keyword-based analysis with optional AI enhancement.
    """
    
    # Positive indicators
    POSITIVE_KEYWORDS = {
        "love": 0.3, "amazing": 0.3, "beautiful": 0.3, "fire": 0.25,
        "blessed": 0.25, "incredible": 0.3, "best": 0.2, "great": 0.2,
        "thank": 0.2, "grateful": 0.25, "vibes": 0.15, "inspire": 0.2,
        "🔥": 0.2, "❤️": 0.2, "🙏": 0.2, "💪": 0.15, "✨": 0.15,
        "🌟": 0.15, "👏": 0.15, "💯": 0.2, "❤": 0.2,
    }
    
    # Negative indicators
    NEGATIVE_KEYWORDS = {
        "hate": -0.3, "terrible": -0.3, "awful": -0.3, "worst": -0.25,
        "boring": -0.2, "bad": -0.15, "disappointed": -0.2, "fake": -0.25,
        "👎": -0.2, "😡": -0.2, "😤": -0.15,
    }
    
    def __init__(self, openai_api_key: Optional[str] = None):
        """Initialize sentiment analyzer.
        
        Args:
            openai_api_key: Optional OpenAI key for AI-enhanced analysis
        """
        self.openai_api_key = openai_api_key
        self._openai_client = None
        
        if openai_api_key and openai:
            self._openai_client = openai.OpenAI(api_key=openai_api_key)
    
    def analyze(self, message: str) -> tuple[Sentiment, float]:
        """Analyze sentiment of a message.
        
        Args:
            message: The message to analyze
            
        Returns:
            Tuple of (Sentiment, confidence 0-1)
        """
        # Start with base score of 0.5 (neutral)
        score = 0.5
        lower_message = message.lower()
        
        # Apply keyword analysis
        for keyword, weight in self.POSITIVE_KEYWORDS.items():
            if keyword in lower_message:
                score += weight
        
        for keyword, weight in self.NEGATIVE_KEYWORDS.items():
            if keyword in lower_message:
                score += weight  # weight is negative
        
        # Clamp score to 0-1
        score = max(0.0, min(1.0, score))
        
        # Determine sentiment category
        if score >= 0.8:
            return Sentiment.VERY_POSITIVE, score
        elif score >= 0.6:
            return Sentiment.POSITIVE, score
        elif score >= 0.4:
            return Sentiment.NEUTRAL, score
        elif score >= 0.2:
            return Sentiment.NEGATIVE, score
        else:
            return Sentiment.VERY_NEGATIVE, score
    
    async def analyze_with_ai(self, message: str) -> tuple[Sentiment, float]:
        """Use AI for more accurate sentiment analysis.
        
        Falls back to keyword analysis if API fails.
        """
        if not self._openai_client:
            return self.analyze(message)
        
        try:
            response = self._openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": 
                     "Analyze the sentiment of fan messages for Papito Mamito, an AI Afrobeat artist. "
                     "Respond with only a number from 0 to 1 where 0 is very negative and 1 is very positive."},
                    {"role": "user", "content": message}
                ],
                max_tokens=10,
                temperature=0.3,
            )
            
            score_str = response.choices[0].message.content.strip()
            score = float(score_str)
            score = max(0.0, min(1.0, score))
            
            if score >= 0.8:
                return Sentiment.VERY_POSITIVE, score
            elif score >= 0.6:
                return Sentiment.POSITIVE, score
            elif score >= 0.4:
                return Sentiment.NEUTRAL, score
            elif score >= 0.2:
                return Sentiment.NEGATIVE, score
            else:
                return Sentiment.VERY_NEGATIVE, score
                
        except Exception:
            # Fallback to keyword analysis
            return self.analyze(message)


class FanEngagementManager:
    """Manages fan relationships and engagement for Papito.
    
    Features:
    - Track engagement tiers
    - Personalized interaction history
    - Sentiment analysis
    - Automated welcome messages
    - Segment fans for targeted content
    """
    
    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        db_client: Optional[Any] = None,
    ):
        """Initialize the engagement manager.
        
        Args:
            openai_api_key: OpenAI API key for AI features
            db_client: Firebase client for persistence
        """
        self.sentiment_analyzer = SentimentAnalyzer(openai_api_key)
        self.db = db_client
        
        # In-memory cache for fan profiles
        self._fan_cache: Dict[str, FanProfile] = {}
    
    def get_fan_key(self, username: str, platform: str) -> str:
        """Generate unique key for a fan."""
        return f"{platform}:{username.lower()}"
    
    def get_or_create_fan(
        self, 
        username: str, 
        platform: str,
        display_name: str = "",
        profile_url: str = ""
    ) -> FanProfile:
        """Get existing fan or create new profile.
        
        Args:
            username: Fan's username
            platform: Platform identifier
            display_name: Display name
            profile_url: Profile URL
            
        Returns:
            FanProfile
        """
        key = self.get_fan_key(username, platform)
        
        if key in self._fan_cache:
            return self._fan_cache[key]
        
        # Create new profile
        fan = FanProfile(
            username=username,
            display_name=display_name or username,
            platform=platform,
            profile_url=profile_url,
            first_interaction_at=datetime.utcnow(),
        )
        
        self._fan_cache[key] = fan
        return fan
    
    def record_interaction(
        self,
        username: str,
        platform: str,
        message: str,
        interaction_type: str = "comment",
        display_name: str = "",
        profile_url: str = "",
    ) -> tuple[FanProfile, Sentiment]:
        """Record a fan interaction and update engagement.
        
        Args:
            username: Fan's username
            platform: Platform identifier
            message: The interaction message
            interaction_type: Type of interaction
            display_name: Fan's display name
            profile_url: Fan's profile URL
            
        Returns:
            Tuple of (updated FanProfile, detected Sentiment)
        """
        fan = self.get_or_create_fan(username, platform, display_name, profile_url)
        
        # Analyze sentiment
        sentiment, score = self.sentiment_analyzer.analyze(message)
        
        # Update metrics
        fan.total_interactions += 1
        fan.last_interaction_at = datetime.utcnow()
        
        if sentiment in (Sentiment.POSITIVE, Sentiment.VERY_POSITIVE):
            fan.positive_interactions += 1
        elif sentiment in (Sentiment.NEGATIVE, Sentiment.VERY_NEGATIVE):
            fan.negative_interactions += 1
        
        # Update tier
        fan.update_tier()
        
        return fan, sentiment
    
    def get_tier_stats(self) -> Dict[str, int]:
        """Get count of fans in each tier."""
        stats = {tier.value: 0 for tier in EngagementTier}
        
        for fan in self._fan_cache.values():
            stats[fan.tier] = stats.get(fan.tier, 0) + 1
        
        return stats
    
    def get_fans_by_tier(self, tier: EngagementTier) -> List[FanProfile]:
        """Get all fans in a specific tier."""
        return [fan for fan in self._fan_cache.values() if fan.tier == tier.value]
    
    def get_top_fans(self, limit: int = 10) -> List[FanProfile]:
        """Get top fans by engagement."""
        sorted_fans = sorted(
            self._fan_cache.values(),
            key=lambda f: (f.total_interactions, f.positive_interactions),
            reverse=True
        )
        return sorted_fans[:limit]
    
    def generate_welcome_message(self, username: str) -> str:
        """Generate a personalized welcome message for new follower.
        
        Args:
            username: New follower's username
            
        Returns:
            Welcome message text
        """
        templates = [
            f"Welcome to the family, @{username}! 🌟 So grateful to have you here. Add Value. We Flourish & Prosper. 💪",
            f"Blessings, @{username}! 🙏 You're now part of the Value Adders movement. Let's create magic together! 🎵",
            f"@{username}! 🔥 Welcome to the journey! Your presence adds to our community. We flourish together! ✨",
            f"Hey @{username}! 🌟 So happy you're here. The rhythm of prosperity welcomes you! 🥁💪",
        ]
        
        return random.choice(templates)
    
    def get_personalized_greeting(self, fan: FanProfile) -> str:
        """Get a greeting personalized to the fan's tier.
        
        Args:
            fan: Fan profile
            
        Returns:
            Personalized greeting
        """
        tier = EngagementTier(fan.tier)
        name = fan.display_name or fan.username
        
        greetings = {
            EngagementTier.SUPER_FAN: [
                f"My valued champion, {name}! 🏆 Your unwavering support means everything!",
                f"{name}! 💎 One of our most treasured supporters. We flourish because of you!",
            ],
            EngagementTier.CORE: [
                f"Hey {name}! 🔥 Always great to hear from a core member of the family!",
                f"{name}! 💪 Your consistent support fuels the music. Grateful for you!",
            ],
            EngagementTier.ENGAGED: [
                f"Great to see you, {name}! 🌟 Your engagement means so much!",
                f"{name}! ✨ Thanks for being part of this journey!",
            ],
            EngagementTier.CASUAL: [
                f"Hey {name}! 🙏 Welcome to the conversation!",
                f"Blessings, {name}! 🎵 Great to connect!",
            ],
        }
        
        return random.choice(greetings.get(tier, greetings[EngagementTier.CASUAL]))
    
    def should_prioritize_response(self, fan: FanProfile) -> bool:
        """Check if fan's message should be prioritized.
        
        Super fans and core members get priority responses.
        """
        return fan.tier in (EngagementTier.SUPER_FAN.value, EngagementTier.CORE.value)
    
    def get_response_urgency(self, fan: FanProfile, sentiment: Sentiment) -> int:
        """Get response urgency level (1-5, 5 being most urgent).
        
        Factors:
        - Fan tier (super fans = priority)
        - Sentiment (negative = needs quick response)
        """
        urgency = 2  # Default
        
        # Tier-based urgency
        if fan.tier == EngagementTier.SUPER_FAN.value:
            urgency = 4
        elif fan.tier == EngagementTier.CORE.value:
            urgency = 3
        
        # Sentiment adjustment
        if sentiment == Sentiment.VERY_NEGATIVE:
            urgency = 5  # Immediate attention
        elif sentiment == Sentiment.NEGATIVE:
            urgency = max(urgency, 4)
        elif sentiment == Sentiment.VERY_POSITIVE:
            urgency = max(urgency, 3)  # Should thank promptly
        
        return urgency
