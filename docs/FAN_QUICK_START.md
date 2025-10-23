# Papito Mamito Fan Quick Start

Welcome to the Value Adders tribe! This guide shows fans how to tap into Papito Mamito’s autonomous creative engine—no coding required if you use a hosted API.

## Option A: Use the hosted API

Ask the Value Adders team for the live API URL (example: `https://papito-api.example.com`). Then you can:

### 1. Generate today’s blessing
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  https://papito-api.example.com/blogs \
  -d '{"title": "Joy in Motion"}'
```

### 2. Request a new groove
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  https://papito-api.example.com/songs/ideate \
  -d '{"mood":"uplifting","theme_focus":"gratitude"}'
```

If Papito’s team enables audio generation, the response includes `audio_url` so you can listen instantly.

### 3. Track the journey
```bash
curl https://papito-api.example.com/health
```

This confirms the engine is humming.

## Option B: Run Papito locally (power fans)

1. Install Python 3.11+ and Git.
2. Clone the repo:
   ```bash
   git clone https://github.com/ValueaddersWorld/Papito-Mamito-AI
   cd Papito-Mamito-AI
   ```
3. Create a virtualenv and install:
   ```bash
   python -m venv .venv && .venv\Scripts\activate
   pip install -e apps/papito_core[api]
   ```
4. Optional: copy `.env.example` to `.env` and add your `SUNO_API_KEY`.
5. Launch the API:
   ```bash
   uvicorn papito_core.api:app --host 0.0.0.0 --port 8000
   ```

Now open `http://localhost:8000/docs` to explore a friendly Swagger UI.

## Fan rituals

- Share your daily blessing on socials using `#ValueOverVanity`.
- Request custom tracks for celebrations.
- Submit your analytics snapshots (streams, playlist adds) to fuel Papito’s insights—just POST them through the API.
- Join the gratitude livestreams when Papito drops a schedule update.

Spread the word, dance with purpose, and keep rising!***
