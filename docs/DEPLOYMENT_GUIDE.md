# Deployment Guide

## Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip
- GoHighLevel location API key
- Linux server or Docker for production webhooks

## Local Setup

```bash
cd ghl-wholesale-automation-kit
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
playwright install chromium
cp .env.example .env
# Edit .env with GHL_API_KEY and GHL_LOCATION_ID
python ghl_custom_fields.py
pytest tests/ -v
python app.py
```

Health check: `curl http://localhost:5000/health`

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GHL_API_KEY` | Yes | GHL / Lead Connector API key |
| `GHL_LOCATION_ID` | Yes | Location sub-account ID |
| `DEALDRIVEN_USERNAME` | For sync | DealDriven login (Playwright) |
| `DEALDRIVEN_PASSWORD` | For sync | DealDriven password |
| `SERVER_PORT` | No | Default `5000` |
| `LOG_LEVEL` | No | Default `INFO` |

## Docker

```bash
docker compose up --build -d
docker compose logs -f ghl-automation
```

## Production (Nginx + SSL)

1. Run app on `127.0.0.1:5000` (Docker or systemd)
2. Proxy with Nginx to your domain
3. `certbot --nginx -d your-domain.com`
4. Configure GHL workflows per `docs/GHL_WORKFLOW_TEMPLATES.md`

## GHL Webhook URLs

After deploy, use:

- `https://your-domain.com/api/webhooks/calculate-score`
- `https://your-domain.com/api/webhooks/seventy-percent-rule`
- `https://your-domain.com/api/webhooks/find-matches`
- `https://your-domain.com/api/webhooks/update-investor-stats`

## DealDriven (no API key)

Investor sync uses Playwright browser automation:

```bash
curl -X POST http://localhost:5000/api/manual/sync-dealdriven \
  -H "Content-Type: application/json" \
  -d '{"dealdriven_username":"you@example.com","dealdriven_password":"secret"}'
```

Or set `DEALDRIVEN_USERNAME` / `DEALDRIVEN_PASSWORD` in `.env`.

## GSCCCA Verification

```bash
python gsccca_verifier.py "123 Main St" "Fulton"
```

## CI

GitHub Actions runs `pytest` on push to `main` / `develop` (see `.github/workflows/tests.yml`).

## Troubleshooting

| Issue | Fix |
|-------|-----|
| 401 from GHL | Verify `GHL_API_KEY` and `Version: 2021-07-28` header (built into client) |
| Webhook 400 | Ensure `contactId` in JSON body |
| Playwright fails | `playwright install chromium` and install system deps in Docker image |
| Port in use | `port-manager find` or change `SERVER_PORT` |
