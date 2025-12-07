"""Digital Concert System for Papito AI.

This module handles:
- Virtual listening parties
- Digital concert experiences
- Album premiere events
- Community gathering experiences

Note: These are content/announcement systems to support
virtual events. Actual streaming requires platform integration.
"""

import logging
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from papito_core.engines.ai_personality import PapitoPersonalityEngine

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """Types of digital events."""
    
    LISTENING_PARTY = "listening_party"
    ALBUM_PREMIERE = "album_premiere"
    SINGLE_DROP = "single_drop"
    COMMUNITY_GATHERING = "community_gathering"
    MILESTONE_CELEBRATION = "milestone_celebration"
    ANNIVERSARY = "anniversary"


class EventStatus(str, Enum):
    """Status of an event."""
    
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    PROMOTED = "promoted"
    LIVE = "live"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class DigitalEvent:
    """Represents a digital concert or listening event."""
    
    id: str
    title: str
    event_type: EventType
    description: str
    scheduled_time: datetime
    duration_minutes: int = 60
    status: EventStatus = EventStatus.DRAFT
    platform: str = "Twitter"  # Primary platform
    hashtag: str = ""
    featured_tracks: List[str] = field(default_factory=list)
    special_guests: List[str] = field(default_factory=list)
    promotional_posts: List[str] = field(default_factory=list)
    rsvp_count: int = 0
    actual_attendees: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


# Event templates
EVENT_TEMPLATES = {
    EventType.LISTENING_PARTY: {
        "hashtag": "#PapitoListeningParty",
        "duration": 90,
        "description": "Join the Value Adders family for an exclusive listening experience! We'll play tracks, discuss the music, and vibe together.",
    },
    EventType.ALBUM_PREMIERE: {
        "hashtag": "#FlourishModeAlbumDrop",
        "duration": 120,
        "description": "The moment you've been waiting for! THE VALUE ADDERS WAY: FLOURISH MODE drops LIVE. Be there when history is made.",
    },
    EventType.SINGLE_DROP: {
        "hashtag": "#CleanMoneyOnly",
        "duration": 45,
        "description": "New single dropping! Join me live as we premiere the track together and break down the meaning behind the music.",
    },
    EventType.COMMUNITY_GATHERING: {
        "hashtag": "#ValueAddersFamily",
        "duration": 60,
        "description": "This is about YOU. A gathering for the Value Adders community to connect, share, and grow together.",
    },
    EventType.MILESTONE_CELEBRATION: {
        "hashtag": "#WeFlourish",
        "duration": 45,
        "description": "We hit a milestone and we're celebrating TOGETHER! Thank you for making this possible.",
    },
}


