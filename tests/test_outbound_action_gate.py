"""Outbound actions from the live worker must pass ActionGate or be skipped."""

import ast
import asyncio
import logging
import os
import subprocess
import sys
from pathlib import Path

import pytest

from papito_core.intelligence.action_gate import ActionGate, GateDecision, GateResult
from papito_core.intelligence.outbound_guard import (
    OUTBOUND_KILL_SWITCH_ENV,
    permit_outbound,
)
from papito_core.intelligence.value_score import (
    ActionType,
    ActionValueScore,
    PillarID,
    PillarScore,
)

ROOT = Path(__file__).resolve().parents[1]
WORKER = ROOT / "scripts" / "papito_autonomous_forever.py"
PACKAGE_SRC = ROOT / "apps" / "papito_core" / "src"

PILLARS = (
    ("awareness", PillarID.AWARENESS),
    ("define", PillarID.DEFINE),
    ("devise", PillarID.DEVISE),
    ("validate", PillarID.VALIDATE),
    ("act_upon", PillarID.ACT_UPON),
    ("learn", PillarID.LEARN),
    ("understand", PillarID.UNDERSTAND),
    ("evolve", PillarID.EVOLVE),
)


class FixedCalculator:
    def __init__(self, pillar_score: float, threshold: float = 70.0):
        self.pillar_score = pillar_score
        self.threshold = threshold

    async def calculate(self, action_type, content, context=None, action_id=None):
        pillars = {
            name: PillarScore(pillar=pillar, score=self.pillar_score, weight=1.0)
            for name, pillar in PILLARS
        }
        return ActionValueScore(
            action_id=action_id or "test-action",
            action_type=action_type,
            content=content,
            threshold=self.threshold,
            context=context or {},
            **pillars,
        )


class ExplodingGate:
    def __init__(self):
        self.calls = 0

    async def evaluate(self, **kwargs):
        self.calls += 1
        raise RuntimeError("scorer unavailable")


def _gate(pillar_score: float, threshold: float = 70.0) -> ActionGate:
    return ActionGate(
        calculator=FixedCalculator(pillar_score, threshold),
        enable_learning=False,
    )


def _messages(caplog, level=logging.WARNING):
    return [record.getMessage() for record in caplog.records if record.levelno >= level]


@pytest.fixture
def quiet_kill_switch(monkeypatch):
    monkeypatch.delenv(OUTBOUND_KILL_SWITCH_ENV, raising=False)


def test_low_value_action_is_skipped_with_score_and_reason(caplog, quiet_kill_switch):
    caplog.set_level(logging.WARNING, logger="papito.outbound")

    decision = permit_outbound(
        "tweet",
        "buy now click here",
        "x",
        gate=_gate(40),
    )

    assert decision.allowed is False
    assert decision.score == pytest.approx(40.0)
    assert decision.decision == GateDecision.BLOCK.value
    assert "below threshold" in decision.reason
    skipped = decision.as_skip()
    assert skipped["success"] is False
    assert skipped["skipped"] is True
    assert skipped["score"] == pytest.approx(40.0)

    message = _messages(caplog)[-1]
    assert "Skipped outbound action" in message
    assert "channel=x" in message
    assert "type=tweet" in message
    assert "score=40.0" in message
    assert decision.reason in message


def test_passing_score_is_allowed(caplog, quiet_kill_switch):
    caplog.set_level(logging.INFO, logger="papito.outbound")

    decision = permit_outbound(
        ActionType.TWEET,
        "The drums leave space so the lesson can land.",
        "x",
        context={"goal": "Share a production note"},
        gate=_gate(95),
    )

    assert decision.allowed is True
    assert decision.score == pytest.approx(95.0)
    assert decision.decision == GateDecision.PASS.value
    assert "Permitted outbound action" in _messages(caplog, logging.INFO)[-1]
    assert "score=95.0" in _messages(caplog, logging.INFO)[-1]


def test_deferred_high_scrutiny_action_is_not_sent(caplog, quiet_kill_switch):
    caplog.set_level(logging.WARNING, logger="papito.outbound")

    decision = permit_outbound(
        ActionType.DM,
        "A private note that is only moderately grounded.",
        "telegram",
        gate=_gate(70),
    )

    assert decision.allowed is False
    assert decision.score == pytest.approx(70.0)
    assert decision.decision == GateDecision.DEFER.value
    message = _messages(caplog)[-1]
    assert "score=70.0" in message
    assert "reason=" in message


def test_gate_error_fails_closed(caplog, quiet_kill_switch):
    caplog.set_level(logging.WARNING, logger="papito.outbound")
    gate = ExplodingGate()

    decision = permit_outbound("reply", "Still here.", "moltbook", gate=gate)

    assert gate.calls == 1
    assert decision.allowed is False
    assert decision.score is None
    assert decision.decision == "error"
    assert decision.reason.startswith("gate error: RuntimeError:")
    message = _messages(caplog)[-1]
    assert "score=n/a" in message
    assert decision.reason in message


