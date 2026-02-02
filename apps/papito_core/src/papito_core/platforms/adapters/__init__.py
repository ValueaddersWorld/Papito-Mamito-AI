"""
PAPITO MAMITO AI - PLATFORM ADAPTERS
====================================
Concrete implementations for each supported platform.

Each adapter translates Papito's unified actions into platform-specific
API calls, and platform-specific events into unified PlatformEvents.

Available Adapters:
- XAdapter: Twitter/X integration
- DiscordAdapter: Discord bot integration
- YouTubeAdapter: YouTube comments integration
- MoltbookAdapter: Moltbook AI agent social network

Future Adapters:
- InstagramAdapter
- TikTokAdapter

© 2026 Value Adders World - Entertainment Division
"Add value or don't act."
"""

from .x_adapter import XAdapter
from .discord_adapter import DiscordAdapter
from .youtube_adapter import YouTubeAdapter
from .moltbook_adapter import MoltbookAdapter

# Adapter registry
_adapters = {
    "x": XAdapter,
    "discord": DiscordAdapter,
    "youtube": YouTubeAdapter,
    "moltbook": MoltbookAdapter,
}


def get_adapter(platform_name: str):
    """Get adapter class by platform name."""
    return _adapters.get(platform_name.lower())


def register_adapter(platform_name: str, adapter_class):
    """Register a custom adapter."""
    _adapters[platform_name.lower()] = adapter_class


__all__ = [
    "XAdapter",
    "DiscordAdapter",
    "YouTubeAdapter",
    "MoltbookAdapter",
    "get_adapter",
    "register_adapter",
]
