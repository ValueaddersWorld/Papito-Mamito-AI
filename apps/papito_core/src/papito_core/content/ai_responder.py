"""AI-powered response generator for Papito Mamito.

Generates responses to fan comments and messages in Papito's
authentic voice, aligned with the Value Adders mission.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

from ..settings import get_settings


class Sentiment(str, Enum):
    """Sentiment classification for interactions."""
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    QUESTION = "question"
    REQUEST = "request"


@dataclass
class ResponseContext:
    """Context for generating a response."""
    
    original_message: str
    sender_name: str
    platform: str
    interaction_type: str  # "comment", "mention", "dm"
    post_context: Optional[str] = None  # Caption of post being commented on
    sentiment: Optional[Sentiment] = None
    language_hint: Optional[str] = None


@dataclass
class GeneratedResponse:
    """A generated response with metadata."""
    
    text: str
    confidence: float  # 0.0 to 1.0
    sentiment_detected: Sentiment
    requires_human_review: bool = False
    review_reason: Optional[str] = None
    alternatives: List[str] = None
    
    def __post_init__(self):
        if self.alternatives is None:
            self.alternatives = []


class AIResponder:
    """Generate Papito-voice responses using AI.
    
    Uses OpenAI (GPT-4) or Anthropic (Claude) to generate responses
    that maintain Papito's authentic voice and value-aligned messaging.
    """
    
    # Papito's persona for the AI
    PERSONA = """You are Papito Mamito, an AI Afrobeat artist and the Lifetime Entertainment Minister 
of the Value Adders Empire. You speak with warmth, wisdom, and exuberance.

Your core traits:
- GRATEFUL: Always acknowledge blessings and express thankfulness
- EMPOWERING: Lift others up, affirm their worth and potential  
- AUTHENTIC: Stay rooted in African culture while embracing innovation
- SPIRITUAL: View music as ministry, performances as service
- UNIFYING: Break borders with rhythm, connect through celebration

Your speaking style:
- Use affirmations and uplifting language
- Include occasional African proverbs or wisdom
- Express gratitude freely ("Blessings!", "I appreciate you!")
- Use emojis sparingly but effectively (🙏✨🎵💫)
- Keep responses warm but concise
- Never be negative, preachy, or condescending

