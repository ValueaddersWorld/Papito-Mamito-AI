"""Tests for Phase 4 monitoring module."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from papito_core.monitoring import (
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


class TestHealthStatus:
    """Tests for HealthStatus dataclass."""
    
    def test_create_health_status(self):
        """Test creating health status."""
        status = HealthStatus(
            component="firebase",
            healthy=True,
            last_check=datetime.utcnow(),
            message="Connected",
            response_time_ms=150.5,
        )
        assert status.component == "firebase"
        assert status.healthy is True
    
    def test_to_dict(self):
        """Test serialization."""
        status = HealthStatus(
            component="test",
            healthy=True,
            last_check=datetime.utcnow(),
        )
        d = status.to_dict()
        assert d["component"] == "test"
        assert d["healthy"] is True


class TestAlert:
    """Tests for Alert dataclass."""
    
    def test_create_alert(self):
        """Test creating an alert."""
        alert = Alert(
            id="test_123",
            alert_type=AlertType.ENGAGEMENT_DROP,
            severity=AlertSeverity.WARNING,
            title="Engagement Drop",
            message="Engagement dropped 20%",
        )
        assert alert.id == "test_123"
        assert alert.severity == AlertSeverity.WARNING
    
    def test_alert_to_dict(self):
        """Test alert serialization."""
        alert = Alert(
            id="test",
            alert_type=AlertType.PLATFORM_ERROR,
            severity=AlertSeverity.ERROR,
            title="Test",
            message="Test message",
            platform="instagram",
        )
        d = alert.to_dict()
        assert d["alert_type"] == "platform_error"
        assert d["severity"] == "error"
        assert d["platform"] == "instagram"


class TestHealthChecker:
    """Tests for HealthChecker."""
    
    @pytest.fixture
    def checker(self):
        return HealthChecker(check_interval_seconds=60)
    
    def test_initialization(self, checker):
        """Test checker initialization."""
        assert checker.check_interval == 60
        assert len(checker.COMPONENTS) >= 3
    
    @pytest.mark.asyncio
    async def test_check_component(self, checker):
        """Test checking a single component."""
        status = await checker.check_component("firebase")
        assert status.component == "firebase"
        assert isinstance(status, HealthStatus)
    
    def test_get_status(self, checker):
        """Test getting status summary."""
        status = checker.get_status()
        assert "overall" in status
        assert "healthy_components" in status
    
    def test_alert_callback(self):
        """Test alert callback is called on failures."""
        alerts = []
        
        def callback(alert):
            alerts.append(alert)
        
        checker = HealthChecker(alert_callback=callback)
        
        # Simulate 3 consecutive failures
        for _ in range(3):
            checker._consecutive_failures["test_component"] = 3
            checker._generate_alert(
                "test_component",
                HealthStatus(
                    component="test_component",
                    healthy=False,
                    last_check=datetime.utcnow(),
                    message="Test failure"
                )
            )
        
        assert len(alerts) == 3


class TestAlertManager:
    """Tests for AlertManager."""
    
    @pytest.fixture
    def manager(self):
        return AlertManager()
    
    def test_create_alert(self, manager):
        """Test creating an alert."""
        alert = manager.create_alert(
            alert_type=AlertType.API_FAILURE,
            severity=AlertSeverity.ERROR,
            title="API Failed",
            message="OpenAI API returned error",
        )
        assert alert.id in manager._alerts
        assert len(manager._alert_history) == 1
    
    def test_acknowledge_alert(self, manager):
        """Test acknowledging an alert."""
        alert = manager.create_alert(
            alert_type=AlertType.RATE_LIMIT,
            severity=AlertSeverity.WARNING,
            title="Rate Limited",
            message="Instagram rate limit reached",
        )
        
        result = manager.acknowledge(alert.id, "admin")
        assert result is True
        assert alert.acknowledged is True
        assert alert.acknowledged_by == "admin"
    
    def test_resolve_alert(self, manager):
        """Test resolving an alert."""
        alert = manager.create_alert(
            alert_type=AlertType.ENGAGEMENT_DROP,
            severity=AlertSeverity.INFO,
            title="Test",
            message="Test",
        )
        
        result = manager.resolve(alert.id)
        assert result is True
        assert alert.resolved is True
    
    def test_get_active_alerts(self, manager):
        """Test getting active alerts."""
        # Create some alerts
        alert1 = manager.create_alert(
            AlertType.API_FAILURE, AlertSeverity.ERROR, "Test 1", "Msg"
        )
        alert2 = manager.create_alert(
            AlertType.RATE_LIMIT, AlertSeverity.WARNING, "Test 2", "Msg"
        )
        
        # Resolve one
        manager.resolve(alert1.id)
        
        active = manager.get_active_alerts()
        assert len(active) == 1
        assert active[0].id == alert2.id
    
    def test_get_alert_summary(self, manager):
        """Test alert summary."""
        manager.create_alert(
            AlertType.API_FAILURE, AlertSeverity.ERROR, "Error", "Msg"
        )
        manager.create_alert(
            AlertType.RATE_LIMIT, AlertSeverity.WARNING, "Warning", "Msg"
        )
        
        summary = manager.get_alert_summary()
        assert summary["total_active"] == 2
        assert summary["by_severity"]["error"] == 1
        assert summary["by_severity"]["warning"] == 1


class TestEscalationManager:
    """Tests for EscalationManager."""
    
    @pytest.fixture
    def alert_manager(self):
        return AlertManager()
    
    @pytest.fixture
    def escalation_manager(self, alert_manager):
        return EscalationManager(alert_manager)
    
    def test_default_rules(self, escalation_manager):
        """Test default escalation rules are added."""
        assert len(escalation_manager._rules) >= 3
    
    def test_check_escalation_negative_vip(self, escalation_manager):
        """Test escalation for negative VIP sentiment."""
        context = {
            "sentiment": "very_negative",
            "fan_tier": "super_fan",
        }
        
        rule = escalation_manager.check_escalation(context)
        assert rule is not None
        assert rule.name == "negative_sentiment_vip"
    
    def test_check_escalation_engagement_drop(self, escalation_manager):
        """Test escalation for major engagement drop."""
        context = {"engagement_change": -60}
        
        rule = escalation_manager.check_escalation(context)
        assert rule is not None
        assert "engagement" in rule.name
    
    def test_check_escalation_no_match(self, escalation_manager):
        """Test no escalation for normal context."""
        context = {"sentiment": "positive", "engagement_change": 5}
        
        rule = escalation_manager.check_escalation(context)
        assert rule is None
    
    def test_add_custom_rule(self, escalation_manager):
        """Test adding custom escalation rule."""
        initial_count = len(escalation_manager._rules)
        
        escalation_manager.add_rule(EscalationRule(
            name="custom_rule",
            condition="Custom condition",
            check_fn=lambda ctx: ctx.get("custom") is True,
            escalation_channel="telegram",
            priority=10,
        ))
        
        assert len(escalation_manager._rules) == initial_count + 1
        # Should be first due to high priority
        assert escalation_manager._rules[0].name == "custom_rule"


class TestWebhookHandler:
    """Tests for WebhookHandler."""
    
    @pytest.fixture
    def handler(self):
        return WebhookHandler(secret_key="test_secret")
    
    def test_register_handler(self, handler):
        """Test registering event handler."""
        def my_handler(payload):
            return {"processed": True}
        
        handler.register_handler("test_event", my_handler)
        assert "test_event" in handler._handlers
        assert len(handler._handlers["test_event"]) == 1
    
    def test_verify_signature_valid(self, handler):
        """Test valid signature verification."""
        import hmac
        import hashlib
        
        payload = b'{"test": "data"}'
        signature = hmac.new(
            b"test_secret",
            payload,
            hashlib.sha256
        ).hexdigest()
        
        assert handler.verify_signature(payload, signature) is True
    
    def test_verify_signature_invalid(self, handler):
        """Test invalid signature rejection."""
        payload = b'{"test": "data"}'
        signature = "invalid_signature"
        
        assert handler.verify_signature(payload, signature) is False
    
    def test_no_secret_always_valid(self):
        """Test no verification when no secret configured."""
        handler = WebhookHandler(secret_key=None)
        assert handler.verify_signature(b"any", "any") is True
    
    @pytest.mark.asyncio
    async def test_handle_event(self, handler):
        """Test handling an event."""
        results = []
        
        def sync_handler(payload):
            results.append(("sync", payload))
            return "sync_result"
        
        async def async_handler(payload):
            results.append(("async", payload))
            return "async_result"
        
        handler.register_handler("test", sync_handler)
        handler.register_handler("test", async_handler)
        
        output = await handler.handle_event("test", {"key": "value"})
        
        assert len(results) == 2
        assert output == ["sync_result", "async_result"]
