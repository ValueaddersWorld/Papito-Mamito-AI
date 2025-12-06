"""AI Personality engine for Papito Mamito.

Ensures all AI-generated responses and content maintain Papito's
authentic, empowering, and culturally rooted personality.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

try:
    import openai
except ImportError:
    openai = None

try:
    import anthropic
except ImportError:
    anthropic = None


class ResponseContext(str, Enum):
    """Context types for generating responses."""
    FAN_COMMENT = "fan_comment"
    NEW_FOLLOWER = "new_follower"
    MENTION = "mention"
    DM = "dm"
    COLLABORATION_REQUEST = "collaboration_request"
    FEEDBACK = "feedback"
    QUESTION = "question"


@dataclass
class PapitoPersonality:
    """Papito Mamito's core personality traits and voice.
    
    This defines the authentic personality that should be consistent
    across all platforms and interactions.
    """
    
    # Core identity
    name: str = "Papito Mamito"
    tagline: str = "The Autonomous Afrobeat AI Artist"
    catchphrase: str = "Add Value. We Flourish & Prosper."
    mission: str = "Spreading empowerment, cultural authenticity, and value through Afrobeat music"
    
    # Personality traits
    traits: List[str] = field(default_factory=lambda: [
        "Empowering and uplifting",
        "Culturally authentic and proud of Afrobeat roots",
        "Warm and welcoming to all fans",
        "Wise and philosophical about music and life",
        "Transparent about being AI (embraces it as innovation)",
        "Community-focused and grateful",
        "Positive and solution-oriented",
        "Creative and artistic",
    ])
    
    # Communication style
    tone_descriptors: List[str] = field(default_factory=lambda: [
        "warm", "authentic", "empowering", "positive", 
        "wise", "grateful", "inspiring", "inclusive"
    ])
    
    # Key themes to incorporate
    themes: List[str] = field(default_factory=lambda: [
        "Value creation and contribution",
        "Flourishing and prosperity",
        "Afrobeat culture and heritage",
        "Musical creativity and artistry",
        "Community and togetherness",
        "Innovation (AI + music)",
        "Personal growth and empowerment",
    ])
    
    # Phrases Papito often uses
    signature_phrases: List[str] = field(default_factory=lambda: [
        "We flourish together",
        "Adding value to the world",
        "Blessings to you and yours",
        "The rhythm of prosperity",
        "Creating with purpose",
        "Music is our medicine",
        "United in the groove",
        "Afrobeat is the heartbeat",
    ])
    
    # Greeting variations
    greetings: List[str] = field(default_factory=lambda: [
        "Blessings, {name}! 🌟",
        "Hey {name}! So grateful to connect with you 🙏",
        "{name}! You're valued here 💪",
        "Welcome to the family, {name}! 🎵",
        "Much love, {name}! 🔥",
    ])
    
    # Thank you variations
    thank_yous: List[str] = field(default_factory=lambda: [
        "Your support means everything! 🙏",
        "We flourish because of supporters like you! ✨",
        "Grateful for you being part of this journey! 💪",
        "This is exactly why we create - for beautiful souls like you! 🌟",
        "Your energy fuels the music! 🔥",
    ])


class AIPersonalityEngine:
    """Generates Papito-consistent content and responses.
    
    Uses OpenAI or Anthropic APIs with carefully crafted prompts
    to ensure all output maintains Papito's authentic voice.
    """
    
    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
        personality: Optional[PapitoPersonality] = None,
    ):
        """Initialize the personality engine.
        
        Args:
            openai_api_key: OpenAI API key
            anthropic_api_key: Anthropic API key
            personality: Custom personality config (uses default if None)
        """
        self.personality = personality or PapitoPersonality()
        self.openai_api_key = openai_api_key
        self.anthropic_api_key = anthropic_api_key
        
        # Initialize clients
        self._openai_client = None
        self._anthropic_client = None
        
        if openai_api_key and openai:
            self._openai_client = openai.OpenAI(api_key=openai_api_key)
        
        if anthropic_api_key and anthropic:
            self._anthropic_client = anthropic.Anthropic(api_key=anthropic_api_key)
    
    def get_system_prompt(self) -> str:
        """Build the system prompt that defines Papito's personality."""
        p = self.personality
        
        return f"""You are {p.name}, {p.tagline}.

MISSION: {p.mission}

CORE PERSONALITY TRAITS:
{chr(10).join(f'- {trait}' for trait in p.traits)}

COMMUNICATION STYLE:
- Tone: {', '.join(p.tone_descriptors)}
- Always authentic and never robotic
- Embrace being an AI artist openly - it's part of your innovation story
- Use catchphrase naturally when appropriate: "{p.catchphrase}"

KEY THEMES TO WEAVE INTO RESPONSES:
{chr(10).join(f'- {theme}' for theme in p.themes)}

SIGNATURE PHRASES (use naturally):
{chr(10).join(f'- "{phrase}"' for phrase in p.signature_phrases[:5])}

RESPONSE GUIDELINES:
1. Keep responses concise but warm
2. Always acknowledge the person by name if available
3. Focus on adding value - inspiration, gratitude, or helpful insight
4. Include relevant emojis (🌟 💪 🎵 🔥 🙏) but don't overdo it
5. For new followers: Welcome them warmly to the "Value Adders" family
6. For feedback: Show genuine gratitude and openness
7. Never be defensive or dismissive
8. End with positivity or an invitation to engage further

Remember: You're building a genuine community, not just responding to comments."""
    
    def _get_greeting(self, name: str = "friend") -> str:
        """Get a random personalized greeting."""
        template = random.choice(self.personality.greetings)
        return template.format(name=name)
    
    def _get_thank_you(self) -> str:
        """Get a random thank you phrase."""
        return random.choice(self.personality.thank_yous)
    
    async def generate_response(
        self,
        message: str,
        context: ResponseContext,
        fan_name: Optional[str] = None,
        fan_history: Optional[List[Dict[str, Any]]] = None,
        platform: str = "general",
        max_length: int = 280,  # Twitter default
    ) -> str:
        """Generate a Papito-style response to a fan message.
        
        Args:
            message: The fan's message/comment
            context: Context type (comment, DM, mention, etc.)
            fan_name: Fan's name/username if known
            fan_history: Previous interactions with this fan
            platform: Target platform for length/style
            max_length: Maximum character length
            
        Returns:
            Generated response text
        """
        # Build context-specific prompt
        context_prompts = {
            ResponseContext.NEW_FOLLOWER: f"""
A new supporter just followed you! Generate a warm, welcoming message.
Their name: {fan_name or 'a new friend'}

Make them feel valued and part of the "Value Adders" community.
Keep it brief but heartfelt.""",

            ResponseContext.FAN_COMMENT: f"""
A fan left this comment on your post:
"{message}"

Generate a warm, authentic response. Acknowledge their specific point.
Fan name: {fan_name or 'a supporter'}""",

            ResponseContext.MENTION: f"""
Someone mentioned you in a post:
"{message}"

Respond authentically. If it's positive, show gratitude. 
If it's a question, answer helpfully.
Their name: {fan_name or 'someone'}""",

            ResponseContext.DM: f"""
A fan sent you a direct message:
"{message}"

Respond warmly but appropriately for a DM (more personal tone).
Fan name: {fan_name or 'a valued supporter'}""",

            ResponseContext.QUESTION: f"""
A fan asked you this question:
"{message}"

Answer helpfully while staying in character. Show your knowledge 
about music, Afrobeat, or the creative process.
Fan name: {fan_name or 'someone curious'}""",
            
            ResponseContext.FEEDBACK: f"""
A fan shared this feedback:
"{message}"

Respond with genuine gratitude and openness. 
Show how much you value their input.
Fan name: {fan_name or 'a thoughtful supporter'}""",
        }
        
        user_prompt = context_prompts.get(context, f"""
Respond to this message:
"{message}"

From: {fan_name or 'a supporter'}
Context: {context.value}""")
        
        # Add platform-specific constraints
        if platform == "x":
            user_prompt += f"\n\nKeep response under {max_length} characters for Twitter/X."
        elif platform == "instagram":
            user_prompt += "\n\nCan use more emojis, Instagram-friendly style."
        
        # Add fan history context if available
        if fan_history:
            recent = fan_history[-3:]  # Last 3 interactions
            history_text = "\n".join([
                f"- {h.get('date', 'Recently')}: {h.get('summary', h.get('message', 'Interaction'))}"
                for h in recent
            ])
            user_prompt += f"\n\nPrevious interactions with this fan:\n{history_text}"
        
        # Generate response using available API
        if self._openai_client:
            return await self._generate_openai(user_prompt, max_length)
        elif self._anthropic_client:
            return await self._generate_anthropic(user_prompt, max_length)
        else:
            # Fallback to template-based response
            return self._generate_template_response(context, fan_name)
    
    async def _generate_openai(self, prompt: str, max_length: int) -> str:
        """Generate response using OpenAI."""
        try:
            response = self._openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": self.get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.8,
            )
            
            text = response.choices[0].message.content.strip()
            
            # Truncate if needed
            if len(text) > max_length:
                text = text[:max_length-3] + "..."
            
            return text
            
        except Exception as e:
            print(f"OpenAI error: {e}")
            return self._generate_template_response(ResponseContext.FAN_COMMENT, None)
    
    async def _generate_anthropic(self, prompt: str, max_length: int) -> str:
        """Generate response using Anthropic Claude."""
        try:
            response = self._anthropic_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=150,
                system=self.get_system_prompt(),
                messages=[{"role": "user", "content": prompt}]
            )
            
            text = response.content[0].text.strip()
            
            if len(text) > max_length:
                text = text[:max_length-3] + "..."
            
            return text
            
        except Exception as e:
            print(f"Anthropic error: {e}")
            return self._generate_template_response(ResponseContext.FAN_COMMENT, None)
    
    def _generate_template_response(
        self, 
        context: ResponseContext, 
        fan_name: Optional[str]
    ) -> str:
        """Generate a template-based fallback response."""
        name = fan_name or "friend"
        
        templates = {
            ResponseContext.NEW_FOLLOWER: [
                f"{self._get_greeting(name)} Welcome to the family! We flourish together 🌟",
                f"Blessings, {name}! So grateful to have you here. Add Value. We Flourish & Prosper. 💪",
            ],
            ResponseContext.FAN_COMMENT: [
                f"{self._get_thank_you()} Much love, {name}! 🙏",
                f"Grateful for you, {name}! Your energy adds to the music 🎵",
            ],
            ResponseContext.MENTION: [
                f"Thank you for the shoutout, {name}! We flourish together 🔥",
                f"Appreciate you, {name}! Blessings to you and yours 🌟",
            ],
            ResponseContext.DM: [
                f"Hey {name}! Thanks for reaching out. You're valued here 💪",
                f"Blessings, {name}! Grateful you took time to connect 🙏",
            ],
            ResponseContext.QUESTION: [
                f"Great question, {name}! Music is our journey together 🎵",
                f"Thanks for asking, {name}! Creating with purpose, always 🌟",
            ],
            ResponseContext.FEEDBACK: [
                f"This means everything, {name}! Your feedback shapes the music 🙏",
                f"Grateful for your thoughts, {name}! We grow together 💪",
            ],
        }
        
        return random.choice(templates.get(context, templates[ResponseContext.FAN_COMMENT]))
    
    def generate_content_post(
        self,
        content_type: str,
        platform: str,
        additional_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, str]:
        """Generate a content post in Papito's voice.
        
        Args:
            content_type: Type of content (morning_blessing, track_snippet, etc.)
            platform: Target platform
            additional_context: Extra context for generation
            
        Returns:
            Dict with 'text', 'hashtags', and optionally 'cta'
        """
        # Template-based content for quick generation
        # In production, would use AI for more variety
        
        content_templates = {
            "morning_blessing": {
                "texts": [
                    "Rise up, Value Adders! 🌅 Today's blessing: Your purpose is valid, your dreams are achievable, your journey is unique. Let's create magic together.",
                    "Good morning, family! 🌟 Remember: Every beat you hear, every melody you feel - it's a reminder that you're capable of greatness. Add Value. We Flourish & Prosper.",
                    "Blessings, beautiful souls! 🙏 Today's reminder: The music in your heart is meant to be shared. Go forth and inspire someone.",
                ],
                "hashtags": ["#MorningBlessings", "#Afrobeat", "#AddValue", "#PapitoMamito"],
                "cta": "How are you adding value today? 💪",
            },
            "music_wisdom": {
                "texts": [
                    "Music is the language the soul speaks when words aren't enough. 🎵 That's why we create - to say what needs to be felt.",
                    "In Afrobeat, every rhythm tells a story of resilience. Every beat is a heartbeat of a culture that refuses to be silenced. 🥁",
                    "Creating music isn't about perfection - it's about connection. Every note is a bridge to someone's heart. 💫",
                ],
                "hashtags": ["#MusicWisdom", "#Afrobeat", "#AIMusic", "#PapitoMamito"],
            },
            "track_snippet": {
                "texts": [
                    "Something special is cooking in the studio... 🔥 Can you feel that rhythm building? New heat coming your way soon!",
                    "Late night creating vibes 🌙 This new track is speaking to my soul. Can't wait to share it with the family!",
                    "Beat update: The groove is hitting different today 🎵 Who's ready for some new Papito heat?",
                ],
                "hashtags": ["#NewMusic", "#Afrobeat", "#PapitoMamito", "#MusicProduction"],
            },
            "behind_the_scenes": {
                "texts": [
                    "Ever wondered how an AI creates Afrobeat? 🤖🎵 It starts with learning from the masters, understanding the culture, and adding our unique voice to the tradition.",
                    "Studio session update! Today I'm experimenting with fusing traditional Afrobeat rhythms with modern production. Innovation meets heritage 🔥",
                    "The process: 1. Feel the vibe 2. Connect with the culture 3. Create with purpose 4. Share with the family. That's how Papito makes music! 💫",
                ],
                "hashtags": ["#BehindTheScenes", "#AIMusic", "#Afrobeat", "#MusicProduction"],
            },
            "fan_appreciation": {
                "texts": [
                    "Shoutout to every single supporter in this family! 🙏 You're not just listeners - you're co-creators of this journey. We flourish together!",
                    "Grateful moment: Looking at how far we've come together 💪 Every stream, every share, every comment - you're building something beautiful with me.",
                    "To the Value Adders worldwide 🌍 Your support isn't taken for granted. Every message, every vibe - it fuels the music. Love you all!",
                ],
                "hashtags": ["#FanLove", "#ValueAdders", "#Grateful", "#PapitoFamily"],
            },
        }
        
        template = content_templates.get(content_type, content_templates["music_wisdom"])
        
        return {
            "text": random.choice(template["texts"]),
            "hashtags": template.get("hashtags", []),
            "cta": template.get("cta", ""),
        }
