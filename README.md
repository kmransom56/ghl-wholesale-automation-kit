# GHL Wholesale Automation Kit

GHL-native wholesale real estate automation — **no Zapier**. Investor scoring, 70% rule, property matching, DealDriven Playwright sync, and webhook endpoints for GoHighLevel workflows.

## Features

- **70% Rule** — ARV-based max offer and profit margin
- **Investor Quality Scoring** — Gold / Silver / Bronze tiers
- **Property Matching** — Weighted investor–deal matching
- **GHL API Client** — Contacts, custom fields, opportunities, workflows
- **DealDriven Scraper** — Playwright sync (no API key)
- **GSCCCA Verifier** — Georgia property record lookup
- **Flask Webhooks** — Six endpoints for GHL automation

## Quick Start

```bash
uv venv && source .venv/bin/activate
uv pip install -r requirements.txt
playwright install chromium
cp .env.example .env
python ghl_custom_fields.py
pytest tests/ -v
python app.py
```

## API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Health check |
| POST | `/api/webhooks/calculate-score` | Investor quality score |
| POST | `/api/webhooks/seventy-percent-rule` | 70% rule analysis |
| POST | `/api/webhooks/find-matches` | Match property to investors |
| POST | `/api/webhooks/update-investor-stats` | Post-close tier update |
| POST | `/api/manual/sync-dealdriven` | Scrape DealDriven → GHL |
| POST | `/api/manual/process-deal` | Full deal workflow |

## Documentation

- [GHL Workflow Templates](docs/GHL_WORKFLOW_TEMPLATES.md)
- [Deployment Guide](docs/DEPLOYMENT_GUIDE.md)

## Project Layout

```
app.py                    # Flask webhook server
ghl_custom_fields.py      # One-time GHL field setup
gsccca_verifier.py        # Georgia property verification
deploy.py                 # CLI entrypoint
config/system_config.json # GHL-first config (no Zapier)
src/
  integrations/           # GHL client, DealDriven scraper, sync
  workflows/              # Scoring, 70% rule, matching
tests/                    # Unit + webhook integration tests
```

## Docker

```bash
docker compose up --build -d
```

## License

See [LICENSE](LICENSE).
