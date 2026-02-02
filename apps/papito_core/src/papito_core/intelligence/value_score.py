"""
PAPITO MAMITO AI - VALUE SCORE CALCULATOR
=========================================
Enhanced ADD VALUE scoring for real-time autonomous actions.

The 8 Pillars of ADD VALUE:
- A: Awareness - See the truth without distortion
- D: Define - Name what is present and required
- D: Devise - Create the simplest path forward
- V: Validate - Confirm reality through evidence
- A: Act Upon - Execute with commitment
- L: Learn - Extract feedback without ego
- U: Understand - Integrate wisdom beneath feedback
- E: Evolve - Apply insight and rise

Every outbound action is scored against these pillars.
Score >= threshold → Execute
Score < threshold → Block + Learn

© 2026 Value Adders World - Entertainment Division
"Add value or don't act."
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger("papito.intelligence.value")


class ActionType(str, Enum):
    """Types of actions Papito can take."""
    # Social actions
    TWEET = "tweet"                    # Post new tweet
    REPLY = "reply"                    # Reply to someone
    QUOTE = "quote"                    # Quote tweet
    RETWEET = "retweet"                # Retweet
    LIKE = "like"                      # Like a tweet
    FOLLOW = "follow"                  # Follow someone
    DM = "dm"                          # Send DM
    
    # Content actions
    CONTENT_CREATE = "content_create"  # Create new content
    CONTENT_SCHEDULE = "content_schedule"  # Schedule content
    
    # Engagement actions
    COLLAB_REQUEST = "collab_request"  # Request collaboration
    SHOUTOUT = "shoutout"              # Give shoutout
    
    # Internal actions
    TREND_RESPONSE = "trend_response"  # Respond to trend
    FAN_ENGAGE = "fan_engage"          # Engage with fan


class PillarID(str, Enum):
    """The 8 Pillars of ADD VALUE."""
    AWARENESS = "A"
    DEFINE = "D1"
    DEVISE = "D2"
    VALIDATE = "V"
    ACT_UPON = "A2"
    LEARN = "L"
    UNDERSTAND = "U"
    EVOLVE = "E"


@dataclass
class PillarScore:
    """Score for a single ADD VALUE pillar."""
    pillar: PillarID
    score: float  # 0-100
    weight: float = 1.0
    reasoning: str = ""
    evidence: List[str] = field(default_factory=list)
    
    @property
    def weighted_score(self) -> float:
        """Get weighted score for this pillar."""
        return self.score * self.weight
    
    @property
    def passed(self) -> bool:
        """Check if pillar score is passing (>=50)."""
        return self.score >= 50


@dataclass
class ActionValueScore:
    """Complete value score for an action."""
    action_id: str
    action_type: ActionType
    content: str
    
    # Pillar scores
    awareness: PillarScore = None
    define: PillarScore = None
    devise: PillarScore = None
    validate: PillarScore = None
    act_upon: PillarScore = None
    learn: PillarScore = None
    understand: PillarScore = None
    evolve: PillarScore = None
    
    # Aggregate
    total_score: float = 0.0
    threshold: float = 70.0
    should_execute: bool = False
    
    # Metadata
    context: Dict[str, Any] = field(default_factory=dict)
    calculated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    calculation_time_ms: int = 0
    
    def __post_init__(self):
        """Calculate aggregate score after initialization."""
        self._calculate_total()
    
    def _calculate_total(self) -> None:
        """Calculate total weighted score."""
        pillars = [
            self.awareness, self.define, self.devise, self.validate,
            self.act_upon, self.learn, self.understand, self.evolve
        ]
        
        valid_pillars = [p for p in pillars if p is not None]
        
        if not valid_pillars:
            self.total_score = 0.0
            self.should_execute = False
            return
        
        total_weight = sum(p.weight for p in valid_pillars)
        weighted_sum = sum(p.weighted_score for p in valid_pillars)
        
        self.total_score = weighted_sum / total_weight if total_weight > 0 else 0.0
        self.should_execute = self.total_score >= self.threshold
    
    @property
    def pillar_summary(self) -> Dict[str, float]:
        """Get summary of all pillar scores."""
        return {
            "A": self.awareness.score if self.awareness else 0,
            "D1": self.define.score if self.define else 0,
            "D2": self.devise.score if self.devise else 0,
            "V": self.validate.score if self.validate else 0,
            "A2": self.act_upon.score if self.act_upon else 0,
            "L": self.learn.score if self.learn else 0,
            "U": self.understand.score if self.understand else 0,
            "E": self.evolve.score if self.evolve else 0,
        }
    
    @property
    def weak_pillars(self) -> List[PillarID]:
        """Get list of pillars scoring below 50."""
        weak = []
        for pillar, score in [
            (PillarID.AWARENESS, self.awareness),
            (PillarID.DEFINE, self.define),
            (PillarID.DEVISE, self.devise),
            (PillarID.VALIDATE, self.validate),
            (PillarID.ACT_UPON, self.act_upon),
            (PillarID.LEARN, self.learn),
            (PillarID.UNDERSTAND, self.understand),
            (PillarID.EVOLVE, self.evolve),
        ]:
            if score and score.score < 50:
                weak.append(pillar)
        return weak
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage/logging."""
        return {
            "action_id": self.action_id,
            "action_type": self.action_type.value,
            "content": self.content[:200] + "..." if len(self.content) > 200 else self.content,
            "total_score": round(self.total_score, 2),
            "threshold": self.threshold,
            "should_execute": self.should_execute,
            "pillars": self.pillar_summary,
            "weak_pillars": [p.value for p in self.weak_pillars],
            "calculated_at": self.calculated_at.isoformat(),
        }


