"""New Follower Manager for Papito AI.

This module handles:
- Monitoring new followers
- Welcoming new followers
- Special acknowledgment for notable followers
- Follower milestones and celebrations
"""

import asyncio
import json
import logging
import os
import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set

import tweepy

from papito_core.engines.ai_personality import PapitoPersonalityEngine

logger = logging.getLogger(__name__)


@dataclass
class Follower:
    """Represents a Twitter follower."""
    
    user_id: str
    username: str
    name: str
    bio: str = ""
    followers_count: int = 0
    following_count: int = 0
    verified: bool = False
    profile_image_url: str = ""
    followed_at: Optional[datetime] = None
    welcomed: bool = False
    follow_back: bool = False
    notable: bool = False  # High profile or relevant account


class FollowerManager:
    """Manages new follower interactions for Papito AI.
    
    Creates a welcoming experience for new fans and builds
    community through acknowledgment and appreciation.
    """
    
    # Welcome message templates
    WELCOME_TEMPLATES = [
        "Welcome to the Value Adders family! 🙏✨ Glad to have you here. Get ready for good vibes, great music, and positive energy! 🎵 #WeFlourish",
        "Thank you for the follow! 🌟 You're now part of something special. Stay tuned for FLOURISH MODE! ✈️ #FlightMode6000",
        "Blessings! 🙏 Appreciate you joining the journey. Together we rise, together we add value! 💯 #TheValueAddersWay",
    ]
    
    # Welcome templates for notable followers (verified/high-profile)
    NOTABLE_WELCOME_TEMPLATES = [
        "Honored to have you here! 🙏 Your presence means a lot. Let's connect and create something amazing! ✨ 🔥",
        "Welcome! 🌟 Truly appreciate the follow. Would love to connect and share the mission of adding value! 💯",
        "Thank you for the support! 🙏 Looking forward to connecting with a fellow creator/influencer! Let's build! 🔥",
    ]
    
    # Milestone templates
    MILESTONE_TEMPLATES = {
        100: "🎉 100 FOLLOWERS! Thank you family! We just getting started! The Value Adders movement is growing! 🙏🔥 #FlourishMode",
        500: "🔥 500 STRONG! Half a thousand souls on this journey together! Blessings to every single one of you! 🙏✨ #TheValueAddersWay",
        1000: "🚀 1K FAMILY! We hit a milestone but we're just warming up! Thank you for believing in the vision! 💯🎵 #WeRise",
        5000: "🌟 5,000 VALUE ADDERS! This movement is real! Together we flourish, together we prosper! 🙏✈️ #FlightMode6000",
        10000: "👑 10K! Ten thousand dreamers, believers, value adders! This is just the beginning! Album coming soon! 🔥💎 #FlourishMode",
    }
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        access_token: Optional[str] = None,
        access_token_secret: Optional[str] = None,
        bearer_token: Optional[str] = None,
        personality_engine: Optional[PapitoPersonalityEngine] = None,
    ):
        """Initialize the follower manager."""
        self.api_key = api_key or os.getenv("X_API_KEY")
        self.api_secret = api_secret or os.getenv("X_API_SECRET")
        self.access_token = access_token or os.getenv("X_ACCESS_TOKEN")
        self.access_token_secret = access_token_secret or os.getenv("X_ACCESS_TOKEN_SECRET")
        self.bearer_token = bearer_token or os.getenv("X_BEARER_TOKEN")
        
        self.client: Optional[tweepy.Client] = None
        self.personality_engine = personality_engine
        self.user_id: Optional[str] = None
        
        # Track followers
        self.known_followers: Set[str] = set()
        self.new_followers: List[Follower] = []
        self.notable_followers: List[Follower] = []
        self.welcomed_followers: Set[str] = set()

        # Best-effort persistence across restarts
        self._state_file = os.getenv(
            "PAPITO_FOLLOWER_STATE_FILE",
            os.path.join("data", "follower_manager_state.json"),
        )
        self._load_state()
        
        # Stats
        self.current_follower_count = 0
        self.welcomes_sent = 0
        self.follow_backs = 0
        self.last_milestone = 0

    def _load_state(self) -> None:
        try:
            if not os.path.exists(self._state_file):
                return
            with open(self._state_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                return
            known = data.get("known_followers")
            if isinstance(known, list):
                self.known_followers.update(str(x) for x in known if x)
            welcomed = data.get("welcomed_followers")
            if isinstance(welcomed, list):
                self.welcomed_followers.update(str(x) for x in welcomed if x)
            last_m = data.get("last_milestone")
            if isinstance(last_m, int):
                self.last_milestone = last_m
        except Exception:
            return

    def _save_state(self) -> None:
        try:
            os.makedirs(os.path.dirname(self._state_file), exist_ok=True)
            payload = {
                "updated_at": datetime.utcnow().isoformat(),
                "known_followers": list(self.known_followers)[-10000:],
                "welcomed_followers": list(self.welcomed_followers)[-10000:],
                "last_milestone": int(self.last_milestone),
            }
            with open(self._state_file, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
        except Exception:
            return
        
    def connect(self) -> bool:
        """Connect to Twitter API."""
        if not all([self.api_key, self.api_secret, self.access_token, self.access_token_secret]):
            logger.error("Missing Twitter credentials for follower management")
            return False
        
        try:
            self.client = tweepy.Client(
                consumer_key=self.api_key,
                consumer_secret=self.api_secret,
                access_token=self.access_token,
                access_token_secret=self.access_token_secret,
                bearer_token=self.bearer_token,
            )
            
            # Get our user info
            me = self.client.get_me(user_fields=["public_metrics"])
            if me and me.data:
                self.user_id = me.data.id
                if me.data.public_metrics:
                    self.current_follower_count = me.data.public_metrics.get("followers_count", 0)
                logger.info(f"FollowerManager connected. Current followers: {self.current_follower_count}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to connect FollowerManager: {e}")
            return False
    
    def is_notable(self, follower: Follower) -> bool:
        """Check if a follower is notable (worth special attention).
        
        Args:
            follower: The follower to check
            
        Returns:
            True if notable
        """
        # Verified accounts
        if follower.verified:
            return True
        
        # High follower count
        if follower.followers_count > 5000:
            return True
        
        # Music/entertainment industry keywords in bio
        industry_keywords = ["artist", "producer", "dj", "musician", "singer", "rapper",
                           "label", "manager", "journalist", "blogger", "influencer",
                           "afrobeat", "nigerian music", "african music"]
        bio_lower = follower.bio.lower()
        if any(kw in bio_lower for kw in industry_keywords):
            return True
        
        return False
    
    async def fetch_recent_followers(self, max_results: int = 50) -> List[Follower]:
        """Fetch recent followers.
        
        Args:
            max_results: Maximum followers to fetch
            
        Returns:
            List of Follower objects
        """
        if not self.client or not self.user_id:
            if not self.connect():
                return []
        
        try:
            response = self.client.get_users_followers(
                id=self.user_id,
                max_results=max_results,
                user_fields=["description", "public_metrics", "verified", "profile_image_url"],
            )
            
            if not response or not response.data:
                return []
            
            followers = []
            for user in response.data:
                metrics = user.public_metrics or {}
                
                follower = Follower(
                    user_id=str(user.id),
                    username=user.username,
                    name=user.name,
                    bio=user.description or "",
                    followers_count=metrics.get("followers_count", 0),
                    following_count=metrics.get("following_count", 0),
                    verified=user.verified or False,
                    profile_image_url=user.profile_image_url or "",
                    followed_at=datetime.utcnow(),
                )
                
                # Check if notable
                follower.notable = self.is_notable(follower)
                
                # Check if already known/welcomed
                if follower.user_id not in self.known_followers:
                    self.new_followers.append(follower)
                    if follower.notable:
                        self.notable_followers.append(follower)
                
                followers.append(follower)
                self.known_followers.add(follower.user_id)
            
            logger.info(f"Fetched {len(followers)} followers, {len(self.new_followers)} new")
            return followers
            
        except Exception as e:
            logger.error(f"Error fetching followers: {e}")
            return []
    
    def generate_welcome_message(self, follower: Follower) -> str:
        """Generate a personalized welcome message.
        
        Args:
            follower: The follower to welcome
            
        Returns:
            Welcome message text
        """
        # Try AI generation for notable followers
        if follower.notable and self.personality_engine:
            try:
                prompt = f"""
                Generate a personalized welcome message for a new follower:
                
                Username: @{follower.username}
                Name: {follower.name}
                Bio: {follower.bio}
                Followers: {follower.followers_count}
                Verified: {follower.verified}
                
                This is a NOTABLE follower. Make the message feel special and personalized.
                Reference something from their bio if relevant.
                Keep it warm, authentic, and under 250 characters.
                Include their @username at the start.
                """
                
                messages = [
                    {"role": "system", "content": self.personality_engine._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ]
                
                response = self.personality_engine._call_openai(messages, max_tokens=80)
                if response:
                    # Ensure username is included
                    if not response.startswith(f"@{follower.username}"):
                        response = f"@{follower.username} {response}"
                    return response.strip()
                    
            except Exception as e:
                logger.error(f"AI welcome generation failed: {e}")
        
        # Use templates
        if follower.notable:
            template = random.choice(self.NOTABLE_WELCOME_TEMPLATES)
        else:
            template = random.choice(self.WELCOME_TEMPLATES)
        
        return f"@{follower.username} {template}"
    
    async def welcome_new_follower(self, follower: Follower) -> bool:
        """Welcome a new follower with a tweet.
        
        Args:
            follower: The follower to welcome
            
        Returns:
            True if welcome was sent
        """
        if not self.client:
            return False
        
        if follower.user_id in self.welcomed_followers:
            return False
        
        try:
            message = self.generate_welcome_message(follower)
            
            # Ensure under 280 characters
            if len(message) > 280:
                message = message[:277] + "..."
            
            result = self.client.create_tweet(text=message)
            
            if result and result.data:
                follower.welcomed = True
                self.welcomed_followers.add(follower.user_id)
                self.welcomes_sent += 1
                logger.info(f"Welcomed @{follower.username}")
                return True
            
            return False
            
        except tweepy.errors.TooManyRequests:
            logger.warning("Rate limited on welcome tweets")
            return False
        except tweepy.errors.Forbidden as e:
            if "duplicate" in str(e).lower():
                self.welcomed_followers.add(follower.user_id)
            return False
        except Exception as e:
            logger.error(f"Error welcoming follower: {e}")
            return False
    
    async def follow_back(self, follower: Follower) -> bool:
        """Follow back a follower.
        
        Args:
            follower: The follower to follow back
            
        Returns:
            True if followed
        """
        if not self.client or follower.follow_back:
            return False
        
        # Only follow back notable accounts or accounts with good ratio
        should_follow = (
            follower.notable or
            (follower.followers_count > 100 and follower.followers_count > follower.following_count * 0.3)
        )
        
        if not should_follow:
            return False
        
        try:
            self.client.follow_user(target_user_id=int(follower.user_id))
            follower.follow_back = True
            self.follow_backs += 1
            logger.info(f"Followed back @{follower.username}")
            return True
            
        except tweepy.errors.Forbidden:
            # Already following or protected
            return False
        except Exception as e:
            logger.debug(f"Could not follow back: {e}")
            return False
    
    async def check_milestone(self) -> Optional[str]:
        """Check if we've hit a follower milestone.
        
        Returns:
            Milestone tweet text if milestone reached, None otherwise
        """
        if not self.client:
            if not self.connect():
                return None
        
        # Get current follower count
        try:
            me = self.client.get_me(user_fields=["public_metrics"])
            if me and me.data and me.data.public_metrics:
                self.current_follower_count = me.data.public_metrics.get("followers_count", 0)
        except Exception:
            pass
        
        # Check milestones
        for threshold, message in sorted(self.MILESTONE_TEMPLATES.items()):
            if self.current_follower_count >= threshold > self.last_milestone:
                self.last_milestone = threshold
                return message
        
        return None
    
    async def post_milestone(self, message: str) -> bool:
        """Post a milestone celebration tweet.
        
        Args:
            message: The milestone message
            
        Returns:
            True if posted
        """
        if not self.client:
            return False
        
        try:
            result = self.client.create_tweet(text=message)
            if result and result.data:
                logger.info(f"Posted milestone: {message[:50]}...")
                return True
            return False
        except Exception as e:
            logger.error(f"Error posting milestone: {e}")
            return False
    
    async def run_welcome_session(self, max_welcomes: int = 5) -> Dict[str, Any]:
        """Run a full welcome session.
        
        Args:
            max_welcomes: Maximum welcomes to send
            
        Returns:
            Session results
        """
        results = {
            "new_followers_found": 0,
            "welcomes_sent": 0,
            "follow_backs": 0,
            "notable_followers": 0,
            "milestone_posted": False,
        }
        
        # Fetch recent followers
        await self.fetch_recent_followers()
        results["new_followers_found"] = len(self.new_followers)
        results["notable_followers"] = len(self.notable_followers)
        
        # Welcome new followers (prioritize notable)
        to_welcome = (
            self.notable_followers[:max_welcomes] + 
            [f for f in self.new_followers if not f.notable][:max_welcomes - len(self.notable_followers)]
        )[:max_welcomes]
        
        for follower in to_welcome:
            success = await self.welcome_new_follower(follower)
            if success:
                results["welcomes_sent"] += 1
            
            # Small delay
            await asyncio.sleep(3)
            
            # Maybe follow back
            if await self.follow_back(follower):
                results["follow_backs"] += 1
            
            await asyncio.sleep(2)
        
        # Check for milestone
        milestone = await self.check_milestone()
        if milestone:
            if await self.post_milestone(milestone):
                results["milestone_posted"] = True
        
        # Clear processed new followers
        self.new_followers = [f for f in self.new_followers if f.user_id not in self.welcomed_followers]
        self.notable_followers = [f for f in self.notable_followers if f.user_id not in self.welcomed_followers]
        
        logger.info(f"Welcome session complete: {results}")
        self._save_state()
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get follower manager statistics."""
        return {
            "current_followers": self.current_follower_count,
            "known_followers_tracked": len(self.known_followers),
            "new_followers_pending": len(self.new_followers),
            "notable_followers_pending": len(self.notable_followers),
            "welcomes_sent": self.welcomes_sent,
            "follow_backs": self.follow_backs,
            "last_milestone": self.last_milestone,
        }


# Singleton instance
_follower_manager: Optional[FollowerManager] = None


def get_follower_manager(
    personality_engine: Optional[PapitoPersonalityEngine] = None
) -> FollowerManager:
    """Get or create the singleton FollowerManager instance."""
    global _follower_manager
    if _follower_manager is None:
        _follower_manager = FollowerManager(personality_engine=personality_engine)
    return _follower_manager
