# InvestIt - Personal Portfolio Tracker

InvestIt is a personal portfolio tracking application for funds, ETFs, stocks, and crypto. It imports Spanish bank CSV order history, stores data locally as JSON, calculates portfolio metrics, and refreshes prices/metadata from external market data providers.

## Stack

- Backend: FastAPI, Python 3.12, JWT auth, JSON storage through `StorageService`
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
- [Roadmap](docs/ROADMAP.md)

## Runtime Notes

- Register with a username and password; email and full name are optional.
- Log in with either username or email when an email exists for the user.
- Cached prices render immediately. The app queues a background refresh after login and on dashboard entry only when prices are missing or stale.
- The manual Portfolio `Fetch Prices` action still forces a refresh.
- Geography allocation is shown by country, with an optional Europe collapse and automatic `Others` grouping only when a chart has more than 15 entries.

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
