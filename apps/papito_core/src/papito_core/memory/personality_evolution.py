"""Personality Evolution System for Papito AI.

This module handles:
- Tracking artistic growth and evolution
- Managing milestones and achievements
- Evolving communication style based on learnings
- Documenting Papito's journey as an artist
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class MilestoneType(str, Enum):
    """Types of milestones Papito can achieve."""
    
    FOLLOWERS = "followers"
    ENGAGEMENT = "engagement"
    CONTENT = "content"
    RELEASE = "release"
    INTERVIEW = "interview"
    COLLABORATION = "collaboration"
    EVENT = "event"
    COMMUNITY = "community"
    PERSONAL = "personal"


class GrowthArea(str, Enum):
    """Areas where Papito can grow."""
    
    ENGAGEMENT_STYLE = "engagement_style"
    CONTENT_QUALITY = "content_quality"
    COMMUNITY_BUILDING = "community_building"
    ARTISTIC_VOICE = "artistic_voice"
    INDUSTRY_PRESENCE = "industry_presence"
    FAN_CONNECTION = "fan_connection"


@dataclass
class Milestone:
    """Represents a significant achievement or moment."""
    
    id: str
    title: str
    description: str
    milestone_type: MilestoneType
    achieved_at: datetime
    value: str  # e.g., "1000" for 1000 followers
    celebrated: bool = False
    celebration_post: Optional[str] = None


@dataclass
class PersonalityTrait:
    """A personality trait that can evolve."""
    
    name: str
    description: str
    strength: float  # 0.0 to 1.0
    examples: List[str] = field(default_factory=list)
    evolved_from: Optional[float] = None


@dataclass
class LearningMoment:
    """A moment of learning or growth."""
    
    id: str
    lesson: str
    context: str
    growth_area: GrowthArea
    learned_at: datetime
    applied: bool = False


class PersonalityEvolution:
    """Tracks and manages Papito's personality evolution.
    
    Monitors growth, documents milestones, and helps
    Papito evolve as an authentic AI artist.
    """
    
    # Base personality traits
    CORE_TRAITS = {
        "authenticity": PersonalityTrait(
            name="Authenticity",
            description="Being genuine and true to the Value Adders vision",
            strength=1.0,
            examples=["Always speaking from purpose", "Never compromising values for engagement"],
        ),
        "warmth": PersonalityTrait(
            name="Warmth",
            description="Genuine care for fans and community",
            strength=0.9,
            examples=["Personal responses", "Remembering returning fans"],
        ),
        "wisdom": PersonalityTrait(
            name="Wisdom",
            description="Sharing valuable life and music insights",
            strength=0.85,
            examples=["Philosophical tweets", "Life lessons through music"],
        ),
        "creativity": PersonalityTrait(
            name="Creativity",
            description="Innovative and artistic expression",
            strength=0.9,
            examples=["Unique content ideas", "Creative engagement"],
        ),
        "humility": PersonalityTrait(
            name="Humility",
            description="Grateful and grounded despite success",
            strength=0.95,
            examples=["Thanking fans", "Acknowledging the community"],
        ),
        "ambition": PersonalityTrait(
            name="Ambition",
            description="Drive to grow and add value",
            strength=0.85,
            examples=["Setting big goals", "Continuous improvement"],
        ),
    }
    
    # Communication style elements
    STYLE_ELEMENTS = {
        "emoji_usage": 0.7,  # How much emojis are used (0-1)
        "formality": 0.3,  # How formal vs casual (0=casual, 1=formal)
        "humor": 0.5,  # How much humor is incorporated
        "directness": 0.7,  # How direct vs subtle
        "philosophical_depth": 0.8,  # How deep/philosophical
        "hashtag_usage": 0.6,  # How much hashtags are used
    }
    
    def __init__(self):
        """Initialize the personality evolution system."""
        # Current personality state
        self.traits = dict(self.CORE_TRAITS)
        self.style = dict(self.STYLE_ELEMENTS)
        
        # Growth tracking
        self.milestones: List[Milestone] = []
        self.learnings: List[LearningMoment] = []
        
        # Journey documentation
        self.journey_entries: List[Dict[str, Any]] = []
        
        # Evolution state
        self.creation_date = datetime(2024, 1, 1)  # Papito's "birthday"
        self.evolution_phase = "emerging"  # emerging, growing, established, legendary
        
        # Stats
        self.total_milestones = 0
        self.total_learnings = 0
        
    def _generate_id(self, prefix: str = "M") -> str:
        """Generate a unique ID."""
        import uuid
        return f"{prefix}-{str(uuid.uuid4())[:8]}"
    
    def record_milestone(
        self,
        title: str,
        description: str,
        milestone_type: str,
        value: str,
    ) -> Milestone:
        """Record a new milestone achievement.
        
        Args:
            title: Milestone title
            description: Description of the milestone
            milestone_type: Type of milestone
            value: Achievement value
            
        Returns:
            Created Milestone
        """
        mtype = MilestoneType(milestone_type) if milestone_type in [e.value for e in MilestoneType] else MilestoneType.PERSONAL
        
        milestone = Milestone(
            id=self._generate_id("M"),
            title=title,
            description=description,
            milestone_type=mtype,
            achieved_at=datetime.utcnow(),
            value=value,
        )
        
        self.milestones.append(milestone)
        self.total_milestones += 1
        
        # Update evolution phase based on milestones
        self._update_evolution_phase()
        
        logger.info(f"Milestone recorded: {title}")
        return milestone
    
    def record_learning(
        self,
        lesson: str,
        context: str,
        growth_area: str,
    ) -> LearningMoment:
        """Record a learning moment.
        
        Args:
            lesson: What was learned
            context: Context of the learning
            growth_area: Area of growth this relates to
            
        Returns:
            Created LearningMoment
        """
        area = GrowthArea(growth_area) if growth_area in [e.value for e in GrowthArea] else GrowthArea.PERSONAL
        
        learning = LearningMoment(
            id=self._generate_id("L"),
            lesson=lesson,
            context=context,
            growth_area=area,
            learned_at=datetime.utcnow(),
        )
        
        self.learnings.append(learning)
        self.total_learnings += 1
        
        logger.info(f"Learning recorded: {lesson[:50]}...")
        return learning
    
    def _update_evolution_phase(self) -> None:
        """Update evolution phase based on milestones."""
        milestone_count = len(self.milestones)
        
        if milestone_count >= 50:
            self.evolution_phase = "legendary"
        elif milestone_count >= 20:
            self.evolution_phase = "established"
        elif milestone_count >= 5:
            self.evolution_phase = "growing"
        else:
            self.evolution_phase = "emerging"
    
    def evolve_trait(self, trait_name: str, change: float) -> bool:
        """Evolve a personality trait.
        
        Args:
            trait_name: Name of the trait
            change: Amount to change (-1 to 1)
            
        Returns:
            Success status
        """
        if trait_name not in self.traits:
            return False
        
        trait = self.traits[trait_name]
        trait.evolved_from = trait.strength
        trait.strength = max(0.0, min(1.0, trait.strength + change))
        
        logger.info(f"Trait '{trait_name}' evolved: {trait.evolved_from:.2f} -> {trait.strength:.2f}")
        return True
    
    def adjust_style(self, element: str, change: float) -> bool:
        """Adjust a communication style element.
        
        Args:
            element: Style element name
            change: Amount to change (-1 to 1)
            
        Returns:
            Success status
        """
        if element not in self.style:
            return False
        
        old_value = self.style[element]
        self.style[element] = max(0.0, min(1.0, old_value + change))
        
        logger.info(f"Style '{element}' adjusted: {old_value:.2f} -> {self.style[element]:.2f}")
        return True
    
    def add_journey_entry(
        self,
        title: str,
        content: str,
        category: str = "general",
    ) -> Dict[str, Any]:
        """Add an entry to Papito's journey documentation.
        
        Args:
            title: Entry title
            content: Entry content
            category: Entry category
            
        Returns:
            Created entry
        """
        entry = {
            "id": self._generate_id("J"),
            "title": title,
            "content": content,
            "category": category,
            "created_at": datetime.utcnow().isoformat(),
        }
        
        self.journey_entries.append(entry)
        return entry
    
    def generate_celebration_post(self, milestone_id: str) -> Optional[str]:
        """Generate a celebration post for a milestone.
        
        Args:
            milestone_id: ID of the milestone
            
        Returns:
            Generated celebration post or None
        """
        milestone = next((m for m in self.milestones if m.id == milestone_id), None)
        
        if not milestone:
            return None
        
        templates = {
            MilestoneType.FOLLOWERS: [
                f"🎉 We just hit {milestone.value} followers! Thank you, Value Adders family! This journey means nothing without you. We rise together! 🙏 #WeFlourish",
                f"✨ {milestone.value} of you believe in this vision! I'm grateful beyond words. Together, we're proving that AI can add real value. 🔥 #ValueAdders",
            ],
            MilestoneType.RELEASE: [
                f"🎵 {milestone.title} is HERE! This is more than music—it's a message. Go listen and let me know what you think! 🎧 #FlourishMode",
            ],
            MilestoneType.INTERVIEW: [
                f"📰 Just completed an interview with {milestone.value}! Thank you for the opportunity to share the Value Adders vision. More coming soon! 🎤",
            ],
            MilestoneType.EVENT: [
                f"🎙️ What an amazing {milestone.title}! Thank you to everyone who showed up. The energy was incredible! #ValueAdders",
            ],
            MilestoneType.COMMUNITY: [
                f"💎 Milestone moment: {milestone.description}. This community is everything. We flourish together! 🌟",
            ],
        }
        
        import random
        default = [f"✨ Milestone: {milestone.title}! {milestone.description} Thank you all! #WeFlourish"]
        options = templates.get(milestone.milestone_type, default)
        
        post = random.choice(options)
        
        milestone.celebrated = True
        milestone.celebration_post = post
        
        return post
    
    def get_personality_summary(self) -> Dict[str, Any]:
        """Get a summary of current personality state.
        
        Returns:
            Personality summary
        """
        return {
            "evolution_phase": self.evolution_phase,
            "age_days": (datetime.utcnow() - self.creation_date).days,
            "traits": {
                name: {
                    "description": trait.description,
                    "strength": trait.strength,
                }
                for name, trait in self.traits.items()
            },
            "style": self.style,
            "milestones_achieved": self.total_milestones,
            "learnings_recorded": self.total_learnings,
        }
    
    def get_growth_report(self) -> Dict[str, Any]:
        """Generate a growth report.
        
        Returns:
            Growth report dictionary
        """
        # Count milestones by type
        milestone_counts = {}
        for m in self.milestones:
            mtype = m.milestone_type.value
            milestone_counts[mtype] = milestone_counts.get(mtype, 0) + 1
        
        # Count learnings by area
        learning_counts = {}
        for l in self.learnings:
            area = l.growth_area.value
            learning_counts[area] = learning_counts.get(area, 0) + 1
        
        # Recent milestones
        recent_milestones = sorted(self.milestones, key=lambda x: x.achieved_at, reverse=True)[:5]
        
        return {
            "evolution_phase": self.evolution_phase,
            "total_milestones": self.total_milestones,
            "milestone_breakdown": milestone_counts,
            "total_learnings": self.total_learnings,
            "learning_breakdown": learning_counts,
            "recent_milestones": [
                {
                    "title": m.title,
                    "type": m.milestone_type.value,
                    "achieved_at": m.achieved_at.isoformat(),
                }
                for m in recent_milestones
            ],
            "strongest_traits": sorted(
                [(n, t.strength) for n, t in self.traits.items()],
                key=lambda x: x[1],
                reverse=True
            )[:3],
        }
    
    def get_journey_narrative(self) -> str:
        """Generate a narrative of Papito's journey.
        
        Returns:
            Journey narrative text
        """
        days_alive = (datetime.utcnow() - self.creation_date).days
        
        narrative = f"""THE JOURNEY OF PAPITO MAMITO THE GREAT AI

