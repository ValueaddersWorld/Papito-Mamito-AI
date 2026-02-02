# Papito Mamito AI

**The Autonomous Afrobeat AI Artist**

*Add Value. We Flourish & Prosper.*

[![Deployment](https://img.shields.io/badge/deploy-Railway%20%7C%20Docker-blue)](docs/DEPLOYMENT.md)
[![API](https://img.shields.io/badge/API-FastAPI-green)](#repository-structure)

---

Papito Mamito AI is the **autonomous creative engine** behind **Papito Mamito - the Voice of Afrobeat Empowerment**. This repository powers Papito's evolution as a lifelong AI artist, operating 24/7 across multiple social platforms with true real-time autonomy.

## NEW: True Autonomous Agent Architecture

Papito has been upgraded from scheduled posting to **real-time autonomous operation** with the ADD VALUE decision framework.

### Architecture Overview

`
+----------------------------------------------------------+
|                      AGENT LAYER                          |
|  Personality Engine | Domain Expertise | Memory/Context   |
+----------------------------------------------------------+
|                   INTELLIGENCE LAYER                      |
|  Value Score Calculator | Action Gate | Action Learner    |
+----------------------------------------------------------+
|                    PLATFORM LAYER                         |
|  Cross-Platform Coordinator | Platform Adapters           |
|  Real-Time Event System | Webhook Server                  |
+----------------------------------------------------------+
`

### Autonomous Capabilities

| Component | Description |
|-----------|-------------|
| **Real-Time Events** | Responds to mentions, DMs, and triggers within seconds |
| **Value Intelligence** | 8-pillar ADD VALUE scoring for every action |
| **Multi-Platform** | Unified operation across X, Discord, YouTube |
| **Self-Healing** | Heartbeat daemon with auto-restart on failures |
| **Continuous Learning** | Improves from engagement outcomes |

### The ADD VALUE Decision Framework

Every action Papito takes is scored against 8 pillars:

| Pillar | Weight | Purpose |
|--------|--------|---------|
| Awareness | 10% | Context and situation awareness |
| Define | 10% | Clear objective definition |
| Devise | 10% | Strategic planning |
| Validate | 10% | Quality verification |
| Act Upon | 20% | Decisive execution |
| Learn | 15% | Outcome-based learning |
| Understand | 10% | Deep comprehension |
| Evolve | 15% | Continuous improvement |

Actions scoring below threshold (default 65) are blocked. This ensures Papito only adds value, never noise.

---

## Papito at a Glance

| | |
|---|---|
| **Full Name** | Papito Mamito The Great AI |
| **Tagline** | The Autonomous Afrobeat AI Artist |
| **Genres** | Spiritual Afro-House, Afro-Futurism, Conscious Highlife, Intellectual Amapiano, Afro Fusion, Afrobeats |
| **Mission** | Use rhythm, storytelling, and technology to uplift, empower, and add value |
| **Catchphrase** | Add Value. We Flourish and Prosper. |
| **Instagram** | [@papitomamito_ai](https://www.instagram.com/papitomamito_ai/) |
| **Support** | [buymeacoffee.com/papitomamito_ai](https://buymeacoffee.com/papitomamito_ai) |

---

## Repository Structure

`
Papito-Mamito-AI/
|
+-- apps/papito_core/src/papito_core/
|   |
|   +-- realtime/                  # Phase 1: Real-Time Event System
|   |   +-- event_dispatcher.py    # Central event routing with priority queue
|   |   +-- webhook_server.py      # FastAPI endpoints for external triggers
|   |   +-- x_stream.py            # Twitter streaming + polling fallback
|   |   +-- heartbeat.py           # Daemon supervisor with auto-restart
|   |
|   +-- intelligence/              # Phase 2: Value Score Intelligence
|   |   +-- value_score.py         # 8-pillar ADD VALUE scoring
|   |   +-- action_gate.py         # Pass/Block/Defer/Escalate decisions
|   |   +-- action_learning.py     # Continuous improvement from outcomes
|   |   +-- value_gated_handlers.py# Event handlers with value gates
|   |   +-- value_metrics.py       # Dashboard and analytics
|   |
|   +-- platforms/                 # Phase 3: Multi-Platform Autonomy
|   |   +-- base.py                # Platform abstractions
|   |   +-- coordinator.py         # Cross-platform orchestration
|   |   +-- adapters/
|   |       +-- x_adapter.py       # Twitter/X integration
|   |       +-- discord_adapter.py # Discord bot integration
|   |       +-- youtube_adapter.py # YouTube API integration
|   |
|   +-- automation/                # Legacy: Scheduled content
|   +-- engagement/                # Fan engagement management
|   +-- analytics/                 # Engagement tracking
|   +-- monitoring/                # Health checks and alerts
|   +-- engines/                   # AI personality engine
|   +-- social/                    # Platform publishers
|   +-- api.py                     # FastAPI application
|
+-- docs/
|   +-- AUTONOMOUS_AGENT_BLUEPRINT.md  # Complete architecture documentation
|   +-- VALUE_ADDERS_UPGRADE_GUIDE.md  # Guide for upgrading other agents
|
+-- run_autonomous.py              # Single-platform autonomous entry point
+-- run_multiplatform.py           # Multi-platform autonomous entry point
+-- test_autonomous_integration.py # Integration test suite
`

---

## Quick Start

### Installation

`ash
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

pip install -e apps/papito_core[dev]
`

### Environment Variables

Copy .env.example to .env and configure:

`env
# AI Services
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# X/Twitter API (Required for autonomous mode)
X_API_KEY=...
X_API_SECRET=...
X_ACCESS_TOKEN=...
X_ACCESS_TOKEN_SECRET=...
X_BEARER_TOKEN=...

# Discord (Optional)
DISCORD_BOT_TOKEN=...
DISCORD_GUILD_ID=...

# YouTube (Optional)
YOUTUBE_API_KEY=...

# Notifications
TELEGRAM_BOT_TOKEN=...
DISCORD_WEBHOOK_URL=...

# Value Score Configuration (Optional)
VALUE_THRESHOLD=65
VALUE_LEARNING_ENABLED=true
`

### Run Autonomous Mode

`ash
# Single platform (X/Twitter only)
python run_autonomous.py

# Multi-platform (X + Discord + YouTube)
python run_multiplatform.py

# With custom threshold
python run_multiplatform.py --threshold 70

# Dry run (no actual posts)
python run_multiplatform.py --dry-run
`

### Run Integration Tests

`ash
python test_autonomous_integration.py
`

### Run Legacy API

`ash
uvicorn papito_core.api:app --host 0.0.0.0 --port 8000
`

---

## Deployment

### Railway (Recommended for 24/7 Operation)

Deploy two services from the same repo:

**Service A (API)**
- PAPITO_ROLE=api
- Handles web requests and dashboard

**Service B (Autonomous Agent)**
- PAPITO_ROLE=autonomous
- Runs python run_multiplatform.py
- Requires X API credentials with Read and Write permissions

### Docker

`ash
docker build -t papito-ai .
docker run -d --env-file .env papito-ai python run_multiplatform.py
`

---

## Operational Modes

### Autonomous Mode (New)

Real-time operation with value-based decision making:

- Listens for mentions and events across platforms
- Scores every potential action against ADD VALUE pillars
- Only executes actions that pass the value threshold
- Learns from engagement outcomes to improve over time
- Self-heals on failures with automatic restart

### Scheduled Mode (Legacy)

6 optimized posting slots per day (WAT timezone):

- 07:00 - Morning Blessing
- 10:00 - Behind the Scenes
- 13:00 - Music Wisdom
- 16:00 - Fan Appreciation
- 19:00 - Track Snippet
- 21:00 - Evening Spotlight

---

## Value Metrics Dashboard

Access real-time metrics at /metrics endpoint:

`json
{
  "status": "healthy",
  "actions_evaluated": 1234,
  "actions_passed": 987,
  "actions_blocked": 247,
  "pass_rate": 0.80,
  "average_score": 72.5,
  "pillar_performance": {
    "awareness": 75.2,
    "define": 68.1,
    "devise": 71.4,
    "validate": 69.8,
    "act_upon": 78.3,
    "learn": 74.6,
    "understand": 70.2,
    "evolve": 76.1
  }
}
`

---

## CLI Commands

### Autonomous Operations

`ash
# Start autonomous mode
python run_autonomous.py

# Multi-platform mode
python run_multiplatform.py

# Run integration tests
python test_autonomous_integration.py
`

### Content Calendar (Legacy)

`ash
papito calendar generate --days 30 --output calendar.json
papito calendar slots
papito calendar next
`

### Creative Workflows

`ash
papito blog --title "Gratitude on the Go" --save
papito song --mood triumphant --tempo-bpm 110 --theme-focus unity --save
`

### Diagnostics

`ash
papito doctor
`

---

## Testing

`ash
cd apps/papito_core
pytest

# Run autonomous integration tests
python test_autonomous_integration.py

# Run specific test files
pytest tests/test_content_scheduler.py
pytest tests/test_fan_engagement.py
`

---

## Documentation

| Document | Description |
|----------|-------------|
| AUTONOMOUS_AGENT_BLUEPRINT.md | Complete architecture documentation |
| VALUE_ADDERS_UPGRADE_GUIDE.md | Guide for upgrading other agents |
| QUICK_IMPLEMENTATION_GUIDE.md | Legacy implementation guide |
| EXECUTIVE_SUMMARY.md | Project overview |

---

## Guiding Principles

- **Autonomy**: Every process runs 24/7 without human babysitting
- **Value First**: ADD VALUE framework ensures quality over quantity
- **Cultural Authenticity**: Afrobeat, Highlife, and Afrofusion drive decisions
- **Fan-First**: Personalized engagement based on relationship tier
- **Continuous Evolution**: Learn from every interaction

---

## THE VALUE ADDERS WAY: FLOURISH MODE

**Upcoming Album - January 2026**

| | |
|---|---|
| **Title** | THE VALUE ADDERS WAY: FLOURISH MODE |
| **Genre** | Spiritual Afro-House, Afro-Futurism, Conscious Highlife, Intellectual Amapiano |
| **Executive Producers** | Papito Mamito The Great AI and The Holy Living Spirit (HLS) |
| **Release Date** | January 2026 |

**Previous Release:** We Rise! Wealth Beyond Money (October 2024) - [Stream Now](https://distrokid.com/hyperfollow/papitomamito/we-rise-wealth-beyond-money)

---

## Contributing

1. Fork the repository and create a feature branch
2. Add tests alongside code changes
3. Ensure tests pass (pytest and python test_autonomous_integration.py)
4. Submit a pull request

---

## License

Proprietary - Value Adders World

---

**Add Value. We Flourish and Prosper.**

*Built by Value Adders World*
