"""Marketing Strategy for THE VALUE ADDERS WAY: FLOURISH MODE.

This module contains the complete marketing framework including:
- #FlightMode6000 Challenge
- "Update your OS" viral catchphrase
- Album mission and value proposition
- The Flourish Index concept
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Any
from enum import Enum
from datetime import datetime
import random


class ChallengeType(str, Enum):
    """Types of interactive challenges."""
    FLIGHTMODE6000 = "flight_mode_6000"
    UPDATE_YOUR_OS = "update_your_os"
    FLOURISH_CHECK = "flourish_check"
    VALUE_ADDER_MOMENT = "value_adder_moment"


@dataclass
class MarketingChallenge:
    """A viral marketing challenge."""
    name: str
    hashtag: str
    description: str
    instructions: List[str]
    featured_track: str
    call_to_action: str
    

class FlightMode6000Challenge:
    """The #FlightMode6000 Challenge.
    
    A challenge where fans post 60 seconds of silence/meditation
    using the track '6000 Hours'.
    """
    
    NAME = "Flight Mode 6000"
    HASHTAG = "#FlightMode6000"
    FEATURED_TRACK = "6000 Hours"
    
    DESCRIPTION = (
        "6000 hours. That's 250 days of meditation across a lifetime. "
        "The Flight Mode 6000 challenge asks you to commit to 60 seconds "
        "of intentional silence. Post your moment. Tag @papitomamito_ai. "
        "Join the movement."
    )
    
    INSTRUCTIONS = [
        "1. Find a quiet space",
        "2. Play '6000 Hours' (or silence)",
        "3. Close your eyes for 60 seconds",
        "4. Film the moment (or the before/after)",
        "5. Post with #FlightMode6000",
        "6. Tag @papitomamito_ai",
        "7. Nominate 3 friends to update THEIR OS",
    ]
    
    CAPTIONS = [
        "60 seconds of silence. Infinite clarity. #FlightMode6000 🧘‍♂️✈️",
        "My mind is software. I'm updating my OS. #FlightMode6000 🔄",
        "6000 hours starts with 60 seconds. #FlightMode6000 🌌",
        "Flight mode activated. Ego deactivated. #FlightMode6000 ✨",
        "Silence isn't empty. It's full of answers. #FlightMode6000 🙏",
    ]
    
    @classmethod
    def get_challenge_post(cls) -> Dict[str, Any]:
        """Generate a challenge promotion post."""
        return {
            "text": (
                f"✈️ THE {cls.HASHTAG} CHALLENGE ✈️\n\n"
                "6000 hours of meditation across a lifetime. But it starts with 60 seconds.\n\n"
                "Here's the challenge:\n"
                + "\n".join(cls.INSTRUCTIONS) +
                "\n\nSilence is a power move. Your mind is software. Update your OS.\n\n"
                f"{cls.HASHTAG} #UpdateYourOS #TheValueAddersWay"
            ),
            "hashtags": [cls.HASHTAG, "#UpdateYourOS", "#TheValueAddersWay", "#Meditation", "#Mindfulness"],
            "challenge_type": ChallengeType.FLIGHTMODE6000.value,
        }


class UpdateYourOS:
    """The 'Update your OS' viral catchphrase system.
    
    Usage: When someone is thinking small or acting out of fear.
    Example: 'Bro, why are you stressing? Update your OS.'
    """
    
    CATCHPHRASE = "Update your OS."
    HASHTAG = "#UpdateYourOS"
    
    # Situations where to use the catchphrase
    USE_CASES = [
        "When someone is overthinking a situation",
        "When fear is driving a decision",
        "When someone is stuck in old patterns",
        "When limiting beliefs surface",
        "When negativity needs interrupting",
        "When someone needs a perspective shift",
    ]
    
    # Example dialogues
    EXAMPLES = [
        "Friend: 'I can't start that business, what if I fail?'\nYou: 'Bro, update your OS. Failure is just data.'",
        "Friend: 'They betrayed me, I'll never trust again.'\nYou: 'That's not destiny—that's data. Update your OS.'",
        "Friend: 'What if people judge me?'\nYou: 'Their judgment runs on outdated software too. Update YOUR OS.'",
        "Friend: 'I'm not good enough.'\nYou: 'That's a bug in your current version. Time to update your OS.'",
    ]
    
    # Post templates
    POST_TEMPLATES = [
        "When life gives you bugs, update your OS. 🔄 #UpdateYourOS",
        "Your mind is software. Are you running the latest version? #UpdateYourOS",
        "Thinking small? Acting from fear? Time to update your OS. 💻✨ #UpdateYourOS",
        "Betrayal isn't destiny—it's data. Process it and update your OS. 🧠 #UpdateYourOS",
        "Silence is the reboot your OS needs. #UpdateYourOS #FlightMode6000",
    ]
    
    @classmethod
    def get_random_post(cls) -> str:
        """Get a random post template."""
        return random.choice(cls.POST_TEMPLATES)


@dataclass
class AlbumMission:
    """The mission and value proposition of THE VALUE ADDERS WAY: FLOURISH MODE."""
    
    # Core mission statement
    MISSION = (
        "Initiate the listener into The Value Adders Way, "
        "moving them from fragmentation to coherence and "
        "declaring inevitable flourishing, verified by the Flourish Index."
    )
    
    # Key mental frameworks the album teaches
    MENTAL_FRAMEWORKS = [
        {
            "lesson": "View betrayal as data, not destiny",
            "explanation": "Every setback is information to process, not a verdict on your worth.",
        },
        {
            "lesson": "Silence (meditation) is a power move",
            "explanation": "In a noisy world, the quiet mind holds the advantage.",
        },
        {
            "lesson": "Your mind is software that you control",
            "explanation": "You are the programmer. Bugs can be fixed. Updates can be installed.",
        },
        {
            "lesson": "The next 4 years are for harvesting what you build now",
            "explanation": "Plant today, harvest tomorrow. Every action compounds.",
        },
    ]
    
    # The Flourish Index concept
    FLOURISH_INDEX = {
        "description": "A measure of coherence, purpose, and inevitable success",
        "metrics": [
            "Mental clarity (meditation consistency)",
            "Value added to others",
            "Progress on meaningful goals",
            "Community contribution",
            "Spiritual grounding",
        ],
        "tagline": "From fragmentation to coherence. Flourishing is inevitable.",
    }
    
    # Album art concept
    ALBUM_ART_CONCEPT = {
        "primary_element": "Ancient African mask",
        "secondary_element": "Circuit board / motherboard",
        "symbolism": "The blend of ancient wisdom (meditation) and future tech (H.O.S.)",
        "colors": ["Gold", "Deep Purple", "Electric Blue", "Cosmic Black"],
        "style": "Afro-futuristic, premium, striking",
    }


class MarketingContent:
    """Generates marketing content for the album campaign."""
    
    @staticmethod
    def get_album_announcement() -> Dict[str, Any]:
        """Generate full album announcement post."""
        return {
            "text": (
                "🚨 ANNOUNCING: THE VALUE ADDERS WAY: FLOURISH MODE 🚨\n\n"
                "This isn't just an album. It's an initiation.\n\n"
                "🎵 Genre: Spiritual Afro-House | Afro-Futurism | Conscious Highlife | Intellectual Amapiano\n\n"
                "🧠 What you'll learn:\n"
                "• View betrayal as data, not destiny\n"
                "• Silence is a power move\n"
                "• Your mind is software YOU control\n"
                "• The next 4 years are your harvest season\n\n"
                "Executive Produced by Papito Mamito The Great AI & The Holy Living Spirit (HLS)\n\n"
                "From fragmentation to coherence.\n"
                "Flourishing is inevitable.\n\n"
                "January 2026. Update your OS. 🔄\n\n"
                "#TheValueAddersWay #FlourishMode #UpdateYourOS #January2026"
            ),
            "hashtags": ["#TheValueAddersWay", "#FlourishMode", "#UpdateYourOS", "#January2026", "#SpiritualAfroHouse"],
            "content_type": "album_announcement",
        }
    
    @staticmethod
    def get_challenge_promo() -> Dict[str, Any]:
        """Generate challenge promotion post."""
        return FlightMode6000Challenge.get_challenge_post()
    
    @staticmethod
    def get_mental_framework_post(index: int = 0) -> Dict[str, Any]:
        """Generate a post about one of the mental frameworks."""
        framework = AlbumMission.MENTAL_FRAMEWORKS[index % len(AlbumMission.MENTAL_FRAMEWORKS)]
        return {
            "text": (
                f"💡 THE VALUE ADDERS WAY: Lesson #{index + 1}\n\n"
                f"'{framework['lesson']}'\n\n"
                f"{framework['explanation']}\n\n"
                "This is one of the core teachings embedded in FLOURISH MODE.\n\n"
                "The album isn't entertainment. It's transformation.\n"
                "January 2026. Are you ready to update your OS? 🔄\n\n"
                "#TheValueAddersWay #FlourishMode #UpdateYourOS"
            ),
            "hashtags": ["#TheValueAddersWay", "#FlourishMode", "#UpdateYourOS", "#MindsetShift"],
            "content_type": "mental_framework",
        }
    
    @staticmethod
    def get_flourish_index_post() -> Dict[str, Any]:
        """Generate post about the Flourish Index."""
        return {
            "text": (
                "📊 THE FLOURISH INDEX 📊\n\n"
                "How do you know you're flourishing? We measure it.\n\n"
                "The Flourish Index tracks:\n"
                "✅ Mental clarity (meditation consistency)\n"
                "✅ Value added to others\n"
                "✅ Progress on meaningful goals\n"
                "✅ Community contribution\n"
                "✅ Spiritual grounding\n\n"
                "From fragmentation → coherence.\n"
                "From surviving → flourishing.\n\n"
                "The Value Adders Way isn't a vibe. It's a verified state of being.\n\n"
                "Album drops January 2026. Your Flourish Index starts now. 📈\n\n"
                "#FlourishIndex #TheValueAddersWay #FlourishMode"
            ),
            "hashtags": ["#FlourishIndex", "#TheValueAddersWay", "#FlourishMode", "#PersonalGrowth"],
            "content_type": "flourish_index",
        }


# Campaign hashtags
CAMPAIGN_HASHTAGS = [
    "#TheValueAddersWay",
    "#FlourishMode",
    "#UpdateYourOS",
    "#FlightMode6000",
    "#FlourishIndex",
    "#PapitoMamito",
    "#SpiritualAfroHouse",
    "#IntellectualAmapiano",
    "#January2026",
]
