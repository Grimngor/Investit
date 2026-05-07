# Operations

## Logging

Backend logging is configured in `backend/app/logger.py`.

- Log directory: `backend/logs/`
- Application log: `backend/logs/app.log`
- Error log: `backend/logs/error.log`
- Rotation: 10 MB per file, 5 backups

Frontend logging is handled by `frontend/src/utils/logger.ts`.

- Logs are written to the browser console in development.
- Recent entries are stored in localStorage under `investit_logs`.
- Do not log passwords, tokens, or personal financial details.

## Health And Diagnostics

- `GET /health`: backend health, storage writability, and metrics.
- `GET /docs`: OpenAPI UI.
- `GET /debug/yahoo-check`: development-only Yahoo Finance connectivity check.
- `.\scripts\dev\verify_backend.ps1`: route and health verification for port `8000`.

## Deployment Settings (.env)

- `SECRET_KEY`: required; replace the development value before any shared deployment.
- `BACKEND_CORS_ORIGINS`: JSON list of allowed frontend origins.
- `INVESTIT_WEB_PORT`: Docker Compose web proxy port bound to localhost; default is `8080`.
- `PERSISTENCE_BACKEND`: runtime persistence backend; default is `sqlite`.
- `DATABASE_PATH`: SQLite database path; default is `data/investit.sqlite3`, resolved from the repository root when relative.
- `PRICE_STALE_THRESHOLD_DAYS`: age threshold for cached prices; default is `3`.
- `FINNHUB_API_KEY`: optional market-data key.
- `OPENFIGI_API_KEY`: optional OpenFIGI key for higher ISIN mapping limits.
- `ISIN_RESOLUTION_CACHE_DAYS`: age threshold for OpenFIGI-derived ISIN mappings; default is `30`.

## WebSocket Events

Connect with:

```text
ws://localhost:8000/ws
```

After opening the socket, authenticate with the first client message:

```json
{ "type": "auth", "token": "<access_token>" }
```

Events:

| Type | Meaning |
| --- | --- |
| `connection_status` | Authenticated connection handshake |
| `pong` | Reply to client `ping` |
| `order_created` | Manual order created |
| `order_updated` | Order updated |
| `order_deleted` | Order deleted |
| `orders_imported` | CSV import completed |
| `orders_cleared` | All orders deleted |
| `prices_updated` | Background price refresh completed |

## Price Refresh Workflow

The app owns price refreshes through lightweight FastAPI background jobs; there is no Windows scheduled task dependency.

- `POST /api/prices/refresh-if-needed`: protected endpoint that queues a background refresh only when cached prices are missing or stale.
- `POST /api/prices/fetch`: protected manual force-refresh endpoint used by the Portfolio `Fetch Prices` action.
- `PRICE_STALE_THRESHOLD_DAYS`: backend setting used by price services; default is `3`.
- `prices_updated`: WebSocket event emitted when a background refresh completes so open dashboard and portfolio views can reload current values.

The frontend triggers `refresh-if-needed` after login and when entering the dashboard with an existing session. Cached data remains visible while the refresh runs.

## Instrument Metadata And ISIN Resolution

- `POST /api/instruments/refresh`: protected force-refresh endpoint that queues provider-backed metadata refreshes for traditional instruments.
- `POST /api/instruments/sync`: protected endpoint that queues missing metadata refreshes where useful.
- Crypto metadata refreshes complete without external fund providers.
- Manual ISIN overrides and OpenFIGI-derived mappings are stored in SQLite.

## Local Data

User-specific runtime files are intentionally ignored by Git:

- `data/investit.sqlite3`
- `data/investit.sqlite3-wal`
- `data/investit.sqlite3-shm`
- `data/backups/`
- `data/*.lock`

Public-safe sample data is kept under `data/examples/`.

## Raspberry Pi Deployment

The Pi deployment uses Docker Compose with a localhost-bound web proxy and an internal-only backend service. Put Tailscale Serve in front of the web proxy and do not publish the backend port.

See [Raspberry Pi Deployment](DEPLOYMENT_PI.md) for the production runbook, including SQLite backup and restore.

Generated caches and test reports are ignored and can be deleted safely:

- `.cache/`
- `.pytest_cache/`
- `.ruff_cache/`
- `.serena/`
- `frontend/test-results/`
- `frontend/playwright-report/`
- `frontend/dist/`
