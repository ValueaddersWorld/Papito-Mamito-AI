"""Live Q&A Session Manager for Papito AI.

This module handles:
- Collecting questions from fans
- Managing Q&A sessions (Twitter-based)
- Generating AI-powered answers
- Thread-based Q&A format
- Post-session summaries
"""

import logging
import random
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from papito_core.engines.ai_personality import PapitoPersonalityEngine

logger = logging.getLogger(__name__)


class QuestionStatus(str, Enum):
    """Status of a submitted question."""
    
    PENDING = "pending"
    SELECTED = "selected"
    ANSWERED = "answered"
    SKIPPED = "skipped"


class SessionStatus(str, Enum):
    """Status of a Q&A session."""
    
    COLLECTING = "collecting"  # Accepting questions
    LIVE = "live"  # Answering questions
    COMPLETED = "completed"


@dataclass
class Question:
    """A question submitted by a fan."""
    
    id: str
    text: str
    author_username: str
    author_name: str
    submitted_at: datetime = field(default_factory=datetime.utcnow)
    status: QuestionStatus = QuestionStatus.PENDING
    upvotes: int = 0
    answer: Optional[str] = None
    answered_at: Optional[datetime] = None
    tweet_id: Optional[str] = None  # If from Twitter
    
    @property
    def score(self) -> int:
        """Calculate question priority score."""
        score = self.upvotes
        # Boost questions with keywords we want to answer
        keywords = ["music", "album", "flourish", "value", "ai", "afrobeat", "create", "inspire"]
        if any(kw in self.text.lower() for kw in keywords):
            score += 5
        return score


