"""Interaction Memory System for Papito AI.

This module handles:
- Storing interaction history with users
- Tracking conversation context
- Remembering user preferences and topics discussed
- Providing context for future interactions
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional
import json

logger = logging.getLogger(__name__)


class InteractionType(str, Enum):
    """Types of interactions Papito has."""
    
    MENTION = "mention"
    REPLY = "reply"
    DM = "dm"
    LIKE = "like"
    RETWEET = "retweet"
    QUOTE = "quote"
    FOLLOW = "follow"
    INTERVIEW = "interview"
    COLLAB = "collab"
    QA = "qa"


class Sentiment(str, Enum):
    """Sentiment of an interaction."""
    
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


@dataclass
class Interaction:
    """Represents a single interaction with a user."""
    
    id: str
    user_id: str
    username: str
    interaction_type: InteractionType
    content: str
    sentiment: Sentiment = Sentiment.NEUTRAL
    topics: List[str] = field(default_factory=list)
    responded: bool = False
    response: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UserMemory:
    """Memory of interactions with a specific user."""
    
    user_id: str
    username: str
    display_name: str
    first_interaction: datetime
    last_interaction: datetime
    interaction_count: int = 0
    interactions: List[Interaction] = field(default_factory=list)
    topics_discussed: Dict[str, int] = field(default_factory=dict)  # topic -> count
    sentiment_history: List[Sentiment] = field(default_factory=list)
    is_fan: bool = False
    is_notable: bool = False
    is_collaborator: bool = False
    notes: str = ""
    tags: List[str] = field(default_factory=list)
    
    @property
    def average_sentiment(self) -> str:
        """Calculate average sentiment from history."""
        if not self.sentiment_history:
            return "neutral"
        
        positive = sum(1 for s in self.sentiment_history if s == Sentiment.POSITIVE)
        negative = sum(1 for s in self.sentiment_history if s == Sentiment.NEGATIVE)
        
        if positive > negative * 2:
            return "very_positive"
        elif positive > negative:
            return "positive"
        elif negative > positive:
            return "negative"
        return "neutral"
    
    @property
    def relationship_strength(self) -> int:
        """Calculate relationship strength (0-100)."""
        score = min(self.interaction_count * 5, 50)  # Up to 50 from interactions
        
        # Bonus for positive sentiment
        if self.average_sentiment == "very_positive":
            score += 30
        elif self.average_sentiment == "positive":
            score += 15
        
        # Bonus for recent interactions
        days_since_last = (datetime.utcnow() - self.last_interaction).days
        if days_since_last < 7:
            score += 20
        elif days_since_last < 30:
            score += 10
        
        return min(score, 100)
    
    @property
    def top_topics(self) -> List[str]:
        """Get top discussed topics."""
        sorted_topics = sorted(
            self.topics_discussed.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return [t[0] for t in sorted_topics[:5]]


class InteractionMemory:
    """Manages memory of all interactions for Papito AI.
    
    Stores and retrieves interaction history, enabling
    personalized and context-aware responses.
    """
    
    # Topics Papito might discuss
    TOPIC_KEYWORDS = {
        "music": ["music", "song", "track", "album", "beat", "lyrics", "melody"],
        "afrobeat": ["afrobeat", "afro", "nigerian", "african music", "highlife"],
        "flourish_mode": ["flourish", "album", "flourish mode", "value adders way"],
        "ai": ["ai", "artificial", "robot", "machine", "technology"],
        "philosophy": ["value", "purpose", "meaning", "life", "success"],
        "collaboration": ["collab", "feature", "work together", "project"],
        "support": ["support", "fan", "love", "appreciate", "thank"],
        "creative": ["create", "inspire", "art", "creative", "vision"],
    }
    
    def __init__(self, max_interactions_per_user: int = 100):
        """Initialize the interaction memory.
        
        Args:
            max_interactions_per_user: Max interactions to store per user
        """
        self.max_interactions_per_user = max_interactions_per_user
        
        # Memory storage
        self.users: Dict[str, UserMemory] = {}  # user_id -> UserMemory
        self.recent_interactions: List[Interaction] = []
        
        # Stats
        self.total_interactions = 0
        self.unique_users = 0
        
    def _generate_id(self) -> str:
        """Generate a unique interaction ID."""
        import uuid
        return f"INT-{str(uuid.uuid4())[:12]}"
    
    def _extract_topics(self, content: str) -> List[str]:
        """Extract topics from content.
        
        Args:
            content: Text content to analyze
            
        Returns:
            List of identified topics
        """
        content_lower = content.lower()
        topics = []
        
        for topic, keywords in self.TOPIC_KEYWORDS.items():
            if any(kw in content_lower for kw in keywords):
                topics.append(topic)
        
        return topics
    
    def _analyze_sentiment(self, content: str) -> Sentiment:
        """Simple sentiment analysis.
        
        Args:
            content: Text to analyze
            
        Returns:
            Detected sentiment
        """
        content_lower = content.lower()
        
        positive_words = ["love", "amazing", "great", "awesome", "fire", "🔥", "❤️", 
                         "beautiful", "blessed", "thank", "appreciate", "incredible",
                         "best", "favorite", "goat", "legend", "inspired"]
        negative_words = ["hate", "trash", "terrible", "worst", "bad", "sucks",
                         "boring", "disappointed", "fake", "fraud"]
        
        positive_count = sum(1 for w in positive_words if w in content_lower)
        negative_count = sum(1 for w in negative_words if w in content_lower)
        
        if positive_count > negative_count:
            return Sentiment.POSITIVE
        elif negative_count > positive_count:
            return Sentiment.NEGATIVE
        return Sentiment.NEUTRAL
    
    def record_interaction(
        self,
        user_id: str,
        username: str,
        display_name: str,
        interaction_type: str,
        content: str,
        responded: bool = False,
        response: Optional[str] = None,
        is_notable: bool = False,
        metadata: Optional[Dict] = None,
    ) -> Interaction:
        """Record a new interaction.
        
        Args:
            user_id: User's ID
            username: User's username
            display_name: User's display name
            interaction_type: Type of interaction
            content: Content of the interaction
            responded: Whether Papito responded
            response: Papito's response if any
            is_notable: Whether user is notable
            metadata: Additional metadata
            
        Returns:
            Created Interaction
        """
        # Get or create user memory
        if user_id not in self.users:
            self.users[user_id] = UserMemory(
                user_id=user_id,
                username=username,
                display_name=display_name,
                first_interaction=datetime.utcnow(),
                last_interaction=datetime.utcnow(),
            )
            self.unique_users += 1
        
        user_memory = self.users[user_id]
        
        # Analyze content
        topics = self._extract_topics(content)
        sentiment = self._analyze_sentiment(content)
        
        # Create interaction
        interaction = Interaction(
            id=self._generate_id(),
            user_id=user_id,
            username=username,
            interaction_type=InteractionType(interaction_type) if interaction_type in [e.value for e in InteractionType] else InteractionType.MENTION,
            content=content,
            sentiment=sentiment,
            topics=topics,
            responded=responded,
            response=response,
            metadata=metadata or {},
        )
        
        # Update user memory
        user_memory.last_interaction = datetime.utcnow()
        user_memory.interaction_count += 1
        user_memory.interactions.append(interaction)
        user_memory.sentiment_history.append(sentiment)
        
        # Update topics discussed
        for topic in topics:
            user_memory.topics_discussed[topic] = user_memory.topics_discussed.get(topic, 0) + 1
        
        # Flag as notable if specified
        if is_notable:
            user_memory.is_notable = True
        
        # Trim old interactions if needed
        if len(user_memory.interactions) > self.max_interactions_per_user:
            user_memory.interactions = user_memory.interactions[-self.max_interactions_per_user:]
        
        # Add to recent interactions
        self.recent_interactions.append(interaction)
        if len(self.recent_interactions) > 1000:
            self.recent_interactions = self.recent_interactions[-500:]
        
        self.total_interactions += 1
        
        logger.info(f"Recorded interaction from @{username}: {interaction_type}")
        return interaction
    
    def get_user_context(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get context about a user for personalized responses.
        
        Args:
            user_id: User's ID
            
        Returns:
            Context dictionary or None if user not found
        """
        if user_id not in self.users:
            return None
        
        user = self.users[user_id]
        
        # Get recent interactions summary
        recent = user.interactions[-5:] if user.interactions else []
        recent_summary = [
            {
                "type": i.interaction_type.value,
                "content_preview": i.content[:100],
                "sentiment": i.sentiment.value,
                "date": i.timestamp.strftime("%Y-%m-%d"),
            }
            for i in recent
        ]
        
        return {
            "user_id": user_id,
            "username": user.username,
            "display_name": user.display_name,
            "interaction_count": user.interaction_count,
            "first_interaction": user.first_interaction.isoformat(),
            "last_interaction": user.last_interaction.isoformat(),
            "relationship_strength": user.relationship_strength,
            "average_sentiment": user.average_sentiment,
            "top_topics": user.top_topics,
            "is_fan": user.is_fan,
            "is_notable": user.is_notable,
            "is_collaborator": user.is_collaborator,
            "recent_interactions": recent_summary,
            "notes": user.notes,
            "tags": user.tags,
        }
    
    def get_personalization_prompt(self, user_id: str) -> str:
        """Generate a personalization prompt for AI responses.
        
        Args:
            user_id: User's ID
            
        Returns:
            Personalization text for AI prompt
        """
        context = self.get_user_context(user_id)
        
        if not context:
            return "This is a new user you haven't interacted with before. Be welcoming!"
        
        prompt_parts = []
        
        # Relationship status
        if context["interaction_count"] > 10:
            prompt_parts.append(f"This is a loyal supporter who has interacted {context['interaction_count']} times.")
        elif context["interaction_count"] > 3:
            prompt_parts.append("This is a returning supporter.")
        else:
            prompt_parts.append("This user has interacted a few times before.")
        
        # Sentiment
        if context["average_sentiment"] == "very_positive":
            prompt_parts.append("They're very positive about your music!")
        elif context["average_sentiment"] == "positive":
            prompt_parts.append("They've been supportive in past interactions.")
        
        # Topics
        if context["top_topics"]:
            prompt_parts.append(f"You've discussed: {', '.join(context['top_topics'][:3])}.")
        
        # Notable status
        if context["is_notable"]:
            prompt_parts.append("This is a notable account - give extra attention!")
        if context["is_collaborator"]:
            prompt_parts.append("This is a potential collaborator.")
        
        # Notes
        if context["notes"]:
            prompt_parts.append(f"Notes: {context['notes']}")
        
        return " ".join(prompt_parts)
    
    def mark_as_fan(self, user_id: str) -> bool:
        """Mark a user as a fan.
        
        Args:
            user_id: User's ID
            
        Returns:
            Success status
        """
        if user_id in self.users:
            self.users[user_id].is_fan = True
            return True
        return False
    
    def mark_as_collaborator(self, user_id: str) -> bool:
        """Mark a user as a potential collaborator.
        
        Args:
            user_id: User's ID
            
        Returns:
            Success status
        """
        if user_id in self.users:
            self.users[user_id].is_collaborator = True
            return True
        return False
    
    def add_note(self, user_id: str, note: str) -> bool:
        """Add a note about a user.
        
        Args:
            user_id: User's ID
            note: Note to add
            
        Returns:
            Success status
        """
        if user_id in self.users:
            self.users[user_id].notes = note
            return True
        return False
    
    def add_tag(self, user_id: str, tag: str) -> bool:
        """Add a tag to a user.
        
        Args:
            user_id: User's ID
            tag: Tag to add
            
        Returns:
            Success status
        """
        if user_id in self.users:
            if tag not in self.users[user_id].tags:
                self.users[user_id].tags.append(tag)
            return True
        return False
    
    def get_fans(self, limit: int = 20) -> List[UserMemory]:
        """Get users marked as fans.
        
        Args:
            limit: Max fans to return
            
        Returns:
            List of fan UserMemory objects
        """
        fans = [u for u in self.users.values() if u.is_fan]
        return sorted(fans, key=lambda x: x.relationship_strength, reverse=True)[:limit]
    
    def get_recent_users(self, hours: int = 24, limit: int = 50) -> List[UserMemory]:
        """Get users who interacted recently.
        
        Args:
            hours: Hours to look back
            limit: Max users to return
            
        Returns:
            List of recent UserMemory objects
        """
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        recent = [u for u in self.users.values() if u.last_interaction > cutoff]
        return sorted(recent, key=lambda x: x.last_interaction, reverse=True)[:limit]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get memory system statistics."""
        return {
            "total_interactions": self.total_interactions,
            "unique_users": self.unique_users,
            "fans_count": len([u for u in self.users.values() if u.is_fan]),
            "notable_count": len([u for u in self.users.values() if u.is_notable]),
            "collaborators_count": len([u for u in self.users.values() if u.is_collaborator]),
            "recent_interactions": len(self.recent_interactions),
        }


# Singleton instance
_interaction_memory: Optional[InteractionMemory] = None


def get_interaction_memory() -> InteractionMemory:
    """Get or create the singleton InteractionMemory instance."""
    global _interaction_memory
    if _interaction_memory is None:
        _interaction_memory = InteractionMemory()
    return _interaction_memory
