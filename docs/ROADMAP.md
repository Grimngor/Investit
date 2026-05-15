# Roadmap

## Current Stabilization

- Keep backend on port `8000` and frontend on port `5174`.
- Keep Python tooling on root `.venv`.
- Keep backend tests, Ruff checks, frontend build, Vitest, and Playwright green.
- Keep Playwright isolated from live user data through `.cache/e2e-data`.

## Recently Completed

- Order and dashboard router logic moved toward service classes.
- Price validation and async retry utilities added for provider calls.
- JSON writes centralized through `StorageService` with sidecar locks.
- Instrument metadata routes added to the FastAPI app.
- Background stale/missing price refresh added for login and dashboard entry.
- FastAPI startup moved to lifespan hooks and CORS origins moved to environment settings.
- Login now accepts username or email, with optional email and full name at registration.
- Geography charts now support country-level allocation, Europe collapse, and max-entry `Others` grouping.
- Position calculations now sort finalized orders chronologically before sell and cost-basis logic.
- Portfolio read and summary endpoints now delegate to `PortfolioService`; legacy holdings write endpoints were removed.
- Runtime data was untracked for public-safe publishing, with sample files added under `data/examples/`.
- Obsolete scripts, scaffold frontend files, local tool metadata, and generated artifacts were cleaned up or ignored.
- Documentation consolidated into the current docs set.
- Added frontend coverage for manual sell orders.
- Replaced query-string WebSocket tokens with first-message authentication.
- Added lightweight in-process background job tracking for provider-heavy price and instrument metadata refreshes.
- Added OpenFIGI-backed ISIN resolution with local manual overrides and provider-derived JSON cache.
- Reviewed public service methods for one-line docstrings and type hints.
- Migrated runtime persistence from JSON files to SQLite and renamed the local `test` user to `grimngor`.
- Added Docker Compose deployment shape for Raspberry Pi 5 with a localhost-bound web proxy, internal FastAPI backend, and SQLite data volume.
- Added Raspberry Pi deployment runbook covering Tailscale Serve, environment setup, release checks, and SQLite backup/restore.
- CSV reimports now skip already-present orders and the preview marks existing rows before import.
- Asset allocation charts now report Hong Kong exposure as China, label the instrument view as funds, exclude crypto from that fund chart, and draw in-slice percentages when they fit.

## Next Engineering Work

- Validate the Docker Compose deployment on the Raspberry Pi 5 hardware and record any ARM64 package or performance adjustments.
- Tailscale passwordless auth mode: trusted proxy identity headers, email allowlist, frontend no-login flow, and WebSocket header authentication.

## Later Work

- Add automated scheduled SQLite backups for the Pi deployment.
- Provider reliability layer: explicit fallback order, stale-cache fallback, provider health metrics, and clearer source attribution for price, metadata, and ISIN lookups.
- PWA or desktop packaging.
- Portfolio export and backup UI.
