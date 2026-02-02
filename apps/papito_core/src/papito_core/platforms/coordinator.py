"""
PAPITO MAMITO AI - CROSS-PLATFORM COORDINATOR
=============================================
Orchestrates Papito's presence across multiple platforms.

The Coordinator handles:
1. Routing events from all platforms to central processing
2. Coordinating actions across platforms
3. Preventing duplicate responses
4. Managing platform priorities
5. Balancing engagement across platforms

Architecture:

    ┌──────────────────────────────────────────────────────────┐
    │              CROSS-PLATFORM COORDINATOR                  │
    │                                                          │
    │  ┌────────────────────────────────────────────────────┐  │
    │  │              Event Router                          │  │
    │  │  - Receives events from all platforms              │  │
    │  │  - Deduplicates cross-posted content               │  │
    │  │  - Routes to unified event dispatcher              │  │
    │  └───────────────────────┬────────────────────────────┘  │
    │                          │                               │
    │  ┌───────────────────────┴────────────────────────────┐  │
    │  │              Action Orchestrator                   │  │
    │  │  - Decides which platforms to respond on           │  │
    │  │  - Adapts content for each platform                │  │
    │  │  - Coordinates timing across platforms             │  │
    │  └───────────────────────┬────────────────────────────┘  │
    │                          │                               │
    │  ┌───────────────────────┴────────────────────────────┐  │
    │  │              Platform Manager                       │  │
    │  │  - Manages adapter lifecycle                       │  │
    │  │  - Handles rate limiting per platform              │  │
    │  │  - Monitors platform health                        │  │
    │  └────────────────────────────────────────────────────┘  │
    │                                                          │
    └──────────────────────────────────────────────────────────┘

© 2026 Value Adders World - Entertainment Division
"Add value or don't act."
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set
import uuid

from .base import (
    Platform,
    PlatformAdapter,
    PlatformConfig,
    PlatformEvent,
    PlatformAction,
    ActionResult,
    PlatformCapability,
    EventCategory,
)

logger = logging.getLogger("papito.platforms.coordinator")


class PlatformPriority(int, Enum):
    """Priority levels for platforms."""
    CRITICAL = 1     # Must respond (primary platform)
    HIGH = 2         # Should respond if possible
    MEDIUM = 3       # Respond if value is high
    LOW = 4          # Only respond if exceptional
    DISABLED = 99    # Don't respond


@dataclass
class CoordinatedAction:
    """An action that may execute across multiple platforms."""
    action_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    
    # Source
    source_event: Optional[PlatformEvent] = None
    source_platform: Optional[Platform] = None
    
    # Content
    base_content: str = ""
    adapted_content: Dict[Platform, str] = field(default_factory=dict)
    
    # Targeting
    target_platforms: List[Platform] = field(default_factory=list)
    executed_platforms: List[Platform] = field(default_factory=list)
    
    # Results
    results: Dict[Platform, ActionResult] = field(default_factory=dict)
    
    # Metadata
    value_score: float = 0.0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    @property
    def is_complete(self) -> bool:
        """Check if action completed on all target platforms."""
        return set(self.executed_platforms) == set(self.target_platforms)
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate across platforms."""
        if not self.results:
            return 0.0
        successes = sum(1 for r in self.results.values() if r.success)
        return successes / len(self.results)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_id": self.action_id,
            "source_platform": self.source_platform.value if self.source_platform else None,
            "base_content": self.base_content[:100],
            "target_platforms": [p.value for p in self.target_platforms],
            "executed_platforms": [p.value for p in self.executed_platforms],
            "success_rate": self.success_rate,
            "value_score": self.value_score,
        }


@dataclass
class PlatformStats:
    """Statistics for a platform."""
    platform: Platform
    events_received: int = 0
    actions_executed: int = 0
    actions_succeeded: int = 0
    actions_failed: int = 0
    last_event_at: Optional[datetime] = None
    last_action_at: Optional[datetime] = None
    
    @property
    def success_rate(self) -> float:
        total = self.actions_succeeded + self.actions_failed
        if total == 0:
            return 1.0
        return self.actions_succeeded / total


