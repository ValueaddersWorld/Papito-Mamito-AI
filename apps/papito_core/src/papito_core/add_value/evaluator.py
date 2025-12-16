"""
ADD VALUE Evaluator for Papito Mamito AI
=========================================
Quick evaluation functions that apply the ADD VALUE principles
to action decisions without needing full framework instantiation.

© 2025 Value Adders AI Technologies. All Rights Reserved.
A Value Adders World Company.
"""

from dataclasses import dataclass
from typing import Tuple, Optional


@dataclass
class ValueScore:
    """Result of a value evaluation"""
    should_act: bool
    score: float  # 0-100
    reasoning: str
    pillar_status: dict


def evaluate_action(
    situation: str,
    awareness: str,
    goal: str = "",
    plan: str = "",
    evidence: str = "",
) -> ValueScore:
    """
    Evaluate whether to take an action based on ADD VALUE pillars.
    
    Args:
        situation: The current situation/context
        awareness: What we know about the situation
        goal: The defined goal (Pillar 2)
        plan: The devised strategy (Pillar 3)
        evidence: Validation evidence (Pillar 4)
    
    Returns:
        ValueScore with recommendation
    """
    score = 0.0
    pillar_status = {
        "awareness": False,
        "define": False,
        "devise": False,
        "validate": False,
    }
    
    # Awareness (25 points)
    if awareness and len(awareness) >= 10:
        score += 25
        pillar_status["awareness"] = True
    
    # Define (25 points)
    if goal and len(goal) >= 5:
        score += 25
        pillar_status["define"] = True
    
    # Devise (25 points)
    if plan and len(plan) >= 10:
        score += 25
        pillar_status["devise"] = True
    
    # Validate (25 points)
    if evidence and len(evidence) >= 5:
        score += 25
        pillar_status["validate"] = True
    
    # Bonus for depth
    total_depth = len(awareness) + len(goal) + len(plan) + len(evidence)
    score += min(10, total_depth / 50)
    
    score = min(100, score)
    should_act = score >= 75 or (score >= 50 and all([
        pillar_status["awareness"],
        pillar_status["define"],
        pillar_status["devise"],
    ]))
    
    if score >= 90:
        reasoning = f"Excellent value foundation ({score:.0f}/100). Full confidence to act."
    elif score >= 75:
        reasoning = f"Strong value foundation ({score:.0f}/100). Ready to execute."
    elif score >= 50:
        reasoning = f"Moderate value ({score:.0f}/100). Consider strengthening validation."
    else:
        reasoning = f"Insufficient value foundation ({score:.0f}/100). Complete more pillars."
    
    return ValueScore(
        should_act=should_act,
        score=score,
        reasoning=reasoning,
        pillar_status=pillar_status,
    )


def should_act(
    awareness: str,
    goal: str,
    threshold: float = 50.0,
) -> bool:
    """
    Quick boolean check if action should be taken.
    
    Args:
        awareness: What we know
        goal: What we want to achieve
        threshold: Minimum score to act (default 50)
    
    Returns:
        True if should act, False otherwise
    """
    score = evaluate_action(
        situation="Quick check",
        awareness=awareness,
        goal=goal,
    )
    return score.score >= threshold
