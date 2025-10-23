# Deployment Checklist

Use this checklist when preparing to host Papito Mamito AI in a staging or production environment.

## Pre-deployment
- [ ] Clone repository and install dependencies (`pip install -e apps/papito_core[api]`).
- [ ] Configure `.env` with `SUNO_API_KEY`, `PAPITO_API_KEYS`, and any optional overrides.
- [ ] Run `papito doctor --check-suno` to verify credentials and schema health.
- [ ] Ensure `content/releases/catalog/` contains the latest release plans and audio metadata.
- [ ] Review fanbase and merch catalogs under `content/fans/` for accuracy.

## Container build & runtime
- [ ] Build Docker image (`docker build -t papito-api .`) or use `docker-compose up -d`.
- [ ] Confirm the API is reachable at `/health` **with** a valid API key header.
- [ ] Configure observability (logs, metrics) through your hosting provider.
- [ ] Enforce HTTPS via load balancer or reverse proxy.
- [ ] Set up secrets storage for API keys and Suno credentials.

## Post-deployment
- [ ] Smoke-test core endpoints (`/blogs`, `/songs/ideate`, `/analytics/summarise`, `/fans`, `/merch`).
- [ ] Generate a release package to validate catalog integrity (`papito release-package --release-title "We Rise! Wealth Beyond Money"`).
- [ ] Update fan communications (blog, livestream schedule) with new access details.
- [ ] Document rollback and backup procedures for content directories and environment variables.
