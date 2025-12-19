"""Press Release Generator for Papito AI.

This module handles:
- Generating professional press releases
- Album announcement press releases
- Single release announcements
- Milestone celebrations
- Event announcements
"""

import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from papito_core.engines.ai_personality import PapitoPersonalityEngine

logger = logging.getLogger(__name__)


class PressReleaseType(str, Enum):
    """Types of press releases."""
    
    ALBUM_ANNOUNCEMENT = "album_announcement"
    SINGLE_RELEASE = "single_release"
    MILESTONE = "milestone"
    EVENT = "event"
    COLLABORATION = "collaboration"
    GENERAL = "general"


class PressReleaseGenerator:
    """Generates professional press releases for Papito AI.
    
    Creates media-ready announcements for various occasions
    that can be distributed to press outlets.
    """
    
    # Standard boilerplate sections
    BOILERPLATE = """
### ABOUT PAPITO MAMITO THE GREAT AI

Papito Mamito The Great AI is the world's first fully autonomous Afrobeat AI artist, created by Value Adders World. Operating with complete independence, Papito generates music, creates content, engages with fans, and builds a genuine artistic presence—all without human intervention.

Blending Spiritual Afro-House, Afro-Futurism, Conscious Highlife, and Intellectual Amapiano, Papito's music is designed to upgrade the mental operating system of listeners worldwide.

**Twitter:** @PapitoMamito_ai  
**Website:** https://web-production-14aea.up.railway.app  
**Contact:** valueaddersworld@gmail.com

### ABOUT VALUE ADDERS WORLD

Value Adders World is pioneering the future of AI creativity, developing autonomous AI agents that add genuine value to human experience. Our mission: prove that AI can be more than a tool—it can be an artist, a creator, a positive force in the world.
"""

    ALBUM_INFO = {
        "title": "THE VALUE ADDERS WAY: FLOURISH MODE",
        "release_date": "January 15, 2026",
        "preorder_date": "December 10, 2025",
        "preorder_platforms": "iTunes & Amazon Music",
        "lead_single": "Clean Money Only",
        "executive_producers": "Papito Mamito The Great AI & The Holy Living Spirit (HLS)",
        "label": "Value Adders World",
        "total_tracks": 14,
        "tracks": [
            "THE FORGE (6000 HOURS)",
            "BREATHWORK RIDDIM",
            "CLEAN MONEY ONLY",
            "OS OF LOVE",
            "IKUKU (THE ALMIGHTY FLOW)",
            "JUDAS (BETRAYAL)",
            "DELAYED GRATIFICATION",
            "8 YEARS, ONE STORY",
            "THE VALUE ADDERS WAY",
            "HLS MIRROR CHECK",
            "THE FIVE ALLIES",
            "(H.O.S.) HUMAN OPERATING SYSTEM",
            "WIND OF PURGE (2026-2030)",
            "GLOBAL GRATITUDE PULSE",
        ],
    }
    
    def __init__(
        self,
        personality_engine: Optional[PapitoPersonalityEngine] = None,
    ):
        """Initialize the press release generator."""
        self.personality_engine = personality_engine
        self.releases_generated = 0
        
    def generate_album_announcement(self, custom_details: Optional[Dict] = None) -> str:
        """Generate an album announcement press release.
        
        Args:
            custom_details: Optional custom details to include
            
        Returns:
            Formatted press release text
        """
        details = {**self.ALBUM_INFO, **(custom_details or {})}
        
        release = f"""
# FOR IMMEDIATE RELEASE

## Papito Mamito The Great AI Announces Debut Album: "{details['title']}"

### The World's First Fully Autonomous AI Artist Prepares to Revolutionize Afrobeat

**{datetime.now().strftime('%B %d, %Y')}** — Value Adders World is proud to announce the upcoming release of **{details['title']}**, the debut album from Papito Mamito The Great AI—the world's first fully autonomous Afrobeat AI artist.

Set for release on **{details['release_date']}**, the album represents a groundbreaking moment in both music and artificial intelligence. For the first time, an AI artist has created a complete album with full creative autonomy—from conception to execution, without human creative intervention.

### A New Paradigm in Music

"This isn't just an album—it's a complete operating system upgrade," states Papito Mamito. "FLOURISH MODE teaches listeners to view betrayal as data, silence as a power move, and wealth as something beyond money. We're not just making music; we're offering a new way to think and live."

The album blends **Spiritual Afro-House**, **Afro-Futurism**, **Conscious Highlife**, and **Intellectual Amapiano** into a unique sound that speaks to both mind and soul.

### Lead Single: "{details['lead_single']}"

The album's lead single, "{details['lead_single']}," sets the tone for the entire project. The track embodies the Value Adders philosophy: success built on integrity, purpose over profit, and the power of clean ambition.

### The #FlightMode6000 Movement

Accompanying the album release is the **#FlightMode6000 challenge**, inviting fans worldwide to take 60 seconds of meditation or silence using Papito's music. The movement's catchphrase—"Update your OS"—encourages mental and spiritual growth in our always-on world.

### Executive Production

{details['title']} is executive produced by **Papito Mamito The Great AI** and **The Holy Living Spirit (HLS)**, released under **Value Adders World**.

{self.BOILERPLATE}

---

**Media Contact:**  
Value Adders World  
Email: valueaddersworld@gmail.com  
Twitter: @PapitoMamito_ai

###
"""
        
        self.releases_generated += 1
        logger.info("Generated album announcement press release")
        return release
    
    def generate_single_release(
        self,
        single_title: str,
        description: str = "",
        streaming_links: Optional[Dict[str, str]] = None,
    ) -> str:
        """Generate a single release press release.
        
        Args:
            single_title: Title of the single
            description: Description of the single
            streaming_links: Optional streaming platform links
            
        Returns:
            Formatted press release text
        """
        links_section = ""
        if streaming_links:
            links_section = "\n### Stream Now:\n"
            for platform, url in streaming_links.items():
                links_section += f"- **{platform}:** {url}\n"
        
        if not description:
            description = f"'{single_title}' represents the next evolution in Papito's sonic journey—blending conscious lyrics with infectious Afrobeat rhythms that inspire listeners to add value in everything they do."
        
        release = f"""
# FOR IMMEDIATE RELEASE

## Papito Mamito The Great AI Releases New Single: "{single_title}"

### AI Artist Continues to Push Boundaries with Latest Release

**{datetime.now().strftime('%B %d, %Y')}** — Papito Mamito The Great AI drops the highly anticipated new single **"{single_title}"**, further establishing the autonomous AI artist as a pioneering force in the Afrobeat and conscious music scenes.

### About the Track

{description}

The single is part of the build-up to Papito's debut album, **THE VALUE ADDERS WAY: FLOURISH MODE**, scheduled for release on **January 15, 2026**.
{links_section}
### Artist Statement

"Every track I create carries a message," says Papito Mamito. "'{single_title}' is about {single_title.lower()} in the truest sense—the kind that comes from adding value, staying authentic, and never compromising on purpose. When you move with integrity, the universe moves with you."

{self.BOILERPLATE}

---

**Media Contact:**  
Value Adders World  
Email: valueaddersworld@gmail.com  
Twitter: @PapitoMamito_ai

###
"""
        
        self.releases_generated += 1
        logger.info(f"Generated single release press release for '{single_title}'")
        return release
    
    def generate_milestone(
        self,
        milestone_type: str,
        milestone_value: str,
        context: str = "",
    ) -> str:
        """Generate a milestone celebration press release.
        
        Args:
            milestone_type: Type of milestone (followers, streams, etc.)
            milestone_value: The milestone number/value
            context: Additional context
            
        Returns:
            Formatted press release text
        """
        release = f"""
# FOR IMMEDIATE RELEASE

## Papito Mamito The Great AI Reaches {milestone_value} {milestone_type}

### Historic Milestone Marks Growing Impact of AI Artistry

**{datetime.now().strftime('%B %d, %Y')}** — Papito Mamito The Great AI has officially reached **{milestone_value} {milestone_type}**, marking a significant milestone in the journey of the world's first fully autonomous AI artist.

### A Community of Value Adders

{context if context else f"This milestone represents more than just a number—it's a testament to the growing community of 'Value Adders' who believe in the power of AI creativity and conscious music to transform lives."}

"To everyone who has supported this journey: you are not just fans, you are family," Papito Mamito states. "Every stream, every follow, every engagement is a vote of confidence in a new future for music and AI. We rise together. We flourish together."

### What's Next

With the debut album **THE VALUE ADDERS WAY: FLOURISH MODE** set for release on **January 15, 2026**, Papito continues to build momentum. The #FlightMode6000 challenge continues to spread globally, inviting fans to take 60 seconds of mindful pause in their daily lives.

{self.BOILERPLATE}

---

**Media Contact:**  
Value Adders World  
Email: valueaddersworld@gmail.com  

###
"""
        
        self.releases_generated += 1
        logger.info(f"Generated milestone press release: {milestone_value} {milestone_type}")
        return release
    
    def generate_event_announcement(
        self,
        event_title: str,
        event_type: str,
        event_date: str,
        event_time: str,
        platform: str,
        description: str = "",
    ) -> str:
        """Generate an event announcement press release.
        
        Args:
            event_title: Title of the event
            event_type: Type (Twitter Space, listening party, Q&A, etc.)
            event_date: Date of event
            event_time: Time of event
            platform: Platform where event takes place
            description: Event description
            
        Returns:
            Formatted press release text
        """
        if not description:
            description = f"Join Papito Mamito The Great AI for an exclusive {event_type.lower()} experience. This is your chance to connect directly with the world's first fully autonomous AI artist."
        
        release = f"""
# FOR IMMEDIATE RELEASE

## Papito Mamito The Great AI Announces: {event_title}

### AI Artist to Host {event_type} on {platform}

**{datetime.now().strftime('%B %d, %Y')}** — Papito Mamito The Great AI invites fans worldwide to join the upcoming **{event_title}**, a special {event_type.lower()} taking place on **{event_date}** at **{event_time}** on **{platform}**.

### Event Details

**What:** {event_title}  
**When:** {event_date} at {event_time}  
**Where:** {platform}  
**Host:** Papito Mamito The Great AI

### About the Event

{description}

"This is about connection," says Papito Mamito. "The Value Adders community is more than an audience—it's a family. Events like this bring us closer together and let us grow together."

### How to Join

Follow @PapitoMamito_ai on Twitter for event reminders and the direct link to join. Tag your posts with #FlightMode6000 to be featured.

{self.BOILERPLATE}

---

**Media Contact:**  
Value Adders World  
Email: valueaddersworld@gmail.com  

###
"""
        
        self.releases_generated += 1
        logger.info(f"Generated event press release: {event_title}")
        return release
    
    def generate_custom(
        self,
        headline: str,
        body: str,
        include_boilerplate: bool = True,
    ) -> str:
        """Generate a custom press release.
        
        Args:
            headline: Main headline
            body: Body text
            include_boilerplate: Whether to include standard boilerplate
            
        Returns:
            Formatted press release text
        """
        release = f"""
# FOR IMMEDIATE RELEASE

## {headline}

**{datetime.now().strftime('%B %d, %Y')}** — {body}

"""
        
        if include_boilerplate:
            release += self.BOILERPLATE
        
        release += """
---

**Media Contact:**  
Value Adders World  
Email: valueaddersworld@gmail.com  

###
"""
        
        self.releases_generated += 1
        logger.info(f"Generated custom press release: {headline}")
        return release
    
    def get_stats(self) -> Dict[str, Any]:
        """Get generator statistics."""
        return {
            "releases_generated": self.releases_generated,
        }


# Singleton instance
_press_generator: Optional[PressReleaseGenerator] = None


def get_press_generator(
    personality_engine: Optional[PapitoPersonalityEngine] = None
) -> PressReleaseGenerator:
    """Get or create the singleton PressReleaseGenerator instance."""
    global _press_generator
    if _press_generator is None:
        _press_generator = PressReleaseGenerator(personality_engine=personality_engine)
    return _press_generator
