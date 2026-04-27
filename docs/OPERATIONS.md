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

## WebSocket Events

Connect with:

```text
ws://localhost:8000/ws?token=<access_token>
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

The app owns price refreshes; there is no Windows scheduled task dependency.

- `POST /api/prices/refresh-if-needed`: protected endpoint that queues a background refresh only when cached prices are missing or stale.
- `POST /api/prices/fetch`: protected manual force-refresh endpoint used by the Portfolio `Fetch Prices` action.
- `PRICE_STALE_THRESHOLD_DAYS`: backend setting used by price services; default is `3`.
- `prices_updated`: WebSocket event emitted when a background refresh completes so open dashboard and portfolio views can reload current values.

The frontend triggers `refresh-if-needed` after login and when entering the dashboard with an existing session. Cached data remains visible while the refresh runs.

## Local Data

User-specific JSON files are intentionally ignored by Git:

- `data/users.json`
- `data/orders.json`
- `data/prices.json`
- `data/settings.json` (legacy local file; not used by the app)
- `data/backups/`
- `data/*.lock`

Generated caches and test reports are ignored and can be deleted safely:

- `.cache/`
- `.pytest_cache/`
- `frontend/test-results/`
- `frontend/playwright-report/`
- `frontend/dist/`
