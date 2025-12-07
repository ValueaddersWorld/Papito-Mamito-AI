"""Twitter Spaces Manager for Papito AI.

This module handles:
- Planning and scheduling Twitter Spaces
- Managing Space topics and formats
- Tracking Space attendance and metrics
- Generating Space announcements
- Post-Space follow-up content

Note: Twitter Spaces API is limited. This module prepares content
and announcements; actual Space hosting requires manual action or
elevated API access.
"""

import logging
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from papito_core.engines.ai_personality import PapitoPersonalityEngine

logger = logging.getLogger(__name__)


class SpaceType(str, Enum):
    """Types of Twitter Spaces Papito can host."""
    
    LISTENING_PARTY = "listening_party"
    FAN_QA = "fan_qa"
    INDUSTRY_DISCUSSION = "industry_discussion"
    ALBUM_PREVIEW = "album_preview"
    COLLABORATION_SHOWCASE = "collaboration_showcase"
    FREESTYLE_VIBES = "freestyle_vibes"
    VALUE_ADDERS_TALK = "value_adders_talk"


class SpaceStatus(str, Enum):
    """Status of a scheduled Space."""
    
    PLANNED = "planned"
    ANNOUNCED = "announced"
    LIVE = "live"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class ScheduledSpace:
    """Represents a planned or completed Twitter Space."""
    
    id: str
    title: str
    space_type: SpaceType
    description: str
    scheduled_time: datetime
    duration_minutes: int = 60
    status: SpaceStatus = SpaceStatus.PLANNED
    co_hosts: List[str] = field(default_factory=list)  # Usernames
    topics: List[str] = field(default_factory=list)
    announcement_tweet: Optional[str] = None
    reminder_tweet: Optional[str] = None
    space_id: Optional[str] = None  # Twitter Space ID once created
    attendees: int = 0
    peak_listeners: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    notes: str = ""


# Space format templates
SPACE_FORMATS = {
    SpaceType.LISTENING_PARTY: {
        "title_templates": [
            "🎧 FLOURISH MODE Listening Party",
            "🎵 Clean Money Only - First Listen Party",
            "✨ New Music Experience with Papito",
        ],
        "description": "Join me for an exclusive listening experience! We'll play tracks, discuss the meaning behind the music, and vibe together as a community.",
        "topics": ["music", "album", "afrobeat", "listening", "community"],
        "default_duration": 60,
    },
    SpaceType.FAN_QA: {
        "title_templates": [
            "💬 Ask Papito Anything",
            "🗣️ Value Adders Q&A Session",
            "❓ Fan Questions Live",
        ],
        "description": "Your chance to ask me anything! Life, music, AI, the Value Adders philosophy - nothing is off limits (within reason 😄).",
        "topics": ["qa", "fans", "questions", "community", "interaction"],
        "default_duration": 45,
    },
    SpaceType.INDUSTRY_DISCUSSION: {
        "title_templates": [
            "🎤 The Future of Afrobeat",
            "🌍 AI in Music: Revolution or Evolution?",
            "💎 Building a Career in African Music",
        ],
        "description": "Let's discuss the state of the music industry, the rise of Afrobeat globally, and what it means for artists and fans.",
        "topics": ["industry", "afrobeat", "music business", "AI", "future"],
        "default_duration": 75,
    },
    SpaceType.ALBUM_PREVIEW: {
        "title_templates": [
            "🚀 FLOURISH MODE: Exclusive Preview",
            "✈️ FlightMode6000: Album Breakdown",
            "🔥 THE VALUE ADDERS WAY: Track by Track",
        ],
        "description": "Get an exclusive look at the upcoming album! Hear snippets, learn the stories behind the tracks, and be the first to experience the vision.",
        "topics": ["album", "preview", "exclusive", "flourish mode", "music"],
        "default_duration": 90,
    },
    SpaceType.COLLABORATION_SHOWCASE: {
        "title_templates": [
            "🤝 Collab Corner: Meet the Artists",
            "🎵 Featuring Friends: Collab Showcase",
        ],
        "description": "Introducing artists I'm working with or who inspire me. We'll talk music, creativity, and the collaborative process.",
        "topics": ["collaboration", "artists", "features", "music", "networking"],
        "default_duration": 60,
    },
    SpaceType.FREESTYLE_VIBES: {
        "title_templates": [
            "🎤 Freestyle Friday with Papito",
            "🔥 Late Night Vibes Session",
            "✨ Musical Meditation Space",
        ],
        "description": "Let's keep it loose! We'll play music, share thoughts, and just vibe with whoever shows up. Good energy only.",
        "topics": ["freestyle", "vibes", "relaxed", "music", "community"],
        "default_duration": 45,
    },
    SpaceType.VALUE_ADDERS_TALK: {
        "title_templates": [
            "💡 Add Value: Life Wisdom Session",
            "🌟 Flourish Mode Mindset",
            "📈 How to Add Value in Everything",
        ],
        "description": "Beyond music - let's talk about the Value Adders philosophy. Success, purpose, adding value, and living with intention.",
        "topics": ["philosophy", "value", "mindset", "success", "purpose"],
        "default_duration": 60,
    },
}