class CrossPlatformCoordinator:
    """
    Coordinates Papito's operations across all platforms.
    
    This is the brain that ensures consistent, value-adding presence
    across X, Discord, YouTube, and any future platforms.
    
    Key responsibilities:
    1. Register and manage platform adapters
    2. Route events from all platforms to central processing
    3. Coordinate responses across platforms
    4. Prevent spam/duplicate responses
    5. Adapt content for each platform's style
    6. Monitor platform health and balance engagement
    
    Usage:
        coordinator = CrossPlatformCoordinator()
        
        # Register platforms
        coordinator.register_adapter(x_adapter, priority=PlatformPriority.CRITICAL)
        coordinator.register_adapter(discord_adapter, priority=PlatformPriority.HIGH)
        
        # Start all platforms
        await coordinator.start()
        
        # Handle events centrally
        @coordinator.on_event
        async def handle_event(event: PlatformEvent):
            # Process event from any platform
            pass
        
        # Execute cross-platform action
        action = CoordinatedAction(
            base_content="Papito says hello!",
            target_platforms=[Platform.X, Platform.DISCORD],
        )
        results = await coordinator.execute_action(action)
    """
    
    def __init__(
        self,
        dedupe_window_minutes: int = 60,
        max_response_per_user_per_hour: int = 5,
    ):
        """Initialize the coordinator.
        
        Args:
            dedupe_window_minutes: Window for detecting duplicate content
            max_response_per_user_per_hour: Rate limit per user
        """
        self.dedupe_window = timedelta(minutes=dedupe_window_minutes)
        self.max_response_per_user = max_response_per_user_per_hour
        
        # Platform management
        self._adapters: Dict[Platform, PlatformAdapter] = {}
        self._priorities: Dict[Platform, PlatformPriority] = {}
        self._configs: Dict[Platform, PlatformConfig] = {}
        
        # Event handling
        self._event_callbacks: List[Callable[[PlatformEvent], Any]] = []
        self._event_history: List[PlatformEvent] = []
        self._content_hashes: Dict[str, datetime] = {}  # For deduplication
        
        # Action tracking
        self._pending_actions: Dict[str, CoordinatedAction] = {}
        self._completed_actions: List[CoordinatedAction] = []
        
        # Rate limiting
        self._user_response_counts: Dict[str, List[datetime]] = defaultdict(list)
        
        # Statistics
        self._stats: Dict[Platform, PlatformStats] = {}
        
        # State
        self._running = False
        self._tasks: List[asyncio.Task] = []
        
        logger.info("CrossPlatformCoordinator initialized")
    
    # === Platform Management ===
    
    def register_adapter(
        self,
        adapter: PlatformAdapter,
        priority: PlatformPriority = PlatformPriority.MEDIUM,
        config: Optional[PlatformConfig] = None,
    ) -> None:
        """Register a platform adapter.
        
        Args:
            adapter: The platform adapter
            priority: Response priority for this platform
            config: Optional additional configuration
        """
        platform = adapter.platform
        
        self._adapters[platform] = adapter
        self._priorities[platform] = priority
        self._stats[platform] = PlatformStats(platform=platform)
        
        if config:
            self._configs[platform] = config
        
        # Set up event routing
        adapter.register_callback(self._route_event)
        
        logger.info(f"Registered {platform.value} adapter with priority {priority.name}")
    
    def unregister_adapter(self, platform: Platform) -> None:
        """Unregister a platform adapter."""
        if platform in self._adapters:
            del self._adapters[platform]
            del self._priorities[platform]
            logger.info(f"Unregistered {platform.value} adapter")
    
    def get_adapter(self, platform: Platform) -> Optional[PlatformAdapter]:
        """Get a registered adapter."""
        return self._adapters.get(platform)
    
    def get_active_platforms(self) -> List[Platform]:
        """Get list of active (connected) platforms."""
        return [
            p for p, a in self._adapters.items()
            if a.is_connected
        ]
    
    # === Lifecycle ===
    
    async def start(self) -> None:
        """Start all registered platform adapters."""
        if self._running:
            logger.warning("Coordinator already running")
            return
        
        logger.info("Starting cross-platform coordinator...")
        
        # Connect all adapters
        for platform, adapter in self._adapters.items():
            try:
                success = await adapter.connect()
                if success:
                    logger.info(f"✅ Connected to {platform.value}")
                    # Start listening
                    await adapter.listen(self._route_event)
                else:
                    logger.error(f"❌ Failed to connect to {platform.value}")
            except Exception as e:
                logger.error(f"❌ Error connecting to {platform.value}: {e}")
        
        self._running = True
        logger.info(f"Coordinator started with {len(self.get_active_platforms())} platforms")
    
    async def stop(self) -> None:
        """Stop all platform adapters."""
        if not self._running:
            return
        
        logger.info("Stopping cross-platform coordinator...")
        
        # Cancel tasks
        for task in self._tasks:
            task.cancel()
        
        # Disconnect adapters
        for platform, adapter in self._adapters.items():
            try:
                await adapter.stop_listening()
                await adapter.disconnect()
                logger.info(f"Disconnected from {platform.value}")
            except Exception as e:
                logger.error(f"Error disconnecting from {platform.value}: {e}")
        
        self._running = False
        logger.info("Coordinator stopped")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of all platforms."""
        health = {
            "status": "healthy" if self._running else "stopped",
            "platforms": {},
            "total_events": len(self._event_history),
            "pending_actions": len(self._pending_actions),
        }
        
        for platform, adapter in self._adapters.items():
            try:
                platform_health = await adapter.health_check()
                health["platforms"][platform.value] = platform_health
            except Exception as e:
                health["platforms"][platform.value] = {
                    "status": "error",
                    "error": str(e),
                }
        
        return health
    
    # === Event Handling ===
    
    def on_event(self, callback: Callable[[PlatformEvent], Any]) -> Callable:
        """Decorator to register an event callback.
        
        Usage:
            @coordinator.on_event
            async def handle_event(event: PlatformEvent):
                print(f"Got event from {event.platform}")
        """
        self._event_callbacks.append(callback)
        return callback
    
    async def _route_event(self, event: PlatformEvent) -> None:
        """Route an event from any platform to central processing."""
        # Check for duplicates
        if self._is_duplicate_content(event):
            logger.debug(f"Skipping duplicate content from {event.platform.value}")
            return
        
        # Update stats
        if event.platform in self._stats:
            self._stats[event.platform].events_received += 1
            self._stats[event.platform].last_event_at = datetime.now(timezone.utc)
        
        # Store in history
        self._event_history.append(event)
        if len(self._event_history) > 1000:
            self._event_history = self._event_history[-500:]
        
        # Emit to callbacks
        for callback in self._event_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                logger.error(f"Error in event callback: {e}")
        
        logger.debug(f"Routed event from {event.platform.value}: {event.category.value}")
    
    def _is_duplicate_content(self, event: PlatformEvent) -> bool:
        """Check if content is a duplicate (cross-posted)."""
        if not event.content:
            return False
        
        content_hash = hashlib.md5(event.content.encode()).hexdigest()[:16]
        
        now = datetime.now(timezone.utc)
        
        # Clean old hashes
        self._content_hashes = {
            h: t for h, t in self._content_hashes.items()
            if now - t < self.dedupe_window
        }
        
        if content_hash in self._content_hashes:
            return True
        
        self._content_hashes[content_hash] = now
        return False
    
    # === Action Execution ===
    
    async def execute_action(self, action: CoordinatedAction) -> Dict[Platform, ActionResult]:
        """Execute an action across target platforms.
        
        Args:
            action: The coordinated action to execute
            
        Returns:
            Results for each target platform
        """
        if not action.target_platforms:
            # Default to source platform if no targets specified
            if action.source_platform:
                action.target_platforms = [action.source_platform]
            else:
                action.target_platforms = self.get_active_platforms()
        
        self._pending_actions[action.action_id] = action
        
        results = {}
        
        for platform in action.target_platforms:
            adapter = self._adapters.get(platform)
            
            if not adapter or not adapter.is_connected:
                logger.warning(f"Skipping {platform.value} - not connected")
                continue
            
            # Check rate limiting
            if action.source_event and not self._check_rate_limit(action.source_event):
                logger.info(f"Rate limited response to user {action.source_event.user_name}")
                continue
            
            # Adapt content for platform
            content = action.adapted_content.get(platform, action.base_content)
            content = self._adapt_content_for_platform(content, platform)
            
            # Create platform-specific action
            platform_action = PlatformAction(
                action_id=f"{action.action_id}_{platform.value}",
                platform=platform,
                action_type="reply" if action.source_event else "post",
                content=content,
                reply_to_id=action.source_event.source_id if action.source_event else "",
                triggered_by_event=action.source_event.event_id if action.source_event else "",
                value_score=action.value_score,
            )
            
            # Execute
            try:
                result = await adapter.execute(platform_action)
                results[platform] = result
                action.results[platform] = result
                action.executed_platforms.append(platform)
                
                # Update stats
                self._stats[platform].actions_executed += 1
                self._stats[platform].last_action_at = datetime.now(timezone.utc)
                
                if result.success:
                    self._stats[platform].actions_succeeded += 1
                    logger.info(f"✅ Action executed on {platform.value}")
                else:
                    self._stats[platform].actions_failed += 1
                    logger.warning(f"❌ Action failed on {platform.value}: {result.error_message}")
                    
            except Exception as e:
                logger.error(f"Error executing action on {platform.value}: {e}")
                results[platform] = ActionResult(
                    success=False,
                    action_id=platform_action.action_id,
                    platform=platform,
                    error_message=str(e),
                )
        
        # Move to completed
        del self._pending_actions[action.action_id]
        self._completed_actions.append(action)
        
        if len(self._completed_actions) > 1000:
            self._completed_actions = self._completed_actions[-500:]
        
        return results
    
    def _adapt_content_for_platform(self, content: str, platform: Platform) -> str:
        """Adapt content for a specific platform.
        
        Args:
            content: Base content
            platform: Target platform
            
        Returns:
            Adapted content
        """
        # Platform-specific adaptations
        if platform == Platform.X:
            # Truncate to 280 chars
            if len(content) > 280:
                content = content[:277] + "..."
        
        elif platform == Platform.DISCORD:
            # Discord allows 2000 chars, add emoji flavor
            pass
        
        elif platform == Platform.YOUTUBE:
            # YouTube comments have different limits
            if len(content) > 500:
                content = content[:497] + "..."
        
        return content
    
    def _check_rate_limit(self, event: PlatformEvent) -> bool:
        """Check if we can respond to a user."""
        user_key = f"{event.platform.value}:{event.user_id}"
        now = datetime.now(timezone.utc)
        hour_ago = now - timedelta(hours=1)
        
        # Clean old entries
        self._user_response_counts[user_key] = [
            t for t in self._user_response_counts[user_key]
            if t > hour_ago
        ]
        
        # Check limit
        if len(self._user_response_counts[user_key]) >= self.max_response_per_user:
            return False
        
        # Record this response
        self._user_response_counts[user_key].append(now)
        return True
    
    # === Query Methods ===
    
    def get_platform_priority(self, platform: Platform) -> PlatformPriority:
        """Get priority for a platform."""
        return self._priorities.get(platform, PlatformPriority.DISABLED)
    
    def set_platform_priority(self, platform: Platform, priority: PlatformPriority) -> None:
        """Set priority for a platform."""
        self._priorities[platform] = priority
        logger.info(f"Set {platform.value} priority to {priority.name}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get coordinator statistics."""
        return {
            "running": self._running,
            "active_platforms": [p.value for p in self.get_active_platforms()],
            "total_events": len(self._event_history),
            "pending_actions": len(self._pending_actions),
            "completed_actions": len(self._completed_actions),
            "platforms": {
                p.value: {
                    "priority": self._priorities[p].name,
                    "events_received": s.events_received,
                    "actions_executed": s.actions_executed,
                    "success_rate": round(s.success_rate * 100, 1),
                }
                for p, s in self._stats.items()
            },
        }
    
    def get_recent_events(self, limit: int = 50, platform: Optional[Platform] = None) -> List[PlatformEvent]:
        """Get recent events, optionally filtered by platform."""
        events = self._event_history
        
        if platform:
            events = [e for e in events if e.platform == platform]
        
        return events[-limit:]
    
    def should_respond_on_platform(
        self,
        platform: Platform,
        value_score: float,
        event: Optional[PlatformEvent] = None,
    ) -> bool:
        """Determine if Papito should respond on a platform.
        
        Args:
            platform: Target platform
            value_score: Value score of proposed response
            event: Source event (if any)
            
        Returns:
            True if should respond
        """
        priority = self.get_platform_priority(platform)
        
        if priority == PlatformPriority.DISABLED:
            return False
        
        if priority == PlatformPriority.CRITICAL:
            return value_score >= 50  # Lower bar for primary platform
        
        if priority == PlatformPriority.HIGH:
            return value_score >= 60
        
        if priority == PlatformPriority.MEDIUM:
            return value_score >= 70
        
        if priority == PlatformPriority.LOW:
            return value_score >= 85  # High bar for secondary platforms
        
        return False


# Global coordinator instance
_coordinator: CrossPlatformCoordinator | None = None


def get_coordinator() -> CrossPlatformCoordinator:
    """Get the global coordinator instance."""
    global _coordinator
    if _coordinator is None:
        _coordinator = CrossPlatformCoordinator()
    return _coordinator
