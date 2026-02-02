"""
PAPITO MAMITO AI - WEBHOOK SERVER
=================================
FastAPI server for receiving external triggers in real-time.

Endpoints:
- POST /webhooks/x/mentions     - Twitter mention webhook
- POST /webhooks/x/trends       - Trending topic alerts  
- POST /webhooks/music/release  - Music platform releases
- POST /webhooks/custom         - Generic webhook
- GET  /health                  - Health check
- GET  /stats                   - Dispatcher statistics

© 2026 Value Adders World - Entertainment Division
"Add value or don't act."
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, Header, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .event_dispatcher import (
    Event, 
    EventType, 
    EventPriority,
    get_event_dispatcher,
)

logger = logging.getLogger("papito.webhooks")

# ============== Pydantic Models ==============

class WebhookPayload(BaseModel):
    """Generic webhook payload."""
    event_type: str = Field(..., description="Type of event")
    source: str = Field(default="webhook", description="Source identifier")
    source_id: str = Field(default="", description="ID from source system")
    user_id: str = Field(default="", description="User who triggered")
    user_name: str = Field(default="", description="Username")
    content: str = Field(default="", description="Event content/message")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional data")
    priority: str = Field(default="normal", description="Priority: critical, high, normal, low")


class MentionPayload(BaseModel):
    """X/Twitter mention webhook payload."""
    tweet_id: str = Field(..., description="Tweet ID")
    user_id: str = Field(..., description="User ID who mentioned")
    username: str = Field(..., description="Username")
    display_name: str = Field(default="", description="Display name")
    text: str = Field(..., description="Tweet text")
    created_at: str = Field(default="", description="Tweet timestamp")
    in_reply_to: str | None = Field(default=None, description="If this is a reply")
    is_quote: bool = Field(default=False, description="If this is a quote tweet")
    follower_count: int = Field(default=0, description="User's follower count")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TrendPayload(BaseModel):
    """Trending topic webhook payload."""
    trend_name: str = Field(..., description="Trending topic/hashtag")
    volume: int = Field(default=0, description="Tweet volume")
    location: str = Field(default="worldwide", description="Trend location")
    category: str = Field(default="music", description="Topic category")
    relevance_score: float = Field(default=0.0, description="How relevant to Papito")
    suggested_content: str = Field(default="", description="AI-suggested content")


class MusicReleasePayload(BaseModel):
    """Music platform release webhook payload."""
    platform: str = Field(..., description="Platform: spotify, soundcloud, apple_music")
    track_id: str = Field(..., description="Track/album ID")
    track_name: str = Field(default="", description="Track name")
    artist_name: str = Field(default="", description="Artist name")
    release_type: str = Field(default="track", description="track, album, ep")
    url: str = Field(default="", description="Link to the release")


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"
    timestamp: str
    uptime_seconds: float
    version: str = "1.0.0"


class StatsResponse(BaseModel):
    """Statistics response."""
    dispatcher: Dict[str, Any]
    server: Dict[str, Any]


# ============== FastAPI Application ==============

def create_webhook_app() -> FastAPI:
    """Create and configure the webhook FastAPI application."""
    
    app = FastAPI(
        title="Papito Mamito AI - Webhook Server",
        description="Real-time event ingestion for autonomous Papito operations",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Store startup time for uptime calculation
    app.state.startup_time = datetime.now(timezone.utc)
    app.state.requests_received = 0
    app.state.events_emitted = 0
    
    # ============== Utility Functions ==============
    
    def verify_signature(payload: bytes, signature: str, secret: str) -> bool:
        """Verify webhook signature (HMAC-SHA256)."""
        if not secret:
            return True  # Skip verification if no secret configured
        
        expected = hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(f"sha256={expected}", signature)
    
    def priority_from_string(priority: str) -> EventPriority:
        """Convert priority string to EventPriority enum."""
        mapping = {
            "critical": EventPriority.CRITICAL,
            "high": EventPriority.HIGH,
            "normal": EventPriority.NORMAL,
            "low": EventPriority.LOW,
        }
        return mapping.get(priority.lower(), EventPriority.NORMAL)
    
    # ============== Health & Stats Endpoints ==============
    
    @app.get("/health", response_model=HealthResponse, tags=["System"])
    async def health_check():
        """Health check endpoint for monitoring."""
        now = datetime.now(timezone.utc)
        uptime = (now - app.state.startup_time).total_seconds()
        
        return HealthResponse(
            status="healthy",
            timestamp=now.isoformat(),
            uptime_seconds=uptime,
        )
    
    @app.get("/stats", response_model=StatsResponse, tags=["System"])
    async def get_stats():
        """Get server and dispatcher statistics."""
        dispatcher = get_event_dispatcher()
        now = datetime.now(timezone.utc)
        uptime = (now - app.state.startup_time).total_seconds()
        
        return StatsResponse(
            dispatcher=dispatcher.get_stats(),
            server={
                "uptime_seconds": uptime,
                "requests_received": app.state.requests_received,
                "events_emitted": app.state.events_emitted,
            }
        )
    
    @app.get("/events/recent", tags=["Events"])
    async def get_recent_events(limit: int = 20, event_type: str | None = None):
        """Get recent events from dispatcher history."""
        dispatcher = get_event_dispatcher()
        
        et = None
        if event_type:
            try:
                et = EventType(event_type)
            except ValueError:
                raise HTTPException(400, f"Invalid event_type: {event_type}")
        
        return {
            "events": dispatcher.get_recent_events(limit=limit, event_type=et),
            "total_in_history": len(dispatcher._history),
        }
    
    # ============== Webhook Endpoints ==============
    
    @app.post("/webhooks/x/mentions", tags=["X/Twitter"])
    async def x_mention_webhook(
        payload: MentionPayload,
        background_tasks: BackgroundTasks,
        x_signature: str = Header(default="", alias="X-Signature"),
    ):
        """
        Receive X/Twitter mention notifications.
        
        This endpoint is called when someone mentions @papito_mamito.
        The event is queued for processing by the mention handler.
        """
        app.state.requests_received += 1
        
        # Determine event type and priority
        event_type = EventType.MENTION
        priority = EventPriority.HIGH
        
        if payload.is_quote:
            event_type = EventType.QUOTE
        elif payload.in_reply_to:
            event_type = EventType.REPLY
        
        # Higher priority for high-follower accounts
        if payload.follower_count > 10000:
            priority = EventPriority.CRITICAL
        
        # Create event
        event = Event(
            type=event_type,
            priority=priority,
            source="x_twitter",
            source_id=payload.tweet_id,
            user_id=payload.user_id,
            user_name=payload.username,
            content=payload.text,
            metadata={
                "display_name": payload.display_name,
                "in_reply_to": payload.in_reply_to,
                "is_quote": payload.is_quote,
                "follower_count": payload.follower_count,
                "tweet_created_at": payload.created_at,
                **payload.metadata,
            }
        )
        
        # Queue for processing
        dispatcher = get_event_dispatcher()
        background_tasks.add_task(dispatcher.emit, event)
        app.state.events_emitted += 1
        
        logger.info(f"Mention webhook received: @{payload.username} - {payload.text[:50]}...")
        
        return {
            "status": "queued",
            "event_id": event.id,
            "event_type": event.type.value,
            "priority": event.priority.name,
        }
    
    @app.post("/webhooks/x/trends", tags=["X/Twitter"])
    async def x_trend_webhook(
        payload: TrendPayload,
        background_tasks: BackgroundTasks,
    ):
        """
        Receive trending topic alerts.
        
        Called when a relevant Afrobeat/music topic is trending.
        Papito can then create content around the trend.
        """
        app.state.requests_received += 1
        
        # Only process high-relevance trends
        if payload.relevance_score < 0.5:
            return {
                "status": "ignored",
                "reason": "relevance_score too low",
                "score": payload.relevance_score,
            }
        
        event = Event(
            type=EventType.TRENDING_TOPIC,
            priority=EventPriority.NORMAL if payload.relevance_score < 0.8 else EventPriority.HIGH,
            source="x_trends",
            source_id=payload.trend_name,
            content=payload.suggested_content or f"Trending: {payload.trend_name}",
            metadata={
                "trend_name": payload.trend_name,
                "volume": payload.volume,
                "location": payload.location,
                "category": payload.category,
                "relevance_score": payload.relevance_score,
            }
        )
        
        dispatcher = get_event_dispatcher()
        background_tasks.add_task(dispatcher.emit, event)
        app.state.events_emitted += 1
        
        logger.info(f"Trend webhook received: {payload.trend_name} (relevance={payload.relevance_score})")
        
        return {
            "status": "queued",
            "event_id": event.id,
            "trend": payload.trend_name,
        }
    
    @app.post("/webhooks/music/release", tags=["Music"])
    async def music_release_webhook(
        payload: MusicReleasePayload,
        background_tasks: BackgroundTasks,
    ):
        """
        Receive music release notifications.
        
        Called when new music is released on Spotify, SoundCloud, etc.
        Papito can auto-promote or react to releases.
        """
        app.state.requests_received += 1
        
        event = Event(
            type=EventType.MUSIC_RELEASE,
            priority=EventPriority.HIGH,
            source=payload.platform,
            source_id=payload.track_id,
            content=f"New {payload.release_type}: {payload.track_name} by {payload.artist_name}",
            metadata={
                "platform": payload.platform,
                "track_name": payload.track_name,
                "artist_name": payload.artist_name,
                "release_type": payload.release_type,
                "url": payload.url,
            }
        )
        
        dispatcher = get_event_dispatcher()
        background_tasks.add_task(dispatcher.emit, event)
        app.state.events_emitted += 1
        
        logger.info(f"Music release webhook: {payload.track_name} on {payload.platform}")
        
        return {
            "status": "queued",
            "event_id": event.id,
        }
    
    @app.post("/webhooks/custom", tags=["Custom"])
    async def custom_webhook(
        payload: WebhookPayload,
        background_tasks: BackgroundTasks,
        x_webhook_secret: str = Header(default="", alias="X-Webhook-Secret"),
    ):
        """
        Generic webhook for custom integrations.
        
        Supports any event type via the payload.
        """
        app.state.requests_received += 1
        
        # Verify secret if configured
        expected_secret = os.getenv("PAPITO_WEBHOOK_SECRET", "")
        if expected_secret and x_webhook_secret != expected_secret:
            raise HTTPException(401, "Invalid webhook secret")
        
        # Map event type string to enum
        try:
            event_type = EventType(payload.event_type)
        except ValueError:
            event_type = EventType.WEBHOOK
        
        event = Event(
            type=event_type,
            priority=priority_from_string(payload.priority),
            source=payload.source,
            source_id=payload.source_id,
            user_id=payload.user_id,
            user_name=payload.user_name,
            content=payload.content,
            metadata=payload.metadata,
        )
        
        dispatcher = get_event_dispatcher()
        background_tasks.add_task(dispatcher.emit, event)
        app.state.events_emitted += 1
        
        logger.info(f"Custom webhook received: {payload.event_type} from {payload.source}")
        
        return {
            "status": "queued",
            "event_id": event.id,
            "event_type": event.type.value,
        }
    
    # ============== Error Handlers ==============
    
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Global exception handler."""
        logger.exception(f"Unhandled exception: {exc}")
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_server_error",
                "message": str(exc) if os.getenv("DEBUG") else "An error occurred",
            }
        )
    
    return app


# Create default app instance
webhook_app = create_webhook_app()


def run_webhook_server(host: str = "0.0.0.0", port: int = 8080):
    """Run the webhook server standalone."""
    import uvicorn
    
    logger.info(f"Starting webhook server on {host}:{port}")
    uvicorn.run(
        webhook_app,
        host=host,
        port=port,
        log_level="info",
    )


if __name__ == "__main__":
    run_webhook_server()