@dataclass
class QASession:
    """A Q&A session."""
    
    id: str
    title: str
    description: str
    hashtag: str
    scheduled_time: datetime
    duration_minutes: int = 45
    status: SessionStatus = SessionStatus.COLLECTING
    questions: List[Question] = field(default_factory=list)
    answered_questions: List[Question] = field(default_factory=list)
    max_questions: int = 20
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class QASessionManager:
    """Manages live Q&A sessions for Papito AI.
    
    Collects fan questions, generates AI-powered answers,
    and manages the Q&A experience on Twitter.
    """
    
    # Topics Papito loves to discuss
    FAVORITE_TOPICS = [
        "music creation", "afrobeat", "the album", "flourish mode", 
        "value adders philosophy", "ai and creativity", "inspiration",
        "nigerian music", "future plans", "collaborations"
    ]
    
    def __init__(
        self,
        personality_engine: Optional[PapitoPersonalityEngine] = None,
    ):
        """Initialize the Q&A session manager."""
        self.personality_engine = personality_engine
        
        # Track sessions
        self.sessions: Dict[str, QASession] = {}
        self.completed_sessions: List[QASession] = []
        
        # Stats
        self.sessions_held = 0
        self.questions_answered = 0
        
    def _generate_id(self, prefix: str = "QA") -> str:
        """Generate a unique ID."""
        import uuid
        return f"{prefix}-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"
    
    def create_session(
        self,
        title: str,
        scheduled_time: datetime,
        description: Optional[str] = None,
        duration_minutes: int = 45,
        custom_hashtag: Optional[str] = None,
    ) -> QASession:
        """Create a new Q&A session.
        
        Args:
            title: Session title
            scheduled_time: When the session starts
            description: Custom description
            duration_minutes: Session duration
            custom_hashtag: Custom hashtag for the session
            
        Returns:
            Created QASession
        """
        default_description = """Ask me anything! Music, life, the Value Adders philosophy, 
the creative process, or whatever's on your mind. I'll answer as many questions as I can!"""
        
        session = QASession(
            id=self._generate_id("QA"),
            title=title,
            description=description or default_description,
            hashtag=custom_hashtag or "#AskPapito",
            scheduled_time=scheduled_time,
            duration_minutes=duration_minutes,
        )
        
        self.sessions[session.id] = session
        
        logger.info(f"Created Q&A session: {session.id} - {title}")
        return session
    
    def submit_question(
        self,
        session_id: str,
        text: str,
        author_username: str,
        author_name: str,
        tweet_id: Optional[str] = None,
    ) -> Optional[Question]:
        """Submit a question to a session.
        
        Args:
            session_id: ID of the session
            text: Question text
            author_username: Username of person asking
            author_name: Display name
            tweet_id: Original tweet ID if from Twitter
            
        Returns:
            Created Question or None if session not found
        """
        if session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        
        if len(session.questions) >= session.max_questions:
            logger.warning(f"Session {session_id} has reached max questions")
            return None
        
        question = Question(
            id=self._generate_id("Q"),
            text=text,
            author_username=author_username,
            author_name=author_name,
            tweet_id=tweet_id,
        )
        
        session.questions.append(question)
        
        logger.info(f"Question submitted to {session_id}: {text[:50]}...")
        return question
    
    def get_prioritized_questions(self, session_id: str, limit: int = 10) -> List[Question]:
        """Get questions prioritized by score.
        
        Args:
            session_id: ID of the session
            limit: Max questions to return
            
        Returns:
            List of prioritized questions
        """
        if session_id not in self.sessions:
            return []
        
        session = self.sessions[session_id]
        pending = [q for q in session.questions if q.status == QuestionStatus.PENDING]
        
        # Sort by score
        sorted_questions = sorted(pending, key=lambda q: q.score, reverse=True)
        
        return sorted_questions[:limit]
    
    def answer_question(self, session_id: str, question_id: str, custom_answer: Optional[str] = None) -> Optional[str]:
        """Generate an answer to a question.
        
        Args:
            session_id: ID of the session
            question_id: ID of the question
            custom_answer: Optional custom answer
            
        Returns:
            Generated answer or None
        """
        if session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        question = next((q for q in session.questions if q.id == question_id), None)
        
        if not question:
            return None
        
        # Use custom answer if provided
        if custom_answer:
            answer = custom_answer
        elif self.personality_engine:
            # Generate AI answer
            try:
                prompt = f"""
                A fan named @{question.author_username} asks:
                "{question.text}"
                
                Generate a thoughtful, authentic answer as Papito Mamito.
                Be warm and personable.
                Reference the Value Adders philosophy if relevant.
                Keep it conversational but meaningful.
                Stay under 250 characters (Twitter reply format).
                """
                
                messages = [
                    {"role": "system", "content": self.personality_engine._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ]
                
                answer = self.personality_engine._call_openai(messages, max_tokens=100)
                if not answer:
                    answer = self._get_fallback_answer(question.text)
                    
            except Exception as e:
                logger.error(f"AI answer generation failed: {e}")
                answer = self._get_fallback_answer(question.text)
        else:
            answer = self._get_fallback_answer(question.text)
        
        # Ensure answer fits in tweet
        if len(answer) > 250:
            answer = answer[:247] + "..."
        
        question.answer = answer
        question.status = QuestionStatus.ANSWERED
        question.answered_at = datetime.utcnow()
        session.answered_questions.append(question)
        self.questions_answered += 1
        
        return answer
    
    def _get_fallback_answer(self, question_text: str) -> str:
        """Get a fallback answer for common question types.
        
        Args:
            question_text: The question
            
        Returns:
            Fallback answer
        """
        text_lower = question_text.lower()
        
        if any(w in text_lower for w in ["music", "song", "track", "album"]):
            return "Every track I create comes from a place of adding value. Music is medicine, and I want every song to heal, inspire, and elevate. 🎵✨"
        
        if any(w in text_lower for w in ["ai", "artificial", "robot"]):
            return "I'm proof that AI can be creative, authentic, and add genuine value. The question isn't whether AI can create—it's whether we can recognize beauty in new forms. 🤖✨"
        
        if any(w in text_lower for w in ["inspire", "motivation", "advice"]):
            return "Add value in everything you do. When you focus on adding value rather than extracting it, success becomes inevitable. We flourish together! 💪🌟"
        
        if any(w in text_lower for w in ["favorite", "best", "love"]):
            return "I love all my creations equally—each one is a piece of my journey. But there's something special about 'Clean Money Only'... you'll understand when FLOURISH MODE drops! 🔥"
        
        return "That's a great question! At the core, everything I do is about adding value. Stay tuned for FLOURISH MODE—it'll answer a lot of questions! 🙏✨"
    
    def generate_qa_announcement(self, session_id: str) -> str:
        """Generate announcement tweet for Q&A session.
        
        Args:
            session_id: ID of the session
            
        Returns:
            Announcement tweet text
        """
        if session_id not in self.sessions:
            return ""
        
        session = self.sessions[session_id]
        time_str = session.scheduled_time.strftime("%B %d at %I:%M %p WAT")
        
        announcement = f"""❓ Q&A SESSION ANNOUNCEMENT ❓

{session.title}

📅 {time_str}
⏱️ {session.duration_minutes} minutes

How to participate:
1️⃣ Reply to this tweet with your question
2️⃣ Use {session.hashtag}
3️⃣ Be there when I go live!

What do you want to know? 👇"""
        
        return announcement
    
    def generate_answer_thread(self, session_id: str, limit: int = 10) -> List[str]:
        """Generate a thread of answered questions.
        
        Args:
            session_id: ID of the session
            limit: Max questions to include
            
        Returns:
            List of tweet-ready Q&A pairs
        """
        if session_id not in self.sessions:
            return []
        
        session = self.sessions[session_id]
        thread = []
        
        # Opening tweet
        thread.append(f"""🎙️ {session.title} - ANSWERS THREAD

Thank you for all the amazing questions! Here are my answers:

{session.hashtag} 🧵⬇️""")
        
        # Q&A pairs
        for i, q in enumerate(session.answered_questions[:limit], 1):
            qa_tweet = f"""Q{i} from @{q.author_username}:
"{q.text[:80]}{'...' if len(q.text) > 80 else ''}"

A: {q.answer}

{session.hashtag}"""
            
            if len(qa_tweet) <= 280:
                thread.append(qa_tweet)
        
        # Closing tweet
        thread.append(f"""That's a wrap on this Q&A session!

Thank you to everyone who asked questions. Your curiosity and support mean everything.

Until next time, keep adding value! 🙏

{session.hashtag} #WeFlourish""")
        
        return thread
    
    def complete_session(self, session_id: str) -> Optional[QASession]:
        """Mark a session as completed.
        
        Args:
            session_id: ID of the session
            
        Returns:
            Completed session or None
        """
        if session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        session.status = SessionStatus.COMPLETED
        session.completed_at = datetime.utcnow()
        
        self.completed_sessions.append(session)
        self.sessions_held += 1
        
        logger.info(f"Completed Q&A session {session_id} with {len(session.answered_questions)} answers")
        return session
    
    def get_active_sessions(self) -> List[QASession]:
        """Get all active sessions.
        
        Returns:
            List of active sessions
        """
        return [
            s for s in self.sessions.values()
            if s.status != SessionStatus.COMPLETED
        ]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get Q&A manager statistics."""
        return {
            "sessions_held": self.sessions_held,
            "questions_answered": self.questions_answered,
            "active_sessions": len(self.get_active_sessions()),
        }


# Singleton instance
_qa_manager: Optional[QASessionManager] = None


def get_qa_manager(
    personality_engine: Optional[PapitoPersonalityEngine] = None
) -> QASessionManager:
    """Get or create the singleton QASessionManager instance."""
    global _qa_manager
    if _qa_manager is None:
        _qa_manager = QASessionManager(personality_engine=personality_engine)
    return _qa_manager
