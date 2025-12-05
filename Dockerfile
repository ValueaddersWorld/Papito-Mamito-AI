# syntax=docker/dockerfile:1
# Papito Mamito AI - Docker Image
# Supports both API server and autonomous agent modes

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    UVICORN_PORT=8000 \
    PAPITO_ENV=production

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy the entire papito_core package (required for editable install)
COPY apps/papito_core /app/apps/papito_core
COPY docs /app/docs

# Install Python dependencies
RUN pip install --upgrade pip && pip install "/app/apps/papito_core[api]"

# Create content directories
RUN mkdir -p content/blogs content/releases content/analytics content/schedules

# Health check for API mode
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${UVICORN_PORT}/health || exit 1

EXPOSE 8000

# Default: Run API server
CMD ["uvicorn", "papito_core.api:app", "--host", "0.0.0.0", "--port", "8000"]

# ==============================================
# USAGE:
# ==============================================
# API Server (default):
#   docker run -p 8000:8000 --env-file .env papito-ai
#
# Autonomous Agent:
#   docker run --env-file .env papito-ai python -m papito_core.cli agent start
#
# Single Agent Iteration:
#   docker run --env-file .env papito-ai python -m papito_core.cli agent once
#
# Interactive CLI:
#   docker run -it --env-file .env papito-ai python -m papito_core.cli
