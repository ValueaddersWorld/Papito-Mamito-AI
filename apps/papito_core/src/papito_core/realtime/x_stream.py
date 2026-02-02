"""
PAPITO MAMITO AI - X/TWITTER STREAM LISTENER
============================================
Real-time Twitter/X mention monitoring using Filtered Stream API.

Instead of polling every 15 minutes, this listens for mentions
in real-time and immediately dispatches events.

Requirements:
- X API v2 Basic tier ($200/month) or higher
- Bearer token with elevated access

Architecture:
    X Filtered Stream API
            │
            │ Real-time push
            ▼
    ┌───────────────────┐
    │  XStreamListener  │
    │  - Filter rules   │
    │  - Reconnection   │
    │  - Rate limiting  │
    └─────────┬─────────┘
              │
              │ emit()
              ▼
    ┌───────────────────┐
    │  EventDispatcher  │
    └───────────────────┘

© 2026 Value Adders World - Entertainment Division
"Add value or don't act."
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional

import httpx

from .event_dispatcher import (
    Event,
    EventType,
    EventPriority,
    EventDispatcher,
    get_event_dispatcher,
)

logger = logging.getLogger("papito.x_stream")

# X API v2 endpoints
X_STREAM_RULES_URL = "https://api.twitter.com/2/tweets/search/stream/rules"
X_STREAM_URL = "https://api.twitter.com/2/tweets/search/stream"
X_USERS_URL = "https://api.twitter.com/2/users"


class XStreamListener:
    """
    Real-time X/Twitter stream listener using Filtered Stream API.
    
    Features:
    - Automatic filter rules for @papito_mamito mentions
    - Real-time event dispatching (< 1 second latency)
    - Automatic reconnection on disconnect
    - Backoff on rate limits
    - User lookup caching
    
    Usage:
        listener = XStreamListener(
            bearer_token="...",
            username="papito_mamito"
        )
        await listener.start()
    """
    
    def __init__(
        self,
        bearer_token: str | None = None,
        username: str = "papito_mamito",
        dispatcher: EventDispatcher | None = None,
    ):
        """Initialize the X stream listener.
        
        Args:
            bearer_token: X API Bearer token (or from env X_BEARER_TOKEN)
            username: Papito's Twitter username to monitor mentions
            dispatcher: EventDispatcher instance (uses global if None)
        """
        self.bearer_token = bearer_token or os.getenv("X_BEARER_TOKEN", "")
        self.username = username
        self.dispatcher = dispatcher or get_event_dispatcher()
        
        self._running = False
        self._stream_task: asyncio.Task | None = None
        self._reconnect_attempts = 0
        self._max_reconnect_attempts = 10
        self._backoff_seconds = 1
        
        # User cache to avoid repeated lookups
        self._user_cache: Dict[str, Dict[str, Any]] = {}
        
        # Stats
        self._tweets_received = 0
        self._events_emitted = 0
        self._last_tweet_at: datetime | None = None
        
        if not self.bearer_token:
            logger.warning("No X_BEARER_TOKEN provided - stream will not connect")
    
    @property
    def headers(self) -> Dict[str, str]:
        """HTTP headers for X API requests."""
        return {
            "Authorization": f"Bearer {self.bearer_token}",
            "Content-Type": "application/json",
        }
    
    async def setup_rules(self) -> bool:
        """Set up stream filter rules for mentions.
        
        Returns:
            True if rules were set up successfully
        """
        if not self.bearer_token:
            logger.error("Cannot setup rules: no bearer token")
            return False
        
        # Define filter rules
        rules = [
            {
                "value": f"@{self.username} -is:retweet",
                "tag": "papito_mentions"
            },
            {
                "value": f"#{self.username} OR #PapitoMamito -is:retweet",
                "tag": "papito_hashtags"
            },
        ]
        
        async with httpx.AsyncClient() as client:
            # First, get existing rules
            try:
                response = await client.get(
                    X_STREAM_RULES_URL,
                    headers=self.headers,
                )
                response.raise_for_status()
                existing = response.json()
                
                # Delete existing rules if any
                if existing.get("data"):
                    rule_ids = [r["id"] for r in existing["data"]]
                    delete_response = await client.post(
                        X_STREAM_RULES_URL,
                        headers=self.headers,
                        json={"delete": {"ids": rule_ids}}
                    )
                    delete_response.raise_for_status()
                    logger.info(f"Deleted {len(rule_ids)} existing rules")
                
                # Add new rules
                add_response = await client.post(
                    X_STREAM_RULES_URL,
                    headers=self.headers,
                    json={"add": rules}
                )
                add_response.raise_for_status()
                result = add_response.json()
                
                if result.get("errors"):
                    logger.error(f"Rule errors: {result['errors']}")
                    return False
                
                logger.info(f"Stream rules configured: {[r['value'] for r in rules]}")
                return True
                
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error setting up rules: {e.response.status_code} - {e.response.text}")
                return False
            except Exception as e:
                logger.exception(f"Error setting up rules: {e}")
                return False
    
    async def get_user_info(self, user_id: str) -> Dict[str, Any]:
        """Get user information from X API with caching.
        
        Args:
            user_id: X user ID
            
        Returns:
            User data dict
        """
        # Check cache first
        if user_id in self._user_cache:
            return self._user_cache[user_id]
        
        if not self.bearer_token:
            return {"id": user_id, "username": "unknown"}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{X_USERS_URL}/{user_id}",
                    headers=self.headers,
                    params={
                        "user.fields": "username,name,public_metrics,description,profile_image_url"
                    }
                )
                response.raise_for_status()
                user_data = response.json().get("data", {})
                
                # Cache the result
                self._user_cache[user_id] = user_data
                return user_data
                
        except Exception as e:
            logger.warning(f"Error fetching user {user_id}: {e}")
            return {"id": user_id, "username": "unknown"}
    
    async def _process_tweet(self, tweet_data: Dict[str, Any]) -> None:
        """Process a tweet from the stream and emit event.
        
        Args:
            tweet_data: Raw tweet data from stream
        """
        self._tweets_received += 1
        self._last_tweet_at = datetime.now(timezone.utc)
        
        tweet = tweet_data.get("data", {})
        includes = tweet_data.get("includes", {})
        matching_rules = tweet_data.get("matching_rules", [])
        
        tweet_id = tweet.get("id", "")
        text = tweet.get("text", "")
        author_id = tweet.get("author_id", "")
        
        # Get user info from includes or fetch
        users = {u["id"]: u for u in includes.get("users", [])}
        author = users.get(author_id) or await self.get_user_info(author_id)
        
        # Determine event type
        event_type = EventType.MENTION
        
        referenced_tweets = tweet.get("referenced_tweets", [])
        for ref in referenced_tweets:
            if ref.get("type") == "replied_to":
                event_type = EventType.REPLY
                break
            elif ref.get("type") == "quoted":
                event_type = EventType.QUOTE
                break
        
        # Determine priority based on follower count
        follower_count = author.get("public_metrics", {}).get("followers_count", 0)
        priority = EventPriority.HIGH
        
        if follower_count > 100000:
            priority = EventPriority.CRITICAL
        elif follower_count > 10000:
            priority = EventPriority.HIGH
        elif follower_count < 1000:
            priority = EventPriority.NORMAL
        
        # Create and emit event
        event = Event(
            type=event_type,
            priority=priority,
            source="x_stream",
            source_id=tweet_id,
            user_id=author_id,
            user_name=author.get("username", "unknown"),
            content=text,
            created_at=datetime.fromisoformat(
                tweet.get("created_at", "").replace("Z", "+00:00")
            ) if tweet.get("created_at") else datetime.now(timezone.utc),
            metadata={
                "display_name": author.get("name", ""),
                "follower_count": follower_count,
                "profile_image": author.get("profile_image_url", ""),
                "matching_rules": [r.get("tag") for r in matching_rules],
                "referenced_tweets": referenced_tweets,
                "conversation_id": tweet.get("conversation_id"),
            }
        )
        
        await self.dispatcher.emit(event)
        self._events_emitted += 1
        
        logger.info(
            f"Stream event: {event_type.value} from @{author.get('username')} "
            f"(followers={follower_count}): {text[:50]}..."
        )
    
    async def _stream_loop(self) -> None:
        """Main streaming loop with reconnection logic."""
        logger.info("Starting X stream loop")
        
        stream_params = {
            "tweet.fields": "created_at,author_id,conversation_id,referenced_tweets,in_reply_to_user_id",
            "user.fields": "username,name,public_metrics,profile_image_url",
            "expansions": "author_id,referenced_tweets.id",
        }
        
        while self._running:
            try:
                async with httpx.AsyncClient(timeout=None) as client:
                    async with client.stream(
                        "GET",
                        X_STREAM_URL,
                        headers=self.headers,
                        params=stream_params,
                    ) as response:
                        if response.status_code == 429:
                            # Rate limited
                            retry_after = int(response.headers.get("retry-after", 60))
                            logger.warning(f"Rate limited, waiting {retry_after}s")
                            await asyncio.sleep(retry_after)
                            continue
                        
                        response.raise_for_status()
                        
                        # Reset reconnect attempts on successful connection
                        self._reconnect_attempts = 0
                        self._backoff_seconds = 1
                        
                        logger.info("Connected to X stream")
                        
                        async for line in response.aiter_lines():
                            if not self._running:
                                break
                            
                            if not line:
                                continue  # Keep-alive empty line
                            
                            try:
                                data = json.loads(line)
                                
                                if "data" in data:
                                    await self._process_tweet(data)
                                elif "errors" in data:
                                    logger.error(f"Stream error: {data['errors']}")
                                    
                            except json.JSONDecodeError:
                                logger.warning(f"Invalid JSON in stream: {line[:100]}")
                
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error in stream: {e.response.status_code}")
                
            except httpx.ReadTimeout:
                logger.warning("Stream read timeout, reconnecting...")
                
            except Exception as e:
                logger.exception(f"Stream error: {e}")
            
            # Reconnection with exponential backoff
            if self._running:
                self._reconnect_attempts += 1
                
                if self._reconnect_attempts > self._max_reconnect_attempts:
                    logger.error("Max reconnection attempts reached, stopping stream")
                    self._running = False
                    break
                
                wait_time = min(self._backoff_seconds * (2 ** self._reconnect_attempts), 300)
                logger.info(f"Reconnecting in {wait_time}s (attempt {self._reconnect_attempts})")
                await asyncio.sleep(wait_time)
        
        logger.info("X stream loop stopped")
    
    async def start(self) -> bool:
        """Start the stream listener.
        
        Returns:
            True if started successfully
        """
        if self._running:
            logger.warning("Stream already running")
            return True
        
        if not self.bearer_token:
            logger.error("Cannot start stream: no bearer token")
            return False
        
        # Set up filter rules
        if not await self.setup_rules():
            logger.error("Failed to set up stream rules")
            return False
        
        self._running = True
        self._stream_task = asyncio.create_task(self._stream_loop())
        
        logger.info("X stream listener started")
        return True
    
    async def stop(self) -> None:
        """Stop the stream listener."""
        if not self._running:
            return
        
        self._running = False
        
        if self._stream_task:
            self._stream_task.cancel()
            try:
                await self._stream_task
            except asyncio.CancelledError:
                pass
        
        logger.info("X stream listener stopped")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get stream listener statistics."""
        return {
            "running": self._running,
            "tweets_received": self._tweets_received,
            "events_emitted": self._events_emitted,
            "last_tweet_at": self._last_tweet_at.isoformat() if self._last_tweet_at else None,
            "reconnect_attempts": self._reconnect_attempts,
            "user_cache_size": len(self._user_cache),
        }


