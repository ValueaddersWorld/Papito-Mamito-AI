"""
PAPITO MAMITO AI - VALUE-GATED EVENT HANDLERS
==============================================
Event handlers that use the Value Score Intelligence system
to decide whether to act on events.

Every action Papito takes must pass through the Action Gate:
    
    Event → [Generate Response] → [Action Gate] → Execute/Block
                                         ↓
                                   [Learner Records]

© 2026 Value Adders World - Entertainment Division
"Add value or don't act."
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional

from papito_core.realtime import Event, EventType
from papito_core.intelligence import (
    ActionType,
    GateDecision,
    get_action_gate,
    get_action_learner,
)

logger = logging.getLogger("papito.handlers")


@dataclass
class HandlerResult:
    """Result from an event handler."""
    event_id: str
    event_type: EventType
    decision: GateDecision
    response_content: Optional[str] = None
    executed: bool = False
    execution_result: Optional[Dict[str, Any]] = None
    reason: str = ""
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)


class ValueGatedHandlers:
    """
    Event handlers that gate all actions through value scoring.
    
    This class provides handlers for different event types, each
    using the Action Gate to ensure Papito only acts when adding value.
    
    Usage:
        handlers = ValueGatedHandlers(
            response_generator=my_ai_responder,
            publisher=my_x_publisher,
        )
        
        # Register with dispatcher
        dispatcher.on(EventType.MENTION)(handlers.handle_mention)
        dispatcher.on(EventType.REPLY)(handlers.handle_reply)
        dispatcher.on(EventType.TRENDING_TOPIC)(handlers.handle_trend)
    """
    
    def __init__(
        self,
        response_generator: Optional[Callable] = None,
        publisher: Optional[Any] = None,
        auto_execute: bool = False,
    ):
        """Initialize value-gated handlers.
        
        Args:
            response_generator: Async function to generate responses
            publisher: X/Twitter publisher instance
            auto_execute: Whether to auto-execute approved actions
        """
        self.gate = get_action_gate()
        self.learner = get_action_learner()
        self.response_generator = response_generator
        self.publisher = publisher
        self.auto_execute = auto_execute
        
        # Stats tracking
        self.stats = {
            "total_events": 0,
            "actions_passed": 0,
            "actions_blocked": 0,
            "actions_deferred": 0,
            "actions_escalated": 0,
            "executions_attempted": 0,
            "executions_successful": 0,
        }
        
        logger.info("ValueGatedHandlers initialized")
    
    async def handle_mention(self, event: Event) -> HandlerResult:
        """Handle Twitter mention with value gating.
        
        Args:
            event: The mention event
            
        Returns:
            HandlerResult with decision and optional response
        """
        self.stats["total_events"] += 1
        logger.info(f"📨 Processing MENTION from @{event.user_name}")
        
        # Generate potential response
        response_content = await self._generate_response(event, "mention")
        
        if not response_content:
            logger.warning(f"No response generated for mention {event.event_id}")
            return HandlerResult(
                event_id=event.event_id,
                event_type=EventType.MENTION,
                decision=GateDecision.BLOCK,
                reason="No response generated",
            )
        
        # Build context for value scoring
        context = {
            "user_name": event.user_name,
            "user_followers": event.metadata.get("followers_count", 0),
            "user_verified": event.metadata.get("verified", False),
            "original_content": event.content,
            "hour_of_day": datetime.now(timezone.utc).hour,
            "is_reply_context": True,
        }
        
        # Evaluate through Action Gate
        gate_result = await self.gate.evaluate(
            action_type=ActionType.REPLY,
            content=response_content,
            context=context,
        )
        
        # Track decision
        self._track_decision(gate_result.decision)
        
        if gate_result.decision == GateDecision.PASS:
            logger.info(f"✅ REPLY APPROVED (score: {gate_result.value_score.total_score:.1f}) for @{event.user_name}")
            
            # Execute if auto_execute is on
            execution_result = None
            if self.auto_execute and self.publisher:
                execution_result = await self._execute_reply(event, response_content)
                await self.learner.record_executed_action(gate_result, execution_result)
            
            return HandlerResult(
                event_id=event.event_id,
                event_type=EventType.MENTION,
                decision=GateDecision.PASS,
                response_content=response_content,
                executed=bool(execution_result),
                execution_result=execution_result,
                reason=gate_result.reason,
            )
        
        elif gate_result.decision == GateDecision.BLOCK:
            logger.info(f"🚫 REPLY BLOCKED (score: {gate_result.value_score.total_score:.1f}) - {gate_result.reason}")
            await self.learner.record_blocked_action(gate_result)
            
            # Log improvement suggestions
            if gate_result.suggestions:
                logger.debug(f"Suggestions: {gate_result.suggestions}")
            
            return HandlerResult(
                event_id=event.event_id,
                event_type=EventType.MENTION,
                decision=GateDecision.BLOCK,
                response_content=response_content,
                reason=gate_result.reason,
            )
        
        elif gate_result.decision == GateDecision.DEFER:
            logger.info(f"⏳ REPLY DEFERRED - {gate_result.reason}")
            
            return HandlerResult(
                event_id=event.event_id,
                event_type=EventType.MENTION,
                decision=GateDecision.DEFER,
                response_content=response_content,
                reason=gate_result.reason,
            )
        
        else:  # ESCALATE
            logger.info(f"⚠️ REPLY ESCALATED for manual review - {gate_result.reason}")
            
            return HandlerResult(
                event_id=event.event_id,
                event_type=EventType.MENTION,
                decision=GateDecision.ESCALATE,
                response_content=response_content,
                reason=gate_result.reason,
            )
    
    async def handle_reply(self, event: Event) -> HandlerResult:
        """Handle reply to Papito's tweet with value gating."""
        self.stats["total_events"] += 1
        logger.info(f"💬 Processing REPLY from @{event.user_name}")
        
        # Generate potential response
        response_content = await self._generate_response(event, "reply_thread")
        
        if not response_content:
            return HandlerResult(
                event_id=event.event_id,
                event_type=EventType.REPLY,
                decision=GateDecision.BLOCK,
                reason="No response generated",
            )
        
        # Context for value scoring
        context = {
            "user_name": event.user_name,
            "thread_depth": event.metadata.get("thread_depth", 1),
            "original_content": event.content,
            "in_thread": True,
        }
        
        # Evaluate through gate
        gate_result = await self.gate.evaluate(
            action_type=ActionType.REPLY,
            content=response_content,
            context=context,
        )
        
        self._track_decision(gate_result.decision)
        
        # Log and record
        if gate_result.decision == GateDecision.PASS:
            logger.info(f"✅ THREAD REPLY APPROVED (score: {gate_result.value_score.total_score:.1f})")
        else:
            logger.info(f"🚫 THREAD REPLY {gate_result.decision.value} - {gate_result.reason}")
            if gate_result.decision == GateDecision.BLOCK:
                await self.learner.record_blocked_action(gate_result)
        
        return HandlerResult(
            event_id=event.event_id,
            event_type=EventType.REPLY,
            decision=gate_result.decision,
            response_content=response_content if gate_result.decision == GateDecision.PASS else None,
            reason=gate_result.reason,
        )
    
    async def handle_trend(self, event: Event) -> HandlerResult:
        """Handle trending topic with value gating."""
        self.stats["total_events"] += 1
        trend_name = event.metadata.get("trend_name", "unknown")
        relevance = event.metadata.get("relevance_score", 0)
        
        logger.info(f"📈 Processing TREND: {trend_name} (relevance: {relevance})")
        
        # Only attempt if relevance is high enough
        if relevance < 0.3:
            logger.info(f"⏭️ Skipping trend {trend_name} - low relevance")
            return HandlerResult(
                event_id=event.event_id,
                event_type=EventType.TRENDING_TOPIC,
                decision=GateDecision.BLOCK,
                reason=f"Low relevance score: {relevance}",
            )
        
        # Generate potential tweet about trend
        response_content = await self._generate_response(event, "trend_comment")
        
        if not response_content:
            return HandlerResult(
                event_id=event.event_id,
                event_type=EventType.TRENDING_TOPIC,
                decision=GateDecision.BLOCK,
                reason="No response generated for trend",
            )
        
        # Context for value scoring
        context = {
            "trend_name": trend_name,
            "trend_relevance": relevance,
            "original_content": event.content,
            "is_proactive": True,  # We're initiating, not responding
        }
        
        # Evaluate through gate
        gate_result = await self.gate.evaluate(
            action_type=ActionType.TWEET,
            content=response_content,
            context=context,
        )
        
        self._track_decision(gate_result.decision)
        
        if gate_result.decision == GateDecision.PASS:
            logger.info(f"✅ TREND TWEET APPROVED (score: {gate_result.value_score.total_score:.1f})")
        else:
            logger.info(f"🚫 TREND TWEET {gate_result.decision.value} - {gate_result.reason}")
            if gate_result.decision == GateDecision.BLOCK:
                await self.learner.record_blocked_action(gate_result)
        
        return HandlerResult(
            event_id=event.event_id,
            event_type=EventType.TRENDING_TOPIC,
            decision=gate_result.decision,
            response_content=response_content if gate_result.decision == GateDecision.PASS else None,
            reason=gate_result.reason,
        )
    
    async def handle_quote(self, event: Event) -> HandlerResult:
        """Handle quote tweets with value gating."""
        self.stats["total_events"] += 1
        logger.info(f"🔄 Processing QUOTE from @{event.user_name}")
        
        # Generate potential response
        response_content = await self._generate_response(event, "quote_response")
        
        if not response_content:
            return HandlerResult(
                event_id=event.event_id,
                event_type=EventType.QUOTE,
                decision=GateDecision.BLOCK,
                reason="No response generated",
            )
        
        # Context for value scoring
        context = {
            "user_name": event.user_name,
            "quote_context": event.content,
            "is_engagement_response": True,
        }
        
        # Evaluate through gate
        gate_result = await self.gate.evaluate(
            action_type=ActionType.REPLY,
            content=response_content,
            context=context,
        )
        
        self._track_decision(gate_result.decision)
        
        if gate_result.decision == GateDecision.PASS:
            logger.info(f"✅ QUOTE REPLY APPROVED (score: {gate_result.value_score.total_score:.1f})")
        else:
            if gate_result.decision == GateDecision.BLOCK:
                await self.learner.record_blocked_action(gate_result)
        
        return HandlerResult(
            event_id=event.event_id,
            event_type=EventType.QUOTE,
            decision=gate_result.decision,
            response_content=response_content if gate_result.decision == GateDecision.PASS else None,
            reason=gate_result.reason,
        )
    
    async def handle_dm(self, event: Event) -> HandlerResult:
        """Handle direct messages with strict value gating."""
        self.stats["total_events"] += 1
        logger.info(f"📬 Processing DM from @{event.user_name}")
        
        # DMs have highest threshold - must add significant value
        response_content = await self._generate_response(event, "dm_reply")
        
        if not response_content:
            return HandlerResult(
                event_id=event.event_id,
                event_type=EventType.DM,
                decision=GateDecision.BLOCK,
                reason="No response generated",
            )
        
        # Context for value scoring (DMs have special considerations)
        context = {
            "user_name": event.user_name,
            "is_private": True,
            "requires_personalization": True,
            "original_content": event.content,
        }
        
        # Evaluate through gate (DMs have threshold 80)
        gate_result = await self.gate.evaluate(
            action_type=ActionType.DM,
            content=response_content,
            context=context,
        )
        
        self._track_decision(gate_result.decision)
        
        if gate_result.decision == GateDecision.PASS:
            logger.info(f"✅ DM REPLY APPROVED (score: {gate_result.value_score.total_score:.1f})")
        else:
            logger.info(f"🚫 DM REPLY {gate_result.decision.value} - High bar for private messages")
            if gate_result.decision == GateDecision.BLOCK:
                await self.learner.record_blocked_action(gate_result)
        
        return HandlerResult(
            event_id=event.event_id,
            event_type=EventType.DM,
            decision=gate_result.decision,
            response_content=response_content if gate_result.decision == GateDecision.PASS else None,
            reason=gate_result.reason,
        )
    
    async def _generate_response(self, event: Event, response_type: str) -> Optional[str]:
        """Generate a response for an event.
        
        Args:
            event: The event to respond to
            response_type: Type of response needed
            
        Returns:
            Generated response content or None
        """
        if self.response_generator:
            try:
                response = await self.response_generator(event, response_type)
                return response
            except Exception as e:
                logger.error(f"Error generating response: {e}")
                return None
        
        # Default placeholder response for testing
        return f"[Placeholder response for {response_type} to: {event.content[:50]}...]"
    
    async def _execute_reply(self, event: Event, content: str) -> Optional[Dict[str, Any]]:
        """Execute a reply action.
        
        Args:
            event: The event to reply to
            content: The reply content
            
        Returns:
            Execution result or None if failed
        """
        if not self.publisher:
            logger.warning("No publisher configured - skipping execution")
            return None
        
        self.stats["executions_attempted"] += 1
        
        try:
            # Call publisher to post reply
            result = await self.publisher.reply(
                tweet_id=event.source_id,
                content=content,
            )
            
            self.stats["executions_successful"] += 1
            logger.info(f"✅ Reply posted successfully")
            
            return {
                "tweet_id": result.get("id"),
                "posted_at": datetime.now(timezone.utc).isoformat(),
                "engagement": {},  # Will be updated later
            }
            
        except Exception as e:
            logger.error(f"Error executing reply: {e}")
            return None
    
    def _track_decision(self, decision: GateDecision) -> None:
        """Track decision statistics."""
        if decision == GateDecision.PASS:
            self.stats["actions_passed"] += 1
        elif decision == GateDecision.BLOCK:
            self.stats["actions_blocked"] += 1
        elif decision == GateDecision.DEFER:
            self.stats["actions_deferred"] += 1
        elif decision == GateDecision.ESCALATE:
            self.stats["actions_escalated"] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get handler statistics."""
        total = max(self.stats["total_events"], 1)
        
        return {
            **self.stats,
            "pass_rate": self.stats["actions_passed"] / total,
            "block_rate": self.stats["actions_blocked"] / total,
            "execution_success_rate": (
                self.stats["executions_successful"] / 
                max(self.stats["executions_attempted"], 1)
            ),
            "learner_stats": self.learner.get_stats(),
        }


def create_value_gated_handlers(
    response_generator: Optional[Callable] = None,
    publisher: Optional[Any] = None,
    auto_execute: bool = False,
) -> ValueGatedHandlers:
    """Factory function to create value-gated handlers.
    
    Args:
        response_generator: Async function to generate responses
        publisher: X/Twitter publisher instance
        auto_execute: Whether to auto-execute approved actions
        
    Returns:
        Configured ValueGatedHandlers instance
    """
    return ValueGatedHandlers(
        response_generator=response_generator,
        publisher=publisher,
        auto_execute=auto_execute,
    )
