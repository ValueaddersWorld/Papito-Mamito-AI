"""Firebase/Firestore client for Papito Mamito AI.

This module provides a unified interface for all database operations,
including content queue management, fan interactions, and analytics.
"""

from __future__ import annotations

import json
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

# Lazy import to avoid issues when firebase-admin is not installed
_firebase_admin = None
_firestore = None


def _ensure_firebase():
    """Lazily import firebase-admin modules."""
    global _firebase_admin, _firestore
    if _firebase_admin is None:
        try:
            import firebase_admin
            from firebase_admin import credentials, firestore
            _firebase_admin = firebase_admin
            _firestore = firestore
        except ImportError:
            raise ImportError(
                "firebase-admin is required for database operations. "
                "Install it with: pip install firebase-admin"
            )


# ============== Data Models ==============

class ContentQueueItem(BaseModel):
    """A content item in the publishing queue."""
    
    id: Optional[str] = None
    content_type: str  # "blog", "track_teaser", "fan_shoutout", "gratitude"
    platform: str  # "instagram", "x", "tiktok", "all"
    
    title: str
    body: str
    media_urls: List[str] = []
    hashtags: List[str] = []
    
    formatted: Dict[str, Any] = {}
    
    status: str = "pending_review"  # "pending_review", "approved", "rejected", "published", "failed"
    auto_approve: bool = False
    requires_review: bool = True
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    
    scheduled_at: Optional[datetime] = None
    
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    source_blog_id: Optional[str] = None
    source_track_id: Optional[str] = None


class PublishedContent(BaseModel):
    """Record of published content."""
    
    id: Optional[str] = None
    queue_id: str
    
    platform: str
    platform_post_id: str
    platform_url: str
    
    content_type: str
    title: str
    body: str
    
    metrics: Dict[str, Any] = {}
    metrics_updated_at: Optional[datetime] = None
    
    published_at: Optional[datetime] = None
    created_at: Optional[datetime] = None


class FanInteraction(BaseModel):
    """A fan comment, mention, or DM."""
    
    id: Optional[str] = None
    
    platform: str
    platform_interaction_id: str
    interaction_type: str  # "comment", "mention", "dm", "reply"
    
    post_id: Optional[str] = None
    fan_username: str
    fan_display_name: str
    fan_profile_url: str
    
    message: str
    media_urls: List[str] = []
    
    status: str = "pending"  # "pending", "responding", "responded", "ignored", "flagged"
    response: Optional[str] = None
    response_id: Optional[str] = None
    responded_at: Optional[datetime] = None
    
    sentiment: str = "neutral"  # "positive", "neutral", "negative"
    requires_human: bool = False
    
    received_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ScheduledPost(BaseModel):
    """A scheduled content calendar entry."""
    
    id: Optional[str] = None
    
    scheduled_at: datetime
    timezone: str = "Africa/Lagos"
    recurrence: Optional[str] = None  # "daily", "weekly", None
    
    post_type: str  # "morning_blessing", "afternoon_engagement", "evening_spotlight", "custom"
    
    generation_params: Dict[str, Any] = {}
    content_id: Optional[str] = None
    
    status: str = "scheduled"  # "scheduled", "generating", "ready", "published", "failed"
    last_run_at: Optional[datetime] = None
    
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class PlatformConnection(BaseModel):
    """OAuth connection to a social platform."""
    
    id: str  # Platform name: "instagram", "x", "buffer"
    
    status: str = "disconnected"  # "connected", "disconnected", "expired", "error"
    
    access_token: str
    refresh_token: Optional[str] = None
    token_expires_at: Optional[datetime] = None
    
    platform_user_id: str
    platform_username: str
    
    rate_limit_remaining: Optional[int] = None
    rate_limit_reset_at: Optional[datetime] = None
    
    connected_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class AgentLog(BaseModel):
    """Activity log entry from the autonomous agent."""
    
    id: Optional[str] = None
    
    agent_session_id: str
    
    action: str
    level: str = "info"  # "info", "warning", "error"
    
    message: str
    details: Dict[str, Any] = {}
    
    content_id: Optional[str] = None
    interaction_id: Optional[str] = None
    platform: Optional[str] = None
    
    created_at: Optional[datetime] = None


# ============== Firebase Client ==============