class XMentionPoller:
    """
    Fallback mention polling for when streaming isn't available.
    
    Uses the standard search/tweets endpoint to poll for mentions
    at configurable intervals. Less real-time than streaming but
    works with lower API tiers.
    """
    
    def __init__(
        self,
        bearer_token: str | None = None,
        username: str = "papito_mamito",
        poll_interval: int = 60,  # seconds
        dispatcher: EventDispatcher | None = None,
    ):
        """Initialize the mention poller.
        
        Args:
            bearer_token: X API Bearer token
            username: Papito's username to monitor
            poll_interval: Seconds between polls (default 60)
            dispatcher: EventDispatcher instance
        """
        self.bearer_token = bearer_token or os.getenv("X_BEARER_TOKEN", "")
        self.username = username
        self.poll_interval = poll_interval
        self.dispatcher = dispatcher or get_event_dispatcher()
        
        self._running = False
        self._poll_task: asyncio.Task | None = None
        self._last_tweet_id: str | None = None
        
        # Stats
        self._polls_completed = 0
        self._tweets_found = 0
    
    @property
    def headers(self) -> Dict[str, str]:
        """HTTP headers for X API requests."""
        return {
            "Authorization": f"Bearer {self.bearer_token}",
        }
    
    async def _poll_mentions(self) -> None:
        """Poll for new mentions."""
        search_url = "https://api.twitter.com/2/tweets/search/recent"
        
        params = {
            "query": f"@{self.username} -is:retweet",
            "tweet.fields": "created_at,author_id,conversation_id,referenced_tweets",
            "user.fields": "username,name,public_metrics",
            "expansions": "author_id",
            "max_results": 100,
        }
        
        if self._last_tweet_id:
            params["since_id"] = self._last_tweet_id
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    search_url,
                    headers=self.headers,
                    params=params,
                )
                response.raise_for_status()
                data = response.json()
                
                tweets = data.get("data", [])
                users = {u["id"]: u for u in data.get("includes", {}).get("users", [])}
                
                if tweets:
                    # Update last tweet ID for next poll
                    self._last_tweet_id = tweets[0]["id"]
                    self._tweets_found += len(tweets)
                    
                    # Process tweets (oldest first)
                    for tweet in reversed(tweets):
                        author = users.get(tweet.get("author_id", ""), {})
                        
                        event = Event(
                            type=EventType.MENTION,
                            priority=EventPriority.HIGH,
                            source="x_poll",
                            source_id=tweet.get("id", ""),
                            user_id=tweet.get("author_id", ""),
                            user_name=author.get("username", "unknown"),
                            content=tweet.get("text", ""),
                            metadata={
                                "display_name": author.get("name", ""),
                                "follower_count": author.get("public_metrics", {}).get("followers_count", 0),
                            }
                        )
                        
                        await self.dispatcher.emit(event)
                
                self._polls_completed += 1
                logger.debug(f"Poll completed: {len(tweets)} new mentions")
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                logger.warning("Rate limited on poll, waiting...")
                await asyncio.sleep(60)
            else:
                logger.error(f"Poll HTTP error: {e.response.status_code}")
        except Exception as e:
            logger.exception(f"Poll error: {e}")
    
    async def _poll_loop(self) -> None:
        """Main polling loop."""
        logger.info(f"Starting mention poll loop (interval={self.poll_interval}s)")
        
        while self._running:
            await self._poll_mentions()
            await asyncio.sleep(self.poll_interval)
        
        logger.info("Mention poll loop stopped")
    
    async def start(self) -> bool:
        """Start the mention poller."""
        if self._running:
            return True
        
        if not self.bearer_token:
            logger.error("Cannot start poller: no bearer token")
            return False
        
        self._running = True
        self._poll_task = asyncio.create_task(self._poll_loop())
        
        logger.info("Mention poller started")
        return True
    
    async def stop(self) -> None:
        """Stop the mention poller."""
        self._running = False
        
        if self._poll_task:
            self._poll_task.cancel()
            try:
                await self._poll_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Mention poller stopped")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get poller statistics."""
        return {
            "running": self._running,
            "poll_interval": self.poll_interval,
            "polls_completed": self._polls_completed,
            "tweets_found": self._tweets_found,
            "last_tweet_id": self._last_tweet_id,
        }
