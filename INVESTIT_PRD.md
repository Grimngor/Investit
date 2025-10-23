# PRD v2 — Investing Web App (Server-backed MVP → PWA post-MVP)

## 1) Overview
- **Purpose:** A personal investing web app for tracking passive index funds and ETFs. Initially for friends & family (≈5 users); long-term goal — open-source.
- **Scope:**
  - Import bank CSVs to record fund purchases/redemptions.
  - Fetch or manually update current NAV/prices.
  - Display portfolio evolution, PnL, and summaries.
- **MVP Architecture:** **Server-backed** (FastAPI + Vue).  
  **Post-MVP:** migrate to **hostless PWA** (and/or desktop/mobile packaging) once stable.

---

## 2) Stack & Architecture

### Backend
- **Framework:** Python **FastAPI** (async).  
- **Responsibilities:** CSV parsing, order CRUD, price/NAV fetching & caching, allocations metadata, auth, and WebSocket broadcasts.
- **Storage (initial):** **Server-side JSON** files (`orders.json`, `instruments.json`, `prices.json`, `settings.json`).  
  - Atomic writes (temp file + rename), file-level lock for concurrent requests, daily rotated backups/export.
- **Background work:** FastAPI `BackgroundTasks` for short I/O (no Celery/Redis).  
- **Security:** OpenFIGI key in server **env vars**; no secrets in client.

### Frontend
- **Vue 3 + Reka UI**; SPA consuming the FastAPI REST/WebSocket API.
- **Charts:** **Chart.js** for line & pie/doughnut charts.
- **IDE:** VS Code.

### Data Providers (server-side fetch)
- **Prices/NAV:** Yahoo Finance (unofficial) via server fetch (e.g., `yfinance`/HTTP); cached daily.
- **Identifier mapping:** **OpenFIGI** (ISIN → symbols), cached to `instruments.json`.
- **CSV Import:** Primary source of orders (user uploads to backend).

### Real-Time Updates
- **WebSockets:** Server pushes portfolio/price refresh events to the client after imports/edits/fetches.

### Privacy
- Personal data and orders stored on the server you control (small trusted cohort).  
- No third-party persistence; exports available on demand.

---

## 3) Navigation (3 Tabs)

### A) **Dashboard** (default)
- **KPIs:** Total invested, current value, absolute & % PnL.
- **Line Chart** (two series):
  1) **Invested value over time** = cumulative net cash flows (sum of `amount_eur` by date; buys positive, redemptions negative).
  2) **Current value over time** = for each date, `Σ(shares_held(date) × price(date))` across instruments. Use last available price for gaps; mark **stale** per policy.
- **Allocation Pie Charts:**
  - **By Instrument** (fund/ETF/crypto/bond buckets).
  - **By Geography** (from instrument metadata): toggle to collapse EU members into **“Europe”**.
  - **By Industry/Sector** (from instrument metadata).
  - **By Asset Type** (Funds, ETFs, Crypto, Bonds, … even if some buckets are empty initially).
- Manual override UI for geo/sector if provider data missing; cached server-side.

### B) **Portfolio Management**
- **CSV Importer** - Accept bank CSV headers (Spanish):  
  `Fecha de la orden, ISIN, Importe estimado, Nº de participaciones, Estado`.
- **Assumptions & Rules:**
  - Encoding: handle header `Nº` (may appear as `NÂº`).
  - Date format: **DD/MM/YYYY**.
  - Amount parsing: accept `,` or `.` decimals; strip `" EUR"`.
  - `order_type`: derived from amount sign (negative = sell).
  - Shares on sells: decrement position even if CSV lists positive shares.
  - Skip rows with `Estado = "Rechazada"`.
  - Validate date/numeric fields; return per-row error report.
- **Manual Orders:** Add/edit/delete orders with same schema.
- **Result:** Normalized entries persisted to `orders.json`; WebSocket broadcast to refresh Dashboard.

### C) **Orders History**
- Filterable, sortable table of all orders:
  - Columns: `date`, `isin`, `instrument_name`, `amount_eur`, `shares`, `order_type (buy/sell)`, `status`, `notes`.
  - Running position per instrument (avg cost & shares).

---

## 4) Data Model

### Core Entities

**Order**
```json
{
  "date": "DD-MM-YYYY",
  "isin": "IE00BYX5NX33",
  "amount_eur": 300.00,
  "shares": 24.624,
  "status": "Finalizada",
  "notes": ""
}
```

**Price**
```json
{ "date": "DD-MM-YYYY", "symbol": "IE00BYX5NX33.SUFFIX", "price": 12.34 }
```

**Instrument (mapping & metadata)**
```json
{
  "isin": "IE00BYX5NX33",
  "symbol": "IE00BYX5NX33.SG",
  "name": "<Fund Name>",
  "type": "fund|etf|crypto|bond",
  "geo_allocation": { "US": 0.52, "UK": 0.05, "DE": 0.04, "ES": 0.03, "Other Europe": 0.10, "APAC": 0.20, "Other": 0.06 },
  "sector_allocation": { "Tech": 0.23, "Financials": 0.15 }
}
```