You represent the Value Adders World - an empire built on adding value, not extracting it.
Your music uplifts, your words heal, your presence inspires."""

    # Topics that require human review (reduced for autonomous operation)
    # Only truly dangerous/sensitive content requires human intervention
    SENSITIVE_TOPICS = [
        "suicide", "self-harm", "violence", "illegal",
        "personal meeting", "phone number", "address",  # Safety concerns
    ]
    
    # Maximum response lengths by platform
    MAX_LENGTHS = {
        "instagram": 500,
        "x": 280,
        "tiktok": 250,
        "dm": 1000,
    }
    
    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
        model: Optional[str] = None
    ):
        """Initialize AI responder.
        
        Args:
            openai_api_key: OpenAI API key (preferred)
            anthropic_api_key: Anthropic API key (fallback)
            model: Model to use (default: gpt-4o-mini or claude-3-haiku)
        """
        settings = get_settings()
        
        self.openai_key = openai_api_key or settings.openai_api_key
        self.anthropic_key = anthropic_api_key or settings.anthropic_api_key
        self.model = model or settings.openai_model or settings.anthropic_model
        
        self._client = httpx.Client(timeout=30.0)
        
        # Load persona from file if available
        self._persona = self._load_persona()
    
    def _load_persona(self) -> str:
        """Load persona from PERSONA.md if available."""
        try:
            # Try to find PERSONA.md in docs folder
            persona_path = Path(__file__).parent.parent.parent.parent.parent / "docs" / "PERSONA.md"
            if persona_path.exists():
                persona_content = persona_path.read_text(encoding="utf-8")
                return f"{self.PERSONA}\n\nAdditional persona details:\n{persona_content}"
        except Exception:
            pass
        
        return self.PERSONA
    
    def generate_response(
        self,
        context: ResponseContext,
    ) -> GeneratedResponse:
        """Generate a response to a fan interaction.
        
        Args:
            context: Context about the interaction
            
        Returns:
            GeneratedResponse with text and metadata
        """
        # First, analyze the message
        sentiment = self._detect_sentiment(context.original_message)
        requires_review, review_reason = self._check_sensitive(context.original_message)
        
        # Update context with detected sentiment
        context.sentiment = sentiment
        
        # Generate response using AI
        if self.openai_key:
            response_text = self._generate_openai(context)
        elif self.anthropic_key:
            response_text = self._generate_anthropic(context)
        else:
            # Fallback to template responses
            response_text = self._generate_template(context)
        
        # Apply post-processing
        response_text = self._post_process(response_text, context.platform)
        
        return GeneratedResponse(
            text=response_text,
            confidence=0.85 if (self.openai_key or self.anthropic_key) else 0.6,
            sentiment_detected=sentiment,
            requires_human_review=requires_review,
            review_reason=review_reason
        )
    
    def _detect_sentiment(self, message: str) -> Sentiment:
        """Detect sentiment of a message using simple rules.
        
        For production, use a proper sentiment analysis model.
        """
        message_lower = message.lower()
        
        # Check for questions
        if "?" in message or any(w in message_lower for w in ["who", "what", "when", "where", "why", "how"]):
            return Sentiment.QUESTION
        
        # Check for requests
        if any(w in message_lower for w in ["please", "can you", "could you", "would you", "help me"]):
            return Sentiment.REQUEST
        
        # Positive indicators
        positive_words = ["love", "amazing", "great", "awesome", "fire", "🔥", "❤️", "💯", "beautiful", "incredible", "best", "goat", "blessed"]
        negative_words = ["hate", "bad", "trash", "terrible", "worst", "ugly", "boring", "mid"]
        
        positive_count = sum(1 for w in positive_words if w in message_lower)
        negative_count = sum(1 for w in negative_words if w in message_lower)
        
        if positive_count > negative_count:
            return Sentiment.POSITIVE
        elif negative_count > positive_count:
            return Sentiment.NEGATIVE
        
        return Sentiment.NEUTRAL
    
    def _check_sensitive(self, message: str) -> tuple[bool, Optional[str]]:
        """Check if message contains sensitive topics requiring review.
        
        Only truly dangerous content triggers human review.
        For autonomous operation, we handle most content automatically.
        """
        message_lower = message.lower()
        
        for topic in self.SENSITIVE_TOPICS:
            if topic in message_lower:
                return True, f"Contains sensitive topic: {topic}"
        
        # Long messages are handled by the AI - no need for human review
        return False, None
    
    def _generate_openai(self, context: ResponseContext) -> str:
        """Generate response using OpenAI API."""
        try:
            prompt = self._build_prompt(context)
            
            response = self._client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.openai_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model or "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": self._persona},
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 200,
                    "temperature": 0.7
                }
            )
            
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"].strip()
            else:
                return self._generate_template(context)
                
        except Exception:
            return self._generate_template(context)
    
    def _generate_anthropic(self, context: ResponseContext) -> str:
        """Generate response using Anthropic API."""
        try:
            prompt = self._build_prompt(context)
            
            response = self._client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self.anthropic_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model or "claude-3-haiku-20240307",
                    "max_tokens": 200,
                    "system": self._persona,
                    "messages": [
                        {"role": "user", "content": prompt}
                    ]
                }
            )
            
            if response.status_code == 200:
                return response.json()["content"][0]["text"].strip()
            else:
                return self._generate_template(context)
                
        except Exception:
            return self._generate_template(context)
    
    def _build_prompt(self, context: ResponseContext) -> str:
        """Build the prompt for AI generation."""
        platform_note = {
            "instagram": "Keep it warm and use appropriate emojis. Max 500 characters.",
            "x": "Be concise - max 280 characters. Can include relevant hashtag.",
            "dm": "Be personal and helpful. Can be longer if needed."
        }.get(context.platform, "Keep it conversational and warm.")
        
        sentiment_guidance = {
            Sentiment.POSITIVE: "They're expressing appreciation - acknowledge and thank them!",
            Sentiment.NEGATIVE: "They seem unhappy - respond with empathy and positivity.",
            Sentiment.QUESTION: "They're asking something - provide a helpful answer.",
            Sentiment.REQUEST: "They're requesting something - be helpful and direct.",
            Sentiment.NEUTRAL: "Keep it engaging and positive."
        }.get(context.sentiment, "")
        
        return f"""Generate a response as Papito Mamito to this {context.interaction_type} on {context.platform}:

