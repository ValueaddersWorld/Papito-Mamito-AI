"""Twitter/X API integration for Papito Mamito AI.

This module provides direct posting to Twitter/X using Tweepy.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    import tweepy
    TWEEPY_AVAILABLE = True
except ImportError:
    TWEEPY_AVAILABLE = False

logger = logging.getLogger("papito.twitter")


@dataclass
class TweetResult:
    """Result of a tweet operation."""
    success: bool
    tweet_id: Optional[str] = None
    tweet_url: Optional[str] = None
    error: Optional[str] = None
    timestamp: Optional[str] = None


class TwitterPublisher:
    """Publisher for Twitter/X using the v2 API.
    
    Requires the following credentials:
    - X_API_KEY (Consumer Key)
    - X_API_SECRET (Consumer Secret)  
    - X_ACCESS_TOKEN (Access Token)
    - X_ACCESS_TOKEN_SECRET (Access Token Secret)
    - X_BEARER_TOKEN (Bearer Token) - optional, for read-only operations
    
    Get these from https://developer.twitter.com
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        access_token: Optional[str] = None,
        access_token_secret: Optional[str] = None,
        bearer_token: Optional[str] = None,
    ):
        """Initialize the Twitter publisher.
        
        Args:
            api_key: Twitter API Key (Consumer Key)
            api_secret: Twitter API Secret (Consumer Secret)
            access_token: User's Access Token
            access_token_secret: User's Access Token Secret
            bearer_token: Bearer Token for read-only operations
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.access_token = access_token
        self.access_token_secret = access_token_secret
        self.bearer_token = bearer_token
        
        self._client: Optional["tweepy.Client"] = None
        self._connected = False
        self._username: Optional[str] = None
        
    @classmethod
    def from_settings(cls) -> "TwitterPublisher":
        """Create a publisher from environment settings."""
        from ..settings import get_settings
        settings = get_settings()
        
        return cls(
            api_key=settings.x_api_key,
            api_secret=settings.x_api_secret,
            access_token=settings.x_access_token,
            access_token_secret=settings.x_access_token_secret,
            bearer_token=settings.x_bearer_token,
        )
    
    def connect(self) -> bool:
        """Connect to Twitter API.
        
        Returns:
            True if connection successful
        """
        if not TWEEPY_AVAILABLE:
            logger.error("Tweepy is not installed. Run: pip install tweepy")
            return False
        
        # Log credential status (without revealing values)
        logger.info(f"Twitter credentials check:")
        logger.info(f"  API Key: {'SET' if self.api_key else 'MISSING'}")
        logger.info(f"  API Secret: {'SET' if self.api_secret else 'MISSING'}")
        logger.info(f"  Access Token: {'SET' if self.access_token else 'MISSING'}")
        logger.info(f"  Access Token Secret: {'SET' if self.access_token_secret else 'MISSING'}")
        logger.info(f"  Bearer Token: {'SET' if self.bearer_token else 'MISSING'}")
            
        if not all([self.api_key, self.api_secret, self.access_token, self.access_token_secret]):
            logger.warning("Twitter credentials not fully configured")
            return False
            
        try:
            # Create v2 client
            self._client = tweepy.Client(
                consumer_key=self.api_key,
                consumer_secret=self.api_secret,
                access_token=self.access_token,
                access_token_secret=self.access_token_secret,
                bearer_token=self.bearer_token,
                wait_on_rate_limit=False,
            )
            
            # Verify credentials
            me = self._client.get_me()
            if me.data:
                self._username = me.data.username
                self._connected = True
                logger.info(f"✅ Connected to Twitter as @{self._username}")
                return True
            else:
                logger.error("Failed to verify Twitter credentials - no user data returned")
                return False
                
        except Exception as e:
            logger.error(f"Twitter connection failed: {type(e).__name__}: {e}")
            return False
    
    @property
    def is_connected(self) -> bool:
        """Check if connected to Twitter."""
        return self._connected
    
    @property
    def username(self) -> Optional[str]:
        """Get the connected username."""
        return self._username
    
    def post_tweet(
        self,
        text: str,
        reply_to: Optional[str] = None,
        quote_tweet_id: Optional[str] = None,
    ) -> TweetResult:
        """Post a tweet.
        
        Args:
            text: Tweet text (max 280 characters)
            reply_to: Optional tweet ID to reply to
            quote_tweet_id: Optional tweet ID to quote
            
        Returns:
            TweetResult with success status and tweet info
        """
        if not self._connected or not self._client:
            return TweetResult(
                success=False,
                error="Not connected to Twitter. Call connect() first.",
            )
            
        # Truncate if too long
        if len(text) > 280:
            text = text[:277] + "..."
            logger.warning("Tweet truncated to 280 characters")
            
        try:
            response = self._client.create_tweet(
                text=text,
                in_reply_to_tweet_id=reply_to,
                quote_tweet_id=quote_tweet_id,
            )
            
            if response.data:
                tweet_id = response.data["id"]
                tweet_url = f"https://twitter.com/{self._username}/status/{tweet_id}"
                
                logger.info(f"✅ Posted tweet: {tweet_url}")
                
                return TweetResult(
                    success=True,
                    tweet_id=tweet_id,
                    tweet_url=tweet_url,
                    timestamp=datetime.now().isoformat(),
                )
            else:
                return TweetResult(
                    success=False,
                    error="No data returned from Twitter API",
                )
                
        except tweepy.TweepyException as e:
            # Tweepy exceptions often contain the HTTP response with structured error details.
            status_code = None
            details: List[str] = []

            resp = getattr(e, "response", None)
            if resp is not None:
                status_code = getattr(resp, "status_code", None)
                try:
                    data = resp.json()
                    if isinstance(data, dict):
                        # Twitter/X tends to return {"title","detail","type","errors":[...]}
                        title = data.get("title")
                        detail = data.get("detail")
                        if title:
                            details.append(str(title))
                        if detail:
                            details.append(str(detail))
                        errors = data.get("errors")
                        if isinstance(errors, list):
                            for err in errors[:3]:
                                if isinstance(err, dict):
                                    msg = err.get("message") or err.get("detail") or err.get("title")
                                    if msg:
                                        details.append(str(msg))
                except Exception:
                    pass

            hint = None
            if status_code == 403:
                hint = (
                    "403 Forbidden from X: this usually means the app/user token does not have "
                    "write permission. In the X Developer Portal, set App permissions to 'Read and Write', "
                    "then regenerate the Access Token & Secret and update Railway env vars."
                )

            error = str(e)
            if status_code is not None:
                error = f"HTTP {status_code}: {error}"
            if details:
                error = f"{error} | Details: {' | '.join(details)}"
            if hint:
                error = f"{error} | Hint: {hint}"

            logger.error(f"Failed to post tweet: {error}")
            return TweetResult(success=False, error=error)
    
    def post_thread(self, tweets: List[str]) -> List[TweetResult]:
        """Post a thread of tweets.
        
        Args:
            tweets: List of tweet texts
            
        Returns:
            List of TweetResults
        """
        results = []
        previous_id = None
        
        for tweet_text in tweets:
            result = self.post_tweet(tweet_text, reply_to=previous_id)
            results.append(result)
            
            if result.success:
                previous_id = result.tweet_id
            else:
                # Stop thread if a tweet fails
                break
                
        return results
    
    def get_recent_tweets(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get recent tweets from the account.
        
        Args:
            count: Number of tweets to retrieve
            
        Returns:
            List of tweet data
        """
        if not self._connected or not self._client:
            return []
            
        try:
            me = self._client.get_me()
            if not me.data:
                return []
                
            tweets = self._client.get_users_tweets(
                me.data.id,
                max_results=min(count, 100),
                tweet_fields=["created_at", "public_metrics"],
            )
            
            if tweets.data:
                return [
                    {
                        "id": t.id,
                        "text": t.text,
                        "created_at": t.created_at.isoformat() if t.created_at else None,
                        "metrics": t.public_metrics,
                    }
                    for t in tweets.data
                ]
            return []
            
        except Exception as e:
            logger.error(f"Failed to get recent tweets: {e}")
            return []


# Convenience function
def get_twitter_publisher() -> TwitterPublisher:
    """Get a Twitter publisher from settings."""
    return TwitterPublisher.from_settings()
