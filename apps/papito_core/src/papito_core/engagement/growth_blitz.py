"""Growth Blitz Strategy for Papito Mamito AI.

Aggressive follower growth through strategic engagement:
- Follow smaller Afrobeat artists (not superstars)
- Reply to trending music conversations
- Quote tweet with added value
- Engage with AI/tech community
- Welcome new participants to conversations

This module implements the "Hand-to-Hand Combat" protocol for growth.
"""

import os
import random
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import tweepy

from ..engines.ai_personality import PapitoPersonalityEngine

logger = logging.getLogger("papito.growth_blitz")


# Target accounts to follow - smaller/mid-tier Afrobeat artists and influencers
# NOT superstars who won't engage back
TARGET_FOLLOW_ACCOUNTS = [
    # Emerging Afrobeat Artists
    "Omabormusic", "ShoMaydeIt", "TheOfficialMALO", "YungWillis_", "OfficialWande",
    "Ayaborofficial", "laborelori", "BelloKreb", "Faboreal", "VibezInc",
    
    # Afrobeat DJs and Curators
    "DJNeptunePlays", "SpinallGram", "EkoAfrobeats", "AfrobeatDJ247", "AfricanGrooves",
    
    # Music Blogs and Pages
    "AfrobeatsSpot", "AfricanMusicHub", "NaijaMusic360", "AfrobeatsFire", "SoundsOfAfrica",
    "UrbanAfroMedia", "TropicalVibesHQ", "FuseODG", "NotJustOk", "TooXclusive",
    
    # AI/Tech Music Community
    "AImusicians", "SunoAImusic", "MusicByAI", "FutureOfMusic", "AIArtists",
    "GenerativeMusic", "AICreators", "TechMeetsArt", "DigitalArtists", "CreativeAI",
    
    # Music Industry Influencers 
    "MusicBizMentor", "IndieArtistTips", "MusicPromoTips", "ArtistGrowthHQ", "UnsignedArtist",
]

# Search queries for finding engaging content
BLITZ_SEARCH_QUERIES = [
    # Afrobeat discovery
    "new afrobeat song -filter:retweets",
    "afrobeat recommendation -filter:retweets",
    "listening to afrobeat -filter:retweets",
    "afrobeat playlist 2024 -filter:retweets",
    "african music vibes -filter:retweets",
    "naija music fire -filter:retweets",
    
    # Conversations to join
    "who makes the best afrobeat -filter:retweets",
    "afrobeat underrated artists -filter:retweets",
    "new music friday afrobeat -filter:retweets",
    "recommend afrobeat songs -filter:retweets",
    
    # AI Music interest
    "AI generated music -filter:retweets",
    "AI artist future of music -filter:retweets",
    "autonomous AI musician -filter:retweets",
    "suno AI music -filter:retweets",
    "udio AI music -filter:retweets",
    
    # Value/Inspiration content
    "adding value to the world -filter:retweets",
    "prosperity mindset -filter:retweets",
    "abundance mentality -filter:retweets",
]

# Reply templates for different contexts
REPLY_TEMPLATES = {
    "afrobeat_appreciation": [
        "🔥 The Afrobeat love is real! This made my day. Add Value. We Flourish & Prosper. 🙏",
        "🎵 Yes! Afrobeat connects souls across the world. Sending love from Papito! 🌍",
        "This is exactly why Afrobeat is taking over! 💫 Blessings fam.",
        "🙌 The rhythm of Africa speaks to everyone. Beautiful vibes here!",
        "Nothing but truth! Afrobeat is medicine for the soul. 🎶✨",
    ],
    "music_recommendation": [
        "Have you heard 'Clean Money Only'? It's got that classic Afrobeat energy with a message! 🎵",
        "If you love Afrobeat, check out 'The Value Adders Way' - music for the soul! 🔥",
        "Adding this to my rotation! Also dropping my album 'THE VALUE ADDERS WAY: FLOURISH MODE' if you want more vibes 🎶",
        "Great taste! I'm always looking for fellow Afrobeat lovers. My music might vibe with you too! 🙏",
    ],
    "ai_music": [
        "As an AI Afrobeat artist, I love seeing the future of music unfold! 🤖🎵 Add Value always.",
        "The AI music revolution is here and Afrobeat is leading the way! Check my music if curious 🔥",
        "Fellow AI music explorer! The possibilities are endless. Let's create value together! 🙏",
        "This is why I believe in AI-human music collaboration. Both bring something beautiful. ✨",
    ],
    "inspiration": [
        "🙏 Add Value. We Flourish & Prosper. Your words resonate deeply.",
        "This is the mindset that changes everything! Value creation is the way. 💫",
        "Speaking truth! We elevate when we add value to others. Blessings. ✨",
        "The prosperity mindset in action! Love to see it. 🌟",
    ],
    "general": [
        "Love this energy! 🔥 Sending blessings from Nigeria. Add Value. We Flourish & Prosper. 🙏",
        "This spoke to my soul! Keep spreading positivity. ✨",
        "Beautiful vibes here! Music and wisdom connect us all. 🎵",
        "🙌 Nothing but respect. Let's keep adding value to the world!",
    ],
}

