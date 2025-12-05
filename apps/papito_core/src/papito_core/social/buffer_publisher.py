"""Buffer publisher for scheduling posts across platforms.

Buffer provides a simpler alternative to direct platform APIs,
especially useful as a fallback when platform APIs are unavailable
or for scheduling posts in advance.

Pricing: Buffer's free tier allows 3 connected channels and limited posts.
Paid plans start at $6/month for Essentials.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx

from .base import BasePublisher, Interaction, Platform, PostType, PublishResult
from ..settings import get_settings


class BufferPublisher(BasePublisher):
    """Publisher for Buffer scheduling service.
    
    Buffer allows posting to multiple platforms through a single API:
    - Instagram (Business accounts)
    - X/Twitter
    - Facebook
    - LinkedIn
    - Pinterest
    - And more
    
    This is useful as a fallback when direct platform APIs fail,
    or for scheduling posts in advance.
    """
    
    platform = Platform.BUFFER
    BASE_URL = "https://api.bufferapp.com/1"
    
    def __init__(
        self,
        access_token: Optional[str] = None,
        profile_ids: Optional[List[str]] = None
    ):
        """Initialize Buffer publisher.
        
        Args:
            access_token: Buffer access token
            profile_ids: List of Buffer profile IDs to post to
        """
        settings = get_settings()
        
        self.access_token = access_token or settings.buffer_access_token
        self.profile_ids = profile_ids or settings.buffer_profile_id_list
        
        self._client: Optional[httpx.Client] = None
        self._connected = False
        self._profiles: Dict[str, Any] = {}
    
    def _get_client(self) -> httpx.Client:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.Client(timeout=30.0)
        return self._client
    
    def is_connected(self) -> bool:
        """Check if connected to Buffer API."""
        return self._connected and len(self._profiles) > 0
    
    def connect(self) -> bool:
        """Verify connection to Buffer API and fetch profiles."""
        if not self.access_token:
            return False
        
        try:
            client = self._get_client()
            
            # Get user info
            user_response = client.get(
                f"{self.BASE_URL}/user.json",
                params={"access_token": self.access_token}
            )
            
            if user_response.status_code != 200:
                self._connected = False
                return False
            
            # Get profiles
            profiles_response = client.get(
                f"{self.BASE_URL}/profiles.json",
                params={"access_token": self.access_token}
            )
            
            if profiles_response.status_code == 200:
                profiles = profiles_response.json()
                self._profiles = {p["id"]: p for p in profiles}
                
                # If no profile_ids specified, use all profiles
                if not self.profile_ids:
                    self.profile_ids = list(self._profiles.keys())
                
                self._connected = True
                return True
            else:
                self._connected = False
                return False
                
        except Exception:
            self._connected = False
            return False
    
    def disconnect(self) -> None:
        """Disconnect from Buffer API."""
        self._connected = False
        if self._client:
            self._client.close()
            self._client = None
    
    def get_profiles(self) -> List[Dict[str, Any]]:
        """Get list of connected Buffer profiles.
        
        Returns:
            List of profile info dicts with id, service, etc.
        """
        if not self._connected:
            return []
        
        return [
            {
                "id": p["id"],
                "service": p.get("service"),
                "formatted_username": p.get("formatted_username"),
                "avatar": p.get("avatar"),
            }
            for p in self._profiles.values()
        ]
    
    def publish_post(
        self,
        content: str,
        media_urls: Optional[List[str]] = None,
        post_type: PostType = PostType.TEXT,
        **kwargs
    ) -> PublishResult:
        """Publish immediately or schedule a post via Buffer.
        
        Args:
            content: Post text/caption
            media_urls: Optional media URLs
            post_type: Type of post
            **kwargs: Additional options:
                - scheduled_at: datetime to schedule (None for now)
                - profile_ids: Override default profile IDs
                - shorten_urls: Whether to shorten URLs (default True)
                
        Returns:
            PublishResult with success status
        """
        if not self._connected:
            return PublishResult(
                success=False,
                platform=self.platform,
                error="Not connected to Buffer API"
            )
        
        profiles = kwargs.get("profile_ids", self.profile_ids)
        if not profiles:
            return PublishResult(
                success=False,
                platform=self.platform,
                error="No Buffer profiles specified"
            )
        
        try:
            client = self._get_client()
            
            # Build update parameters
            params: Dict[str, Any] = {
                "access_token": self.access_token,
                "text": content,
                "profile_ids[]": profiles,
                "shorten": kwargs.get("shorten_urls", True),
            }
            
            # Add media if provided
            if media_urls:
                # Buffer accepts up to 4 images or 1 video
                for i, url in enumerate(media_urls[:4]):
                    params[f"media[photo]"] = url
            
            # Schedule or post now
            scheduled_at = kwargs.get("scheduled_at")
            if scheduled_at:
                if isinstance(scheduled_at, datetime):
                    params["scheduled_at"] = int(scheduled_at.timestamp())
                else:
                    params["scheduled_at"] = scheduled_at
            else:
                params["now"] = True
            
            # Create the update
            response = client.post(
                f"{self.BASE_URL}/updates/create.json",
                data=params
            )
            
            if response.status_code == 200:
                data = response.json()
                update = data.get("update", data.get("updates", [{}])[0])
                
                return PublishResult(
                    success=True,
                    platform=self.platform,
                    post_id=update.get("id"),
                    post_url=update.get("service_link"),
                    raw_response=data
                )
            else:
                error_data = response.json() if response.text else {}
                return PublishResult(
                    success=False,
                    platform=self.platform,
                    error=error_data.get("message", f"HTTP {response.status_code}"),
                    raw_response=error_data
                )
                
        except Exception as e:
            return PublishResult(
                success=False,
                platform=self.platform,
                error=str(e)
            )
    
    def schedule_posts(
        self,
        posts: List[Dict[str, Any]],
        profile_ids: Optional[List[str]] = None
    ) -> List[PublishResult]:
        """Schedule multiple posts at once.
        
        Args:
            posts: List of post dicts with 'content', 'scheduled_at', 'media_urls'
            profile_ids: Override default profile IDs
            
        Returns:
            List of PublishResults
        """
        results = []
        
        for post in posts:
            result = self.publish_post(
                content=post.get("content", ""),
                media_urls=post.get("media_urls"),
                scheduled_at=post.get("scheduled_at"),
                profile_ids=profile_ids
            )
            results.append(result)
        
        return results
    
    def get_pending_updates(self, profile_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get pending/scheduled updates for a profile.
        
        Args:
            profile_id: Specific profile or None for first profile
            
        Returns:
            List of pending update dicts
        """
        if not self._connected:
            return []
        
        profile = profile_id or (self.profile_ids[0] if self.profile_ids else None)
        if not profile:
            return []
        
        try:
            client = self._get_client()
            
            response = client.get(
                f"{self.BASE_URL}/profiles/{profile}/updates/pending.json",
                params={
                    "access_token": self.access_token,
                    "count": 100
                }
            )
            
            if response.status_code == 200:
                return response.json().get("updates", [])
            
            return []
            
        except Exception:
            return []
    
    def delete_update(self, update_id: str) -> bool:
        """Delete a pending update.
        
        Args:
            update_id: Buffer update ID
            
        Returns:
            True if successful
        """
        if not self._connected:
            return False
        
        try:
            client = self._get_client()
            
            response = client.post(
                f"{self.BASE_URL}/updates/{update_id}/destroy.json",
                data={"access_token": self.access_token}
            )
            
            return response.status_code == 200
            
        except Exception:
            return False
    
    def reply_to_post(
        self,
        post_id: str,
        content: str,
        **kwargs
    ) -> PublishResult:
        """Buffer doesn't support direct replies.
        
        Use the platform-specific publisher for replies.
        """
        return PublishResult(
            success=False,
            platform=self.platform,
            error="Buffer doesn't support replies - use platform API directly"
        )
    
    def get_interactions(
        self,
        since: Optional[datetime] = None,
        limit: int = 50
    ) -> List[Interaction]:
        """Buffer doesn't support fetching interactions.
        
        Use platform-specific publishers for interactions.
        """
        return []
    
    def like_post(self, post_id: str) -> bool:
        """Buffer doesn't support liking posts."""
        return False
    
    def follow_user(self, username: str) -> bool:
        """Buffer doesn't support following users."""
        return False
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get Buffer analytics for connected profiles."""
        if not self._connected:
            return {}
        
        try:
            metrics = {
                "profiles": [],
                "total_updates_sent": 0,
            }
            
            for profile_id in self.profile_ids:
                profile = self._profiles.get(profile_id, {})
                
                # Get analytics for this profile
                client = self._get_client()
                analytics = client.get(
                    f"{self.BASE_URL}/profiles/{profile_id}/updates/sent.json",
                    params={
                        "access_token": self.access_token,
                        "count": 100
                    }
                )
                
                sent_count = len(analytics.json().get("updates", [])) if analytics.status_code == 200 else 0
                
                metrics["profiles"].append({
                    "id": profile_id,
                    "service": profile.get("service"),
                    "username": profile.get("formatted_username"),
                    "updates_sent": sent_count,
                })
                
                metrics["total_updates_sent"] += sent_count
            
            return metrics
            
        except Exception:
            return {}