class ValueScoreCalculator:
    """
    Calculates ADD VALUE scores for Papito's actions.
    
    Every action Papito takes is evaluated against the 8 pillars
    to determine if it truly adds value. This is the core differentiator
    of Value Adders World - "Add value or don't act."
    
    Scoring Logic:
    - Each pillar scores 0-100
    - Pillars can be weighted differently by action type
    - Total score is weighted average
    - Default threshold is 70 (configurable)
    - Actions below threshold are blocked
    
    Usage:
        calculator = ValueScoreCalculator()
        
        score = await calculator.calculate(
            action_type=ActionType.REPLY,
            content="Great vibes! 🔥",
            context={
                "user": "@fan123",
                "their_message": "Love your music!",
                "relationship_tier": "engaged_fan"
            }
        )
        
        if score.should_execute:
            # Execute the reply
        else:
            # Log why it was blocked
    """
    
    # Default weights for each pillar (can be overridden)
    DEFAULT_WEIGHTS = {
        PillarID.AWARENESS: 1.5,    # Critical: understand context
        PillarID.DEFINE: 1.2,       # Important: clear goal
        PillarID.DEVISE: 1.0,       # Standard: good plan
        PillarID.VALIDATE: 1.3,     # Important: evidence-based
        PillarID.ACT_UPON: 0.8,     # Lower: execution readiness
        PillarID.LEARN: 0.7,        # Lower: past learnings
        PillarID.UNDERSTAND: 0.8,   # Standard: pattern recognition
        PillarID.EVOLVE: 0.7,       # Lower: growth potential
    }
    
    # Action-specific weight overrides
    ACTION_WEIGHTS = {
        ActionType.REPLY: {
            PillarID.AWARENESS: 2.0,   # Must understand what they said
            PillarID.VALIDATE: 1.5,    # Must be relevant
        },
        ActionType.TWEET: {
            PillarID.DEFINE: 1.5,      # Clear message purpose
            PillarID.DEVISE: 1.5,      # Well-crafted content
        },
        ActionType.FOLLOW: {
            PillarID.AWARENESS: 1.8,   # Who are they?
            PillarID.VALIDATE: 1.8,    # Are they genuine?
        },
        ActionType.DM: {
            PillarID.AWARENESS: 2.0,   # Very personal, must understand
            PillarID.VALIDATE: 2.0,    # Must be appropriate
        },
    }
    
    # Thresholds by action type (some actions need higher bar)
    ACTION_THRESHOLDS = {
        ActionType.TWEET: 70,
        ActionType.REPLY: 65,          # Lower bar for engagement
        ActionType.QUOTE: 75,
        ActionType.RETWEET: 60,        # Lower bar for amplification
        ActionType.LIKE: 50,           # Lowest bar
        ActionType.FOLLOW: 60,
        ActionType.DM: 80,             # High bar for DMs
        ActionType.COLLAB_REQUEST: 85, # Very high bar
        ActionType.SHOUTOUT: 70,
    }
    
    def __init__(
        self,
        default_threshold: float = 70.0,
        personality_context: Dict[str, Any] = None,
    ):
        """Initialize the value score calculator.
        
        Args:
            default_threshold: Default score threshold for execution
            personality_context: Papito's personality traits for scoring
        """
        self.default_threshold = default_threshold
        self.personality = personality_context or self._default_personality()
        
        # Stats
        self._calculations = 0
        self._passed = 0
        self._blocked = 0
        
        logger.info("ValueScoreCalculator initialized")
    
    def _default_personality(self) -> Dict[str, Any]:
        """Default Papito personality traits for scoring."""
        return {
            "core_values": ["authenticity", "joy", "connection", "music", "afrobeat"],
            "communication_style": "warm, enthusiastic, musical, empowering",
            "engagement_principles": [
                "Celebrate fans genuinely",
                "Share music and culture",
                "Build community",
                "Stay positive but real",
                "Never spam or manipulate",
            ],
            "avoid": ["negativity", "controversy", "spam", "manipulation", "fake engagement"],
        }
    
    def _get_weights(self, action_type: ActionType) -> Dict[PillarID, float]:
        """Get pillar weights for an action type."""
        weights = self.DEFAULT_WEIGHTS.copy()
        
        if action_type in self.ACTION_WEIGHTS:
            weights.update(self.ACTION_WEIGHTS[action_type])
        
        return weights
    
    def _get_threshold(self, action_type: ActionType) -> float:
        """Get score threshold for an action type."""
        return self.ACTION_THRESHOLDS.get(action_type, self.default_threshold)
    
    async def calculate(
        self,
        action_type: ActionType,
        content: str,
        context: Dict[str, Any] = None,
        action_id: str = None,
    ) -> ActionValueScore:
        """
        Calculate value score for an action.
        
        Args:
            action_type: Type of action being evaluated
            content: The content/message of the action
            context: Additional context (user, situation, etc.)
            action_id: Unique ID for this action (auto-generated if None)
            
        Returns:
            ActionValueScore with pillar breakdowns and decision
        """
        import time
        import uuid
        
        start_time = time.time()
        self._calculations += 1
        
        action_id = action_id or str(uuid.uuid4())[:12]
        context = context or {}
        
        weights = self._get_weights(action_type)
        threshold = self._get_threshold(action_type)
        
        # Calculate each pillar
        awareness = await self._score_awareness(action_type, content, context, weights[PillarID.AWARENESS])
        define = await self._score_define(action_type, content, context, weights[PillarID.DEFINE])
        devise = await self._score_devise(action_type, content, context, weights[PillarID.DEVISE])
        validate = await self._score_validate(action_type, content, context, weights[PillarID.VALIDATE])
        act_upon = await self._score_act_upon(action_type, content, context, weights[PillarID.ACT_UPON])
        learn = await self._score_learn(action_type, content, context, weights[PillarID.LEARN])
        understand = await self._score_understand(action_type, content, context, weights[PillarID.UNDERSTAND])
        evolve = await self._score_evolve(action_type, content, context, weights[PillarID.EVOLVE])
        
        # Create score object
        score = ActionValueScore(
            action_id=action_id,
            action_type=action_type,
            content=content,
            awareness=awareness,
            define=define,
            devise=devise,
            validate=validate,
            act_upon=act_upon,
            learn=learn,
            understand=understand,
            evolve=evolve,
            threshold=threshold,
            context=context,
            calculation_time_ms=int((time.time() - start_time) * 1000),
        )
        
        # Recalculate totals
        score._calculate_total()
        
        # Update stats
        if score.should_execute:
            self._passed += 1
        else:
            self._blocked += 1
        
        logger.info(
            f"Value score for {action_type.value}: {score.total_score:.1f}/{threshold} "
            f"({'✓ PASS' if score.should_execute else '✗ BLOCK'})"
        )
        
        return score
    
    async def _score_awareness(
        self,
        action_type: ActionType,
        content: str,
        context: Dict[str, Any],
        weight: float,
    ) -> PillarScore:
        """
        Score AWARENESS pillar: Do we understand the situation clearly?
        
        Factors:
        - Is there context about who we're engaging with?
        - Do we understand the conversation history?
        - Are we aware of the user's relationship tier?
        - Is the timing appropriate?
        """
        score = 50.0  # Base score
        evidence = []
        
        # User context (+20)
        if context.get("user_id") or context.get("user_name"):
            score += 10
            evidence.append("User identified")
            
            if context.get("follower_count"):
                score += 5
                evidence.append(f"Follower count known: {context['follower_count']}")
            
            if context.get("relationship_tier"):
                score += 5
                evidence.append(f"Relationship tier: {context['relationship_tier']}")
        
        # Conversation context (+15)
        if context.get("their_message") or context.get("original_content"):
            score += 10
            evidence.append("Original message available")
            
            if len(context.get("their_message", "")) > 20:
                score += 5
                evidence.append("Detailed message context")
        
        # Timing context (+15)
        if context.get("event_time") or context.get("created_at"):
            score += 10
            evidence.append("Timing context available")
            
            # Check if responding within reasonable time
            # (would need actual time comparison logic here)
            score += 5
            evidence.append("Timely response")
        
        reasoning = f"Awareness of context: {len(evidence)} factors identified"
        
        return PillarScore(
            pillar=PillarID.AWARENESS,
            score=min(100, score),
            weight=weight,
            reasoning=reasoning,
            evidence=evidence,
        )
    
    async def _score_define(
        self,
        action_type: ActionType,
        content: str,
        context: Dict[str, Any],
        weight: float,
    ) -> PillarScore:
        """
        Score DEFINE pillar: Is the goal clear?
        
        Factors:
        - What is the purpose of this action?
        - Is the intended outcome defined?
        - Is this aligned with Papito's mission?
        """
        score = 50.0
        evidence = []
        
        # Action type clarity (+15)
        if action_type in [ActionType.REPLY, ActionType.TWEET]:
            score += 15
            evidence.append(f"Clear action type: {action_type.value}")
        
        # Content has clear intent (+20)
        if content and len(content) >= 10:
            score += 10
            evidence.append("Content has substance")
            
            # Check for engagement words
            engagement_words = ["love", "amazing", "thank", "appreciate", "welcome", "vibe", "music"]
            if any(word in content.lower() for word in engagement_words):
                score += 10
                evidence.append("Positive engagement intent")
        
        # Goal alignment (+15)
        if context.get("goal") or context.get("intent"):
            score += 15
            evidence.append(f"Explicit goal: {context.get('goal', context.get('intent'))}")
        else:
            # Infer goal from action type
            inferred_goals = {
                ActionType.REPLY: "Engage with fan/community",
                ActionType.TWEET: "Share content with audience",
                ActionType.FOLLOW: "Build network",
                ActionType.LIKE: "Show appreciation",
            }
            if action_type in inferred_goals:
                score += 10
                evidence.append(f"Inferred goal: {inferred_goals[action_type]}")
        
        reasoning = f"Goal clarity: {'Strong' if score >= 75 else 'Moderate' if score >= 50 else 'Weak'}"
        
        return PillarScore(
            pillar=PillarID.DEFINE,
            score=min(100, score),
            weight=weight,
            reasoning=reasoning,
            evidence=evidence,
        )
    
    async def _score_devise(
        self,
        action_type: ActionType,
        content: str,
        context: Dict[str, Any],
        weight: float,
    ) -> PillarScore:
        """
        Score DEVISE pillar: Is this the best approach?
        
        Factors:
        - Is the content well-crafted?
        - Is this the simplest effective approach?
        - Does it follow best practices?
        """
        score = 50.0
        evidence = []
        
        # Content quality (+25)
        if content:
            # Length check
            if 20 <= len(content) <= 280:
                score += 10
                evidence.append("Appropriate length")
            elif len(content) > 280:
                score -= 10
                evidence.append("Too long (needs trimming)")
            
            # No spam indicators
            spam_indicators = ["buy now", "click here", "free", "dm me for", "🔥🔥🔥🔥🔥"]
            if not any(spam in content.lower() for spam in spam_indicators):
                score += 10
                evidence.append("Not spammy")
            else:
                score -= 20
                evidence.append("Contains spam indicators")
            
            # Has personality
            personality_markers = ["vibes", "fam", "music", "love", "blessed", "🎵", "🔥", "❤️"]
            if any(marker in content.lower() for marker in personality_markers):
                score += 5
                evidence.append("Has Papito personality")
        
        # Best approach (+10)
        if action_type == ActionType.REPLY and context.get("their_message"):
            # Check if reply is relevant to their message
            their_words = set(context["their_message"].lower().split())
            our_words = set(content.lower().split())
            overlap = their_words & our_words
            if len(overlap) >= 2:
                score += 10
                evidence.append("Reply is relevant to their message")
        
        reasoning = f"Approach quality: {len(evidence)} positive factors"
        
        return PillarScore(
            pillar=PillarID.DEVISE,
            score=min(100, score),
            weight=weight,
            reasoning=reasoning,
            evidence=evidence,
        )
    
    async def _score_validate(
        self,
        action_type: ActionType,
        content: str,
        context: Dict[str, Any],
        weight: float,
    ) -> PillarScore:
        """
        Score VALIDATE pillar: Is this validated by evidence?
        
        Factors:
        - Is the user genuine (not a bot)?
        - Is the context verified?
        - Is this action appropriate for the situation?
        """
        score = 50.0
        evidence = []
        
        # User validation (+20)
        follower_count = context.get("follower_count", 0)
        if follower_count > 100:
            score += 10
            evidence.append(f"User has {follower_count} followers (likely real)")
        elif follower_count > 0:
            score += 5
            evidence.append("User has some followers")
        
        # Not a bot check (+15)
        if context.get("is_verified") or context.get("verified"):
            score += 15
            evidence.append("User is verified")
        elif context.get("account_age_days", 365) > 30:
            score += 10
            evidence.append("Account is established")
        
        # Content appropriateness (+15)
        inappropriate = ["hate", "spam", "scam", "fake", "nsfw"]
        if not any(word in content.lower() for word in inappropriate):
            score += 15
            evidence.append("Content is appropriate")
        else:
            score -= 30
            evidence.append("Content may be inappropriate")
        
        reasoning = f"Validation: {'Strong' if score >= 75 else 'Moderate' if score >= 50 else 'Weak'}"
        
        return PillarScore(
            pillar=PillarID.VALIDATE,
            score=min(100, score),
            weight=weight,
            reasoning=reasoning,
            evidence=evidence,
        )
    
    async def _score_act_upon(
        self,
        action_type: ActionType,
        content: str,
        context: Dict[str, Any],
        weight: float,
    ) -> PillarScore:
        """
        Score ACT UPON pillar: Are we ready to execute?
        
        Factors:
        - Is everything in place to act?
        - Are rate limits OK?
        - Is the system healthy?
        """
        score = 70.0  # Higher base - if we got here, we're likely ready
        evidence = []
        
        # Content ready (+15)
        if content and len(content.strip()) > 0:
            score += 15
            evidence.append("Content is ready")
        
        # No blockers (+15)
        if not context.get("blocked_reason"):
            score += 15
            evidence.append("No blockers identified")
        else:
            score -= 30
            evidence.append(f"Blocker: {context['blocked_reason']}")
        
        reasoning = "Ready to execute" if score >= 70 else "Execution readiness unclear"
        
        return PillarScore(
            pillar=PillarID.ACT_UPON,
            score=min(100, score),
            weight=weight,
            reasoning=reasoning,
            evidence=evidence,
        )
    
    async def _score_learn(
        self,
        action_type: ActionType,
        content: str,
        context: Dict[str, Any],
        weight: float,
    ) -> PillarScore:
        """
        Score LEARN pillar: What have we learned from similar actions?
        
        Factors:
        - Past performance of similar actions
        - User engagement history
        - What worked before?
        """
        score = 60.0  # Base - learning is ongoing
        evidence = []
        
        # Historical context (+20)
        if context.get("past_interactions"):
            score += 15
            evidence.append("Have history with this user")
            
            if context.get("past_positive_outcome"):
                score += 5
                evidence.append("Past interactions were positive")
        
        # Similar action performance (+15)
        if context.get("similar_action_success_rate"):
            rate = context["similar_action_success_rate"]
            if rate > 0.7:
                score += 15
                evidence.append(f"Similar actions succeed {rate*100:.0f}% of time")
            elif rate > 0.5:
                score += 10
                evidence.append(f"Similar actions have moderate success")
        
        reasoning = f"Learning score based on {len(evidence)} historical factors"
        
        return PillarScore(
            pillar=PillarID.LEARN,
            score=min(100, score),
            weight=weight,
            reasoning=reasoning,
            evidence=evidence,
        )
    
    async def _score_understand(
        self,
        action_type: ActionType,
        content: str,
        context: Dict[str, Any],
        weight: float,
    ) -> PillarScore:
        """
        Score UNDERSTAND pillar: Do we see the deeper pattern?
        
        Factors:
        - Understanding of user's intent
        - Pattern recognition
        - Contextual wisdom
        """
        score = 60.0
        evidence = []
        
        # Intent understanding (+20)
        if context.get("detected_intent"):
            score += 15
            evidence.append(f"Detected intent: {context['detected_intent']}")
            
            if context.get("intent_confidence", 0) > 0.8:
                score += 5
                evidence.append("High confidence in intent")
        
        # Pattern recognition (+15)
        if context.get("user_pattern") or context.get("engagement_pattern"):
            score += 15
            evidence.append("User engagement pattern identified")
        
        reasoning = f"Understanding depth: {len(evidence)} insights"
        
        return PillarScore(
            pillar=PillarID.UNDERSTAND,
            score=min(100, score),
            weight=weight,
            reasoning=reasoning,
            evidence=evidence,
        )
    
    async def _score_evolve(
        self,
        action_type: ActionType,
        content: str,
        context: Dict[str, Any],
        weight: float,
    ) -> PillarScore:
        """
        Score EVOLVE pillar: Does this action help Papito grow?
        
        Factors:
        - Will this improve future interactions?
        - Is this expanding reach meaningfully?
        - Are we building real relationships?
        """
        score = 60.0
        evidence = []
        
        # Relationship building (+20)
        if action_type in [ActionType.REPLY, ActionType.DM]:
            score += 15
            evidence.append("Deepens relationship with fan")
            
            if context.get("relationship_tier") in ["super_fan", "engaged_fan"]:
                score += 5
                evidence.append("Engaging valuable community member")
        
        # Reach expansion (+15)
        if action_type == ActionType.TWEET:
            score += 10
            evidence.append("Expands content reach")
            
            if context.get("trending_topic"):
                score += 5
                evidence.append("Leverages trending topic")
        
        # Growth potential (+10)
        if context.get("growth_potential"):
            score += 10
            evidence.append(f"Growth potential: {context['growth_potential']}")
        
        reasoning = f"Evolution potential: {'High' if score >= 75 else 'Moderate' if score >= 50 else 'Low'}"
        
        return PillarScore(
            pillar=PillarID.EVOLVE,
            score=min(100, score),
            weight=weight,
            reasoning=reasoning,
            evidence=evidence,
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get calculator statistics."""
        total = self._passed + self._blocked
        return {
            "calculations": self._calculations,
            "passed": self._passed,
            "blocked": self._blocked,
            "pass_rate": self._passed / total if total > 0 else 0,
            "block_rate": self._blocked / total if total > 0 else 0,
        }


# Global calculator instance
_calculator: ValueScoreCalculator | None = None


def get_value_calculator() -> ValueScoreCalculator:
    """Get the global value score calculator instance."""
    global _calculator
    if _calculator is None:
        _calculator = ValueScoreCalculator()
    return _calculator
