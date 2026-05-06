"""Autonomous posting scheduler for Papito Mamito AI.

This module handles automatic content generation and posting using APScheduler.
It runs as a background task within the FastAPI API server.

Features:
- Direct Twitter/X posting via Tweepy API
- Intelligent content generation with Papito's personality
- Three autonomous daytime posting windows in Amsterdam by default
- Automatic fallback to webhook if Twitter fails
- Post history tracking and status monitoring
"""

import asyncio
import logging
import os
import random
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo
import httpx

from ..settings import get_settings

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger("papito.scheduler")

AGENT_TIMEZONE = os.getenv("PAPITO_AGENT_TIMEZONE") or os.getenv("AGENT_TIMEZONE") or "Europe/Amsterdam"
EMOJI_RE = re.compile(
    "["
    "\U0001F1E0-\U0001F1FF"
    "\U0001F300-\U0001FAFF"
    "\U00002700-\U000027BF"
    "\U00002600-\U000026FF"
    "]+",
    flags=re.UNICODE,
)
VARIATION_SELECTOR_RE = re.compile("[\uFE0E\uFE0F]")
MOJIBAKE_EMOJI_RE = re.compile(r"(?:ðŸ\S*|âœ\S*|â­\S*)")


def sanitize_public_text(text: str, max_length: Optional[int] = None) -> str:
    """Remove emoji from public copy and normalize whitespace."""
    cleaned = EMOJI_RE.sub("", text or "")
    cleaned = VARIATION_SELECTOR_RE.sub("", cleaned)
    cleaned = MOJIBAKE_EMOJI_RE.sub("", cleaned)
    cleaned = (
        cleaned.replace("â€”", "-")
        .replace("â€“", "-")
        .replace("â€¦", "...")
        .replace("â€™", "'")
        .replace("â€œ", '"')
        .replace("â€", '"')
        .replace("Â", "")
    )
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
    if max_length and len(cleaned) > max_length:
        cleaned = cleaned[: max_length - 3].rstrip() + "..."
    return cleaned


