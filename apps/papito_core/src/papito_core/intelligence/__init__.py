"""PAPITO MAMITO AI - INTELLIGENCE MODULE"""

from .content_generator import PapitoContext, WisdomLibrary, IntelligentContentGenerator
from .value_score import (
    PillarID,
    ActionType,
    PillarScore,
    ActionValueScore,
    ValueScoreCalculator,
    get_value_calculator,
)
from .action_gate import GateDecision, GateResult, ActionGate, get_action_gate
from .action_learning import (
    ActionOutcome,
    ActionRecord,
    LearningInsight,
    ActionLearner,
    get_action_learner,
)
from .value_metrics import ValueMetricsDashboard, get_metrics_dashboard, create_metrics_routes

# Value-gated handlers import the realtime webhook stack, which needs FastAPI.
# The live Railway worker does not install that stack, so these stay lazy.
_HANDLER_EXPORTS = {
    "HandlerResult",
    "ValueGatedHandlers",
    "create_value_gated_handlers",
}

__all__ = [
    "PapitoContext",
    "WisdomLibrary",
    "IntelligentContentGenerator",
    "PillarID",
    "ActionType",
    "PillarScore",
    "ActionValueScore",
    "ValueScoreCalculator",
    "get_value_calculator",
    "GateDecision",
    "GateResult",
    "ActionGate",
    "get_action_gate",
    "ActionOutcome",
    "ActionRecord",
    "LearningInsight",
    "ActionLearner",
    "get_action_learner",
    "HandlerResult",
    "ValueGatedHandlers",
    "create_value_gated_handlers",
    "ValueMetricsDashboard",
    "get_metrics_dashboard",
    "create_metrics_routes",
]


def __getattr__(name: str):
    if name not in _HANDLER_EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    from .value_gated_handlers import (
        HandlerResult,
        ValueGatedHandlers,
        create_value_gated_handlers,
    )

    exports = {
        "HandlerResult": HandlerResult,
        "ValueGatedHandlers": ValueGatedHandlers,
        "create_value_gated_handlers": create_value_gated_handlers,
    }
    globals().update(exports)
    return exports[name]
