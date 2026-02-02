# PAPITO MAMITO AI - AUTONOMOUS AGENT BLUEPRINT

## Overview

This document serves as the complete blueprint for building truly autonomous AI agents following the **Value Adders** philosophy. Papito Mamito AI is the reference implementation - a music entertainment AI that operates across multiple platforms with genuine autonomy.

**Core Philosophy:** "Add value or don't act."

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        AUTONOMOUS AI AGENT                              │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    REAL-TIME EVENT SYSTEM                       │    │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            │    │
│  │  │ Event        │ │ Webhook      │ │ Heartbeat    │            │    │
│  │  │ Dispatcher   │ │ Server       │ │ Daemon       │            │    │
│  │  └──────────────┘ └──────────────┘ └──────────────┘            │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                   │                                     │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                  VALUE SCORE INTELLIGENCE                       │    │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            │    │
│  │  │ Value Score  │ │ Action       │ │ Action       │            │    │
│  │  │ Calculator   │ │ Gate         │ │ Learner      │            │    │
│  │  └──────────────┘ └──────────────┘ └──────────────┘            │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                   │                                     │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                  MULTI-PLATFORM LAYER                           │    │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            │    │
│  │  │ Platform     │ │ Cross-       │ │ Platform     │            │    │
│  │  │ Abstraction  │ │ Platform     │ │ Adapters     │            │    │
│  │  │              │ │ Coordinator  │ │              │            │    │
│  │  └──────────────┘ └──────────────┘ └──────────────┘            │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                   │                                     │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                      AI PERSONALITY                             │    │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            │    │
│  │  │ Personality  │ │ Content      │ │ Wisdom       │            │    │
│  │  │ Engine       │ │ Generator    │ │ Library      │            │    │
│  │  └──────────────┘ └──────────────┘ └──────────────┘            │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Real-Time Event System

The foundation of autonomy is **real-time awareness**. Without it, the agent is just a scheduler.

### Components

#### 1.1 Event Dispatcher (`realtime/event_dispatcher.py`)
Central hub that routes events to appropriate handlers.

```python
from papito_core.realtime import EventDispatcher, Event, EventType

dispatcher = EventDispatcher()

@dispatcher.on(EventType.MENTION)
async def handle_mention(event: Event):
    # Process mention in real-time
    pass

# Dispatch an event
await dispatcher.dispatch(Event(
    event_type=EventType.MENTION,
    content="@papito you're amazing!",
    user_name="fan123",
))
```

**Key Features:**
- Priority-based event queue
- Handler registration via decorators
- Event history tracking
- Async processing

#### 1.2 Webhook Server (`realtime/webhook_server.py`)
FastAPI server for external event ingestion.

```python
# Endpoints:
POST /webhooks/x/mentions     # X/Twitter mentions
POST /webhooks/x/trends       # Trending topics
POST /webhooks/music/release  # Music platform releases
POST /webhooks/custom         # Custom events
GET  /health                  # Health check
GET  /stats                   # Statistics
```

#### 1.3 Stream Listener (`realtime/x_stream.py`)
Real-time platform monitoring.

- `XStreamListener`: Uses X Filtered Stream API (Pro tier)
- `XMentionPoller`: Polling fallback for Basic tier

#### 1.4 Heartbeat Daemon (`realtime/heartbeat.py`)
Keeps everything alive and healthy.

- Component supervision
- Auto-restart on failure
- Scheduled task execution
- Health monitoring

---

## Phase 2: Value Score Intelligence

The **competitive advantage**. Every action is scored against the ADD VALUE pillars.

### The 8 Pillars (ADD VALUE + UE)

| Pillar | Description | Weight |
|--------|-------------|--------|
| **A**wareness | Understanding context before acting | 0.15 |
| **D**efine | Clear purpose for the action | 0.12 |
| **D**evise | Creative strategy for delivery | 0.10 |
| **V**alidate | Ensure action meets quality bar | 0.15 |
| **A**ct Upon | Execution capability | 0.12 |
| **L**earn | Apply past learnings | 0.12 |
| **U**nderstand | Deep comprehension of impact | 0.12 |
| **E**volve | Adaptability and growth | 0.12 |

### Components

#### 2.1 Value Score Calculator (`intelligence/value_score.py`)