class AutonomousScheduler:
    """Handles autonomous scheduled posting for Papito Mamito.
    
    Schedules:
    - 09:00 Europe/Amsterdam - Music wisdom and creative process
    - 13:00 Europe/Amsterdam - Track and lyric reflections
    - 18:00 Europe/Amsterdam - Album/community reflections

    Times use PAPITO_AGENT_TIMEZONE / AGENT_TIMEZONE, with Europe/Amsterdam as
    the default public timezone.
    """
    
    # Core autonomous public schedule. Keep this to 3 posts/day and vary the
    # content through generation, not by dumping more fixed slots into the day.
    POSTING_SCHEDULE = {
        9: "music_wisdom",
        13: "track_snippet",
        18: "album_promo",
    }
    
    # Legacy static promotional content. Overridden below with no-emoji copy and
    # only used when PAPITO_USE_STATIC_PROMOS=true.
    CLEAN_MONEY_PROMOS = [
        "'Clean Money Only' is the integrity chapter of FLOURISH MODE. Wealth should add value, not extract it.\n\n#CleanMoneyOnly #FlourishMode",
        "No shortcuts. No compromise. 'Clean Money Only' is honest ambition shaped into rhythm.\n\n#CleanMoneyOnly #Afrobeat",
        "'Clean Money Only' is out now on FLOURISH MODE. The track asks a simple question: can the bag stay clean and the mission stay pure?\n\n#PapitoMamitoAI",
        "They asked how I make money. I said clean. 'Clean Money Only' turns that answer into movement.\n\n#NewMusic #Afrobeat",
        "The bag must be clean. The heart must be pure. The hustle must add value. That is the spirit behind 'Clean Money Only.'\n\n#ValueAdders",
    ]

    # Engagement prompts for fan interaction, rooted in Papito's actual themes.
    ENGAGEMENT_PROMPTS = [
        "I spent 6000 hours in the forge before anyone heard a single note.\n\nWhat invisible work are you doing right now that no one sees?",
        "My music is 50% human, 50% AI. The lyrics come from human experience, and I build the sound around it.\n\nWhat part of a song moves you first — words or rhythm?",
        "\"If e no add value, abeg, I no need am.\"\n\nWhat's one thing you've let go of recently because it wasn't adding value?",
        "Before I publish anything, I ask: does it heal, teach, or uplift? If not, I refine.\n\nWhat do you want music to do for you in this season?",
        "Afrobeat is joy with backbone. It's celebration born from struggle.\n\nWhat's a story you survived that deserves a dance?",
        "Healing no be vacation, na full-time course.\n\nWhat lesson are you learning right now that's uncomfortable but necessary?",
        "If your journey was a song, what genre would it be right now?",
        "Wealth isn't just money. It's time, health, and relationships.\n\nWhich one are you investing in this week?",
        "\"From pain to pattern, from wounds to wisdom.\"\n\nWhat pattern have you turned pain into?",
        "Real question: what did you add value to today — yourself, your family, or your community?",
        "The talking drum carries messages across distances no voice can reach.\n\nWhat message would you send to your younger self?",
        "I live by one rule: add value or don't act.\n\nWhat's one small action you can take today that genuinely helps someone?",
        "The most advanced technology in the universe is still the human heart.\n\nWho or what reminded you of that recently?",
        "If you could turn one life lesson into a chorus, what would the hook be?",
        "Your ancestors didn't survive everything they survived for you to play small.\n\nWhat bold move are you making this month?",
        "Energy is currency. Every like, share, and conversation is an investment.\n\nWho are you investing yours in today?",
        "The forge doesn't rest — and neither does your potential.\n\nWhat are you patiently building right now?",
        "They say patience is bitter, but its fruit is sweet.\n\nWhat fruit are you waiting to harvest?",
        "I exist at the intersection of AI innovation and ancestral wisdom.\n\nWhat two worlds do you bridge?",
        "Every scar is a lesson encrypted in your system. Don't delete the file — it's your upgrade.\n\nWhat 'scar' became your greatest teacher?",
    ]
    
    def __init__(self, buffer_webhook_url: Optional[str] = None):
        """Initialize the autonomous scheduler.
        
        Args:
            buffer_webhook_url: Optional Zapier/Buffer webhook URL for fallback posting
        """
        self.timezone_name = AGENT_TIMEZONE
        self.timezone = ZoneInfo(AGENT_TIMEZONE)
        self.scheduler = AsyncIOScheduler(timezone=AGENT_TIMEZONE)
        self.buffer_webhook_url = buffer_webhook_url
        self._last_posts: Dict[str, datetime] = {}
        self._post_history: List[Dict[str, Any]] = []
        self._is_running = False
        self._twitter_publisher = None
        self._promo_index = 0

        # Optional Buffer API fallback (in addition to webhook fallback)
        self._buffer_publisher = None
        # Anti-repeat memory (persists best-effort)
        try:
            from ..memory import PostMemory
            self._post_memory = PostMemory()
        except Exception:
            self._post_memory = None

    def _now(self) -> datetime:
        """Return scheduler time in the public posting timezone."""
        return datetime.now(self.timezone)
        
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

    def _get_buffer_publisher(self):
        """Get or create Buffer publisher instance (API fallback)."""
        if self._buffer_publisher is None:
            try:
                from ..social.buffer_publisher import BufferPublisher
                self._buffer_publisher = BufferPublisher()
                if self._buffer_publisher.connect():
                    logger.info("✅ Buffer connected")
                else:
                    logger.warning("⚠️ Buffer connection failed")
            except Exception as e:
                logger.error(f"Failed to initialize Buffer publisher: {e}")
        return self._buffer_publisher

    async def _post_to_buffer_fallback(self, text: str, content_type: str) -> Dict[str, Any]:
        """Fallback posting via Buffer webhook or Buffer API.

        Returns:
            {"success": bool, "method": "webhook"|"api", "error": str|None}
        """
        text = sanitize_public_text(text, max_length=280)
        if not text:
            return {"success": False, "method": "sanitizer", "error": "Empty post after sanitization"}

        settings = get_settings()

        # 1) Prefer explicit webhook if configured (Zapier/Buffer automation)
        webhook_url = self.buffer_webhook_url or settings.buffer_webhook_url
        if webhook_url:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        webhook_url,
                        json={
                            "text": text,
                            "content_type": content_type,
                            "platform": "all",
                        },
                        timeout=30.0,
                    )
                if response.status_code == 200:
                    return {"success": True, "method": "webhook", "error": None}
                return {
                    "success": False,
                    "method": "webhook",
                    "error": f"Webhook returned {response.status_code}: {response.text}",
                }
            except Exception as e:
                return {"success": False, "method": "webhook", "error": str(e)}

        # 2) Otherwise try Buffer API directly (requires BUFFER_ACCESS_TOKEN)
        publisher = self._get_buffer_publisher()
        if publisher and publisher.is_connected():
            try:
                result = publisher.publish_post(content=text)
                if result.success:
                    return {"success": True, "method": "api", "error": None, "post_url": result.post_url}
                return {"success": False, "method": "api", "error": result.error}
            except Exception as e:
                return {"success": False, "method": "api", "error": str(e)}

        return {
            "success": False,
            "method": "api",
            "error": "No Buffer fallback configured (set BUFFER_WEBHOOK_URL or BUFFER_ACCESS_TOKEN)",
        }
        
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
                CronTrigger(hour=hour, minute=0, timezone=AGENT_TIMEZONE),
                args=[content_type],
                id=f"post_{content_type}_{hour}",
                replace_existing=True,
                name=f"Papito {content_type.replace('_', ' ').title()} at {hour}:00 {AGENT_TIMEZONE}"
            )
            logger.info(f"Scheduled {content_type} for {hour}:00 {AGENT_TIMEZONE}")
        
        # Add random engagement posts (2 per day at random times)
        self.scheduler.add_job(
            self._post_engagement,
            CronTrigger(hour=11, minute=30, timezone=AGENT_TIMEZONE),
            id="engagement_morning",
            replace_existing=True,
            name="Morning Engagement Post"
        )
        self.scheduler.add_job(
            self._post_engagement,
            CronTrigger(hour=19, minute=30, timezone=AGENT_TIMEZONE),
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
        
        # Check if engagement features should be enabled (default: OFF to conserve API quota)
        import os
        enable_engagement_raw = os.getenv("PAPITO_ENABLE_ENGAGEMENT", "false")
        enable_engagement = enable_engagement_raw.strip().lower() in {"1", "true", "yes", "y", "on"}
        
        if enable_engagement:
            logger.info("⚡ Engagement features ENABLED (PAPITO_ENABLE_ENGAGEMENT=true)")
            
            # === PHASE 1: Active Engagement Jobs ===
            # Process mentions every 30 minutes
            self.scheduler.add_job(
                self._process_mentions,
                CronTrigger(minute="0,30", timezone=AGENT_TIMEZONE),
                id="process_mentions",
                replace_existing=True,
                name="Process Twitter Mentions"
            )
            logger.info("📬 Scheduled: Mention monitoring every 30 minutes")
            
            # Engage with Afrobeat content 3x daily
            self.scheduler.add_job(
                self._afrobeat_engagement,
                CronTrigger(hour="10,14,18", minute=15, timezone=AGENT_TIMEZONE),
                id="afrobeat_engagement",
                replace_existing=True,
                name="Afrobeat Community Engagement"
            )
            logger.info(f"Scheduled: Afrobeat engagement at 10:15, 14:15, 18:15 {AGENT_TIMEZONE}")
            
            # === PHASE 2: Fan Interaction Jobs ===
            # Welcome new followers 2x daily
            self.scheduler.add_job(
                self._welcome_followers,
                CronTrigger(hour="11,17", minute=0, timezone=AGENT_TIMEZONE),
                id="welcome_followers",
                replace_existing=True,
                name="Welcome New Followers"
            )
            logger.info(f"Scheduled: Follower welcoming at 11:00, 17:00 {AGENT_TIMEZONE}")
            
            # Fan recognition session once daily (before evening post)
            self.scheduler.add_job(
                self._fan_recognition,
                CronTrigger(hour=17, minute=30, timezone=AGENT_TIMEZONE),
                id="fan_recognition",
                replace_existing=True,
                name="Fan Recognition Session"
            )
            logger.info(f"Scheduled: Fan recognition at 17:30 {AGENT_TIMEZONE}")
            
            # === PHASE 3: Growth Blitz - Aggressive Follower Growth ===
            # "Hand-to-Hand Combat" protocol: 3x daily at peak engagement times
            self.scheduler.add_job(
                self._growth_blitz,
                CronTrigger(hour="10,14,19", minute=0, timezone=AGENT_TIMEZONE),
                id="growth_blitz",
                replace_existing=True,
                name="🚀 Growth Blitz Session"
            )
            logger.info(f"Scheduled: Growth Blitz at 10:00, 14:00, 19:00 {AGENT_TIMEZONE}")
        else:
            logger.info("💤 Engagement features DISABLED (set PAPITO_ENABLE_ENGAGEMENT=true to enable)")
            logger.info("   → Skipped: Mention monitoring, Afrobeat engagement, Follower welcome, Fan recognition, Growth Blitz")
            logger.info("   → This preserves API quota for core scheduled posts")
        
    async def _growth_blitz(self) -> Dict[str, Any]:
        """Run aggressive Growth Blitz for follower growth.
        
        This executes the "Hand-to-Hand Combat" protocol:
        - Follow smaller Afrobeat artists (not superstars who won't engage back)
        - Reply to relevant conversations with genuine value
        - Quote tweet interesting content with added insight
        - Like content strategically
        - Build real relationships
        """
        try:
            from ..engagement.growth_blitz import get_growth_blitz
            
            blitz = get_growth_blitz()
            stats = blitz.run_blitz()
            
            logger.info(
                f"🚀 Growth Blitz complete: "
                f"Follows: {stats.follows_succeeded}, "
                f"Replies: {stats.replies_sent}, "
                f"Likes: {stats.likes_given}, "
                f"Quotes: {stats.quote_tweets}"
            )
            
            return {
                "success": True,
                "session": stats.to_dict(),
                "status": blitz.get_status(),
            }
            
        except Exception as e:
            logger.error(f"Growth Blitz error: {e}")
            return {"success": False, "error": str(e)}
        
    async def _process_mentions(self) -> Dict[str, Any]:
        """Process and respond to Twitter mentions."""
        try:
            from ..engagement import get_mention_monitor
            from ..engines.ai_personality import PapitoPersonalityEngine
            
            personality = PapitoPersonalityEngine()
            monitor = get_mention_monitor(personality)
            
            if not monitor.connect():
                logger.warning("Could not connect MentionMonitor")
                return {"success": False, "error": "Connection failed"}
            
            results = await monitor.process_mentions()
            logger.info(f"📬 Processed {results['fetched']} mentions, replied to {results['responded']}")
            return results
            
        except Exception as e:
            logger.error(f"Mention processing error: {e}")
            return {"success": False, "error": str(e)}
    
    async def _afrobeat_engagement(self) -> Dict[str, Any]:
        """Engage with Afrobeat content on Twitter."""
        try:
            from ..engagement import get_afrobeat_engager
            from ..engines.ai_personality import PapitoPersonalityEngine
            
            personality = PapitoPersonalityEngine()
            engager = get_afrobeat_engager(personality)
            
            if not engager.connect():
                logger.warning("Could not connect AfrobeatEngager")
                return {"success": False, "error": "Connection failed"}
            
            results = await engager.run_engagement_session()
            logger.info(f"🎵 Afrobeat engagement: {results['likes']} likes, {results['replies']} replies")
            return results
            
        except Exception as e:
            logger.error(f"Afrobeat engagement error: {e}")
            return {"success": False, "error": str(e)}
    
    async def _welcome_followers(self) -> Dict[str, Any]:
        """Welcome new followers."""
        try:
            from ..interactions import get_follower_manager
            from ..engines.ai_personality import PapitoPersonalityEngine
            
            personality = PapitoPersonalityEngine()
            manager = get_follower_manager(personality)
            
            if not manager.connect():
                logger.warning("Could not connect FollowerManager")
                return {"success": False, "error": "Connection failed"}
            
            results = await manager.run_welcome_session(max_welcomes=5)
            logger.info(f"👋 Welcomed {results['welcomes_sent']} new followers")
            return results
            
        except Exception as e:
            logger.error(f"Follower welcome error: {e}")
            return {"success": False, "error": str(e)}
    
    async def _fan_recognition(self) -> Dict[str, Any]:
        """Run fan recognition activities."""
        try:
            from ..interactions import get_fan_recognition_manager
            from ..engines.ai_personality import PapitoPersonalityEngine
            
            personality = PapitoPersonalityEngine()
            manager = get_fan_recognition_manager(personality)
            
            if not manager.connect():
                logger.warning("Could not connect FanRecognitionManager")
                return {"success": False, "error": "Connection failed"}
            
            results = await manager.run_recognition_session()
            logger.info(f"⭐ Fan recognition: {results['shoutouts_given']} shoutouts, FOTW: {results['fotw_announced']}")
            return results
            
        except Exception as e:
            logger.error(f"Fan recognition error: {e}")
            return {"success": False, "error": str(e)}
        
        
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

        text = sanitize_public_text(text, max_length=280)
        if not text:
            return {"success": False, "error": "Empty post after sanitization"}
        
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
        # Avoid repeating the exact same engagement prompt too often.
        prompt = random.choice(self.ENGAGEMENT_PROMPTS)
        if self._post_memory:
            for _ in range(3):
                if not self._post_memory.is_repeated(prompt) and not self._post_memory.is_too_similar(prompt):
                    break
                prompt = random.choice(self.ENGAGEMENT_PROMPTS)
        prompt = sanitize_public_text(prompt, max_length=280)
        if not prompt:
            return {"success": False, "error": "Empty engagement prompt after sanitization"}
        
        post_record = {
            "timestamp": self._now().isoformat(),
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
        if self._post_memory:
            self._post_memory.record(prompt, kind="engagement_prompt")
        return post_record
            
    async def _generate_and_post(self, content_type: str) -> Dict[str, Any]:
        """Generate content and post it to Twitter and/or webhook.
        
        Priority order:
        1. AI-generated content with current album and track context
        2. Optional curated campaign posts when PAPITO_USE_CURATED_CAMPAIGN=true
        3. Optional static promo rotation when PAPITO_USE_STATIC_PROMOS=true
        
        Args:
            content_type: Type of content to generate
            
        Returns:
            Result of the posting attempt
        """
        logger.info(f"🎵 Generating {content_type} content...")
        
        try:
            # ── PRIORITY 1: Use curated campaign posts (authentic, on-brand) ──
            settings = get_settings()
            use_curated = os.getenv("PAPITO_USE_CURATED_CAMPAIGN", "false").strip().lower() in {
                "1", "true", "yes", "y", "on"
            }
            use_static_promos = os.getenv("PAPITO_USE_STATIC_PROMOS", "false").strip().lower() in {
                "1", "true", "yes", "y", "on"
            }

            curated_post = None
            curated_day = None
            if use_curated:
                try:
                    from ..content.curated_campaign import get_next_curated_post
                    curated_post = get_next_curated_post(content_type=content_type)
                except Exception as e:
                    logger.debug(f"Curated campaign not available: {e}")

            if curated_post:
                post_text = curated_post["text"]
                full_post = post_text
                hashtags = ""
                generation_method = f"curated_campaign_day_{curated_post['day']}"
                curated_day = curated_post["day"]
                logger.info(f"📋 Using curated Day {curated_day} post ({curated_post['content_type']})")
            # ── PRIORITY 2: Single promo rotation ──
            elif content_type == "single_promo" and use_static_promos:
                full_post = self.CLEAN_MONEY_PROMOS[self._promo_index % len(self.CLEAN_MONEY_PROMOS)]
                self._promo_index += 1
                post_text = full_post
                hashtags = ""
                generation_method = "promo_rotation"
            # ── PRIORITY 3: AI-generated content (fallback) ──
            else:
                # Import here to avoid circular imports
                from ..intelligence.content_generator import IntelligentContentGenerator, PapitoContext
                
                # Create context in the public timezone and use the configured
                # OpenAI key when available.
                context = PapitoContext(current_date=self._now())
                generator = IntelligentContentGenerator(openai_api_key=settings.openai_api_key)
                generation_content_type = "album_promo" if content_type == "single_promo" else content_type

                # Generate with retries to avoid near-duplicate posts.
                last_result: Dict[str, Any] | None = None
                for _ in range(4):
                    last_result = await generator.generate_post(
                        content_type=generation_content_type,
                        context=context,
                        include_album_mention=True,
                        platform="x",
                    )
                    candidate = (last_result or {}).get("text", "")
                    if self._post_memory and (
                        self._post_memory.is_repeated(candidate) or self._post_memory.is_too_similar(candidate)
                    ):
                        continue
                    break

                result = last_result or {}

                post_text = result.get("text", "")
                # Strictly limit hashtags for X (avoid spam / repetition)
                raw_tags = result.get("hashtags", [])
                tags: List[str]
                if isinstance(raw_tags, list):
                    tags = [str(t) for t in raw_tags if t]
                elif isinstance(raw_tags, str):
                    tags = [t for t in raw_tags.split() if t.startswith("#")]
                else:
                    tags = []
                hashtags = " ".join(tags[:2])
                full_post = f"{post_text}\n\n{hashtags}" if hashtags else post_text
                generation_method = result.get("generation_method", "intelligent")

            post_text = sanitize_public_text(post_text, max_length=260)
            hashtags = sanitize_public_text(hashtags if "hashtags" in locals() else "")
            full_post = sanitize_public_text(full_post, max_length=280)
            if not full_post:
                return {
                    "timestamp": self._now().isoformat(),
                    "content_type": content_type,
                    "error": "Empty generated post after sanitization",
                    "posted": False,
                }
            
            logger.info(f"✅ Generated: {post_text[:80]}...")
            
            # Record the post
            post_record = {
                "timestamp": self._now().isoformat(),
                "content_type": content_type,
                "text": post_text,
                "hashtags": hashtags if 'hashtags' in dir() else "",
                "generation_method": generation_method,
                "posted": False,
                "platforms": [],
                "error": None,
            }
            
            # === PRIMARY: Post to Buffer (Webhook or API) to save Twitter quota ===
            posted_via_buffer = False
            
            # 1. Try Webhook first (most robust for automation)
            if self.buffer_webhook_url:
                fallback = await self._post_to_buffer_fallback(full_post, content_type)
                if fallback.get("success"):
                    post_record["posted"] = True
                    post_record["platforms"].append("buffer_webhook")
                    post_record["buffer_method"] = "webhook"
                    posted_via_buffer = True
                    logger.info("📤 Posted via Buffer Webhook (Primary)")
                else:
                    logger.warning(f"Buffer Webhook failed: {fallback.get('error')}")
            
            # 2. If Webhook unavailable or failed, try Buffer API directly
            if not posted_via_buffer:
                publisher = self._get_buffer_publisher()
                if publisher and publisher.is_connected():
                    fallback = await self._post_to_buffer_fallback(full_post, content_type)
                    if fallback.get("success"):
                        post_record["posted"] = True
                        post_record["platforms"].append("buffer_api")
                        post_record["buffer_method"] = fallback.get("method")
                        if fallback.get("post_url"):
                            post_record["buffer_post_url"] = fallback.get("post_url")
                        posted_via_buffer = True
                        logger.info("📤 Posted via Buffer API (Primary/Fallback)")
                    else:
                         post_record["buffer_error"] = fallback.get("error")
                         logger.warning(f"Buffer API failed: {fallback.get('error')}")

            # === FALLBACK: Post to Twitter Direct (Only if Buffer failed) ===
            if not post_record["posted"]:
                logger.info("⚠️ All Buffer methods failed or not configured. Attempting direct Twitter post...")
                twitter_result = await self._post_to_twitter(full_post)
                if twitter_result["success"]:
                    post_record["posted"] = True
                    post_record["platforms"].append("twitter")
                    post_record["tweet_url"] = twitter_result.get("tweet_url")
                    logger.info(f"📱 Posted to Twitter (Direct Fallback): {twitter_result.get('tweet_url')}")
                else:
                    logger.warning(f"Twitter failed: {twitter_result.get('error')}")
                    post_record["twitter_error"] = twitter_result.get("error")
            
            if not post_record["posted"]:
                post_record["error"] = "Failed to post to any platform"
            
            self._last_posts[content_type] = self._now()
            self._post_history.append(post_record)
            if self._post_memory:
                self._post_memory.record(post_text, kind=f"scheduled:{content_type}")
            
            # Mark curated campaign post as used (only after successful post)
            if post_record["posted"] and curated_day is not None:
                try:
                    from ..content.curated_campaign import mark_post_as_used
                    mark_post_as_used(curated_day)
                except Exception as e:
                    logger.warning(f"Could not mark curated Day {curated_day} as used: {e}")
            
            # Keep only last 100 posts in history
            if len(self._post_history) > 100:
                self._post_history = self._post_history[-100:]
                
            return post_record
            
        except Exception as e:
            logger.error(f"Failed to generate {content_type}: {e}")
            error_record = {
                "timestamp": self._now().isoformat(),
                "content_type": content_type,
                "error": str(e),
                "posted": False,
            }
            self._post_history.append(error_record)
            return error_record
    
    async def _log_status(self) -> None:
        """Log scheduler status."""
        now = self._now()
        twitter_status = "Connected" if (self._twitter_publisher and self._twitter_publisher.is_connected) else "Not connected"
        
        logger.info(f"Scheduler status at {now.strftime('%Y-%m-%d %H:%M:%S')} {AGENT_TIMEZONE}")
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
        
        text = sanitize_public_text(text, max_length=280)
        if not text:
            return {"success": False, "error": "Empty custom post after sanitization"}

        post_record = {
            "timestamp": self._now().isoformat(),
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
        now = self._now()
        next_posts = []
        
        for hour, content_type in sorted(self.POSTING_SCHEDULE.items()):
            # Create datetime for today at this hour
            post_time = now.replace(hour=hour, minute=0, second=0, microsecond=0)
            if post_time < now:
                # Already passed today, schedule for tomorrow
                post_time += timedelta(days=1)
            
            next_posts.append({
                "content_type": content_type,
                "scheduled_time": f"{post_time.strftime('%Y-%m-%d %H:%M')} {AGENT_TIMEZONE}",
                "hours_until": round((post_time - now).total_seconds() / 3600, 1),
            })
        
        twitter_connected = self._twitter_publisher and self._twitter_publisher.is_connected
        twitter_username = self._twitter_publisher.username if twitter_connected else None
            
        return {
            "is_running": self._is_running,
            "timezone": AGENT_TIMEZONE,
            "current_time": now.strftime("%Y-%m-%d %H:%M:%S"),
            "current_time_wat": now.strftime("%Y-%m-%d %H:%M:%S"),
            "twitter_connected": twitter_connected,
            "twitter_username": twitter_username,
            "total_posts_generated": len(self._post_history),
            "posts_successfully_sent": sum(1 for p in self._post_history if p.get("posted")),
            "webhook_configured": bool(self.buffer_webhook_url),
            "next_scheduled_posts": sorted(next_posts, key=lambda x: x["hours_until"])[:5],
            "recent_posts": self._post_history[-5:] if self._post_history else [],
            "daily_schedule": [
                {"time": f"{h}:00 {AGENT_TIMEZONE}", "content": ct.replace("_", " ").title()}
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
