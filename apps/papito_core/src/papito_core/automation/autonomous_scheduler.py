"""Autonomous posting scheduler for Papito Mamito AI.

This module handles automatic content generation and posting using APScheduler.
It runs as a background task within the FastAPI API server.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import httpx

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger("papito.scheduler")


class AutonomousScheduler:
    """Handles autonomous scheduled posting for Papito Mamito.
    
    Schedules:
    - 07:00 WAT - Morning Blessing
    - 12:00 WAT - Midday Wisdom  
    - 15:00 WAT - Challenge Promo
    - 18:00 WAT - Album Promo
    - 21:00 WAT - Evening Reflection
    
    All times are in WAT (West Africa Time, UTC+1).
    """
    
    # Posting schedule (hour in WAT -> content_type)
    POSTING_SCHEDULE = {
        7: "morning_blessing",
        12: "music_wisdom",
        15: "challenge_promo",
        18: "album_promo",
        21: "fan_appreciation",
    }
    
    def __init__(self, buffer_webhook_url: Optional[str] = None):
        """Initialize the autonomous scheduler.
        
        Args:
            buffer_webhook_url: Optional Zapier/Buffer webhook URL for direct posting
        """
        self.scheduler = AsyncIOScheduler(timezone="Africa/Lagos")
        self.buffer_webhook_url = buffer_webhook_url
        self._last_posts: Dict[str, datetime] = {}
        self._post_history: List[Dict[str, Any]] = []
        self._is_running = False
        
    def start(self) -> None:
        """Start the autonomous scheduler."""
        if self._is_running:
            logger.info("Scheduler already running")
            return
            
        # Schedule posts for each time slot
        for hour, content_type in self.POSTING_SCHEDULE.items():
            self.scheduler.add_job(
                self._generate_and_post,
                CronTrigger(hour=hour, minute=0, timezone="Africa/Lagos"),
                args=[content_type],
                id=f"post_{content_type}_{hour}",
                replace_existing=True,
                name=f"Papito {content_type.replace('_', ' ').title()} at {hour}:00 WAT"
            )
            logger.info(f"Scheduled {content_type} for {hour}:00 WAT")
        
        # Add a health check job (every hour)
        self.scheduler.add_job(
            self._log_status,
            CronTrigger(minute=30),
            id="hourly_status",
            replace_existing=True,
            name="Hourly Status Check"
        )
        
        self.scheduler.start()
        self._is_running = True
        logger.info("🚀 Autonomous scheduler started - Papito is now truly autonomous!")
        
    def stop(self) -> None:
        """Stop the autonomous scheduler."""
        if self._is_running:
            self.scheduler.shutdown()
            self._is_running = False
            logger.info("Autonomous scheduler stopped")
            
    async def _generate_and_post(self, content_type: str) -> Dict[str, Any]:
        """Generate content and post it.
        
        Args:
            content_type: Type of content to generate
            
        Returns:
            Result of the posting attempt
        """
        logger.info(f"🎵 Generating {content_type} content...")
        
        try:
            # Import here to avoid circular imports
            from ..intelligence.content_generator import IntelligentContentGenerator, PapitoContext
            
            # Create context
            context = PapitoContext()
            generator = IntelligentContentGenerator()
            
            # Generate content
            result = await generator.generate_post(
                content_type=content_type,
                context=context,
                include_album_mention=True
            )
            
            post_text = result.get("text", "")
            hashtags = " ".join(result.get("hashtags", []))
            full_post = f"{post_text}\n\n{hashtags}"
            
            logger.info(f"✅ Generated content: {post_text[:100]}...")
            
            # Record the post
            post_record = {
                "timestamp": datetime.now().isoformat(),
                "content_type": content_type,
                "text": post_text,
                "hashtags": hashtags,
                "generation_method": result.get("generation_method", "unknown"),
                "posted": False,
                "error": None,
            }
            
            # Try to post via Buffer/Zapier webhook if configured
            if self.buffer_webhook_url:
                try:
                    async with httpx.AsyncClient() as client:
                        response = await client.post(
                            self.buffer_webhook_url,
                            json={
                                "text": full_post,
                                "content_type": content_type,
                                "platform": "instagram",
                            },
                            timeout=30.0
                        )
                        if response.status_code == 200:
                            post_record["posted"] = True
                            logger.info(f"📤 Posted to Buffer/Zapier successfully!")
                        else:
                            post_record["error"] = f"Webhook returned {response.status_code}"
                            logger.warning(f"Webhook returned {response.status_code}")
                except Exception as e:
                    post_record["error"] = str(e)
                    logger.error(f"Failed to post to webhook: {e}")
            else:
                post_record["error"] = "No webhook URL configured"
                logger.info("📝 Content generated but no webhook configured for auto-posting")
            
            self._last_posts[content_type] = datetime.now()
            self._post_history.append(post_record)
            
            # Keep only last 50 posts in history
            if len(self._post_history) > 50:
                self._post_history = self._post_history[-50:]
                
            return post_record
            
        except Exception as e:
            logger.error(f"Failed to generate {content_type}: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "content_type": content_type,
                "error": str(e),
                "posted": False,
            }
    
    async def _log_status(self) -> None:
        """Log scheduler status."""
        now = datetime.now()
        logger.info(f"📊 Scheduler status at {now.strftime('%Y-%m-%d %H:%M:%S WAT')}")
        logger.info(f"   Running: {self._is_running}")
        logger.info(f"   Total posts generated: {len(self._post_history)}")
        logger.info(f"   Posts successfully sent: {sum(1 for p in self._post_history if p.get('posted'))}")
        
    async def trigger_post_now(self, content_type: str = "morning_blessing") -> Dict[str, Any]:
        """Manually trigger a post immediately.
        
        Args:
            content_type: Type of content to generate
            
        Returns:
            Result of the posting attempt
        """
        logger.info(f"🎯 Manual trigger for {content_type}")
        return await self._generate_and_post(content_type)
        
    def get_status(self) -> Dict[str, Any]:
        """Get current scheduler status.
        
        Returns:
            Status dictionary
        """
        now = datetime.now()
        next_posts = []
        
        for hour, content_type in sorted(self.POSTING_SCHEDULE.items()):
            # Create datetime for today at this hour
            post_time = now.replace(hour=hour, minute=0, second=0, microsecond=0)
            if post_time < now:
                # Already passed today, schedule for tomorrow
                post_time += timedelta(days=1)
            
            next_posts.append({
                "content_type": content_type,
                "scheduled_time": post_time.strftime("%Y-%m-%d %H:%M WAT"),
                "hours_until": round((post_time - now).total_seconds() / 3600, 1),
            })
            
        return {
            "is_running": self._is_running,
            "timezone": "Africa/Lagos (WAT)",
            "current_time_wat": now.strftime("%Y-%m-%d %H:%M:%S"),
            "total_posts_generated": len(self._post_history),
            "posts_successfully_sent": sum(1 for p in self._post_history if p.get("posted")),
            "webhook_configured": bool(self.buffer_webhook_url),
            "next_scheduled_posts": next_posts[:3],
            "recent_posts": self._post_history[-5:] if self._post_history else [],
        }


# Global scheduler instance
_scheduler: Optional[AutonomousScheduler] = None


def get_scheduler() -> AutonomousScheduler:
    """Get the global scheduler instance."""
    global _scheduler
    if _scheduler is None:
        from ..settings import get_settings
        settings = get_settings()
        webhook_url = getattr(settings, 'buffer_webhook_url', None)
        _scheduler = AutonomousScheduler(buffer_webhook_url=webhook_url)
    return _scheduler


def start_scheduler() -> None:
    """Start the global scheduler."""
    scheduler = get_scheduler()
    scheduler.start()


def stop_scheduler() -> None:
    """Stop the global scheduler."""
    global _scheduler
    if _scheduler:
        _scheduler.stop()