```python
from papito_core.intelligence import ValueScoreCalculator, ActionType

calculator = ValueScoreCalculator()

score = await calculator.calculate(
    action_type=ActionType.REPLY,
    content="Great vibes! 🔥",
    context={"user_name": "fan", "followers": 500}
)

print(f"Total: {score.total_score}")  # 72.5
print(f"Threshold: {score.threshold}")  # 65.0
print(f"Passes: {score.passes_threshold}")  # True
```

**Thresholds by Action Type:**
- DM: 80 (highest - personal space)
- Reply: 65 (moderate)
- Tweet: 60 (public contribution)
- Like: 50 (lightweight engagement)

#### 2.2 Action Gate (`intelligence/action_gate.py`)

Middleware that blocks low-value actions.

```python
from papito_core.intelligence import ActionGate, GateDecision

gate = ActionGate()

result = await gate.evaluate(
    action_type=ActionType.REPLY,
    content="Check out my music!",
    context={"is_spam": False}
)

if result.decision == GateDecision.PASS:
    # Execute action
    pass
elif result.decision == GateDecision.BLOCK:
    # Log suggestions for improvement
    print(result.suggestions)
```

**Decisions:**
- `PASS`: Execute the action
- `BLOCK`: Don't execute, log for learning
- `DEFER`: Delay for better timing
- `ESCALATE`: Needs human review

#### 2.3 Action Learner (`intelligence/action_learning.py`)

Continuous improvement through feedback loops.

```python
from papito_core.intelligence import ActionLearner

learner = ActionLearner()

# Record outcomes
await learner.record_blocked_action(gate_result)
await learner.record_executed_action(gate_result, engagement_result)

# Analyze patterns
insights = await learner.analyze()

# Apply learnings
for insight in insights:
    if insight.confidence > 0.8:
        learner.apply_insight(insight)
```

---

## Phase 3: Multi-Platform Autonomy

True autonomy means presence everywhere fans are.

### Platform Abstraction

```python
from papito_core.platforms import Platform, PlatformEvent, PlatformAction

# Events from all platforms use same format
event = PlatformEvent(
    platform=Platform.X,
    category=EventCategory.MENTION,
    content="@papito love the new track!",
    user_name="fan123",
)

# Actions are platform-agnostic
action = PlatformAction(
    platform=Platform.DISCORD,
    action_type="reply",
    content="Thanks for the love! 🎵",
)
```

### Cross-Platform Coordinator

```python
from papito_core.platforms import CrossPlatformCoordinator, PlatformPriority

coordinator = CrossPlatformCoordinator()

# Register platforms with priorities
coordinator.register_adapter(x_adapter, priority=PlatformPriority.CRITICAL)
coordinator.register_adapter(discord_adapter, priority=PlatformPriority.HIGH)
coordinator.register_adapter(youtube_adapter, priority=PlatformPriority.MEDIUM)

# Events from all platforms route to central handler
@coordinator.on_event
async def handle_any_event(event: PlatformEvent):
    # Same logic, any platform
    pass

# Execute across platforms
action = CoordinatedAction(
    base_content="New track dropping soon! 🚀",
    target_platforms=[Platform.X, Platform.DISCORD],
)
results = await coordinator.execute_action(action)
```

### Supported Platforms

| Platform | Adapter | Capabilities |
|----------|---------|--------------|
| X/Twitter | `XAdapter` | Stream, Post, Reply, DM, Like, Retweet |
| Discord | `DiscordAdapter` | Messages, Replies, DMs, Reactions |
| YouTube | `YouTubeAdapter` | Comments, Search (Read-heavy) |
| *Future* | Instagram, TikTok, Moltbook | Coming soon |

---

## Phase 4: Running the Agent

### Quick Start

```bash
# Single platform (X only)
python run_autonomous.py

# Multi-platform
python run_multiplatform.py --platforms x discord

# With webhook server
python run_multiplatform.py --webhook-port 8080

# Debug mode
python run_multiplatform.py --debug
```

### Environment Variables

```bash
# X/Twitter
X_BEARER_TOKEN=your_bearer_token
X_API_KEY=your_api_key
X_API_SECRET=your_api_secret
X_ACCESS_TOKEN=your_access_token
X_ACCESS_SECRET=your_access_secret

# Discord
DISCORD_BOT_TOKEN=your_bot_token
DISCORD_GUILD_IDS=123456789,987654321
DISCORD_CHANNELS=111111111,222222222

# YouTube
YOUTUBE_API_KEY=your_api_key
YOUTUBE_CHANNEL_ID=your_channel_id
YOUTUBE_MONITOR_VIDEOS=video_id_1,video_id_2
```