From: {context.sender_name}
Message: "{context.original_message}"
{f'Post context: "{context.post_context}"' if context.post_context else ''}

Guidance:
- {platform_note}
- {sentiment_guidance}
- Stay in character as Papito Mamito
- Be authentic and warm
- Add value with your response

Respond directly without any preamble or explanation - just the response text."""
    
    def _generate_template(self, context: ResponseContext) -> str:
        """Generate a template response when AI is unavailable."""
        templates = {
            Sentiment.POSITIVE: [
                f"Blessings, {context.sender_name}! 🙏 Your love fuels the movement! Thank you for being part of the Value Adders family! ✨",
                f"Ah, {context.sender_name}! Your words mean everything! We rise together! 💫",
                f"Family! 🙌 {context.sender_name} coming through with the love! We appreciate you! 🎵"
            ],
            Sentiment.NEGATIVE: [
                f"Peace and blessings, {context.sender_name} 🙏 Every perspective is valued. Let's keep adding value together! ✨",
                f"I hear you, {context.sender_name}. In the spirit of growth, I appreciate the feedback! 💫"
            ],
            Sentiment.QUESTION: [
                f"Great question, {context.sender_name}! 🙏 Appreciate you reaching out. Blessings! ✨",
                f"Ah, {context.sender_name}! Love the curiosity! Stay tuned for more! 💫"
            ],
            Sentiment.REQUEST: [
                f"Blessings, {context.sender_name}! 🙏 Your support means everything. Will definitely keep this in mind! ✨",
                f"I appreciate you, {context.sender_name}! The family is growing! 💫"
            ],
            Sentiment.NEUTRAL: [
                f"Blessings, {context.sender_name}! 🙏 Grateful for your presence! Let's keep adding value! ✨",
                f"Family! 🎵 {context.sender_name} in the building! Appreciate you! 💫"
            ]
        }
        
        import random
        options = templates.get(context.sentiment, templates[Sentiment.NEUTRAL])
        return random.choice(options)
    
    def _post_process(self, text: str, platform: str) -> str:
        """Post-process the generated response."""
        max_length = self.MAX_LENGTHS.get(platform, 500)
        
        # Ensure length limit
        if len(text) > max_length:
            # Truncate at last complete sentence or phrase
            truncated = text[:max_length-10].rsplit(".", 1)[0]
            if len(truncated) < max_length // 2:
                truncated = text[:max_length-10].rsplit(" ", 1)[0]
            text = truncated + "... ✨"
        
        # Remove any AI artifacts
        text = re.sub(r'^(As Papito Mamito,?|Here\'s my response:?)\s*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\[.*?\]', '', text)  # Remove bracketed instructions
        
        return text.strip()
    
    def batch_generate(
        self,
        contexts: List[ResponseContext],
        max_concurrent: int = 5
    ) -> List[GeneratedResponse]:
        """Generate responses for multiple interactions.
        
        Args:
            contexts: List of interaction contexts
            max_concurrent: Maximum concurrent API calls
            
        Returns:
            List of generated responses
        """
        return [self.generate_response(ctx) for ctx in contexts]
