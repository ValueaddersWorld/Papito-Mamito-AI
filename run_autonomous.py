"""
PAPITO MAMITO AI - AUTONOMOUS RUNNER
====================================
Main entry point for running Papito as a truly autonomous agent.

This script initializes and runs all real-time components:
- EventDispatcher: Routes events to handlers
- HeartbeatDaemon: Keeps everything alive
- XStreamListener: Real-time Twitter mentions
- WebhookServer: External trigger endpoints
- Event Handlers: Process mentions, trends, etc.

Usage:
    # Run in foreground
    python run_autonomous.py
    
    # Run with webhook server on custom port
    python run_autonomous.py --port 8080
    
    # Run with polling fallback (if streaming unavailable)
    python run_autonomous.py --poll
    
    # Debug mode
    python run_autonomous.py --debug

© 2026 Value Adders World - Entertainment Division
"Add value or don't act."
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

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
logger = logging.getLogger("papito.runner")

# Import realtime components
from papito_core.realtime import (
    EventDispatcher,
    Event,
    EventType,
    EventPriority,
    HeartbeatDaemon,
    HealthStatus,
)
from papito_core.realtime.x_stream import XStreamListener, XMentionPoller
from papito_core.realtime.webhook_server import webhook_app, run_webhook_server

# Import existing Papito components
try:
    from papito_core.settings import get_settings
    from papito_core.content import AIResponder
    from papito_core.engines.ai_personality import AIPersonalityEngine
    from papito_core.social import XPublisher
    from papito_core.engagement import FanEngagementManager
    from papito_core.memory.interaction_memory import InteractionMemory
    HAS_PAPITO_CORE = True
except ImportError as e:
    logger.warning(f"Some papito_core modules not available: {e}")
    HAS_PAPITO_CORE = False


class AutonomousPapito:
    """
    The Autonomous Papito Mamito Agent.
    
    This class orchestrates all real-time components to make Papito
    truly autonomous - responding to events in real-time rather than
    on a fixed schedule.
    
    Architecture:
        ┌─────────────────────────────────────────────────────┐
        │              AUTONOMOUS PAPITO                      │
        │                                                     │
        │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
        │  │ X Stream    │  │ Webhook     │  │ Scheduler   │ │
        │  │ (mentions)  │  │ Server      │  │ (cron)      │ │
        │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘ │
        │         │                │                │        │
        │         └────────────────┼────────────────┘        │
        │                          ▼                         │
        │              ┌───────────────────┐                 │
        │              │  Event Dispatcher │                 │
        │              └─────────┬─────────┘                 │
        │                        │                           │
        │         ┌──────────────┼──────────────┐            │
        │         ▼              ▼              ▼            │
        │    [Mention]     [Trend]       [Scheduled]         │
        │    Handler       Handler        Handler            │
        │         │              │              │            │
        │         └──────────────┼──────────────┘            │
        │                        ▼                           │
        │              ┌───────────────────┐                 │
        │              │  AI Personality   │                 │
        │              │  + Value Score    │                 │
        │              └─────────┬─────────┘                 │
        │                        │                           │
        │                        ▼                           │
        │              ┌───────────────────┐                 │
        │              │  X Publisher      │                 │
        │              └───────────────────┘                 │
        └─────────────────────────────────────────────────────┘
    """
    
    def __init__(
        self,
        use_streaming: bool = True,
        webhook_port: int = 8080,
        debug: bool = False,
    ):
        """Initialize Autonomous Papito.
        
        Args:
            use_streaming: Use X Filtered Stream (vs polling)
            webhook_port: Port for webhook server
            debug: Enable debug logging
        """
        self.use_streaming = use_streaming
        self.webhook_port = webhook_port
        self.debug = debug
        
        if debug:
            logging.getLogger().setLevel(logging.DEBUG)
        
        # Core components
        self.dispatcher = EventDispatcher()
        self.daemon = HeartbeatDaemon()
        
        # X/Twitter listener
        if use_streaming:
            self.x_listener = XStreamListener(dispatcher=self.dispatcher)
        else:
            self.x_listener = XMentionPoller(
                poll_interval=60,
                dispatcher=self.dispatcher
            )
        
        # Initialize Papito-specific components if available
        if HAS_PAPITO_CORE:
            self.settings = get_settings()
            self.personality = AIPersonalityEngine()
            # self.x_publisher = XPublisher()  # Uncomment when configured
            # self.fan_manager = FanEngagementManager()
            # self.memory = InteractionMemory()
        
        self._webhook_task: asyncio.Task | None = None
        
        logger.info("AutonomousPapito initialized")
    
    def _register_event_handlers(self) -> None:
        """Register all event handlers with the dispatcher."""
        
        @self.dispatcher.on(EventType.MENTION)
        async def handle_mention(event: Event) -> str:
            """Handle Twitter mentions in real-time."""
            logger.info(f"🔔 MENTION from @{event.user_name}: {event.content[:100]}")
            
            # TODO: Integrate with existing AI responder
            # response = await self.generate_response(event)
            # await self.x_publisher.reply(event.source_id, response)
            
            # For now, just log
            return f"Received mention from @{event.user_name}"
        
        @self.dispatcher.on(EventType.REPLY)
        async def handle_reply(event: Event) -> str:
            """Handle replies to Papito's tweets."""
            logger.info(f"💬 REPLY from @{event.user_name}: {event.content[:100]}")
            return f"Received reply from @{event.user_name}"
        
        @self.dispatcher.on(EventType.QUOTE)
        async def handle_quote(event: Event) -> str:
            """Handle quote tweets of Papito."""
            logger.info(f"🔄 QUOTE from @{event.user_name}: {event.content[:100]}")
            return f"Received quote from @{event.user_name}"
        
        @self.dispatcher.on(EventType.TRENDING_TOPIC)
        async def handle_trend(event: Event) -> str:
            """Handle trending topic alerts."""
            trend = event.metadata.get("trend_name", "unknown")
            relevance = event.metadata.get("relevance_score", 0)
            
            logger.info(f"📈 TRENDING: {trend} (relevance={relevance})")
            
            # TODO: Generate trend-related content
            # if relevance > 0.8:
            #     content = await self.generate_trend_content(trend)
            #     await self.x_publisher.post(content)
            
            return f"Processed trend: {trend}"
        
        @self.dispatcher.on(EventType.MUSIC_RELEASE)
        async def handle_music_release(event: Event) -> str:
            """Handle music release notifications."""
            track = event.metadata.get("track_name", "unknown")
            platform = event.metadata.get("platform", "unknown")
            
            logger.info(f"🎵 MUSIC RELEASE: {track} on {platform}")
            
            # TODO: Auto-promote music
            return f"Processed music release: {track}"
        
        @self.dispatcher.on(EventType.WEBHOOK)
        async def handle_webhook(event: Event) -> str:
            """Handle generic webhook events."""
            logger.info(f"🔗 WEBHOOK from {event.source}: {event.content[:100]}")
            return f"Processed webhook from {event.source}"
        
        @self.dispatcher.on(EventType.HEARTBEAT)
        async def handle_heartbeat(event: Event) -> str:
            """Handle heartbeat events (for logging/monitoring)."""
            # Just acknowledge, don't log to avoid spam
            return "heartbeat_ok"
        
        @self.dispatcher.on(EventType.STARTUP)
        async def handle_startup(event: Event) -> str:
            """Handle startup event."""
            logger.info("🚀 PAPITO IS NOW AUTONOMOUS!")
            return "startup_complete"
        
        @self.dispatcher.on(EventType.SHUTDOWN)
        async def handle_shutdown(event: Event) -> str:
            """Handle shutdown event."""
            logger.info("👋 PAPITO SHUTTING DOWN...")
            return "shutdown_initiated"
        
        @self.dispatcher.on(EventType.ERROR)
        async def handle_error(event: Event) -> str:
            """Handle error events."""
            logger.error(f"❌ ERROR: {event.content}")
            # TODO: Send alert to Discord/Telegram
            return "error_logged"
        
        logger.info(f"Registered {sum(len(h) for h in self.dispatcher._handlers.values())} event handlers")
    
    def _register_scheduled_tasks(self) -> None:
        """Register scheduled tasks with the daemon."""
        
        async def post_scheduled_content():
            """Post scheduled content (integrated with ContentScheduler)."""
            logger.info("📅 Running scheduled content task...")
            # TODO: Integrate with existing ContentScheduler
            # await self.content_scheduler.run_cycle()
        
        async def check_trends():
            """Check for relevant trending topics."""
            logger.info("📊 Checking trends...")
            # TODO: Integrate with TrendingDetector
            # trends = await self.trending_detector.get_relevant_trends()
            # for trend in trends:
            #     await self.dispatcher.emit(Event(type=EventType.TRENDING_TOPIC, ...))
        
        async def update_fan_relationships():
            """Update fan relationship tiers."""
            logger.info("👥 Updating fan relationships...")
            # TODO: Integrate with FanEngagementManager
        
        # Register scheduled tasks
        self.daemon.schedule(
            name="scheduled_content",
            func=post_scheduled_content,
            interval_seconds=3600,  # Every hour
        )
        
        self.daemon.schedule(
            name="trend_check",
            func=check_trends,
            interval_seconds=1800,  # Every 30 minutes
        )
        
        self.daemon.schedule(
            name="fan_relationships",
            func=update_fan_relationships,
            interval_seconds=21600,  # Every 6 hours
        )
        
        logger.info("Registered scheduled tasks")
    
    def _register_components(self) -> None:
        """Register components with the daemon for supervision."""
        
        # X Stream/Poller
        self.daemon.register_component(
            name="x_listener",
            start_func=self.x_listener.start,
            stop_func=self.x_listener.stop,
            health_check=lambda: asyncio.coroutine(lambda: self.x_listener._running)(),
        )
        
        # Event Dispatcher
        self.daemon.register_component(
            name="dispatcher",
            start_func=self.dispatcher.start,
            stop_func=self.dispatcher.stop,
            health_check=lambda: asyncio.coroutine(lambda: self.dispatcher._running)(),
        )
        
        logger.info("Registered components with daemon")
    
    async def _run_webhook_server(self) -> None:
        """Run the webhook server in background."""
        import uvicorn
        
        config = uvicorn.Config(
            webhook_app,
            host="0.0.0.0",
            port=self.webhook_port,
            log_level="warning",  # Reduce noise
        )
        server = uvicorn.Server(config)
        
        logger.info(f"Starting webhook server on port {self.webhook_port}")
        await server.serve()
    
    async def run(self) -> None:
        """Run Papito autonomously.
        
        This method blocks until shutdown signal is received.
        """
        logger.info("=" * 60)
        logger.info("    PAPITO MAMITO AI - AUTONOMOUS MODE")
        logger.info("=" * 60)
        logger.info(f"    Streaming: {self.use_streaming}")
        logger.info(f"    Webhook Port: {self.webhook_port}")
        logger.info(f"    Debug: {self.debug}")
        logger.info("=" * 60)
        
        # Register all handlers and components
        self._register_event_handlers()
        self._register_scheduled_tasks()
        self._register_components()
        
        # Start webhook server in background
        self._webhook_task = asyncio.create_task(self._run_webhook_server())
        
        # Run the daemon (blocks until shutdown)
        try:
            await self.daemon.run()
        finally:
            # Cleanup webhook server
            if self._webhook_task:
                self._webhook_task.cancel()
                try:
                    await self._webhook_task
                except asyncio.CancelledError:
                    pass
        
        logger.info("Papito autonomous mode ended")
    
    def get_status(self) -> dict:
        """Get current status of all components."""
        return {
            "daemon": self.daemon.get_status(),
            "dispatcher": self.dispatcher.get_stats(),
            "x_listener": self.x_listener.get_stats(),
            "health": self.daemon.get_health().value,
        }


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run Papito Mamito AI in autonomous mode"
    )
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=8080,
        help="Webhook server port (default: 8080)"
    )
    parser.add_argument(
        "--poll",
        action="store_true",
        help="Use polling instead of streaming (for lower API tiers)"
    )
    parser.add_argument(
        "--debug", "-d",
        action="store_true",
        help="Enable debug logging"
    )
    
    args = parser.parse_args()
    
    # Create and run autonomous Papito
    papito = AutonomousPapito(
        use_streaming=not args.poll,
        webhook_port=args.port,
        debug=args.debug,
    )
    
    try:
        asyncio.run(papito.run())
    except KeyboardInterrupt:
        logger.info("Interrupted by user")


if __name__ == "__main__":
    main()
