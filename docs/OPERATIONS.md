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
- `GOOGLE_OAUTH_CLIENT_ID` and `GOOGLE_OAUTH_CLIENT_SECRET`: optional Google OAuth credentials for Gmail-backed MyInvestor import.
- `GOOGLE_LOGIN_REDIRECT_URI`: optional explicit OAuth callback URL for Google login/register.
- `GMAIL_OAUTH_REDIRECT_URI`: optional explicit OAuth callback URL for deployed Gmail import.
- `GMAIL_IMPORT_MAX_MESSAGES`: normal Gmail scan size after initial import history exists; default is `20`.
- `GMAIL_IMPORT_INITIAL_MAX_MESSAGES`: first-run Gmail backfill scan size; default is `100`.
- `GMAIL_IMPORT_QUERY`: Gmail search query used to find MyInvestor order emails.

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
| `orders_imported` | CSV or Gmail import completed |
| `orders_cleared` | All orders deleted |
| `prices_updated` | Background price refresh completed |

## Price Refresh Workflow

The app owns price refreshes through lightweight FastAPI background jobs; there is no Windows scheduled task dependency.

- `POST /api/prices/refresh-if-needed`: protected endpoint that queues a background refresh only when cached prices are missing or stale.
- `POST /api/prices/fetch`: protected manual force-refresh endpoint used by the Portfolio `Fetch Prices` action.
- `PRICE_STALE_THRESHOLD_DAYS`: backend setting used by price services; default is `3`.
- `prices_updated`: WebSocket event emitted when a background refresh completes so open dashboard and portfolio views can reload current values.

The frontend triggers `refresh-if-needed` after login and when entering the dashboard with an existing session. Cached data remains visible while the refresh runs.

## Gmail MyInvestor Import

Gmail import is optional and remains preview-first:

- Allowlisted users can use Google login/register and grant Gmail read consent in the same flow.
- The user connects Gmail from the Portfolio `Import` dropdown.
- InvestIt requests `gmail.readonly`, searches candidate MyInvestor messages, parses order confirmations, and shows a preview.
- Exact duplicates are skipped as already present.
- Close duplicates are marked for review and are not selected by default.
- Selected imports are re-fetched server-side before writing orders.
- Gmail message IDs and import status are stored in SQLite.

The feature requires Google OAuth credentials in `.env`. Google login is shown only when OAuth credentials and the email allowlist are configured. For public users, the Google OAuth app may need verification because Gmail read-only access is a restricted scope.

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

Prefer the app UI for editing portfolio data. The Portfolio and Orders screens should own normal order imports, manual order edits, and derived holdings changes. Use direct SQLite maintenance only for operations that do not have UI support yet, and take a backup first.

Create a local SQLite backup from PowerShell:

```powershell
New-Item -ItemType Directory -Force data\backups
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
Copy-Item data\investit.sqlite3 "data\backups\investit_backup_$stamp.sqlite3"
```

Inspect users without modifying the database:

```powershell
.\.venv\Scripts\python.exe -c "import sqlite3; c = sqlite3.connect('data/investit.sqlite3'); print([r[0] for r in c.execute('select username from users order by username')]); c.close()"
```

For user profile fields that are not editable in the UI, use the app persistence layer instead of hand-editing SQLite rows:

```powershell
.\.venv\Scripts\python.exe -c "import sys; sys.path.insert(0, 'backend'); from app.models.persistence import load_user_data, save_user_data; u = load_user_data('<username>'); u['full_name'] = 'Your Name'; u['email'] = 'you@example.com'; save_user_data('<username>', u)"
```

Do not edit password hashes directly unless you are using `app.services.auth.get_password_hash` or a dedicated maintenance command.

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
