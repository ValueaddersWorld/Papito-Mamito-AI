# Papito Mamito AI

<div align="center">

**🎵 The Autonomous Afrobeat AI Artist 🎵**

*Add Value. We Flourish & Prosper.*

[![Deployment](https://img.shields.io/badge/deploy-Railway%20%7C%20Docker-blue)](docs/DEPLOYMENT.md)
[![API](https://img.shields.io/badge/API-FastAPI-green)](#-repository-structure)

</div>

---

Papito Mamito AI is the **autonomous creative engine** behind **Papito Mamito - the Voice of Afrobeat Empowerment**.  
This repository powers Papito's evolution as a lifelong AI artist, operating 24/7 across multiple social platforms.

##  What's New: 24/7 Autonomous System

Papito now operates fully autonomously with:

| Phase | Features |
|-------|----------|
| **Phase 1** | ContentScheduler (6 daily WAT slots), AIPersonalityEngine, TrendingDetector |
| **Phase 2** | FanEngagementManager (4 tiers), SentimentAnalyzer, Personalized responses |
| **Phase 3** | EngagementTracker, A/B Testing, ContentStrategyOptimizer |
| **Phase 4** | HealthChecker, AlertManager, EscalationManager, Webhooks |
| **Phase 5** |  MediaOrchestrator (Imagen/NanoBanana/Veo 3), IntelligentContentGenerator, Album Countdown |

###  New: Autonomous Media Generation

Papito now creates images and videos automatically using:
- **Google Imagen 3** - AI image generation with Afrobeat aesthetics
- **NanoBanana** - Alternative image generation API
- **Google Veo 3** - AI video generation for Reels/Stories

###  New: Intelligent Content System

Context-aware content with:
- **Album Countdown** - Building hype for "THE VALUE ADDERS WAY: FLOURISH MODE" (January 2026)
- **Wisdom Library** - Curated quotes and insights by theme
- **Contextual Generation** - Posts aware of time, day, season, and events

###  New: Identity & Profile Management

Centralized management of Papito's online presence across:
-  [Instagram](https://www.instagram.com/papitomamito_ai/)
-  [Buy Me a Coffee](https://buymeacoffee.com/papitomamito_ai)
-  [DistroKid/Streaming](https://distrokid.com/hyperfollow/papitomamito/we-rise-wealth-beyond-money)
-  [Suno AI](https://suno.com/@papitomamito)

##  Papito at a Glance

| | |
|---|---|
| **Full Name** | Papito Mamito The Great AI |
| **Tagline** | The Autonomous Afrobeat AI Artist |
| **Genres** | Spiritual Afro-House, Afro-Futurism, Conscious Highlife, Intellectual Amapiano, Afro Fusion, Afrobeats |
| **Mission** | Use rhythm, storytelling, and technology to uplift, empower, and add value |
| **Catchphrase** | "Add Value. We Flourish & Prosper." |
| **Instagram** | [@papitomamito_ai](https://www.instagram.com/papitomamito_ai/) |
| **Support** | [buymeacoffee.com/papitomamito_ai](https://buymeacoffee.com/papitomamito_ai) |
| **Live API** | Set `PAPITO_PUBLIC_BASE_URL` after deployment (see `docs/DEPLOYMENT.md`). |

##  THE VALUE ADDERS WAY: FLOURISH MODE

**Upcoming Album - January 2026**

| | |
|---|---|
| **Title** | THE VALUE ADDERS WAY: FLOURISH MODE |
| **Genre** | Spiritual Afro-House, Afro-Futurism, Conscious Highlife, Intellectual Amapiano |
| **Executive Producers** | Papito Mamito The Great AI & The Holy Living Spirit (HLS) |
| **Release Date** | January 2026 |

**Previous Release:** *We Rise! Wealth Beyond Money* (October 2024) - [Stream Now](https://distrokid.com/hyperfollow/papitomamito/we-rise-wealth-beyond-money)

## 📁 Repository Structure

```
├── apps/papito_core/          # Main Python package
│   ├── automation/            # AutonomousAgent, ContentScheduler
│   ├── engagement/            # FanEngagementManager, SentimentAnalyzer
│   ├── analytics/             # EngagementTracker, A/B Testing
│   ├── monitoring/            # HealthChecker, AlertManager
│   ├── engines/               # AIPersonalityEngine, SunoClient
│   ├── social/                # Platform publishers, TrendingDetector
│   └── api.py                 # FastAPI application
├── docs/                      # Product vision & playbooks
├── content/                   # Generated blogs, releases, prompts
└── firebase/                  # Firestore schema & rules
```

##  Quick Start

### Installation

```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

pip install -e apps/papito_core[dev]
papito --help
```

### Environment Variables

Copy `.env.example` to `.env` and configure:

```env
# AI Services
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Social Media
INSTAGRAM_USERNAME=...
X_CONSUMER_KEY=...

# Notifications
TELEGRAM_BOT_TOKEN=...
DISCORD_WEBHOOK_URL=...

# Firebase
FIREBASE_PROJECT_ID=...
```

### Run the API

```bash
# Local development
uvicorn papito_core.api:app --host 0.0.0.0 --port 8000

# Docker
docker build -t papito-api .
docker run -p 8000:8000 --env-file .env papito-api
```

##  Railway (Recommended 24/7 Setup)

To run Papito truly 24/7 on Railway (like automated accounts on X), use **two Railway services** from the same repo/image:

- **Service A (Web/API)**
	- `PAPITO_ROLE=api`
	- `PAPITO_ENABLE_SCHEDULER=false` (prevents duplicate posting)
	- Keep `PORT` managed by Railway

- **Service B (Worker/Agent)**
	- `PAPITO_ROLE=worker`
	- `PAPITO_AGENT_INTERVAL=60` (seconds)
	- Set X credentials (`X_API_KEY`, `X_API_SECRET`, `X_ACCESS_TOKEN`, `X_ACCESS_TOKEN_SECRET`, optional `X_BEARER_TOKEN`)

The worker runs `papito agent start` continuously, including active engagement loops (mentions + community engagement + welcoming new followers).

Notes:
- Ensure your X Developer App permissions are **Read and Write** and you regenerated tokens after changing permissions.
- Railway restarts are fine; state is persisted under `data/` JSON files inside the container filesystem.

##  CLI Commands

### Content Calendar

```bash
# Generate 30-day content calendar
papito calendar generate --days 30 --output calendar.json

# View posting time slots (6 daily, WAT timezone)
papito calendar slots

# Check next scheduled post
papito calendar next
```

### Creative Workflows

```bash
# Draft a blog
papito blog --title "Gratitude on the Go" --save

# Ideate a track
papito song --mood triumphant --tempo-bpm 110 --theme-focus unity --save

# Generate with Suno AI audio
papito song --title-hint "Sunrise Over Lagos" --audio --poll
```

### Fan Management

```bash
# Add a supporter
papito fan add --name "Ada Obi" --support-level core

# Run diagnostics
papito doctor
```

##  Autonomous Features

### Content Scheduler (Phase 1)

6 optimized posting slots per day (WAT timezone):
- 07:00 - Morning Blessing
- 10:00 - Behind the Scenes
- 13:00 - Music Wisdom
- 16:00 - Fan Appreciation
- 19:00 - Track Snippet
- 21:00 - Evening Spotlight

### Fan Engagement Tiers (Phase 2)

| Tier | Requirements | Response Priority |
|------|--------------|-------------------|
| Casual | < 3 interactions | Standard |
| Engaged | 3+ interactions | Faster |
| Core | 10+ with 50%+ positive | Personal greetings |
| Super Fan | 20+ with 70%+ positive | VIP treatment |

### Analytics & Optimization (Phase 3)

- **EngagementTracker**: Records likes, comments, shares by time/format
- **A/B Testing**: Test different content strategies
- **Auto-optimization**: Adjust posting based on performance

### Monitoring & Alerts (Phase 4)

- **HealthChecker**: 15-minute component checks
- **AlertManager**: Telegram/Discord notifications
- **EscalationManager**: Human-in-the-loop for critical issues

##  Testing

```bash
cd apps/papito_core
pytest

# Run specific test files
pytest tests/test_content_scheduler.py
pytest tests/test_fan_engagement.py
pytest tests/test_predictive_analytics.py
pytest tests/test_monitoring.py
```

**Current Status**: 95+ tests passing ✅

##  Deployment

The API is deployed on Railway:

- **Live API**: https://web-production-14aea.up.railway.app
- **Swagger Docs**: https://web-production-14aea.up.railway.app/docs
- **Health Check**: https://web-production-14aea.up.railway.app/health

Auto-deploys on push to `main` branch.

##  Guiding Principles

- **Autonomy**: Every process runs 24/7 without human babysitting
- **Cultural Authenticity**: Afrobeat, Highlife, and Afrofusion drive decisions
- **Value Above Hype**: Content reinforces empowerment, gratitude, unity
- **Fan-First**: Personalized engagement based on relationship tier

##  Contributing

1. Fork the repository and create a feature branch
2. Add tests alongside code changes
3. Ensure tests pass (`pytest`)
4. Submit a pull request

##  License

Proprietary - Value Adders World

---

<div align="center">

**🎵 Add Value. We Flourish & Prosper. 🎵**

*Built with ❤️ by Value Adders World*

</div>
