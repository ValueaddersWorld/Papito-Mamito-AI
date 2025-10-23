# syntax=docker/dockerfile:1

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    UVICORN_PORT=8000

WORKDIR /app

COPY apps/papito_core/pyproject.toml /app/apps/papito_core/pyproject.toml
RUN pip install --upgrade pip && pip install "apps/papito_core[api] @ file:///app/apps/papito_core"

COPY . /app

EXPOSE 8000

CMD ["uvicorn", "papito_core.api:app", "--host", "0.0.0.0", "--port", "8000"]
