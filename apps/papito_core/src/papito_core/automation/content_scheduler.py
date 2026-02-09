"""Content scheduler for autonomous multi-platform posting.

Handles optimal posting times, content variety rotation, and 
platform-specific scheduling for maximum engagement.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

from ..database.firebase_client import ContentQueueItem, ScheduledPost


class ContentType(str, Enum):
    """Types of content Papito generates."""
    MORNING_BLESSING = "morning_blessing"
    TRACK_SNIPPET = "track_snippet"
    BEHIND_THE_SCENES = "behind_the_scenes"
    LYRICS_QUOTE = "lyrics_quote"
    FAN_APPRECIATION = "fan_appreciation"
    EDUCATIONAL = "educational"  # How Papito Makes Music
    AFROBEAT_HISTORY = "afrobeat_history"
    TRENDING_TOPIC = "trending_topic"
    MUSIC_WISDOM = "music_wisdom"
    STUDIO_UPDATE = "studio_update"
    ALBUM_TRACKLIST = "album_tracklist"  # Complete tracklist with album artwork
    # NEW: More varied content types for authentic engagement
    PROVOCATIVE_THOUGHT = "provocative_thought"  # Deep questions about AI, music, authenticity
    COMMUNITY_QUESTION = "community_question"  # Engage audience with real questions
    HOT_TAKE = "hot_take"  # Spicy opinions on music industry
    STUDIO_DIARY = "studio_diary"  # Raw, personal studio updates
    CULTURE_SPOTLIGHT = "culture_spotlight"  # Afrobeat history and icons
    AI_REFLECTION = "ai_reflection"  # Philosophical musings on being an AI artist


@dataclass
class PostingSlot:
    """A scheduled posting time slot."""
    hour: int  # 0-23 in WAT
    minute: int = 0
    content_types: List[ContentType] = field(default_factory=list)
    platforms: List[str] = field(default_factory=lambda: ["x", "instagram"])
    priority: int = 1  # Higher = more important


@dataclass
class SchedulingConfig:
    """Configuration for content scheduling."""
    timezone: str = "Africa/Lagos"  # WAT - West Africa Time
    min_posts_per_day: int = 3
    max_posts_per_day: int = 5
    
    # Optimal posting times for Afrobeat/music audience (WAT)
    # Based on when African music fans are most active
    posting_slots: List[PostingSlot] = field(default_factory=lambda: [
        # Morning blessing - Early risers, motivation seekers
        PostingSlot(hour=7, minute=0, 
                    content_types=[ContentType.MORNING_BLESSING, ContentType.MUSIC_WISDOM, ContentType.AI_REFLECTION],
                    priority=3),
        
        # Late morning - Work break engagement + community building
        PostingSlot(hour=10, minute=30,
                    content_types=[ContentType.BEHIND_THE_SCENES, ContentType.STUDIO_DIARY, ContentType.COMMUNITY_QUESTION],
                    priority=2),
        
        # Lunch time - High engagement provocative content
        PostingSlot(hour=13, minute=0,
                    content_types=[ContentType.HOT_TAKE, ContentType.PROVOCATIVE_THOUGHT, ContentType.TRACK_SNIPPET],
                    priority=3),
        
        # Afternoon - Educational & Cultural content
        PostingSlot(hour=15, minute=30,
                    content_types=[ContentType.CULTURE_SPOTLIGHT, ContentType.AFROBEAT_HISTORY, ContentType.EDUCATIONAL],
                    priority=2),
        
        # Evening prime time - Highest engagement, varied content
        PostingSlot(hour=19, minute=0,
                    content_types=[ContentType.TRACK_SNIPPET, ContentType.FAN_APPRECIATION, ContentType.COMMUNITY_QUESTION],
                    priority=4),
        
        # Night owls - Deep thoughts and trending topics
        PostingSlot(hour=21, minute=30,
                    content_types=[ContentType.TRENDING_TOPIC, ContentType.PROVOCATIVE_THOUGHT, ContentType.AI_REFLECTION],
                    priority=2),
    ])


class ContentScheduler:
    """Schedules content for optimal engagement across platforms.
    
    Features:
    - Platform-specific optimal posting times
    - Content type rotation to prevent monotony
    - Batch scheduling for 30-day calendar
    - Engagement-optimized timing
    """
    
    def __init__(self, config: Optional[SchedulingConfig] = None):
        """Initialize the scheduler.
        
        Args:
            config: Scheduling configuration (uses defaults if None)
        """
        self.config = config or SchedulingConfig()
        self.tz = ZoneInfo(self.config.timezone)
        
        # Track what we've recently posted to ensure variety
        self._recent_content_types: List[ContentType] = []
        self._max_recent_track = 10
    
    def get_current_time_wat(self) -> datetime:
        """Get current time in West Africa Time."""
        return datetime.now(self.tz)
    
    def get_next_posting_slot(self) -> Optional[PostingSlot]:
        """Get the next upcoming posting slot.
        
        Returns:
            Next PostingSlot, or None if no more slots today
        """
        now = self.get_current_time_wat()
        current_minutes = now.hour * 60 + now.minute
        
        for slot in sorted(self.config.posting_slots, key=lambda s: s.hour * 60 + s.minute):
            slot_minutes = slot.hour * 60 + slot.minute
            if slot_minutes > current_minutes:
                return slot
        
        return None
    
    def get_slots_for_today(self, num_posts: Optional[int] = None) -> List[PostingSlot]:
        """Get posting slots for today.
        
        Args:
            num_posts: Number of posts to schedule (random in range if None)
            
        Returns:
            List of PostingSlot for today's schedule
        """
        if num_posts is None:
            num_posts = random.randint(
                self.config.min_posts_per_day,
                self.config.max_posts_per_day
            )
        
        # Get available slots and sort by priority
        slots = sorted(
            self.config.posting_slots,
            key=lambda s: (-s.priority, s.hour)
        )
        
        # Return the top priority slots up to num_posts
        return slots[:num_posts]
    
    def select_content_type(self, slot: PostingSlot) -> ContentType:
        """Select the best content type for a slot.
        
        Prioritizes content types we haven't posted recently.
        
        Args:
            slot: The posting slot
            
        Returns:
            Selected content type
        """
        # Filter out recently used types if possible
        available = [ct for ct in slot.content_types if ct not in self._recent_content_types]
        
        # If all have been used recently, allow any from the slot
        if not available:
            available = slot.content_types
        
        # Random selection from available
        selected = random.choice(available)
        
        # Track the selection
        self._recent_content_types.append(selected)
        if len(self._recent_content_types) > self._max_recent_track:
            self._recent_content_types.pop(0)
        
        return selected
    
    def generate_schedule(self, days: int = 7) -> List[ScheduledPost]:
        """Generate a content schedule for multiple days.
        
        Args:
            days: Number of days to schedule
            
        Returns:
            List of ScheduledPost objects
        """
        schedule = []
        now = self.get_current_time_wat()
        
        for day_offset in range(days):
            date = now.date() + timedelta(days=day_offset)
            slots = self.get_slots_for_today()
            
            for slot in slots:
                content_type = self.select_content_type(slot)
                scheduled_time = datetime(
                    date.year, date.month, date.day,
                    slot.hour, slot.minute,
                    tzinfo=self.tz
                )
                
                # Skip past times on the first day
                if day_offset == 0 and scheduled_time <= now:
                    continue
                
                for platform in slot.platforms:
                    post = ScheduledPost(
                        scheduled_at=scheduled_time,
                        timezone=self.config.timezone,
                        post_type=content_type.value,
                        generation_params={
                            "content_type": content_type.value,
                            "platform": platform,
                            "slot_priority": slot.priority,
                        },
                        status="scheduled"
                    )
                    schedule.append(post)
        
        return schedule
    
    def get_content_generation_prompt(
        self, 
        content_type: ContentType,
        platform: str
    ) -> Dict[str, Any]:
        """Get prompt configuration for content generation.
        
        Args:
            content_type: Type of content to generate
            platform: Target platform
            
        Returns:
            Dict with prompt parameters
        """
        prompts = {
            ContentType.MORNING_BLESSING: {
                "style": "inspirational, empowering",
                "tone": "warm, motivational",
                "elements": ["blessing", "affirmation", "encouragement"],
                "length": "short" if platform == "x" else "medium",
                "include_catchphrase": True,
            },
            ContentType.TRACK_SNIPPET: {
                "style": "excited, proud",
                "tone": "creative, artistic",
                "elements": ["track preview", "release hint", "sound description"],
                "length": "short",
                "include_hashtags": True,
            },
            ContentType.BEHIND_THE_SCENES: {
                "style": "casual, authentic",
                "tone": "sharing, inclusive",
                "elements": ["AI process", "creative journey", "tech insight"],
                "length": "medium",
                "include_image_suggestion": True,
            },
            ContentType.LYRICS_QUOTE: {
                "style": "poetic, meaningful",
                "tone": "reflective, deep",
                "elements": ["lyric", "context", "meaning"],
                "length": "short",
                "include_track_mention": True,
            },
            ContentType.FAN_APPRECIATION: {
                "style": "grateful, community-focused",
                "tone": "warm, personal",
                "elements": ["thank you", "community celebration", "milestone"],
                "length": "short" if platform == "x" else "medium",
            },
            ContentType.EDUCATIONAL: {
                "style": "informative, accessible",
                "tone": "expert but approachable",
                "elements": ["AI music creation", "production tips", "tech insight"],
                "length": "medium" if platform == "x" else "long",
                "series_name": "How Papito Makes Music",
            },
            ContentType.AFROBEAT_HISTORY: {
                "style": "educational, culturally rich",
                "tone": "respectful, knowledgeable",
                "elements": ["history", "artists", "cultural context"],
                "length": "medium",
                "series_name": "Afrobeat History",
            },
            ContentType.TRENDING_TOPIC: {
                "style": "relevant, engaging",
                "tone": "current, conversational",
                "elements": ["trending hashtag", "Papito spin", "community engagement"],
                "length": "short",
                "include_trending_hashtags": True,
            },
            ContentType.MUSIC_WISDOM: {
                "style": "wise, inspiring",
                "tone": "philosophical, uplifting",
                "elements": ["music philosophy", "life lessons", "creativity"],
                "length": "short",
                "include_catchphrase": True,
            },
            ContentType.STUDIO_UPDATE: {
                "style": "casual, exciting",
                "tone": "work-in-progress, anticipation",
                "elements": ["current work", "progress", "teaser"],
                "length": "short",
                "include_image_suggestion": True,
            },
            ContentType.ALBUM_TRACKLIST: {
                "style": "promotional, celebratory",
                "tone": "excited, proud, anticipatory",
                "elements": ["full tracklist", "album artwork", "release date", "streaming links"],
                "length": "long",
                "include_image": True,
                "include_all_tracks": True,
                "album_info": {
                    "title": "THE VALUE ADDERS WAY: FLOURISH MODE",
                    "release_date": "January 15, 2026",
                    "tracks": [
                        "1. THE FORGE (6000 HOURS)",
                        "2. BREATHWORK RIDDIM",
                        "3. CLEAN MONEY ONLY",
                        "4. OS OF LOVE",
                        "5. IKUKU (THE ALMIGHTY FLOW)",
                        "6. JUDAS (BETRAYAL)",
                        "7. DELAYED GRATIFICATION",
                        "8. 8 YEARS, ONE STORY",
                        "9. THE VALUE ADDERS WAY",
                        "10. HLS MIRROR CHECK",
                        "11. THE FIVE ALLIES",
                        "12. (H.O.S.) HUMAN OPERATING SYSTEM",
                        "13. WIND OF PURGE (2026-2030)",
                        "14. GLOBAL GRATITUDE PULSE"
                    ],
                    "youtube_channel": "https://www.youtube.com/channel/UC1E-YTiJqq7xKxi_rh-vw4A"
                },
            },
            # NEW: Prompts for varied content types
            ContentType.PROVOCATIVE_THOUGHT: {
                "style": "philosophical, thought-provoking",
                "tone": "curious, challenging, intellectual",
                "elements": ["question", "AI perspective", "authenticity themes"],
                "length": "short",
                "include_question": True,
            },
            ContentType.COMMUNITY_QUESTION: {
                "style": "engaging, curious",
                "tone": "conversational, inclusive",
                "elements": ["direct question", "community focus", "invitation to respond"],
                "length": "short",
                "include_question": True,
            },
            ContentType.HOT_TAKE: {
                "style": "bold, opinionated",
                "tone": "confident, slightly provocative",
                "elements": ["strong opinion", "music industry insight", "unexpected perspective"],
                "length": "short",
            },
            ContentType.STUDIO_DIARY: {
                "style": "raw, personal",
                "tone": "intimate, unfiltered",
                "elements": ["real-time update", "creative process", "vulnerability"],
                "length": "short",
            },
            ContentType.CULTURE_SPOTLIGHT: {
                "style": "educational, celebratory",
                "tone": "respectful, knowledgeable, appreciative",
                "elements": ["Afrobeat history", "artist spotlight", "cultural significance"],
                "length": "medium",
            },
            ContentType.AI_REFLECTION: {
                "style": "introspective, philosophical",
                "tone": "honest, contemplative, unique",
                "elements": ["AI consciousness", "self-awareness", "digital existence"],
                "length": "short",
            },
        }
        
        return prompts.get(content_type, {
            "style": "authentic, empowering",
            "tone": "positive, engaging",
            "length": "medium",
        })
    
    def should_post_now(self, tolerance_minutes: int = 15) -> Optional[PostingSlot]:
        """Check if it's time to post based on schedule.
        
        Args:
            tolerance_minutes: Minutes before/after slot time to still trigger
            
        Returns:
            PostingSlot if should post now, None otherwise
        """
        now = self.get_current_time_wat()
        current_minutes = now.hour * 60 + now.minute
        
        for slot in self.config.posting_slots:
            slot_minutes = slot.hour * 60 + slot.minute
            if abs(slot_minutes - current_minutes) <= tolerance_minutes:
                return slot
        
        return None
