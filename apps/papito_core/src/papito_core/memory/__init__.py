"""Memory Module for Papito AI.

This module provides intelligent memory systems including:
- Interaction memory (user relationships)
- Content learning (what works)
- Personality evolution (artistic growth)
"""

from .interaction_memory import (
    InteractionMemory,
    Interaction,
    UserMemory,
    InteractionType,
    Sentiment,
    get_interaction_memory,
)

from .content_learning import (
    ContentLearner,
    ContentPerformance,
    ContentInsight,
    ContentType,
    TimeSlot,
    get_content_learner,
)

from .personality_evolution import (
    PersonalityEvolution,
    Milestone,
    MilestoneType,
    PersonalityTrait,
    LearningMoment,
    GrowthArea,
    get_personality_evolution,
)

__all__ = [
    # Interaction Memory
    "InteractionMemory",
    "Interaction",
    "UserMemory",
    "InteractionType",
    "Sentiment",
    "get_interaction_memory",
    # Content Learning
    "ContentLearner",
    "ContentPerformance",
    "ContentInsight",
    "ContentType",
    "TimeSlot",
    "get_content_learner",
    # Personality Evolution
    "PersonalityEvolution",
    "Milestone",
    "MilestoneType",
    "PersonalityTrait",
    "LearningMoment",
    "GrowthArea",
    "get_personality_evolution",
]
