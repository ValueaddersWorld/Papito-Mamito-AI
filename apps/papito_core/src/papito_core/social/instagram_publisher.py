"""Instagram publisher using Meta Graph API.

This module provides Instagram publishing capabilities through the
Meta Business Suite Graph API. Requires an Instagram Business account
connected to a Facebook Page.

Authentication:
- Requires Instagram access token with appropriate permissions
- Permissions needed: instagram_basic, instagram_content_publish,
  instagram_manage_comments, instagram_manage_insights
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
import time

import httpx

from .base import BasePublisher, Interaction, Platform, PostType, PublishResult
from ..settings import get_settings


class InstagramPublisher(BasePublisher):
    """Publisher for Instagram via Meta Graph API.
    
    Supports:
    - Single image posts
    - Carousel posts (up to 10 images)
    - Reels/Videos
    - Reading and replying to comments
    - Fetching mentions
    
    Note: Instagram API does not support Stories via Graph API.
    For Stories, consider using Buffer or another service.
    """
    
    platform = Platform.INSTAGRAM
    BASE_URL = "https://graph.facebook.com/v21.0"
    
    def __init__(
        self,
        access_token: Optional[str] = None,
        business_id: Optional[str] = None
    ):
        """Initialize Instagram publisher.
        
        Args:
            access_token: Instagram Graph API access token.
                         If None, loaded from settings.
            business_id: Instagram Business account ID.
                        If None, loaded from settings.
        """
        settings = get_settings()
        self.access_token = access_token or settings.instagram_access_token
        self.business_id = business_id or settings.instagram_business_id
        self._client = httpx.Client(timeout=30.0)
        self._connected = False
    
    def is_connected(self) -> bool:
        """Check if connected to Instagram API."""
        if not self._connected or not self.access_token:
            return False
        
        try:
            response = self._client.get(
                f"{self.BASE_URL}/me",
                params={"access_token": self.access_token}
            )
            return response.status_code == 200
        except Exception:
            return False
    
    def connect(self) -> bool:
        """Verify connection to Instagram API."""
        if not self.access_token or not self.business_id:
            return False
        
        try:
            # Verify the token and get account info
            response = self._client.get(
                f"{self.BASE_URL}/{self.business_id}",
                params={
                    "fields": "id,username,name,profile_picture_url",
                    "access_token": self.access_token
                }
            )
            
            if response.status_code == 200:
                self._connected = True
                self._account_info = response.json()
                return True
            else:
                self._connected = False
                return False
                
        except Exception as e:
            self._connected = False
            return False
    
    def disconnect(self) -> None:
        """Disconnect from Instagram API."""
        self._connected = False
        self._client.close()
    
    def publish_post(
        self,
        content: str,
        media_urls: Optional[List[str]] = None,
        post_type: PostType = PostType.SINGLE_IMAGE,
        **kwargs
    ) -> PublishResult:
        """Publish a post to Instagram.
        
        Args:
            content: Caption for the post
            media_urls: List of image/video URLs (must be publicly accessible)
            post_type: Type of post (SINGLE_IMAGE, CAROUSEL, VIDEO, REEL)
            **kwargs: Additional options like location_id, user_tags
            
        Returns:
            PublishResult with success status and post details
        """
        if not self._connected:
            return PublishResult(
                success=False,
                platform=self.platform,
                error="Not connected to Instagram API"
            )
        
        if not media_urls:
            return PublishResult(
                success=False,
                platform=self.platform,
                error="Instagram requires at least one media URL"
            )
        
        try:
            if post_type == PostType.CAROUSEL and len(media_urls) > 1:
                return self._publish_carousel(content, media_urls, **kwargs)
            elif post_type in (PostType.VIDEO, PostType.REEL):
                return self._publish_video(content, media_urls[0], is_reel=(post_type == PostType.REEL), **kwargs)
            else:
                return self._publish_single_image(content, media_urls[0], **kwargs)
                
        except Exception as e:
            return PublishResult(
                success=False,
                platform=self.platform,
                error=str(e)
            )
    
    def _publish_single_image(
        self,
        caption: str,
        image_url: str,
        **kwargs
    ) -> PublishResult:
        """Publish a single image post."""
        # Step 1: Create media container
        container_response = self._client.post(
            f"{self.BASE_URL}/{self.business_id}/media",
            params={
                "image_url": image_url,
                "caption": caption,
                "access_token": self.access_token
            }
        )
        
        if container_response.status_code != 200:
            return PublishResult(
                success=False,
                platform=self.platform,
                error=f"Failed to create container: {container_response.text}",
                raw_response=container_response.json()
            )
        
        container_id = container_response.json()["id"]
        
        # Wait for container to be ready
        if not self._wait_for_container(container_id):
            return PublishResult(
                success=False,
                platform=self.platform,
                error="Container processing timed out"
            )
        
        # Step 2: Publish the container
        publish_response = self._client.post(
            f"{self.BASE_URL}/{self.business_id}/media_publish",
            params={
                "creation_id": container_id,
                "access_token": self.access_token
            }
        )
        
        if publish_response.status_code != 200:
            return PublishResult(
                success=False,
                platform=self.platform,
                error=f"Failed to publish: {publish_response.text}",
                raw_response=publish_response.json()
            )
        
        post_id = publish_response.json()["id"]
        
        return PublishResult(
            success=True,
            platform=self.platform,
            post_id=post_id,
            post_url=f"https://www.instagram.com/p/{self._get_shortcode(post_id)}/",
            raw_response=publish_response.json()
        )
    
    def _publish_carousel(
        self,
        caption: str,
        media_urls: List[str],
        **kwargs
    ) -> PublishResult:
        """Publish a carousel post with multiple images."""
        if len(media_urls) > 10:
            return PublishResult(
                success=False,
                platform=self.platform,
                error="Carousel can have maximum 10 items"
            )
        
        # Step 1: Create containers for each item
        child_ids = []
        for url in media_urls:
            is_video = any(ext in url.lower() for ext in ['.mp4', '.mov', '.avi'])
            
            params = {
                "is_carousel_item": "true",
                "access_token": self.access_token
            }
            
            if is_video:
                params["media_type"] = "VIDEO"
                params["video_url"] = url
            else:
                params["image_url"] = url
            
            response = self._client.post(
                f"{self.BASE_URL}/{self.business_id}/media",
                params=params
            )
            
            if response.status_code != 200:
                return PublishResult(
                    success=False,
                    platform=self.platform,
                    error=f"Failed to create carousel item: {response.text}"
                )
            
            child_id = response.json()["id"]
            if not self._wait_for_container(child_id):
                return PublishResult(
                    success=False,
                    platform=self.platform,
                    error=f"Carousel item processing timed out"
                )
            child_ids.append(child_id)
        
        # Step 2: Create carousel container
        carousel_response = self._client.post(
            f"{self.BASE_URL}/{self.business_id}/media",
            params={
                "media_type": "CAROUSEL",
                "caption": caption,
                "children": ",".join(child_ids),
                "access_token": self.access_token
            }
        )
        
        if carousel_response.status_code != 200:
            return PublishResult(
                success=False,
                platform=self.platform,
                error=f"Failed to create carousel: {carousel_response.text}"
            )
        
        container_id = carousel_response.json()["id"]
        
        # Wait for carousel to be ready
        if not self._wait_for_container(container_id):
            return PublishResult(
                success=False,
                platform=self.platform,
                error="Carousel processing timed out"
            )
        
        # Step 3: Publish
        publish_response = self._client.post(
            f"{self.BASE_URL}/{self.business_id}/media_publish",
            params={
                "creation_id": container_id,
                "access_token": self.access_token
            }
        )
        
        if publish_response.status_code != 200:
            return PublishResult(
                success=False,
                platform=self.platform,
                error=f"Failed to publish carousel: {publish_response.text}"
            )
        
        post_id = publish_response.json()["id"]
        
        return PublishResult(
            success=True,
            platform=self.platform,
            post_id=post_id,
            post_url=f"https://www.instagram.com/p/{self._get_shortcode(post_id)}/",
            raw_response=publish_response.json()
        )
    
    def _publish_video(
        self,
        caption: str,
        video_url: str,
        is_reel: bool = False,
        **kwargs
    ) -> PublishResult:
        """Publish a video or reel."""
        params = {
            "video_url": video_url,
            "caption": caption,
            "media_type": "REELS" if is_reel else "VIDEO",
            "access_token": self.access_token
        }
        
        if "cover_url" in kwargs:
            params["cover_url"] = kwargs["cover_url"]
        
        container_response = self._client.post(
            f"{self.BASE_URL}/{self.business_id}/media",
            params=params
        )
        
        if container_response.status_code != 200:
            return PublishResult(
                success=False,
                platform=self.platform,
                error=f"Failed to create video container: {container_response.text}"
            )
        
        container_id = container_response.json()["id"]
        
        # Videos may take longer to process
        if not self._wait_for_container(container_id, max_attempts=60, interval=5):
            return PublishResult(
                success=False,
                platform=self.platform,
                error="Video processing timed out"
            )
        
        publish_response = self._client.post(
            f"{self.BASE_URL}/{self.business_id}/media_publish",
            params={
                "creation_id": container_id,
                "access_token": self.access_token
            }
        )
        
        if publish_response.status_code != 200:
            return PublishResult(
                success=False,
                platform=self.platform,
                error=f"Failed to publish video: {publish_response.text}"
            )
        
        post_id = publish_response.json()["id"]
        
        return PublishResult(
            success=True,
            platform=self.platform,
            post_id=post_id,
            post_url=f"https://www.instagram.com/p/{self._get_shortcode(post_id)}/",
            raw_response=publish_response.json()
        )
    
    def _wait_for_container(
        self,
        container_id: str,
        max_attempts: int = 30,
        interval: int = 2
    ) -> bool:
        """Wait for media container to be ready for publishing."""
        for _ in range(max_attempts):
            response = self._client.get(
                f"{self.BASE_URL}/{container_id}",
                params={
                    "fields": "status_code",
                    "access_token": self.access_token
                }
            )
            
            if response.status_code == 200:
                status = response.json().get("status_code")
                if status == "FINISHED":
                    return True
                elif status == "ERROR":
                    return False
            
            time.sleep(interval)
        
        return False
    
    def _get_shortcode(self, media_id: str) -> str:
        """Get Instagram shortcode from media ID for URL."""
        response = self._client.get(
            f"{self.BASE_URL}/{media_id}",
            params={
                "fields": "shortcode",
                "access_token": self.access_token
            }
        )
        
        if response.status_code == 200:
            return response.json().get("shortcode", media_id)
        return media_id
    
    def reply_to_post(
        self,
        post_id: str,
        content: str,
        **kwargs
    ) -> PublishResult:
        """Reply to a comment on Instagram.
        
        Args:
            post_id: ID of the comment to reply to
            content: Reply text
            
        Returns:
            PublishResult with success status
        """
        if not self._connected:
            return PublishResult(
                success=False,
                platform=self.platform,
                error="Not connected to Instagram API"
            )
        
        try:
            response = self._client.post(
                f"{self.BASE_URL}/{post_id}/replies",
                params={
                    "message": content,
                    "access_token": self.access_token
                }
            )
            
            if response.status_code == 200:
                return PublishResult(
                    success=True,
                    platform=self.platform,
                    post_id=response.json().get("id"),
                    raw_response=response.json()
                )
            else:
                return PublishResult(
                    success=False,
                    platform=self.platform,
                    error=f"Failed to reply: {response.text}"
                )
                
        except Exception as e:
            return PublishResult(
                success=False,
                platform=self.platform,
                error=str(e)
            )
    
    def get_interactions(
        self,
        since: Optional[datetime] = None,
        limit: int = 50
    ) -> List[Interaction]:
        """Fetch recent comments and mentions from Instagram.
        
        Args:
            since: Only fetch interactions after this time
            limit: Maximum number to fetch
            
        Returns:
            List of Interaction objects
        """
        if not self._connected:
            return []
        
        interactions = []
        
        try:
            # Get recent media to check for comments
            media_response = self._client.get(
                f"{self.BASE_URL}/{self.business_id}/media",
                params={
                    "fields": "id,comments{id,text,username,timestamp,from}",
                    "limit": 25,
                    "access_token": self.access_token
                }
            )
            
            if media_response.status_code == 200:
                for media in media_response.json().get("data", []):
                    comments_data = media.get("comments", {}).get("data", [])
                    
                    for comment in comments_data:
                        comment_time = datetime.fromisoformat(
                            comment["timestamp"].replace("Z", "+00:00")
                        )
                        
                        if since and comment_time <= since:
                            continue
                        
                        interactions.append(Interaction(
                            platform=self.platform,
                            interaction_id=comment["id"],
                            interaction_type="comment",
                            post_id=media["id"],
                            username=comment.get("username", ""),
                            display_name=comment.get("from", {}).get("name", ""),
                            profile_url=f"https://instagram.com/{comment.get('username', '')}",
                            message=comment["text"],
                            media_urls=[],
                            created_at=comment_time
                        ))
            
            # Get mentions
            mentions_response = self._client.get(
                f"{self.BASE_URL}/{self.business_id}/tags",
                params={
                    "fields": "id,caption,permalink,timestamp,username",
                    "limit": 25,
                    "access_token": self.access_token
                }
            )
            
            if mentions_response.status_code == 200:
                for mention in mentions_response.json().get("data", []):
                    mention_time = datetime.fromisoformat(
                        mention["timestamp"].replace("Z", "+00:00")
                    )
                    
                    if since and mention_time <= since:
                        continue
                    
                    interactions.append(Interaction(
                        platform=self.platform,
                        interaction_id=mention["id"],
                        interaction_type="mention",
                        post_id=mention["id"],
                        username=mention.get("username", ""),
                        display_name="",
                        profile_url=mention.get("permalink", ""),
                        message=mention.get("caption", ""),
                        media_urls=[],
                        created_at=mention_time
                    ))
                    
        except Exception:
            pass
        
        return interactions[:limit]
    
    def like_post(self, post_id: str) -> bool:
        """Instagram Graph API doesn't support liking posts.
        
        This is a limitation of the official API.
        """
        return False
    
    def follow_user(self, username: str) -> bool:
        """Instagram Graph API doesn't support following users.
        
        This is a limitation of the official API.
        """
        return False
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get Instagram account and content metrics."""
        if not self._connected:
            return {}
        
        try:
            # Account insights
            account_response = self._client.get(
                f"{self.BASE_URL}/{self.business_id}",
                params={
                    "fields": "followers_count,follows_count,media_count,username,name",
                    "access_token": self.access_token
                }
            )
            
            metrics = {}
            
            if account_response.status_code == 200:
                data = account_response.json()
                metrics = {
                    "followers": data.get("followers_count"),
                    "following": data.get("follows_count"),
                    "posts_count": data.get("media_count"),
                    "username": data.get("username"),
                    "name": data.get("name"),
                }
            
            # Get insights for the account
            insights_response = self._client.get(
                f"{self.BASE_URL}/{self.business_id}/insights",
                params={
                    "metric": "impressions,reach,profile_views",
                    "period": "day",
                    "access_token": self.access_token
                }
            )
            
            if insights_response.status_code == 200:
                for insight in insights_response.json().get("data", []):
                    name = insight.get("name")
                    values = insight.get("values", [])
                    if values:
                        metrics[name] = values[0].get("value")
            
            return metrics
            
        except Exception:
            return {}