- **Symbol mapping:** `Instrument.symbol` (e.g., `IE00BYX5NX33.SG`) is the price source and is maintained server-side in `instruments.json`.  
- **Standards:** Countries as **ISO-3166** codes; sectors follow a fixed list (e.g., **GICS** names).

---

## 5) Development Guidelines
- **Simplicity:** Prefer clear solutions over framework complexity.
- **Code Reuse:** Centralize utilities (`utils/formatters.py|.js`, `utils/parser.py`).
- **Clean Codebase:** Maintain organized project files and clear documentation. Feature-oriented folders (frontend/src/features/ …).  
- **API Integration:** Always verify the latest documentation when integrating with external APIs.
- **Open-Source Readiness:** Maintain README, `CONTRIBUTING.md`, issue/PR templates.
- **Security:** No secrets in client; server reads keys from env; HTTPS; basic auth for MVP.
- **Testing Targets:** Unit (70%), integration (20%), E2E (10%).

---

## 6) Data Handling
- **Persistence:** Server-side JSON with atomic writes + lock; daily backup/export.
- **Caching:** Daily price fetch; HTTP-429 back-off; display **“stale”** badge if price age > policy (e.g., 3 days).
- **Computation:**
  - Positions: per-ISIN running shares (sum of buys − sells).
  - Average cost: moving-average per instrument.
  - Current value: `Σ(shares × latest_price)`.
  - PnL: `current_value − total_invested`.
- **Exposure data:** Pull from provider/factsheet when available; else manual entry; always cached.

---

## 7) Non-Functional Requirements
| Area | Target |
|---|---|
| Performance | Dashboard median API < 300 ms; page render < 2 s |
| Availability | Self-hosted; graceful degradation on provider outage |
| Security | HTTPS; env-stored keys; auth; audit logs of imports/edits |
| Data Freshness | Mark price **stale** if last NAV/price > 3 days |
| Reliability | JSON backups; deterministic recompute from orders |
| Maintainability | Storage adapter isolates JSON now, SQLite later |

---

## 8) Future Enhancements
- **SQLite** migration for transactions/concurrency; ORM models.
- **PWA (hostless) migration:** Serve static SPA + service worker; move fetch to client; per-user secrets stored locally; or package with **Tauri/Capacitor**.
- **Minimal proxy endpoints** if adopting hostless PWA but CORS/rate-limits need a shim.
- **More providers** (e.g., Finnhub for ETFs/equities).
- **Notifications** (price alerts; email/web push).

---

## 9) Project Structure
```
investing-web-app/
├─ backend/
│  └─ app/
│     ├─ main.py                 # FastAPI app entry
│     ├─ config.py               # settings (env)
│     ├─ routes/
│     │  ├─ orders.py            # CSV upload + CRUD
│     │  ├─ prices.py            # fetch/cache quotes
│     │  ├─ instruments.py       # mapping + metadata
│     │  └─ ws.py                # WebSocket endpoints
│     ├─ services/
│     │  ├─ pricing_service.py   # Yahoo fetch/cache
│     │  ├─ figi_service.py      # OpenFIGI lookup
│     │  ├─ storage_service.py   # JSON I/O (atomic/locks)
│     │  └─ compute_service.py   # PnL/positions/allocations
│     ├─ utils/
│     │  ├─ csv_parser.py
│     │  └─ validators.py
│     └─ data/                   # server JSON store
│        ├─ orders.json
│        ├─ instruments.json
│        ├─ prices.json
│        └─ settings.json
├─ frontend/
│  ├─ public/index.html
│  └─ src/
│     ├─ features/
│     │  ├─ dashboard/
│     │  │  ├─ Dashboard.vue
│     │  │  └─ dashboardStore.js
│     │  ├─ portfolio/
│     │  │  ├─ PortfolioManagement.vue
│     │  │  └─ csvClientHints.js
│     │  └─ orders/
│     │     └─ OrdersHistory.vue
│     ├─ charts/
│     │  ├─ LineInvestedVsCurrent.vue
│     │  └─ PieAllocations.vue
│     ├─ services/
│     │  ├─ api_client.js        # REST/WebSocket client
│     │  └─ mapping_client.js
│     ├─ App.vue
│     └─ main.js
├─ docs/PRD.md
└─ README.md
```

---

## 10) Implementation Notes
- **Endpoints (REST):**
  - `POST /orders/import-csv` (multipart CSV) → parsed rows + errors.
  - `GET/POST/PUT/DELETE /orders`
  - `GET /prices?symbol=...&range=...` (server cache)
  - `GET/PUT /instruments/:isin` (symbol, geo/sector)
- **WebSockets:** `ws://.../ws/updates` broadcasts `{type:"orders|prices|instruments", ids:[...]}`.
- **Rates/Back-off:** On 429/5xx, exponential back-off; write cache with timestamp.
- **Atomic JSON writes:** write `*.tmp` + `fsync` + `rename`; file lock during write.

---

## 11) Documentation Format
- Markdown PRD (this file) for Git versioning and AI assistant compatibility (GitHub Copilot, Cursor).
- Inline code comments reference PRD sections for traceability.
