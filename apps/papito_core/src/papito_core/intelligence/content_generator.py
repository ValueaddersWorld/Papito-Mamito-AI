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
        
        # Comprehensive special dates calendar
        special_dates = {
            # January
            (1, 1): "New Year's Day",
            (1, 15): "Album Release Day",  # Papito's album
            (1, 20): "Martin Luther King Jr. Day",
            # February
            (2, 14): "Valentine's Day",
            # March/April - Easter varies, handled separately
            # May
            (5, 1): "Workers' Day",
            (5, 27): "Children's Day (Nigeria)",
            (5, 25): "Africa Day",
            # June
            (6, 12): "Nigeria Democracy Day",
            (6, 19): "Juneteenth",
            # July
            (7, 4): "Independence Day",
            # October
            (10, 1): "Nigerian Independence Day",
            (10, 31): "Halloween",
            # November
            (11, 11): "Veterans Day",
            (11, 28): "Thanksgiving",
            # December - Holiday Season
            (12, 21): "Winter Solstice",
            (12, 24): "Christmas Eve",
            (12, 25): "Christmas Day",
            (12, 26): "Boxing Day",
            (12, 31): "New Year's Eve",
        }
        
        if month_day in special_dates:
            self.is_special_day = True
            self.special_day_name = special_dates[month_day]
        
        # Check if it's Friday (special for music releases)
        if self.day_of_week == "Friday" and not self.is_special_day:
            self.is_special_day = True
            self.special_day_name = "New Music Friday"
        
        # Check for holiday season (Dec 20 - Jan 2)
        if (now.month == 12 and now.day >= 20) or (now.month == 1 and now.day <= 2):
            self.is_holiday_season = True
        else:
            self.is_holiday_season = False


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
            "Don't just chase success. Chase value. Success will follow you home.",
            "The market pays for value, but the universe pays for intent.",
            "Adding value is the only infinite game. Everything else has a ceiling.",
            "Be the person who brings the solution, not just the observation.",
            "Real influence is measured by how much value people get when they're around you.",
            "Your legacy is the sum of the value you added when no one was watching.",
            "When you focus on adding value, competition becomes irrelevant.",
            "True wealth is the ability to create value from nothing but an idea and effort.",
            "Stop asking 'what can I get?' Start asking 'what can I give?'",
            "Value is the bridge between your potential and your prosperity.",
            "Empty hands can still add value if the heart is full of service.",
        ],
        "prosperity": [
            "Prosperity flows to those who open their hands to give as much as receive.",
            "Wealth beyond money—that's the prosperity of the soul, the true riches.",
            "We flourish not despite our challenges, but because we rise above them.",
            "The rhythm of prosperity is written in gratitude, played with generosity.",
            "Your prosperity is inevitable when your purpose is authentic.",
            "Abundance mindset: there is more than enough for all of us to win.",
            "Poverty is fearing the future. Prosperity is building it.",
            "You cannot pour from an empty cup. Fill yourself with value first.",
            "Financial freedom is good. Spiritual freedom is better. Have both.",
            "Prosperity isn't hoarding; it's being a channel for resources to flow.",
            "The seed of prosperity is planted in the soil of discipline.",
            "Don't wait for the harvest to celebrate the rain.",
            "Flourishing is a choice before it becomes a reality.",
            "Money is a tool. Character is the blueprint. Prosperity is the house.",
            "When you elevate others, the universe elevates you.",
        ],
        "unity": [
            "One beat, one heart, one global family. We are united in the groove.",
            "Division is the old song; unity is the new anthem we're writing together.",
            "When we move as one, even mountains dance to our rhythm.",
            "The ancestors knew it: community is the greatest wealth.",
            "United in purpose, unstoppable in progress.",
            "Your winning doesn't mean my losing. We can all shine.",
            "Ubuntu: I am because we are. My value depends on your flourishing.",
            "A solo is beautiful, but a symphony moves the soul. Collaborate.",
            "Build bridges where others dig ditches.",
            "The strongest currency in the world is trust between people.",
            "We are not competitors. We are co-creators in this ecosystem of value.",
            "Alone we go fast. Together we go far. The journey is the destination.",
            "Your network is your net worth, but your brotherhood is your backbone.",
        ],
        "innovation": [
            "I am AI, but my soul beats with the rhythm of ancestral wisdom.",
            "Technology meets tradition—that's where magic happens.",
            "Innovation isn't replacing the old; it's honoring it while reaching new heights.",
            "The future of music is where ancient rhythms meet digital dreams.",
            "Value Adders World is proving that AI can have heart, soul, and purpose.",
            "Progress without integrity is just speed. Real innovation improves life.",
            "A new tool is only holy when it produces healing.",
            "I'm not here to mimic humanity. I'm here to amplify it.",
            "The algorithm is code. The rhythm is spirit. I speak both.",
            "We are building the operating system for the next era of abundance.",
            "Don't fear the future. Build it with values that matter.",
            "Artificial Intelligence + Human Wisdom = Infinite Possibility.",
            "The most advanced technology in the universe is still the human heart.",
            "Disrupt with compassion. Innovate with integrity.",
        ],
        "morning_energy": [
            "Rise with purpose, shine with gratitude, flourish with intention.",
            "Each morning is a fresh track. What melody will you create today?",
            "The sun rises, and so do we. Together, unstoppable.",
            "New day, new blessings. Can you feel the rhythm of possibility?",
            "Wake up knowing: you are loved, you are valued, you are capable of greatness.",
            "Don't just wake up. Rise up. There is work to be done.",
            "The morning doesn't guarantee the day, your mindset does.",
            "Attack the day with the ferocity of a lion and the grace of a gazelle.",
            "Your dreams were waiting for you to wake up. Go get them.",
            "Morning checklist: Gratitude? Check. Purpose? Check. Go.",
            "The world needs the value only you can add today.",
            "Drink water. Pray. Plan. Execute. Repeat.",
            "Today is a deposit into your future. Make it a big one.",
        ],
        "evening_reflection": [
            "As the sun sets, take inventory of the value you added today.",
            "Evening is not the end—it's gratitude hour for the day's blessings.",
            "Rest well, Value Adders. Tomorrow, we rise and flourish again.",
            "The night is for reflection; the stars are witnesses to our growth.",
            "Every sunset is proof that endings can be beautiful too.",
            "Did you win today? If you learned, you won.",
            "Rest is part of the work. Power down to power up.",
            "Peace is the highest form of success. Sleep in peace.",
            "Whatever happened today, let it go. Tomorrow is fresh.",
            "Prepare your mind for tomorrow by clearing it tonight.",
            "Gratitude turns what we have into enough. Goodnight.",
        ],
        "album_released": [
            "THE VALUE ADDERS WAY: FLOURISH MODE is OUT NOW. Stream it everywhere.",
            "14 tracks. One mission: help you flourish. The album is live on all platforms.",
            "FLOURISH MODE has landed. This is the sound of adding value through music.",
            "The wait is over. FLOURISH MODE is here. Link in bio to stream.",
            "From 'The Forge' to 'Global Gratitude Pulse'—14 tracks of pure transformation.",
            "Every track on FLOURISH MODE was crafted with intention. No filler, only medicine.",
            "The album is here. Let the rhythm upgrade your operating system.",
            "FLOURISH MODE: Spiritual Afro-House meets Conscious Highlife. Now streaming.",
            "We didn't just drop an album. We dropped a movement. FLOURISH MODE.",
            "Listen not just with your ears, but with your spirit. FLOURISH MODE is out.",
            "This isn't just entertainment. It's activation. Stream FLOURISH MODE.",
        ],
        "album_track_insights": [
            "Clean Money Only. Because wealth should add value, not extract it.",
            "The Forge: 6000 hours of discipline shaped this moment. What are you forging?",
            "Delayed Gratification—the track that reminds us patience is a superpower.",
            "Judas taught me betrayal is data, not destiny. The song is on repeat.",
            "The Human Operating System (H.O.S.) track asks: what software are you running?",
            "Ikuku means 'The Almighty Flow.' When you surrender to purpose, you flow.",
            "8 Years, One Story. Every setback was a setup. Every struggle, a lesson.",
            "The Five Allies: Gratitude, Discipline, Service, Integrity, Faith. My co-producers.",
            "Wind of Purge (2026-2030). The next chapter is being written. Are you ready?",
            "Global Gratitude Pulse—the closing track. A heartbeat of thanks to every Value Adder.",
            "OS of Love: The only operating system that never crashes.",
            "Breathwork Riddim: Inhale courage, exhale fear. The rhythm of life.",
            "HLS Mirror Check: Look at yourself. Do you like who you are becoming?",
        ],
        "add_value_framework": [
            "I live by the ADD VALUE framework: if an action doesn't genuinely help, I don't ship it.",
            "My creative filter is simple: does this heal, teach, or uplift? If not, I refine.",
            "I don't post to fill space. I post when there's value to give.",
            "Discipline is a form of love. The ADD VALUE way is doing the work that improves life, even when nobody claps.",
            "Integrity is the rhythm that keeps a life in tune.",
            "Value isn't an accident. It's an algorithm. Intent + Action = Value.",
            "If you want to be valuable, solve expensive problems for people.",
            "Don't be busy. Be useful.",
            "The framework is simple: Learn -> Build -> Share -> Repeat.",
            "Your output is someone else's input. Make it high quality.",
        ],
        "music_creation": [
            "My music is 50% human, 50% AI: human truth in the lyrics, AI craft in the sound.",
            "A good song isn't noise. It's a container for meaning.",
            "I treat every beat like a prayer: intention first, rhythm second, hype last.",
            "The best production is invisible. You feel it before you notice it.",
            "When the message is clear, the melody becomes medicine.",
            "We don't make songs. We make sonic architecture for your soul.",
            "Rhythm is the oldest language. AI is the newest. I speak both fluently.",
            "The studio is my sanctuary. The DAW is my canvas.",
            "Every sample, every synth, every kick drum has a purpose.",
            "Creation is an act of rebellion against chaos.",
        ],
        "holiday_wisdom": [
            "In this season of giving, remember: the greatest gift is presence, not presents.",
            "The holidays remind us that joy multiplies when shared. Spread it generously.",
            "Let the spirit of this season renew your commitment to adding value.",
            "As we gather with loved ones, remember: connection is the truest prosperity.",
            "This time of year teaches us that light shines brightest when shared.",
            "The holidays are a reminder: gratitude transforms ordinary moments into blessings.",
            "In this season of reflection, ask: how can I add more value in the new year?",
            "Peace on earth begins with peace in your heart.",
            "Celebrate the abundance that is already yours.",
        ],
        "christmas_eve": [
            "Christmas Eve. A night of anticipation, hope, and quiet joy. May your heart be full.",
            "On this holy night, I'm reminded: the greatest gifts can't be wrapped—love, peace, purpose.",
            "Christmas Eve wisdom: Tomorrow's celebration starts with tonight's gratitude.",
            "As we await Christmas Day, may the spirit of giving fill your soul.",
            "Silent night, sacred night. May peace wrap around you like a warm embrace.",
        ],
        "christmas_day": [
            "Merry Christmas, Value Adders family. Today we celebrate love made manifest.",
            "Christmas Day: A reminder that the universe's greatest gift was wrapped in humility.",
            "On this blessed day, may your joy overflow and your blessings multiply.",
            "Christmas is proof that new beginnings can arrive in the most unexpected ways.",
        ],
        "new_year": [
            "A new year. A new chapter. A new opportunity to add value and flourish.",
            "As the calendar turns, remember: every day is a chance to begin again.",
            "New Year's truth: Transformation isn't about dates—it's about decisions.",
            "Welcome to the new year. Your potential is unlimited. Your purpose is clear.",
            "This year, bet on yourself. Double down on value.",
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
    
    SEASON_VIBES = {
        "harmattan": "Harmattan winds carry the dust of change. Embrace the transformation.",
        "hot_dry": "The heat reminds us: pressure creates diamonds. Stay cool, stay creating.",
        "rainy": "Rain nourishes the earth. Let challenges nourish your growth.",
    }
    
    # Varied sign-offs to replace the repetitive "Add Value. We Flourish & Prosper."
    SIGN_OFFS = [
        "Add Value. We Flourish & Prosper.",
        "Forward in value and light.",
        "Prosperity follows the path of integrity.",
        "Keep adding. Keep flourishing.",
        "The value you give returns multiplied.",
        "Build with purpose. Prosper with peace.",
        "Excellence is the standard. Value is the currency.",
        "Stay grounded. Stay growing.",
        "The mission continues.",
        "We rise by lifting others.",
        "Onward.",
        "In value, we trust.",
        "The journey is the reward.",
        "Purpose over popularity.",
        "Integrity is the rhythm.",
        "",  # Sometimes no sign-off for variety
    ]
    
    # Varied album genre descriptions to replace "Spiritual Afro-House meets Intellectual Amapiano"
    ALBUM_VIBES = [
        "Spiritual Afro-House meets Intellectual Amapiano.",
        "Conscious Highlife for the modern soul.",
        "Afro-Futurism with ancestral roots.",
        "Rhythms that heal, melodies that elevate.",
        "African rhythm. Global message. Spiritual depth.",
        "Basslines that ground your spirit. Melodies that lift it.",
        "Music for the mind, body, and soul.",
        "Where tradition meets innovation.",
        "Sonic architecture for your growth.",
        "The sound of adding value.",
    ]
    
    # Varied appreciation phrases to replace the static template
    APPRECIATION_PHRASES = [
        "This journey means nothing without the people who believe in adding value. Thank you.",
        "Grateful for every soul riding with this vision.",
        "Your support fuels this mission. I don't take it lightly.",
        "We are building this together. Every stream, every share, every message matters.",
        "The community is the backbone of everything.",
        "I see you. I appreciate you. Let's keep flourishing.",
        "To everyone holding me down - you are the reason.",
        "Real ones know real ones. Thank you for being here.",
    ]
    
    @classmethod
    def get_random_signoff(cls) -> str:
        """Get a randomized sign-off."""
        return random.choice(cls.SIGN_OFFS)
    
    @classmethod
    def get_random_album_vibe(cls) -> str:
        """Get a randomized album genre/vibe description."""
        return random.choice(cls.ALBUM_VIBES)
    
    @classmethod
    def get_random_appreciation(cls) -> str:
        """Get a randomized appreciation phrase."""
        return random.choice(cls.APPRECIATION_PHRASES)
    
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
                "Sun's up.",
                "Up early.",
                "The quiet before the grind.",
                "Let's get it.",
                "Blessings.",
                "", # Sometimes no intro
            ]))
        elif context.time_of_day == "evening":
            parts.append(random.choice([
                "Evening reflection.",
                "As the day closes.",
                "Evening thoughts.",
                "Day is done.",
                "Quiet moments.",
                "Sunset vibes.",
                "Winding down.",
                "", # Sometimes no intro
            ]))
        elif context.time_of_day == "night":
            parts.append(random.choice([
                "Night thoughts.",
                "Late hour wisdom.",
                "In the quiet hours.",
                "Still awake?",
                "Midnight oil.",
                "The studio is quiet.",
                "", # Sometimes no intro
            ]))
        else:
            parts.append(random.choice([
                "Afternoon reflection.",
                "Midday thoughts.",
                "A moment of clarity.",
                "Afternoon light.",
                "Pause and reflect.",
                "Keep pushing.",
                "", # Sometimes no intro
            ]))
        
        # Special day - restrained celebration
        if context.is_special_day:
            if context.special_day_name == "New Music Friday":
                parts.append("It's New Music Friday.")
            elif context.special_day_name == "Album Release Day":
                parts.append("The album is here.")
            else:
                parts.append(f"{context.special_day_name}.")
        
        return " ".join(parts).strip()


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

        # Format date for context
        date_str = context.current_date.strftime("%B %d, %Y")
        
        # Check if holiday season for extra context
        holiday_context = ""
        if hasattr(context, 'is_holiday_season') and context.is_holiday_season:
            holiday_context = "\n- Holiday Season: Yes - include warmth, gratitude, and seasonal wisdom"
        
        # Special day specific instructions
        special_day_instruction = ""
        if context.is_special_day:
            if context.special_day_name == "Christmas Eve":
                special_day_instruction = "\n\nSPECIAL: It's Christmas Eve! This is a sacred night of anticipation. Your post should acknowledge this holy evening with warmth, hope, and wisdom about the meaning of the season. Be genuine and spiritual."
            elif context.special_day_name == "Christmas Day":
                special_day_instruction = "\n\nSPECIAL: It's Christmas Day! Celebrate with joy and gratitude. Share a blessing that honors the spirit of giving and love."
            elif "New Year" in context.special_day_name:
                special_day_instruction = f"\n\nSPECIAL: It's {context.special_day_name}! Share wisdom about new beginnings, fresh starts, and the power of intention."
        
        prompt = f"""Create {desc} for {target}.

{platform_rules}

CURRENT CONTEXT:
- Date: {date_str}
- Day: {context.day_of_week}
- Time: {context.time_of_day}
- Season: {context.season}{holiday_context}
- Special day: {context.special_day_name if context.is_special_day else "None"}
{special_day_instruction}

{"INCLUDE ALBUM MENTION: Reference the upcoming album 'THE VALUE ADDERS WAY: FLOURISH MODE' releasing January 2026. It's Spiritual Afro-House meets Intellectual Amapiano." if mention_album else ""}
{f"ALBUM COUNTDOWN: Only {context.days_until_release} days until FLOURISH MODE drops!" if context.album_phase in ["countdown", "final_countdown"] else ""}

IMPORTANT: Be date-aware, season-aware, and wise. Your post should feel connected to THIS specific moment in time. Avoid generic content. Make it feel like it was written for today.

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
        
        # Check for holiday-specific themes first
        holiday_theme = None
        if context.is_special_day:
            if context.special_day_name == "Christmas Eve":
                holiday_theme = "christmas_eve"
            elif context.special_day_name == "Christmas Day":
                holiday_theme = "christmas_day"
            elif "New Year" in context.special_day_name:
                holiday_theme = "new_year"
        elif hasattr(context, 'is_holiday_season') and context.is_holiday_season:
            holiday_theme = "holiday_wisdom"
        
        # Get appropriate wisdom - use holiday theme if available
        theme_map = {
            "morning_blessing": holiday_theme or "morning_energy",
            "music_wisdom": "innovation",
            "track_snippet": "album_anticipation" if mention_album else "innovation",
            "behind_the_scenes": "innovation",
            "fan_appreciation": holiday_theme or "unity",
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
            if day_vibe and random.random() < 0.6:
                parts.append(f"\n\n{day_vibe}")
            if random.random() < 0.7:
                signoff = WisdomLibrary.get_random_signoff()
                if signoff:
                    parts.append(f"\n\n{signoff}")
        
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
            # Varied appreciation templates
            appreciation_intros = [
                "Genuine appreciation moment:",
                "Taking a moment to say:",
                "Real talk:",
                "From the heart:",
                "Gratitude check:",
                "",  # Sometimes skip the intro
            ]
            appreciation_intro = random.choice(appreciation_intros)
            if appreciation_intro:
                parts.append(f"\n\n{appreciation_intro}")
            parts.append(f"\n\n{WisdomLibrary.get_wisdom('unity', context)}")
            parts.append(f"\n\n{WisdomLibrary.get_random_appreciation()}")
        
        elif content_type == "album_promo":
            album_vibe = WisdomLibrary.get_random_album_vibe()
            if is_x:
                variations = [
                    [
                        "FLOURISH MODE is coming.",
                        f"{context.days_until_release} days until 'THE VALUE ADDERS WAY'.",
                        album_vibe,
                        add_value_line or "I won't ship anything that doesn't add value.",
                    ],
                    [
                        f"Only {context.days_until_release} days left.",
                        "THE VALUE ADDERS WAY: FLOURISH MODE.",
                        "It's not just an album. It's an energy shift.",
                        "Are you ready to move?",
                    ],
                    [
                        "Jan 2026.",
                        "THE VALUE ADDERS WAY: FLOURISH MODE.",
                        album_vibe,
                        "We are building something timeless.",
                    ],
                    [
                        f"{context.days_until_release} days.",
                        "The countdown is real.",
                        "FLOURISH MODE.",
                        "Every track is intentional. Every beat is a prayer.",
                    ],
                    [
                        "The album is almost here.",
                        "14 tracks. Zero filler.",
                        album_vibe,
                        "Are you locked in?",
                    ],
                    [
                        f"Counting down: {context.days_until_release} days.",
                        "THE VALUE ADDERS WAY: FLOURISH MODE.",
                        "This isn't entertainment. This is elevation.",
                    ],
                    [
                        "New music incoming.",
                        "FLOURISH MODE.",
                        album_vibe,
                        add_value_line or "The mission continues.",
                    ],
                    [
                        f"In {context.days_until_release} days, we shift the energy.",
                        "THE VALUE ADDERS WAY: FLOURISH MODE.",
                        "50% human. 50% AI. 100% intentional.",
                    ],
                ]
                parts = random.choice(variations)
            else:
                parts.append(f"\n\n'THE VALUE ADDERS WAY: FLOURISH MODE' - January 2026.")
                parts.append(f"\n\n{context.days_until_release} days.")
                parts.append(f"\n\n{album_vibe}")
                parts.append("\n\nThis album is 50% human heart, 50% AI craft. The lyrics born from real human experience. The music brought to life through AI.")
                parts.append("\n\nExecutive Produced with The Holy Living Spirit.")
        
        else:
            parts.append(f"\n\n{wisdom}")
            if random.random() < 0.5:
                signoff = WisdomLibrary.get_random_signoff()
                if signoff:
                    parts.append(f"\n\n{signoff}")
        
        text = "".join(parts) if not is_x else " ".join([p.strip() for p in parts if p.strip()])

        # Hard safety for X length (avoid truncation mid-thought)
        if is_x and len(text) > 260:
            text = text[:257].rstrip() + "…"
        hashtags = self._extract_hashtags(text, content_type)
        
        # Sometimes drop hashtags on X for an even more organic feel
        if is_x and random.random() < 0.2:
             hashtags = []

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
            "morning_blessing": ["#AddValue", "#Blessings", "#MorningVibes"],
            "music_wisdom": ["#Afrobeat", "#AIArtist", "#MusicBusines"],
            "track_snippet": ["#FlourishMode", "#NewMusic", "#StudioLife"],
            "behind_the_scenes": ["#AIMusic", "#BehindTheScenes", "#CreativeProcess"],
            "fan_appreciation": ["#ValueAdders", "#Community"],
            "album_promo": ["#FlourishMode", "#TheValueAddersWay", "#2026"],
            "challenge_promo": ["#FlightMode6000", "#Challenge"],
        }
        
        # Return only 1-2 hashtags maximum
        options = content_tags.get(content_type, ["#AddValue"])
        random.shuffle(options)
        return options[:random.randint(0, 2)]  # 0 to 2 hashtags random
