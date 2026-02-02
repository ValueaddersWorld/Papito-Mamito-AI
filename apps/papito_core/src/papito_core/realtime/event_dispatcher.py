"""
PAPITO MAMITO AI - EVENT DISPATCHER
===================================
Central event routing system for real-time autonomous operations.

Architecture:
    External Event (mention, trend, webhook)
            │
            ▼
    ┌───────────────────┐
    │  EVENT DISPATCHER │
    │  - Validates      │
    │  - Prioritizes    │
    │  - Routes         │
    └─────────┬─────────┘
              │
    ┌─────────┴─────────┐
    ▼                   ▼
[Handler A]        [Handler B]
(mentions)         (trends)

© 2026 Value Adders World - Entertainment Division
"Add value or don't act."
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, List, Optional

logger = logging.getLogger("papito.events")


class EventType(str, Enum):
    """Types of events Papito can respond to."""
    # Social interactions
    MENTION = "mention"              # Someone mentioned @papito
    REPLY = "reply"                  # Reply to Papito's tweet
    QUOTE = "quote"                  # Quote tweet of Papito
    LIKE = "like"                    # Like on Papito's content
    FOLLOW = "follow"                # New follower
    DM = "dm"                        # Direct message
    
    # Content triggers
    TRENDING_TOPIC = "trending"      # Afrobeat trending topic detected
    VIRAL_CONTENT = "viral"          # Papito's content going viral
    SCHEDULED_POST = "scheduled"     # Time for scheduled content
    
    # External triggers
    WEBHOOK = "webhook"              # External webhook call
    MUSIC_RELEASE = "music_release"  # New track released (Spotify/SoundCloud)
    COLLAB_REQUEST = "collab"        # Collaboration request
    
    # System events
    HEARTBEAT = "heartbeat"          # Regular health check
    ERROR = "error"                  # Error occurred
    STARTUP = "startup"              # System starting up
    SHUTDOWN = "shutdown"            # System shutting down


class EventPriority(int, Enum):
    """Priority levels for event processing."""
    CRITICAL = 1    # Process immediately (errors, viral)
    HIGH = 2        # Process ASAP (mentions, DMs)
    NORMAL = 3      # Standard priority (trends, scheduled)
    LOW = 4         # Process when idle (analytics, cleanup)


@dataclass
class Event:
    """Universal event format for Papito's autonomous system."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: EventType = EventType.HEARTBEAT
    priority: EventPriority = EventPriority.NORMAL
    
    # Event data
    source: str = ""                 # Where the event came from
    source_id: str = ""              # ID from source (tweet_id, user_id, etc.)
    user_id: str = ""                # User who triggered (if applicable)
    user_name: str = ""              # Username
    content: str = ""                # Content of the event
    
    # Timestamps
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    received_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Processing state
    processed: bool = False
    processing_started: datetime | None = None
    processing_completed: datetime | None = None
    result: str = ""
    error: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/storage."""
        return {
            "id": self.id,
            "type": self.type.value,
            "priority": self.priority.value,
            "source": self.source,
            "source_id": self.source_id,
            "user_id": self.user_id,
            "user_name": self.user_name,
            "content": self.content[:200] + "..." if len(self.content) > 200 else self.content,
            "created_at": self.created_at.isoformat(),
            "received_at": self.received_at.isoformat(),
            "processed": self.processed,
            "result": self.result,
            "error": self.error,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        """Create Event from dictionary."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            type=EventType(data.get("type", "heartbeat")),
            priority=EventPriority(data.get("priority", 3)),
            source=data.get("source", ""),
            source_id=data.get("source_id", ""),
            user_id=data.get("user_id", ""),
            user_name=data.get("user_name", ""),
            content=data.get("content", ""),
            metadata=data.get("metadata", {}),
        )


# Type alias for event handlers
EventHandler = Callable[[Event], Awaitable[str]]


