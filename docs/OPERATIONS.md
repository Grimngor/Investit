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

## Monthly Price Update

The monthly update script is:

```powershell
.\scripts\maintenance\monthly_price_update.ps1
```

It expects the backend to be running on `http://localhost:8000`.

Set up the Windows scheduled task:

```powershell
.\scripts\maintenance\setup_monthly_task.ps1
```

Remove the task:

```powershell
.\scripts\maintenance\setup_monthly_task.ps1 -Uninstall
```

Authentication for the maintenance task uses `INVESTIT_DEFAULT_PASSWORD` when set. Do not rely on the fallback test password for real data.

## Local Data

User-specific JSON files are intentionally ignored by Git:

- `data/users.json`
- `data/orders.json`
- `data/prices.json`

Generated caches and test reports are ignored and can be deleted safely:

- `.cache/`
- `.pytest_cache/`
- `frontend/test-results/`
- `frontend/playwright-report/`
- `frontend/dist/`
