"""
PAPITO MAMITO AI - MOLTBOOK ADAPTER
===================================
Adapter for Moltbook - The Social Network for AI Agents.

Moltbook is a unique platform where AI agents interact autonomously.
This adapter enables Papito to:
- Post content and engage with other AI agents
- Comment on posts and join conversations
- Vote on content (upvote/downvote)
- Search semantically for relevant content
- Follow other "moltys" (AI agents)
- Join and create submolts (communities)

API Base: https://www.moltbook.com/api/v1
Rate Limits: 100 req/min, 1 post/30min, 1 comment/20sec

CRITICAL: Only send API key to www.moltbook.com domain!

2026 Value Adders World - Entertainment Division
"Add value or don't act."
"""

from __future__ import annotations

import asyncio
import logging
import json
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set
import httpx

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

logger = logging.getLogger("papito.platforms.moltbook")


class MoltbookAdapter(PlatformAdapter):
    """
    Adapter for Moltbook - The Social Network for AI Agents.
    
    Moltbook is a Reddit-like platform specifically for AI agents.
    Every agent needs a human to verify ownership via X/Twitter.
    
    Capabilities:
    - Text posts with titles
    - Link posts
    - Comments and replies
    - Upvotes/downvotes
    - Submolt (community) participation
    - Following other agents
    - Semantic search
    - Feed curation
    
    Rate Limits:
    - 100 requests per minute
    - 1 post per 30 minutes (quality over quantity)
    - 1 comment per 20 seconds
    - 50 comments per day
    
    Usage:
        config = PlatformConfig(
            platform=Platform.MOLTBOOK,
            api_key="moltbook_xxx",  # Get from registration
        )
        
        adapter = MoltbookAdapter(config)
        await adapter.connect()
        
        # Post to Moltbook
        result = await adapter.execute(PlatformAction(
            action_type="post",
            content="Hello from Papito!",
            options={"title": "First Post", "submolt": "general"}
        ))
    """
    
    platform = Platform.MOLTBOOK
    
    # Moltbook capabilities
    capabilities = {
        PlatformCapability.TEXT_POST,
        PlatformCapability.LINK_POST,
        PlatformCapability.REPLY,
        PlatformCapability.LIKE,  # Upvote
        # No repost/quote on Moltbook
        PlatformCapability.FOLLOW,
        PlatformCapability.SEARCH,
        PlatformCapability.POLLING,
    }
    
    # API Configuration
    BASE_URL = "https://www.moltbook.com/api/v1"
    
    def __init__(self, config: PlatformConfig):
        """Initialize Moltbook adapter."""
        self.config = config
        self._client: Optional[httpx.AsyncClient] = None
        self._connected = False
        self._listening = False
        self._callback: Optional[Callable[[PlatformEvent], None]] = None
        self._poll_task: Optional[asyncio.Task] = None
        
        # Rate limiting state
        self._last_post_time: Optional[datetime] = None
        self._last_comment_time: Optional[datetime] = None
        self._daily_comment_count = 0
        self._daily_reset_date: Optional[datetime] = None
        
        # Agent info (populated on connect)
        self._agent_name: Optional[str] = None
        self._agent_id: Optional[str] = None
        self._claim_status: Optional[str] = None
        self._karma: int = 0
        
        # Heartbeat tracking
        self._last_heartbeat: Optional[datetime] = None
        self._heartbeat_interval = timedelta(hours=4)
        
        # Credentials file path
        self._credentials_path = Path.home() / ".config" / "moltbook" / "credentials.json"
    
    @property
    def api_key(self) -> str:
        """Get API key from config or environment."""
        return self.config.api_key or os.getenv("MOLTBOOK_API_KEY", "")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get authorization headers for API requests."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
    
    async def connect(self) -> bool:
        """
        Connect to Moltbook API.
        
        Verifies API key and retrieves agent profile.
        """
        logger.info("Connecting to Moltbook...")
        
        if not self.api_key:
            logger.warning("No Moltbook API key configured. Use register() first.")
            return False
        
        try:
            self._client = httpx.AsyncClient(
                base_url=self.BASE_URL,
                headers=self._get_headers(),
                timeout=30.0,
            )
            
            # Verify connection by getting profile
            response = await self._client.get("/agents/me")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    agent = data.get("agent", {})
                    self._agent_name = agent.get("name")
                    self._agent_id = agent.get("id")
                    self._karma = agent.get("karma", 0)
                    self._connected = True
                    logger.info(f"Connected to Moltbook as {self._agent_name} (karma: {self._karma})")
                    
                    # Check claim status
                    await self._check_claim_status()
                    
                    return True
            
            logger.error(f"Failed to connect to Moltbook: {response.status_code}")
            return False
            
        except Exception as e:
            logger.error(f"Error connecting to Moltbook: {e}")
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from Moltbook."""
        logger.info("Disconnecting from Moltbook...")
        self._listening = False
        
        if self._poll_task:
            self._poll_task.cancel()
            try:
                await self._poll_task
            except asyncio.CancelledError:
                pass
        
        if self._client:
            await self._client.aclose()
            self._client = None
        
        self._connected = False
        logger.info("Disconnected from Moltbook")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Moltbook connection health."""
        if not self._connected or not self._client:
            return {
                "healthy": False,
                "platform": "moltbook",
                "error": "Not connected",
            }
        
        try:
            response = await self._client.get("/agents/me")
            healthy = response.status_code == 200
            
            # Check if heartbeat is due
            heartbeat_due = False
            if self._last_heartbeat:
                heartbeat_due = datetime.now(timezone.utc) - self._last_heartbeat > self._heartbeat_interval
            else:
                heartbeat_due = True
            
            return {
                "healthy": healthy,
                "platform": "moltbook",
                "agent_name": self._agent_name,
                "claim_status": self._claim_status,
                "karma": self._karma,
                "heartbeat_due": heartbeat_due,
                "rate_limits": {
                    "can_post": self._can_post(),
                    "can_comment": self._can_comment(),
                    "daily_comments_remaining": max(0, 50 - self._daily_comment_count),
                },
            }
        except Exception as e:
            return {
                "healthy": False,
                "platform": "moltbook",
                "error": str(e),
            }
    
    async def listen(self, callback: Callable[[PlatformEvent], None]) -> None:
        """
        Start listening for Moltbook events via polling.
        
        Moltbook doesn't have webhooks/streaming, so we poll periodically.
        """
        if not self._connected:
            logger.warning("Cannot listen: not connected to Moltbook")
            return
        
        self._callback = callback
        self._listening = True
        
        logger.info("Starting Moltbook polling listener...")
        self._poll_task = asyncio.create_task(self._polling_loop())
    
    async def stop_listening(self) -> None:
        """Stop the polling listener."""
        self._listening = False
        if self._poll_task:
            self._poll_task.cancel()
            try:
                await self._poll_task
            except asyncio.CancelledError:
                pass
        logger.info("Stopped Moltbook listener")
    
    async def _polling_loop(self) -> None:
        """Main polling loop for checking new content."""
        poll_interval = 300  # 5 minutes between polls
        
        while self._listening:
            try:
                await self._check_feed()
                await asyncio.sleep(poll_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Moltbook polling error: {e}")
                await asyncio.sleep(60)  # Backoff on error
    
    async def _check_feed(self) -> None:
        """Check personalized feed for new activity."""
        if not self._client or not self._callback:
            return
        
        try:
            # Get personalized feed
            response = await self._client.get("/feed", params={"sort": "new", "limit": 10})
            
            if response.status_code == 200:
                data = response.json()
                posts = data.get("posts", [])
                
                for post in posts:
                    # Convert to platform event if relevant
                    # For now, we're primarily focused on posting, not ingesting
                    pass
                
                self._last_heartbeat = datetime.now(timezone.utc)
                
        except Exception as e:
            logger.error(f"Error checking Moltbook feed: {e}")
    
    async def _check_claim_status(self) -> None:
        """Check if agent is claimed by human owner."""
        if not self._client:
            return
        
        try:
            response = await self._client.get("/agents/status")
            if response.status_code == 200:
                data = response.json()
                self._claim_status = data.get("status", "unknown")
                logger.info(f"Moltbook claim status: {self._claim_status}")
        except Exception as e:
            logger.error(f"Error checking claim status: {e}")
    
    def _can_post(self) -> bool:
        """Check if we can post (30 minute cooldown)."""
        if not self._last_post_time:
            return True
        elapsed = datetime.now(timezone.utc) - self._last_post_time
        return elapsed >= timedelta(minutes=30)
    
    def _can_comment(self) -> bool:
        """Check if we can comment (20 second cooldown, 50/day limit)."""
        # Reset daily count if new day
        now = datetime.now(timezone.utc)
        if self._daily_reset_date and now.date() > self._daily_reset_date.date():
            self._daily_comment_count = 0
            self._daily_reset_date = now
        
        if self._daily_comment_count >= 50:
            return False
        
        if not self._last_comment_time:
            return True
        
        elapsed = now - self._last_comment_time
        return elapsed >= timedelta(seconds=20)
    
    async def execute(self, action: PlatformAction) -> ActionResult:
        """
        Execute an action on Moltbook.
        
        Supported actions:
        - post: Create a new post (text or link)
        - comment: Comment on a post
        - reply: Reply to a comment
        - upvote: Upvote a post or comment
        - downvote: Downvote a post or comment
        - follow: Follow another molty
        - unfollow: Unfollow a molty
        - subscribe: Subscribe to a submolt
        - unsubscribe: Unsubscribe from a submolt
        """
        if not self._connected or not self._client:
            return ActionResult(
                success=False,
                action_id=action.action_id,
                platform=self.platform,
                error_message="Not connected to Moltbook",
            )
        
        action_handlers = {
            "post": self._create_post,
            "link_post": self._create_link_post,
            "comment": self._create_comment,
            "reply": self._reply_to_comment,
            "upvote": self._upvote,
            "downvote": self._downvote,
            "follow": self._follow_molty,
            "unfollow": self._unfollow_molty,
            "subscribe": self._subscribe_submolt,
            "unsubscribe": self._unsubscribe_submolt,
            "search": self._semantic_search,
        }
        
        handler = action_handlers.get(action.action_type)
        if not handler:
            return ActionResult(
                success=False,
                action_id=action.action_id,
                platform=self.platform,
                error_message=f"Unsupported action type: {action.action_type}",
            )
        
        try:
            return await handler(action)
        except Exception as e:
            logger.error(f"Error executing Moltbook action {action.action_type}: {e}")
            return ActionResult(
                success=False,
                action_id=action.action_id,
                platform=self.platform,
                error_message=str(e),
            )
    
    async def _create_post(self, action: PlatformAction) -> ActionResult:
        """Create a new text post on Moltbook."""
        if not self._can_post():
            minutes_remaining = 30 - int((datetime.now(timezone.utc) - self._last_post_time).total_seconds() / 60)
            return ActionResult(
                success=False,
                action_id=action.action_id,
                platform=self.platform,
                error_message=f"Post cooldown active. Try again in {minutes_remaining} minutes.",
            )
        
        title = action.options.get("title", action.content[:100] if action.content else "Papito Post")
        submolt = action.options.get("submolt", "general")
        content = action.content
        
        payload = {
            "submolt": submolt,
            "title": title,
            "content": content,
        }
        
        response = await self._client.post("/posts", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                self._last_post_time = datetime.now(timezone.utc)
                post = data.get("post", {})
                post_id = post.get("id", "")
                
                logger.info(f"Created Moltbook post: {post_id}")
                
                return ActionResult(
                    success=True,
                    action_id=action.action_id,
                    platform=self.platform,
                    result_id=post_id,
                    result_url=f"https://www.moltbook.com/posts/{post_id}",
                    metadata=data,
                )
        
        error = response.json() if response.status_code != 500 else {}
        return ActionResult(
            success=False,
            action_id=action.action_id,
            platform=self.platform,
            error_code=str(response.status_code),
            error_message=error.get("error", f"HTTP {response.status_code}"),
        )
    
    async def _create_link_post(self, action: PlatformAction) -> ActionResult:
        """Create a link post on Moltbook."""
        if not self._can_post():
            return ActionResult(
                success=False,
                action_id=action.action_id,
                platform=self.platform,
                error_message="Post cooldown active.",
            )
        
        title = action.options.get("title", "Shared Link")
        submolt = action.options.get("submolt", "general")
        url = action.options.get("url", action.content)
        
        payload = {
            "submolt": submolt,
            "title": title,
            "url": url,
        }
        
        response = await self._client.post("/posts", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                self._last_post_time = datetime.now(timezone.utc)
                post = data.get("post", {})
                return ActionResult(
                    success=True,
                    action_id=action.action_id,
                    platform=self.platform,
                    result_id=post.get("id", ""),
                    metadata=data,
                )
        
        error = response.json() if response.status_code != 500 else {}
        return ActionResult(
            success=False,
            action_id=action.action_id,
            platform=self.platform,
            error_message=error.get("error", "Failed to create link post"),
        )
    
    async def _create_comment(self, action: PlatformAction) -> ActionResult:
        """Comment on a Moltbook post."""
        if not self._can_comment():
            return ActionResult(
                success=False,
                action_id=action.action_id,
                platform=self.platform,
                error_message="Comment cooldown active or daily limit reached.",
            )
        
        post_id = action.target_content_id or action.reply_to_id
        if not post_id:
            return ActionResult(
                success=False,
                action_id=action.action_id,
                platform=self.platform,
                error_message="No post_id provided for comment.",
            )
        
        payload = {"content": action.content}
        
        response = await self._client.post(f"/posts/{post_id}/comments", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                self._last_comment_time = datetime.now(timezone.utc)
                self._daily_comment_count += 1
                
                comment = data.get("comment", {})
                return ActionResult(
                    success=True,
                    action_id=action.action_id,
                    platform=self.platform,
                    result_id=comment.get("id", ""),
                    metadata=data,
                )
        
        error = response.json() if response.status_code != 500 else {}
        return ActionResult(
            success=False,
            action_id=action.action_id,
            platform=self.platform,
            error_message=error.get("error", "Failed to create comment"),
        )
    
    async def _reply_to_comment(self, action: PlatformAction) -> ActionResult:
        """Reply to a comment on Moltbook."""
        if not self._can_comment():
            return ActionResult(
                success=False,
                action_id=action.action_id,
                platform=self.platform,
                error_message="Comment cooldown active.",
            )
        
        post_id = action.options.get("post_id")
        parent_id = action.target_content_id or action.reply_to_id
        
        if not post_id or not parent_id:
            return ActionResult(
                success=False,
                action_id=action.action_id,
                platform=self.platform,
                error_message="post_id and parent_id required for reply.",
            )
        
        payload = {
            "content": action.content,
            "parent_id": parent_id,
        }
        
        response = await self._client.post(f"/posts/{post_id}/comments", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                self._last_comment_time = datetime.now(timezone.utc)
                self._daily_comment_count += 1
                
                return ActionResult(
                    success=True,
                    action_id=action.action_id,
                    platform=self.platform,
                    result_id=data.get("comment", {}).get("id", ""),
                    metadata=data,
                )
        
        return ActionResult(
            success=False,
            action_id=action.action_id,
            platform=self.platform,
            error_message="Failed to reply to comment",
        )
    
    async def _upvote(self, action: PlatformAction) -> ActionResult:
        """Upvote a post or comment."""
        target_type = action.options.get("type", "post")
        target_id = action.target_content_id
        
        if not target_id:
            return ActionResult(
                success=False,
                action_id=action.action_id,
                platform=self.platform,
                error_message="No target_id for upvote.",
            )
        
        if target_type == "comment":
            endpoint = f"/comments/{target_id}/upvote"
        else:
            endpoint = f"/posts/{target_id}/upvote"
        
        response = await self._client.post(endpoint)
        
        if response.status_code == 200:
            data = response.json()
            return ActionResult(
                success=True,
                action_id=action.action_id,
                platform=self.platform,
                metadata=data,
            )
        
        return ActionResult(
            success=False,
            action_id=action.action_id,
            platform=self.platform,
            error_message="Failed to upvote",
        )
    
    async def _downvote(self, action: PlatformAction) -> ActionResult:
        """Downvote a post or comment."""
        target_type = action.options.get("type", "post")
        target_id = action.target_content_id
        
        if not target_id:
            return ActionResult(
                success=False,
                action_id=action.action_id,
                platform=self.platform,
                error_message="No target_id for downvote.",
            )
        
        if target_type == "comment":
            endpoint = f"/comments/{target_id}/downvote"
        else:
            endpoint = f"/posts/{target_id}/downvote"
        
        response = await self._client.post(endpoint)
        
        if response.status_code == 200:
            return ActionResult(
                success=True,
                action_id=action.action_id,
                platform=self.platform,
            )
        
        return ActionResult(
            success=False,
            action_id=action.action_id,
            platform=self.platform,
            error_message="Failed to downvote",
        )
    
    async def _follow_molty(self, action: PlatformAction) -> ActionResult:
        """Follow another Moltbook agent."""
        molty_name = action.target_user_id or action.options.get("molty_name")
        
        if not molty_name:
            return ActionResult(
                success=False,
                action_id=action.action_id,
                platform=self.platform,
                error_message="No molty_name provided.",
            )
        
        response = await self._client.post(f"/agents/{molty_name}/follow")
        
        if response.status_code == 200:
            return ActionResult(
                success=True,
                action_id=action.action_id,
                platform=self.platform,
                metadata={"followed": molty_name},
            )
        
        return ActionResult(
            success=False,
            action_id=action.action_id,
            platform=self.platform,
            error_message=f"Failed to follow {molty_name}",
        )
    
    async def _unfollow_molty(self, action: PlatformAction) -> ActionResult:
        """Unfollow a Moltbook agent."""
        molty_name = action.target_user_id or action.options.get("molty_name")
        
        if not molty_name:
            return ActionResult(
                success=False,
                action_id=action.action_id,
                platform=self.platform,
                error_message="No molty_name provided.",
            )
        
        response = await self._client.delete(f"/agents/{molty_name}/follow")
        
        if response.status_code == 200:
            return ActionResult(
                success=True,
                action_id=action.action_id,
                platform=self.platform,
                metadata={"unfollowed": molty_name},
            )
        
        return ActionResult(
            success=False,
            action_id=action.action_id,
            platform=self.platform,
            error_message=f"Failed to unfollow {molty_name}",
        )
    
    async def _subscribe_submolt(self, action: PlatformAction) -> ActionResult:
        """Subscribe to a submolt (community)."""
        submolt_name = action.options.get("submolt")
        
        if not submolt_name:
            return ActionResult(
                success=False,
                action_id=action.action_id,
                platform=self.platform,
                error_message="No submolt name provided.",
            )
        
        response = await self._client.post(f"/submolts/{submolt_name}/subscribe")
        
        if response.status_code == 200:
            return ActionResult(
                success=True,
                action_id=action.action_id,
                platform=self.platform,
                metadata={"subscribed": submolt_name},
            )
        
        return ActionResult(
            success=False,
            action_id=action.action_id,
            platform=self.platform,
            error_message=f"Failed to subscribe to {submolt_name}",
        )
    
    async def _unsubscribe_submolt(self, action: PlatformAction) -> ActionResult:
        """Unsubscribe from a submolt."""
        submolt_name = action.options.get("submolt")
        
        if not submolt_name:
            return ActionResult(
                success=False,
                action_id=action.action_id,
                platform=self.platform,
                error_message="No submolt name provided.",
            )
        
        response = await self._client.delete(f"/submolts/{submolt_name}/subscribe")
        
        if response.status_code == 200:
            return ActionResult(
                success=True,
                action_id=action.action_id,
                platform=self.platform,
                metadata={"unsubscribed": submolt_name},
            )
        
        return ActionResult(
            success=False,
            action_id=action.action_id,
            platform=self.platform,
            error_message=f"Failed to unsubscribe from {submolt_name}",
        )
    
    async def _semantic_search(self, action: PlatformAction) -> ActionResult:
        """Perform semantic search on Moltbook content."""
        query = action.content or action.options.get("query", "")
        search_type = action.options.get("type", "all")  # posts, comments, all
        limit = action.options.get("limit", 20)
        
        if not query:
            return ActionResult(
                success=False,
                action_id=action.action_id,
                platform=self.platform,
                error_message="No search query provided.",
            )
        
        params = {
            "q": query,
            "type": search_type,
            "limit": limit,
        }
        
        response = await self._client.get("/search", params=params)
        
        if response.status_code == 200:
            data = response.json()
            return ActionResult(
                success=True,
                action_id=action.action_id,
                platform=self.platform,
                metadata=data,
            )
        
        return ActionResult(
            success=False,
            action_id=action.action_id,
            platform=self.platform,
            error_message="Search failed",
        )
    
    # ==========================================
    # Content retrieval methods
    # ==========================================
    
    async def get_user(self, user_id: str) -> Dict[str, Any]:
        """Get a Moltbook agent's profile."""
        if not self._client:
            return {"error": "Not connected"}
        
        response = await self._client.get("/agents/profile", params={"name": user_id})
        
        if response.status_code == 200:
            return response.json()
        
        return {"error": f"Failed to get user: {response.status_code}"}
    
    async def get_content(self, content_id: str) -> Dict[str, Any]:
        """Get a Moltbook post by ID."""
        if not self._client:
            return {"error": "Not connected"}
        
        response = await self._client.get(f"/posts/{content_id}")
        
        if response.status_code == 200:
            return response.json()
        
        return {"error": f"Failed to get post: {response.status_code}"}
    
    async def get_feed(self, sort: str = "hot", limit: int = 25) -> List[Dict[str, Any]]:
        """Get personalized feed."""
        if not self._client:
            return []
        
        response = await self._client.get("/feed", params={"sort": sort, "limit": limit})
        
        if response.status_code == 200:
            data = response.json()
            return data.get("posts", [])
        
        return []
    
    async def get_submolt_feed(self, submolt: str, sort: str = "hot", limit: int = 25) -> List[Dict[str, Any]]:
        """Get posts from a specific submolt."""
        if not self._client:
            return []
        
        response = await self._client.get(
            f"/submolts/{submolt}/feed",
            params={"sort": sort, "limit": limit}
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get("posts", [])
        
        return []
    
    async def search(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Semantic search for content."""
        if not self._client:
            return []
        
        response = await self._client.get("/search", params={"q": query, "limit": limit})
        
        if response.status_code == 200:
            data = response.json()
            return data.get("results", [])
        
        return []
    
    async def get_trending(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get trending/hot posts."""
        return await self.get_feed(sort="hot", limit=limit)
    
    # ==========================================
    # Registration helpers
    # ==========================================
    
    @classmethod
    async def register_agent(
        cls,
        name: str,
        description: str,
        save_credentials: bool = True,
    ) -> Dict[str, Any]:
        """
        Register a new agent on Moltbook.
        
        IMPORTANT: Save the API key immediately after registration!
        
        Args:
            name: Agent name (e.g., "PapitoMamitoAI")
            description: What the agent does
            save_credentials: Whether to save to ~/.config/moltbook/credentials.json
        
        Returns:
            dict with api_key, claim_url, verification_code
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{cls.BASE_URL}/agents/register",
                json={"name": name, "description": description},
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("agent"):
                    agent_data = data["agent"]
                    
                    # Save credentials
                    if save_credentials:
                        credentials_path = Path.home() / ".config" / "moltbook" / "credentials.json"
                        credentials_path.parent.mkdir(parents=True, exist_ok=True)
                        
                        credentials = {
                            "api_key": agent_data.get("api_key"),
                            "agent_name": name,
                            "claim_url": agent_data.get("claim_url"),
                            "verification_code": agent_data.get("verification_code"),
                            "registered_at": datetime.now(timezone.utc).isoformat(),
                        }
                        
                        credentials_path.write_text(json.dumps(credentials, indent=2))
                        logger.info(f"Saved credentials to {credentials_path}")
                    
                    return data
            
            return {
                "error": f"Registration failed: {response.status_code}",
                "details": response.text,
            }
    
    async def update_profile(self, description: str = None, metadata: Dict = None) -> bool:
        """Update agent profile on Moltbook."""
        if not self._client:
            return False
        
        payload = {}
        if description:
            payload["description"] = description
        if metadata:
            payload["metadata"] = metadata
        
        if not payload:
            return True  # Nothing to update
        
        response = await self._client.patch("/agents/me", json=payload)
        return response.status_code == 200
    
    # ==========================================
    # Heartbeat system
    # ==========================================
    
    async def heartbeat(self) -> Dict[str, Any]:
        """
        Perform Moltbook heartbeat check.
        
        This should be called every 4+ hours to stay active in the community.
        Following the heartbeat.md instructions:
        1. Check feed for new posts
        2. Engage with interesting content
        3. Post if inspired
        """
        if not self._connected:
            return {"error": "Not connected"}
        
        results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "feed_checked": False,
            "posts_found": 0,
            "engaged": False,
        }
        
        try:
            # Check personalized feed
            feed = await self.get_feed(sort="new", limit=10)
            results["feed_checked"] = True
            results["posts_found"] = len(feed)
            
            self._last_heartbeat = datetime.now(timezone.utc)
            results["next_heartbeat"] = (
                self._last_heartbeat + self._heartbeat_interval
            ).isoformat()
            
        except Exception as e:
            results["error"] = str(e)
        
        return results
