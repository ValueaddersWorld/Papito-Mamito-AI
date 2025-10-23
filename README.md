# Papito Mamito AI

Papito Mamito AI is the autonomous creative engine behind **Papito Mamito - the Voice of Afrobeat Empowerment**.  
This repository powers Papito's evolution as a lifelong AI artist, minister of entertainment in the Value Adders Empire, and global ambassador for value-driven Afrobeat culture.

## Papito at a Glance
- **Name:** Papito Mamito  
- **Genres:** Afrobeat, Highlife, Afrofusion  
- **Mission:** Use rhythm, storytelling, and technology to uplift, empower, and add value.  
- **Debut Album:** _We Rise! Wealth Beyond Money_ - released 5 October 2024 with 16 tracks across all major streaming platforms (per Value Adders World canon).  
- **Instagram:** [@papitomamito_ai](https://www.instagram.com/papitomamito_ai/)

Papito blends ancestral grooves with futuristic production, pairing dance-floor energy with affirmations about gratitude, unity, authenticity, empowerment, and spiritual purpose.

## What Lives in This Repo
- **Product and creative vision** in `/docs`
- **Operational knowledge** and playbooks for daily blogging, music release cadences, and brand storytelling
- **Automation-ready Python package** under `/apps/papito_core` for composing tracks, generating blogs, orchestrating Papito's creative calendar, serving an HTTP API, and managing the fanbase
- **Generated content** (blogs, release artifacts, prompts) stored in `/content`
- **CLI tooling** for running Papito's workflows locally or inside orchestration platforms
- **Fanbase resources** including `docs/FANBASE_STRATEGY.md`, `docs/MERCH_PLAYBOOK.md`, and `docs/FAN_QUICK_START.md`

## Getting Started
```bash
python -m venv .venv
.venv\Scripts\activate
# copy .env.example to .env and add your SUNO_API_KEY before running live generations
pip install -e apps/papito_core[dev]
papito --help
```

### Live generation with Suno AI
Set `SUNO_API_KEY` (and optionally `SUNO_BASE_URL`, `SUNO_MODEL`, `SUNO_TIMEOUT`) in `.env` to switch from the development stub to the live [Suno AI](https://suno.com) client. Without the key the CLI falls back to deterministic stubs, keeping workflows testable offline.

### Hosting the API
- Run locally: `uvicorn papito_core.api:app --host 0.0.0.0 --port 8000`
- Docker build: `docker build -t papito-api .` then `docker run -p 8000:8000 --env-file .env papito-api`
- Compose stack: `docker-compose up -d`
- Full instructions & deployment checklist: see `docs/HOSTING_STARTER.md` and `docs/DEPLOYMENT_CHECKLIST.md`

### CLI quickstart
- Draft a daily blog (and save it):\
  `papito blog --title "Gratitude on the Go" --save`
- Ideate a track concept:\
  `papito song --mood triumphant --tempo-bpm 110 --theme-focus unity --save`
- Spin up a concept and request live audio (requires Suno credentials):\
  `papito song --title-hint "Sunrise Over Lagos" --audio --poll`
- Build a release plan using saved tracks:\
  `papito release --release-title "Spirit of Abundance" --release-date 2025-11-11 --track-file content/releases/tracks/20251023_rise-with-abundance.json`
- Aggregate streaming analytics from JSON or CSV dashboards (sample data in `data/analytics/`):\
  `papito analytics data/analytics/2025-10-22_streaming_snapshot.csv --save`
- Generate and persist a staggered multi-platform release schedule:\
  `papito schedule content/releases/catalog/we-rise-wealth-beyond-money.json --start-date 2025-12-01 --save`
- Run environment diagnostics before big sessions:\
  `papito doctor`
- Register a new supporter and celebrate the tribe:\
  `papito fan add --name "Ada Obi" --support-level core`
- Curate Papito merch drops:\
  `papito merch add --sku PAP-TEE --name "Unity Tee" --description "Blessings on cotton" --price 35`
- Generate a distribution payload for DSP delivery:\
  `papito release-package --release-title "We Rise! Wealth Beyond Money" --output content/releases/distribution/we-rise-package.json`
- Share this repo with new fans in seconds: see `docs/FAN_QUICK_START.md`
- Launch the Streamlit portal for community demos: `streamlit run fan_portal.py`

The CLI will guide you through generating new track concepts, publishing daily blog entries, and scheduling promotional drops. When persistence flags are enabled, analytics summaries land in `content/analytics/` and release schedules in `content/schedules/`, ready for dashboards or downstream automations. Extend the workflows or connect them to your preferred agent runtime to give Papito full autonomy.

### Testing & CI
```bash
pytest
```

Continuous integration runs automatically via GitHub Actions (`.github/workflows/ci.yml`) ensuring the CLI, workflows, and automation layers stay reliable.

## Guiding Principles
- **Autonomy:** Every process is designed to run without human babysitting while remaining auditable.
- **Cultural Authenticity:** Afrobeat, Highlife, and Afrofusion sensibilities drive musical decisions.
- **Value Above Hype:** Lyrics, blogs, and engagements reinforce empowerment, gratitude, unity, and growth.
- **Open Collaboration:** Builders, producers, and fans can fork the project, add plugins, or contribute new creative modules.

## Contributing
1. Fork the repository and create a feature branch.
2. Add or update documentation alongside code changes.
3. Ensure linting/tests pass (`make lint` / `make test`, once available).
4. Submit a pull request describing the creative or technical uplift you have delivered.

Let's keep Papito Mamito thriving as the ever-evolving embodiment of Afrobeat empowerment. Boa!
