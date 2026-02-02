"""
PAPITO MAMITO AI - ACTION GATE
==============================
Middleware that gates all outbound actions through ADD VALUE scoring.

Every action Papito takes must pass through this gate:
    
    Action Request → [ACTION GATE] → Pass/Block Decision
                          │
                    ┌─────┴─────┐
                    │  Value    │
                    │  Score    │
                    │  Check    │
                    └─────┬─────┘
                          │
               ┌──────────┴──────────┐
               │                     │
         Score >= Threshold    Score < Threshold
               │                     │
               ▼                     ▼
          [EXECUTE]            [BLOCK + LOG]
                                     │
                                     ▼
                              [LEARN FROM IT]

© 2026 Value Adders World - Entertainment Division
"Add value or don't act."
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, List, Optional

from .value_score import (
    ValueScoreCalculator,
    ActionValueScore,
    ActionType,
    get_value_calculator,
)

logger = logging.getLogger("papito.intelligence.gate")


class GateDecision(str, Enum):
    """Possible decisions from the action gate."""
    PASS = "pass"           # Action approved, execute it
    BLOCK = "block"         # Action blocked, don't execute
    DEFER = "defer"         # Action deferred for review
    ESCALATE = "escalate"   # Escalate to higher authority


@dataclass
class GateResult:
    """Result from the action gate evaluation."""
    decision: GateDecision
    action_id: str
    action_type: ActionType
    content: str
    
    # Score details
    value_score: ActionValueScore
    
    # Decision details
    reason: str = ""
    blocked_pillars: List[str] = field(default_factory=list)
    improvement_suggestions: List[str] = field(default_factory=list)
    
    # Timing
    evaluated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    evaluation_time_ms: int = 0
    
    # If deferred/escalated
    defer_reason: str = ""
    escalate_to: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/storage."""
        return {
            "decision": self.decision.value,
            "action_id": self.action_id,
            "action_type": self.action_type.value,
            "content": self.content[:100] + "..." if len(self.content) > 100 else self.content,
            "value_score": self.value_score.total_score,
            "threshold": self.value_score.threshold,
            "reason": self.reason,
            "blocked_pillars": self.blocked_pillars,
            "improvement_suggestions": self.improvement_suggestions,
            "evaluated_at": self.evaluated_at.isoformat(),
            "evaluation_time_ms": self.evaluation_time_ms,
        }


# Callback type for gated actions
ActionCallback = Callable[[str, ActionType, Dict[str, Any]], Awaitable[Any]]


