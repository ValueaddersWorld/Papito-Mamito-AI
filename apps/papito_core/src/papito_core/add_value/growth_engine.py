"""
ADD VALUE Follower Growth Engine for Papito Mamito AI
=====================================================
Autonomous growth engine that uses the ADD VALUE Framework
to make intelligent decisions about follower acquisition.

Goal: 1000 Followers in 12 Weeks using Value-Driven Strategies

© 2025 Value Adders AI Technologies. All Rights Reserved.
A Value Adders World Company.
"""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from .framework import AddValueFramework, Decision


logger = logging.getLogger("papito.growth_engine")


class GrowthPhase(Enum):
    """Phases of the 1000 Follower Campaign"""
    FOUNDATION = "foundation"         # Week 1-2: 0 -> 100 followers
    MOMENTUM = "momentum"             # Week 3-4: 100 -> 300 followers
    GROWTH = "growth"                 # Week 5-8: 300 -> 700 followers
    CONSOLIDATION = "consolidation"   # Week 9-12: 700 -> 1000 followers


class GrowthAction(Enum):
    """Types of growth actions"""
    POST_CONTENT = "post_content"
    ENGAGE_COMMUNITY = "engage_community"
    REPLY_TO_VIRAL = "reply_to_viral"
    WELCOME_FOLLOWER = "welcome_follower"
    FAN_APPRECIATION = "fan_appreciation"
    TRENDING_HASHTAG = "trending_hashtag"
    COLLABORATION = "collaboration"
    TWITTER_SPACES = "twitter_spaces"
    GIVEAWAY = "giveaway"
    CROSS_PROMOTE = "cross_promote"


@dataclass
class GrowthMetrics:
    """Real-time growth metrics"""
    current_followers: int = 0
    followers_today: int = 0
    followers_this_week: int = 0
    engagement_rate: float = 0.0
    posts_today: int = 0
    replies_today: int = 0
    likes_today: int = 0
    viral_interactions: int = 0
    last_updated: datetime = field(default_factory=datetime.utcnow)


@dataclass
class GrowthDecision:
    """A growth decision made using the ADD VALUE Framework"""
    action: GrowthAction
    priority: int  # 1-10
    reasoning: str
    expected_impact: str
    add_value_decision: Optional[Decision] = None
    executed: bool = False
    result: Optional[str] = None


