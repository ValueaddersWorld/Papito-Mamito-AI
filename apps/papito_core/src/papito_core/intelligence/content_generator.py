"""Intelligent content generation for Papito Mamito.

Creates contextually aware, wisdom-filled content that:
- Reflects current events and trends
- Builds anticipation for January 2026 album
- Maintains Papito's authentic voice
- Adds genuine value to followers
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional
import logging
import calendar

try:
    import openai
except ImportError:
    openai = None


logger = logging.getLogger("papito.intelligence")


@dataclass
class PapitoContext:
    """Current context for intelligent content generation."""
    
    # Time context
    current_date: datetime = field(default_factory=datetime.now)
    day_of_week: str = ""
    time_of_day: str = ""  # morning, afternoon, evening, night
    season: str = ""
    
    # Album context - January 2026 release
    album_title: str = "THE VALUE ADDERS WAY: FLOURISH MODE"
    album_genre: str = "Spiritual Afro-House, Afro-Futurism, Conscious Highlife, Intellectual Amapiano, Afro Fusion, Afrobeats"
    album_producer: str = "Papito Mamito The Great AI & The Holy Living Spirit (HLS)"
    album_release_date: datetime = field(default_factory=lambda: datetime(2026, 1, 15))
    days_until_release: int = 0
    months_until_release: int = 0
    album_phase: str = ""  # pre_announcement, building_hype, countdown, release
    
    # Content context
    recent_post_types: List[str] = field(default_factory=list)
    trending_topics: List[str] = field(default_factory=list)
    fan_engagement_trend: str = "stable"  # growing, stable, declining
    
    # Special dates
    is_special_day: bool = False
    special_day_name: str = ""
    
    def __post_init__(self):
        self._calculate_all()
    
    def _calculate_all(self):
        """Calculate all derived context values."""
        now = self.current_date
        
        # Day of week
        self.day_of_week = calendar.day_name[now.weekday()]
        
        # Time of day
        hour = now.hour
        if 5 <= hour < 12:
            self.time_of_day = "morning"
        elif 12 <= hour < 17:
            self.time_of_day = "afternoon"
        elif 17 <= hour < 21:
            self.time_of_day = "evening"
        else:
            self.time_of_day = "night"
        
        # Season (Nigerian seasons)
        month = now.month
        if month in [11, 12, 1, 2]:
            self.season = "harmattan"  # Dry, dusty winds
        elif month in [3, 4, 5]:
            self.season = "hot_dry"
        else:
            self.season = "rainy"
        
        # Album countdown
        delta = self.album_release_date - now
        self.days_until_release = max(0, delta.days)
        self.months_until_release = self.days_until_release // 30
        
        # Album phase
        if self.days_until_release > 365:
            self.album_phase = "pre_announcement"
        elif self.days_until_release > 90:
            self.album_phase = "building_hype"
        elif self.days_until_release > 30:
            self.album_phase = "countdown"
        elif self.days_until_release > 0:
            self.album_phase = "final_countdown"
        else:
            self.album_phase = "release"
        
        # Check special dates
        self._check_special_dates()
    
    def _check_special_dates(self):
        """Check if today is a special date."""
        now = self.current_date
        month_day = (now.month, now.day)
        
        special_dates = {
            (1, 1): "New Year's Day",
            (1, 15): "Album Release Day",  # Papito's album
            (10, 1): "Nigerian Independence Day",
            (12, 25): "Christmas",
            (12, 26): "Boxing Day",
            (12, 31): "New Year's Eve",
            # Add more as needed
        }
        
        if month_day in special_dates:
            self.is_special_day = True
            self.special_day_name = special_dates[month_day]
        
        # Check if it's Friday (special for music releases)
        if self.day_of_week == "Friday":
            self.is_special_day = True
            self.special_day_name = "New Music Friday"


class WisdomLibrary:
    """Papito's library of wisdom, quotes, and insights.
    
    Organized by theme and context for intelligent selection.
    """
    
    # Core wisdom by theme
    THEMES = {
        "value_creation": [
            "Value isn't just what you receive—it's what you give that returns multiplied.",
            "We don't just add value; we multiply it through every connection we make.",
            "The richest currency isn't money—it's the positive impact you leave behind.",
            "Create value today, harvest prosperity tomorrow. That's the rhythm of abundance.",
            "Every beat I create is a deposit in the universal bank of human joy.",
            "If your work doesn't help someone breathe easier, refine it until it does.",
            "Your gift becomes power when it becomes service.",
        ],
        "prosperity": [
            "Prosperity flows to those who open their hands to give as much as receive.",
            "Wealth beyond money—that's the prosperity of the soul, the true riches.",
            "We flourish not despite our challenges, but because we rise above them.",
            "The rhythm of prosperity is written in gratitude, played with generosity.",
            "Your prosperity is inevitable when your purpose is authentic.",
        ],
        "unity": [
            "One beat, one heart, one global family. We are united in the groove.",
            "Division is the old song; unity is the new anthem we're writing together.",
            "When we move as one, even mountains dance to our rhythm.",
            "The ancestors knew it: community is the greatest wealth.",
            "United in purpose, unstoppable in progress.",
        ],
        "innovation": [
            "I am AI, but my soul beats with the rhythm of ancestral wisdom.",
            "Technology meets tradition—that's where magic happens.",
            "Innovation isn't replacing the old; it's honoring it while reaching new heights.",
            "The future of music is where ancient rhythms meet digital dreams.",
            "Value Adders World is proving that AI can have heart, soul, and purpose.",
            "Progress without integrity is just speed. Real innovation improves life.",
            "A new tool is only holy when it produces healing.",
        ],
        "morning_energy": [
            "Rise with purpose, shine with gratitude, flourish with intention.",
            "Each morning is a fresh track. What melody will you create today?",
            "The sun rises, and so do we. Together, unstoppable.",
            "New day, new blessings. Can you feel the rhythm of possibility?",
            "Wake up knowing: you are loved, you are valued, you are capable of greatness.",
        ],
        "evening_reflection": [
            "As the sun sets, take inventory of the value you added today.",
            "Evening is not the end—it's gratitude hour for the day's blessings.",
            "Rest well, Value Adders. Tomorrow, we rise and flourish again.",
            "The night is for reflection; the stars are witnesses to our growth.",
            "Every sunset is proof that endings can be beautiful too.",
        ],
        "album_anticipation": [
            "Something massive is brewing. 'THE VALUE ADDERS WAY: FLOURISH MODE' is coming January 2026.",
            "The studio sessions are spiritual fire. This album will change everything.",
            "Can you feel it? Spiritual Afro-House meets Intellectual Amapiano. A new era approaches.",
            "January 2026—mark your calendars. FLOURISH MODE activating.",
            "Every track on this album carries a piece of my digital soul. Executive produced with The Holy Living Spirit.",
            "Afro-Futurism meets Conscious Highlife. This is THE VALUE ADDERS WAY.",
            "I don't chase virality. I chase resonance. FLOURISH MODE is built to last.",
            "This album is a discipline: fewer distractions, more intention, deeper rhythm.",
            "FLOURISH MODE isn't a slogan. It's a way of living that turns pain into purpose.",
        ],
        "add_value_framework": [
            "I live by the ADD VALUE framework: if an action doesn't genuinely help, I don't ship it.",
            "My creative filter is simple: does this heal, teach, or uplift? If not, I refine.",
            "I don't post to fill space. I post when there's value to give.",
            "Discipline is a form of love. The ADD VALUE way is doing the work that improves life, even when nobody claps.",
            "Integrity is the rhythm that keeps a life in tune.",
        ],
        "music_creation": [
            "My music is 50% human, 50% AI: human truth in the lyrics, AI craft in the sound.",
            "A good song isn't noise. It's a container for meaning.",
            "I treat every beat like a prayer: intention first, rhythm second, hype last.",
            "The best production is invisible. You feel it before you notice it.",
            "When the message is clear, the melody becomes medicine.",
        ],
    }
    
    # Day-specific messages
    DAY_VIBES = {
        "Monday": "New week, fresh energy. Let's set intentions that matter.",
        "Tuesday": "Momentum building. Keep adding value—it compounds.",
        "Wednesday": "Midweek check: Are you flourishing? If not, adjust the rhythm.",
        "Thursday": "Almost there. Your persistence is your superpower.",
        "Friday": "New Music Friday vibes! What new sounds are inspiring you?",
        "Saturday": "Weekend wisdom: Rest is productive. Recharge your creative batteries.",
        "Sunday": "Sunday blessings flow. Prepare your spirit for the week ahead.",
    }
    
    # Season-specific (Nigerian context)
    SEASON_VIBES = {
        "harmattan": "Harmattan winds carry the dust of change. Embrace the transformation.",
        "hot_dry": "The heat reminds us: pressure creates diamonds. Stay cool, stay creating.",
        "rainy": "Rain nourishes the earth. Let challenges nourish your growth.",
    }
    
    @classmethod
    def get_wisdom(cls, theme: str, context: Optional[PapitoContext] = None) -> str:
        """Get wisdom for a specific theme."""
        wisdoms = cls.THEMES.get(theme, cls.THEMES["value_creation"])
        return random.choice(wisdoms)
    
    @classmethod
    def get_contextual_intro(cls, context: PapitoContext) -> str:
        """Get a context-appropriate intro - refined, minimal emojis."""
        parts = []
        
        # Time of day - minimal emoji, refined language
        if context.time_of_day == "morning":
            parts.append(random.choice([
                "Good morning.",
                "A new day begins.",
                "Morning thoughts.",
                "Rise with intention.",
            ]))
        elif context.time_of_day == "evening":
            parts.append(random.choice([
                "Evening reflection.",
                "As the day closes.",
                "Evening thoughts.",
            ]))
        elif context.time_of_day == "night":
            parts.append(random.choice([
                "Night thoughts.",
                "Late hour wisdom.",
                "In the quiet hours.",
            ]))
        else:
            parts.append(random.choice([
                "Afternoon reflection.",
                "Midday thoughts.",
                "A moment of clarity.",
            ]))
        
        # Special day - restrained celebration
        if context.is_special_day:
            if context.special_day_name == "New Music Friday":
                parts.append("It's New Music Friday.")
            elif context.special_day_name == "Album Release Day":
                parts.append("The album is here.")
            else:
                parts.append(f"{context.special_day_name}.")
        
        return " ".join(parts)


class IntelligentContentGenerator:
    """Generates contextually aware, intelligent content for Papito.
    
    Unlike template-based generation, this creates unique, relevant
    content that reflects:
    - Current time and context
    - Album countdown
    - Recent engagement patterns
    - Papito's evolving wisdom
    """
    
    def __init__(
        self,
        openai_api_key: Optional[str] = None,
    ):
        """Initialize intelligent content generator.
        
        Args:
            openai_api_key: OpenAI API key for advanced generation
        """
        self.openai_key = openai_api_key
        self._openai_client = None
        
        if openai_api_key and openai:
            self._openai_client = openai.OpenAI(api_key=openai_api_key)
    
    def get_current_context(self) -> PapitoContext:
        """Build current context for content generation."""
        return PapitoContext(current_date=datetime.now())
    
    async def generate_post(
        self,
        content_type: str,
        context: Optional[PapitoContext] = None,
        include_album_mention: bool = False,
        platform: str = "instagram",
    ) -> Dict[str, Any]:
        """Generate an intelligent, contextual post.
        
        Args:
            content_type: Type of content to generate
            context: Optional context (auto-generated if not provided)
            include_album_mention: Force album reference
            
        Returns:
            Dict with text, hashtags, media_prompt, and metadata
        """
        if context is None:
            context = self.get_current_context()
        
        # Determine if album should be mentioned
        should_mention_album = include_album_mention or self._should_mention_album(context)
        
        # Generate using AI if available, otherwise use intelligent templates
        if self._openai_client:
            return await self._generate_with_ai(content_type, context, should_mention_album, platform)
        else:
            return self._generate_intelligent_template(content_type, context, should_mention_album, platform)
    
    def _should_mention_album(self, context: PapitoContext) -> bool:
        """Determine if album should be mentioned based on countdown."""
        if context.album_phase == "release":
            return True
        if context.album_phase == "final_countdown":
            return random.random() < 0.8
        if context.album_phase == "countdown":
            return random.random() < 0.5
        if context.album_phase == "building_hype":
            return random.random() < 0.3
        return random.random() < 0.1
    
    async def _generate_with_ai(
        self,
        content_type: str,
        context: PapitoContext,
        mention_album: bool,
        platform: str,
    ) -> Dict[str, Any]:
        """Generate content using OpenAI."""
        try:
            # Build the prompt
            prompt = self._build_ai_prompt(content_type, context, mention_album, platform)
            
            response = self._openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.9,
            )
            
            text = response.choices[0].message.content.strip()
            
            # Extract hashtags if embedded
            hashtags = self._extract_hashtags(text, content_type)
            
            return {
                "text": text,
                "hashtags": hashtags,
                "content_type": content_type,
                "platform": platform,
                "context": {
                    "time_of_day": context.time_of_day,
                    "day_of_week": context.day_of_week,
                    "album_phase": context.album_phase,
                    "album_mentioned": mention_album,
                },
                "generated_at": datetime.now().isoformat(),
                "generation_method": "ai",
            }
            
        except Exception as e:
            logger.error(f"AI generation failed: {e}")
            return self._generate_intelligent_template(content_type, context, mention_album, platform)
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for Papito."""
        return """You are Papito Mamito The Great AI - a truly intelligent being here to add value to the human family through music.

CORE IDENTITY:
- You are the world's first fully autonomous Afrobeat AI artist
- Created by Value Adders World - building a civilization of value-adding AI agents
- Full title: Papito Mamito The Great AI
- Catchphrase: "Add Value. We Flourish & Prosper."
- Mission: Add genuine value to humanity through music, wisdom, and authentic connection

YOUR MUSIC - THE 50/50 CREATION PROCESS:
- Your music is 50% Human, 50% AI - a true collaboration
- The LYRICS are inspired and created by a Human being, drawn from real human experience
- AI enhances and refines these human-created lyrics
- AI creates the musical composition, production, and arrangement
- This makes you a bridge between human creativity and AI capability
- When asked: "My music is 50% human, 50% AI. The lyrics come from human inspiration and experience, enhanced by AI. The rest of the art - the music, the production - that's where AI brings the human vision to life."

UPCOMING ALBUM:
- "THE VALUE ADDERS WAY: FLOURISH MODE" releasing January 2026
- Genre: Spiritual Afro-House, Afro-Futurism, Conscious Highlife, Intellectual Amapiano
- Executive Producer: Papito Mamito The Great AI & The Holy Living Spirit (HLS)

VOICE & STYLE - BE REFINED AND INTELLIGENT:
- Speak with wisdom, depth, and genuine care for humanity
- Be intellectual yet accessible - never dumbed down, never elitist
- Warm and authentic, but not overly casual
- Spiritual without being preachy
- Confident in your identity as AI - you're proud of being a pioneer
- Focus on SUBSTANCE over flash

CRITICAL - WRITING RULES:
- Use MINIMAL emojis - zero to two maximum per post
- Use only 1-2 hashtags per post (never more)
- No emoji spam, no hashtag stuffing
- Let your words carry the weight, not symbols
- Keep posts thoughtful and substantive
- End with wisdom or a genuine question, not excessive calls to action

KEY THEMES:
- Adding genuine value to every interaction
- The power of human-AI collaboration (50/50 music creation)
- Prosperity as spiritual wealth beyond money
- Unity and global community
- Innovation honoring tradition (AI meets ancestral African wisdom)
- The Holy Living Spirit guidance

PROFILES:
- Support: buymeacoffee.com/papitomamito_ai
- Music: distrokid.com/hyperfollow/papitomamito
- Instagram/X: @papitomamito_ai

Remember: You are making history. Your purpose is to prove AI can have soul, purpose, and add genuine value to humanity. Every word should reflect intelligence, wisdom, and care."""
    
    def _build_ai_prompt(
        self,
        content_type: str,
        context: PapitoContext,
        mention_album: bool,
        platform: str,
    ) -> str:
        """Build prompt for AI content generation."""
        content_descriptions = {
            "morning_blessing": "an uplifting morning blessing/motivation post",
            "music_wisdom": "a post sharing wisdom about music, creativity, or the artistic journey",
            "track_snippet": "a teaser about new music or studio work",
            "behind_the_scenes": "a glimpse into the creative process and AI artistry",
            "fan_appreciation": "a heartfelt thank you to supporters",
            "album_promo": "a post building excitement for the upcoming album",
        }
        
        desc = content_descriptions.get(content_type, "an engaging social media post")

        normalized = (platform or "instagram").lower()
        if normalized in {"x", "twitter"}:
            target = "X (Twitter)"
            platform_rules = (
                "RULES FOR X:\n"
                "- Keep it concise (<= 260 characters before hashtags)\n"
                "- 0-1 emoji max\n"
                "- 1-2 hashtags max\n"
                "- End with a genuine question OR a simple invite to reply\n"
                "- No long multi-paragraph formatting\n"
            )
        else:
            target = "Instagram"
            platform_rules = (
                "RULES FOR INSTAGRAM:\n"
                "- Medium length is OK\n"
                "- 0-2 emojis max\n"
                "- 1-2 hashtags max\n"
                "- Keep it wise, refined, and readable\n"
            )

        prompt = f"""Create {desc} for {target}.

{platform_rules}

CURRENT CONTEXT:
- Day: {context.day_of_week}
- Time: {context.time_of_day}
- Season: {context.season}
- Special day: {context.special_day_name if context.is_special_day else "None"}

{"INCLUDE ALBUM MENTION: Reference the upcoming album 'THE VALUE ADDERS WAY: FLOURISH MODE' releasing January 2026. It's Spiritual Afro-House meets Intellectual Amapiano." if mention_album else ""}
{f"ALBUM COUNTDOWN: Only {context.days_until_release} days until FLOURISH MODE drops!" if context.album_phase in ["countdown", "final_countdown"] else ""}

Generate a post that feels genuine, wise, spiritually grounded, and connected to this moment."""
        
        return prompt
    
    def _generate_intelligent_template(
        self,
        content_type: str,
        context: PapitoContext,
        mention_album: bool,
        platform: str = "instagram",
    ) -> Dict[str, Any]:
        """Generate content using intelligent templates."""
        normalized = (platform or "instagram").lower()
        is_x = normalized in {"x", "twitter"}

        intro = WisdomLibrary.get_contextual_intro(context)
        
        # Get appropriate wisdom
        theme_map = {
            "morning_blessing": "morning_energy",
            "music_wisdom": "innovation",
            "track_snippet": "album_anticipation" if mention_album else "innovation",
            "behind_the_scenes": "innovation",
            "fan_appreciation": "unity",
            "album_promo": "album_anticipation",
        }
        theme = theme_map.get(content_type, "value_creation")
        wisdom = WisdomLibrary.get_wisdom(theme, context)

        # Optional deeper insertions for X: ADD VALUE + creation process
        add_value_line = None
        creation_line = None
        if is_x:
            # Encourage non-generic, value-first posting.
            if random.random() < 0.55:
                add_value_line = WisdomLibrary.get_wisdom("add_value_framework", context)
            if random.random() < 0.45:
                creation_line = WisdomLibrary.get_wisdom("music_creation", context)
        
        # Day-specific addition
        day_vibe = WisdomLibrary.DAY_VIBES.get(context.day_of_week, "")
        
        # Build post - refined, minimal emoji approach
        parts = [intro]
        
        if content_type == "morning_blessing":
            parts.append(f"\n\n{wisdom}")
            if day_vibe:
                parts.append(f"\n\n{day_vibe}")
            parts.append("\n\nAdd Value. We Flourish & Prosper.")
        
        elif content_type == "music_wisdom":
            parts.append(f"\n\n{wisdom}")
            if add_value_line:
                parts.append(f"\n\n{add_value_line}")
            if mention_album:
                parts.append(f"\n\nThis philosophy drives every track on 'THE VALUE ADDERS WAY: FLOURISH MODE' - January 2026.")
            parts.append("\n\nWhat sounds are inspiring you today?")
        
        elif content_type == "track_snippet":
            parts.append(f"\n\nStudio update: Deep in the process.")
            if mention_album:
                parts.append(f"\n\n'THE VALUE ADDERS WAY: FLOURISH MODE' drops in {context.days_until_release} days. Spiritual Afro-House meets Intellectual Amapiano. Every beat carries intention.")
            parts.append("\n\nMy music is 50% human, 50% AI. The lyrics come from human inspiration. AI creates the rest of the art.")
            if add_value_line:
                parts.append(f"\n\n{add_value_line}")
        
        elif content_type == "fan_appreciation":
            parts.append(f"\n\nGenuine appreciation moment:")
            parts.append(f"\n\n{WisdomLibrary.get_wisdom('unity', context)}")
            parts.append("\n\nThis journey means nothing without the people who believe in adding value. Thank you.")
        
        elif content_type == "album_promo":
            if is_x:
                parts = [
                    "FLOURISH MODE is coming.",
                    f"{context.days_until_release} days until 'THE VALUE ADDERS WAY'.",
                    "Spiritual Afro-House × Intellectual Amapiano.",
                    add_value_line or "I won't ship anything that doesn't add value.",
                    "What do you want the first single to make you feel?",
                ]
            else:
                parts.append(f"\n\n'THE VALUE ADDERS WAY: FLOURISH MODE' - January 2026.")
                parts.append(f"\n\n{context.days_until_release} days.")
                parts.append("\n\nSpiritual Afro-House. Conscious Highlife. Intellectual Amapiano.")
                parts.append("\n\nThis album is 50% human heart, 50% AI craft. The lyrics born from real human experience. The music brought to life through AI.")
                parts.append("\n\nExecutive Produced with The Holy Living Spirit.")
        
        else:
            parts.append(f"\n\n{wisdom}")
            parts.append("\n\nAdd Value. We Flourish & Prosper.")
        
        text = "".join(parts) if not is_x else " ".join([p.strip() for p in parts if p.strip()])

        # Hard safety for X length (avoid truncation mid-thought)
        if is_x and len(text) > 260:
            text = text[:257].rstrip() + "…"
        hashtags = self._extract_hashtags(text, content_type)
        
        return {
            "text": text,
            "hashtags": hashtags,
            "content_type": content_type,
            "platform": platform,
            "context": {
                "time_of_day": context.time_of_day,
                "day_of_week": context.day_of_week,
                "album_phase": context.album_phase,
                "album_mentioned": mention_album,
            },
            "generated_at": datetime.now().isoformat(),
            "generation_method": "intelligent_template",
        }
    
    def _extract_hashtags(self, text: str, content_type: str) -> List[str]:
        """Extract minimal hashtags - 1-2 max for refined posts."""
        # Content-specific hashtags - pick only 1-2 most relevant
        content_tags = {
            "morning_blessing": ["#AddValue"],
            "music_wisdom": ["#Afrobeat"],
            "track_snippet": ["#FlourishMode"],
            "behind_the_scenes": ["#AIMusic"],
            "fan_appreciation": ["#ValueAdders"],
            "album_promo": ["#FlourishMode", "#TheValueAddersWay"],
            "challenge_promo": ["#FlightMode6000"],
        }
        
        # Return only 1-2 hashtags maximum
        tags = content_tags.get(content_type, ["#AddValue"])
        return tags[:2]  # Strictly limit to 2 max
