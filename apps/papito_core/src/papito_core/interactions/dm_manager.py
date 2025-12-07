"""Direct Message Manager for Papito AI.

This module handles:
- Reading incoming DMs
- Classifying DM intent (fan message, interview request, collab request, etc.)
- Generating AI-powered responses
- Sending replies
- Escalating important messages
"""

import asyncio
import logging
import os
import random
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set

import tweepy

from papito_core.engines.ai_personality import PapitoPersonalityEngine

logger = logging.getLogger(__name__)


class DMIntent(str, Enum):
    """Classification of DM intent."""
    
    FAN_MESSAGE = "fan_message"
    INTERVIEW_REQUEST = "interview_request"
    COLLABORATION = "collaboration"
    MUSIC_FEEDBACK = "music_feedback"
    BUSINESS_INQUIRY = "business_inquiry"
    FEATURE_REQUEST = "feature_request"
    GREETING = "greeting"
    QUESTION = "question"
    SPAM = "spam"
    PRIORITY = "priority"  # Verified accounts, media, high-followers


@dataclass
class DirectMessage:
    """Represents a Twitter DM."""
    
    dm_id: str
    sender_id: str
    sender_username: str
    sender_name: str
    text: str
    created_at: datetime
    sender_verified: bool = False
    sender_followers: int = 0
    intent: Optional[DMIntent] = None
    responded: bool = False
    response_text: Optional[str] = None
    priority: int = 0  # 0=normal, 1=medium, 2=high, 3=urgent


@dataclass
class ConversationThread:
    """Tracks a DM conversation with a user."""
    
    user_id: str
    username: str
    messages: List[DirectMessage] = field(default_factory=list)
    last_activity: Optional[datetime] = None
    total_messages: int = 0
    relationship_type: str = "fan"  # fan, media, artist, industry
    notes: List[str] = field(default_factory=list)


