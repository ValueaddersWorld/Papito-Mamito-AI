# syntax=docker/dockerfile:1
# Papito Mamito AI - Docker Image
# Supports both API server and autonomous agent modes

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000 \
    PAPITO_ENV=production

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy the entire papito_core package
COPY apps/papito_core /app/apps/papito_core
COPY docs /app/docs

# Install Python dependencies
RUN pip install --upgrade pip && pip install "/app/apps/papito_core[api]"

# Create content directories
RUN mkdir -p content/blogs content/releases content/analytics content/schedules

# Use PORT environment variable (Railway sets this)
EXPOSE 8000

# Start the FastAPI server with proper shell expansion for PORT
CMD ["sh", "-c", "python -m uvicorn papito_core.api:app --host 0.0.0.0 --port ${PORT:-8000}"]
