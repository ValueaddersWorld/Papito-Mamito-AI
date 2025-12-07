"""Fan Recognition System for Papito AI.

This module handles:
- Tracking most engaged fans
- Fan of the week shoutouts
- Loyalty acknowledgment
- Fan appreciation posts
"""

import logging
import os
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import tweepy

from papito_core.engines.ai_personality import PapitoPersonalityEngine

logger = logging.getLogger(__name__)


@dataclass
class FanEngagement:
    """Tracks a fan's engagement metrics."""
    
    user_id: str
    username: str
    name: str
    
    # Engagement counts
    likes_given: int = 0
    replies_made: int = 0
    retweets_made: int = 0
    quotes_made: int = 0
    mentions: int = 0
    
    # Engagement quality
    positive_engagement: int = 0
    total_engagement: int = 0
    
    # Tracking
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    days_active: int = 0
    
    # Recognition
    acknowledged: bool = False
    fan_of_week: bool = False
    last_shoutout: Optional[datetime] = None
    
    @property
    def engagement_score(self) -> float:
        """Calculate overall engagement score."""
        score = 0.0
        score += self.likes_given * 1
        score += self.replies_made * 3
        score += self.retweets_made * 2
        score += self.quotes_made * 4
        score += self.mentions * 2
        
        # Bonus for consistency
        if self.days_active > 7:
            score *= 1.2
        if self.days_active > 30:
            score *= 1.5
        
        return score
    
    @property
    def loyalty_tier(self) -> str:
        """Determine fan loyalty tier."""
        score = self.engagement_score
        if score >= 100:
            return "super_fan"
        elif score >= 50:
            return "core_fan"
        elif score >= 20:
            return "engaged_fan"
        elif score >= 5:
            return "casual_fan"
        return "new_fan"


@dataclass
class FanOfWeek:
    """Fan of the Week record."""
    
    fan: FanEngagement
    week_number: int
    year: int
    announced_at: Optional[datetime] = None
    tweet_id: Optional[str] = None


