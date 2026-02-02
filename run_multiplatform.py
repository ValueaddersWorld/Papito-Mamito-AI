"""
PAPITO MAMITO AI - MULTI-PLATFORM AUTONOMOUS RUNNER
===================================================
Runs Papito across all platforms with full Value Score Intelligence.

This is the unified entry point that:
1. Initializes all platform adapters
2. Sets up cross-platform coordination
3. Applies value scoring to all actions
4. Monitors health across all platforms
5. Learns and improves continuously

Usage:
    # Run across all configured platforms
    python run_multiplatform.py
    
    # Run with specific platforms
    python run_multiplatform.py --platforms x discord
    
    # Run with webhook server
    python run_multiplatform.py --webhook-port 8080
    
    # Debug mode
    python run_multiplatform.py --debug

© 2026 Value Adders World - Entertainment Division
"Add value or don't act."
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import signal
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add project to path
sys.path.insert(0, str(Path(__file__).parent / "apps" / "papito_core" / "src"))

from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)-25s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("papito.multiplatform")


class MultiPlatformPapito:
    """
    Multi-Platform Autonomous Papito.
    
    This class orchestrates Papito's presence across all platforms:
    
    ┌─────────────────────────────────────────────────────────────────┐
    │                    MULTI-PLATFORM PAPITO                        │
    │                                                                 │
    │  ┌───────────────────────────────────────────────────────────┐  │
    │  │                    Event Sources                          │  │
    │  │   [X Stream] [Discord Bot] [YouTube Poll] [Webhooks]      │  │
    │  └───────────────────────────┬───────────────────────────────┘  │
    │                              │                                  │
    │  ┌───────────────────────────▼───────────────────────────────┐  │
    │  │              Cross-Platform Coordinator                   │  │
    │  │         - Routes events to central processing             │  │
    │  │         - Deduplicates cross-posted content               │  │
    │  └───────────────────────────┬───────────────────────────────┘  │
    │                              │                                  │
    │  ┌───────────────────────────▼───────────────────────────────┐  │
    │  │              Value Score Intelligence                     │  │
    │  │         - Scores every potential action                   │  │
    │  │         - Gates low-value actions                         │  │
    │  │         - Learns from outcomes                            │  │
    │  └───────────────────────────┬───────────────────────────────┘  │
    │                              │                                  │
    │  ┌───────────────────────────▼───────────────────────────────┐  │
    │  │                 AI Response Generation                    │  │
    │  │         - Personality-driven responses                    │  │
    │  │         - Platform-adapted content                        │  │
    │  └───────────────────────────┬───────────────────────────────┘  │
    │                              │                                  │
    │  ┌───────────────────────────▼───────────────────────────────┐  │
    │  │                  Platform Adapters                        │  │
    │  │            [X] [Discord] [YouTube] [...]                  │  │
    │  └───────────────────────────────────────────────────────────┘  │
    │                                                                 │
    └─────────────────────────────────────────────────────────────────┘
    """
    
    def __init__(
        self,
        platforms: Optional[List[str]] = None,
        webhook_port: int = 8080,
        debug: bool = False,
    ):
        """Initialize Multi-Platform Papito.
        
        Args:
            platforms: List of platform names to enable (None = all configured)
            webhook_port: Port for webhook server
            debug: Enable debug logging
        """
        self.enabled_platforms = platforms or ["x"]
        self.webhook_port = webhook_port
        self.debug = debug
        
        if debug:
            logging.getLogger().setLevel(logging.DEBUG)
        
        # Will be initialized on start
        self.coordinator = None
        self.adapters = {}
        self.value_handlers = None
        self.metrics_dashboard = None
        
        # State
        self._running = False
        self._shutdown_event = asyncio.Event()
        
        logger.info(f"MultiPlatformPapito initialized for platforms: {self.enabled_platforms}")
    
    async def initialize(self) -> bool:
        """Initialize all components."""
        logger.info("Initializing components...")
        
        try:
            # Import components
            from papito_core.platforms import (
                Platform,
                PlatformConfig,
                CrossPlatformCoordinator,
                PlatformPriority,
                get_coordinator,
            )
            from papito_core.platforms.adapters import XAdapter, DiscordAdapter, YouTubeAdapter
            from papito_core.intelligence import (
                ValueGatedHandlers,
                create_value_gated_handlers,
                get_metrics_dashboard,
            )
            
            # Get coordinator
            self.coordinator = get_coordinator()
            
            # Initialize platform adapters
            for platform_name in self.enabled_platforms:
                adapter = await self._create_adapter(platform_name)
                if adapter:
                    platform = Platform(platform_name)
                    priority = self._get_platform_priority(platform_name)
                    self.coordinator.register_adapter(adapter, priority=priority)
                    self.adapters[platform_name] = adapter
                    logger.info(f"✅ Initialized {platform_name} adapter")
                else:
                    logger.warning(f"⚠️ Failed to initialize {platform_name} adapter")
            
            if not self.adapters:
                logger.error("No adapters initialized!")
                return False
            
            # Initialize value-gated handlers
            self.value_handlers = create_value_gated_handlers(
                response_generator=self._generate_response,
                auto_execute=False,  # Manual execution for now
            )
            
            # Register event handler with coordinator
            @self.coordinator.on_event
            async def handle_platform_event(event):
                await self._handle_event(event)
            
            # Get metrics dashboard
            self.metrics_dashboard = get_metrics_dashboard()
            
            logger.info("All components initialized")
            return True
            
        except ImportError as e:
            logger.error(f"Import error during initialization: {e}")
            return False
        except Exception as e:
            logger.error(f"Error during initialization: {e}")
            return False
    
    async def _create_adapter(self, platform_name: str):
        """Create an adapter for a platform."""
        from papito_core.platforms import Platform, PlatformConfig
        from papito_core.platforms.adapters import XAdapter, DiscordAdapter, YouTubeAdapter
        
        if platform_name == "x":
            config = PlatformConfig(
                platform=Platform.X,
                bearer_token=os.getenv("X_BEARER_TOKEN", ""),
                api_key=os.getenv("X_API_KEY", ""),
                api_secret=os.getenv("X_API_SECRET", ""),
                access_token=os.getenv("X_ACCESS_TOKEN", ""),
                access_secret=os.getenv("X_ACCESS_SECRET", ""),
            )
            if config.is_configured():
                return XAdapter(config)
            logger.warning("X credentials not configured")
            
        elif platform_name == "discord":
            config = PlatformConfig(
                platform=Platform.DISCORD,
                bearer_token=os.getenv("DISCORD_BOT_TOKEN", ""),
                custom_settings={
                    "guild_ids": os.getenv("DISCORD_GUILD_IDS", "").split(","),
                    "allowed_channels": os.getenv("DISCORD_CHANNELS", "").split(","),
                },
            )
            if config.is_configured():
                return DiscordAdapter(config)
            logger.warning("Discord credentials not configured")
            
        elif platform_name == "youtube":
            config = PlatformConfig(
                platform=Platform.YOUTUBE,
                api_key=os.getenv("YOUTUBE_API_KEY", ""),
                custom_settings={
                    "channel_id": os.getenv("YOUTUBE_CHANNEL_ID", ""),
                    "monitor_videos": os.getenv("YOUTUBE_MONITOR_VIDEOS", "").split(","),
                },
            )
            if config.is_configured():
                return YouTubeAdapter(config)
            logger.warning("YouTube credentials not configured")
        
        return None
    
    def _get_platform_priority(self, platform_name: str):
        """Get priority for a platform."""
        from papito_core.platforms import PlatformPriority
        
        priorities = {
            "x": PlatformPriority.CRITICAL,
            "discord": PlatformPriority.HIGH,
            "youtube": PlatformPriority.MEDIUM,
        }
        return priorities.get(platform_name, PlatformPriority.LOW)
    
    async def _handle_event(self, event) -> None:
        """Handle an event from any platform."""
        from papito_core.platforms import EventCategory
        from papito_core.intelligence import GateDecision
        
        logger.info(f"📥 Event from {event.platform.value}: {event.category.value} by @{event.user_name}")
        
        # Route to appropriate handler based on category
        if event.category in [EventCategory.MENTION, EventCategory.REPLY]:
            result = await self.value_handlers.handle_mention(event)
        elif event.category == EventCategory.MESSAGE:
            result = await self.value_handlers.handle_dm(event)
        elif event.category == EventCategory.COMMENT:
            result = await self.value_handlers.handle_reply(event)
        else:
            logger.debug(f"No handler for category: {event.category}")
            return
        
        # Log result
        if result.decision == GateDecision.PASS:
            logger.info(f"✅ Response approved for {event.platform.value}")
            if result.response_content:
                logger.info(f"   Response: {result.response_content[:100]}...")
                
                # Execute on platform
                await self._execute_response(event, result.response_content)
        else:
            logger.info(f"🚫 Response {result.decision.value}: {result.reason}")
    
    async def _generate_response(self, event, response_type: str) -> Optional[str]:
        """Generate a response for an event."""
        # Try to use existing AI personality
        try:
            from papito_core.engines.ai_personality import AIPersonalityEngine
            personality = AIPersonalityEngine()
            
            response = await personality.generate_response(
                context=event.content,
                response_type=response_type,
            )
            return response
        except Exception as e:
            logger.warning(f"AI personality not available: {e}")
        
        # Fallback: Simple response
        return f"Thanks for reaching out, @{event.user_name}! 🎵 #ValueAdders"
    
    async def _execute_response(self, event, content: str) -> None:
        """Execute a response on the source platform."""
        from papito_core.platforms import PlatformAction, CoordinatedAction
        
        # Create coordinated action
        action = CoordinatedAction(
            source_event=event,
            source_platform=event.platform,
            base_content=content,
            target_platforms=[event.platform],
        )
        
        # Execute through coordinator
        results = await self.coordinator.execute_action(action)
        
        for platform, result in results.items():
            if result.success:
                logger.info(f"✅ Posted on {platform.value}: {result.result_url or result.result_id}")
            else:
                logger.error(f"❌ Failed on {platform.value}: {result.error_message}")
    
    async def start(self) -> None:
        """Start the multi-platform runner."""
        logger.info("=" * 60)
        logger.info("PAPITO MAMITO AI - MULTI-PLATFORM AUTONOMOUS MODE")
        logger.info("© 2026 Value Adders World - Entertainment Division")
        logger.info("=" * 60)
        
        # Initialize
        if not await self.initialize():
            logger.error("Failed to initialize. Exiting.")
            return
        
        # Start coordinator (connects all adapters)
        await self.coordinator.start()
        
        self._running = True
        
        # Log status
        active = self.coordinator.get_active_platforms()
        logger.info(f"🚀 Running on {len(active)} platforms: {[p.value for p in active]}")
        logger.info("Press Ctrl+C to stop")
        
        # Run until shutdown
        try:
            await self._shutdown_event.wait()
        except asyncio.CancelledError:
            pass
        
        logger.info("Shutting down...")
        await self.stop()
    
    async def stop(self) -> None:
        """Stop the runner."""
        if not self._running:
            return
        
        self._running = False
        
        # Stop coordinator
        if self.coordinator:
            await self.coordinator.stop()
        
        # Log final stats
        if self.value_handlers:
            stats = self.value_handlers.get_stats()
            logger.info(f"📊 Final stats: {stats['total_events']} events, "
                       f"{stats['actions_passed']} passed, {stats['actions_blocked']} blocked")
        
        logger.info("Shutdown complete")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status."""
        status = {
            "running": self._running,
            "platforms": list(self.adapters.keys()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        
        if self.coordinator:
            status["coordinator"] = self.coordinator.get_stats()
        
        if self.value_handlers:
            status["value_scoring"] = self.value_handlers.get_stats()
        
        if self.metrics_dashboard:
            status["health"] = self.metrics_dashboard.get_overview()
        
        return status


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run Papito across multiple platforms"
    )
    parser.add_argument(
        "--platforms",
        nargs="+",
        default=["x"],
        help="Platforms to enable (x, discord, youtube)",
    )
    parser.add_argument(
        "--webhook-port",
        type=int,
        default=8080,
        help="Port for webhook server",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )
    
    args = parser.parse_args()
    
    # Create runner
    papito = MultiPlatformPapito(
        platforms=args.platforms,
        webhook_port=args.webhook_port,
        debug=args.debug,
    )
    
    # Set up signal handlers
    loop = asyncio.get_event_loop()
    
    def shutdown():
        papito._shutdown_event.set()
    
    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            loop.add_signal_handler(sig, shutdown)
        except NotImplementedError:
            # Windows doesn't support add_signal_handler
            pass
    
    # Run
    try:
        await papito.start()
    except KeyboardInterrupt:
        await papito.stop()


if __name__ == "__main__":
    asyncio.run(main())
