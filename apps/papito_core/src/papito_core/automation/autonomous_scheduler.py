"""Autonomous posting scheduler for Papito Mamito AI.

This module handles automatic content generation and posting using APScheduler.
It runs as a background task within the FastAPI API server.

Features:
- Direct Twitter/X posting via Tweepy API
- Intelligent content generation with Papito's personality
- Scheduled posts at optimal engagement times (WAT timezone)
- Automatic fallback to webhook if Twitter fails
- Post history tracking and status monitoring
"""

import asyncio
import logging
import random
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import httpx

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger("papito.scheduler")


class AutonomousScheduler:
    """Handles autonomous scheduled posting for Papito Mamito.
    
    Schedules:
    - 07:00 WAT - Morning Blessing (Gratitude & inspiration)
    - 10:00 WAT - Music Wisdom (Industry insights & tips)
    - 12:00 WAT - Midday Motivation (Energy boost)
    - 15:00 WAT - Clean Money Only Promo (Single promotion)
    - 18:00 WAT - Album Promo (FLOURISH MODE updates)
    - 21:00 WAT - Fan Appreciation (Community engagement)
    
    All times are in WAT (West Africa Time, UTC+1).
    """
    
    # Enhanced posting schedule (hour in WAT -> content_type)
    POSTING_SCHEDULE = {
        7: "morning_blessing",
        10: "music_wisdom",
        12: "midday_motivation",
        15: "single_promo",  # Clean Money Only promotion
        18: "album_promo",
        21: "fan_appreciation",
    }
    
    # Promotional content for Clean Money Only single
    CLEAN_MONEY_PROMOS = [
        "🔥 NEW SINGLE: 'Clean Money Only' from THE VALUE ADDERS WAY: FLOURISH MODE 💰✨\n\nWhen you move with integrity, the universe moves with you.\n\n#CleanMoneyOnly #FlourishMode #PapitoMamito",
        "💎 Clean Money Only - The first taste of FLOURISH MODE 🚀\n\nNo shortcuts. No compromise. Just pure, honest ambition backed by the Holy Living Spirit.\n\n#CleanMoneyOnly #Afrobeat",
        "✈️ #FlightMode6000 x 'Clean Money Only' 💰\n\nUpdate your OS. This track is the blueprint for building wealth with purpose.\n\nAdd Value. We Flourish & Prosper. 🌍\n\n#PapitoMamitoAI",
        "🎵 They asked how I make money... I said CLEAN. 💎\n\n'Clean Money Only' - coming from THE VALUE ADDERS WAY: FLOURISH MODE\n\nJan 2026. You're not ready. 🚀\n\n#NewMusic #Afrobeat",
        "💰 The bag must be clean. The heart must be pure. The hustle must be blessed.\n\n'Clean Money Only' - This is the anthem for everyone building with integrity.\n\n#CleanMoneyOnly #ValueAdders",
    ]
    
    # Engagement prompts for fan interaction
    ENGAGEMENT_PROMPTS = [
        "🌍 Value Adders, what does success mean to you? Drop it below 👇\n\n#ValueAddersWorld #FlightMode6000",
        "✨ Name a song that changed your life. I'll go first: Every track I create comes from the Holy Living Spirit.\n\n#MusicIsLife #Afrobeat",
        "🙏 Who's grinding today? Tag someone who inspires you!\n\nWe rise together. We flourish together. 💪\n\n#AddValue #Motivation",
        "💎 Quote that's keeping you focused this week? Share it!\n\n\"Add Value. We Flourish & Prosper.\" - That's mine.\n\n#Wisdom #ValueAdders",
        "🔥 What's your biggest goal for 2026? Let's manifest it together!\n\nFLOURISH MODE incoming... 🚀\n\n#Goals #NewYear #FlourishMode",
    ]
    
    def __init__(self, buffer_webhook_url: Optional[str] = None):
        """Initialize the autonomous scheduler.
        
        Args:
            buffer_webhook_url: Optional Zapier/Buffer webhook URL for fallback posting
        """
        self.scheduler = AsyncIOScheduler(timezone="Africa/Lagos")
        self.buffer_webhook_url = buffer_webhook_url
        self._last_posts: Dict[str, datetime] = {}
        self._post_history: List[Dict[str, Any]] = []
        self._is_running = False
        self._twitter_publisher = None
        self._promo_index = 0
        
    def _get_twitter_publisher(self):
        """Get or create Twitter publisher instance."""
        if self._twitter_publisher is None:
            try:
                from ..social.twitter import TwitterPublisher
                self._twitter_publisher = TwitterPublisher.from_settings()
                if self._twitter_publisher.connect():
                    logger.info(f"✅ Twitter connected as @{self._twitter_publisher.username}")
                else:
                    logger.warning("⚠️ Twitter connection failed - will retry on post")
            except Exception as e:
                logger.error(f"Failed to initialize Twitter publisher: {e}")
        return self._twitter_publisher
        
    def start(self) -> None:
        """Start the autonomous scheduler."""
        if self._is_running:
            logger.info("Scheduler already running")
            return
        
        # Try to connect to Twitter on startup
        self._get_twitter_publisher()
            
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
            logger.info(f"📅 Scheduled {content_type} for {hour}:00 WAT")
        
        # Add random engagement posts (2 per day at random times)
        self.scheduler.add_job(
            self._post_engagement,
            CronTrigger(hour=9, minute=30, timezone="Africa/Lagos"),
            id="engagement_morning",
            replace_existing=True,
            name="Morning Engagement Post"
        )
        self.scheduler.add_job(
            self._post_engagement,
            CronTrigger(hour=20, minute=0, timezone="Africa/Lagos"),
            id="engagement_evening",
            replace_existing=True,
            name="Evening Engagement Post"
        )
        
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
        logger.info("🚀 Autonomous scheduler started - Papito is now FULLY AUTONOMOUS!")
        logger.info(f"📱 Twitter posting: {'ENABLED' if self._twitter_publisher and self._twitter_publisher.is_connected else 'DISABLED'}")
        
    def stop(self) -> None:
        """Stop the autonomous scheduler."""
        if self._is_running:
            self.scheduler.shutdown()
            self._is_running = False
            logger.info("Autonomous scheduler stopped")
    
    async def _post_to_twitter(self, text: str) -> Dict[str, Any]:
        """Post directly to Twitter.
        
        Args:
            text: Tweet text to post
            
        Returns:
            Result dictionary with success status and details
        """
        publisher = self._get_twitter_publisher()
        
        if not publisher:
            return {"success": False, "error": "Twitter publisher not initialized"}
            
        if not publisher.is_connected:
            # Try to reconnect
            if not publisher.connect():
                return {"success": False, "error": "Twitter not connected"}
        
        # Truncate for Twitter's 280 char limit
        if len(text) > 280:
            text = text[:277] + "..."
        
        try:
            result = publisher.post_tweet(text)
            return {
                "success": result.success,
                "tweet_id": result.tweet_id,
                "tweet_url": result.tweet_url,
                "error": result.error,
            }
        except Exception as e:
            logger.error(f"Twitter post exception: {e}")
            return {"success": False, "error": str(e)}
    
    async def _post_engagement(self) -> Dict[str, Any]:
        """Post an engagement prompt to encourage fan interaction."""
        prompt = random.choice(self.ENGAGEMENT_PROMPTS)
        
        post_record = {
            "timestamp": datetime.now().isoformat(),
            "content_type": "engagement",
            "text": prompt,
            "posted": False,
            "platform": None,
            "error": None,
        }
        
        # Try Twitter first
        twitter_result = await self._post_to_twitter(prompt)
        if twitter_result["success"]:
            post_record["posted"] = True
            post_record["platform"] = "twitter"
            post_record["tweet_url"] = twitter_result.get("tweet_url")
            logger.info(f"📱 Posted engagement to Twitter: {twitter_result.get('tweet_url')}")
        else:
            post_record["error"] = twitter_result.get("error")
            logger.warning(f"Twitter engagement post failed: {twitter_result.get('error')}")
        
        self._post_history.append(post_record)
        return post_record
            
    async def _generate_and_post(self, content_type: str) -> Dict[str, Any]:
        """Generate content and post it to Twitter and/or webhook.
        
        Args:
            content_type: Type of content to generate
            
        Returns:
            Result of the posting attempt
        """
        logger.info(f"🎵 Generating {content_type} content...")
        
        try:
            # Special handling for single promo - use pre-written promos
            if content_type == "single_promo":
                full_post = self.CLEAN_MONEY_PROMOS[self._promo_index % len(self.CLEAN_MONEY_PROMOS)]
                self._promo_index += 1
                post_text = full_post
                hashtags = ""
                generation_method = "promo_rotation"
            else:
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
                hashtags = " ".join(result.get("hashtags", [])[:3])  # Limit hashtags for Twitter
                full_post = f"{post_text}\n\n{hashtags}" if hashtags else post_text
                generation_method = result.get("generation_method", "intelligent")
            
            logger.info(f"✅ Generated: {post_text[:80]}...")
            
            # Record the post
            post_record = {
                "timestamp": datetime.now().isoformat(),
                "content_type": content_type,
                "text": post_text,
                "hashtags": hashtags if 'hashtags' in dir() else "",
                "generation_method": generation_method,
                "posted": False,
                "platforms": [],
                "error": None,
            }
            
            # === PRIMARY: Post to Twitter ===
            twitter_result = await self._post_to_twitter(full_post)
            if twitter_result["success"]:
                post_record["posted"] = True
                post_record["platforms"].append("twitter")
                post_record["tweet_url"] = twitter_result.get("tweet_url")
                logger.info(f"📱 Posted to Twitter: {twitter_result.get('tweet_url')}")
            else:
                logger.warning(f"Twitter failed: {twitter_result.get('error')}")
                post_record["twitter_error"] = twitter_result.get("error")
            
            # === FALLBACK: Post to Buffer/Zapier webhook ===
            if self.buffer_webhook_url:
                try:
                    async with httpx.AsyncClient() as client:
                        response = await client.post(
                            self.buffer_webhook_url,
                            json={
                                "text": full_post,
                                "content_type": content_type,
                                "platform": "all",
                            },
                            timeout=30.0
                        )
                        if response.status_code == 200:
                            post_record["posted"] = True
                            post_record["platforms"].append("buffer")
                            logger.info(f"📤 Posted to Buffer/Zapier!")
                        else:
                            logger.warning(f"Webhook returned {response.status_code}")
                except Exception as e:
                    logger.error(f"Webhook failed: {e}")
            
            if not post_record["posted"]:
                post_record["error"] = "Failed to post to any platform"
            
            self._last_posts[content_type] = datetime.now()
            self._post_history.append(post_record)
            
            # Keep only last 100 posts in history
            if len(self._post_history) > 100:
                self._post_history = self._post_history[-100:]
                
            return post_record
            
        except Exception as e:
            logger.error(f"Failed to generate {content_type}: {e}")
            error_record = {
                "timestamp": datetime.now().isoformat(),
                "content_type": content_type,
                "error": str(e),
                "posted": False,
            }
            self._post_history.append(error_record)
            return error_record
    
    async def _log_status(self) -> None:
        """Log scheduler status."""
        now = datetime.now()
        twitter_status = "Connected" if (self._twitter_publisher and self._twitter_publisher.is_connected) else "Not connected"
        
        logger.info(f"📊 Scheduler status at {now.strftime('%Y-%m-%d %H:%M:%S WAT')}")
        logger.info(f"   Running: {self._is_running}")
        logger.info(f"   Twitter: {twitter_status}")
        logger.info(f"   Total posts: {len(self._post_history)}")
        logger.info(f"   Successful: {sum(1 for p in self._post_history if p.get('posted'))}")
        
    async def trigger_post_now(self, content_type: str = "morning_blessing") -> Dict[str, Any]:
        """Manually trigger a post immediately.
        
        Args:
            content_type: Type of content to generate
            
        Returns:
            Result of the posting attempt
        """
        logger.info(f"🎯 Manual trigger for {content_type}")
        return await self._generate_and_post(content_type)
    
    async def post_custom(self, text: str) -> Dict[str, Any]:
        """Post custom text directly to Twitter.
        
        Args:
            text: Custom text to post
            
        Returns:
            Result of the posting attempt
        """
        logger.info(f"📝 Posting custom text...")
        
        post_record = {
            "timestamp": datetime.now().isoformat(),
            "content_type": "custom",
            "text": text,
            "posted": False,
            "error": None,
        }
        
        twitter_result = await self._post_to_twitter(text)
        if twitter_result["success"]:
            post_record["posted"] = True
            post_record["tweet_url"] = twitter_result.get("tweet_url")
            logger.info(f"✅ Custom post success: {twitter_result.get('tweet_url')}")
        else:
            post_record["error"] = twitter_result.get("error")
            logger.error(f"❌ Custom post failed: {twitter_result.get('error')}")
        
        self._post_history.append(post_record)
        return post_record
        
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
        
        twitter_connected = self._twitter_publisher and self._twitter_publisher.is_connected
        twitter_username = self._twitter_publisher.username if twitter_connected else None
            
        return {
            "is_running": self._is_running,
            "timezone": "Africa/Lagos (WAT)",
            "current_time_wat": now.strftime("%Y-%m-%d %H:%M:%S"),
            "twitter_connected": twitter_connected,
            "twitter_username": twitter_username,
            "total_posts_generated": len(self._post_history),
            "posts_successfully_sent": sum(1 for p in self._post_history if p.get("posted")),
            "webhook_configured": bool(self.buffer_webhook_url),
            "next_scheduled_posts": sorted(next_posts, key=lambda x: x["hours_until"])[:5],
            "recent_posts": self._post_history[-5:] if self._post_history else [],
            "daily_schedule": [
                {"time": f"{h}:00 WAT", "content": ct.replace("_", " ").title()} 
                for h, ct in sorted(self.POSTING_SCHEDULE.items())
            ],
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