class EventDispatcher:
    """
    Central dispatcher for routing events to handlers.
    
    Features:
    - Register handlers for specific event types
    - Priority-based event queue
    - Async event processing
    - Handler timeout protection
    - Event history for debugging
    
    Usage:
        dispatcher = EventDispatcher()
        
        @dispatcher.on(EventType.MENTION)
        async def handle_mention(event: Event) -> str:
            # Process mention
            return "Replied to mention"
        
        # Dispatch event
        await dispatcher.dispatch(Event(type=EventType.MENTION, ...))
    """
    
    def __init__(self, max_history: int = 1000):
        """Initialize the event dispatcher.
        
        Args:
            max_history: Maximum events to keep in history
        """
        self._handlers: Dict[EventType, List[EventHandler]] = {et: [] for et in EventType}
        self._queue: asyncio.PriorityQueue[tuple[int, Event]] = asyncio.PriorityQueue()
        self._running = False
        self._history: List[Event] = []
        self._max_history = max_history
        self._processing_task: asyncio.Task | None = None
        
        # Stats
        self._events_received = 0
        self._events_processed = 0
        self._events_failed = 0
        
        logger.info("EventDispatcher initialized")
    
    def on(self, event_type: EventType):
        """Decorator to register an event handler.
        
        Usage:
            @dispatcher.on(EventType.MENTION)
            async def handle_mention(event: Event) -> str:
                return "processed"
        """
        def decorator(handler: EventHandler):
            self.register_handler(event_type, handler)
            return handler
        return decorator
    
    def register_handler(self, event_type: EventType, handler: EventHandler) -> None:
        """Register a handler for an event type.
        
        Args:
            event_type: Type of event to handle
            handler: Async function that processes the event
        """
        self._handlers[event_type].append(handler)
        logger.info(f"Registered handler for {event_type.value}: {handler.__name__}")
    
    def unregister_handler(self, event_type: EventType, handler: EventHandler) -> bool:
        """Remove a handler from an event type.
        
        Returns:
            True if handler was removed, False if not found
        """
        if handler in self._handlers[event_type]:
            self._handlers[event_type].remove(handler)
            logger.info(f"Unregistered handler for {event_type.value}: {handler.__name__}")
            return True
        return False
    
    async def emit(self, event: Event) -> None:
        """Add an event to the processing queue.
        
        Events are processed by priority (lower number = higher priority).
        
        Args:
            event: The event to process
        """
        self._events_received += 1
        event.received_at = datetime.now(timezone.utc)
        
        # Add to priority queue (priority value, event)
        await self._queue.put((event.priority.value, event))
        
        logger.info(f"Event queued: {event.type.value} (priority={event.priority.name}, id={event.id[:8]})")
    
    async def dispatch(self, event: Event) -> str:
        """Immediately process an event (bypasses queue).
        
        Args:
            event: The event to process immediately
            
        Returns:
            Result string from handler
        """
        return await self._process_event(event)
    
    async def _process_event(self, event: Event) -> str:
        """Process a single event through all registered handlers.
        
        Args:
            event: The event to process
            
        Returns:
            Combined result from all handlers
        """
        handlers = self._handlers.get(event.type, [])
        
        if not handlers:
            logger.warning(f"No handlers for event type: {event.type.value}")
            event.processed = True
            event.result = "no_handlers"
            self._add_to_history(event)
            return "no_handlers"
        
        event.processing_started = datetime.now(timezone.utc)
        results = []
        
        for handler in handlers:
            try:
                # Run handler with timeout (30 seconds default)
                result = await asyncio.wait_for(
                    handler(event),
                    timeout=30.0
                )
                results.append(result)
                logger.info(f"Handler {handler.__name__} completed: {result[:100] if result else 'ok'}")
                
            except asyncio.TimeoutError:
                error_msg = f"Handler {handler.__name__} timed out"
                logger.error(error_msg)
                event.error = error_msg
                self._events_failed += 1
                
            except Exception as e:
                error_msg = f"Handler {handler.__name__} failed: {str(e)}"
                logger.exception(error_msg)
                event.error = error_msg
                self._events_failed += 1
        
        event.processing_completed = datetime.now(timezone.utc)
        event.processed = True
        event.result = " | ".join(filter(None, results))
        
        self._events_processed += 1
        self._add_to_history(event)
        
        return event.result
    
    def _add_to_history(self, event: Event) -> None:
        """Add event to history, maintaining max size."""
        self._history.append(event)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]
    
    async def start(self) -> None:
        """Start the event processing loop."""
        if self._running:
            logger.warning("EventDispatcher already running")
            return
        
        self._running = True
        self._processing_task = asyncio.create_task(self._processing_loop())
        logger.info("EventDispatcher started")
        
        # Emit startup event
        await self.emit(Event(
            type=EventType.STARTUP,
            priority=EventPriority.HIGH,
            source="dispatcher",
            content="Papito EventDispatcher started"
        ))
    
    async def stop(self) -> None:
        """Stop the event processing loop."""
        if not self._running:
            return
        
        # Emit shutdown event
        await self.dispatch(Event(
            type=EventType.SHUTDOWN,
            priority=EventPriority.CRITICAL,
            source="dispatcher",
            content="Papito EventDispatcher shutting down"
        ))
        
        self._running = False
        
        if self._processing_task:
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass
        
        logger.info("EventDispatcher stopped")
    
    async def _processing_loop(self) -> None:
        """Main loop that processes events from the queue."""
        logger.info("Event processing loop started")
        
        while self._running:
            try:
                # Wait for event with timeout (allows checking _running flag)
                try:
                    _, event = await asyncio.wait_for(
                        self._queue.get(),
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                # Process the event
                await self._process_event(event)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception(f"Error in processing loop: {e}")
                await asyncio.sleep(1)  # Prevent tight loop on persistent errors
        
        logger.info("Event processing loop stopped")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get dispatcher statistics."""
        return {
            "running": self._running,
            "queue_size": self._queue.qsize(),
            "events_received": self._events_received,
            "events_processed": self._events_processed,
            "events_failed": self._events_failed,
            "handlers_registered": sum(len(h) for h in self._handlers.values()),
            "history_size": len(self._history),
        }
    
    def get_recent_events(self, limit: int = 10, event_type: EventType | None = None) -> List[Dict[str, Any]]:
        """Get recent events from history.
        
        Args:
            limit: Maximum number of events to return
            event_type: Filter by event type (optional)
            
        Returns:
            List of event dictionaries
        """
        events = self._history
        
        if event_type:
            events = [e for e in events if e.type == event_type]
        
        return [e.to_dict() for e in events[-limit:]]


# Global dispatcher instance (singleton pattern)
_dispatcher: EventDispatcher | None = None


def get_event_dispatcher() -> EventDispatcher:
    """Get the global event dispatcher instance."""
    global _dispatcher
    if _dispatcher is None:
        _dispatcher = EventDispatcher()
    return _dispatcher
