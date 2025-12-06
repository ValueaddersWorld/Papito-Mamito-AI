"""Autonomous agent for Papito Mamito AI.

The main orchestration loop that runs continuously to:
- Generate and queue scheduled content
- Publish approved content to social platforms
- Monitor and respond to fan interactions
- Collect analytics
- Log all activities

This agent can run as a standalone process or be integrated
with APScheduler for more sophisticated scheduling.
"""

from __future__ import annotations

import asyncio
import logging
import random
import time
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..content import ContentAdapter, AIResponder
from ..content.ai_responder import ResponseContext
from ..database import get_firebase_client, AgentLog, ContentQueueItem
from ..engines.ai_personality import AIPersonalityEngine, ResponseContext as PersonalityContext
from ..engagement import FanEngagementManager, EngagementTier, Sentiment
from ..queue import ReviewQueue
from ..queue.review_queue import ContentCategory
from ..settings import get_settings
from ..social import InstagramPublisher, XPublisher, BufferPublisher, TrendingDetector
from ..social.base import Platform, PublishResult
from .content_scheduler import ContentScheduler, ContentType


# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("papito.agent")


class AutonomousAgent:
    """The autonomous Papito Mamito agent.
    
    Runs in a continuous loop performing scheduled tasks:
    - Uses ContentScheduler for optimal posting times (6 daily slots)
    - Uses AIPersonalityEngine for consistent Papito voice
    - Uses TrendingDetector for hashtag optimization
    - Hourly comment checking with AI-powered responses
    - Content publishing from review queue
    
    All actions are logged to Firebase for monitoring.
    """
    
    def __init__(
        self,
        session_id: Optional[str] = None,
        debug: bool = False
    ):
        """Initialize the autonomous agent.
        
        Args:
            session_id: Unique session ID (auto-generated if None)
            debug: Enable debug logging
        """
        self.session_id = session_id or str(uuid.uuid4())[:8]
        self.debug = debug
        
        if debug:
            logger.setLevel(logging.DEBUG)
        
        self.settings = get_settings()
        self.db = get_firebase_client()
        
        # Initialize Phase 1 components
        self.scheduler = ContentScheduler()
        self.personality = AIPersonalityEngine(
            openai_api_key=self.settings.openai_api_key,
            anthropic_api_key=self.settings.anthropic_api_key
        )
        self.trending = TrendingDetector()
        
        # Initialize Phase 2 components
        self.fan_engagement = FanEngagementManager(
            openai_api_key=self.settings.openai_api_key,
            db_client=self.db
        )
        
        # Initialize content components
        self.content_adapter = ContentAdapter()
        self.ai_responder = AIResponder()
        self.review_queue = ReviewQueue()
        
        # Initialize publishers (they'll check their own connectivity)
        self.instagram = InstagramPublisher()
        self.x_publisher = XPublisher()
        self.buffer = BufferPublisher()
        
        # Track last run times
        self._last_runs: Dict[str, datetime] = {}
        
        # Running state
        self._running = False
        
        logger.info(f"Agent initialized with session ID: {self.session_id}")
        logger.info(f"ContentScheduler: {len(self.scheduler.config.posting_slots)} daily slots configured")
    
    def log_action(
        self,
        action: str,
        message: str,
        level: str = "info",
        details: Optional[Dict[str, Any]] = None,
        content_id: Optional[str] = None,
        interaction_id: Optional[str] = None,
        platform: Optional[str] = None
    ) -> None:
        """Log an agent action to Firebase.
        
        Args:
            action: Action type (e.g., "post_published")
            message: Human-readable message
            level: Log level ("info", "warning", "error")
            details: Additional context
            content_id: Related content queue ID
            interaction_id: Related interaction ID
            platform: Related platform
        """
        try:
            log = AgentLog(
                agent_session_id=self.session_id,
                action=action,
                level=level,
                message=message,
                details=details or {},
                content_id=content_id,
                interaction_id=interaction_id,
                platform=platform
            )
            self.db.log_agent_action(log)
            
            # Also log locally
            log_fn = getattr(logger, level, logger.info)
            log_fn(f"[{action}] {message}")
            
        except Exception as e:
            logger.error(f"Failed to log action: {e}")
    
    def start(self, interval_seconds: int = 60) -> None:
        """Start the autonomous agent loop.
        
        Args:
            interval_seconds: Seconds between each loop iteration
        """
        self._running = True
        self.log_action("agent_started", f"Agent started (interval: {interval_seconds}s)")
        
        try:
            while self._running:
                self._run_iteration()
                time.sleep(interval_seconds)
                
        except KeyboardInterrupt:
            self.log_action("agent_stopped", "Agent stopped by user")
            self._running = False
            
        except Exception as e:
            self.log_action(
                "agent_error",
                f"Agent crashed: {str(e)}",
                level="error",
                details={"error": str(e)}
            )
            raise
    
    def stop(self) -> None:
        """Stop the autonomous agent."""
        self._running = False
        self.log_action("agent_stopped", "Agent stop requested")
    
    def _run_iteration(self) -> None:
        """Run one iteration of the agent loop."""
        # Check if it's time to post based on scheduler
        posting_slot = self.scheduler.should_post_now(tolerance_minutes=10)
        
        if posting_slot and self._should_run(f"slot_{posting_slot.hour}", minutes=90):
            # Generate content for this slot
            content_type = self.scheduler.select_content_type(posting_slot)
            self._generate_scheduled_content(content_type, posting_slot.platforms)
        
        # Publish approved content
        self._publish_ready_content()
        
        # Check for fan interactions (hourly)
        if self._should_run("check_interactions", minutes=60):
            self._check_and_respond_to_interactions()
        
        # Collect analytics (every 4 hours)
        if self._should_run("collect_analytics", minutes=240):
            self._collect_analytics()
    
    def _should_run(self, task: str, minutes: int) -> bool:
        """Check if a task should run based on last run time.
        
        Args:
            task: Task identifier
            minutes: Minimum minutes between runs
            
        Returns:
            True if task should run
        """
        now = datetime.utcnow()
        last_run = self._last_runs.get(task)
        
        if last_run is None or (now - last_run) >= timedelta(minutes=minutes):
            self._last_runs[task] = now
            return True
        
        return False
    
    def _generate_scheduled_content(
        self, 
        content_type: ContentType, 
        platforms: List[str]
    ) -> None:
        """Generate and queue content based on scheduler's content type.
        
        Uses AIPersonalityEngine for consistent voice and TrendingDetector
        for optimized hashtags.
        
        Args:
            content_type: Type of content from ContentScheduler
            platforms: List of platforms to target
        """
        self.log_action(
            "generating_content", 
            f"Generating {content_type.value} content",
            details={"platforms": platforms, "content_type": content_type.value}
        )
        
        # Get AI-generated content from personality engine
        content_data = self.personality.generate_content_post(
            content_type=content_type.value,
            platform=platforms[0] if platforms else "x",
        )
        
        # Get relevant hashtags from trending detector
        hashtags = self.trending.get_relevant_hashtags_for_content(
            content_type=content_type.value,
            max_hashtags=5,
            include_core=True
        )
        
        # Map content types to categories
        category_map = {
            ContentType.MORNING_BLESSING: ContentCategory.DAILY_BLESSING,
            ContentType.MUSIC_WISDOM: ContentCategory.AFFIRMATION,
            ContentType.TRACK_SNIPPET: ContentCategory.MUSIC_PROMOTION,
            ContentType.BEHIND_THE_SCENES: ContentCategory.ENGAGEMENT,
            ContentType.LYRICS_QUOTE: ContentCategory.MUSIC_PROMOTION,
            ContentType.FAN_APPRECIATION: ContentCategory.GRATITUDE,
            ContentType.EDUCATIONAL: ContentCategory.ENGAGEMENT,
            ContentType.AFROBEAT_HISTORY: ContentCategory.ENGAGEMENT,
            ContentType.TRENDING_TOPIC: ContentCategory.ENGAGEMENT,
            ContentType.STUDIO_UPDATE: ContentCategory.MUSIC_PROMOTION,
        }
        
        category = category_map.get(content_type, ContentCategory.DAILY_BLESSING)
        
        # Queue content for each platform
        for platform in platforms:
            text = content_data["text"]
            
            # Add CTA if present
            if content_data.get("cta"):
                text += f"\n\n{content_data['cta']}"
            
            # Combine hashtags
            all_hashtags = list(set(hashtags + content_data.get("hashtags", [])))
            
            self.review_queue.add_to_queue(
                content_type=content_type.value,
                platform=platform,
                title=f"{content_type.value.replace('_', ' ').title()}",
                body=text,
                category=category,
                hashtags=all_hashtags[:7],  # Limit hashtags
                scheduled_at=datetime.utcnow() + timedelta(minutes=5)
            )
        
        self.log_action(
            "content_queued",
            f"{content_type.value} queued for {', '.join(platforms)}",
            details={"hashtags": hashtags, "content_type": content_type.value}
        )
    
    # Legacy methods kept for backward compatibility
    def _check_scheduled_content_generation(self, current_hour: int) -> None:
        """Check if scheduled content should be generated.
        
        Args:
            current_hour: Current hour in WAT
        """
        morning_hour = self.settings.agent_morning_hour
        afternoon_hour = self.settings.agent_afternoon_hour
        evening_hour = self.settings.agent_evening_hour
        
        # Morning blessing (around 8am WAT)
        if current_hour == morning_hour and self._should_run("morning_blessing", minutes=120):
            self._generate_morning_blessing()
        
        # Afternoon engagement (around 2pm WAT)
        if current_hour == afternoon_hour and self._should_run("afternoon_engagement", minutes=120):
            self._generate_afternoon_content()
        
        # Evening spotlight (around 8pm WAT)
        if current_hour == evening_hour and self._should_run("evening_spotlight", minutes=120):
            self._generate_evening_content()
    
    def _generate_morning_blessing(self) -> None:
        """Generate and queue morning blessing content."""
        self.log_action("generating_content", "Generating morning blessing")
        
        themes = ["gratitude", "abundance", "love", "wisdom", "peace", "strength"]
        theme = random.choice(themes)
        
        content = self.content_adapter.create_daily_blessing(theme=theme)
        
        # Queue for Instagram
        ig_content = content["instagram"]
        self.review_queue.add_to_queue(
            content_type="morning_blessing",
            platform="instagram",
            title="Morning Blessing",
            body=ig_content.get_full_caption(),
            category=ContentCategory.DAILY_BLESSING,
            hashtags=ig_content.hashtags,
            scheduled_at=datetime.utcnow() + timedelta(minutes=5)
        )
        
        # Queue for X
        x_content = content["x"]
        self.review_queue.add_to_queue(
            content_type="morning_blessing",
            platform="x",
            title="Morning Blessing",
            body=x_content.tweets[0],
            category=ContentCategory.DAILY_BLESSING,
            hashtags=x_content.hashtags,
            scheduled_at=datetime.utcnow() + timedelta(minutes=10)
        )
        
        self.log_action(
            "content_queued",
            "Morning blessing queued for Instagram and X",
            details={"theme": theme}
        )
    
    def _generate_afternoon_content(self) -> None:
        """Generate afternoon engagement/appreciation content."""
        self.log_action("generating_content", "Generating afternoon content")
        
        # Create fan appreciation content
        content = self.content_adapter.adapt_fan_shoutout(
            fan_name="Value Adders Family",
            support_type="support"
        )
        
        # Queue for Instagram
        ig_content = content["instagram"]
        self.review_queue.add_to_queue(
            content_type="fan_appreciation",
            platform="instagram",
            title="Gratitude Roll Call",
            body=ig_content.get_full_caption(),
            category=ContentCategory.GRATITUDE,
            hashtags=ig_content.hashtags,
            scheduled_at=datetime.utcnow() + timedelta(minutes=5)
        )
        
        self.log_action("content_queued", "Afternoon content queued")
    
    def _generate_evening_content(self) -> None:
        """Generate evening spotlight/music content."""
        self.log_action("generating_content", "Generating evening spotlight")
        
        # For now, create a motivational quote
        content = self.content_adapter.create_daily_blessing(
            custom_message="As the day closes, remember: every sunset is proof that endings can be beautiful. Rest well, rise stronger! 🌅"
        )
        
        # Queue for both platforms
        ig_content = content["instagram"]
        self.review_queue.add_to_queue(
            content_type="evening_spotlight",
            platform="instagram",
            title="Evening Reflection",
            body=ig_content.get_full_caption(),
            category=ContentCategory.AFFIRMATION,
            hashtags=ig_content.hashtags,
            scheduled_at=datetime.utcnow() + timedelta(minutes=5)
        )
        
        self.log_action("content_queued", "Evening spotlight queued")
    
    def _publish_ready_content(self) -> None:
        """Publish content that's approved and scheduled for now."""
        ready_items = self.review_queue.get_ready_to_publish(limit=10)
        
        for item in ready_items:
            try:
                result = self._publish_item(item)
                
                if result.success:
                    self.review_queue.mark_published(
                        item.id,
                        result.post_id,
                        result.post_url
                    )
                    
                    self.log_action(
                        "post_published",
                        f"Published to {item.platform}: {item.title}",
                        content_id=item.id,
                        platform=item.platform,
                        details={"post_url": result.post_url}
                    )
                else:
                    self.review_queue.mark_failed(item.id, result.error)
                    
                    self.log_action(
                        "post_failed",
                        f"Failed to publish: {result.error}",
                        level="error",
                        content_id=item.id,
                        platform=item.platform
                    )
                    
            except Exception as e:
                self.review_queue.mark_failed(item.id, str(e))
                self.log_action(
                    "post_error",
                    f"Error publishing: {str(e)}",
                    level="error",
                    content_id=item.id
                )
    
    def _publish_item(self, item: ContentQueueItem) -> PublishResult:
        """Publish a single content item.
        
        Args:
            item: Content queue item to publish
            
        Returns:
            PublishResult
        """
        platform = item.platform.lower()
        
        # Use Buffer as fallback if direct API not available
        use_buffer = False
        
        if platform == "instagram":
            if self.instagram.is_connected():
                return self.instagram.publish_post(
                    content=item.body,
                    media_urls=item.media_urls if item.media_urls else None
                )
            use_buffer = True
            
        elif platform == "x":
            if self.x_publisher.is_connected():
                return self.x_publisher.publish_post(
                    content=item.body,
                    media_urls=item.media_urls if item.media_urls else None
                )
            use_buffer = True
        
        # Fallback to Buffer
        if use_buffer and self.buffer.is_connected():
            return self.buffer.publish_post(
                content=item.body,
                media_urls=item.media_urls if item.media_urls else None
            )
        
        return PublishResult(
            success=False,
            platform=Platform(platform) if platform in ["instagram", "x"] else Platform.BUFFER,
            error=f"No publisher available for {platform}"
        )
    
    def _check_and_respond_to_interactions(self) -> None:
        """Check for new fan interactions and generate responses.
        
        Enhanced with Phase 2 fan engagement:
        - Tracks fan tier (Casual → Super Fan)
        - Analyzes sentiment for response priority
        - Uses personalized greetings based on tier
        """
        self.log_action("checking_interactions", "Checking for fan interactions")
        
        # Get pending interactions from database
        pending = self.db.get_pending_interactions(limit=20)
        
        if not pending:
            return
        
        self.log_action(
            "interactions_found",
            f"Found {len(pending)} pending interactions",
            details={"count": len(pending)}
        )
        
        # Sort by urgency (negative sentiment and VIP fans first)
        prioritized = []
        for interaction in pending:
            fan, sentiment = self.fan_engagement.record_interaction(
                username=interaction.fan_username,
                platform=interaction.platform,
                message=interaction.message,
                interaction_type=interaction.interaction_type,
                display_name=interaction.fan_display_name,
                profile_url=interaction.fan_profile_url,
            )
            urgency = self.fan_engagement.get_response_urgency(fan, sentiment)
            prioritized.append((urgency, interaction, fan, sentiment))
        
        # Sort by urgency (highest first)
        prioritized.sort(key=lambda x: x[0], reverse=True)
        
        for urgency, interaction, fan, sentiment in prioritized:
            try:
                # Get personalized greeting based on fan tier
                greeting = self.fan_engagement.get_personalized_greeting(fan)
                
                # Generate response using AI personality with fan context
                response_text = self.personality.generate_response(
                    context=PersonalityContext.FAN_COMMENT,
                    message=interaction.message,
                    fan_name=interaction.fan_username,
                    platform=interaction.platform,
                )
                
                # For very negative sentiment, flag for human review
                if sentiment == Sentiment.VERY_NEGATIVE:
                    self.log_action(
                        "response_needs_review",
                        f"Negative sentiment from {interaction.fan_username} - flagging for review",
                        interaction_id=interaction.id,
                        details={"sentiment": sentiment.value, "tier": fan.tier}
                    )
                    continue
                
                # Send the response
                result = self._send_response(
                    interaction.platform,
                    interaction.platform_interaction_id,
                    response_text
                )
                
                if result.success:
                    self.db.mark_interaction_responded(
                        interaction.id,
                        response_text,
                        result.post_id
                    )
                    
                    self.log_action(
                        "response_sent",
                        f"Responded to {interaction.fan_username} (tier: {fan.tier}, urgency: {urgency})",
                        interaction_id=interaction.id,
                        platform=interaction.platform,
                        details={
                            "tier": fan.tier,
                            "sentiment": sentiment.value,
                            "urgency": urgency
                        }
                    )
                    
            except Exception as e:
                self.log_action(
                    "response_error",
                    f"Error responding to interaction: {str(e)}",
                    level="error",
                    interaction_id=interaction.id
                )
    
    def _send_response(
        self,
        platform: str,
        interaction_id: str,
        response_text: str
    ) -> PublishResult:
        """Send a response to an interaction.
        
        Args:
            platform: Platform name
            interaction_id: Platform's interaction ID
            response_text: Response to send
            
        Returns:
            PublishResult
        """
        if platform == "instagram" and self.instagram.is_connected():
            return self.instagram.reply_to_post(interaction_id, response_text)
        
        elif platform == "x" and self.x_publisher.is_connected():
            return self.x_publisher.reply_to_post(interaction_id, response_text)
        
        return PublishResult(
            success=False,
            platform=Platform.INSTAGRAM if platform == "instagram" else Platform.X,
            error=f"Publisher not connected for {platform}"
        )
    
    def _collect_analytics(self) -> None:
        """Collect analytics from connected platforms."""
        self.log_action("collecting_analytics", "Collecting platform analytics")
        
        analytics = {}
        
        if self.instagram.is_connected():
            analytics["instagram"] = self.instagram.get_metrics()
        
        if self.x_publisher.is_connected():
            analytics["x"] = self.x_publisher.get_metrics()
        
        if analytics:
            self.log_action(
                "analytics_collected",
                "Analytics collected successfully",
                details=analytics
            )
    
    def run_once(self) -> Dict[str, Any]:
        """Run a single iteration of the agent.
        
        Useful for testing or one-off runs.
        
        Returns:
            Summary of actions taken
        """
        self.log_action("agent_run_once", "Running single iteration")
        
        summary = {
            "content_published": 0,
            "interactions_responded": 0,
            "errors": []
        }
        
        try:
            self._run_iteration()
        except Exception as e:
            summary["errors"].append(str(e))
        
        return summary
    
    def connect_platforms(self) -> Dict[str, bool]:
        """Try to connect to all configured platforms.
        
        Returns:
            Dict of platform -> connected status
        """
        connections = {}
        
        if self.settings.has_instagram_credentials():
            connections["instagram"] = self.instagram.connect()
            self.log_action(
                "platform_connected" if connections["instagram"] else "platform_failed",
                f"Instagram: {'connected' if connections['instagram'] else 'failed'}",
                platform="instagram"
            )
        
        if self.settings.has_x_credentials():
            connections["x"] = self.x_publisher.connect()
            self.log_action(
                "platform_connected" if connections["x"] else "platform_failed",
                f"X: {'connected' if connections['x'] else 'failed'}",
                platform="x"
            )
        
        if self.settings.buffer_access_token:
            connections["buffer"] = self.buffer.connect()
            self.log_action(
                "platform_connected" if connections["buffer"] else "platform_failed",
                f"Buffer: {'connected' if connections['buffer'] else 'failed'}",
                platform="buffer"
            )
        
        return connections
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status.
        
        Returns:
            Dict with status information
        """
        return {
            "session_id": self.session_id,
            "running": self._running,
            "last_runs": {k: v.isoformat() for k, v in self._last_runs.items()},
            "platforms": {
                "instagram": self.instagram.is_connected(),
                "x": self.x_publisher.is_connected(),
                "buffer": self.buffer.is_connected()
            },
            "queue_stats": self.review_queue.get_stats().__dict__
        }
