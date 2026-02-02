"""
PAPITO MAMITO AI - ACTION LEARNING
==================================
Learn from blocked and executed actions to continuously improve.

The feedback loop:
    
    Action Executed/Blocked
            │
            ▼
    ┌───────────────────┐
    │   ACTION LEARNER  │
    │   - Record        │
    │   - Analyze       │
    │   - Extract       │
    │   - Apply         │
    └─────────┬─────────┘
              │
    ┌─────────┴─────────┐
    │                   │
    ▼                   ▼
[Patterns DB]     [Insights]
                        │
                        ▼
              [Improve Future Scoring]

© 2026 Value Adders World - Entertainment Division
"Add value or don't act."
"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from .value_score import ActionType, ActionValueScore, PillarID

logger = logging.getLogger("papito.intelligence.learning")


class ActionOutcome(str, Enum):
    """Outcomes of actions for learning."""
    EXECUTED_SUCCESS = "executed_success"    # Action executed, positive result
    EXECUTED_NEUTRAL = "executed_neutral"    # Action executed, neutral result
    EXECUTED_FAILURE = "executed_failure"    # Action executed, negative result
    BLOCKED = "blocked"                       # Action was blocked by gate
    DEFERRED = "deferred"                     # Action was deferred
    ERROR = "error"                           # Technical error during execution


@dataclass
class ActionRecord:
    """Record of an action for learning."""
    action_id: str
    action_type: ActionType
    content: str
    outcome: ActionOutcome
    
    # Scores
    value_score: float
    pillar_scores: Dict[str, float]
    threshold: float
    
    # Context
    context: Dict[str, Any] = field(default_factory=dict)
    
    # Outcome details
    outcome_details: str = ""
    engagement_result: Dict[str, Any] = field(default_factory=dict)  # likes, replies, etc.
    
    # Timing
    recorded_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "action_id": self.action_id,
            "action_type": self.action_type.value,
            "content": self.content[:200],
            "outcome": self.outcome.value,
            "value_score": self.value_score,
            "pillar_scores": self.pillar_scores,
            "threshold": self.threshold,
            "context": self.context,
            "outcome_details": self.outcome_details,
            "engagement_result": self.engagement_result,
            "recorded_at": self.recorded_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ActionRecord":
        """Create from dictionary."""
        return cls(
            action_id=data["action_id"],
            action_type=ActionType(data["action_type"]),
            content=data["content"],
            outcome=ActionOutcome(data["outcome"]),
            value_score=data["value_score"],
            pillar_scores=data["pillar_scores"],
            threshold=data["threshold"],
            context=data.get("context", {}),
            outcome_details=data.get("outcome_details", ""),
            engagement_result=data.get("engagement_result", {}),
            recorded_at=datetime.fromisoformat(data["recorded_at"]) if data.get("recorded_at") else datetime.now(timezone.utc),
        )


@dataclass
class LearningInsight:
    """An insight extracted from learning."""
    insight_id: str
    insight_type: str  # "threshold_adjustment", "pillar_weight", "content_pattern", etc.
    description: str
    
    # The insight
    recommendation: str
    confidence: float  # 0-1
    evidence_count: int
    
    # Impact
    affected_action_types: List[ActionType] = field(default_factory=list)
    affected_pillars: List[PillarID] = field(default_factory=list)
    
    # Suggested changes
    suggested_threshold_delta: float = 0.0
    suggested_weight_changes: Dict[str, float] = field(default_factory=dict)
    
    # Metadata
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    applied: bool = False
    applied_at: datetime | None = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "insight_id": self.insight_id,
            "insight_type": self.insight_type,
            "description": self.description,
            "recommendation": self.recommendation,
            "confidence": self.confidence,
            "evidence_count": self.evidence_count,
            "affected_action_types": [a.value for a in self.affected_action_types],
            "affected_pillars": [p.value for p in self.affected_pillars],
            "suggested_threshold_delta": self.suggested_threshold_delta,
            "suggested_weight_changes": self.suggested_weight_changes,
            "generated_at": self.generated_at.isoformat(),
            "applied": self.applied,
        }


class ActionLearner:
    """
    Learns from action outcomes to improve future scoring.
    
    This creates a feedback loop where Papito continuously improves
    his value scoring based on real outcomes:
    
    - Blocked actions that would have been good → Lower threshold
    - Passed actions that performed poorly → Raise threshold
    - Patterns in weak pillars → Adjust weights
    - Content patterns that work → Learn from them
    
    Features:
    - Records all action outcomes
    - Analyzes patterns in blocked vs successful actions
    - Generates insights for threshold/weight adjustments
    - Tracks engagement metrics for executed actions
    - Persists learning data to disk
    
    Usage:
        learner = ActionLearner()
        
        # Record outcomes
        await learner.record_blocked_action(gate_result)
        await learner.record_executed_action(gate_result, engagement_result)
        
        # Analyze and get insights
        insights = await learner.analyze()
        
        # Apply insights
        for insight in insights:
            if insight.confidence > 0.8:
                learner.apply_insight(insight)
    """
    
    def __init__(
        self,
        data_dir: str | Path = None,
        max_records: int = 10000,
        analysis_window_days: int = 7,
    ):
        """Initialize the action learner.
        
        Args:
            data_dir: Directory for persistent storage
            max_records: Maximum records to keep
            analysis_window_days: Days of data to analyze
        """
        self.data_dir = Path(data_dir) if data_dir else Path(__file__).parent.parent.parent.parent.parent / "data" / "learning"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.max_records = max_records
        self.analysis_window_days = analysis_window_days
        
        self._records: List[ActionRecord] = []
        self._insights: List[LearningInsight] = []
        
        # Stats by action type
        self._stats_by_type: Dict[str, Dict[str, int]] = {}
        
        # Pattern tracking
        self._content_patterns: Dict[str, List[float]] = {}  # pattern -> engagement scores
        self._pillar_performance: Dict[str, List[tuple[float, str]]] = {}  # pillar -> (score, outcome)
        
        # Load existing data
        self._load_data()
        
        logger.info(f"ActionLearner initialized with {len(self._records)} existing records")
    
    def _load_data(self) -> None:
        """Load persisted learning data."""
        records_file = self.data_dir / "action_records.json"
        insights_file = self.data_dir / "insights.json"
        
        if records_file.exists():
            try:
                with open(records_file, "r") as f:
                    data = json.load(f)
                    self._records = [ActionRecord.from_dict(r) for r in data]
            except Exception as e:
                logger.error(f"Error loading records: {e}")
        
        if insights_file.exists():
            try:
                with open(insights_file, "r") as f:
                    self._insights = json.load(f)
            except Exception as e:
                logger.error(f"Error loading insights: {e}")
    
    def _save_data(self) -> None:
        """Persist learning data to disk."""
        records_file = self.data_dir / "action_records.json"
        insights_file = self.data_dir / "insights.json"
        
        try:
            with open(records_file, "w") as f:
                json.dump([r.to_dict() for r in self._records[-self.max_records:]], f, indent=2)
        except Exception as e:
            logger.error(f"Error saving records: {e}")
        
        try:
            with open(insights_file, "w") as f:
                json.dump([i.to_dict() for i in self._insights], f, indent=2)
        except Exception as e:
            logger.error(f"Error saving insights: {e}")
    
    async def record_blocked_action(self, gate_result) -> None:
        """Record a blocked action for learning.
        
        Args:
            gate_result: GateResult from the action gate
        """
        record = ActionRecord(
            action_id=gate_result.action_id,
            action_type=gate_result.action_type,
            content=gate_result.content,
            outcome=ActionOutcome.BLOCKED,
            value_score=gate_result.value_score.total_score,
            pillar_scores=gate_result.value_score.pillar_summary,
            threshold=gate_result.value_score.threshold,
            context=gate_result.value_score.context,
            outcome_details=gate_result.reason,
        )
        
        self._add_record(record)
        self._update_stats(record)
        
        logger.debug(f"Recorded blocked action: {gate_result.action_id}")
    
    async def record_executed_action(
        self,
        gate_result,
        execution_result: Any = None,
    ) -> None:
        """Record an executed action for learning.
        
        Args:
            gate_result: GateResult from the action gate
            execution_result: Result from the action execution
        """
        # Determine outcome based on execution result
        outcome = ActionOutcome.EXECUTED_SUCCESS
        engagement = {}
        
        if execution_result:
            # Try to extract engagement metrics
            if isinstance(execution_result, dict):
                engagement = execution_result.get("engagement", {})
                
                # Determine success based on engagement
                likes = engagement.get("likes", 0)
                replies = engagement.get("replies", 0)
                
                if likes + replies > 0:
                    outcome = ActionOutcome.EXECUTED_SUCCESS
                else:
                    outcome = ActionOutcome.EXECUTED_NEUTRAL
        
        record = ActionRecord(
            action_id=gate_result.action_id,
            action_type=gate_result.action_type,
            content=gate_result.content,
            outcome=outcome,
            value_score=gate_result.value_score.total_score,
            pillar_scores=gate_result.value_score.pillar_summary,
            threshold=gate_result.value_score.threshold,
            context=gate_result.value_score.context,
            outcome_details="Executed successfully",
            engagement_result=engagement,
        )
        
        self._add_record(record)
        self._update_stats(record)
        self._track_content_pattern(record)
        
        logger.debug(f"Recorded executed action: {gate_result.action_id}")
    
    async def record_failed_action(
        self,
        gate_result,
        error: str,
    ) -> None:
        """Record a failed action execution.
        
        Args:
            gate_result: GateResult from the action gate
            error: Error message
        """
        record = ActionRecord(
            action_id=gate_result.action_id,
            action_type=gate_result.action_type,
            content=gate_result.content,
            outcome=ActionOutcome.ERROR,
            value_score=gate_result.value_score.total_score,
            pillar_scores=gate_result.value_score.pillar_summary,
            threshold=gate_result.value_score.threshold,
            context=gate_result.value_score.context,
            outcome_details=f"Error: {error}",
        )
        
        self._add_record(record)
        self._update_stats(record)
        
        logger.debug(f"Recorded failed action: {gate_result.action_id}")
    
    def _add_record(self, record: ActionRecord) -> None:
        """Add a record and maintain max size."""
        self._records.append(record)
        
        if len(self._records) > self.max_records:
            self._records = self._records[-self.max_records:]
        
        # Periodically save (every 100 records)
        if len(self._records) % 100 == 0:
            self._save_data()
    
    def _update_stats(self, record: ActionRecord) -> None:
        """Update statistics for an action type."""
        action_key = record.action_type.value
        
        if action_key not in self._stats_by_type:
            self._stats_by_type[action_key] = {
                "total": 0,
                "blocked": 0,
                "success": 0,
                "neutral": 0,
                "failure": 0,
                "error": 0,
            }
        
        stats = self._stats_by_type[action_key]
        stats["total"] += 1
        
        if record.outcome == ActionOutcome.BLOCKED:
            stats["blocked"] += 1
        elif record.outcome == ActionOutcome.EXECUTED_SUCCESS:
            stats["success"] += 1
        elif record.outcome == ActionOutcome.EXECUTED_NEUTRAL:
            stats["neutral"] += 1
        elif record.outcome == ActionOutcome.EXECUTED_FAILURE:
            stats["failure"] += 1
        elif record.outcome == ActionOutcome.ERROR:
            stats["error"] += 1
        
        # Track pillar performance
        for pillar, score in record.pillar_scores.items():
            if pillar not in self._pillar_performance:
                self._pillar_performance[pillar] = []
            self._pillar_performance[pillar].append((score, record.outcome.value))
    
    def _track_content_pattern(self, record: ActionRecord) -> None:
        """Track content patterns that lead to good engagement."""
        # Extract simple patterns from content
        content_lower = record.content.lower()
        
        patterns = []
        
        # Check for common patterns
        if "🔥" in record.content:
            patterns.append("fire_emoji")
        if "❤️" in record.content or "♥" in record.content:
            patterns.append("heart_emoji")
        if "vibes" in content_lower:
            patterns.append("vibes_word")
        if "love" in content_lower:
            patterns.append("love_word")
        if "thank" in content_lower:
            patterns.append("gratitude")
        if "?" in record.content:
            patterns.append("question")
        if "!" in record.content:
            patterns.append("exclamation")
        
        # Get engagement score
        engagement = record.engagement_result
        engagement_score = (
            engagement.get("likes", 0) * 1 +
            engagement.get("replies", 0) * 3 +
            engagement.get("retweets", 0) * 2
        )
        
        # Track patterns
        for pattern in patterns:
            if pattern not in self._content_patterns:
                self._content_patterns[pattern] = []
            self._content_patterns[pattern].append(engagement_score)
    
    async def analyze(self) -> List[LearningInsight]:
        """Analyze learning data and generate insights.
        
        Returns:
            List of learning insights
        """
        import uuid
        
        insights = []
        
        # Get recent records
        cutoff = datetime.now(timezone.utc) - timedelta(days=self.analysis_window_days)
        recent = [r for r in self._records if r.recorded_at >= cutoff]
        
        if len(recent) < 10:
            logger.info("Not enough recent data for analysis")
            return insights
        
        # Analyze threshold effectiveness
        threshold_insight = await self._analyze_thresholds(recent)
        if threshold_insight:
            insights.append(threshold_insight)
        
        # Analyze pillar weights
        pillar_insights = await self._analyze_pillar_weights(recent)
        insights.extend(pillar_insights)
        
        # Analyze content patterns
        pattern_insight = await self._analyze_content_patterns()
        if pattern_insight:
            insights.append(pattern_insight)
        
        # Store insights
        self._insights.extend(insights)
        self._save_data()
        
        logger.info(f"Analysis complete: {len(insights)} new insights")
        
        return insights
    
    async def _analyze_thresholds(self, records: List[ActionRecord]) -> Optional[LearningInsight]:
        """Analyze if thresholds need adjustment."""
        import uuid
        
        # Check for actions blocked that might have been good
        blocked = [r for r in records if r.outcome == ActionOutcome.BLOCKED]
        successful = [r for r in records if r.outcome == ActionOutcome.EXECUTED_SUCCESS]
        
        if not blocked or not successful:
            return None
        
        # Compare scores
        blocked_scores = [r.value_score for r in blocked]
        successful_scores = [r.value_score for r in successful]
        
        avg_blocked = sum(blocked_scores) / len(blocked_scores)
        avg_successful = sum(successful_scores) / len(successful_scores)
        
        # If blocked scores are close to successful, threshold might be too high
        gap = avg_successful - avg_blocked
        
        if gap < 10:  # Small gap
            return LearningInsight(
                insight_id=str(uuid.uuid4())[:12],
                insight_type="threshold_adjustment",
                description=f"Blocked actions scoring close to successful ones (gap={gap:.1f})",
                recommendation="Consider lowering threshold slightly to allow more engagement",
                confidence=0.7,
                evidence_count=len(blocked) + len(successful),
                suggested_threshold_delta=-5.0,
            )
        elif gap > 30:  # Large gap
            return LearningInsight(
                insight_id=str(uuid.uuid4())[:12],
                insight_type="threshold_adjustment",
                description=f"Large gap between blocked and successful scores (gap={gap:.1f})",
                recommendation="Threshold is well-calibrated, consider raising for quality",
                confidence=0.6,
                evidence_count=len(blocked) + len(successful),
                suggested_threshold_delta=2.0,
            )
        
        return None
    
    async def _analyze_pillar_weights(self, records: List[ActionRecord]) -> List[LearningInsight]:
        """Analyze if pillar weights need adjustment."""
        import uuid
        
        insights = []
        
        for pillar, performances in self._pillar_performance.items():
            if len(performances) < 20:
                continue
            
            # Get recent performances
            recent = performances[-100:]
            
            # Separate by outcome
            success_scores = [s for s, o in recent if o == "executed_success"]
            blocked_scores = [s for s, o in recent if o == "blocked"]
            
            if len(success_scores) < 5 or len(blocked_scores) < 5:
                continue
            
            avg_success = sum(success_scores) / len(success_scores)
            avg_blocked = sum(blocked_scores) / len(blocked_scores)
            
            # If this pillar is consistently low in blocked actions
            if avg_blocked < 40 and avg_success > 60:
                insights.append(LearningInsight(
                    insight_id=str(uuid.uuid4())[:12],
                    insight_type="pillar_weight",
                    description=f"Pillar {pillar} is key differentiator (blocked avg={avg_blocked:.0f}, success avg={avg_success:.0f})",
                    recommendation=f"Increase weight for pillar {pillar}",
                    confidence=0.75,
                    evidence_count=len(recent),
                    affected_pillars=[PillarID(pillar)] if pillar in [p.value for p in PillarID] else [],
                    suggested_weight_changes={pillar: 0.2},
                ))
        
        return insights
    
    async def _analyze_content_patterns(self) -> Optional[LearningInsight]:
        """Analyze content patterns that lead to good engagement."""
        import uuid
        
        if not self._content_patterns:
            return None
        
        # Find best performing patterns
        pattern_avgs = {}
        for pattern, scores in self._content_patterns.items():
            if len(scores) >= 5:
                pattern_avgs[pattern] = sum(scores) / len(scores)
        
        if not pattern_avgs:
            return None
        
        # Sort by average engagement
        sorted_patterns = sorted(pattern_avgs.items(), key=lambda x: x[1], reverse=True)
        best_patterns = sorted_patterns[:3]
        
        if best_patterns and best_patterns[0][1] > 5:  # Meaningful engagement
            return LearningInsight(
                insight_id=str(uuid.uuid4())[:12],
                insight_type="content_pattern",
                description=f"Top performing content patterns: {[p[0] for p in best_patterns]}",
                recommendation=f"Content with {best_patterns[0][0]} pattern performs best (avg engagement: {best_patterns[0][1]:.1f})",
                confidence=0.65,
                evidence_count=sum(len(self._content_patterns[p]) for p, _ in best_patterns),
            )
        
        return None
    
    def apply_insight(self, insight: LearningInsight, calculator=None) -> bool:
        """Apply an insight to the value calculator.
        
        Args:
            insight: The insight to apply
            calculator: ValueScoreCalculator to update (uses global if None)
            
        Returns:
            True if applied successfully
        """
        from .value_score import get_value_calculator
        
        calculator = calculator or get_value_calculator()
        
        try:
            if insight.insight_type == "threshold_adjustment":
                calculator.default_threshold += insight.suggested_threshold_delta
                logger.info(f"Adjusted default threshold by {insight.suggested_threshold_delta}")
            
            elif insight.insight_type == "pillar_weight":
                for pillar, delta in insight.suggested_weight_changes.items():
                    pillar_id = PillarID(pillar)
                    if pillar_id in calculator.DEFAULT_WEIGHTS:
                        calculator.DEFAULT_WEIGHTS[pillar_id] += delta
                        logger.info(f"Adjusted weight for {pillar} by {delta}")
            
            insight.applied = True
            insight.applied_at = datetime.now(timezone.utc)
            
            self._save_data()
            return True
            
        except Exception as e:
            logger.error(f"Error applying insight: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get learner statistics."""
        return {
            "total_records": len(self._records),
            "insights_generated": len(self._insights),
            "insights_applied": sum(1 for i in self._insights if isinstance(i, dict) and i.get("applied")),
            "stats_by_action_type": self._stats_by_type,
            "content_patterns_tracked": len(self._content_patterns),
            "pillars_tracked": len(self._pillar_performance),
        }
    
    def get_action_type_report(self, action_type: ActionType) -> Dict[str, Any]:
        """Get detailed report for an action type.
        
        Args:
            action_type: The action type to report on
            
        Returns:
            Detailed statistics and recommendations
        """
        action_key = action_type.value
        stats = self._stats_by_type.get(action_key, {})
        
        if not stats:
            return {"action_type": action_key, "message": "No data available"}
        
        # Calculate rates
        total = stats.get("total", 1)
        
        return {
            "action_type": action_key,
            "total_actions": total,
            "pass_rate": (stats.get("success", 0) + stats.get("neutral", 0)) / total,
            "block_rate": stats.get("blocked", 0) / total,
            "success_rate": stats.get("success", 0) / total,
            "error_rate": stats.get("error", 0) / total,
            "recommendation": self._get_recommendation_for_type(stats),
        }
    
    def _get_recommendation_for_type(self, stats: Dict[str, int]) -> str:
        """Generate recommendation based on stats."""
        total = stats.get("total", 1)
        block_rate = stats.get("blocked", 0) / total
        success_rate = stats.get("success", 0) / total
        
        if block_rate > 0.5:
            return "High block rate - consider improving context gathering before actions"
        elif success_rate < 0.3:
            return "Low success rate - review content quality and timing"
        elif success_rate > 0.7:
            return "Performing well - maintain current approach"
        else:
            return "Moderate performance - look for patterns in successful actions"


# Global learner instance
_learner: ActionLearner | None = None


def get_action_learner() -> ActionLearner:
    """Get the global action learner instance."""
    global _learner
    if _learner is None:
        _learner = ActionLearner()
    return _learner
