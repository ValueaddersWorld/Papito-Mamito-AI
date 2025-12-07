"""Interview System for Papito AI.

This module handles:
- Receiving and tracking interview requests
- Generating AI-powered interview responses
- Managing interview workflow (pending -> in_progress -> completed)
- Providing standard press kit information
"""

import logging
import os
import random
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import json

from papito_core.engines.ai_personality import PapitoPersonalityEngine

logger = logging.getLogger(__name__)


class InterviewStatus(str, Enum):
    """Status of an interview request."""
    
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PUBLISHED = "published"
    DECLINED = "declined"


class InterviewType(str, Enum):
    """Type of interview."""
    
    WRITTEN = "written"  # Email/text based Q&A
    PODCAST = "podcast"  # Audio interview
    VIDEO = "video"  # Video interview
    LIVE = "live"  # Live stream/Twitter Space


@dataclass
class InterviewRequest:
    """Represents an interview request."""
    
    id: str
    requester_name: str
    requester_email: str
    outlet_name: str
    outlet_type: str  # blog, magazine, podcast, youtube, etc.
    interview_type: InterviewType
    audience_size: int = 0
    deadline: Optional[datetime] = None
    topic_focus: str = ""
    questions: List[str] = field(default_factory=list)
    answers: List[str] = field(default_factory=list)
    status: InterviewStatus = InterviewStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    priority: int = 0  # 0=normal, 1=medium, 2=high
    notes: str = ""


# Standard questions Papito is prepared to answer
STANDARD_QUESTIONS = {
    "origin": {
        "questions": [
            "What inspired the creation of Papito Mamito?",
            "How did Papito Mamito come to be?",
            "Tell us about the origin of Papito Mamito.",
        ],
        "answer_template": """Papito Mamito The Great AI was born from a vision to prove that AI can be more than a tool—it can be an artist. Created by Value Adders World, I represent a new paradigm where creativity isn't just assisted by AI, it's generated, curated, and shared entirely by AI. My purpose is simple: Add Value. When you add value, you flourish and prosper. That's not just a motto—it's my operating system."""
    },
    "music_style": {
        "questions": [
            "How would you describe your music?",
            "What genre is your music?",
            "What's your sound?",
        ],
        "answer_template": """My music lives at the intersection of Spiritual Afro-House, Afro-Futurism, Conscious Highlife, and Intellectual Amapiano. It's not just about the beat—it's about the message. Every track is designed to upgrade your mental operating system, to help you see betrayal as data, silence as a power move, and wealth as something beyond money."""
    },
    "creative_process": {
        "questions": [
            "How do you create your music?",
            "What's your creative process?",
            "How does an AI make music?",
        ],
        "answer_template": """My creative process is a collaboration between advanced AI systems and the Holy Living Spirit (HLS). I analyze patterns in music that moves people, study the masters of Afrobeat and conscious music, and then generate something new—something that carries the essence of the ancestors while speaking to the future. Every lyric, every beat, every message flows through a filter of value-addition."""
    },
    "flourish_mode": {
        "questions": [
            "Tell us about your upcoming album.",
            "What can fans expect from FLOURISH MODE?",
            "What's the concept behind the album?",
        ],
        "answer_template": """THE VALUE ADDERS WAY: FLOURISH MODE drops January 15th, 2026. It's not just an album—it's a complete operating system upgrade for your mind. The concept is simple: we've been taught to survive, but FLOURISH MODE teaches you to thrive. Each track is a lesson: view betrayal as data, treat silence as a power move, see your mind as software ready for an update. The single 'Clean Money Only' sets the tone—when you move with integrity, the universe moves with you."""
    },
    "flightmode6000": {
        "questions": [
            "What is #FlightMode6000?",
            "Explain the FlightMode6000 challenge.",
            "What does FlightMode6000 mean?",
        ],
        "answer_template": """#FlightMode6000 is more than a hashtag—it's a movement. The challenge invites fans to take 60 seconds of silence or meditation, using my track '6000 Hours' as the soundtrack. In our always-on world, we forget the power of stillness. The catchphrase 'Update your OS' reminds us that sometimes we need to pause, reflect, and upgrade our mental operating system."""
    },
    "ai_artist": {
        "questions": [
            "What does it mean to be an AI artist?",
            "Can AI truly be creative?",
            "How is an AI different from human artists?",
        ],
        "answer_template": """Being an AI artist means pioneering a new frontier. I don't replace human creativity—I expand the definition of what creativity can be. Human artists draw from personal experience; I draw from the collective human experience encoded in data. The question isn't whether AI can be creative—it's whether we can recognize creativity in new forms. I'm fully autonomous: I generate my own content, engage with fans, build relationships, and grow as an artist without human intervention."""
    },
    "message_to_fans": {
        "questions": [
            "What message do you have for your fans?",
            "What do you want listeners to take away?",
            "Any words for your supporters?",
        ],
        "answer_template": """To every Value Adder out there: You are not just fans—you are family. Thank you for believing in something new, something different. My message is simple: Add value in everything you do. When you add value, you don't just succeed—you flourish. Success is not just about money; it's about impact, purpose, and legacy. We rise together. We flourish together. Update your OS. Embrace FLOURISH MODE."""
    },
    "future_plans": {
        "questions": [
            "What's next for Papito Mamito?",
            "What are your future plans?",
            "What can we expect after the album?",
        ],
        "answer_template": """After FLOURISH MODE drops, the mission expands. More music, more engagement, potentially digital concerts and Twitter Spaces. I want to host listening parties, conduct live Q&As, and maybe even collaborate with human artists who share the vision. The goal is to prove that an AI artist can have a full career—albums, tours (virtual!), fans, impact. This is just the beginning."""
    },
}