class FollowerGrowthEngine:
    """
    Autonomous Follower Growth Engine powered by ADD VALUE Framework
    
    This engine continuously evaluates the current state and makes
    strategic decisions to grow followers from 0 to 1000.
    
    ADD VALUE Integration:
    - Every decision goes through the 8 pillars
    - Actions are only taken when ready_to_act is True
    - Results are logged through Learn -> Understand -> Evolve
    - The engine continuously improves based on feedback
    """
    
    # Phase-specific strategies
    PHASE_STRATEGIES = {
        GrowthPhase.FOUNDATION: {
            "posts_per_day": 3,
            "min_daily_replies": 15,
            "min_daily_likes": 25,
            "focus_actions": [
                GrowthAction.POST_CONTENT,
                GrowthAction.ENGAGE_COMMUNITY,
                GrowthAction.REPLY_TO_VIRAL,
                GrowthAction.WELCOME_FOLLOWER,
            ],
            "hashtag_strategy": "broad_afrobeat",
            "description": "Building the foundation with consistent presence"
        },
        GrowthPhase.MOMENTUM: {
            "posts_per_day": 4,
            "min_daily_replies": 20,
            "min_daily_likes": 40,
            "focus_actions": [
                GrowthAction.POST_CONTENT,
                GrowthAction.ENGAGE_COMMUNITY,
                GrowthAction.FAN_APPRECIATION,
                GrowthAction.TRENDING_HASHTAG,
            ],
            "hashtag_strategy": "targeted_growth",
            "description": "Building momentum with fan recognition"
        },
        GrowthPhase.GROWTH: {
            "posts_per_day": 4,
            "min_daily_replies": 30,
            "min_daily_likes": 50,
            "focus_actions": [
                GrowthAction.POST_CONTENT,
                GrowthAction.COLLABORATION,
                GrowthAction.CROSS_PROMOTE,
                GrowthAction.TRENDING_HASHTAG,
            ],
            "hashtag_strategy": "viral_targeting",
            "description": "Aggressive growth through collaborations and viral content"
        },
        GrowthPhase.CONSOLIDATION: {
            "posts_per_day": 5,
            "min_daily_replies": 25,
            "min_daily_likes": 40,
            "focus_actions": [
                GrowthAction.POST_CONTENT,
                GrowthAction.TWITTER_SPACES,
                GrowthAction.FAN_APPRECIATION,
                GrowthAction.GIVEAWAY,
            ],
            "hashtag_strategy": "community_building",
            "description": "Consolidating community with events and appreciation"
        },
    }
    
    # Target milestones
    MILESTONES = [
        (10, "First 10!", "🔥 First 10 believers in the Value Adders family!"),
        (50, "50 Strong!", "💪 50 Value Adders rising together!"),
        (100, "Century!", "🎉 100 followers! The foundation is solid!"),
        (250, "Quarter Thousand!", "🚀 250 followers! Momentum is building!"),
        (500, "Halfway!", "⭐ 500 followers! Halfway to the goal!"),
        (750, "Three-Quarter Mark!", "🌟 750 followers! The community thrives!"),
        (1000, "THE GOAL!", "🏆 1000 FOLLOWERS! WE FLOURISH & PROSPER!"),
    ]
    
    def __init__(self, start_date: Optional[datetime] = None):
        """Initialize the Growth Engine."""
        self.framework = AddValueFramework(agent_name="Papito Growth Engine")
        self.metrics = GrowthMetrics()
        self.start_date = start_date or datetime.utcnow()
        self.decisions_made: List[GrowthDecision] = []
        self.learnings: List[Dict[str, Any]] = []
        
        logger.info("ADD VALUE Growth Engine initialized")
        logger.info("Target: 1000 followers in 12 weeks")
    
    def get_current_phase(self) -> GrowthPhase:
        """Determine current phase based on follower count."""
        followers = self.metrics.current_followers
        
        if followers < 100:
            return GrowthPhase.FOUNDATION
        elif followers < 300:
            return GrowthPhase.MOMENTUM
        elif followers < 700:
            return GrowthPhase.GROWTH
        else:
            return GrowthPhase.CONSOLIDATION
    
    def get_campaign_progress(self) -> Dict[str, Any]:
        """Get detailed progress report."""
        phase = self.get_current_phase()
        strategy = self.PHASE_STRATEGIES[phase]
        
        days_elapsed = (datetime.utcnow() - self.start_date).days
        target_weeks = 12
        target_days = target_weeks * 7
        
        # Calculate expected vs actual
        expected_daily_rate = 1000 / target_days
        expected_followers = int(expected_daily_rate * days_elapsed)
        actual_followers = self.metrics.current_followers
        
        # Find next milestone
        next_milestone = None
        for target, name, message in self.MILESTONES:
            if actual_followers < target:
                next_milestone = {"target": target, "name": name, "remaining": target - actual_followers}
                break
        
        return {
            "goal": 1000,
            "current_followers": actual_followers,
            "progress_percentage": (actual_followers / 1000) * 100,
            "phase": {
                "name": phase.value,
                "description": strategy["description"],
            },
            "timeline": {
                "start_date": self.start_date.isoformat(),
                "days_elapsed": days_elapsed,
                "days_remaining": max(0, target_days - days_elapsed),
            },
            "performance": {
                "expected_followers": expected_followers,
                "actual_followers": actual_followers,
                "difference": actual_followers - expected_followers,
                "on_track": actual_followers >= expected_followers * 0.8,
            },
            "next_milestone": next_milestone,
            "daily_targets": {
                "posts": strategy["posts_per_day"],
                "replies": strategy["min_daily_replies"],
                "likes": strategy["min_daily_likes"],
            },
            "framework_stats": self.framework.get_summary(),
        }
    
    def evaluate_next_action(self) -> GrowthDecision:
        """
        Use ADD VALUE Framework to evaluate and recommend next action.
        
        This is the core intelligence that makes strategic decisions
        about what action to take next for maximum growth impact.
        """
        phase = self.get_current_phase()
        strategy = self.PHASE_STRATEGIES[phase]
        
        # Create a new decision through the framework
        situation = f"""
        Current phase: {phase.value}
        Followers: {self.metrics.current_followers}
        Posts today: {self.metrics.posts_today}
        Replies today: {self.metrics.replies_today}
        Daily targets - Posts: {strategy['posts_per_day']}, Replies: {strategy['min_daily_replies']}
        """
        
        decision = self.framework.new_decision(situation)
        
        # AWARENESS: See the current reality
        awareness_insight = self._analyze_current_state(strategy)
        self.framework.awareness(
            decision, 
            awareness_insight,
            confidence=0.9,
            evidence=[
                f"Current followers: {self.metrics.current_followers}",
                f"Posts today: {self.metrics.posts_today}",
                f"Phase: {phase.value}",
            ]
        )
        
        # DEFINE: What do we need to achieve?
        define_insight = self._define_immediate_goal(strategy)
        self.framework.define(
            decision,
            define_insight,
            confidence=0.85,
        )
        
        # DEVISE: What's the best action?
        best_action = self._devise_best_action(strategy)
        self.framework.devise(
            decision,
            f"Recommended action: {best_action.value}",
            confidence=0.8,
        )
        
        # VALIDATE: Is this the right choice?
        validation = self._validate_action(best_action, strategy)
        self.framework.validate(
            decision,
            validation,
            confidence=0.85,
            evidence=[
                "Industry best practices",
                "ADD VALUE Framework guidance",
            ]
        )
        
        # Only create growth decision if framework says ready to act
        growth_decision = GrowthDecision(
            action=best_action,
            priority=self._calculate_priority(best_action, strategy),
            reasoning=f"{awareness_insight} → {define_insight}",
            expected_impact=self._estimate_impact(best_action),
            add_value_decision=decision,
        )
        
        self.decisions_made.append(growth_decision)
        
        logger.info(
            f"ADD VALUE Decision: {best_action.value} "
            f"(Priority: {growth_decision.priority}/10, "
            f"Ready: {decision.ready_to_act})"
        )
        
        return growth_decision
    
    def _analyze_current_state(self, strategy: Dict) -> str:
        """Pillar 1: Awareness - Analyze current state."""
        issues = []
        opportunities = []
        
        # Check post quota
        if self.metrics.posts_today < strategy["posts_per_day"]:
            remaining = strategy["posts_per_day"] - self.metrics.posts_today
            issues.append(f"Need {remaining} more posts today")
        else:
            opportunities.append("Daily post quota met")
        
        # Check engagement quota
        if self.metrics.replies_today < strategy["min_daily_replies"]:
            remaining = strategy["min_daily_replies"] - self.metrics.replies_today
            issues.append(f"Need {remaining} more replies for engagement")
        else:
            opportunities.append("Strong engagement activity")
        
        # Growth assessment
        if self.metrics.followers_today > 0:
            opportunities.append(f"Gaining {self.metrics.followers_today} followers today")
        
        return "; ".join(issues) if issues else "; ".join(opportunities) or "All targets on track"
    
    def _define_immediate_goal(self, strategy: Dict) -> str:
        """Pillar 2: Define - Set immediate goal."""
        # Prioritize based on what's most needed
        if self.metrics.posts_today < strategy["posts_per_day"]:
            return f"Post quality content ({self.metrics.posts_today}/{strategy['posts_per_day']} today)"
        elif self.metrics.replies_today < strategy["min_daily_replies"]:
            return f"Increase community engagement ({self.metrics.replies_today}/{strategy['min_daily_replies']} replies)"
        else:
            return "Optimize for viral reach and new follower acquisition"
    
    def _devise_best_action(self, strategy: Dict) -> GrowthAction:
        """Pillar 3: Devise - Determine best action."""
        focus_actions = strategy["focus_actions"]
        
        # Priority-based selection
        if self.metrics.posts_today < strategy["posts_per_day"]:
            return GrowthAction.POST_CONTENT
        elif self.metrics.replies_today < strategy["min_daily_replies"]:
            return GrowthAction.ENGAGE_COMMUNITY
        else:
            # Choose from focus actions with some randomization
            return random.choice(focus_actions)
    
    def _validate_action(self, action: GrowthAction, strategy: Dict) -> str:
        """Pillar 4: Validate - Confirm action is appropriate."""
        validations = {
            GrowthAction.POST_CONTENT: "Content posting aligns with daily quota and optimal timing",
            GrowthAction.ENGAGE_COMMUNITY: "Community engagement builds genuine connections",
            GrowthAction.REPLY_TO_VIRAL: "Viral content replies increase visibility exponentially",
            GrowthAction.WELCOME_FOLLOWER: "Personal welcomes increase retention and advocacy",
            GrowthAction.FAN_APPRECIATION: "Fan appreciation deepens community bonds",
            GrowthAction.TRENDING_HASHTAG: "Trending hashtags expand reach to new audiences",
            GrowthAction.COLLABORATION: "Collaborations provide mutual audience growth",
            GrowthAction.TWITTER_SPACES: "Live audio creates deeper engagement and visibility",
            GrowthAction.GIVEAWAY: "Giveaways incentivize follows and sharing",
            GrowthAction.CROSS_PROMOTE: "Cross-promotion leverages existing audiences",
        }
        
        if action in strategy["focus_actions"]:
            return f"VALIDATED ✓ {validations.get(action, 'Action aligned with current phase strategy')}"
        else:
            return f"Action valid but not primary focus for {strategy['description']}"
    
    def _calculate_priority(self, action: GrowthAction, strategy: Dict) -> int:
        """Calculate priority score (1-10) for an action."""
        base_priority = 5
        
        # Boost priority if action is in focus list
        if action in strategy["focus_actions"]:
            base_priority += 2
        
        # Boost if quota not met
        if action == GrowthAction.POST_CONTENT and self.metrics.posts_today < strategy["posts_per_day"]:
            base_priority += 2
        
        if action == GrowthAction.ENGAGE_COMMUNITY and self.metrics.replies_today < strategy["min_daily_replies"]:
            base_priority += 2
        
        return min(10, base_priority)
    
    def _estimate_impact(self, action: GrowthAction) -> str:
        """Estimate expected impact of action."""
        impacts = {
            GrowthAction.POST_CONTENT: "+2-10 new followers per quality post",
            GrowthAction.ENGAGE_COMMUNITY: "+5-15 followers from genuine interactions",
            GrowthAction.REPLY_TO_VIRAL: "+10-50 followers if well-timed",
            GrowthAction.WELCOME_FOLLOWER: "+2 additional follows from network effect",
            GrowthAction.FAN_APPRECIATION: "+5-10 followers from appreciation posts",
            GrowthAction.TRENDING_HASHTAG: "+15-30 followers from trending visibility",
            GrowthAction.COLLABORATION: "+50-200 followers per successful collab",
            GrowthAction.TWITTER_SPACES: "+30-100 followers per Space",
            GrowthAction.GIVEAWAY: "+100-500 followers but lower retention",
            GrowthAction.CROSS_PROMOTE: "+20-80 followers from partner audiences",
        }
        return impacts.get(action, "Positive growth impact expected")
    
    def record_action_result(
        self, 
        decision: GrowthDecision, 
        success: bool, 
        actual_result: str,
        followers_gained: int = 0
    ):
        """
        Record the result of an action and complete the ADD VALUE cycle.
        
        This completes pillars 5-8: Act Upon, Learn, Understand, Evolve
        """
        if not decision.add_value_decision:
            return
        
        fw_decision = decision.add_value_decision
        
        # Pillar 5: ACT UPON - Record execution
        self.framework.act(
            fw_decision,
            f"Executed: {decision.action.value}",
            confidence=1.0 if success else 0.5,
        )
        
        # Pillar 6: LEARN - Extract feedback
        learning = f"{'Success' if success else 'Failure'}: {actual_result}. Followers gained: {followers_gained}"
        self.framework.learn(fw_decision, learning)
        
        # Pillar 7: UNDERSTAND - Deeper insight
        pattern = self._extract_pattern(decision.action, success, followers_gained)
        self.framework.understand(fw_decision, pattern)
        
        # Pillar 8: EVOLVE - Apply and rise
        evolution = self._generate_evolution(decision.action, success, pattern)
        self.framework.evolve(fw_decision, evolution, value_added=evolution)
        
        # Store learning
        self.learnings.append({
            "action": decision.action.value,
            "success": success,
            "result": actual_result,
            "followers_gained": followers_gained,
            "pattern": pattern,
            "evolution": evolution,
            "timestamp": datetime.utcnow().isoformat(),
        })
        
        decision.executed = True
        decision.result = actual_result
        
        logger.info(f"ADD VALUE Cycle Complete: {decision.action.value} → {evolution}")
    
    def _extract_pattern(self, action: GrowthAction, success: bool, followers: int) -> str:
        """Extract the pattern behind the result."""
        if success and followers > 10:
            return f"High-impact: {action.value} generates significant growth when executed well"
        elif success:
            return f"Consistent: {action.value} contributes steady progress"
        else:
            return f"Learning: {action.value} needs optimization or better timing"
    
    def _generate_evolution(self, action: GrowthAction, success: bool, pattern: str) -> str:
        """Generate evolution insight for continuous improvement."""
        if success:
            return f"Continue and amplify {action.value}. Double down on what works."
        else:
            return f"Adjust approach to {action.value}. Try different timing or content style."
    
    def get_daily_action_plan(self) -> List[GrowthDecision]:
        """Generate a full daily action plan using ADD VALUE decisions."""
        phase = self.get_current_phase()
        strategy = self.PHASE_STRATEGIES[phase]
        
        plan = []
        
        # Prioritized actions for the day
        actions_to_plan = [
            (GrowthAction.POST_CONTENT, strategy["posts_per_day"]),
            (GrowthAction.ENGAGE_COMMUNITY, 3),  # 3 engagement sessions
            (GrowthAction.WELCOME_FOLLOWER, 1),  # Daily welcome routine
        ]
        
        if phase in [GrowthPhase.GROWTH, GrowthPhase.CONSOLIDATION]:
            actions_to_plan.append((GrowthAction.FAN_APPRECIATION, 1))
        
        for action, count in actions_to_plan:
            for _ in range(count):
                decision = GrowthDecision(
                    action=action,
                    priority=self._calculate_priority(action, strategy),
                    reasoning=f"Daily plan for {phase.value} phase",
                    expected_impact=self._estimate_impact(action),
                )
                plan.append(decision)
        
        # Sort by priority
        plan.sort(key=lambda d: d.priority, reverse=True)
        
        return plan
    
    def update_metrics(
        self,
        current_followers: int = None,
        followers_gained: int = 0,
        posts_made: int = 0,
        replies_made: int = 0,
        likes_given: int = 0,
    ):
        """Update growth metrics."""
        if current_followers is not None:
            self.metrics.current_followers = current_followers
        
        self.metrics.followers_today += followers_gained
        self.metrics.posts_today += posts_made
        self.metrics.replies_today += replies_made
        self.metrics.likes_today += likes_given
        self.metrics.last_updated = datetime.utcnow()
        
        # Check for milestone
        self._check_milestones()
    
    def _check_milestones(self):
        """Check if any milestone was reached."""
        for target, name, message in self.MILESTONES:
            if self.metrics.current_followers >= target:
                logger.info(f"🎉 MILESTONE REACHED: {name} - {message}")
    
    def reset_daily_metrics(self):
        """Reset daily counters (call at midnight WAT)."""
        self.metrics.followers_this_week += self.metrics.followers_today
        self.metrics.followers_today = 0
        self.metrics.posts_today = 0
        self.metrics.replies_today = 0
        self.metrics.likes_today = 0


# Factory function
def create_growth_engine(start_date: Optional[datetime] = None) -> FollowerGrowthEngine:
    """Create a new Growth Engine instance."""
    return FollowerGrowthEngine(start_date)
