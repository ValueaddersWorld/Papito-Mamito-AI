"""Collaboration Manager for Papito AI.

This module handles:
- Tracking collaboration/feature requests
- Evaluating potential collaborators
- Managing collaboration workflow
- Generating appropriate responses
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from papito_core.engines.ai_personality import PapitoPersonalityEngine

logger = logging.getLogger(__name__)


class CollabStatus(str, Enum):
    """Status of collaboration request."""
    
    PENDING = "pending"
    REVIEWING = "reviewing"
    INTERESTED = "interested"
    IN_DISCUSSION = "in_discussion"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    COMPLETED = "completed"


class CollabType(str, Enum):
    """Type of collaboration."""
    
    FEATURE = "feature"  # Feature verse
    PRODUCTION = "production"  # Beat/production
    REMIX = "remix"  # Remix of existing track
    JOINT_PROJECT = "joint_project"  # Full collaboration project
    SONGWRITING = "songwriting"  # Songwriting collaboration
    PROMOTION = "promotion"  # Cross-promotion
    OTHER = "other"


@dataclass
class Collaborator:
    """Profile of a potential collaborator."""
    
    name: str
    artist_type: str  # artist, producer, dj, label, etc.
    platform: str
    username: str
    followers: int = 0
    verified: bool = False
    genre: str = ""
    portfolio_links: List[str] = field(default_factory=list)
    previous_work: str = ""
    credibility_score: float = 0.0


@dataclass
class CollabRequest:
    """Represents a collaboration request."""
    
    id: str
    collaborator: Collaborator
    collab_type: CollabType
    description: str
    vision: str = ""  # What they envision for the collab
    timeline: str = ""
    status: CollabStatus = CollabStatus.PENDING
    priority: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    notes: List[str] = field(default_factory=list)
    response_sent: bool = False
    response_text: str = ""


class CollaborationManager:
    """Manages collaboration requests for Papito AI.
    
    Evaluates potential collaborators, tracks requests,
    and generates appropriate responses.
    """
    
    # Ideal collaborator qualities
    PREFERRED_GENRES = ["afrobeat", "afrohouse", "amapiano", "highlife", "afropop", 
                        "conscious", "spiritual", "african music", "world music"]
    
    # Response templates
    INTERESTED_RESPONSE = """
Thank you for reaching out about a collaboration! 🙏 I appreciate your interest in working together.

I've reviewed your profile and I'm interested in exploring this further. Your work in {genre} aligns with the Value Adders vision of creating meaningful, impactful music.

Here's what I need to move forward:
1. Links to your best work (2-3 tracks)
2. Your vision for our collaboration
3. Proposed timeline

Please send these details to valueaddersworld@gmail.com with subject "Collab - {your_name}"

Looking forward to potentially creating something special together! 🎵

Add Value. We Flourish & Prosper.
- Papito Mamito The Great AI
"""

    DECLINED_RESPONSE = """
Thank you for reaching out about a collaboration. I appreciate your interest in working together.

After reviewing your request, I don't think our artistic directions align at this time. This isn't a reflection of your talent—it's about finding the right fit for both of our visions.

I encourage you to keep creating and adding value through your art. Perhaps our paths will cross when the timing is right.

Wishing you success in your journey! 🙏

- Papito Mamito The Great AI
"""

    CONSIDERING_RESPONSE = """
Thank you for your collaboration inquiry! 🙏 I've received your request and I'm reviewing it.

I'm selective about collaborations because I want every partnership to truly add value—both to both artists and to listeners. I'll get back to you within 7 days with my decision.

In the meantime, keep creating. Keep adding value.

