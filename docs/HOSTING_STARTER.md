# Hosting Starter Guide

This guide walks you through packaging and deploying the Papito Mamito AI workflows so collaborators and fans can access them through a simple HTTP API.

## 1. Prerequisites

- Python 3.11+
- Docker (optional but recommended for deployment)
- Suno API credentials if you plan to enable live audio generation (`SUNO_API_KEY`, optional `SUNO_BASE_URL`, `SUNO_MODEL`, `SUNO_TIMEOUT`)

## 2. Local API Server

```bash
# Clone & install
git clone https://github.com/ValueaddersWorld/Papito-Mamito-AI
cd Papito-Mamito-AI
python -m venv .venv && .venv\Scripts\activate  # or source .venv/bin/activate
pip install -e apps/papito_core[api]

# Optional: enable Suno
cp .env.example .env
# edit .env and add SUNO_API_KEY=...

# Launch API
uvicorn papito_core.api:app --host 0.0.0.0 --port 8000
```

### Available endpoints

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/health` | Basic readiness probe |
| `POST` | `/blogs` | Generate a blog entry (body: `BlogBrief`) |
| `POST` | `/songs/ideate` | Create a track concept and optionally generate audio (`SongIdeationRequest`) |
| `POST` | `/analytics/summarise` | Aggregate analytics snapshots (`snapshots` array payload) |

## 3. Docker packaging

The repository ships with a ready-to-use `Dockerfile`.

```bash
docker build -t papito-api .
docker run -p 8000:8000 --env-file .env papito-api
```

For a quick local stack with environment loading:

```bash
docker-compose up -d
```

By default the container runs `uvicorn papito_core.api:app` on port `8000`. Supply one or more API keys via the `.env` file to secure the endpoint:

```env
PAPITO_API_KEYS=dev-key-1,dev-key-2
```

Every request must include `X-API-Key` when keys are configured.

### Kubernetes / container platforms

For platforms like Render, Fly.io, or Azure Container Apps, deploy the image and configure environment variables:

| Variable | Purpose |
| --- | --- |
| `SUNO_API_KEY` | Enables live audio generation via Suno |
| `SUNO_BASE_URL` | Optional override for the Suno endpoint |
| `SUNO_MODEL` | Optional model override |
| `SUNO_TIMEOUT` | Optional request timeout |
| `PAPITO_API_KEYS` | Comma-separated API keys required to call the service |
| `PAPITO_API_RATE_LIMIT_PER_MIN` | Requests allowed per API key/IP per minute (default 60) |

## 4. Static deployment checklist

1. Run `papito doctor --check-suno` locally to confirm credentials and analytics schema validation.
2. Push analytics samples and release catalogs to the server (they live in `content/analytics/` and `content/releases/`).
3. Expose the API endpoint publicly or behind an authentication layer depending on your needs.
4. Optionally add a reverse proxy (Nginx, Cloudflare) to provide TLS and caching.

## 5. Future enhancements

- Streamlit or Next.js front-end consuming the API.
- Auth and rate limiting for public endpoints.
- Background job queue for long-running audio polls.
- Automated deployments via GitHub Actions or your preferred CI/CD.

For now, this guide gets builders to a hosted API in minutes so Papito can share his creative engine with the world. Add improvements as you scale!***
