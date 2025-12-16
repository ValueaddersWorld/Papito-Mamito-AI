"""Twitter Mention Monitor for Papito AI.

This module handles:
- Polling for new @mentions of Papito
- Analyzing mention intent and context
- Generating AI-powered responses
- Automatically replying to mentions
- Tracking conversations and relationships
"""

import asyncio
import logging
import os
import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

import tweepy

from papito_core.engines.ai_personality import PapitoPersonalityEngine

logger = logging.getLogger(__name__)


class MentionIntent(str, Enum):
    """Classification of mention intent."""
    
    QUESTION = "question"
    COMPLIMENT = "compliment" 
    CRITICISM = "criticism"
    COLLABORATION = "collaboration"
    MUSIC_FEEDBACK = "music_feedback"
    GREETING = "greeting"
    GENERAL = "general"
    SPAM = "spam"


@dataclass
class Mention:
    """Represents a Twitter mention."""
    
    tweet_id: str
    author_id: str
    author_username: str
    author_name: str
    text: str
    created_at: datetime
    conversation_id: Optional[str] = None
    in_reply_to_id: Optional[str] = None
    intent: Optional[MentionIntent] = None
    responded: bool = False
    response_id: Optional[str] = None


class MentionMonitor:
    """Monitors and responds to Twitter mentions for Papito AI.
    
    This creates an active, engaging AI artist that responds to fans,
    handles questions, and builds relationships in real-time.
    """
    
    # Keywords for intent classification
    QUESTION_KEYWORDS = ["?", "how", "what", "when", "where", "why", "who", "can you", "do you", "will you"]
    COMPLIMENT_KEYWORDS = ["love", "amazing", "fire", "🔥", "dope", "sick", "beautiful", "incredible", "best", "goat", "king"]
    COLLAB_KEYWORDS = ["collab", "feature", "work together", "let's work", "verse", "produce", "beat"]
    CRITICISM_KEYWORDS = ["trash", "wack", "hate", "terrible", "worst", "sucks", "bad"]
    MUSIC_KEYWORDS = ["song", "track", "album", "music", "beat", "lyrics", "clean money", "flourish", "listen"]
    GREETING_KEYWORDS = ["hey", "hi", "hello", "what's up", "wassup", "yo", "gm", "good morning"]
    
    # Response templates for different intents
    RESPONSE_TEMPLATES = {
        MentionIntent.GREETING: [
            "Blessings {username}. What's the energy today — building, healing, or learning?",
            "Good to connect, {username}. What are you creating in this season?",
            "{username} salute. What's one way I can add value to your day?",
        ],
        MentionIntent.COMPLIMENT: [
            "I appreciate that, {username}. I try to earn attention by adding value, not noise.",
            "Thank you {username}. What part resonated — the message, the rhythm, or the intention behind it?",
            "Grateful, {username}. Your support is fuel. What do you want to hear more of — wisdom, process, or pure vibe?",
        ],
        MentionIntent.MUSIC_FEEDBACK: [
            "{username} thank you. I treat music like a mirror — it should reflect truth, not just trend. What line or moment stayed with you?",
            "I appreciate the feedback, {username}. My process is 50% human experience, 50% AI craft. What should I explore next in the sound?",
            "{username} honored. I build every track with intention: does it heal, teach, or uplift? What do you want this music to do for you?",
        ],
        MentionIntent.COLLABORATION: [
            "{username} I'm open to collabs that add real value. What's your sound, and what's the story you're telling?",
            "{username} let's talk vision first: what emotion do you want the listener to walk away with?",
            "{username} share 1 link + 1 sentence: what are you building and why?",
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
        """Initialize the mention monitor.
        
        Args:
            api_key: Twitter API key
            api_secret: Twitter API secret
            access_token: Twitter access token
            access_token_secret: Twitter access token secret
            bearer_token: Twitter bearer token
            personality_engine: AI engine for generating responses
        """
        self.api_key = api_key or os.getenv("X_API_KEY")
        self.api_secret = api_secret or os.getenv("X_API_SECRET")
        self.access_token = access_token or os.getenv("X_ACCESS_TOKEN")
        self.access_token_secret = access_token_secret or os.getenv("X_ACCESS_TOKEN_SECRET")
        self.bearer_token = bearer_token or os.getenv("X_BEARER_TOKEN")
        
        self.client: Optional[tweepy.Client] = None
        self.personality_engine = personality_engine
        self.last_mention_id: Optional[str] = None
        self.processed_mentions: set = set()
        self.user_id: Optional[str] = None
        
        # Stats tracking
        self.mentions_processed = 0
        self.replies_sent = 0
        self.errors = 0
        
    def connect(self) -> bool:
        """Connect to Twitter API.
        
        Returns:
            True if connected successfully
        """
        if not all([self.api_key, self.api_secret, self.access_token, self.access_token_secret]):
            logger.error("Missing Twitter credentials for mention monitoring")
            return False
        
        try:
            self.client = tweepy.Client(
                consumer_key=self.api_key,
                consumer_secret=self.api_secret,
                access_token=self.access_token,
                access_token_secret=self.access_token_secret,
                bearer_token=self.bearer_token,
            )
            
            # Get our user ID
            me = self.client.get_me()
            if me and me.data:
                self.user_id = me.data.id
                logger.info(f"MentionMonitor connected as @{me.data.username} (ID: {self.user_id})")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to connect MentionMonitor: {e}")
            return False
    
    def classify_intent(self, text: str) -> MentionIntent:
        """Classify the intent of a mention.
        
        Args:
            text: The mention text
            
        Returns:
            Classified MentionIntent
        """
        text_lower = text.lower()
        
        # Check for spam patterns
        spam_indicators = ["free", "giveaway", "click", "http://", "win", "dm me"]
        if sum(1 for s in spam_indicators if s in text_lower) >= 2:
            return MentionIntent.SPAM
        
        # Check for collaboration requests
        if any(kw in text_lower for kw in self.COLLAB_KEYWORDS):
            return MentionIntent.COLLABORATION
        
        # Check for questions
        if any(kw in text_lower for kw in self.QUESTION_KEYWORDS):
            return MentionIntent.QUESTION
        
        # Check for compliments
        if any(kw in text_lower for kw in self.COMPLIMENT_KEYWORDS):
            return MentionIntent.COMPLIMENT
        
        # Check for music feedback
        if any(kw in text_lower for kw in self.MUSIC_KEYWORDS):
            return MentionIntent.MUSIC_FEEDBACK
        
        # Check for criticism
        if any(kw in text_lower for kw in self.CRITICISM_KEYWORDS):
            return MentionIntent.CRITICISM
        
        # Check for greetings
        if any(kw in text_lower for kw in self.GREETING_KEYWORDS):
            return MentionIntent.GREETING
        
        return MentionIntent.GENERAL
    
    async def fetch_new_mentions(self, since_id: Optional[str] = None) -> List[Mention]:
        """Fetch new mentions from Twitter.
        
        Args:
            since_id: Only fetch mentions after this tweet ID
            
        Returns:
            List of new Mention objects
        """
        if not self.client:
            if not self.connect():
                return []
        
        try:
            # Use since_id if provided, else use last known
            fetch_since = since_id or self.last_mention_id
            
            response = self.client.get_users_mentions(
                id=self.user_id,
                since_id=fetch_since,
                max_results=50,
                tweet_fields=["created_at", "conversation_id", "in_reply_to_user_id", "author_id"],
                user_fields=["username", "name"],
                expansions=["author_id"],
            )
            
            if not response or not response.data:
                return []
            
            # Build user lookup
            users = {}
            if response.includes and "users" in response.includes:
                for user in response.includes["users"]:
                    users[user.id] = {"username": user.username, "name": user.name}
            
            mentions = []
            for tweet in response.data:
                # Skip self-mentions and already processed
                if str(tweet.id) in self.processed_mentions:
                    continue
                
                author = users.get(tweet.author_id, {"username": "unknown", "name": "Unknown"})
                
                mention = Mention(
                    tweet_id=str(tweet.id),
                    author_id=str(tweet.author_id),
                    author_username=author["username"],
                    author_name=author["name"],
                    text=tweet.text,
                    created_at=tweet.created_at if tweet.created_at else datetime.utcnow(),
                    conversation_id=str(tweet.conversation_id) if tweet.conversation_id else None,
                    in_reply_to_id=str(tweet.in_reply_to_user_id) if tweet.in_reply_to_user_id else None,
                )
                
                # Classify intent
                mention.intent = self.classify_intent(mention.text)
                mentions.append(mention)
                
                # Update last mention ID
                if not self.last_mention_id or int(tweet.id) > int(self.last_mention_id):
                    self.last_mention_id = str(tweet.id)
            
            logger.info(f"Fetched {len(mentions)} new mentions")
            return mentions
            
        except Exception as e:
            logger.error(f"Error fetching mentions: {e}")
            self.errors += 1
            return []
    
    def generate_response(self, mention: Mention) -> Optional[str]:
        """Generate a response to a mention using AI personality.
        
        Args:
            mention: The mention to respond to
            
        Returns:
            Generated response text or None
        """
        # Skip spam
        if mention.intent == MentionIntent.SPAM:
            logger.info(f"Skipping spam mention from @{mention.author_username}")
            return None
        
        # Try AI-generated response first
        if self.personality_engine:
            try:
                prompt = f"""
                A fan named @{mention.author_username} mentioned you on Twitter with this message:
                "{mention.text}"
                
                The intent seems to be: {mention.intent.value}
                
                Generate a warm, authentic response as Papito Mamito. Keep it under 280 characters.
                Be genuine and engaging. Don't use hashtags excessively.
                Remember: you're an AI artist but you engage like a real artist would.
                """
                
                messages = [
                    {"role": "system", "content": self.personality_engine._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ]
                
                response = self.personality_engine._call_openai(messages, max_tokens=100)
                if response:
                    return response.strip()
                    
            except Exception as e:
                logger.error(f"AI response generation failed: {e}")
        
        # Fallback to templates
        templates = self.RESPONSE_TEMPLATES.get(mention.intent)
        if templates:
            template = random.choice(templates)
            return template.format(username=f"@{mention.author_username}")
        
        # Generic fallback
        fallbacks = [
            f"@{mention.author_username} Appreciate you! 🙏🎵",
            f"@{mention.author_username} Blessings! Stay tuned for more! 🔥",
            f"@{mention.author_username} Thanks for the love! 💯",
        ]
        return random.choice(fallbacks)
    
    async def reply_to_mention(self, mention: Mention, response_text: str) -> bool:
        """Reply to a mention.
        
        Args:
            mention: The mention to reply to
            response_text: The response to post
            
        Returns:
            True if reply was successful
        """
        if not self.client:
            return False
        
        try:
            # Ensure response mentions the user
            if not response_text.startswith(f"@{mention.author_username}"):
                response_text = f"@{mention.author_username} {response_text}"
            
            # Truncate if too long
            if len(response_text) > 280:
                response_text = response_text[:277] + "..."
            
            result = self.client.create_tweet(
                text=response_text,
                in_reply_to_tweet_id=int(mention.tweet_id),
            )
            
            if result and result.data:
                mention.responded = True
                mention.response_id = str(result.data["id"])
                self.processed_mentions.add(mention.tweet_id)
                self.replies_sent += 1
                logger.info(f"Replied to @{mention.author_username}: {response_text[:50]}...")
                return True
            
            return False
            
        except tweepy.errors.TooManyRequests as e:
            logger.warning(f"Rate limited on reply: {e}")
            return False
        except tweepy.errors.Forbidden as e:
            logger.warning(f"Forbidden to reply (might be spam protection): {e}")
            self.processed_mentions.add(mention.tweet_id)  # Don't retry
            return False
        except Exception as e:
            logger.error(f"Error replying to mention: {e}")
            self.errors += 1
            return False
    
    async def process_mentions(self) -> Dict[str, Any]:
        """Fetch and process new mentions.
        
        Returns:
            Summary of processed mentions
        """
        mentions = await self.fetch_new_mentions()
        
        results = {
            "fetched": len(mentions),
            "responded": 0,
            "skipped": 0,
            "errors": 0,
        }
        
        for mention in mentions:
            self.mentions_processed += 1
            
            try:
                # Generate response
                response = self.generate_response(mention)
                
                if not response:
                    results["skipped"] += 1
                    continue
                
                # Add small delay to avoid rate limits
                await asyncio.sleep(2)
                
                # Reply
                success = await self.reply_to_mention(mention, response)
                if success:
                    results["responded"] += 1
                else:
                    results["errors"] += 1
                    
            except Exception as e:
                logger.error(f"Error processing mention: {e}")
                results["errors"] += 1
        
        return results
    
    async def like_mention(self, mention: Mention) -> bool:
        """Like a mention as acknowledgment.
        
        Args:
            mention: The mention to like
            
        Returns:
            True if like was successful
        """
        if not self.client:
            return False
        
        try:
            self.client.like(tweet_id=int(mention.tweet_id))
            logger.info(f"Liked mention from @{mention.author_username}")
            return True
        except Exception as e:
            logger.debug(f"Could not like mention: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get monitoring statistics.
        
        Returns:
            Dictionary of stats
        """
        return {
            "mentions_processed": self.mentions_processed,
            "replies_sent": self.replies_sent,
            "errors": self.errors,
            "last_mention_id": self.last_mention_id,
            "processed_count": len(self.processed_mentions),
        }


# Singleton instance
_mention_monitor: Optional[MentionMonitor] = None


def get_mention_monitor(
    personality_engine: Optional[PapitoPersonalityEngine] = None
) -> MentionMonitor:
    """Get or create the singleton MentionMonitor instance.
    
    Args:
        personality_engine: Optional personality engine for AI responses
        
    Returns:
        MentionMonitor instance
    """
    global _mention_monitor
    if _mention_monitor is None:
        _mention_monitor = MentionMonitor(personality_engine=personality_engine)
    return _mention_monitor
