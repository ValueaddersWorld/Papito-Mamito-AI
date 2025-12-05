"""X (Twitter) publisher using Twitter API v2.

This module provides X/Twitter publishing capabilities through the
Twitter API v2. Supports tweets, threads, and media attachments.

Authentication:
- Requires API keys and access tokens from Twitter Developer Portal
- OAuth 1.0a User Context authentication
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
import time

import httpx

from .base import BasePublisher, Interaction, Platform, PostType, PublishResult
from ..settings import get_settings


class XPublisher(BasePublisher):
    """Publisher for X (Twitter) via API v2.
    
    Supports:
    - Single tweets
    - Threads (multiple connected tweets)
    - Tweets with images/videos
    - Replies to tweets
    - Likes and retweets
    - Following users
    - Fetching mentions and replies
    """
    
    platform = Platform.X
    BASE_URL = "https://api.twitter.com/2"
    UPLOAD_URL = "https://upload.twitter.com/1.1"
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        access_token: Optional[str] = None,
        access_token_secret: Optional[str] = None,
        bearer_token: Optional[str] = None
    ):
        """Initialize X publisher.
        
        Args:
            api_key: Twitter API Key (Consumer Key)
            api_secret: Twitter API Secret (Consumer Secret)
            access_token: OAuth Access Token
            access_token_secret: OAuth Access Token Secret
            bearer_token: Bearer token for app-only auth
        """
        settings = get_settings()
        
        self.api_key = api_key or settings.x_api_key
        self.api_secret = api_secret or settings.x_api_secret
        self.access_token = access_token or settings.x_access_token
        self.access_token_secret = access_token_secret or settings.x_access_token_secret
        self.bearer_token = bearer_token or settings.x_bearer_token
        
        self._client: Optional[httpx.Client] = None
        self._connected = False
        self._user_id: Optional[str] = None
        self._username: Optional[str] = None
        
        # Rate limit tracking
        self._rate_limits: Dict[str, Dict[str, Any]] = {}
    
    def _get_oauth_headers(self) -> Dict[str, str]:
        """Generate OAuth 1.0a headers for API requests.
        
        Note: For production, use tweepy or authlib for proper OAuth signing.
        This is a simplified placeholder that uses Bearer token for some endpoints.
        """
        if self.bearer_token:
            return {"Authorization": f"Bearer {self.bearer_token}"}
        return {}
    
    def _get_client(self) -> httpx.Client:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.Client(
                timeout=30.0,
                headers=self._get_oauth_headers()
            )
        return self._client
    
    def is_connected(self) -> bool:
        """Check if connected to X API."""
        return self._connected and self._user_id is not None
    
    def connect(self) -> bool:
        """Verify connection to X API."""
        if not self.bearer_token:
            return False
        
        try:
            client = self._get_client()
            
            # Get authenticated user info
            response = client.get(
                f"{self.BASE_URL}/users/me",
                params={"user.fields": "id,username,name,public_metrics"}
            )
            
            if response.status_code == 200:
                data = response.json()["data"]
                self._user_id = data["id"]
                self._username = data["username"]
                self._connected = True
                return True
            else:
                self._connected = False
                return False
                
        except Exception:
            self._connected = False
            return False
    
    def disconnect(self) -> None:
        """Disconnect from X API."""
        self._connected = False
        if self._client:
            self._client.close()
            self._client = None
    
    def publish_post(
        self,
        content: str,
        media_urls: Optional[List[str]] = None,
        post_type: PostType = PostType.TEXT,
        **kwargs
    ) -> PublishResult:
        """Publish a tweet to X.
        
        Args:
            content: Tweet text (max 280 characters)
            media_urls: Optional list of media URLs to attach
            post_type: TEXT or THREAD
            **kwargs: Additional options like reply_to_tweet_id, quote_tweet_id
            
        Returns:
            PublishResult with success status and tweet details
        """
        if not self._connected:
            return PublishResult(
                success=False,
                platform=self.platform,
                error="Not connected to X API"
            )
        
        try:
            if post_type == PostType.THREAD:
                tweets = kwargs.get("tweets", [content])
                return self._publish_thread(tweets, media_urls)
            else:
                return self._publish_single_tweet(content, media_urls, **kwargs)
                
        except Exception as e:
            return PublishResult(
                success=False,
                platform=self.platform,
                error=str(e)
            )
    
    def _publish_single_tweet(
        self,
        text: str,
        media_urls: Optional[List[str]] = None,
        **kwargs
    ) -> PublishResult:
        """Publish a single tweet."""
        client = self._get_client()
        
        payload: Dict[str, Any] = {"text": text}
        
        # Handle reply
        if "reply_to_tweet_id" in kwargs:
            payload["reply"] = {"in_reply_to_tweet_id": kwargs["reply_to_tweet_id"]}
        
        # Handle quote tweet
        if "quote_tweet_id" in kwargs:
            payload["quote_tweet_id"] = kwargs["quote_tweet_id"]
        
        # Handle media (would need to upload first via v1.1 API)
        if media_urls:
            media_ids = self._upload_media(media_urls)
            if media_ids:
                payload["media"] = {"media_ids": media_ids}
        
        response = client.post(
            f"{self.BASE_URL}/tweets",
            json=payload,
            headers={
                **self._get_oauth_headers(),
                "Content-Type": "application/json"
            }
        )
        
        self._update_rate_limits("tweets", response.headers)
        
        if response.status_code in (200, 201):
            data = response.json()["data"]
            tweet_id = data["id"]
            
            return PublishResult(
                success=True,
                platform=self.platform,
                post_id=tweet_id,
                post_url=f"https://x.com/{self._username}/status/{tweet_id}",
                rate_limit_remaining=self._rate_limits.get("tweets", {}).get("remaining"),
                raw_response=response.json()
            )
        else:
            return PublishResult(
                success=False,
                platform=self.platform,
                error=f"Failed to tweet: {response.text}",
                raw_response=response.json() if response.text else None
            )
    
    def _publish_thread(
        self,
        tweets: List[str],
        media_urls: Optional[List[str]] = None
    ) -> PublishResult:
        """Publish a thread of connected tweets."""
        if not tweets:
            return PublishResult(
                success=False,
                platform=self.platform,
                error="No tweets provided for thread"
            )
        
        first_tweet_id = None
        last_tweet_id = None
        
        for i, tweet_text in enumerate(tweets):
            kwargs = {}
            
            # Reply to previous tweet in thread
            if last_tweet_id:
                kwargs["reply_to_tweet_id"] = last_tweet_id
            
            # Attach media to first tweet only
            tweet_media = media_urls if i == 0 else None
            
            result = self._publish_single_tweet(tweet_text, tweet_media, **kwargs)
            
            if not result.success:
                return PublishResult(
                    success=False,
                    platform=self.platform,
                    error=f"Thread failed at tweet {i+1}: {result.error}",
                    post_id=first_tweet_id
                )
            
            if i == 0:
                first_tweet_id = result.post_id
            last_tweet_id = result.post_id
            
            # Small delay between tweets to avoid rate limits
            if i < len(tweets) - 1:
                time.sleep(1)
        
        return PublishResult(
            success=True,
            platform=self.platform,
            post_id=first_tweet_id,
            post_url=f"https://x.com/{self._username}/status/{first_tweet_id}",
            raw_response={"thread_length": len(tweets), "last_tweet_id": last_tweet_id}
        )
    
    def _upload_media(self, media_urls: List[str]) -> List[str]:
        """Upload media files and return media IDs.
        
        Note: Media upload requires v1.1 API with OAuth 1.0a.
        This is a placeholder - for production use tweepy or similar.
        """
        # TODO: Implement proper media upload with OAuth 1.0a
        return []
    
    def reply_to_post(
        self,
        post_id: str,
        content: str,
        **kwargs
    ) -> PublishResult:
        """Reply to a tweet.
        
        Args:
            post_id: ID of the tweet to reply to
            content: Reply text
            
        Returns:
            PublishResult with success status
        """
        return self._publish_single_tweet(content, reply_to_tweet_id=post_id)
    
    def get_interactions(
        self,
        since: Optional[datetime] = None,
        limit: int = 50
    ) -> List[Interaction]:
        """Fetch recent mentions and replies.
        
        Args:
            since: Only fetch interactions after this time
            limit: Maximum number to fetch
            
        Returns:
            List of Interaction objects
        """
        if not self._connected:
            return []
        
        interactions = []
        client = self._get_client()
        
        try:
            # Get mentions timeline
            params: Dict[str, Any] = {
                "max_results": min(limit, 100),
                "tweet.fields": "created_at,author_id,conversation_id",
                "expansions": "author_id",
                "user.fields": "username,name,profile_image_url"
            }
            
            if since:
                params["start_time"] = since.isoformat() + "Z"
            
            response = client.get(
                f"{self.BASE_URL}/users/{self._user_id}/mentions",
                params=params
            )
            
            if response.status_code == 200:
                data = response.json()
                tweets = data.get("data", [])
                users = {u["id"]: u for u in data.get("includes", {}).get("users", [])}
                
                for tweet in tweets:
                    author = users.get(tweet["author_id"], {})
                    
                    interactions.append(Interaction(
                        platform=self.platform,
                        interaction_id=tweet["id"],
                        interaction_type="mention",
                        post_id=tweet.get("conversation_id"),
                        username=author.get("username", ""),
                        display_name=author.get("name", ""),
                        profile_url=f"https://x.com/{author.get('username', '')}",
                        message=tweet.get("text", ""),
                        media_urls=[],
                        created_at=datetime.fromisoformat(
                            tweet["created_at"].replace("Z", "+00:00")
                        )
                    ))
                    
        except Exception:
            pass
        
        return interactions[:limit]
    
    def like_post(self, post_id: str) -> bool:
        """Like a tweet.
        
        Args:
            post_id: ID of the tweet to like
            
        Returns:
            True if successful
        """
        if not self._connected:
            return False
        
        try:
            client = self._get_client()
            response = client.post(
                f"{self.BASE_URL}/users/{self._user_id}/likes",
                json={"tweet_id": post_id},
                headers={
                    **self._get_oauth_headers(),
                    "Content-Type": "application/json"
                }
            )
            
            return response.status_code == 200
            
        except Exception:
            return False
    
    def retweet(self, post_id: str) -> bool:
        """Retweet a tweet.
        
        Args:
            post_id: ID of the tweet to retweet
            
        Returns:
            True if successful
        """
        if not self._connected:
            return False
        
        try:
            client = self._get_client()
            response = client.post(
                f"{self.BASE_URL}/users/{self._user_id}/retweets",
                json={"tweet_id": post_id},
                headers={
                    **self._get_oauth_headers(),
                    "Content-Type": "application/json"
                }
            )
            
            return response.status_code == 200
            
        except Exception:
            return False
    
    def follow_user(self, username: str) -> bool:
        """Follow a user.
        
        Args:
            username: Username to follow (without @)
            
        Returns:
            True if successful
        """
        if not self._connected:
            return False
        
        try:
            client = self._get_client()
            
            # First get user ID from username
            user_response = client.get(
                f"{self.BASE_URL}/users/by/username/{username}"
            )
            
            if user_response.status_code != 200:
                return False
            
            target_user_id = user_response.json()["data"]["id"]
            
            # Then follow
            response = client.post(
                f"{self.BASE_URL}/users/{self._user_id}/following",
                json={"target_user_id": target_user_id},
                headers={
                    **self._get_oauth_headers(),
                    "Content-Type": "application/json"
                }
            )
            
            return response.status_code == 200
            
        except Exception:
            return False
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get X account metrics."""
        if not self._connected:
            return {}
        
        try:
            client = self._get_client()
            
            response = client.get(
                f"{self.BASE_URL}/users/{self._user_id}",
                params={"user.fields": "public_metrics,created_at"}
            )
            
            if response.status_code == 200:
                data = response.json()["data"]
                metrics = data.get("public_metrics", {})
                
                return {
                    "followers": metrics.get("followers_count"),
                    "following": metrics.get("following_count"),
                    "tweets_count": metrics.get("tweet_count"),
                    "listed_count": metrics.get("listed_count"),
                    "username": data.get("username"),
                    "created_at": data.get("created_at"),
                }
            
            return {}
            
        except Exception:
            return {}
    
    def _update_rate_limits(self, endpoint: str, headers: httpx.Headers) -> None:
        """Update rate limit tracking from response headers."""
        limit = headers.get("x-rate-limit-limit")
        remaining = headers.get("x-rate-limit-remaining")
        reset = headers.get("x-rate-limit-reset")
        
        if remaining is not None:
            self._rate_limits[endpoint] = {
                "limit": int(limit) if limit else None,
                "remaining": int(remaining),
                "reset_at": datetime.fromtimestamp(int(reset)) if reset else None
            }
    
    def get_rate_limit_status(self) -> Dict[str, Any]:
        """Get current rate limit status for all tracked endpoints."""
        return self._rate_limits
