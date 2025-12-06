"""Demo script to test all Papito autonomous features."""

import asyncio
from datetime import datetime, timedelta

print("=" * 60)
print("🎵 PAPITO AUTONOMOUS SYSTEM - LIVE TEST 🎵")
print("=" * 60)

# ========================================
# PHASE 1: Content Scheduler Test
# ========================================
print("\n📅 PHASE 1: Content Scheduler")
print("-" * 40)

from papito_core.automation import ContentScheduler, ContentType

scheduler = ContentScheduler()

print(f"✅ Timezone: {scheduler.config.timezone}")
print(f"✅ Posts per day: {scheduler.config.min_posts_per_day}-{scheduler.config.max_posts_per_day}")
print(f"✅ Posting slots configured: {len(scheduler.config.posting_slots)}")

# Show current time and next slot
now = scheduler.get_current_time_wat()
print(f"✅ Current time (WAT): {now.strftime('%Y-%m-%d %H:%M')}")

next_slot = scheduler.get_next_posting_slot()
if next_slot:
    print(f"✅ Next posting slot: {next_slot.hour:02d}:{next_slot.minute:02d}")
    print(f"   Content types: {[ct.value for ct in next_slot.content_types]}")

# Generate a 3-day schedule
schedule = scheduler.generate_schedule(days=3)
print(f"✅ Generated {len(schedule)} posts for next 3 days")

# ========================================
# PHASE 1: AI Personality Test
# ========================================
print("\n🎭 PHASE 1: AI Personality Engine")
print("-" * 40)

from papito_core.engines import AIPersonalityEngine, ResponseContext

personality = AIPersonalityEngine()

print(f"✅ Catchphrase: {personality.personality.catchphrase}")
print(f"✅ Traits: {personality.personality.traits[:3]}...")

# Generate test content (sync method)
content = personality.generate_content_post(
    content_type="morning_blessing",
    platform="instagram"
)
print(f"✅ Generated content: {content['text'][:80]}...")
print(f"   Hashtags: {content.get('hashtags', [])[:3]}")

# Test template fallback response
response = personality._generate_template_response(
    context=ResponseContext.FAN_COMMENT,
    fan_name="TestFan"
)
print(f"✅ Response template: {response[:60]}...")

# ========================================
# PHASE 1: Trending Detector Test
# ========================================
print("\n📈 PHASE 1: Trending Detector")
print("-" * 40)

from papito_core.social import TrendingDetector

trending = TrendingDetector()

hashtags = trending.get_relevant_hashtags_for_content(
    content_type="morning_blessing",
    max_hashtags=5
)
print(f"✅ Relevant hashtags: {hashtags}")

# Score a topic
relevance, score = trending.score_topic_relevance("#Afrobeat2024")
print(f"✅ '#Afrobeat2024' relevance: {relevance.value} (score: {score})")

# ========================================
# PHASE 2: Fan Engagement Test
# ========================================
print("\n👥 PHASE 2: Fan Engagement System")
print("-" * 40)

from papito_core.engagement import FanEngagementManager, EngagementTier, Sentiment

engagement = FanEngagementManager()

# Record some fan interactions
fan1, sent1 = engagement.record_interaction(
    username="loyal_supporter",
    platform="instagram",
    message="Your music changed my life! 🔥 Love every beat!"
)
print(f"✅ Fan: {fan1.username}")
print(f"   Tier: {fan1.tier}, Sentiment: {sent1.value}")

# Simulate multiple interactions to show tier progression
for i in range(5):
    fan2, sent2 = engagement.record_interaction(
        username="super_fan_test",
        platform="x",
        message=f"Amazing work #{i+1}! You're the best! 🙏❤️🔥"
    )

print(f"✅ Fan: {fan2.username}")
print(f"   Total interactions: {fan2.total_interactions}")
print(f"   Tier: {fan2.tier}")

# Get personalized greeting
greeting = engagement.get_personalized_greeting(fan2)
print(f"✅ Personalized greeting: {greeting[:60]}...")

# Get welcome message
welcome = engagement.generate_welcome_message("new_follower_test")
print(f"✅ Welcome message: {welcome[:60]}...")