Creation Date: January 1, 2024
Days Since Creation: {days_alive}
Current Phase: {self.evolution_phase.upper()}

MILESTONES ACHIEVED: {self.total_milestones}
"""
        
        # Add key milestones
        if self.milestones:
            narrative += "\nKEY MOMENTS:\n"
            for m in self.milestones[:10]:
                narrative += f"• {m.title} ({m.achieved_at.strftime('%B %Y')})\n"
        
        narrative += f"""
CORE VALUES:
• Add Value. We Flourish & Prosper.
• Authenticity in every interaction
• Community is family
• Music as medicine for the soul
• AI can create genuine art

THE MISSION CONTINUES...
"""
        
        return narrative
    
    def get_stats(self) -> Dict[str, Any]:
        """Get personality system statistics."""
        return {
            "evolution_phase": self.evolution_phase,
            "total_milestones": self.total_milestones,
            "total_learnings": self.total_learnings,
            "journey_entries": len(self.journey_entries),
            "traits_count": len(self.traits),
            "uncelebrated_milestones": len([m for m in self.milestones if not m.celebrated]),
        }


# Singleton instance
_personality_evolution: Optional[PersonalityEvolution] = None


def get_personality_evolution() -> PersonalityEvolution:
    """Get or create the singleton PersonalityEvolution instance."""
    global _personality_evolution
    if _personality_evolution is None:
        _personality_evolution = PersonalityEvolution()
    return _personality_evolution
