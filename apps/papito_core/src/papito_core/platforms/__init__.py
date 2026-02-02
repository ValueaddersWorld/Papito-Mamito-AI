"""
PAPITO MAMITO AI - MULTI-PLATFORM MODULE
========================================
Platform-agnostic architecture for true multi-platform autonomy.

Papito can operate across any platform through unified abstractions:

    ┌─────────────────────────────────────────────────────────┐
    │                    PAPITO CORE                          │
    │    ┌─────────────────────────────────────────────┐      │
    │    │          Cross-Platform Coordinator          │      │
    │    └─────────────────────┬───────────────────────┘      │
    │                          │                              │
    │    ┌─────────────────────┴───────────────────────┐      │
    │    │           Platform Abstraction Layer         │      │
    │    └─────────────────────┬───────────────────────┘      │
    │                          │                              │
    └──────────────────────────┼──────────────────────────────┘
                               │
         ┌─────────────────────┼─────────────────────┐
         │                     │                     │
         ▼                     ▼                     ▼
    ┌─────────┐          ┌─────────┐          ┌─────────┐
    │    X    │          │ Discord │          │ YouTube │
    │ Adapter │          │ Adapter │          │ Adapter │
    └─────────┘          └─────────┘          └─────────┘

Supported Platforms:
- X/Twitter: Primary social presence
- Discord: Community engagement
- YouTube: Video comments & community
- Instagram: Visual content (future)
- TikTok: Short-form engagement (future)
- Moltbook: Decentralized social (future)

© 2026 Value Adders World - Entertainment Division
"Add value or don't act."
"""

# Base abstractions
from .base import (
    Platform,
    PlatformConfig,
    PlatformEvent,
    PlatformAction,
    PlatformAdapter,
    PlatformCapability,
)

# Coordinator
from .coordinator import (
    CrossPlatformCoordinator,
    PlatformPriority,
    CoordinatedAction,
    get_coordinator,
)

# Platform adapters
from .adapters import (
    XAdapter,
    DiscordAdapter,
    YouTubeAdapter,
    get_adapter,
    register_adapter,
)

__all__ = [
    # Base
    "Platform",
    "PlatformConfig",
    "PlatformEvent",
    "PlatformAction",
    "PlatformAdapter",
    "PlatformCapability",
    # Coordinator
    "CrossPlatformCoordinator",
    "PlatformPriority",
    "CoordinatedAction",
    "get_coordinator",
    # Adapters
    "XAdapter",
    "DiscordAdapter",
    "YouTubeAdapter",
    "get_adapter",
    "register_adapter",
]