def test_unknown_action_type_fails_closed(caplog, quiet_kill_switch):
    caplog.set_level(logging.WARNING, logger="papito.outbound")

    decision = permit_outbound("not-an-action", "hello", "x", gate=ExplodingGate())

    assert decision.allowed is False
    assert decision.score is None
    assert "unknown action type" in decision.reason
    assert "score=n/a" in _messages(caplog)[-1]


@pytest.mark.parametrize("enabled", ["1", "true", "yes", "on", " TRUE "])
def test_kill_switch_pauses_without_calling_the_gate(monkeypatch, caplog, enabled):
    caplog.set_level(logging.WARNING, logger="papito.outbound")
    monkeypatch.setenv(OUTBOUND_KILL_SWITCH_ENV, enabled)
    gate = ExplodingGate()

    decision = permit_outbound("dm", "private update", "telegram", gate=gate)

    assert gate.calls == 0
    assert decision.allowed is False
    assert decision.score is None
    assert decision.decision == "paused"
    assert OUTBOUND_KILL_SWITCH_ENV in decision.reason
    message = _messages(caplog)[-1]
    assert "score=n/a" in message
    assert decision.reason in message


def test_kill_switch_off_values_do_not_pause(monkeypatch, quiet_kill_switch):
    monkeypatch.setenv(OUTBOUND_KILL_SWITCH_ENV, "0")

    decision = permit_outbound("like", "upvote post-1", "moltbook", gate=_gate(95))

    assert decision.allowed is True


def test_permit_outbound_works_from_a_running_event_loop(quiet_kill_switch):
    async def _check():
        return permit_outbound("follow", "follow a listener", "moltbook", gate=_gate(90))

    decision = asyncio.run(_check())

    assert decision.allowed is True
    assert decision.score == pytest.approx(90.0)


def _direct_calls(node):
    """Calls in this function, ignoring nested function and class bodies."""
    found = []
    for child in ast.iter_child_nodes(node):
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        if isinstance(child, ast.Call):
            found.append(child)
        found.extend(_direct_calls(child))
    return found


def test_worker_gates_every_outbound_send():
    source = WORKER.read_text(encoding="utf-8")
    tree = ast.parse(source)
    send_names = {"post", "create_tweet", "reply_text"}
    offenders = []

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        guard_lines = []
        send_lines = []
        for child in _direct_calls(node):
            func = child.func
            name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")
            if name == "_outbound_block":
                guard_lines.append(child.lineno)
            elif name in send_names:
                send_lines.append((name, child.lineno))
        for name, lineno in send_lines:
            if not any(guard_line < lineno for guard_line in guard_lines):
                offenders.append(f"{node.name}:{lineno} {name}")

    assert offenders == []
    assert "from papito_core.intelligence.outbound_guard import permit_outbound" in source
    assert "papito_core.intelligence.action_gate" not in source
    assert "import action_gate" not in source


def test_outbound_guard_imports_without_fastapi(tmp_path):
    code = """
import importlib.abc
import sys

class NoFastAPI(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] == 'fastapi':
            raise ModuleNotFoundError('Optional web dependency: ' + fullname)

sys.meta_path.insert(0, NoFastAPI())
from papito_core.intelligence.outbound_guard import permit_outbound, OUTBOUND_KILL_SWITCH_ENV
from papito_core.intelligence import ActionGate, GateDecision
assert permit_outbound and OUTBOUND_KILL_SWITCH_ENV and ActionGate and GateDecision
assert 'fastapi' not in sys.modules
"""
    env = {**os.environ, "PYTHONPATH": str(PACKAGE_SRC), "PYTHON_DOTENV_DISABLED": "1"}
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr


def test_handler_exports_stay_lazy_and_importable():
    import papito_core.intelligence as intelligence

    handlers = intelligence.ValueGatedHandlers
    assert handlers.__name__ == "ValueGatedHandlers"


def test_gate_result_shape_used_by_the_guard():
    """The guard treats only an explicit pass as permission to send."""
    assert GateDecision.PASS.value == "pass"
    assert {item.value for item in GateDecision} >= {"pass", "block", "defer", "escalate"}
    result = GateResult(
        decision=GateDecision.BLOCK,
        action_id="a",
        action_type=ActionType.REPLY,
        content="no",
        value_score=ActionValueScore(
            action_id="a",
            action_type=ActionType.REPLY,
            content="no",
            threshold=70,
        ),
        reason="too thin",
    )
    assert result.value_score.total_score == 0
    assert result.value_score.should_execute is False
