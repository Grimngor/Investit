# Roadmap

## Current Stabilization

- Keep the local development backend on port `8000` and Vite frontend on port `5174`.
- Keep Raspberry Pi deployment traffic behind the localhost-bound Compose web proxy on `INVESTIT_WEB_PORT`, currently `8080`.
- Keep Python tooling on the repository root `.venv`.
- Keep backend tests, Ruff checks, frontend build, Vitest, and Playwright green before releases.
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
- Migrated runtime persistence from JSON files to SQLite and renamed the local `test` user to the primary user account.
- Added Docker Compose deployment shape for Raspberry Pi 5 with a localhost-bound web proxy, internal FastAPI backend, and SQLite data volume.
- Added Raspberry Pi deployment runbook covering Tailscale Serve, environment setup, release checks, and SQLite backup/restore.
- CSV reimports now skip already-present orders and the preview marks existing rows before import.
- Asset allocation charts now report Hong Kong exposure as China, label the instrument view as funds, exclude crypto from that fund chart, and draw in-slice percentages when they fit.
- Added a Raspberry Pi deployment validation script and runbook section for ARM64 Compose smoke checks.
- Added optional hybrid Tailscale Serve passwordless auth with trusted identity headers, email allowlisting, normal JWT issuance, and password-login fallback.
- Validated the Raspberry Pi 5 deployment on Debian GNU/Linux 13 trixie ARM64 with Docker 29.4.3 and Docker Compose v5.1.3; build, startup, health check, localhost-only web exposure, internal backend networking, Tailscale Serve, and container logs all passed without warnings.
- Documented the Pi deployment HTTPS path through Tailscale Serve, why direct local HTTP shows browser security warnings, URL customization options, and the local-to-Pi SQLite transfer flow.
- Documented local SQLite backup and safe primary-user profile-editing guidance.
- Pruned the local SQLite runtime database back to only the primary user after creating timestamped backups.
- Removed obsolete empty project folders and disposable generated artifacts where Windows locks allowed cleanup.
- Improved mobile frontend readiness for navigation, orders tables, order editing, CSV preview, and responsive page actions.
- Added Playwright phone/tablet projects, fixed SQLite E2E isolation through `DATABASE_PATH`, and added focused Orders E2E coverage for mobile card rendering without duplicate desktop tables.
- Verified the frontend through Browser screenshots on phone and tablet viewports for dashboard, portfolio, orders, auth, CSV preview, and order edit modal with no horizontal overflow in checked screens.
- Added a provider reliability layer with explicit fallback ordering, stale-cache price fallback, provider health metrics, and source attribution for price, metadata, and ISIN lookups.
- Moved Portfolio CSV import and manual order entry into responsive modals opened from page actions, removing the need to scroll to those forms.
- Added Portfolio Performance range controls (`1M`, `3M`, `6M`, `1Y`, `3Y`, `Max`) and `DD/MM/YY` chart date formatting.
- Standardized Asset Allocation pie chart sizing and added responsive allocation legends.
- Fixed short Portfolio Performance ranges for sparse time-series data, made desktop allocation legends visible by default, improved legend contrast and mobile legend scrolling, and unified Portfolio page action button styling with an icon-only refresh action.
- Added a Gmail-backed MyInvestor order import flow from the Portfolio page, including Gmail OAuth setup, read-only message scanning, MyInvestor email parsing, preview/selection UI, duplicate detection, first-run backfill scanning, and local processed-message tracking. See [temporary Gmail import notes](TEMP_GMAIL_MYINVESTOR_IMPORT.md).
- Unified Portfolio CSV import, Gmail import, and manual order actions under one `Import` dropdown ordered Gmail, CSV, then manual order.
- Removed the Portfolio manual refresh button and kept portfolio data refreshing automatically after imports, manual order changes, price WebSocket events, and page entry.
- Fixed desktop Asset Allocation pie chart alignment when responsive legends are visible.
- Added smart CSV/Gmail import duplicate review for close ISIN/type/share/date/amount matches, with review rows unchecked by default and existing-order comparisons shown in preview tables.
- Preserved saved Gmail OAuth connections across SQLite user/order/price rewrites by avoiding user-row delete/reinsert cascades for existing users.

## Next Work

- Brainstorm standarizing the button colors and style depending on the type of button and state.

## Later Work

- Add a browser-friendly Raspberry Pi access path with Cloudflare Tunnel and Cloudflare Access for `javiansoleaga.es`, keeping the Pi behind a localhost-bound web proxy while allowing trusted users to authenticate without installing Tailscale. See [temporary Cloudflare Access notes](TEMP_CLOUDFLARE_TUNNEL_ACCESS.md).
- Add automated scheduled SQLite backups for the Pi deployment.
- Portfolio export and backup UI so live data can be exported, backed up, and restored from the app instead of relying only on command-line SQLite copies.
- PWA or desktop packaging for installing InvestIt as an app-like experience on trusted devices, either through browser PWA support or a lightweight desktop wrapper.
