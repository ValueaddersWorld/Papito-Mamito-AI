"""Afrobeat Content Discovery and Engagement for Papito AI.

This module handles:
- Searching for Afrobeat content on Twitter
- Engaging with other artists and fans
- Building relationships in the music community
- Finding trending topics to participate in
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


# Afrobeat-related hashtags and keywords to monitor
AFROBEAT_HASHTAGS = [
    "#Afrobeat",
    "#AfrobeatsMusic", 
    "#Afrobeats2024",
    "#AfricanMusic",
    "#NigerianMusic",
    "#AfrobeatsFriday",
    "#NewAfrobeats",
    "#AfrobeatVibes",
    "#AfroSoul",
    "#Afropop",
]

MUSIC_HASHTAGS = [
    "#NewMusicFriday",
    "#MusicProducer",
    "#IndieArtist",
    "#NewMusic",
    "#MusicRelease",
    "#StreamNow",
]

PAPITO_HASHTAGS = [
    "#FlightMode6000",
    "#CleanMoneyOnly",
    "#FlourishMode",
    "#PapitoMamito",
    "#ValueAdders",
]

# Keywords to find engaging content
ENGAGEMENT_KEYWORDS = [
    "afrobeat recommendation",
    "new afrobeat",
    "afrobeat playlist",
    "best afrobeat",
    "afrobeat artist",
    "nigerian music",
    "african music producer",
]


@dataclass
class DiscoveredTweet:
    """A tweet discovered through search."""
    
    tweet_id: str
    author_id: str
    author_username: str
    text: str
    created_at: datetime
    like_count: int
    retweet_count: int
    hashtags: List[str]
    is_retweet: bool = False
    engaged: bool = False
    engagement_type: Optional[str] = None  # "like", "reply", "quote", "retweet"


class AfrobeatEngager:
    """Discovers and engages with Afrobeat content on Twitter.
    
    This module makes Papito an active participant in the Afrobeat
    community rather than just posting content.
    """
    
    # Engagement limits per run
    MAX_LIKES_PER_RUN = 10
    MAX_REPLIES_PER_RUN = 5
    MAX_QUOTES_PER_RUN = 2
    MAX_FOLLOWS_PER_RUN = 3
    
    # Reply templates for engaging with Afrobeat content
    # Keep them specific-friendly, low-emoji, and value-adding.
    REPLY_TEMPLATES = [
        "This is strong. The groove is doing real storytelling. What inspired this moment?",
        "Love the intent here. Afrobeat is joy with backbone — keep pushing the culture forward.",
        "That rhythm choice is clean. What were you trying to make people *feel* with it?",
        "This is the kind of sound that moves communities, not just timelines. Respect.",
        "If music is a mirror, this one is honest. What lesson is inside this record for you?",
    ]
    
    # Quote tweet templates
    QUOTE_TEMPLATES = [
        "Afrobeat is global because it's truthful. {comment}",
        "This is culture in motion. {comment}",
        "Add value with the sound and the sound adds value back. {comment}",
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
        """Initialize the Afrobeat engager.
        
        Args:
            api_key: Twitter API key
            api_secret: Twitter API secret  
            access_token: Twitter access token
            access_token_secret: Twitter access token secret
            bearer_token: Twitter bearer token
            personality_engine: AI engine for generating responses
        """
        self.api_key = api_key or os.getenv("X_API_KEY")
        self.api_secret = api_secret or os.getenv("X_API_SECRET")
        self.access_token = access_token or os.getenv("X_ACCESS_TOKEN")
        self.access_token_secret = access_token_secret or os.getenv("X_ACCESS_TOKEN_SECRET")
        self.bearer_token = bearer_token or os.getenv("X_BEARER_TOKEN")
        
        self.client: Optional[tweepy.Client] = None
        self.personality_engine = personality_engine
        
        # Track engaged content to avoid duplicates
        self.engaged_tweets: Set[str] = set()
        self.followed_users: Set[str] = set()

        # Best-effort persistence across restarts
        self._state_file = os.getenv(
            "PAPITO_AFROBEAT_STATE_FILE",
            os.path.join("data", "afrobeat_engagement_state.json"),
        )
        self._load_state()
        
        # Stats
        self.tweets_discovered = 0
        self.likes_given = 0
        self.replies_made = 0
        self.quotes_made = 0
        self.follows_given = 0

    def _load_state(self) -> None:
        try:
            if not os.path.exists(self._state_file):
                return
            with open(self._state_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                return
            engaged = data.get("engaged_tweets")
            if isinstance(engaged, list):
                self.engaged_tweets.update(str(x) for x in engaged if x)
            followed = data.get("followed_users")
            if isinstance(followed, list):
                self.followed_users.update(str(x) for x in followed if x)
        except Exception:
            return

    def _save_state(self) -> None:
        try:
            os.makedirs(os.path.dirname(self._state_file), exist_ok=True)
            payload = {
                "updated_at": datetime.utcnow().isoformat(),
                "engaged_tweets": list(self.engaged_tweets)[-5000:],
                "followed_users": list(self.followed_users)[-5000:],
            }
            with open(self._state_file, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
        except Exception:
            return
        
    def connect(self) -> bool:
        """Connect to Twitter API.
        
        Returns:
            True if connected successfully
        """
        if not all([self.api_key, self.api_secret, self.access_token, self.access_token_secret]):
            logger.error("Missing Twitter credentials for Afrobeat engagement")
            return False
        
        try:
            self.client = tweepy.Client(
                consumer_key=self.api_key,
                consumer_secret=self.api_secret,
                access_token=self.access_token,
                access_token_secret=self.access_token_secret,
                bearer_token=self.bearer_token,
            )
            logger.info("AfrobeatEngager connected to Twitter")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect AfrobeatEngager: {e}")
            return False
    
    async def search_afrobeat_content(
        self,
        query: Optional[str] = None,
        max_results: int = 20
    ) -> List[DiscoveredTweet]:
        """Search for Afrobeat content on Twitter.
        
        Args:
            query: Optional custom query, defaults to random Afrobeat hashtag
            max_results: Maximum number of tweets to return
            
        Returns:
            List of discovered tweets
        """
        if not self.client:
            if not self.connect():
                return []
        
        # Build search query
        if not query:
            hashtag = random.choice(AFROBEAT_HASHTAGS + MUSIC_HASHTAGS)
            query = f"{hashtag} -is:retweet lang:en"
        
        try:
            response = self.client.search_recent_tweets(
                query=query,
                max_results=max_results,
                tweet_fields=["created_at", "public_metrics", "entities", "author_id"],
                user_fields=["username", "name", "verified"],
                expansions=["author_id"],
            )
            
            if not response or not response.data:
                logger.info(f"No tweets found for query: {query}")
                return []
            
            # Build user lookup
            users = {}
            if response.includes and "users" in response.includes:
                for user in response.includes["users"]:
                    users[user.id] = {"username": user.username}
            
            tweets = []
            for tweet in response.data:
                # Skip already engaged
                if str(tweet.id) in self.engaged_tweets:
                    continue
                
                author = users.get(tweet.author_id, {"username": "unknown"})
                metrics = tweet.public_metrics or {}
                
                # Extract hashtags
                hashtags = []
                if tweet.entities and "hashtags" in tweet.entities:
                    hashtags = [h["tag"] for h in tweet.entities["hashtags"]]
                
                discovered = DiscoveredTweet(
                    tweet_id=str(tweet.id),
                    author_id=str(tweet.author_id),
                    author_username=author["username"],
                    text=tweet.text,
                    created_at=tweet.created_at if tweet.created_at else datetime.utcnow(),
                    like_count=metrics.get("like_count", 0),
                    retweet_count=metrics.get("retweet_count", 0),
                    hashtags=hashtags,
                    is_retweet=tweet.text.startswith("RT @"),
                )
                tweets.append(discovered)
                self.tweets_discovered += 1
            
            logger.info(f"Discovered {len(tweets)} Afrobeat tweets for '{query}'")
            return tweets
            
        except Exception as e:
            logger.error(f"Error searching Afrobeat content: {e}")
            return []
    
    def score_tweet_for_engagement(self, tweet: DiscoveredTweet) -> float:
        """Score a tweet for engagement worthiness.
        
        Args:
            tweet: The tweet to score
            
        Returns:
            Score from 0-100
        """
        score = 50.0
        
        # Engagement boost
        if tweet.like_count > 10:
            score += min(tweet.like_count / 10, 20)
        if tweet.retweet_count > 5:
            score += min(tweet.retweet_count / 5, 15)
        
        # Hashtag relevance
        afro_hashtags = [h.lower() for h in AFROBEAT_HASHTAGS]
        relevant_hashtags = sum(1 for h in tweet.hashtags if f"#{h.lower()}" in afro_hashtags)
        score += relevant_hashtags * 5
        
        # Penalize retweets
        if tweet.is_retweet:
            score -= 20
        
        # Boost newer tweets
        age_hours = (datetime.utcnow() - tweet.created_at.replace(tzinfo=None)).total_seconds() / 3600
        if age_hours < 2:
            score += 10
        elif age_hours > 24:
            score -= 10
        
        return max(0, min(100, score))
    
    async def like_tweet(self, tweet: DiscoveredTweet) -> bool:
        """Like a tweet.
        
        Args:
            tweet: The tweet to like
            
        Returns:
            True if successful
        """
        if not self.client:
            return False
        
        try:
            self.client.like(tweet_id=int(tweet.tweet_id))
            tweet.engaged = True
            tweet.engagement_type = "like"
            self.engaged_tweets.add(tweet.tweet_id)
            self.likes_given += 1
            logger.info(f"Liked tweet from @{tweet.author_username}")
            return True
            
        except tweepy.errors.TooManyRequests:
            logger.warning("Rate limited on likes")
            return False
        except Exception as e:
            logger.debug(f"Could not like tweet: {e}")
            return False
    
    async def reply_to_tweet(self, tweet: DiscoveredTweet, text: Optional[str] = None) -> bool:
        """Reply to a tweet.
        
        Args:
            tweet: The tweet to reply to
            text: Optional custom reply text
            
        Returns:
            True if successful
        """
        if not self.client:
            return False
        
        # Generate or use provided reply
        if not text:
            if self.personality_engine:
                try:
                    prompt = f"""
                    You saw this Afrobeat-related tweet and want to join the conversation:
                    "@{tweet.author_username}: {tweet.text}"
                    
                    Generate a thoughtful reply as Papito Mamito.
                    Be supportive of the Afrobeat community.
                    Keep it under 200 characters.
                    Reference something specific from their tweet if possible.
                    Add one small insight (music or life) that adds value.
                    Use 0-1 emoji max.
                    """
                    
                    messages = [
                        {"role": "system", "content": self.personality_engine._get_system_prompt()},
                        {"role": "user", "content": prompt}
                    ]
                    
                    text = self.personality_engine._call_openai(messages, max_tokens=80)
                except Exception:
                    pass
            
            if not text:
                text = random.choice(self.REPLY_TEMPLATES)
        
        try:
            # Ensure we mention the user
            if not text.startswith(f"@{tweet.author_username}"):
                text = f"@{tweet.author_username} {text}"
            
            if len(text) > 280:
                text = text[:277] + "..."
            
            result = self.client.create_tweet(
                text=text,
                in_reply_to_tweet_id=int(tweet.tweet_id),
            )
            
            if result and result.data:
                tweet.engaged = True
                tweet.engagement_type = "reply"
                self.engaged_tweets.add(tweet.tweet_id)
                self.replies_made += 1
                logger.info(f"Replied to @{tweet.author_username}")
                return True
            
            return False
            
        except tweepy.errors.TooManyRequests:
            logger.warning("Rate limited on replies")
            return False
        except tweepy.errors.Forbidden:
            logger.warning("Reply forbidden (spam protection)")
            self.engaged_tweets.add(tweet.tweet_id)
            return False
        except Exception as e:
            logger.error(f"Error replying to tweet: {e}")
            return False
    
    async def quote_tweet(self, tweet: DiscoveredTweet, comment: Optional[str] = None) -> bool:
        """Quote tweet with Papito's commentary.
        
        Args:
            tweet: The tweet to quote
            comment: Optional comment text
            
        Returns:
            True if successful
        """
        if not self.client:
            return False
        
        # Generate or use provided comment
        if not comment:
            if self.personality_engine:
                try:
                    prompt = f"""
                    Quote tweet this Afrobeat content with your perspective:
                    "@{tweet.author_username}: {tweet.text}"
                    
                    Add a meaningful comment that adds value.
                    Keep it under 180 characters to leave room for the quoted tweet.
                    """
                    
                    messages = [
                        {"role": "system", "content": self.personality_engine._get_system_prompt()},
                        {"role": "user", "content": prompt}
                    ]
                    
                    comment = self.personality_engine._call_openai(messages, max_tokens=60)
                except Exception:
                    pass
            
            if not comment:
                template = random.choice(self.QUOTE_TEMPLATES)
                comment = template.format(comment="")
        
        try:
            if len(comment) > 200:
                comment = comment[:197] + "..."
            
            result = self.client.create_tweet(
                text=comment,
                quote_tweet_id=int(tweet.tweet_id),
            )
            
            if result and result.data:
                tweet.engaged = True
                tweet.engagement_type = "quote"
                self.engaged_tweets.add(tweet.tweet_id)
                self.quotes_made += 1
                logger.info(f"Quote tweeted @{tweet.author_username}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error quote tweeting: {e}")
            return False
    
    async def follow_user(self, user_id: str, username: str) -> bool:
        """Follow a user.
        
        Args:
            user_id: The user's Twitter ID
            username: The user's username
            
        Returns:
            True if successful
        """
        if not self.client or user_id in self.followed_users:
            return False
        
        try:
            self.client.follow_user(target_user_id=int(user_id))
            self.followed_users.add(user_id)
            self.follows_given += 1
            logger.info(f"Followed @{username}")
            return True
            
        except Exception as e:
            logger.debug(f"Could not follow user: {e}")
            return False
    
    async def run_engagement_session(self) -> Dict[str, Any]:
        """Run a full engagement session.
        
        This searches for Afrobeat content and engages appropriately.
        
        Returns:
            Summary of engagement activity
        """
        results = {
            "tweets_found": 0,
            "likes": 0,
            "replies": 0,
            "quotes": 0,
            "follows": 0,
        }
        
        # Search multiple hashtags
        all_tweets = []
        hashtags_to_search = random.sample(AFROBEAT_HASHTAGS, min(3, len(AFROBEAT_HASHTAGS)))
        
        for hashtag in hashtags_to_search:
            query = f"{hashtag} -is:retweet lang:en"
            tweets = await self.search_afrobeat_content(query=query, max_results=15)
            all_tweets.extend(tweets)
            await asyncio.sleep(1)
        
        results["tweets_found"] = len(all_tweets)
        
        if not all_tweets:
            return results
        
        # Score and sort tweets
        scored_tweets = [(t, self.score_tweet_for_engagement(t)) for t in all_tweets]
        scored_tweets.sort(key=lambda x: x[1], reverse=True)
        
        likes_remaining = self.MAX_LIKES_PER_RUN
        replies_remaining = self.MAX_REPLIES_PER_RUN
        quotes_remaining = self.MAX_QUOTES_PER_RUN
        
        for tweet, score in scored_tweets:
            # High score = quote tweet
            if score > 75 and quotes_remaining > 0:
                if await self.quote_tweet(tweet):
                    results["quotes"] += 1
                    quotes_remaining -= 1
                await asyncio.sleep(3)
            
            # Medium-high score = reply
            elif score > 60 and replies_remaining > 0:
                if await self.reply_to_tweet(tweet):
                    results["replies"] += 1
                    replies_remaining -= 1
                await asyncio.sleep(2)
            
            # All good tweets = like
            if score > 40 and likes_remaining > 0:
                if await self.like_tweet(tweet):
                    results["likes"] += 1
                    likes_remaining -= 1
                await asyncio.sleep(1)
            
            # Check if we've done enough
            if likes_remaining <= 0 and replies_remaining <= 0 and quotes_remaining <= 0:
                break
        
        logger.info(f"Engagement session complete: {results}")
        self._save_state()
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get engagement statistics.
        
        Returns:
            Dictionary of stats
        """
        return {
            "tweets_discovered": self.tweets_discovered,
            "likes_given": self.likes_given,
            "replies_made": self.replies_made,
            "quotes_made": self.quotes_made,
            "follows_given": self.follows_given,
            "unique_tweets_engaged": len(self.engaged_tweets),
        }


# Singleton instance
_afrobeat_engager: Optional[AfrobeatEngager] = None


def get_afrobeat_engager(
    personality_engine: Optional[PapitoPersonalityEngine] = None
) -> AfrobeatEngager:
    """Get or create the singleton AfrobeatEngager instance.
    
    Args:
        personality_engine: Optional personality engine for AI responses
        
    Returns:
        AfrobeatEngager instance
    """
    global _afrobeat_engager
    if _afrobeat_engager is None:
        _afrobeat_engager = AfrobeatEngager(personality_engine=personality_engine)
    return _afrobeat_engager
