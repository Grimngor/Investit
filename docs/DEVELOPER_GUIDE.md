# InvestIt Developer Guide

## Local Environment

Use the repository-root `.venv` for Python work.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env

cd frontend
npm install
Copy-Item .env.example .env
cd ..
```

Canonical development ports:

- Backend: `http://localhost:8000`
- Frontend: `http://localhost:5174`

The repository intentionally keeps a split layout: backend Python code and shared scripts/docs live at the root and under `backend/`; the Vue/Vite app owns its own config, package files, and tests under `frontend/`.

`SECRET_KEY` must be changed before any shared or hosted deployment. `FINNHUB_API_KEY` and `OPENFIGI_API_KEY` are optional; unauthenticated providers are used when they are blank.

For non-local frontends, set `BACKEND_CORS_ORIGINS` in `.env` to a JSON list of allowed origins.

Real runtime data stays in ignored files under `data/`. Public-safe examples are stored under `data/examples/`.

Runtime persistence uses SQLite by default:

- Database file: `data/investit.sqlite3`
- Backend setting: `PERSISTENCE_BACKEND=sqlite`
- Relative `DATABASE_PATH` values are resolved from the repository root, even when Uvicorn starts from `backend/`.
- Tests use isolated temporary SQLite databases.

## Launcher Scripts

```powershell
.\start-backend.ps1
.\start-fullstack.ps1
.\stop-all.ps1
```

`start-backend.ps1` starts FastAPI with Uvicorn on port `8000`.

`start-fullstack.ps1` starts the backend on `8000`, starts Vite on `5174`, and opens the frontend.

`stop-all.ps1` stops Python and Node processes. Use it carefully if other Python or Node apps are running.

## Manual Startup

Backend:

```powershell
cd backend
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Frontend:

```powershell
cd frontend
npm run dev -- --host 127.0.0.1 --port 5174
```

## Backend Tests And Quality

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests -q
.\.venv\Scripts\python.exe -m ruff check backend
.\.venv\Scripts\python.exe -m ruff format --check backend
```

Focused examples:

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests\test_orders.py -q
.\.venv\Scripts\python.exe -m pytest backend\tests\test_instruments.py -q
```

Ruff is configured in `backend/pyproject.toml` for Python 3.12, 140 character lines, and tab indentation.

## Frontend Tests And Quality

```powershell
cd frontend
npm run build
npx vitest run
npm run test:e2e
```

Playwright starts the backend and frontend automatically:

- Backend command runs from `backend/` on `127.0.0.1:8000`.
- Backend uses isolated E2E data in `.cache/e2e-data`.
- Frontend runs on `127.0.0.1:5174`.

Stop any manually running local servers before `npm run test:e2e`; Playwright is configured not to reuse existing servers so tests stay isolated.

## Pre-Commit

`.pre-commit-config.yaml` runs:

- Ruff lint autofix and format
- Fast backend pytest on pre-commit
- Full backend pytest on pre-push
- Standard whitespace, YAML, merge-conflict, and large-file checks

Playwright is intentionally not a pre-commit hook. Run it manually before release-oriented work.

## Maintenance Scripts

- `scripts/maintenance/create_test_user.py`: create a local development user.
- `scripts/maintenance/backfill_order_prices.py`: backfill missing historical order prices for local data.

Scripts not listed here should not be added as scratch probes. Prefer backend tests or documented dev scripts.

## Troubleshooting

- Backend unreachable: verify `http://localhost:8000/health` and check `backend/logs/error.log`.
- Frontend cannot register or log in: confirm the frontend API URL points to `http://localhost:8000`.
- Stale prices: use Portfolio `Fetch Prices` for a manual force refresh, or check `POST /api/prices/refresh-if-needed` and the `prices_updated` WebSocket event.
- ISIN resolution: local manual overrides and OpenFIGI-derived mappings are stored in SQLite.
- Vitest scans inaccessible folders: `.pytest_cache/**` is excluded in `frontend/vitest.config.ts`.
- Route mismatch: run `.\scripts\dev\verify_backend.ps1` after starting the backend.