class SpacesManager:
    """Manages Twitter Spaces planning and content for Papito AI.
    
    Handles Space scheduling, announcements, and post-Space content.
    Note: Actual Space hosting requires Twitter's Space API or manual action.
    """
    
    def __init__(
        self,
        personality_engine: Optional[PapitoPersonalityEngine] = None,
    ):
        """Initialize the Spaces manager."""
        self.personality_engine = personality_engine
        
        # Track Spaces
        self.scheduled_spaces: Dict[str, ScheduledSpace] = {}
        self.completed_spaces: List[ScheduledSpace] = []
        
        # Stats
        self.spaces_planned = 0
        self.spaces_completed = 0
        self.total_attendees = 0
        
    def _generate_id(self) -> str:
        """Generate a unique Space ID."""
        import uuid
        return f"SPACE-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"
    
    def plan_space(
        self,
        space_type: str,
        scheduled_time: datetime,
        custom_title: Optional[str] = None,
        custom_description: Optional[str] = None,
        duration_minutes: int = 60,
        co_hosts: Optional[List[str]] = None,
        topics: Optional[List[str]] = None,
    ) -> ScheduledSpace:
        """Plan a new Twitter Space.
        
        Args:
            space_type: Type of Space to host
            scheduled_time: When to host the Space
            custom_title: Optional custom title
            custom_description: Optional custom description
            duration_minutes: Expected duration
            co_hosts: Optional list of co-host usernames
            topics: Optional custom topics
            
        Returns:
            Created ScheduledSpace
        """
        stype = SpaceType(space_type) if space_type in [e.value for e in SpaceType] else SpaceType.FAN_QA
        format_info = SPACE_FORMATS.get(stype, SPACE_FORMATS[SpaceType.FAN_QA])
        
        # Generate title
        if custom_title:
            title = custom_title
        else:
            title = random.choice(format_info["title_templates"])
        
        # Generate description
        description = custom_description or format_info["description"]
        
        space = ScheduledSpace(
            id=self._generate_id(),
            title=title,
            space_type=stype,
            description=description,
            scheduled_time=scheduled_time,
            duration_minutes=duration_minutes or format_info["default_duration"],
            co_hosts=co_hosts or [],
            topics=topics or format_info["topics"],
        )
        
        self.scheduled_spaces[space.id] = space
        self.spaces_planned += 1
        
        logger.info(f"Planned Space: {space.id} - {title} at {scheduled_time}")
        return space
    
    def generate_announcement(self, space_id: str) -> str:
        """Generate an announcement tweet for a Space.
        
        Args:
            space_id: ID of the Space to announce
            
        Returns:
            Announcement tweet text
        """
        if space_id not in self.scheduled_spaces:
            return ""
        
        space = self.scheduled_spaces[space_id]
        
        # Format time
        time_str = space.scheduled_time.strftime("%A, %B %d at %I:%M %p WAT")
        
        # Build announcement
        announcement_templates = [
            f"""🎙️ SPACE ALERT!

{space.title}

📅 {time_str}
⏱️ {space.duration_minutes} minutes

{space.description[:100]}...

Set your reminders! 🔔

#PapitoSpace #ValueAdders #FlightMode6000""",

            f"""🚀 JOIN ME LIVE!

{space.title}

When: {time_str}

{space.description[:80]}...

{"Co-hosting with: " + ", ".join(f"@{h}" for h in space.co_hosts) if space.co_hosts else ""}

Drop a 🔥 if you'll be there!

#TwitterSpaces #Afrobeat""",

            f"""✨ SPACE INCOMING ✨

{space.title}

🗓️ {time_str}
🎵 Topics: {", ".join(space.topics[:3])}

This is your invitation to the Value Adders community gathering!

#FlourishMode #PapitoMamito""",
        ]
        
        announcement = random.choice(announcement_templates)
        
        # Ensure under 280 chars
        if len(announcement) > 280:
            announcement = announcement[:277] + "..."
        
        space.announcement_tweet = announcement
        space.status = SpaceStatus.ANNOUNCED
        
        return announcement
    
    def generate_reminder(self, space_id: str, minutes_until: int = 30) -> str:
        """Generate a reminder tweet for an upcoming Space.
        
        Args:
            space_id: ID of the Space
            minutes_until: Minutes until the Space starts
            
        Returns:
            Reminder tweet text
        """
        if space_id not in self.scheduled_spaces:
            return ""
        
        space = self.scheduled_spaces[space_id]
        
        reminder_templates = [
            f"""⏰ {minutes_until} MINUTES!

{space.title} is about to start!

Jump in when we go live! 🎙️

#PapitoSpace #ValueAdders""",

            f"""🔔 REMINDER: Going live in {minutes_until} mins!

{space.title}

Don't miss this! 🚀

#TwitterSpaces #Afrobeat""",

            f"""⚡ ALMOST TIME!

Starting {space.title} in {minutes_until} minutes!

This is your final call, Value Adders! 🙌

#FlourishMode""",
        ]
        
        reminder = random.choice(reminder_templates)
        space.reminder_tweet = reminder
        
        return reminder
    
    def generate_live_announcement(self, space_id: str) -> str:
        """Generate a 'we're live' tweet.
        
        Args:
            space_id: ID of the Space
            
        Returns:
            Live announcement tweet
        """
        if space_id not in self.scheduled_spaces:
            return ""
        
        space = self.scheduled_spaces[space_id]
        space.status = SpaceStatus.LIVE
        
        live_templates = [
            f"""🔴 WE ARE LIVE!

{space.title}

Join now! Link in bio 👆

#PapitoLive #TwitterSpaces""",

            f"""🎙️ LIVE NOW!

{space.title}

The Space is open - pull up! 🚀

#ValueAdders #FlourishMode""",
        ]
        
        return random.choice(live_templates)
    
    def generate_recap(self, space_id: str, highlights: Optional[List[str]] = None) -> str:
        """Generate a post-Space recap tweet.
        
        Args:
            space_id: ID of the completed Space
            highlights: Optional list of highlights from the Space
            
        Returns:
            Recap tweet text
        """
        if space_id not in self.scheduled_spaces:
            return ""
        
        space = self.scheduled_spaces[space_id]
        space.status = SpaceStatus.COMPLETED
        space.completed_at = datetime.utcnow()
        
        self.completed_spaces.append(space)
        self.spaces_completed += 1
        if space.peak_listeners > 0:
            self.total_attendees += space.peak_listeners
        
        # Build recap
        recap = f"""✨ SPACE COMPLETE!

Thank you to everyone who joined {space.title}!

"""
        
        if space.peak_listeners > 0:
            recap += f"👥 Peak listeners: {space.peak_listeners}\n"
        
        if highlights:
            recap += "\n🔥 Highlights:\n"
            for h in highlights[:3]:
                recap += f"• {h}\n"
        
        recap += "\nUntil next time, keep adding value! 🙏\n\n#ValueAdders #FlourishMode"
        
        if len(recap) > 280:
            recap = recap[:277] + "..."
        
        return recap
    
    def get_upcoming_spaces(self) -> List[ScheduledSpace]:
        """Get all upcoming scheduled Spaces.
        
        Returns:
            List of upcoming Spaces sorted by time
        """
        now = datetime.utcnow()
        upcoming = [
            s for s in self.scheduled_spaces.values()
            if s.scheduled_time > now and s.status in [SpaceStatus.PLANNED, SpaceStatus.ANNOUNCED]
        ]
        return sorted(upcoming, key=lambda x: x.scheduled_time)
    
    def suggest_space_ideas(self, count: int = 3) -> List[Dict[str, Any]]:
        """Suggest Space ideas based on current context.
        
        Args:
            count: Number of suggestions to return
            
        Returns:
            List of Space suggestions
        """
        suggestions = []
        
        # Always suggest these core types
        core_types = [
            SpaceType.FAN_QA,
            SpaceType.LISTENING_PARTY,
            SpaceType.VALUE_ADDERS_TALK,
        ]
        
        for stype in core_types[:count]:
            format_info = SPACE_FORMATS[stype]
            suggestions.append({
                "type": stype.value,
                "title": random.choice(format_info["title_templates"]),
                "description": format_info["description"],
                "suggested_duration": format_info["default_duration"],
                "topics": format_info["topics"],
            })
        
        return suggestions
    
    def get_stats(self) -> Dict[str, Any]:
        """Get Spaces manager statistics."""
        return {
            "spaces_planned": self.spaces_planned,
            "spaces_completed": self.spaces_completed,
            "upcoming_count": len(self.get_upcoming_spaces()),
            "total_attendees": self.total_attendees,
        }


# Singleton instance
_spaces_manager: Optional[SpacesManager] = None


def get_spaces_manager(
    personality_engine: Optional[PapitoPersonalityEngine] = None
) -> SpacesManager:
    """Get or create the singleton SpacesManager instance."""
    global _spaces_manager
    if _spaces_manager is None:
        _spaces_manager = SpacesManager(personality_engine=personality_engine)
    return _spaces_manager
