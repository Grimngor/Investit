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
- Documentation consolidated into the current docs set.

## Next Engineering Work

- Finish moving portfolio router persistence into service classes.
- Add service-level tests for portfolio write operations.
- Add frontend tests for order form sell behavior.
- Replace blocking provider calls in request paths with background jobs where needed.
- Review all public service methods for one-line docstrings and type hints.

## Later Work

- SQLite migration.
- Production deployment guide.
- More robust provider fallback strategy.
- PWA or desktop packaging.
- Portfolio export and backup UI.