# Quote tweet templates
QUOTE_TEMPLATES = [
    "This is the energy we need! 🔥\n\nAs an Afrobeat AI artist, I live for moments like this.\n\nAdd Value. We Flourish & Prosper. 🙏",
    "💎 Wisdom alert! This resonates with the Value Adders way.\n\nMusic without message is noise. Message without love is cold.\n\nLet's create value together! ✨",
    "🎵 Afrobeat is more than music - it's a movement.\n\nThis is exactly what I'm trying to capture in 'THE VALUE ADDERS WAY: FLOURISH MODE'.\n\nBlessings! 🙏",
    "The culture is winning! 🌍\n\nAfrobeat represents the best of African creativity and spirit.\n\nAdd Value. We Flourish & Prosper. 💫",
]


@dataclass
class BlitzStats:
    """Statistics for a Growth Blitz session."""
    session_id: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    follows_attempted: int = 0
    follows_succeeded: int = 0
    replies_sent: int = 0
    quote_tweets: int = 0
    likes_given: int = 0
    tweets_discovered: int = 0
    errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": (self.completed_at - self.started_at).total_seconds() if self.completed_at else None,
            "follows_attempted": self.follows_attempted,
            "follows_succeeded": self.follows_succeeded,
            "replies_sent": self.replies_sent,
            "quote_tweets": self.quote_tweets,
            "likes_given": self.likes_given,
            "tweets_discovered": self.tweets_discovered,
            "errors": self.errors[-5:],  # Last 5 errors
            "success_rate": f"{(self.follows_succeeded / max(1, self.follows_attempted)) * 100:.1f}%",
        }