class FirebaseClient:
    """Client for Firebase/Firestore operations.
    
    Provides CRUD operations for all Papito collections:
    - content_queue
    - published_content
    - fan_interactions
    - scheduled_posts
    - platform_connections
    - agent_logs
    - fans
    - analytics_snapshots
    """
    
    # Content types that auto-approve (80% of content)
    AUTO_APPROVE_CONTENT_TYPES = {
        "daily_blessing",
        "morning_blessing",
        "gratitude",
        "fan_shoutout",
        "music_quote",
        "affirmation",
    }
    
    def __init__(self, service_account_path: Optional[str] = None, project_id: Optional[str] = None):
        """Initialize Firebase client.
        
        Args:
            service_account_path: Path to service account JSON file.
                                 If None, uses GOOGLE_APPLICATION_CREDENTIALS env var.
            project_id: Firebase project ID. If None, inferred from credentials.
        """
        _ensure_firebase()
        
        self._initialized = False
        self._db = None
        self._service_account_path = service_account_path
        self._project_id = project_id
        
    def _initialize(self):
        """Lazily initialize Firebase app."""
        if self._initialized:
            return
            
        try:
            # Check if already initialized
            _firebase_admin.get_app()
        except ValueError:
            # Not initialized, do it now
            if self._service_account_path:
                cred = _firebase_admin.credentials.Certificate(self._service_account_path)
                _firebase_admin.initialize_app(cred, {
                    'projectId': self._project_id
                } if self._project_id else None)
            else:
                # Use default credentials (GOOGLE_APPLICATION_CREDENTIALS)
                _firebase_admin.initialize_app()
        
        self._db = _firestore.client()
        self._initialized = True
    
    @property
    def db(self):
        """Get Firestore client instance."""
        self._initialize()
        return self._db
    
    # ============== Content Queue Operations ==============
    
    def add_to_queue(self, item: ContentQueueItem) -> str:
        """Add a content item to the publishing queue.
        
        Returns:
            The document ID of the created item.
        """
        now = datetime.utcnow()
        item.created_at = now
        item.updated_at = now
        
        # Auto-approve logic: 80% of certain content types
        if item.content_type in ("gratitude", "morning_blessing", "fan_shoutout"):
            item.auto_approve = True
            item.requires_review = False
            item.status = "approved"
        
        doc_ref = self.db.collection("content_queue").document()
        doc_ref.set(item.model_dump(exclude={"id"}, exclude_none=True))
        
        return doc_ref.id
    
    def get_queue_item(self, item_id: str) -> Optional[ContentQueueItem]:
        """Get a content queue item by ID."""
        doc = self.db.collection("content_queue").document(item_id).get()
        if not doc.exists:
            return None
        
        data = doc.to_dict()
        data["id"] = doc.id
        return ContentQueueItem(**data)
    
    def get_pending_queue_items(self, limit: int = 50) -> List[ContentQueueItem]:
        """Get items pending review."""
        query = (
            self.db.collection("content_queue")
            .where("status", "==", "pending_review")
            .order_by("created_at")
            .limit(limit)
        )
        
        items = []
        for doc in query.stream():
            data = doc.to_dict()
            data["id"] = doc.id
            items.append(ContentQueueItem(**data))
        
        return items
    
    def get_approved_ready_to_publish(self, limit: int = 20) -> List[ContentQueueItem]:
        """Get approved items ready to publish (scheduled_at <= now)."""
        now = datetime.utcnow()
        
        query = (
            self.db.collection("content_queue")
            .where("status", "==", "approved")
            .where("scheduled_at", "<=", now)
            .order_by("scheduled_at")
            .limit(limit)
        )
        
        items = []
        for doc in query.stream():
            data = doc.to_dict()
            data["id"] = doc.id
            items.append(ContentQueueItem(**data))
        
        return items
    
    def approve_queue_item(self, item_id: str, reviewed_by: str = "system") -> bool:
        """Approve a queue item for publishing."""
        doc_ref = self.db.collection("content_queue").document(item_id)
        doc_ref.update({
            "status": "approved",
            "reviewed_by": reviewed_by,
            "reviewed_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        })
        return True
    
    def reject_queue_item(self, item_id: str, reason: str, reviewed_by: str = "system") -> bool:
        """Reject a queue item."""
        doc_ref = self.db.collection("content_queue").document(item_id)
        doc_ref.update({
            "status": "rejected",
            "rejection_reason": reason,
            "reviewed_by": reviewed_by,
            "reviewed_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        })
        return True
    
    def mark_as_published(self, item_id: str, platform_post_id: str, platform_url: str) -> str:
        """Mark a queue item as published and archive it.
        
        Returns:
            The ID of the published_content record.
        """
        # Get the queue item
        item = self.get_queue_item(item_id)
        if not item:
            raise ValueError(f"Queue item {item_id} not found")
        
        # Update queue item status
        self.db.collection("content_queue").document(item_id).update({
            "status": "published",
            "updated_at": datetime.utcnow(),
        })
        
        # Create published content record
        published = PublishedContent(
            queue_id=item_id,
            platform=item.platform,
            platform_post_id=platform_post_id,
            platform_url=platform_url,
            content_type=item.content_type,
            title=item.title,
            body=item.body,
            published_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
        )
        
        doc_ref = self.db.collection("published_content").document()
        doc_ref.set(published.model_dump(exclude={"id"}, exclude_none=True))
        
        return doc_ref.id
    
    # ============== Fan Interactions Operations ==============
    
    def add_interaction(self, interaction: FanInteraction) -> str:
        """Add a new fan interaction to process."""
        now = datetime.utcnow()
        interaction.created_at = now
        interaction.updated_at = now
        
        doc_ref = self.db.collection("fan_interactions").document()
        doc_ref.set(interaction.model_dump(exclude={"id"}, exclude_none=True))
        
        return doc_ref.id
    
    def get_pending_interactions(self, limit: int = 50) -> List[FanInteraction]:
        """Get interactions awaiting response."""
        query = (
            self.db.collection("fan_interactions")
            .where("status", "==", "pending")
            .order_by("received_at")
            .limit(limit)
        )
        
        items = []
        for doc in query.stream():
            data = doc.to_dict()
            data["id"] = doc.id
            items.append(FanInteraction(**data))
        
        return items
    
    def mark_interaction_responded(
        self, 
        interaction_id: str, 
        response: str, 
        response_id: str
    ) -> bool:
        """Mark an interaction as responded."""
        doc_ref = self.db.collection("fan_interactions").document(interaction_id)
        doc_ref.update({
            "status": "responded",
            "response": response,
            "response_id": response_id,
            "responded_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        })
        return True
    
    # ============== Scheduled Posts Operations ==============
    
    def add_scheduled_post(self, post: ScheduledPost) -> str:
        """Add a new scheduled post."""
        now = datetime.utcnow()
        post.created_at = now
        post.updated_at = now
        
        doc_ref = self.db.collection("scheduled_posts").document()
        doc_ref.set(post.model_dump(exclude={"id"}, exclude_none=True))
        
        return doc_ref.id
    
    def get_due_scheduled_posts(self, limit: int = 20) -> List[ScheduledPost]:
        """Get scheduled posts that are due to run."""
        now = datetime.utcnow()
        
        query = (
            self.db.collection("scheduled_posts")
            .where("status", "==", "scheduled")
            .where("scheduled_at", "<=", now)
            .order_by("scheduled_at")
            .limit(limit)
        )
        
        items = []
        for doc in query.stream():
            data = doc.to_dict()
            data["id"] = doc.id
            items.append(ScheduledPost(**data))
        
        return items
    
    # ============== Platform Connections Operations ==============
    
    def save_platform_connection(self, connection: PlatformConnection) -> bool:
        """Save or update a platform connection."""
        connection.updated_at = datetime.utcnow()
        
        self.db.collection("platform_connections").document(connection.id).set(
            connection.model_dump(exclude_none=True),
            merge=True
        )
        return True
    
    def get_platform_connection(self, platform: str) -> Optional[PlatformConnection]:
        """Get a platform connection by name."""
        doc = self.db.collection("platform_connections").document(platform).get()
        if not doc.exists:
            return None
        
        return PlatformConnection(**doc.to_dict())
    
    def get_all_connected_platforms(self) -> List[PlatformConnection]:
        """Get all connected platforms."""
        query = (
            self.db.collection("platform_connections")
            .where("status", "==", "connected")
        )
        
        items = []
        for doc in query.stream():
            items.append(PlatformConnection(**doc.to_dict()))
        
        return items
    
    # ============== Agent Logs Operations ==============
    
    def log_agent_action(self, log: AgentLog) -> str:
        """Log an agent action."""
        log.created_at = datetime.utcnow()
        
        doc_ref = self.db.collection("agent_logs").document()
        doc_ref.set(log.model_dump(exclude={"id"}, exclude_none=True))
        
        return doc_ref.id
    
    def get_recent_logs(self, limit: int = 100) -> List[AgentLog]:
        """Get recent agent logs."""
        query = (
            self.db.collection("agent_logs")
            .order_by("created_at", direction=_firestore.Query.DESCENDING)
            .limit(limit)
        )
        
        items = []
        for doc in query.stream():
            data = doc.to_dict()
            data["id"] = doc.id
            items.append(AgentLog(**data))
        
        return items
    
    # ============== Queue Statistics ==============
    
    def get_queue_stats(self) -> Dict[str, int]:
        """Get statistics about the content queue."""
        stats = {
            "pending_review": 0,
            "approved": 0,
            "published": 0,
            "rejected": 0,
            "failed": 0,
        }
        
        for status in stats.keys():
            query = (
                self.db.collection("content_queue")
                .where("status", "==", status)
            )
            stats[status] = len(list(query.stream()))
        
        return stats


# ============== Singleton Instance ==============

_client_instance: Optional[FirebaseClient] = None


@lru_cache(maxsize=1)
def get_firebase_client() -> FirebaseClient:
    """Get or create the Firebase client singleton."""
    global _client_instance
    if _client_instance is None:
        from ..settings import get_settings
        settings = get_settings()
        
        # Try to get service account path from settings
        service_account_path = getattr(settings, 'firebase_service_account_path', None)
        project_id = getattr(settings, 'firebase_project_id', None)
        
        _client_instance = FirebaseClient(
            service_account_path=service_account_path,
            project_id=project_id
        )
    
    return _client_instance