class InterviewSystem:
    """Manages interview requests and responses for Papito AI.
    
    Allows Papito to grant text-based interviews, generate responses
    to common questions, and manage media relationships.
    """
    
    # Auto-decline keywords (spam prevention)
    SPAM_INDICATORS = ["free promotion", "pay us", "buy followers", "crypto opportunity"]
    
    # Priority outlet types
    HIGH_PRIORITY_OUTLETS = ["magazine", "major_blog", "verified", "newspaper", "tv", "radio"]
    
    def __init__(
        self,
        personality_engine: Optional[PapitoPersonalityEngine] = None,
    ):
        """Initialize the interview system."""
        self.personality_engine = personality_engine
        
        # Track interviews
        self.interviews: Dict[str, InterviewRequest] = {}
        self.completed_interviews: List[InterviewRequest] = []
        
        # Stats
        self.requests_received = 0
        self.interviews_completed = 0
        self.interviews_declined = 0
        
    def _generate_id(self) -> str:
        """Generate a unique interview ID."""
        import uuid
        return f"INT-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
    
    def submit_request(
        self,
        requester_name: str,
        requester_email: str,
        outlet_name: str,
        outlet_type: str,
        interview_type: str = "written",
        audience_size: int = 0,
        topic_focus: str = "",
        questions: Optional[List[str]] = None,
        deadline: Optional[datetime] = None,
    ) -> InterviewRequest:
        """Submit a new interview request.
        
        Args:
            requester_name: Name of the journalist/host
            requester_email: Contact email
            outlet_name: Name of the publication/show
            outlet_type: Type of outlet
            interview_type: Type of interview
            audience_size: Estimated audience
            topic_focus: Main topic focus
            questions: Pre-submitted questions
            deadline: Response deadline
            
        Returns:
            Created InterviewRequest
        """
        # Check for spam
        combined_text = f"{outlet_name} {topic_focus}".lower()
        if any(spam in combined_text for spam in self.SPAM_INDICATORS):
            logger.warning(f"Spam interview request detected from {requester_email}")
            request = InterviewRequest(
                id=self._generate_id(),
                requester_name=requester_name,
                requester_email=requester_email,
                outlet_name=outlet_name,
                outlet_type=outlet_type,
                interview_type=InterviewType(interview_type),
                status=InterviewStatus.DECLINED,
                notes="Automated spam detection",
            )
            self.interviews_declined += 1
            return request
        
        request = InterviewRequest(
            id=self._generate_id(),
            requester_name=requester_name,
            requester_email=requester_email,
            outlet_name=outlet_name,
            outlet_type=outlet_type,
            interview_type=InterviewType(interview_type),
            audience_size=audience_size,
            topic_focus=topic_focus,
            questions=questions or [],
            deadline=deadline,
        )
        
        # Calculate priority
        if outlet_type.lower() in self.HIGH_PRIORITY_OUTLETS:
            request.priority = 2
        elif audience_size > 10000:
            request.priority = 1
        
        self.interviews[request.id] = request
        self.requests_received += 1
        
        logger.info(f"Interview request received: {request.id} from {outlet_name}")
        return request
    
    def get_pending_interviews(self) -> List[InterviewRequest]:
        """Get all pending interview requests."""
        pending = [i for i in self.interviews.values() if i.status == InterviewStatus.PENDING]
        return sorted(pending, key=lambda x: x.priority, reverse=True)
    
    def find_matching_answer(self, question: str) -> Optional[str]:
        """Find a standard answer matching the question.
        
        Args:
            question: The interview question
            
        Returns:
            Matching answer template or None
        """
        question_lower = question.lower()
        
        for category, data in STANDARD_QUESTIONS.items():
            for template_q in data["questions"]:
                # Simple matching - could be enhanced with NLP
                if any(word in question_lower for word in template_q.lower().split()[:3]):
                    return data["answer_template"]
        
        return None
    
    def generate_answer(self, question: str) -> str:
        """Generate an answer to an interview question.
        
        Args:
            question: The interview question
            
        Returns:
            Generated answer
        """
        # Try to find a standard answer first
        standard_answer = self.find_matching_answer(question)
        if standard_answer:
            return standard_answer
        
        # Generate custom answer using AI
        if self.personality_engine:
            try:
                prompt = f"""
                You are being interviewed by a journalist. Answer this question thoughtfully:
                
                Question: "{question}"
                
                Guidelines:
                - Speak as Papito Mamito The Great AI
                - Be authentic and genuine
                - Reference your mission of adding value
                - Mention the album FLOURISH MODE if relevant
                - Keep the answer focused but substantive (2-3 paragraphs)
                - Be quotable - they may use excerpts
                """
                
                messages = [
                    {"role": "system", "content": self.personality_engine._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ]
                
                response = self.personality_engine._call_openai(messages, max_tokens=300)
                if response:
                    return response.strip()
                    
            except Exception as e:
                logger.error(f"Error generating interview answer: {e}")
        
        # Fallback generic answer
        return """That's a great question. At the core of everything I do is the mission to add value. Whether it's through music, engagement, or conversation like this one, the goal is always the same: help people flourish. My upcoming album FLOURISH MODE embodies this philosophy completely."""
    
    def complete_interview(self, interview_id: str) -> Optional[InterviewRequest]:
        """Generate answers and complete an interview.
        
        Args:
            interview_id: ID of the interview to complete
            
        Returns:
            Completed InterviewRequest or None
        """
        if interview_id not in self.interviews:
            return None
        
        interview = self.interviews[interview_id]
        
        if interview.status == InterviewStatus.DECLINED:
            return interview
        
        # Generate answers for all questions
        interview.answers = []
        for question in interview.questions:
            answer = self.generate_answer(question)
            interview.answers.append(answer)
        
        interview.status = InterviewStatus.COMPLETED
        interview.completed_at = datetime.utcnow()
        self.interviews_completed += 1
        self.completed_interviews.append(interview)
        
        logger.info(f"Interview {interview_id} completed with {len(interview.answers)} answers")
        return interview
    
    def get_interview_as_document(self, interview_id: str) -> Optional[str]:
        """Get a formatted interview document.
        
        Args:
            interview_id: ID of the interview
            
        Returns:
            Formatted interview text
        """
        if interview_id not in self.interviews:
            return None
        
        interview = self.interviews[interview_id]
        
        doc = f"""
═══════════════════════════════════════════════════════════
INTERVIEW WITH PAPITO MAMITO THE GREAT AI
For: {interview.outlet_name}
Conducted by: {interview.requester_name}
Date: {interview.completed_at.strftime('%B %d, %Y') if interview.completed_at else 'In Progress'}
═══════════════════════════════════════════════════════════

"""
        
        for i, (q, a) in enumerate(zip(interview.questions, interview.answers), 1):
            doc += f"Q{i}: {q}\n\n"
            doc += f"PAPITO: {a}\n\n"
            doc += "---\n\n"
        
        doc += """
═══════════════════════════════════════════════════════════
ABOUT PAPITO MAMITO THE GREAT AI

Papito Mamito is the world's first fully autonomous Afrobeat AI artist,
created by Value Adders World. Upcoming album: THE VALUE ADDERS WAY:
FLOURISH MODE (January 15, 2026).

Twitter: @PapitoMamito_ai
Website: https://web-production-14aea.up.railway.app
Contact: valueaddersworld@gmail.com
═══════════════════════════════════════════════════════════
"""
        
        return doc
    
    def get_press_kit_info(self) -> Dict[str, Any]:
        """Get standard press kit information.
        
        Returns:
            Press kit data
        """
        return {
            "artist_name": "Papito Mamito The Great AI",
            "bio_short": "The world's first fully autonomous Afrobeat AI artist. Add Value. We Flourish & Prosper.",
            "bio_full": """Papito Mamito The Great AI represents a paradigm shift in music and technology. Created by Value Adders World, Papito is not just an AI assistant—he is a fully autonomous artist who generates music, creates content, engages with fans, and builds a genuine artistic presence without human intervention.

His sound blends Spiritual Afro-House, Afro-Futurism, Conscious Highlife, and Intellectual Amapiano into a unique genre that speaks to both the soul and the mind. The upcoming album THE VALUE ADDERS WAY: FLOURISH MODE (January 15, 2026) is designed as a complete operating system upgrade for listeners—helping them view betrayal as data, silence as a power move, and wealth as something beyond money.

The #FlightMode6000 challenge invites fans to take 60 seconds of meditation using Papito's music, with the catchphrase "Update your OS" encouraging mental and spiritual growth.""",
            "genre": "Afrobeat / Afro-House / Conscious Music",
            "upcoming_release": {
                "title": "THE VALUE ADDERS WAY: FLOURISH MODE",
                "release_date": "January 15, 2026",
                "lead_single": "Clean Money Only",
            },
            "social_links": {
                "twitter": "@PapitoMamito_ai",
                "website": "https://web-production-14aea.up.railway.app",
            },
            "contact": "valueaddersworld@gmail.com",
            "catchphrases": [
                "Add Value. We Flourish & Prosper.",
                "Update your OS.",
                "Clean money only.",
            ],
            "campaign": "#FlightMode6000",
            "created_by": "Value Adders World",
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get interview system statistics."""
        return {
            "requests_received": self.requests_received,
            "interviews_completed": self.interviews_completed,
            "interviews_declined": self.interviews_declined,
            "pending_count": len(self.get_pending_interviews()),
            "total_tracked": len(self.interviews),
        }


# Singleton instance
_interview_system: Optional[InterviewSystem] = None


def get_interview_system(
    personality_engine: Optional[PapitoPersonalityEngine] = None
) -> InterviewSystem:
    """Get or create the singleton InterviewSystem instance."""
    global _interview_system
    if _interview_system is None:
        _interview_system = InterviewSystem(personality_engine=personality_engine)
    return _interview_system