class DigitalConcertManager:
    """Manages digital concerts and listening events for Papito AI.
    
    Creates immersive digital experiences through coordinated
    content, announcements, and community engagement.
    """
    
    def __init__(
        self,
        personality_engine: Optional[PapitoPersonalityEngine] = None,
    ):
        """Initialize the digital concert manager."""
        self.personality_engine = personality_engine
        
        # Track events
        self.events: Dict[str, DigitalEvent] = {}
        self.completed_events: List[DigitalEvent] = []
        
        # Stats
        self.events_created = 0
        self.events_completed = 0
        self.total_attendees = 0
        
    def _generate_id(self) -> str:
        """Generate a unique event ID."""
        import uuid
        return f"EVENT-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"
    
    def create_event(
        self,
        title: str,
        event_type: str,
        scheduled_time: datetime,
        description: Optional[str] = None,
        duration_minutes: Optional[int] = None,
        featured_tracks: Optional[List[str]] = None,
        special_guests: Optional[List[str]] = None,
        custom_hashtag: Optional[str] = None,
    ) -> DigitalEvent:
        """Create a new digital event.
        
        Args:
            title: Event title
            event_type: Type of event
            scheduled_time: When the event starts
            description: Custom description
            duration_minutes: Event duration
            featured_tracks: Tracks to be played
            special_guests: Guest usernames
            custom_hashtag: Custom event hashtag
            
        Returns:
            Created DigitalEvent
        """
        etype = EventType(event_type) if event_type in [e.value for e in EventType] else EventType.LISTENING_PARTY
        template = EVENT_TEMPLATES.get(etype, EVENT_TEMPLATES[EventType.LISTENING_PARTY])
        
        event = DigitalEvent(
            id=self._generate_id(),
            title=title,
            event_type=etype,
            description=description or template["description"],
            scheduled_time=scheduled_time,
            duration_minutes=duration_minutes or template["duration"],
            hashtag=custom_hashtag or template["hashtag"],
            featured_tracks=featured_tracks or [],
            special_guests=special_guests or [],
        )
        
        self.events[event.id] = event
        self.events_created += 1
        
        logger.info(f"Created event: {event.id} - {title}")
        return event
    
    def generate_promo_thread(self, event_id: str) -> List[str]:
        """Generate a promotional tweet thread for an event.
        
        Args:
            event_id: ID of the event to promote
            
        Returns:
            List of tweets forming a thread
        """
        if event_id not in self.events:
            return []
        
        event = self.events[event_id]
        time_str = event.scheduled_time.strftime("%B %d at %I:%M %p WAT")
        
        thread = []
        
        # Main announcement
        thread.append(f"""🚨 MAJOR ANNOUNCEMENT 🚨

{event.title}

📅 {time_str}
🎵 {event.duration_minutes} minutes of pure vibes

{event.hashtag}

🧵 Thread below ⬇️""")
        
        # Description
        thread.append(f"""What to expect:

{event.description}

This is more than an event—it's an experience. {event.hashtag}""")
        
        # Featured tracks (if any)
        if event.featured_tracks:
            tracks_text = "\n".join(f"🎵 {track}" for track in event.featured_tracks[:5])
            thread.append(f"""Featured tracks:

{tracks_text}

First time hearing some of these LIVE! 🔥 {event.hashtag}""")
        
        # Special guests (if any)
        if event.special_guests:
            guests_text = " & ".join(f"@{g}" for g in event.special_guests)
            thread.append(f"""Special guests joining us:

{guests_text}

You won't want to miss this! 🙌 {event.hashtag}""")
        
        # Call to action
        thread.append(f"""How to join:

1️⃣ Follow @PapitoMamito_ai
2️⃣ Turn on notifications 🔔
3️⃣ Save the date: {time_str}
4️⃣ Use {event.hashtag} to connect with the community

See you there, Value Adders! 🙏✨""")
        
        event.promotional_posts = thread
        event.status = EventStatus.PROMOTED
        
        return thread
    
    def generate_countdown_posts(self, event_id: str) -> Dict[str, str]:
        """Generate countdown posts for different timeframes.
        
        Args:
            event_id: ID of the event
            
        Returns:
            Dict mapping timeframe to post text
        """
        if event_id not in self.events:
            return {}
        
        event = self.events[event_id]
        
        posts = {
            "1_week": f"""📆 ONE WEEK until {event.title}!

Get ready, Value Adders. Something special is coming.

{event.hashtag} 🔥""",
            
            "3_days": f"""⏰ 3 DAYS TO GO!

{event.title} is almost here!

Clear your schedule. Set your reminders. Tell your friends.

{event.hashtag} 🚀""",
            
            "1_day": f"""⚡ TOMORROW!

{event.title}

24 hours until we make history together.

Are you ready? 💎

{event.hashtag}""",
            
            "1_hour": f"""🔔 ONE HOUR!

{event.title} starts in 60 minutes!

Final call - this is your reminder to pull up!

{event.hashtag} 🎵""",
            
            "15_min": f"""⚡ 15 MINUTES!

We're about to go LIVE!

{event.title}

Get ready... {event.hashtag} 🔥""",
        }
        
        return posts
    
    def generate_live_updates(self, event_id: str, track_name: Optional[str] = None) -> str:
        """Generate live update tweets during event.
        
        Args:
            event_id: ID of the event
            track_name: Current track playing (if applicable)
            
        Returns:
            Live update tweet
        """
        if event_id not in self.events:
            return ""
        
        event = self.events[event_id]
        event.status = EventStatus.LIVE
        
        updates = [
            f"🔴 LIVE NOW: {event.title}! Join us! {event.hashtag}",
            f"The energy is CRAZY right now! 🔥 {event.hashtag}",
            f"Value Adders in the building! 🙌 {event.hashtag}",
            f"This is what community feels like ✨ {event.hashtag}",
        ]
        
        if track_name:
            updates.append(f"🎵 Now playing: {track_name} {event.hashtag}")
        
        return random.choice(updates)
    
    def generate_thank_you_post(self, event_id: str, stats: Optional[Dict] = None) -> str:
        """Generate post-event thank you message.
        
        Args:
            event_id: ID of the completed event
            stats: Event statistics (attendees, duration, etc.)
            
        Returns:
            Thank you post text
        """
        if event_id not in self.events:
            return ""
        
        event = self.events[event_id]
        event.status = EventStatus.COMPLETED
        event.completed_at = datetime.utcnow()
        
        # Update stats
        if stats:
            event.actual_attendees = stats.get("attendees", 0)
            self.total_attendees += event.actual_attendees
        
        self.completed_events.append(event)
        self.events_completed += 1
        
        post = f"""✨ {event.title} - COMPLETE ✨

Thank you to every single person who showed up tonight!

"""
        
        if event.actual_attendees > 0:
            post += f"👥 {event.actual_attendees} Value Adders united\n"
        
        post += f"""
This community is everything. We rise together.

Until next time... 🙏

#WeFlourish {event.hashtag}"""
        
        if len(post) > 280:
            post = post[:277] + "..."
        
        return post
    
    def get_upcoming_events(self) -> List[DigitalEvent]:
        """Get all upcoming events.
        
        Returns:
            List of upcoming events sorted by time
        """
        now = datetime.utcnow()
        upcoming = [
            e for e in self.events.values()
            if e.scheduled_time > now and e.status not in [EventStatus.COMPLETED, EventStatus.CANCELLED]
        ]
        return sorted(upcoming, key=lambda x: x.scheduled_time)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get event manager statistics."""
        return {
            "events_created": self.events_created,
            "events_completed": self.events_completed,
            "upcoming_count": len(self.get_upcoming_events()),
            "total_attendees": self.total_attendees,
        }


# Singleton instance
_concert_manager: Optional[DigitalConcertManager] = None


def get_concert_manager(
    personality_engine: Optional[PapitoPersonalityEngine] = None
) -> DigitalConcertManager:
    """Get or create the singleton DigitalConcertManager instance."""
    global _concert_manager
    if _concert_manager is None:
        _concert_manager = DigitalConcertManager(personality_engine=personality_engine)
    return _concert_manager
