"""
PAPITO MAMITO AI - REAL-TIME AUTONOMOUS SYSTEM
==============================================
Phase 1: Event-driven architecture for true autonomy.

Modules:
- event_dispatcher: Central hub routing events to handlers
- webhook_server: FastAPI endpoints for external triggers
- x_stream: Real-time Twitter/X mention monitoring
- heartbeat: Always-on daemon health management

© 2026 Value Adders World - Entertainment Division
"Add value or don't act."
"""

from .event_dispatcher import (
    EventDispatcher,
    Event,
    EventType,
    EventPriority,
    get_event_dispatcher,
)
from .heartbeat import (
    HeartbeatDaemon,
    HealthStatus,
    ComponentStatus,
    get_heartbeat_daemon,
)
from .x_stream import XStreamListener, XMentionPoller
from .webhook_server import webhook_app, create_webhook_app

__all__ = [
    # Event Dispatcher
    "EventDispatcher",
    "Event",
    "EventType",
    "EventPriority",
    "get_event_dispatcher",
    # Heartbeat
    "HeartbeatDaemon",
    "HealthStatus",
    "ComponentStatus",
    "get_heartbeat_daemon",
    # X/Twitter
    "XStreamListener",
    "XMentionPoller",
    # Webhook
    "webhook_app",
    "create_webhook_app",
]