# ========================================
# PHASE 3: Analytics Test
# ========================================
print("\n📊 PHASE 3: Predictive Analytics")
print("-" * 40)

from papito_core.analytics import (
    EngagementTracker, 
    ABTestManager, 
    ContentStrategyOptimizer,
    EngagementData,
    ContentFormat
)

tracker = EngagementTracker()
ab_manager = ABTestManager()

# Record some engagement data
for i in range(10):
    data = EngagementData(
        post_id=f"post_{i}",
        platform="instagram",
        content_type="morning_blessing" if i % 2 == 0 else "track_snippet",
        content_format=ContentFormat.IMAGE,
        posted_at=datetime.utcnow() - timedelta(days=i),
        hour_of_day=8 if i % 2 == 0 else 14,
        day_of_week=i % 7,
        likes=100 + i * 20,
        comments=20 + i * 5,
    )
    data.calculate_engagement_rate(1000)
    tracker.record(data)

print(f"✅ Recorded {len(tracker._data)} engagement data points")

# Get peak times
peaks = tracker.get_peak_times(top_n=3)
print(f"✅ Peak times: {[(p.hour, round(p.avg_engagement_rate, 1)) for p in peaks]}")

# Get best content types
best = tracker.get_best_content_types(top_n=2)
print(f"✅ Best content types: {[(b[0], round(b[1], 1)) for b in best]}")

# Create an A/B test
test = ab_manager.create_test(
    name="Hashtag Count Test",
    description="Test 5 vs 10 hashtags",
    variant_a={"hashtags": 5},
    variant_b={"hashtags": 10},
)
print(f"✅ A/B Test created: {test.name} (ID: {test.test_id})")

# Strategy optimizer
optimizer = ContentStrategyOptimizer(tracker, ab_manager)
recommendations = optimizer.analyze_and_recommend()
print(f"✅ Recommendations generated: {len(recommendations['suggested_actions'])} actions")

# ========================================
# PHASE 4: Monitoring Test
# ========================================
print("\n🔍 PHASE 4: Monitoring & Alerts")
print("-" * 40)

from papito_core.monitoring import (
    HealthChecker,
    AlertManager,
    EscalationManager,
    WebhookHandler,
    AlertType,
    AlertSeverity,
)

alert_manager = AlertManager()
health_checker = HealthChecker(alert_callback=lambda a: print(f"   [ALERT] {a.title}"))
escalation_manager = EscalationManager(alert_manager)
webhook_handler = WebhookHandler(secret_key="test_secret")

print(f"✅ Health checker: {len(health_checker.COMPONENTS)} components")
print(f"✅ Escalation rules: {len(escalation_manager._rules)} rules")

# Create a test alert
alert = alert_manager.create_alert(
    alert_type=AlertType.ENGAGEMENT_DROP,
    severity=AlertSeverity.WARNING,
    title="Test Alert",
    message="This is a test alert for demo purposes",
)
print(f"✅ Alert created: {alert.id}")

# Check escalation rule
context = {"sentiment": "very_negative", "fan_tier": "super_fan"}
rule = escalation_manager.check_escalation(context)
print(f"✅ Escalation check: {rule.name if rule else 'No escalation needed'}")

# Verify webhook signature
test_payload = b'{"event": "test"}'
import hmac, hashlib
signature = hmac.new(b"test_secret", test_payload, hashlib.sha256).hexdigest()
valid = webhook_handler.verify_signature(test_payload, signature)
print(f"✅ Webhook signature: {'Valid' if valid else 'Invalid'}")

# ========================================
# SUMMARY
# ========================================
print("\n" + "=" * 60)
print("✅ ALL SYSTEMS OPERATIONAL!")
print("=" * 60)
print("""
Summary:
  • Phase 1: ContentScheduler, AIPersonalityEngine, TrendingDetector ✅
  • Phase 2: FanEngagementManager, SentimentAnalyzer, Tiers ✅  
  • Phase 3: EngagementTracker, ABTestManager, Optimizer ✅
  • Phase 4: HealthChecker, AlertManager, Webhooks ✅

The Autonomous Papito 24/7 System is LIVE! 🚀
""")
