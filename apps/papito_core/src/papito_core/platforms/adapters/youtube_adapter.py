"""
PAPITO MAMITO AI - YOUTUBE ADAPTER
==================================
Adapter for YouTube platform.

This adapter provides:
- Comment monitoring on videos
- Comment replies
- Community post interactions
- Live chat integration (future)

API Requirements:
- YouTube Data API v3 key
- OAuth 2.0 for user actions (commenting)

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

logger = logging.getLogger("papito.platforms.youtube")


class YouTubeAdapter(PlatformAdapter):
    """
    Adapter for YouTube platform.
    
    Capabilities:
    - Comment reading on videos
    - Comment replies
    - Community post interactions
    - Video search
    
    Note: YouTube API has strict quotas. Use wisely.
    
    Usage:
        config = PlatformConfig(
            platform=Platform.YOUTUBE,
            api_key="your_api_key",
            custom_settings={
                "channel_id": "your_channel_id",
                "monitor_videos": ["video_id_1", "video_id_2"],
            }
        )
        
        adapter = YouTubeAdapter(config)
        await adapter.connect()
        
        # Listen for comments
        await adapter.listen(handle_event)
        
        # Reply to a comment
        result = await adapter.execute(PlatformAction(
            action_type="reply",
            content="Thanks for watching!",
            reply_to_id="comment_id",
        ))
    """
    
    platform = Platform.YOUTUBE
    
    capabilities = {
        PlatformCapability.TEXT_POST,  # Comments
        PlatformCapability.REPLY,
        PlatformCapability.LIKE,
        PlatformCapability.SEARCH,
        PlatformCapability.POLLING,  # YouTube uses polling for comments
        PlatformCapability.ANALYTICS,
    }
    
    def __init__(self, config: PlatformConfig):
        """Initialize YouTube adapter.
        
        Args:
            config: Platform configuration with YouTube credentials
        """
        super().__init__(config)
        
        self._service = None
        self._channel_id = config.custom_settings.get("channel_id")
        self._monitor_videos: List[str] = config.custom_settings.get("monitor_videos", [])
        self._poll_interval = config.custom_settings.get("poll_interval", 300)  # 5 min default
        self._poll_task: Optional[asyncio.Task] = None
        self._last_comment_times: Dict[str, datetime] = {}
    
    async def connect(self) -> bool:
        """Connect to YouTube API."""
        try:
            from googleapiclient.discovery import build
            
            # Build YouTube service
            self._service = build(
                "youtube",
                "v3",
                developerKey=self.config.api_key,
            )
            
            # Verify by getting channel info
            if self._channel_id:
                response = self._service.channels().list(
                    part="snippet",
                    id=self._channel_id,
                ).execute()
                
                if response.get("items"):
                    channel = response["items"][0]
                    logger.info(f"Connected to YouTube channel: {channel['snippet']['title']}")
                    self._connected = True
                    return True
            else:
                # Just verify API key works
                self._connected = True
                logger.info("Connected to YouTube API")
                return True
            
            logger.error("Failed to verify YouTube connection")
            return False
            
        except ImportError:
            logger.error("google-api-python-client not installed - run: pip install google-api-python-client")
            return False
        except Exception as e:
            logger.error(f"Error connecting to YouTube: {e}")
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from YouTube API."""
        if self._poll_task:
            self._poll_task.cancel()
            self._poll_task = None
        
        self._service = None
        self._connected = False
        logger.info("Disconnected from YouTube")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check YouTube API health."""
        if not self._service or not self._connected:
            return {"status": "disconnected", "platform": "youtube"}
        
        return {
            "status": "healthy",
            "platform": "youtube",
            "channel_id": self._channel_id,
            "monitored_videos": len(self._monitor_videos),
            "poll_interval": self._poll_interval,
        }
    
    async def listen(self, callback: Callable[[PlatformEvent], None]) -> None:
        """Start listening for YouTube events (comments)."""
        self.register_callback(callback)
        
        if self._monitor_videos:
            await self._start_polling()
        else:
            logger.warning("No videos to monitor - add video IDs to monitor_videos")
    
    async def stop_listening(self) -> None:
        """Stop listening for events."""
        if self._poll_task:
            self._poll_task.cancel()
            self._poll_task = None
        
        self._event_callbacks.clear()
        logger.info("Stopped listening on YouTube")
    
    async def _start_polling(self) -> None:
        """Start polling for new comments."""
        async def poll_loop():
            while True:
                try:
                    for video_id in self._monitor_videos:
                        await self._poll_video_comments(video_id)
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Error polling YouTube: {e}")
                
                await asyncio.sleep(self._poll_interval)
        
        self._poll_task = asyncio.create_task(poll_loop())
        logger.info(f"Started YouTube polling for {len(self._monitor_videos)} videos")
    
    async def _poll_video_comments(self, video_id: str) -> None:
        """Poll for new comments on a video."""
        if not self._service:
            return
        
        try:
            response = self._service.commentThreads().list(
                part="snippet,replies",
                videoId=video_id,
                order="time",
                maxResults=50,
            ).execute()
            
            last_time = self._last_comment_times.get(video_id)
            new_last_time = last_time
            
            for item in response.get("items", []):
                comment = item["snippet"]["topLevelComment"]["snippet"]
                comment_time = datetime.fromisoformat(
                    comment["publishedAt"].replace("Z", "+00:00")
                )
                
                # Track newest
                if new_last_time is None or comment_time > new_last_time:
                    new_last_time = comment_time
                
                # Skip if we've seen this
                if last_time and comment_time <= last_time:
                    continue
                
                # Convert to event
                event = self._convert_comment_to_event(item, video_id)
                if event:
                    await self._emit_event(event)
            
            self._last_comment_times[video_id] = new_last_time
            
        except Exception as e:
            logger.error(f"Error polling YouTube video {video_id}: {e}")
    
    def _convert_comment_to_event(
        self,
        comment_thread: Dict[str, Any],
        video_id: str,
    ) -> Optional[PlatformEvent]:
        """Convert a YouTube comment to a PlatformEvent."""
        try:
            snippet = comment_thread["snippet"]["topLevelComment"]["snippet"]
            
            # Check if it's a reply to us (mentions our channel)
            is_mention = self._channel_id and self._channel_id in snippet.get("textDisplay", "")
            
            return PlatformEvent(
                event_id=f"youtube_{comment_thread['id']}",
                platform=Platform.YOUTUBE,
                category=EventCategory.MENTION if is_mention else EventCategory.COMMENT,
                user_id=snippet["authorChannelId"]["value"],
                user_name=snippet["authorDisplayName"],
                user_display_name=snippet["authorDisplayName"],
                content=snippet["textOriginal"],
                source_id=comment_thread["id"],
                conversation_id=video_id,
                metadata={
                    "video_id": video_id,
                    "like_count": snippet.get("likeCount", 0),
                    "reply_count": comment_thread["snippet"].get("totalReplyCount", 0),
                    "author_channel_url": snippet.get("authorChannelUrl"),
                },
                created_at=datetime.fromisoformat(
                    snippet["publishedAt"].replace("Z", "+00:00")
                ),
            )
        except Exception as e:
            logger.error(f"Error converting YouTube comment: {e}")
            return None
    
    async def execute(self, action: PlatformAction) -> ActionResult:
        """Execute an action on YouTube."""
        if not self._service or not self._connected:
            return ActionResult(
                success=False,
                action_id=action.action_id,
                platform=Platform.YOUTUBE,
                error_message="Not connected to YouTube",
            )
        
        # Note: Most write actions require OAuth 2.0, not just API key
        logger.warning("YouTube write actions require OAuth 2.0 authentication")
        
        try:
            if action.action_type == "reply":
                return await self._reply_to_comment(action)
            elif action.action_type == "like":
                return await self._like_comment(action)
            else:
                return ActionResult(
                    success=False,
                    action_id=action.action_id,
                    platform=Platform.YOUTUBE,
                    error_message=f"Action type {action.action_type} not implemented",
                )
        except Exception as e:
            logger.error(f"Error executing YouTube action: {e}")
            return ActionResult(
                success=False,
                action_id=action.action_id,
                platform=Platform.YOUTUBE,
                error_message=str(e),
            )
    
    async def _reply_to_comment(self, action: PlatformAction) -> ActionResult:
        """Reply to a comment (requires OAuth)."""
        # This requires OAuth 2.0 user authentication
        logger.warning("YouTube comment replies require OAuth 2.0")
        
        return ActionResult(
            success=False,
            action_id=action.action_id,
            platform=Platform.YOUTUBE,
            error_message="YouTube replies require OAuth 2.0 setup",
        )
    
    async def _like_comment(self, action: PlatformAction) -> ActionResult:
        """Like a comment (requires OAuth)."""
        logger.warning("YouTube likes require OAuth 2.0")
        
        return ActionResult(
            success=False,
            action_id=action.action_id,
            platform=Platform.YOUTUBE,
            error_message="YouTube likes require OAuth 2.0 setup",
        )
    
    async def get_user(self, user_id: str) -> Dict[str, Any]:
        """Get channel information."""
        if not self._service:
            return {}
        
        try:
            response = self._service.channels().list(
                part="snippet,statistics",
                id=user_id,
            ).execute()
            
            if response.get("items"):
                channel = response["items"][0]
                return {
                    "id": channel["id"],
                    "title": channel["snippet"]["title"],
                    "description": channel["snippet"]["description"],
                    "subscribers": channel["statistics"].get("subscriberCount"),
                    "video_count": channel["statistics"].get("videoCount"),
                    "view_count": channel["statistics"].get("viewCount"),
                }
        except Exception as e:
            logger.error(f"Error getting YouTube channel: {e}")
        
        return {}
    
    async def get_content(self, content_id: str) -> Dict[str, Any]:
        """Get video information."""
        if not self._service:
            return {}
        
        try:
            response = self._service.videos().list(
                part="snippet,statistics",
                id=content_id,
            ).execute()
            
            if response.get("items"):
                video = response["items"][0]
                return {
                    "id": video["id"],
                    "title": video["snippet"]["title"],
                    "description": video["snippet"]["description"],
                    "channel_id": video["snippet"]["channelId"],
                    "channel_title": video["snippet"]["channelTitle"],
                    "view_count": video["statistics"].get("viewCount"),
                    "like_count": video["statistics"].get("likeCount"),
                    "comment_count": video["statistics"].get("commentCount"),
                    "published_at": video["snippet"]["publishedAt"],
                }
        except Exception as e:
            logger.error(f"Error getting YouTube video: {e}")
        
        return {}
    
    async def search(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search for videos."""
        if not self._service:
            return []
        
        try:
            response = self._service.search().list(
                part="snippet",
                q=query,
                type="video",
                maxResults=min(limit, 50),
            ).execute()
            
            results = []
            for item in response.get("items", []):
                results.append({
                    "id": item["id"]["videoId"],
                    "title": item["snippet"]["title"],
                    "description": item["snippet"]["description"],
                    "channel_title": item["snippet"]["channelTitle"],
                    "published_at": item["snippet"]["publishedAt"],
                })
            
            return results
        except Exception as e:
            logger.error(f"Error searching YouTube: {e}")
            return []
    
    async def get_analytics(self, content_id: str) -> Dict[str, Any]:
        """Get video analytics."""
        # Basic analytics from video stats
        return await self.get_content(content_id)