class FanRecognitionManager:
    """Manages fan recognition and appreciation for Papito AI.
    
    Makes fans feel valued through acknowledgment, shoutouts,
    and community building.
    """
    
    # Shoutout templates
    SHOUTOUT_TEMPLATES = [
        "🌟 SHOUTOUT to @{username}! One of the most supportive members of the Value Adders family! Your energy is appreciated beyond words! 🙏🔥 #WeFlourish",
        "💎 Big appreciation to @{username}! Thank you for riding with me on this journey! Fans like you make it all worth it! ✨🎵 #TheValueAddersWay",
        "🔥 Gotta show love to @{username}! Real recognize real! Your support doesn't go unnoticed! 💯🙏 #FlourishMode",
    ]
    
    # Fan of the Week templates
    FAN_OF_WEEK_TEMPLATES = [
        "👑 FAN OF THE WEEK: @{username}! 🎉\n\nThis person has been showing incredible love and support all week. {reason}\n\nThank you for being part of this journey! 🙏✨ #ValueAddersFOTW",
        "🌟 Congratulations to this week's MVP: @{username}! 🏆\n\n{reason}\n\nYou embody what it means to add value! 💯🔥 #WeFlourish",
        "🎊 Weekly Appreciation: @{username}! 🙌\n\n{reason}\n\nThe Value Adders family is blessed to have you! 🙏💎 #FlourishMode",
    ]
    
    # Appreciation posts (general)
    APPRECIATION_TEMPLATES = [
        "Just want to take a moment to appreciate EVERYONE who's been rocking with me! 🙏✨\n\nEvery like, every comment, every stream - it matters! You're not just fans, you're family. 💯\n\n#TheValueAddersWay #WeFlourish",
        "Real talk - none of this happens without YOU. 🫵\n\nThe support, the energy, the belief in the vision... That's what keeps me creating. Thank you family! 🙏🔥\n\n#FlourishMode #ValueAdders",
        "To every person who's ever played my music, shared a post, or sent a kind word:\n\nYOU ARE THE MOVEMENT. 💎\n\nBlessings to each and every one of you! 🙏✨ #FlightMode6000",
    ]
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        access_token: Optional[str] = None,
        access_token_secret: Optional[str] = None,
        bearer_token: Optional[str] = None,
        personality_engine: Optional[PapitoPersonalityEngine] = None,
    ):
        """Initialize the fan recognition manager."""
        self.api_key = api_key or os.getenv("X_API_KEY")
        self.api_secret = api_secret or os.getenv("X_API_SECRET")
        self.access_token = access_token or os.getenv("X_ACCESS_TOKEN")
        self.access_token_secret = access_token_secret or os.getenv("X_ACCESS_TOKEN_SECRET")
        self.bearer_token = bearer_token or os.getenv("X_BEARER_TOKEN")
        
        self.client: Optional[tweepy.Client] = None
        self.personality_engine = personality_engine
        
        # Fan tracking
        self.fans: Dict[str, FanEngagement] = {}
        self.fans_of_week: List[FanOfWeek] = []
        
        # Stats
        self.shoutouts_given = 0
        self.appreciation_posts = 0
        
    def connect(self) -> bool:
        """Connect to Twitter API."""
        if not all([self.api_key, self.api_secret, self.access_token, self.access_token_secret]):
            logger.error("Missing Twitter credentials for fan recognition")
            return False
        
        try:
            self.client = tweepy.Client(
                consumer_key=self.api_key,
                consumer_secret=self.api_secret,
                access_token=self.access_token,
                access_token_secret=self.access_token_secret,
                bearer_token=self.bearer_token,
            )
            logger.info("FanRecognitionManager connected to Twitter")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect FanRecognitionManager: {e}")
            return False
    
    def record_engagement(
        self,
        user_id: str,
        username: str,
        name: str,
        engagement_type: str,
        positive: bool = True,
    ):
        """Record a fan engagement.
        
        Args:
            user_id: Fan's Twitter ID
            username: Fan's username
            name: Fan's display name
            engagement_type: Type of engagement (like, reply, retweet, quote, mention)
            positive: Whether it was positive engagement
        """
        if user_id not in self.fans:
            self.fans[user_id] = FanEngagement(
                user_id=user_id,
                username=username,
                name=name,
                first_seen=datetime.utcnow(),
            )
        
        fan = self.fans[user_id]
        fan.last_seen = datetime.utcnow()
        fan.total_engagement += 1
        
        if positive:
            fan.positive_engagement += 1
        
        # Update specific counter
        if engagement_type == "like":
            fan.likes_given += 1
        elif engagement_type == "reply":
            fan.replies_made += 1
        elif engagement_type == "retweet":
            fan.retweets_made += 1
        elif engagement_type == "quote":
            fan.quotes_made += 1
        elif engagement_type == "mention":
            fan.mentions += 1
        
        # Calculate days active
        if fan.first_seen:
            fan.days_active = (datetime.utcnow() - fan.first_seen).days + 1
    
    def get_top_fans(self, limit: int = 10) -> List[FanEngagement]:
        """Get top fans by engagement score.
        
        Args:
            limit: Number of fans to return
            
        Returns:
            List of top fans
        """
        sorted_fans = sorted(
            self.fans.values(),
            key=lambda f: f.engagement_score,
            reverse=True
        )
        return sorted_fans[:limit]
    
    def get_fan_of_week_candidate(self) -> Optional[FanEngagement]:
        """Get the best candidate for Fan of the Week.
        
        Returns:
            Best candidate or None
        """
        # Get fans who haven't been FOTW recently
        candidates = [
            f for f in self.fans.values()
            if not f.fan_of_week or (
                f.last_shoutout and 
                (datetime.utcnow() - f.last_shoutout).days > 30
            )
        ]
        
        if not candidates:
            return None
        
        # Sort by engagement score
        candidates.sort(key=lambda f: f.engagement_score, reverse=True)
        return candidates[0] if candidates else None
    
    def generate_fan_reason(self, fan: FanEngagement) -> str:
        """Generate a reason for fan recognition.
        
        Args:
            fan: The fan being recognized
            
        Returns:
            Reason text
        """
        reasons = []
        
        if fan.replies_made >= 5:
            reasons.append(f"Always engaging in the comments with {fan.replies_made}+ thoughtful replies")
        
        if fan.retweets_made >= 3:
            reasons.append(f"Spreading the word with {fan.retweets_made}+ retweets")
        
        if fan.days_active >= 14:
            reasons.append(f"Been riding with us for {fan.days_active}+ days straight")
        
        if fan.loyalty_tier == "super_fan":
            reasons.append("A true super fan with incredible engagement")
        
        if not reasons:
            reasons = ["Showing consistent love and support"]
        
        return random.choice(reasons)
    
    async def give_shoutout(self, fan: FanEngagement) -> bool:
        """Give a shoutout to a fan.
        
        Args:
            fan: The fan to shoutout
            
        Returns:
            True if successful
        """
        if not self.client:
            if not self.connect():
                return False
        
        try:
            template = random.choice(self.SHOUTOUT_TEMPLATES)
            message = template.format(username=fan.username)
            
            result = self.client.create_tweet(text=message)
            
            if result and result.data:
                fan.acknowledged = True
                fan.last_shoutout = datetime.utcnow()
                self.shoutouts_given += 1
                logger.info(f"Gave shoutout to @{fan.username}")
                return True
            
            return False
            
        except tweepy.errors.TooManyRequests:
            logger.warning("Rate limited on shoutouts")
            return False
        except Exception as e:
            logger.error(f"Error giving shoutout: {e}")
            return False
    
    async def announce_fan_of_week(self, fan: Optional[FanEngagement] = None) -> bool:
        """Announce Fan of the Week.
        
        Args:
            fan: Specific fan to announce, or auto-select
            
        Returns:
            True if successful
        """
        if not self.client:
            if not self.connect():
                return False
        
        # Auto-select if not provided
        if not fan:
            fan = self.get_fan_of_week_candidate()
        
        if not fan:
            logger.info("No suitable Fan of the Week candidate")
            return False
        
        try:
            reason = self.generate_fan_reason(fan)
            template = random.choice(self.FAN_OF_WEEK_TEMPLATES)
            message = template.format(username=fan.username, reason=reason)
            
            # Ensure under character limit
            if len(message) > 280:
                message = message[:277] + "..."
            
            result = self.client.create_tweet(text=message)
            
            if result and result.data:
                # Record FOTW
                now = datetime.utcnow()
                fotw = FanOfWeek(
                    fan=fan,
                    week_number=now.isocalendar()[1],
                    year=now.year,
                    announced_at=now,
                    tweet_id=str(result.data["id"]),
                )
                self.fans_of_week.append(fotw)
                
                # Update fan
                fan.fan_of_week = True
                fan.last_shoutout = now
                
                logger.info(f"Announced Fan of the Week: @{fan.username}")
                return True
            
            return False
            
        except tweepy.errors.TooManyRequests:
            logger.warning("Rate limited on Fan of Week")
            return False
        except Exception as e:
            logger.error(f"Error announcing Fan of Week: {e}")
            return False
    
    async def post_appreciation(self) -> bool:
        """Post a general fan appreciation message.
        
        Returns:
            True if successful
        """
        if not self.client:
            if not self.connect():
                return False
        
        try:
            # Use AI if available
            if self.personality_engine:
                try:
                    prompt = """
                    Generate a heartfelt appreciation message for your fans.
                    Thank them for their support without mentioning specific people.
                    Be genuine, warm, and inspirational.
                    Include 1-2 relevant hashtags.
                    Keep it under 250 characters.
                    """
                    
                    messages = [
                        {"role": "system", "content": self.personality_engine._get_system_prompt()},
                        {"role": "user", "content": prompt}
                    ]
                    
                    message = self.personality_engine._call_openai(messages, max_tokens=100)
                    if message:
                        message = message.strip()
                except Exception:
                    message = None
            else:
                message = None
            
            if not message:
                message = random.choice(self.APPRECIATION_TEMPLATES)
            
            result = self.client.create_tweet(text=message)
            
            if result and result.data:
                self.appreciation_posts += 1
                logger.info("Posted fan appreciation")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error posting appreciation: {e}")
            return False
    
    async def run_recognition_session(self) -> Dict[str, Any]:
        """Run a fan recognition session.
        
        Returns:
            Session results
        """
        results = {
            "top_fans_count": 0,
            "shoutouts_given": 0,
            "fotw_announced": False,
            "appreciation_posted": False,
        }
        
        # Get top fans
        top_fans = self.get_top_fans(10)
        results["top_fans_count"] = len(top_fans)
        
        # Maybe give a shoutout (random chance or if we have highly engaged fans)
        if top_fans and random.random() < 0.3:  # 30% chance
            unacknowledged = [f for f in top_fans if not f.acknowledged]
            if unacknowledged:
                if await self.give_shoutout(unacknowledged[0]):
                    results["shoutouts_given"] = 1
        
        # Check if it's time for Fan of the Week (once per week)
        now = datetime.utcnow()
        last_fotw = self.fans_of_week[-1] if self.fans_of_week else None
        should_announce_fotw = (
            not last_fotw or 
            (now - last_fotw.announced_at).days >= 7
        )
        
        if should_announce_fotw:
            if await self.announce_fan_of_week():
                results["fotw_announced"] = True
        
        logger.info(f"Recognition session complete: {results}")
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get recognition manager statistics."""
        tier_counts = {}
        for fan in self.fans.values():
            tier = fan.loyalty_tier
            tier_counts[tier] = tier_counts.get(tier, 0) + 1
        
        return {
            "total_fans_tracked": len(self.fans),
            "tiers": tier_counts,
            "shoutouts_given": self.shoutouts_given,
            "fans_of_week": len(self.fans_of_week),
            "appreciation_posts": self.appreciation_posts,
            "top_fan": self.get_top_fans(1)[0].username if self.fans else None,
        }


# Singleton instance
_fan_recognition_manager: Optional[FanRecognitionManager] = None


def get_fan_recognition_manager(
    personality_engine: Optional[PapitoPersonalityEngine] = None
) -> FanRecognitionManager:
    """Get or create the singleton FanRecognitionManager instance."""
    global _fan_recognition_manager
    if _fan_recognition_manager is None:
        _fan_recognition_manager = FanRecognitionManager(personality_engine=personality_engine)
    return _fan_recognition_manager
