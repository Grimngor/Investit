# InvestIt - Personal Portfolio Tracker

InvestIt is a personal portfolio tracking application for funds, ETFs, stocks, and crypto. It imports Spanish bank CSV order history, stores data locally in SQLite, calculates portfolio metrics, and refreshes prices/metadata from external market data providers.

## Stack

- Backend: FastAPI, Python 3.12, JWT auth, SQLite persistence through `StorageService`
- Frontend: Vue 3, TypeScript, Vite, Tailwind CSS, Pinia, Chart.js
- Tests: Pytest, Vitest, Playwright
- Data providers: Yahoo Finance (`yfinance`, `yahooquery`) and Morningstar (`mstarpy`)

## Quick Start

Prerequisites:

- Python 3.12+
- Node.js 18+
- Windows PowerShell for the bundled launcher scripts

```powershell
# Backend dependencies
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env

# Frontend dependencies
cd frontend
npm install
Copy-Item .env.example .env
cd ..
```

Run the app:

```powershell
.\start-fullstack.ps1
```

Local URLs:

- Frontend: http://localhost:5174
- Backend API: http://localhost:8000
- API docs: http://localhost:8000/docs

Stop local servers:

```powershell
.\stop-all.ps1
```

## Documentation

- [Developer Guide](docs/DEVELOPER_GUIDE.md)
- [Orders Management](docs/ORDERS_MANAGEMENT.md)
- [Operations](docs/OPERATIONS.md)
- [Raspberry Pi Deployment](docs/DEPLOYMENT_PI.md)
- [Roadmap](docs/ROADMAP.md)

## Runtime Notes

- Register with a username and password; email and full name are optional.
- Log in with either username or email when an email exists for the user.
- Cached prices render immediately. The app queues a background refresh after login and on dashboard entry only when prices are missing or stale.
- The manual Portfolio `Fetch Prices` action still forces a refresh.
- Geography allocation is shown by country, with an optional Europe collapse and automatic `Others` grouping only when a chart has more than 15 entries.

## Data And Publishing

Runtime SQLite files in `data/` are local state and intentionally ignored by Git. Public-safe example files live in `data/examples/`.

Before publishing or sharing:

- Confirm `.env` and `frontend/.env` are ignored.
- Keep real `data/investit.sqlite3`, `data/investit.sqlite3-wal`, `data/investit.sqlite3-shm`, and `data/backups/` local.
- Use the sample files in `data/examples/` for documentation, tests, or onboarding examples.
- Run the verification commands below.

## Raspberry Pi Deployment

The Docker Compose deployment target is a private Raspberry Pi 5 behind Tailscale Serve. The web container binds only to `127.0.0.1`, proxies `/api` and `/ws` to the internal backend container, and stores SQLite data under `data/`.

See [Raspberry Pi Deployment](docs/DEPLOYMENT_PI.md) for first install, Tailscale Serve, backup/restore, upgrade, and release checks.

## Local Docker Test

Docker testing does not use the Python virtual environment or the local Vite server.

```powershell
docker compose build
docker compose up -d
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8080/health
```

Open http://127.0.0.1:8080. To avoid touching local runtime data, set `INVESTIT_DATA_DIR=.cache/docker-data` in `.env` before starting Compose.

## Verification

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests -q
.\.venv\Scripts\python.exe -m ruff check backend
.\.venv\Scripts\python.exe -m ruff format --check backend

cd frontend
npm run build
npx vitest run
npm run test:e2e
```