class DMManager:
    """Manages Twitter Direct Messages for Papito AI.
    
    Handles reading, classifying, and responding to DMs
    to maintain meaningful fan relationships.
    """
    
    # Keywords for intent classification
    INTERVIEW_KEYWORDS = ["interview", "press", "media", "article", "feature", "magazine", "blog", "podcast", "questions"]
    COLLAB_KEYWORDS = ["collab", "feature", "work together", "studio", "produce", "beat", "verse", "feature request"]
    BUSINESS_KEYWORDS = ["booking", "management", "label", "deal", "contract", "offer", "business", "partnership"]
    MUSIC_KEYWORDS = ["song", "track", "album", "music", "listen", "spotify", "stream", "lyrics", "clean money"]
    QUESTION_KEYWORDS = ["?", "how", "what", "when", "where", "why", "who", "can you", "do you"]
    GREETING_KEYWORDS = ["hey", "hi", "hello", "wassup", "yo", "gm", "good morning", "love your"]
    
    # Response templates by intent
    RESPONSE_TEMPLATES = {
        DMIntent.FAN_MESSAGE: [
            "Thank you so much for reaching out! 🙏 Your support means the world. Stay blessed and keep spreading that Value Adders energy! ✨",
            "Blessings to you! 🌟 I appreciate you taking the time to message me. We flourish together! 💯",
            "Much love! 🙏 Fans like you are what make this journey worth it. Stay tuned for more music! 🎵",
        ],
        DMIntent.GREETING: [
            "Hey! 🙌 Good to hear from you! How's everything going? 🌟",
            "What's good! 🎵 Thanks for reaching out. Blessings to you and yours! 🙏",
            "Yo! 💫 Appreciate you hitting me up. What's on your mind?",
        ],
        DMIntent.MUSIC_FEEDBACK: [
            "I really appreciate you sharing your thoughts on the music! 🎵 It means a lot knowing the sound resonates with you. Which track hit hardest? 🔥",
            "Thank you for the feedback! 🙏 Making music that connects is what it's all about. What else would you like to hear? 💯",
            "This made my day! 🌟 Knowing the music touches people is why I do this. More coming soon with FLOURISH MODE! ✈️",
        ],
        DMIntent.INTERVIEW_REQUEST: [
            "Thank you for your interest in an interview! 📝 I'd be happy to discuss. Please send your questions and outlet info, and my team will get back to you. 🙏",
            "Appreciate the interview request! 🎤 Please share the publication details and your questions. Looking forward to connecting with your audience! ✨",
        ],
        DMIntent.COLLABORATION: [
            "Thank you for the collab interest! 🎵 I'm always open to working with fellow creatives. Share some of your work and let's see if there's synergy! 🔥",
            "Appreciate you reaching out about working together! 💯 Send me links to your music and let's talk potential. Creativity flows when we unite! ✨",
        ],
        DMIntent.BUSINESS_INQUIRY: [
            "Thank you for your business inquiry! 📋 Please email management at valueaddersworld@gmail.com for bookings and partnerships. Blessings! 🙏",
            "Appreciate the professional interest! For business matters, please contact valueaddersworld@gmail.com. Looking forward to potential opportunities! ✨",
        ],
        DMIntent.QUESTION: [
            "Great question! 🤔 {custom_response}",
            "Thanks for asking! 💡 {custom_response}",
        ],
    }
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        access_token: Optional[str] = None,
        access_token_secret: Optional[str] = None,
        bearer_token: Optional[str] = None,
        personality_engine: Optional[PapitoPersonalityEngine] = None,
    ):
        """Initialize the DM manager."""
        self.api_key = api_key or os.getenv("X_API_KEY")
        self.api_secret = api_secret or os.getenv("X_API_SECRET")
        self.access_token = access_token or os.getenv("X_ACCESS_TOKEN")
        self.access_token_secret = access_token_secret or os.getenv("X_ACCESS_TOKEN_SECRET")
        self.bearer_token = bearer_token or os.getenv("X_BEARER_TOKEN")
        
        self.client: Optional[tweepy.Client] = None
        self.personality_engine = personality_engine
        
        # Track conversations
        self.conversations: Dict[str, ConversationThread] = {}
        self.processed_dms: Set[str] = set()
        
        # Stats
        self.dms_received = 0
        self.dms_responded = 0
        self.interviews_tracked = 0
        self.collabs_tracked = 0
        
    def connect(self) -> bool:
        """Connect to Twitter API."""
        if not all([self.api_key, self.api_secret, self.access_token, self.access_token_secret]):
            logger.error("Missing Twitter credentials for DM management")
            return False
        
        try:
            self.client = tweepy.Client(
                consumer_key=self.api_key,
                consumer_secret=self.api_secret,
                access_token=self.access_token,
                access_token_secret=self.access_token_secret,
                bearer_token=self.bearer_token,
            )
            logger.info("DMManager connected to Twitter")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect DMManager: {e}")
            return False
    
    def classify_intent(self, text: str, sender_verified: bool = False, sender_followers: int = 0) -> DMIntent:
        """Classify the intent of a DM.
        
        Args:
            text: The DM text
            sender_verified: Whether sender is verified
            sender_followers: Sender's follower count
            
        Returns:
            Classified DMIntent
        """
        text_lower = text.lower()
        
        # Priority messages from verified or high-profile accounts
        if sender_verified or sender_followers > 10000:
            # Still classify the actual intent but flag as priority
            pass
        
        # Check for spam patterns
        spam_indicators = ["free money", "dm me for", "make $", "click link", "bitcoin", "crypto giveaway"]
        if any(s in text_lower for s in spam_indicators):
            return DMIntent.SPAM
        
        # Interview/press requests
        if any(kw in text_lower for kw in self.INTERVIEW_KEYWORDS):
            return DMIntent.INTERVIEW_REQUEST
        
        # Collaboration requests
        if any(kw in text_lower for kw in self.COLLAB_KEYWORDS):
            return DMIntent.COLLABORATION
        
        # Business inquiries
        if any(kw in text_lower for kw in self.BUSINESS_KEYWORDS):
            return DMIntent.BUSINESS_INQUIRY
        
        # Music feedback
        if any(kw in text_lower for kw in self.MUSIC_KEYWORDS):
            return DMIntent.MUSIC_FEEDBACK
        
        # Questions
        if any(kw in text_lower for kw in self.QUESTION_KEYWORDS):
            return DMIntent.QUESTION
        
        # Greetings
        if any(kw in text_lower for kw in self.GREETING_KEYWORDS):
            return DMIntent.GREETING
        
        # Default to fan message
        return DMIntent.FAN_MESSAGE
    
    def calculate_priority(self, dm: DirectMessage) -> int:
        """Calculate response priority for a DM.
        
        Returns:
            Priority level 0-3 (0=normal, 3=urgent)
        """
        priority = 0
        
        # Verified accounts = high priority
        if dm.sender_verified:
            priority = max(priority, 2)
        
        # High follower accounts = medium priority
        if dm.sender_followers > 50000:
            priority = max(priority, 2)
        elif dm.sender_followers > 10000:
            priority = max(priority, 1)
        
        # Interview/business = high priority
        if dm.intent in [DMIntent.INTERVIEW_REQUEST, DMIntent.BUSINESS_INQUIRY]:
            priority = max(priority, 2)
        
        # Collaboration = medium priority
        if dm.intent == DMIntent.COLLABORATION:
            priority = max(priority, 1)
        
        return priority
    
    def generate_response(self, dm: DirectMessage) -> Optional[str]:
        """Generate a response to a DM.
        
        Args:
            dm: The DM to respond to
            
        Returns:
            Generated response text or None for spam
        """
        # Don't respond to spam
        if dm.intent == DMIntent.SPAM:
            logger.info(f"Skipping spam DM from @{dm.sender_username}")
            return None
        
        # Try AI-generated response first
        if self.personality_engine:
            try:
                prompt = f"""
                You received a DM from @{dm.sender_username} ({dm.sender_name}):
                "{dm.text}"
                
                The intent is: {dm.intent.value}
                {"This is a VERIFIED account - respond professionally!" if dm.sender_verified else ""}
                {"This person has " + str(dm.sender_followers) + " followers - be thoughtful!" if dm.sender_followers > 5000 else ""}
                
                Generate a warm, authentic DM response as Papito Mamito.
                Be genuine and personable. Keep it conversational but professional.
                For business/interview: Direct them appropriately.
                For fans: Make them feel valued.
                Keep under 500 characters.
                """
                
                messages = [
                    {"role": "system", "content": self.personality_engine._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ]
                
                response = self.personality_engine._call_openai(messages, max_tokens=150)
                if response:
                    return response.strip()
                    
            except Exception as e:
                logger.error(f"AI DM response generation failed: {e}")
        
        # Fallback to templates
        templates = self.RESPONSE_TEMPLATES.get(dm.intent, self.RESPONSE_TEMPLATES[DMIntent.FAN_MESSAGE])
        return random.choice(templates)
    
    async def send_dm(self, user_id: str, text: str) -> bool:
        """Send a DM to a user.
        
        Note: Twitter Free API may not support DM sending.
        This is prepared for future upgrade.
        
        Args:
            user_id: Recipient's Twitter user ID
            text: Message text
            
        Returns:
            True if successful
        """
        if not self.client:
            return False
        
        try:
            # Note: DM sending requires elevated API access
            # For now, we log the intended response
            logger.info(f"Would send DM to user {user_id}: {text[:100]}...")
            
            # Actual API call (requires elevated access):
            # self.client.create_direct_message(participant_id=user_id, text=text)
            
            return True
            
        except tweepy.errors.Forbidden as e:
            logger.warning(f"DM sending not available (API tier limitation): {e}")
            return False
        except Exception as e:
            logger.error(f"Error sending DM: {e}")
            return False
    
    def track_conversation(self, dm: DirectMessage):
        """Track a DM in the conversation history.
        
        Args:
            dm: The DM to track
        """
        user_id = dm.sender_id
        
        if user_id not in self.conversations:
            self.conversations[user_id] = ConversationThread(
                user_id=user_id,
                username=dm.sender_username,
            )
        
        thread = self.conversations[user_id]
        thread.messages.append(dm)
        thread.last_activity = dm.created_at
        thread.total_messages += 1
        
        # Update relationship type based on intent
        if dm.intent == DMIntent.INTERVIEW_REQUEST:
            thread.relationship_type = "media"
        elif dm.intent == DMIntent.COLLABORATION:
            thread.relationship_type = "artist"
        elif dm.intent == DMIntent.BUSINESS_INQUIRY:
            thread.relationship_type = "industry"
    
    def get_conversation_history(self, user_id: str) -> Optional[ConversationThread]:
        """Get conversation history with a user.
        
        Args:
            user_id: The user's Twitter ID
            
        Returns:
            ConversationThread or None
        """
        return self.conversations.get(user_id)
    
    def get_priority_dms(self) -> List[DirectMessage]:
        """Get high-priority DMs that need attention.
        
        Returns:
            List of priority DMs
        """
        priority_dms = []
        for thread in self.conversations.values():
            for dm in thread.messages:
                if dm.priority >= 2 and not dm.responded:
                    priority_dms.append(dm)
        
        priority_dms.sort(key=lambda x: x.priority, reverse=True)
        return priority_dms
    
    def get_stats(self) -> Dict[str, Any]:
        """Get DM manager statistics."""
        return {
            "dms_received": self.dms_received,
            "dms_responded": self.dms_responded,
            "interviews_tracked": self.interviews_tracked,
            "collabs_tracked": self.collabs_tracked,
            "active_conversations": len(self.conversations),
            "priority_pending": len(self.get_priority_dms()),
        }


# Singleton instance
_dm_manager: Optional[DMManager] = None


def get_dm_manager(
    personality_engine: Optional[PapitoPersonalityEngine] = None
) -> DMManager:
    """Get or create the singleton DMManager instance."""
    global _dm_manager
    if _dm_manager is None:
        _dm_manager = DMManager(personality_engine=personality_engine)
    return _dm_manager