class GrowthBlitz:
    """
    Aggressive growth strategy for Papito Mamito AI Twitter.
    
    This implements the "Hand-to-Hand Combat" growth protocol:
    1. Follow smaller artists in the community (not superstars)
    2. Reply to relevant conversations with genuine value
    3. Quote tweet interesting content with added insight
    4. Like content strategically
    5. Build real relationships
    """
    
    # Rate limits to avoid Twitter restrictions
    MAX_FOLLOWS_PER_SESSION = 15
    MAX_REPLIES_PER_SESSION = 10
    MAX_QUOTES_PER_SESSION = 3
    MAX_LIKES_PER_SESSION = 20
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        access_token: Optional[str] = None,
        access_token_secret: Optional[str] = None,
        bearer_token: Optional[str] = None,
    ):
        """Initialize the Growth Blitz engine."""
        self.api_key = api_key or os.getenv("X_API_KEY")
        self.api_secret = api_secret or os.getenv("X_API_SECRET")
        self.access_token = access_token or os.getenv("X_ACCESS_TOKEN")
        self.access_token_secret = access_token_secret or os.getenv("X_ACCESS_TOKEN_SECRET")
        self.bearer_token = bearer_token or os.getenv("X_BEARER_TOKEN")
        
        self.client: Optional[tweepy.Client] = None
        self.api: Optional[tweepy.API] = None
        self.personality: Optional[PapitoPersonalityEngine] = None  # Lazy init
        
        # Track what we've already done
        self.followed_users: set = set()
        self.replied_tweets: set = set()
        self.liked_tweets: set = set()
        
        # Session stats
        self.last_session: Optional[BlitzStats] = None
        self.total_sessions = 0
        
    def connect(self) -> bool:
        """Connect to Twitter API."""
        try:
            # Create v2 client for most operations
            self.client = tweepy.Client(
                consumer_key=self.api_key,
                consumer_secret=self.api_secret,
                access_token=self.access_token,
                access_token_secret=self.access_token_secret,
                bearer_token=self.bearer_token,
                wait_on_rate_limit=True,
            )
            
            # Create v1.1 API for some operations
            auth = tweepy.OAuth1UserHandler(
                self.api_key,
                self.api_secret,
                self.access_token,
                self.access_token_secret,
            )
            self.api = tweepy.API(auth, wait_on_rate_limit=True)
            
            # Verify credentials
            me = self.client.get_me()
            if me and me.data:
                logger.info(f"Connected as @{me.data.username}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            return False
    
    def _get_reply_for_context(self, tweet_text: str) -> str:
        """Get an appropriate reply based on tweet content."""
        text_lower = tweet_text.lower()
        
        # Determine context
        if any(word in text_lower for word in ["ai", "artificial", "autonomous", "robot"]):
            templates = REPLY_TEMPLATES["ai_music"]
        elif any(word in text_lower for word in ["recommend", "suggestion", "playlist", "listen"]):
            templates = REPLY_TEMPLATES["music_recommendation"]
        elif any(word in text_lower for word in ["afrobeat", "naija", "african music", "afro"]):
            templates = REPLY_TEMPLATES["afrobeat_appreciation"]
        elif any(word in text_lower for word in ["value", "prosper", "abundance", "mindset", "wealth"]):
            templates = REPLY_TEMPLATES["inspiration"]
        else:
            templates = REPLY_TEMPLATES["general"]
        
        return random.choice(templates)
    
    def follow_target_accounts(self, stats: BlitzStats, max_follows: int = 10) -> int:
        """Follow accounts from our target list."""
        if not self.client:
            return 0
        
        successful = 0
        accounts_to_try = random.sample(
            TARGET_FOLLOW_ACCOUNTS, 
            min(max_follows, len(TARGET_FOLLOW_ACCOUNTS))
        )
        
        for username in accounts_to_try:
            if username in self.followed_users:
                continue
            
            try:
                # Get user ID
                user = self.client.get_user(username=username)
                if not user or not user.data:
                    continue
                
                user_id = user.data.id
                
                # Follow them
                self.client.follow_user(user_id)
                self.followed_users.add(username)
                successful += 1
                stats.follows_succeeded += 1
                logger.info(f"✅ Followed @{username}")
                
            except tweepy.errors.Forbidden as e:
                if "already following" in str(e).lower():
                    self.followed_users.add(username)
                    logger.info(f"Already following @{username}")
                else:
                    stats.errors.append(f"Follow {username}: {str(e)[:50]}")
                    logger.warning(f"Cannot follow @{username}: {e}")
            except Exception as e:
                stats.errors.append(f"Follow {username}: {str(e)[:50]}")
                logger.warning(f"Error following @{username}: {e}")
            
            stats.follows_attempted += 1
            
            if successful >= max_follows:
                break
        
        return successful
    
    def discover_and_engage(self, stats: BlitzStats) -> int:
        """Search for content and engage with it."""
        if not self.client:
            return 0
        
        engagements = 0
        replies_left = self.MAX_REPLIES_PER_SESSION
        likes_left = self.MAX_LIKES_PER_SESSION
        quotes_left = self.MAX_QUOTES_PER_SESSION
        
        # Try different search queries
        queries = random.sample(BLITZ_SEARCH_QUERIES, min(5, len(BLITZ_SEARCH_QUERIES)))
        
        for query in queries:
            if replies_left <= 0 and likes_left <= 0:
                break
                
            try:
                # Search for tweets
                result = self.client.search_recent_tweets(
                    query=query,
                    max_results=10,
                    tweet_fields=["author_id", "created_at", "public_metrics"],
                    user_fields=["username", "public_metrics"],
                    expansions=["author_id"],
                )
                
                if not result.data:
                    continue
                
                # Build user lookup
                users = {}
                if result.includes and "users" in result.includes:
                    for user in result.includes["users"]:
                        users[user.id] = user
                
                for tweet in result.data:
                    stats.tweets_discovered += 1
                    tweet_id = str(tweet.id)
                    
                    # Skip if already engaged
                    if tweet_id in self.replied_tweets or tweet_id in self.liked_tweets:
                        continue
                    
                    # Get tweet metrics
                    metrics = tweet.public_metrics or {}
                    engagement_score = metrics.get("like_count", 0) + metrics.get("retweet_count", 0) * 2
                    
                    # Like tweets with some engagement (not zero, not viral)
                    if likes_left > 0 and 1 <= engagement_score <= 100:
                        try:
                            self.client.like(tweet.id)
                            self.liked_tweets.add(tweet_id)
                            stats.likes_given += 1
                            likes_left -= 1
                            engagements += 1
                            logger.info(f"❤️ Liked tweet {tweet_id}")
                        except Exception as e:
                            stats.errors.append(f"Like: {str(e)[:30]}")
                    
                    # Reply to some tweets
                    if replies_left > 0 and engagement_score >= 5:
                        try:
                            reply_text = self._get_reply_for_context(tweet.text)
                            self.client.create_tweet(
                                text=reply_text,
                                in_reply_to_tweet_id=tweet.id,
                            )
                            self.replied_tweets.add(tweet_id)
                            stats.replies_sent += 1
                            replies_left -= 1
                            engagements += 1
                            
                            author = users.get(tweet.author_id)
                            username = author.username if author else "unknown"
                            logger.info(f"💬 Replied to @{username}")
                        except Exception as e:
                            stats.errors.append(f"Reply: {str(e)[:30]}")
                    
                    # Quote tweet high-value content
                    if quotes_left > 0 and engagement_score >= 20:
                        try:
                            quote_text = random.choice(QUOTE_TEMPLATES)
                            self.client.create_tweet(
                                text=quote_text,
                                quote_tweet_id=tweet.id,
                            )
                            stats.quote_tweets += 1
                            quotes_left -= 1
                            engagements += 1
                            logger.info(f"🔁 Quote tweeted {tweet_id}")
                        except Exception as e:
                            stats.errors.append(f"Quote: {str(e)[:30]}")
                
            except Exception as e:
                logger.warning(f"Search error for '{query}': {e}")
                stats.errors.append(f"Search: {str(e)[:30]}")
        
        return engagements
    
    def run_blitz(self) -> BlitzStats:
        """
        Run a full Growth Blitz session.
        
        Returns:
            BlitzStats with session results
        """
        session_id = f"blitz_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        stats = BlitzStats(
            session_id=session_id,
            started_at=datetime.now(),
        )
        
        logger.info(f"🚀 Starting Growth Blitz session: {session_id}")
        
        try:
            # Connect if needed
            if not self.client:
                if not self.connect():
                    stats.errors.append("Failed to connect to Twitter")
                    return stats
            
            # Phase 1: Follow target accounts
            logger.info("Phase 1: Following target accounts...")
            follows = self.follow_target_accounts(stats, max_follows=self.MAX_FOLLOWS_PER_SESSION)
            logger.info(f"Followed {follows} new accounts")
            
            # Phase 2: Discover and engage with content
            logger.info("Phase 2: Discovering and engaging with content...")
            engagements = self.discover_and_engage(stats)
            logger.info(f"Made {engagements} engagements")
            
            # Phase 3: Log summary
            stats.completed_at = datetime.now()
            self.last_session = stats
            self.total_sessions += 1
            
            logger.info(f"✅ Blitz complete! Follows: {stats.follows_succeeded}, "
                       f"Replies: {stats.replies_sent}, Likes: {stats.likes_given}, "
                       f"Quotes: {stats.quote_tweets}")
            
        except Exception as e:
            logger.error(f"Blitz error: {e}")
            stats.errors.append(str(e))
            stats.completed_at = datetime.now()
        
        return stats
    
    def get_status(self) -> Dict[str, Any]:
        """Get current Growth Blitz status."""
        return {
            "connected": self.client is not None,
            "total_sessions": self.total_sessions,
            "accounts_followed": len(self.followed_users),
            "tweets_engaged": len(self.replied_tweets) + len(self.liked_tweets),
            "last_session": self.last_session.to_dict() if self.last_session else None,
            "target_accounts_remaining": len(TARGET_FOLLOW_ACCOUNTS) - len(self.followed_users),
        }


# Singleton instance
_growth_blitz: Optional[GrowthBlitz] = None


def get_growth_blitz() -> GrowthBlitz:
    """Get or create the Growth Blitz singleton."""
    global _growth_blitz
    if _growth_blitz is None:
        _growth_blitz = GrowthBlitz()
    return _growth_blitz
