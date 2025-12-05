# Procfile for Heroku / Railway / Render deployment

# Web server (API)
web: uvicorn papito_core.api:app --host 0.0.0.0 --port ${PORT:-8000}

# Background worker (Autonomous Agent)
worker: python -m papito_core.cli agent start --interval 60

# One-off agent run (for scheduled jobs)
agent-once: python -m papito_core.cli agent once

# Release command (run migrations, etc.)
release: echo "No migrations needed for Papito"