class ActionGate:
    """
    The gate through which all Papito actions must pass.
    
    This is the enforcement layer of "Add value or don't act."
    Every outbound action is scored and only passes if it meets
    the value threshold.
    
    Features:
    - Automatic value scoring of all actions
    - Configurable thresholds by action type
    - Improvement suggestions for blocked actions
    - Learning integration for continuous improvement
    - Override capability for special cases
    - Audit trail of all decisions
    
    Usage:
        gate = ActionGate()
        
        # Method 1: Check before acting
        result = await gate.evaluate(
            action_type=ActionType.REPLY,
            content="Great vibes! 🔥",
            context={"user": "@fan123"}
        )
        
        if result.decision == GateDecision.PASS:
            # Execute the action
        else:
            # Handle blocked action
            print(result.improvement_suggestions)
        
        # Method 2: Gated execution
        result = await gate.execute_if_passes(
            action_type=ActionType.REPLY,
            content="Great vibes! 🔥",
            context={"user": "@fan123"},
            executor=my_reply_function,
        )
    """
    
    # Actions that can bypass the gate with override
    OVERRIDABLE_ACTIONS = {
        ActionType.LIKE,      # Low impact
        ActionType.RETWEET,   # Low impact
    }
    
    # Actions that require extra scrutiny
    HIGH_SCRUTINY_ACTIONS = {
        ActionType.DM,
        ActionType.COLLAB_REQUEST,
        ActionType.SHOUTOUT,
    }
    
    def __init__(
        self,
        calculator: ValueScoreCalculator = None,
        default_threshold: float = 70.0,
        enable_learning: bool = True,
        max_history: int = 1000,
    ):
        """Initialize the action gate.
        
        Args:
            calculator: ValueScoreCalculator instance (uses global if None)
            default_threshold: Default score threshold
            enable_learning: Whether to feed blocked actions to learner
            max_history: Maximum decisions to keep in history
        """
        self.calculator = calculator or get_value_calculator()
        self.default_threshold = default_threshold
        self.enable_learning = enable_learning
        self.max_history = max_history
        
        self._history: List[GateResult] = []
        self._overrides: Dict[str, bool] = {}  # action_id -> override
        
        # Stats
        self._total_evaluated = 0
        self._passed = 0
        self._blocked = 0
        self._deferred = 0
        self._overridden = 0
        
        # Learner reference (set later)
        self._learner = None
        
        logger.info("ActionGate initialized")
    
    def set_learner(self, learner) -> None:
        """Set the action learner for feedback loop.
        
        Args:
            learner: ActionLearner instance
        """
        self._learner = learner
        logger.info("ActionGate connected to learner")
    
    async def evaluate(
        self,
        action_type: ActionType,
        content: str,
        context: Dict[str, Any] = None,
        action_id: str = None,
    ) -> GateResult:
        """
        Evaluate an action through the gate.
        
        Args:
            action_type: Type of action
            content: Action content
            context: Additional context
            action_id: Unique action ID (auto-generated if None)
            
        Returns:
            GateResult with decision and details
        """
        import time
        
        start_time = time.time()
        self._total_evaluated += 1
        
        action_id = action_id or str(uuid.uuid4())[:12]
        context = context or {}
        
        # Calculate value score
        value_score = await self.calculator.calculate(
            action_type=action_type,
            content=content,
            context=context,
            action_id=action_id,
        )
        
        # Determine decision
        decision, reason = self._make_decision(action_type, value_score, context)
        
        # Get improvement suggestions for blocked actions
        suggestions = []
        blocked_pillars = []
        
        if decision == GateDecision.BLOCK:
            suggestions = self._get_improvement_suggestions(value_score)
            blocked_pillars = [p.value for p in value_score.weak_pillars]
            self._blocked += 1
        elif decision == GateDecision.PASS:
            self._passed += 1
        elif decision == GateDecision.DEFER:
            self._deferred += 1
        
        # Create result
        result = GateResult(
            decision=decision,
            action_id=action_id,
            action_type=action_type,
            content=content,
            value_score=value_score,
            reason=reason,
            blocked_pillars=blocked_pillars,
            improvement_suggestions=suggestions,
            evaluation_time_ms=int((time.time() - start_time) * 1000),
        )
        
        # Add to history
        self._add_to_history(result)
        
        # Send to learner if blocked
        if self.enable_learning and decision == GateDecision.BLOCK and self._learner:
            await self._learner.record_blocked_action(result)
        
        logger.info(
            f"Gate decision for {action_type.value}: {decision.value} "
            f"(score={value_score.total_score:.1f}, threshold={value_score.threshold})"
        )
        
        return result
    
    def _make_decision(
        self,
        action_type: ActionType,
        value_score: ActionValueScore,
        context: Dict[str, Any],
    ) -> tuple[GateDecision, str]:
        """Make the gate decision based on score and context.
        
        Returns:
            Tuple of (decision, reason)
        """
        # Check for override
        if context.get("override") and action_type in self.OVERRIDABLE_ACTIONS:
            self._overridden += 1
            return GateDecision.PASS, "Override approved for low-impact action"
        
        # Check for escalation requirement
        if action_type in self.HIGH_SCRUTINY_ACTIONS and value_score.total_score < 80:
            if value_score.total_score >= 60:
                return GateDecision.DEFER, "High-scrutiny action needs review"
        
        # Standard decision based on score
        if value_score.should_execute:
            return GateDecision.PASS, f"Value score {value_score.total_score:.1f} meets threshold {value_score.threshold}"
        else:
            weak = [p.value for p in value_score.weak_pillars]
            return GateDecision.BLOCK, f"Value score {value_score.total_score:.1f} below threshold. Weak pillars: {weak}"
    
    def _get_improvement_suggestions(self, score: ActionValueScore) -> List[str]:
        """Generate improvement suggestions for a blocked action.
        
        Args:
            score: The action's value score
            
        Returns:
            List of actionable suggestions
        """
        suggestions = []
        
        weak_pillars = score.weak_pillars
        
        for pillar in weak_pillars:
            if pillar.value == "A":  # Awareness
                suggestions.append("Add more context about the user or situation")
            elif pillar.value == "D1":  # Define
                suggestions.append("Clarify the goal or purpose of this action")
            elif pillar.value == "D2":  # Devise
                suggestions.append("Improve the content quality or approach")
            elif pillar.value == "V":  # Validate
                suggestions.append("Verify the user is genuine and context is appropriate")
            elif pillar.value == "A2":  # Act Upon
                suggestions.append("Check if all prerequisites for action are met")
            elif pillar.value == "L":  # Learn
                suggestions.append("Consider past interactions with similar actions")
            elif pillar.value == "U":  # Understand
                suggestions.append("Better understand the user's intent or pattern")
            elif pillar.value == "E":  # Evolve
                suggestions.append("Consider how this action helps build relationships")
        
        # General suggestions based on score
        if score.total_score < 40:
            suggestions.append("This action needs significant improvement across multiple pillars")
        elif score.total_score < 60:
            suggestions.append("Consider waiting for more context before acting")
        
        return suggestions
    
    def _add_to_history(self, result: GateResult) -> None:
        """Add result to history, maintaining max size."""
        self._history.append(result)
        if len(self._history) > self.max_history:
            self._history = self._history[-self.max_history:]
    
    async def execute_if_passes(
        self,
        action_type: ActionType,
        content: str,
        context: Dict[str, Any],
        executor: ActionCallback,
    ) -> tuple[GateResult, Any]:
        """
        Evaluate action and execute if it passes.
        
        Args:
            action_type: Type of action
            content: Action content
            context: Additional context
            executor: Async function to execute the action
            
        Returns:
            Tuple of (GateResult, executor result or None)
        """
        result = await self.evaluate(action_type, content, context)
        
        if result.decision == GateDecision.PASS:
            try:
                execution_result = await executor(content, action_type, context)
                
                # Record successful execution with learner
                if self.enable_learning and self._learner:
                    await self._learner.record_executed_action(result, execution_result)
                
                return result, execution_result
                
            except Exception as e:
                logger.exception(f"Action execution failed: {e}")
                
                # Record failure with learner
                if self.enable_learning and self._learner:
                    await self._learner.record_failed_action(result, str(e))
                
                raise
        
        return result, None
    
    def add_override(self, action_id: str) -> None:
        """Add an override for a specific action ID.
        
        Args:
            action_id: The action ID to override
        """
        self._overrides[action_id] = True
        logger.info(f"Override added for action {action_id}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get gate statistics."""
        total = self._passed + self._blocked + self._deferred
        return {
            "total_evaluated": self._total_evaluated,
            "passed": self._passed,
            "blocked": self._blocked,
            "deferred": self._deferred,
            "overridden": self._overridden,
            "pass_rate": self._passed / total if total > 0 else 0,
            "block_rate": self._blocked / total if total > 0 else 0,
            "history_size": len(self._history),
        }
    
    def get_recent_decisions(
        self,
        limit: int = 20,
        decision_type: GateDecision = None,
    ) -> List[Dict[str, Any]]:
        """Get recent gate decisions.
        
        Args:
            limit: Maximum results to return
            decision_type: Filter by decision type
            
        Returns:
            List of decision dictionaries
        """
        results = self._history
        
        if decision_type:
            results = [r for r in results if r.decision == decision_type]
        
        return [r.to_dict() for r in results[-limit:]]
    
    def get_blocked_summary(self) -> Dict[str, Any]:
        """Get summary of blocked actions.
        
        Returns:
            Summary with common block reasons and suggestions
        """
        blocked = [r for r in self._history if r.decision == GateDecision.BLOCK]
        
        if not blocked:
            return {"count": 0, "common_weak_pillars": [], "common_suggestions": []}
        
        # Count weak pillars
        pillar_counts: Dict[str, int] = {}
        for result in blocked:
            for pillar in result.blocked_pillars:
                pillar_counts[pillar] = pillar_counts.get(pillar, 0) + 1
        
        # Sort by frequency
        sorted_pillars = sorted(pillar_counts.items(), key=lambda x: x[1], reverse=True)
        
        # Get unique suggestions
        all_suggestions = []
        for result in blocked:
            all_suggestions.extend(result.improvement_suggestions)
        unique_suggestions = list(set(all_suggestions))[:5]
        
        return {
            "count": len(blocked),
            "common_weak_pillars": sorted_pillars[:5],
            "common_suggestions": unique_suggestions,
            "average_score": sum(r.value_score.total_score for r in blocked) / len(blocked),
        }


# Global gate instance
_gate: ActionGate | None = None


def get_action_gate() -> ActionGate:
    """Get the global action gate instance."""
    global _gate
    if _gate is None:
        _gate = ActionGate()
    return _gate