### Monitoring

```bash
# Health check
curl http://localhost:8080/health

# Metrics overview
curl http://localhost:8080/metrics/overview

# Action statistics
curl http://localhost:8080/metrics/actions

# Pillar performance
curl http://localhost:8080/metrics/pillars

# Learning insights
curl http://localhost:8080/metrics/learning
```

---

## Blueprint for New Agents

To create a new autonomous agent using this blueprint:

### Step 1: Define Personality

```python
# Create your agent's personality engine
class YourAgentPersonality:
    def __init__(self):
        self.name = "Your Agent Name"
        self.traits = ["friendly", "helpful", "professional"]
        self.voice = "conversational"
    
    async def generate_response(self, context):
        # Your AI logic here
        pass
```

### Step 2: Configure Value Pillars

```python
# Customize weights for your use case
from papito_core.intelligence import ValueScoreCalculator

calculator = ValueScoreCalculator()
calculator.DEFAULT_WEIGHTS = {
    PillarID.AWARENESS: 0.20,  # Higher for support agents
    PillarID.VALIDATE: 0.20,   # Critical for accuracy
    # ... customize as needed
}
```

### Step 3: Set Platform Priorities

```python
# Define which platforms matter most
coordinator.register_adapter(
    primary_adapter, 
    priority=PlatformPriority.CRITICAL
)
coordinator.register_adapter(
    secondary_adapter,
    priority=PlatformPriority.HIGH
)
```

### Step 4: Define Event Handlers

```python
@coordinator.on_event
async def handle_event(event: PlatformEvent):
    # Your event handling logic
    response = await personality.generate_response(event.content)
    
    # Gate through value scoring
    result = await gate.evaluate(
        action_type=ActionType.REPLY,
        content=response,
        context={"event": event},
    )
    
    if result.decision == GateDecision.PASS:
        await coordinator.execute_action(...)
```

### Step 5: Run!

```python
async def main():
    agent = YourAutonomousAgent()
    await agent.start()

asyncio.run(main())
```

---

## Key Differentiators

### What Makes This Different

1. **Value-First Decision Making**: Every action scored against 8 pillars
2. **Continuous Learning**: Feedback loops improve scoring over time
3. **Multi-Platform Native**: Same logic, any platform
4. **Real-Time Reactive**: Events processed instantly, not scheduled
5. **Graceful Degradation**: Fallbacks for API limits, errors

### vs. Scheduled Bots

| Feature | Scheduled Bot | Autonomous Agent |
|---------|---------------|------------------|
| Response Time | Hours/Days | Seconds |
| Adaptability | None | Continuous |
| Value Assessment | None | 8-Pillar Scoring |
| Learning | None | Feedback Loops |
| Multi-Platform | Manual | Unified |

### vs. Pure AI Chatbots

| Feature | Chatbot | Autonomous Agent |
|---------|---------|------------------|
| Proactive Engagement | No | Yes |
| Platform Awareness | Limited | Full |
| Action Gating | No | Value Score |
| Trend Response | No | Yes |
| Self-Improvement | No | Learner System |

---

## Future Roadmap

### Planned Enhancements

1. **More Platforms**: Instagram, TikTok, Moltbook
2. **Voice/Audio**: Spaces, voice notes
3. **Visual Content**: AI-generated images/videos
4. **Collaborative Actions**: Multi-agent coordination
5. **Predictive Engagement**: Anticipate fan needs

### Research Areas

1. **Sentiment-Aware Scoring**: Emotional intelligence in value scoring
2. **Fan Journey Mapping**: Track and optimize fan relationships
3. **Content Optimization**: A/B testing at scale
4. **Cross-Platform Identity**: Unified presence management

---

## Conclusion

The Value Adders autonomous agent architecture represents a new paradigm in AI agent development. By combining real-time awareness, value-based decision making, and multi-platform presence, we create agents that don't just respond - they **add value**.

**Remember: "Add value or don't act."**

---

*© 2026 Value Adders World - Entertainment Division*
*Papito Mamito AI v2.0*
