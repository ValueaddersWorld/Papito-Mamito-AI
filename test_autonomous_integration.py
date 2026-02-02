"""
PAPITO MAMITO AI - INTEGRATION TEST
===================================
Validates that all autonomous components work together.

Run this script to verify your installation:
    python test_autonomous_integration.py

© 2026 Value Adders World - Entertainment Division
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timezone

# Add project to path
sys.path.insert(0, str(Path(__file__).parent / "apps" / "papito_core" / "src"))

# Test results tracking
results = {
    "passed": 0,
    "failed": 0,
    "tests": []
}


def test(name):
    """Decorator to track test results."""
    def decorator(func):
        async def wrapper():
            print(f"\n🧪 Testing: {name}...")
            try:
                await func() if asyncio.iscoroutinefunction(func) else func()
                print(f"   ✅ PASSED: {name}")
                results["passed"] += 1
                results["tests"].append({"name": name, "status": "passed"})
            except Exception as e:
                print(f"   ❌ FAILED: {name}")
                print(f"      Error: {e}")
                results["failed"] += 1
                results["tests"].append({"name": name, "status": "failed", "error": str(e)})
        return wrapper
    return decorator


# ============================================
# PHASE 1 TESTS: Real-Time Event System
# ============================================

@test("Event Dispatcher - Import")
def test_event_dispatcher_import():
    from papito_core.realtime import EventDispatcher, Event, EventType, EventPriority
    assert EventDispatcher is not None
    assert EventType.MENTION is not None


@test("Event Dispatcher - Create and Register Handler")
async def test_event_dispatcher_handler():
    from papito_core.realtime import EventDispatcher, Event, EventType
    
    dispatcher = EventDispatcher()
    handler_called = False
    
    @dispatcher.on(EventType.MENTION)
    async def handle_mention(event):
        nonlocal handler_called
        handler_called = True
        return "handled"
    
    event = Event(
        event_type=EventType.MENTION,
        content="Test mention",
        user_name="tester",
    )
    
    await dispatcher.dispatch(event)
    await asyncio.sleep(0.1)  # Allow handler to run
    assert handler_called, "Handler was not called"


@test("Webhook Server - Import")
def test_webhook_server_import():
    from papito_core.realtime.webhook_server import webhook_app
    assert webhook_app is not None


@test("Heartbeat Daemon - Import and Create")
def test_heartbeat_import():
    from papito_core.realtime import HeartbeatDaemon, HealthStatus
    
    daemon = HeartbeatDaemon()
    assert daemon is not None
    assert HealthStatus.HEALTHY is not None


@test("X Stream - Import")
def test_x_stream_import():
    from papito_core.realtime.x_stream import XStreamListener, XMentionPoller
    assert XStreamListener is not None
    assert XMentionPoller is not None


# ============================================
# PHASE 2 TESTS: Value Score Intelligence
# ============================================

@test("Value Score Calculator - Import and Create")
def test_value_score_import():
    from papito_core.intelligence import ValueScoreCalculator, PillarID, ActionType
    
    calculator = ValueScoreCalculator()
    assert calculator is not None
    assert len(PillarID) == 8  # 8 pillars


@test("Value Score Calculator - Calculate Score")
async def test_value_score_calculate():
    from papito_core.intelligence import ValueScoreCalculator, ActionType
    
    calculator = ValueScoreCalculator()
    
    score = await calculator.calculate(
        action_type=ActionType.REPLY,
        content="Great vibes! Love the music! 🔥",
        context={"user_name": "fan", "hour_of_day": 14}
    )
    
    assert score is not None
    assert 0 <= score.total_score <= 100
    assert score.threshold > 0


@test("Action Gate - Import and Evaluate")
async def test_action_gate():
    from papito_core.intelligence import ActionGate, GateDecision, ActionType
    
    gate = ActionGate()
    
    result = await gate.evaluate(
        action_type=ActionType.REPLY,
        content="This is a thoughtful response with value!",
        context={"user_name": "fan"}
    )
    
    assert result is not None
    assert result.decision in [GateDecision.PASS, GateDecision.BLOCK, GateDecision.DEFER, GateDecision.ESCALATE]


@test("Action Learner - Import and Create")
def test_action_learner():
    from papito_core.intelligence import ActionLearner, ActionOutcome
    
    learner = ActionLearner()
    stats = learner.get_stats()
    
    assert learner is not None
    assert "total_records" in stats


@test("Value Gated Handlers - Import")
def test_value_gated_handlers():
    from papito_core.intelligence import ValueGatedHandlers, create_value_gated_handlers
    
    handlers = create_value_gated_handlers()
    assert handlers is not None


@test("Value Metrics Dashboard - Import and Create")
def test_value_metrics():
    from papito_core.intelligence import ValueMetricsDashboard, get_metrics_dashboard
    
    dashboard = get_metrics_dashboard()
    overview = dashboard.get_overview()
    
    assert dashboard is not None
    assert "status" in overview


# ============================================
# PHASE 3 TESTS: Multi-Platform Autonomy
# ============================================

@test("Platform Base - Import")
def test_platform_base():
    from papito_core.platforms import Platform, PlatformEvent, PlatformAction, PlatformCapability
    
    assert Platform.X is not None
    assert Platform.DISCORD is not None
    assert Platform.YOUTUBE is not None


@test("Platform Event - Create")
def test_platform_event():
    from papito_core.platforms import Platform, PlatformEvent
    from papito_core.platforms.base import EventCategory
    
    event = PlatformEvent(
        platform=Platform.X,
        category=EventCategory.MENTION,
        content="Test content",
        user_name="tester",
    )
    
    assert event.event_id is not None
    assert event.platform == Platform.X


@test("Cross-Platform Coordinator - Import and Create")
def test_coordinator():
    from papito_core.platforms import CrossPlatformCoordinator, get_coordinator
    
    coordinator = get_coordinator()
    stats = coordinator.get_stats()
    
    assert coordinator is not None
    assert "running" in stats


@test("Platform Adapters - Import")
def test_adapters_import():
    from papito_core.platforms.adapters import XAdapter, DiscordAdapter, YouTubeAdapter
    
    assert XAdapter is not None
    assert DiscordAdapter is not None
    assert YouTubeAdapter is not None


@test("Mock Adapter - Full Flow")
async def test_mock_adapter_flow():
    from papito_core.platforms.base import MockPlatformAdapter, PlatformConfig, Platform, PlatformAction
    
    config = PlatformConfig(platform=Platform.CUSTOM)
    adapter = MockPlatformAdapter(config, "test_platform")
    
    # Connect
    connected = await adapter.connect()
    assert connected, "Failed to connect"
    
    # Execute action
    action = PlatformAction(
        action_type="post",
        content="Test post",
    )
    result = await adapter.execute(action)
    
    assert result.success, "Action failed"
    
    # Disconnect
    await adapter.disconnect()
    assert not adapter.is_connected


# ============================================
# INTEGRATION TESTS
# ============================================

@test("Full Pipeline - Event → Value Score → Gate")
async def test_full_pipeline():
    from papito_core.realtime import EventDispatcher, Event, EventType
    from papito_core.intelligence import ActionGate, ActionType, GateDecision
    
    dispatcher = EventDispatcher()
    gate = ActionGate()
    
    gate_results = []
    
    @dispatcher.on(EventType.MENTION)
    async def handle_mention(event):
        # Simulate generating a response
        response = f"Thanks @{event.user_name}! Appreciate the love! 🎵"
        
        # Gate the response
        result = await gate.evaluate(
            action_type=ActionType.REPLY,
            content=response,
            context={"user_name": event.user_name}
        )
        
        gate_results.append(result)
        return result
    
    # Dispatch test event
    event = Event(
        event_type=EventType.MENTION,
        content="@papito you're the best!",
        user_name="superfan",
    )
    
    await dispatcher.dispatch(event)
    await asyncio.sleep(0.2)
    
    assert len(gate_results) > 0, "No gate results"
    assert gate_results[0].value_score is not None


@test("Multi-Platform Event Routing")
async def test_multiplatform_routing():
    from papito_core.platforms import CrossPlatformCoordinator, Platform, PlatformEvent
    from papito_core.platforms.base import EventCategory, MockPlatformAdapter, PlatformConfig
    
    coordinator = CrossPlatformCoordinator()
    
    # Register mock adapter
    config = PlatformConfig(platform=Platform.CUSTOM)
    adapter = MockPlatformAdapter(config, "test")
    coordinator.register_adapter(adapter)
    
    events_received = []
    
    @coordinator.on_event
    async def handle_event(event):
        events_received.append(event)
    
    # Inject test event
    test_event = PlatformEvent(
        platform=Platform.CUSTOM,
        category=EventCategory.MENTION,
        content="Test cross-platform",
        user_name="tester",
    )
    
    await adapter.inject_event(test_event)
    await asyncio.sleep(0.1)
    
    assert len(events_received) > 0, "Event not routed"


# ============================================
# RUN ALL TESTS
# ============================================

async def run_all_tests():
    """Run all integration tests."""
    print("=" * 60)
    print("PAPITO MAMITO AI - INTEGRATION TEST SUITE")
    print("=" * 60)
    print(f"Started at: {datetime.now(timezone.utc).isoformat()}")
    
    tests = [
        # Phase 1
        test_event_dispatcher_import,
        test_event_dispatcher_handler,
        test_webhook_server_import,
        test_heartbeat_import,
        test_x_stream_import,
        
        # Phase 2
        test_value_score_import,
        test_value_score_calculate,
        test_action_gate,
        test_action_learner,
        test_value_gated_handlers,
        test_value_metrics,
        
        # Phase 3
        test_platform_base,
        test_platform_event,
        test_coordinator,
        test_adapters_import,
        test_mock_adapter_flow,
        
        # Integration
        test_full_pipeline,
        test_multiplatform_routing,
    ]
    
    for test_func in tests:
        try:
            await test_func()
        except Exception as e:
            print(f"   ❌ Test error: {e}")
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"✅ Passed: {results['passed']}")
    print(f"❌ Failed: {results['failed']}")
    print(f"📊 Total:  {results['passed'] + results['failed']}")
    
    if results['failed'] == 0:
        print("\n🎉 ALL TESTS PASSED! Papito is ready for autonomous operation!")
    else:
        print("\n⚠️ Some tests failed. Check the errors above.")
        print("\nFailed tests:")
        for test in results['tests']:
            if test['status'] == 'failed':
                print(f"  - {test['name']}: {test.get('error', 'Unknown error')}")
    
    return results['failed'] == 0


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
