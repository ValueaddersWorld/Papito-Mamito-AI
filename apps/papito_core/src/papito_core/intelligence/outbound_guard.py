"""Fail-closed outbound check for Papito's live worker.

Posts, replies, DMs, and other platform messages call ``permit_outbound``
before they are sent. The check uses ActionGate (ADD VALUE, default
threshold 70). Anything that is not an explicit pass is skipped, including
gate errors and the outbound kill switch.
"""

from __future__ import annotations

import asyncio
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any, Dict, Optional, Union

from papito_core.intelligence.action_gate import ActionGate, GateDecision, get_action_gate
from papito_core.intelligence.value_score import ActionType

logger = logging.getLogger("papito.outbound")

# Set to 1, true, yes, or on to pause every outbound action.
OUTBOUND_KILL_SWITCH_ENV = "PAPITO_OUTBOUND_KILL_SWITCH"

_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="papito-outbound-gate")


@dataclass(frozen=True)
class OutboundDecision:
    """Whether one outbound action may be sent."""

    allowed: bool
    score: Optional[float]
    reason: str
    action_type: str
    channel: str
    decision: str

    def as_skip(self) -> Dict[str, Any]:
        """Payload callers already treat as a failed send."""
        return {
            "success": False,
            "skipped": True,
            "error": self.reason,
            "score": self.score,
            "gate_decision": self.decision,
        }


def outbound_kill_switch_enabled() -> bool:
    """Return whether the operator has paused every outbound action."""
    value = os.getenv(OUTBOUND_KILL_SWITCH_ENV)
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _score_label(score: Optional[float]) -> str:
    if score is None:
        return "n/a"
    return f"{score:.1f}"


def _log_skip(decision: OutboundDecision) -> None:
    logger.warning(
        "Skipped outbound action channel=%s type=%s score=%s reason=%s",
        decision.channel,
        decision.action_type,
        _score_label(decision.score),
        decision.reason,
    )


def _coerce_action_type(action_type: Union[ActionType, str]) -> ActionType:
    if isinstance(action_type, ActionType):
        return action_type
    return ActionType(str(action_type))


def _evaluate_sync(
    gate: ActionGate,
    action_type: ActionType,
    content: str,
    context: Dict[str, Any],
):
    """Run the async gate from sync worker code, including a live event loop."""

    def _run():
        return asyncio.run(
            gate.evaluate(
                action_type=action_type,
                content=content,
                context=context,
            )
        )

    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return _run()
    return _executor.submit(_run).result()


def permit_outbound(
    action_type: Union[ActionType, str],
    content: str,
    channel: str,
    context: Optional[Dict[str, Any]] = None,
    gate: Optional[ActionGate] = None,
) -> OutboundDecision:
    """Approve or skip one outbound action.

    This never raises. A kill switch, an unknown action type, a non-pass
    gate decision, or any gate exception skips the action.
    """
    channel_name = (channel or "unknown").strip() or "unknown"
    raw_type = action_type.value if isinstance(action_type, ActionType) else str(action_type)

    if outbound_kill_switch_enabled():
        decision = OutboundDecision(
            allowed=False,
            score=None,
            reason=f"{OUTBOUND_KILL_SWITCH_ENV} is enabled; all outbound actions are paused",
            action_type=raw_type,
            channel=channel_name,
            decision="paused",
        )
        _log_skip(decision)
        return decision

    try:
        resolved = _coerce_action_type(action_type)
    except ValueError:
        decision = OutboundDecision(
            allowed=False,
            score=None,
            reason=f"unknown action type {raw_type!r}",
            action_type=raw_type,
            channel=channel_name,
            decision="error",
        )
        _log_skip(decision)
        return decision

    merged: Dict[str, Any] = {"channel": channel_name, "platform": channel_name}
    if context:
        merged.update(context)

    try:
        active_gate = gate if gate is not None else get_action_gate()
        result = _evaluate_sync(active_gate, resolved, content or "", merged)
        score = float(result.value_score.total_score)
        reason = result.reason or result.decision.value
        decision = OutboundDecision(
            allowed=result.decision == GateDecision.PASS,
            score=score,
            reason=reason,
            action_type=resolved.value,
            channel=channel_name,
            decision=result.decision.value,
        )
    except Exception as exc:
        decision = OutboundDecision(
            allowed=False,
            score=None,
            reason=f"gate error: {type(exc).__name__}: {exc}",
            action_type=resolved.value,
            channel=channel_name,
            decision="error",
        )
        _log_skip(decision)
        return decision

    if decision.allowed:
        logger.info(
            "Permitted outbound action channel=%s type=%s score=%s reason=%s",
            decision.channel,
            decision.action_type,
            _score_label(decision.score),
            decision.reason,
        )
    else:
        _log_skip(decision)
    return decision
