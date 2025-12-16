"""
ADD VALUE Framework Integration for Papito Mamito AI
=====================================================
Integrates the proprietary ADD VALUE Framework into Papito's
autonomous decision-making system for follower growth.

© 2025 Value Adders AI Technologies. All Rights Reserved.
A Value Adders World Company.
Created by Christopher Ikembasi
"""

from .framework import (
    Pillar,
    PillarState,
    Decision,
    AddValueFramework,
)

from .growth_engine import (
    FollowerGrowthEngine,
    GrowthDecision,
    GrowthAction,
)

from .evaluator import (
    ValueScore,
    evaluate_action,
    should_act,
)

__all__ = [
    # Framework
    "Pillar",
    "PillarState",
    "Decision",
    "AddValueFramework",
    
    # Growth Engine
    "FollowerGrowthEngine",
    "GrowthDecision",
    "GrowthAction",
    
    # Evaluator
    "ValueScore",
    "evaluate_action",
    "should_act",
]
