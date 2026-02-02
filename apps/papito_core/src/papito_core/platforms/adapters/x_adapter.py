"""
PAPITO MAMITO AI - X/TWITTER ADAPTER
====================================
Adapter for X (formerly Twitter) platform.

This adapter provides:
- Real-time mention streaming (Filtered Stream API)
- Polling fallback for free tier
- Tweet posting, replying, liking
- User lookup and analytics

API Requirements:
- X API v2 access (Basic or Pro tier for streaming)
- OAuth 2.0 User Context for user actions
- App-only auth for read operations

© 2026 Value Adders World - Entertainment Division
"Add value or don't act."
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Set

from ..base import (
    Platform,
    PlatformAdapter,
    PlatformConfig,
    PlatformEvent,
    PlatformAction,
    ActionResult,
    PlatformCapability,
    EventCategory,
)

logger = logging.getLogger("papito.platforms.x")


class XAdapter(PlatformAdapter):
    """
    Adapter for X/Twitter platform.
    
    Capabilities:
    - Text posts (tweets)
    - Replies
    - Likes
    - Retweets/reposts
    - Quote tweets
    - Direct messages
    - Real-time streaming (Pro tier)
    - Search
    - Trending topics
    
    Usage:
        config = PlatformConfig(
            platform=Platform.X,
            bearer_token="your_bearer_token",
            api_key="your_api_key",
            api_secret="your_api_secret",
            access_token="your_access_token",
            access_secret="your_access_secret",
        )
        
        adapter = XAdapter(config)
        await adapter.connect()
        
        # Listen for mentions
        await adapter.listen(handle_event)
        
        # Post a tweet
        result = await adapter.execute(PlatformAction(
            action_type="post",
            content="Hello from Papito!",
        ))
    """
    
    platform = Platform.X
    
    capabilities = {
        PlatformCapability.TEXT_POST,
        PlatformCapability.IMAGE_POST,
        PlatformCapability.VIDEO_POST,
        PlatformCapability.REPLY,
        PlatformCapability.LIKE,
        PlatformCapability.REPOST,
        PlatformCapability.QUOTE,
        PlatformCapability.FOLLOW,
        PlatformCapability.DIRECT_MESSAGE,
        PlatformCapability.SEARCH,
        PlatformCapability.TRENDING,
        PlatformCapability.POLLING,
        # STREAMING available only with Pro tier
    }
    
    def __init__(self, config: PlatformConfig):
        """Initialize X adapter.
        
        Args:
            config: Platform configuration with X credentials
        """
        super().__init__(config)
        
        self._client = None
        self._stream = None
        self._poll_task: Optional[asyncio.Task] = None
        self._poll_interval = 60  # seconds
        self._last_mention_id: Optional[str] = None
        self._user_cache: Dict[str, Dict[str, Any]] = {}
        
        # Check for streaming capability
        if config.custom_settings.get("streaming_enabled"):
            self.capabilities.add(PlatformCapability.STREAMING)
    
    async def connect(self) -> bool:
        """Connect to X API."""
        try:
            # Import tweepy here to allow graceful degradation
            import tweepy
            
            # Create client
            self._client = tweepy.Client(
                bearer_token=self.config.bearer_token,
                consumer_key=self.config.api_key,
                consumer_secret=self.config.api_secret,
                access_token=self.config.access_token,
                access_token_secret=self.config.access_secret,
                wait_on_rate_limit=True,
            )
            
            # Verify credentials
            me = self._client.get_me()
            if me and me.data:
                self._connected = True
                self._user_cache["me"] = {
                    "id": me.data.id,
                    "username": me.data.username,
                    "name": me.data.name,
                }
                logger.info(f"Connected to X as @{me.data.username}")
                return True
            
            logger.error("Failed to verify X credentials")
            return False
            
        except ImportError:
            logger.error("tweepy not installed - run: pip install tweepy")
            return False
        except Exception as e:
            logger.error(f"Error connecting to X: {e}")
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from X API."""
        if self._poll_task:
            self._poll_task.cancel()
            self._poll_task = None
        
        if self._stream:
            self._stream.disconnect()
            self._stream = None
        
        self._client = None
        self._connected = False
        logger.info("Disconnected from X")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check X API health."""
        if not self._client:
            return {"status": "disconnected", "platform": "x"}
        
        try:
            # Simple health check - get rate limit status
            me = self._client.get_me()
            return {
                "status": "healthy",
                "platform": "x",
                "username": me.data.username if me and me.data else None,
                "last_mention_id": self._last_mention_id,
            }
        except Exception as e:
            return {
                "status": "error",
                "platform": "x",
                "error": str(e),
            }
    
    async def listen(self, callback: Callable[[PlatformEvent], None]) -> None:
        """Start listening for X events."""
        self.register_callback(callback)
        
        if PlatformCapability.STREAMING in self.capabilities:
            # Use Filtered Stream
            await self._start_streaming()
        else:
            # Use polling
            await self._start_polling()
    
    async def stop_listening(self) -> None:
        """Stop listening for events."""
        if self._poll_task:
            self._poll_task.cancel()
            self._poll_task = None
        
        if self._stream:
            self._stream.disconnect()
            self._stream = None
        
        self._event_callbacks.clear()
        logger.info("Stopped listening on X")
    
    async def _start_streaming(self) -> None:
        """Start streaming with Filtered Stream API."""
        try:
            import tweepy
            
            class PapitoStreamListener(tweepy.StreamingClient):
                def __init__(self, adapter: "XAdapter", bearer_token: str):
                    super().__init__(bearer_token, wait_on_rate_limit=True)
                    self.adapter = adapter
                
                def on_tweet(self, tweet):
                    # Convert to PlatformEvent
                    event = self.adapter._convert_tweet_to_event(tweet)
                    if event:
                        asyncio.create_task(self.adapter._emit_event(event))
                
                def on_error(self, error):
                    logger.error(f"Stream error: {error}")
            
            self._stream = PapitoStreamListener(self, self.config.bearer_token)
            
            # Add rules for mentions
            me = self._user_cache.get("me", {})
            username = me.get("username")
            
            if username:
                # Delete existing rules
                rules = self._stream.get_rules()
                if rules and rules.data:
                    self._stream.delete_rules([r.id for r in rules.data])
                
                # Add mention rule
                self._stream.add_rules(
                    tweepy.StreamRule(f"@{username}", tag="mentions")
                )
                
                # Start streaming in background
                self._stream.filter(
                    tweet_fields=["author_id", "created_at", "conversation_id", "in_reply_to_user_id"],
                    user_fields=["username", "name", "verified"],
                    expansions=["author_id"],
                    threaded=True,
                )
                
                logger.info(f"Started X streaming for @{username}")
            
        except Exception as e:
            logger.error(f"Error starting X stream: {e}")
            # Fall back to polling
            await self._start_polling()
    
    async def _start_polling(self) -> None:
        """Start polling for mentions."""
        async def poll_loop():
            while True:
                try:
                    await self._poll_mentions()
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Error polling X: {e}")
                
                await asyncio.sleep(self._poll_interval)
        
        self._poll_task = asyncio.create_task(poll_loop())
        logger.info("Started X polling")
    
    async def _poll_mentions(self) -> None:
        """Poll for new mentions."""
        if not self._client:
            return
        
        try:
            me = self._user_cache.get("me", {})
            user_id = me.get("id")
            
            if not user_id:
                return
            
            # Get mentions
            mentions = self._client.get_users_mentions(
                id=user_id,
                since_id=self._last_mention_id,
                tweet_fields=["author_id", "created_at", "conversation_id"],
                user_fields=["username", "name", "verified"],
                expansions=["author_id"],
                max_results=100,
            )
            
            if mentions and mentions.data:
                # Build user lookup
                users = {}
                if mentions.includes and "users" in mentions.includes:
                    for user in mentions.includes["users"]:
                        users[user.id] = {
                            "username": user.username,
                            "name": user.name,
                            "verified": getattr(user, "verified", False),
                        }
                
                # Process mentions (newest first)
                for tweet in reversed(mentions.data):
                    event = self._convert_tweet_to_event(tweet, users)
                    if event:
                        await self._emit_event(event)
                    
                    self._last_mention_id = tweet.id
                
                logger.debug(f"Processed {len(mentions.data)} X mentions")
                
        except Exception as e:
            logger.error(f"Error polling X mentions: {e}")
    
    def _convert_tweet_to_event(
        self,
        tweet,
        users: Optional[Dict[str, Dict]] = None,
    ) -> Optional[PlatformEvent]:
        """Convert a tweet to a PlatformEvent."""
        try:
            users = users or {}
            author = users.get(str(tweet.author_id), {})
            
            # Determine category
            if hasattr(tweet, "in_reply_to_user_id") and tweet.in_reply_to_user_id:
                category = EventCategory.REPLY
            else:
                category = EventCategory.MENTION
            
            return PlatformEvent(
                event_id=f"x_{tweet.id}",
                platform=Platform.X,
                category=category,
                user_id=str(tweet.author_id),
                user_name=author.get("username", "unknown"),
                user_display_name=author.get("name", ""),
                content=tweet.text,
                source_id=str(tweet.id),
                conversation_id=str(tweet.conversation_id) if hasattr(tweet, "conversation_id") else "",
                metadata={
                    "verified": author.get("verified", False),
                },
                raw_event=tweet,
                created_at=tweet.created_at if hasattr(tweet, "created_at") else datetime.now(timezone.utc),
            )
        except Exception as e:
            logger.error(f"Error converting tweet: {e}")
            return None
    
    async def execute(self, action: PlatformAction) -> ActionResult:
        """Execute an action on X."""
        if not self._client:
            return ActionResult(
                success=False,
                action_id=action.action_id,
                platform=Platform.X,
                error_message="Not connected to X",
            )
        
        try:
            if action.action_type == "post":
                return await self._post_tweet(action)
            elif action.action_type == "reply":
                return await self._reply_to_tweet(action)
            elif action.action_type == "like":
                return await self._like_tweet(action)
            elif action.action_type == "retweet":
                return await self._retweet(action)
            elif action.action_type == "quote":
                return await self._quote_tweet(action)
            elif action.action_type == "dm":
                return await self._send_dm(action)
            elif action.action_type == "follow":
                return await self._follow_user(action)
            else:
                return ActionResult(
                    success=False,
                    action_id=action.action_id,
                    platform=Platform.X,
                    error_message=f"Unknown action type: {action.action_type}",
                )
        except Exception as e:
            logger.error(f"Error executing X action: {e}")
            return ActionResult(
                success=False,
                action_id=action.action_id,
                platform=Platform.X,
                error_message=str(e),
            )
    
    async def _post_tweet(self, action: PlatformAction) -> ActionResult:
        """Post a new tweet."""
        response = self._client.create_tweet(text=action.content)
        
        if response and response.data:
            tweet_id = response.data["id"]
            return ActionResult(
                success=True,
                action_id=action.action_id,
                platform=Platform.X,
                result_id=tweet_id,
                result_url=f"https://x.com/i/web/status/{tweet_id}",
            )
        
        return ActionResult(
            success=False,
            action_id=action.action_id,
            platform=Platform.X,
            error_message="Failed to create tweet",
        )
    
    async def _reply_to_tweet(self, action: PlatformAction) -> ActionResult:
        """Reply to a tweet."""
        response = self._client.create_tweet(
            text=action.content,
            in_reply_to_tweet_id=action.reply_to_id,
        )
        
        if response and response.data:
            tweet_id = response.data["id"]
            return ActionResult(
                success=True,
                action_id=action.action_id,
                platform=Platform.X,
                result_id=tweet_id,
                result_url=f"https://x.com/i/web/status/{tweet_id}",
            )
        
        return ActionResult(
            success=False,
            action_id=action.action_id,
            platform=Platform.X,
            error_message="Failed to reply to tweet",
        )
    
    async def _like_tweet(self, action: PlatformAction) -> ActionResult:
        """Like a tweet."""
        me = self._user_cache.get("me", {})
        response = self._client.like(me["id"], action.target_content_id)
        
        return ActionResult(
            success=bool(response),
            action_id=action.action_id,
            platform=Platform.X,
            result_id=action.target_content_id,
        )
    
    async def _retweet(self, action: PlatformAction) -> ActionResult:
        """Retweet a tweet."""
        me = self._user_cache.get("me", {})
        response = self._client.retweet(me["id"], action.target_content_id)
        
        return ActionResult(
            success=bool(response),
            action_id=action.action_id,
            platform=Platform.X,
            result_id=action.target_content_id,
        )
    
    async def _quote_tweet(self, action: PlatformAction) -> ActionResult:
        """Quote tweet."""
        response = self._client.create_tweet(
            text=action.content,
            quote_tweet_id=action.target_content_id,
        )
        
        if response and response.data:
            tweet_id = response.data["id"]
            return ActionResult(
                success=True,
                action_id=action.action_id,
                platform=Platform.X,
                result_id=tweet_id,
                result_url=f"https://x.com/i/web/status/{tweet_id}",
            )
        
        return ActionResult(
            success=False,
            action_id=action.action_id,
            platform=Platform.X,
            error_message="Failed to quote tweet",
        )
    
    async def _send_dm(self, action: PlatformAction) -> ActionResult:
        """Send a direct message."""
        # Note: DM API has limited access
        try:
            # This requires OAuth 1.0a user context
            response = self._client.create_direct_message(
                participant_id=action.target_user_id,
                text=action.content,
            )
            
            return ActionResult(
                success=bool(response),
                action_id=action.action_id,
                platform=Platform.X,
            )
        except Exception as e:
            return ActionResult(
                success=False,
                action_id=action.action_id,
                platform=Platform.X,
                error_message=f"DM failed: {e}",
            )
    
    async def _follow_user(self, action: PlatformAction) -> ActionResult:
        """Follow a user."""
        me = self._user_cache.get("me", {})
        response = self._client.follow_user(me["id"], action.target_user_id)
        
        return ActionResult(
            success=bool(response),
            action_id=action.action_id,
            platform=Platform.X,
        )
    
    async def get_user(self, user_id: str) -> Dict[str, Any]:
        """Get user information."""
        if not self._client:
            return {}
        
        try:
            response = self._client.get_user(
                id=user_id,
                user_fields=["username", "name", "description", "public_metrics", "verified"],
            )
            
            if response and response.data:
                user = response.data
                return {
                    "id": user.id,
                    "username": user.username,
                    "name": user.name,
                    "description": user.description,
                    "followers_count": user.public_metrics["followers_count"],
                    "following_count": user.public_metrics["following_count"],
                    "verified": getattr(user, "verified", False),
                }
        except Exception as e:
            logger.error(f"Error getting X user: {e}")
        
        return {}
    
    async def get_content(self, content_id: str) -> Dict[str, Any]:
        """Get tweet by ID."""
        if not self._client:
            return {}
        
        try:
            response = self._client.get_tweet(
                id=content_id,
                tweet_fields=["author_id", "created_at", "public_metrics", "conversation_id"],
            )
            
            if response and response.data:
                tweet = response.data
                return {
                    "id": tweet.id,
                    "text": tweet.text,
                    "author_id": tweet.author_id,
                    "created_at": tweet.created_at.isoformat() if tweet.created_at else None,
                    "likes": tweet.public_metrics["like_count"],
                    "retweets": tweet.public_metrics["retweet_count"],
                    "replies": tweet.public_metrics["reply_count"],
                }
        except Exception as e:
            logger.error(f"Error getting X tweet: {e}")
        
        return {}
    
    async def search(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search tweets."""
        if not self._client:
            return []
        
        try:
            response = self._client.search_recent_tweets(
                query=query,
                max_results=min(limit, 100),
                tweet_fields=["author_id", "created_at", "public_metrics"],
            )
            
            results = []
            if response and response.data:
                for tweet in response.data:
                    results.append({
                        "id": tweet.id,
                        "text": tweet.text,
                        "author_id": tweet.author_id,
                    })
            
            return results
        except Exception as e:
            logger.error(f"Error searching X: {e}")
            return []
    
    async def get_trending(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get trending topics."""
        # Note: Trends API requires elevated access
        logger.warning("X trending requires elevated API access")
        return []