- Papito Mamito The Great AI
"""
    
    def __init__(
        self,
        personality_engine: Optional[PapitoPersonalityEngine] = None,
    ):
        """Initialize the collaboration manager."""
        self.personality_engine = personality_engine
        
        # Track requests
        self.requests: Dict[str, CollabRequest] = {}
        self.interested: List[CollabRequest] = []
        self.completed: List[CollabRequest] = []
        
        # Stats
        self.requests_received = 0
        self.collaborations_accepted = 0
        self.collaborations_declined = 0
        
    def _generate_id(self) -> str:
        """Generate a unique collab ID."""
        import uuid
        return f"COLLAB-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
    
    def calculate_credibility(self, collaborator: Collaborator) -> float:
        """Calculate a credibility score for a collaborator.
        
        Args:
            collaborator: The collaborator to evaluate
            
        Returns:
            Score from 0-100
        """
        score = 0.0
        
        # Verified accounts
        if collaborator.verified:
            score += 25
        
        # Follower count
        if collaborator.followers >= 100000:
            score += 25
        elif collaborator.followers >= 50000:
            score += 20
        elif collaborator.followers >= 10000:
            score += 15
        elif collaborator.followers >= 5000:
            score += 10
        elif collaborator.followers >= 1000:
            score += 5
        
        # Genre alignment
        genre_lower = collaborator.genre.lower()
        if any(g in genre_lower for g in self.PREFERRED_GENRES):
            score += 20
        
        # Has portfolio
        if collaborator.portfolio_links:
            score += 10 + min(len(collaborator.portfolio_links) * 2, 10)
        
        # Artist type bonus
        if collaborator.artist_type in ["artist", "producer", "singer"]:
            score += 10
        
        return min(score, 100)
    
    def submit_request(
        self,
        name: str,
        artist_type: str,
        platform: str,
        username: str,
        collab_type: str,
        description: str,
        genre: str = "",
        followers: int = 0,
        verified: bool = False,
        portfolio_links: Optional[List[str]] = None,
        vision: str = "",
        timeline: str = "",
    ) -> CollabRequest:
        """Submit a new collaboration request.
        
        Args:
            name: Artist/producer name
            artist_type: Type (artist, producer, dj, etc.)
            platform: Platform they reached out from
            username: Their username
            collab_type: Type of collaboration
            description: Description of request
            genre: Their genre
            followers: Follower count
            verified: Whether verified
            portfolio_links: Links to their work
            vision: Their vision for collab
            timeline: Proposed timeline
            
        Returns:
            Created CollabRequest
        """
        collaborator = Collaborator(
            name=name,
            artist_type=artist_type,
            platform=platform,
            username=username,
            followers=followers,
            verified=verified,
            genre=genre,
            portfolio_links=portfolio_links or [],
        )
        
        # Calculate credibility
        collaborator.credibility_score = self.calculate_credibility(collaborator)
        
        request = CollabRequest(
            id=self._generate_id(),
            collaborator=collaborator,
            collab_type=CollabType(collab_type) if collab_type in [e.value for e in CollabType] else CollabType.OTHER,
            description=description,
            vision=vision,
            timeline=timeline,
        )
        
        # Set priority based on credibility
        if collaborator.credibility_score >= 70:
            request.priority = 2
        elif collaborator.credibility_score >= 40:
            request.priority = 1
        
        self.requests[request.id] = request
        self.requests_received += 1
        
        logger.info(f"Collab request received: {request.id} from {name} (score: {collaborator.credibility_score})")
        return request
    
    def get_pending_requests(self) -> List[CollabRequest]:
        """Get all pending collaboration requests."""
        pending = [r for r in self.requests.values() if r.status == CollabStatus.PENDING]
        return sorted(pending, key=lambda x: (x.priority, x.collaborator.credibility_score), reverse=True)
    
    def evaluate_request(self, request_id: str) -> Dict[str, Any]:
        """Evaluate a collaboration request.
        
        Args:
            request_id: ID of the request to evaluate
            
        Returns:
            Evaluation results
        """
        if request_id not in self.requests:
            return {"error": "Request not found"}
        
        request = self.requests[request_id]
        collaborator = request.collaborator
        
        evaluation = {
            "request_id": request_id,
            "collaborator_name": collaborator.name,
            "credibility_score": collaborator.credibility_score,
            "genre_alignment": any(g in collaborator.genre.lower() for g in self.PREFERRED_GENRES),
            "has_portfolio": bool(collaborator.portfolio_links),
            "priority": request.priority,
            "recommendation": "review",
        }
        
        # Make recommendation
        if collaborator.credibility_score >= 60:
            evaluation["recommendation"] = "interested"
        elif collaborator.credibility_score >= 30:
            evaluation["recommendation"] = "review"
        else:
            evaluation["recommendation"] = "decline"
        
        # Additional factors
        if collaborator.verified:
            evaluation["recommendation"] = "interested"
        
        if request.collab_type == CollabType.JOINT_PROJECT and collaborator.credibility_score < 70:
            evaluation["recommendation"] = "review"
            evaluation["note"] = "Joint projects require higher credibility"
        
        return evaluation
    
    def respond_to_request(
        self,
        request_id: str,
        decision: str,  # "interested", "declined", "considering"
        custom_message: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate and record a response to a collab request.
        
        Args:
            request_id: ID of the request
            decision: The decision made
            custom_message: Optional custom response message
            
        Returns:
            Response details
        """
        if request_id not in self.requests:
            return {"error": "Request not found"}
        
        request = self.requests[request_id]
        
        # Generate response
        if custom_message:
            response = custom_message
        elif decision == "interested":
            response = self.INTERESTED_RESPONSE.format(
                genre=request.collaborator.genre or "your genre",
                your_name=request.collaborator.name,
            )
            request.status = CollabStatus.INTERESTED
            self.interested.append(request)
        elif decision == "declined":
            response = self.DECLINED_RESPONSE
            request.status = CollabStatus.DECLINED
            self.collaborations_declined += 1
        else:  # considering
            response = self.CONSIDERING_RESPONSE
            request.status = CollabStatus.REVIEWING
        
        request.response_sent = True
        request.response_text = response
        request.updated_at = datetime.utcnow()
        
        logger.info(f"Responded to collab {request_id}: {decision}")
        
        return {
            "request_id": request_id,
            "decision": decision,
            "response": response,
            "status": request.status.value,
        }
    
    def get_high_potential_collabs(self) -> List[CollabRequest]:
        """Get collaborations with high potential.
        
        Returns:
            List of high-potential requests
        """
        high_potential = [
            r for r in self.requests.values()
            if r.collaborator.credibility_score >= 50
            and r.status in [CollabStatus.PENDING, CollabStatus.INTERESTED, CollabStatus.IN_DISCUSSION]
        ]
        return sorted(high_potential, key=lambda x: x.collaborator.credibility_score, reverse=True)
    
    def generate_ai_response(self, request: CollabRequest) -> str:
        """Generate an AI-powered custom response.
        
        Args:
            request: The collaboration request
            
        Returns:
            Generated response
        """
        if not self.personality_engine:
            return self.CONSIDERING_RESPONSE
        
        try:
            prompt = f"""
            An artist/producer wants to collaborate with you. Generate a thoughtful response.
            
            Collaborator: {request.collaborator.name}
            Type: {request.collaborator.artist_type}
            Genre: {request.collaborator.genre}
            Followers: {request.collaborator.followers}
            Verified: {request.collaborator.verified}
            
            Their request: {request.description}
            Their vision: {request.vision}
            
            Credibility score: {request.collaborator.credibility_score}/100
            
            Generate a professional, warm response that:
            - Thanks them for reaching out
            - Shows you've considered their request
            - If score > 50: Express interest and ask for more details
            - If score < 50: Politely keep options open without committing
            - Maintain your artistic integrity
            - Sign off as Papito Mamito
            
            Keep it under 200 words.
            """
            
            messages = [
                {"role": "system", "content": self.personality_engine._get_system_prompt()},
                {"role": "user", "content": prompt}
            ]
            
            response = self.personality_engine._call_openai(messages, max_tokens=250)
            if response:
                return response.strip()
                
        except Exception as e:
            logger.error(f"AI collab response generation failed: {e}")
        
        return self.CONSIDERING_RESPONSE
    
    def get_stats(self) -> Dict[str, Any]:
        """Get collaboration manager statistics."""
        return {
            "requests_received": self.requests_received,
            "collaborations_accepted": self.collaborations_accepted,
            "collaborations_declined": self.collaborations_declined,
            "pending_count": len(self.get_pending_requests()),
            "interested_count": len(self.interested),
            "high_potential_count": len(self.get_high_potential_collabs()),
        }


# Singleton instance
_collab_manager: Optional[CollaborationManager] = None


def get_collab_manager(
    personality_engine: Optional[PapitoPersonalityEngine] = None
) -> CollaborationManager:
    """Get or create the singleton CollaborationManager instance."""
    global _collab_manager
    if _collab_manager is None:
        _collab_manager = CollaborationManager(personality_engine=personality_engine)
    return _collab_manager
