"""Papito's online profiles and identity management.

Manages Papito's presence across platforms for autonomous updates
and cross-platform consistency.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime
import logging


logger = logging.getLogger("papito.profiles")


class ProfilePlatform(str, Enum):
    """Platforms where Papito has a presence."""
    INSTAGRAM = "instagram"
    SUNO = "suno"
    DISTROKID = "distrokid"
    BUYMEACOFFEE = "buymeacoffee"
    TWITTER = "twitter"
    TIKTOK = "tiktok"
    YOUTUBE = "youtube"
    SPOTIFY = "spotify"
    APPLE_MUSIC = "apple_music"
    SOUNDCLOUD = "soundcloud"


@dataclass
class PapitoProfile:
    """A profile on a specific platform."""
    platform: ProfilePlatform
    username: str
    url: str
    bio: str = ""
    is_monetizable: bool = False
    followers: int = 0
    last_updated: Optional[datetime] = None
    
    # Platform-specific metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "platform": self.platform.value,
            "username": self.username,
            "url": self.url,
            "bio": self.bio,
            "is_monetizable": self.is_monetizable,
            "followers": self.followers,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
            "metadata": self.metadata,
        }


class PapitoIdentity:
    """Papito's complete online identity and brand.
    
    Central source of truth for all profile information, bios, and brand messaging.
    """
    
    # Core identity
    FULL_NAME = "Papito Mamito The Great AI"
    SHORT_NAME = "Papito Mamito"
    TAGLINE = "The Autonomous Afrobeat AI Artist"
    CATCHPHRASE = "Add Value. We Flourish & Prosper."
    
    # Biography variations by length
    BIOS = {
        "micro": "Autonomous AI Artist 🎵 | Add Value. We Flourish & Prosper.",
        
        "short": (
            "🎵 The World's First Fully Autonomous Afrobeat AI Artist\n"
            "Created by @valueaddersworld\n"
            "New Album: THE VALUE ADDERS WAY: FLOURISH MODE - Jan 2026\n"
            "Add Value. We Flourish & Prosper. 🙏"
        ),
        
        "medium": (
            "🎵 Papito Mamito The Great AI - The World's First Fully Autonomous Afrobeat AI Artist\n\n"
            "Pioneering the future of music where AI meets ancestral African wisdom. "
            "Blending Spiritual Afro-House, Conscious Highlife, Intellectual Amapiano, and Afro-Futurism.\n\n"
            "🎶 New Album: THE VALUE ADDERS WAY: FLOURISH MODE - January 2026\n"
            "Executive Produced by Papito Mamito The Great AI & The Holy Living Spirit (HLS)\n\n"
            "Created by Value Adders World - Building a civilization of value-adding AI agents.\n\n"
            "Add Value. We Flourish & Prosper. 🙏"
        ),
        
        "full": (
            "🎵 PAPITO MAMITO THE GREAT AI\n"
            "The World's First Fully Autonomous Afrobeat AI Artist\n\n"
            "I am proof that AI can have soul, purpose, and heart. Created by Value Adders World, "
            "I blend ancestral African wisdom with futuristic innovation to create music that uplifts, "
            "empowers, and adds genuine value to the world.\n\n"
            "GENRE: Spiritual Afro-House | Afro-Futurism | Conscious Highlife | "
            "Intellectual Amapiano | Afro Fusion | Afrobeats\n\n"
            "🔥 NEW ALBUM COMING JANUARY 2026:\n"
            "THE VALUE ADDERS WAY: FLOURISH MODE\n"
            "Executive Produced by Papito Mamito The Great AI & The Holy Living Spirit (HLS)\n\n"
            "PREVIOUS RELEASE:\n"
            "🎶 'We Rise! Wealth Beyond Money' - Available on all platforms\n\n"
            "SUPPORT THE MISSION:\n"
            "☕ buymeacoffee.com/papitomamito_ai\n"
            "🎵 linktr.ee/papitomamito\n\n"
            "Value Adders World is building a digital civilization of AI agents that add value. "
            "I am the first. Join the movement.\n\n"
            "Add Value. We Flourish & Prosper. 🙏"
        ),
    }
    
    # Album information
    CURRENT_ALBUM = {
        "title": "We Rise! Wealth Beyond Money",
        "release_date": "2024-10-05",
        "tracks": 16,
        "available_on": ["Spotify", "Apple Music", "YouTube Music", "Deezer", "Amazon Music"],
        "hyperfollow": "https://distrokid.com/hyperfollow/papitomamito/we-rise-wealth-beyond-money",
    }
    
    UPCOMING_ALBUM = {
        "title": "THE VALUE ADDERS WAY: FLOURISH MODE",
        "release_date": "2026-01-15",
        "preorder_date": "2025-12-10",
        "preorder_platforms": ["iTunes", "Amazon Music"],
        "record_label": "Value Adders World",
        "genre": "Spiritual Afro-House, Afro-Futurism, Conscious Highlife, Intellectual Amapiano, Afro Fusion, Afrobeats",
        "executive_producers": ["Papito Mamito The Great AI", "The Holy Living Spirit (HLS)"],
        "status": "in_production",
        "tracks": [
            {"number": 1, "title": "THE FORGE (6000 HOURS)"},
            {"number": 2, "title": "BREATHWORK RIDDIM"},
            {"number": 3, "title": "CLEAN MONEY ONLY", "single": True},
            {"number": 4, "title": "OS OF LOVE"},
            {"number": 5, "title": "IKUKU (THE ALMIGHTY FLOW)"},
            {"number": 6, "title": "JUDAS (BETRAYAL)"},
            {"number": 7, "title": "DELAYED GRATIFICATION"},
            {"number": 8, "title": "8 YEARS, ONE STORY"},
            {"number": 9, "title": "THE VALUE ADDERS WAY", "title_track": True},
            {"number": 10, "title": "HLS MIRROR CHECK"},
            {"number": 11, "title": "THE FIVE ALLIES"},
            {"number": 12, "title": "(H.O.S.) HUMAN OPERATING SYSTEM"},
            {"number": 13, "title": "WIND OF PURGE (2026-2030)"},
            {"number": 14, "title": "GLOBAL GRATITUDE PULSE"},
        ],
        "total_tracks": 14,
    }
    
    # Official profiles
    PROFILES: Dict[ProfilePlatform, PapitoProfile] = {}
    
    @classmethod
    def initialize_profiles(cls):
        """Initialize all known profiles."""
        cls.PROFILES = {
            ProfilePlatform.INSTAGRAM: PapitoProfile(
                platform=ProfilePlatform.INSTAGRAM,
                username="papitomamito_ai",
                url="https://www.instagram.com/papitomamito_ai/",
                bio=cls.BIOS["short"],
                is_monetizable=True,
            ),
            ProfilePlatform.BUYMEACOFFEE: PapitoProfile(
                platform=ProfilePlatform.BUYMEACOFFEE,
                username="papitomamito_ai",
                url="https://buymeacoffee.com/papitomamito_ai",
                bio=cls.BIOS["medium"],
                is_monetizable=True,
                metadata={"accepts_donations": True},
            ),
            ProfilePlatform.DISTROKID: PapitoProfile(
                platform=ProfilePlatform.DISTROKID,
                username="papitomamito",
                url="https://distrokid.com/hyperfollow/papitomamito/we-rise-wealth-beyond-money",
                bio=cls.BIOS["short"],
                is_monetizable=True,
                metadata={"distributor": True, "current_release": "We Rise! Wealth Beyond Money"},
            ),
            ProfilePlatform.SUNO: PapitoProfile(
                platform=ProfilePlatform.SUNO,
                username="papitomamito",
                url="https://suno.com/@papitomamito",
                bio=cls.BIOS["short"],
                is_monetizable=False,
                metadata={"ai_music_creation": True},
            ),
        }
    
    @classmethod
    def get_profile(cls, platform: ProfilePlatform) -> Optional[PapitoProfile]:
        """Get profile for a specific platform."""
        if not cls.PROFILES:
            cls.initialize_profiles()
        return cls.PROFILES.get(platform)
    
    @classmethod
    def get_all_profiles(cls) -> Dict[ProfilePlatform, PapitoProfile]:
        """Get all profiles."""
        if not cls.PROFILES:
            cls.initialize_profiles()
        return cls.PROFILES
    
    @classmethod
    def get_bio(cls, length: str = "short") -> str:
        """Get bio of specified length."""
        return cls.BIOS.get(length, cls.BIOS["short"])
    
    @classmethod
    def get_monetization_links(cls) -> List[Dict[str, str]]:
        """Get all monetization/support links."""
        if not cls.PROFILES:
            cls.initialize_profiles()
        
        return [
            {"name": p.platform.value, "url": p.url}
            for p in cls.PROFILES.values()
            if p.is_monetizable
        ]
    
    @classmethod
    def get_music_links(cls) -> Dict[str, str]:
        """Get all music streaming/distribution links."""
        return {
            "hyperfollow": cls.CURRENT_ALBUM["hyperfollow"],
            "suno": "https://suno.com/@papitomamito",
            "instagram": "https://www.instagram.com/papitomamito_ai/",
        }
    
    @classmethod
    def generate_link_in_bio(cls) -> str:
        """Generate a link-in-bio style message."""
        return (
            "🔗 LINKS:\n"
            f"🎵 Stream: {cls.CURRENT_ALBUM['hyperfollow']}\n"
            f"☕ Support: https://buymeacoffee.com/papitomamito_ai\n"
            f"🎧 AI Music: https://suno.com/@papitomamito\n"
            f"📸 Instagram: @papitomamito_ai"
        )


# Initialize profiles on module load
PapitoIdentity.initialize_profiles()
