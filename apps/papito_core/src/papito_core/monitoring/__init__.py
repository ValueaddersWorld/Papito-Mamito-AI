"""Monitoring module for Papito Mamito.

Provides health checks, alerting, escalation,
and webhook handling for autonomous operation.
"""

from .health import (
    AlertSeverity,
    AlertType,
    HealthStatus,
    Alert,
    EscalationRule,
    HealthChecker,
    AlertManager,
    EscalationManager,
    WebhookHandler,
)

__all__ = [
    "AlertSeverity",
    "AlertType",
    "HealthStatus",
    "Alert",
    "EscalationRule",
    "HealthChecker",
    "AlertManager",
    "EscalationManager",
    "WebhookHandler",
]
