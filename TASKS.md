# InvestIt - Task Tracker

**Last Updated:** October 25, 2025

### 1. Project Cleanup & File Review
- [x] 1.1. Review and remove obsolete files
- [x] 1.2. Format all code files
- [x] 1.3. Initialize git repository
- [x] 1.4. Validate launcher scripts

### 2. Testing & Verification
- [x] 2.1. Write smoke tests
- [x] 2.2. Write authentication tests
- [x] 2.3. Write portfolio CRUD tests
- [x] 2.4. Add test coverage reporting (72% achieved)
- [ ] 2.5. Add frontend E2E tests (Playwright)

### 3. Data Model & Structure
- [x] 3.1. Migrate from holdings to orders model
- [x] 3.2. Create migration script
- [x] 3.3. Create JSON files (orders, instruments, prices, settings)
- [x] 3.4. Implement ISIN mapping
- [x] 3.5. Add atomic JSON writes with file locking
- [x] 3.6. Add backup/export functionality

### 4. Service Layer & Utils
- [x] 4.1. Implement CSV parser with Spanish format support
- [x] 4.2. Implement validators for order/CSV validation
- [x] 4.3. Create compute service for PnL calculations
- [x] 4.4. Create storage service for JSON I/O
- [x] 4.5. Rename data_fetcher to pricing_service

### 5. Backend Features (PRD)
- [x] 5.1. CSV import endpoint
- [x] 5.2. Manual order CRUD endpoints
- [x] 5.3. Orders history with filtering/sorting
- [x] 5.4. Dashboard KPI calculations
- [x] 5.5. Allocation pie charts data
- [x] 5.6. Line chart data (invested vs current)
- [x] 5.7. WebSocket real-time updates
- [x] 5.8. Stale price indicators
- [x] 5.9. Backend logging infrastructure
- [x] 5.10. Yahoo Finance price fetching service
- [x] 5.11. Automatic price caching (24-hour TTL)
- [x] 5.12. Price fetch endpoint with background tasks
- [x] 5.13. Historical price tracking for accurate gain/loss
- [x] 5.14. Automatic scheduled task registration
- [x] 5.15. Morningstar integration for fund metadata
- [x] 5.16. YahooQuery integration for sector allocations
- [x] 5.17. Hybrid metadata sourcing (Morningstar primary, YahooQuery fallback)

### 6. Code Quality
- [x] 6.1. Format Python files (Ruff with tabs)
- [x] 6.2. Add type hints to all functions
- [x] 6.3. Add docstrings
- [x] 6.4. Remove unused imports and dead code
- [x] 6.5. Fix deprecation warnings

### 7. Frontend Features (PRD)
- [x] 7.1. Dashboard view with KPIs
- [x] 7.2. Line chart component (invested vs current)
- [x] 7.3. Allocation pie charts (4 types)
- [x] 7.4. Stale price indicators UI
- [x] 7.5. Portfolio summary table
- [x] 7.6. CSV import UI with drag-and-drop
- [x] 7.7. Manual order form (add/edit/delete)
- [x] 7.8. Instrument metadata API
- [x] 7.9. Orders history table
- [x] 7.10. Filter and sort controls
- [x] 7.11. Running position display
- [x] 7.12. Pagination controls
- [x] 7.13. Chart.js integration with dark mode
- [x] 7.14. Frontend logging infrastructure
- [x] 7.15. Chart percentage calculation and sorting
- [x] 7.16. Gain/loss cards with percentage and +/- signs
- [x] 7.17. Euro symbol positioning (after amount with space)
- [x] 7.18. Unified SummaryCard component across views
- [ ] 7.19. CSV import preview/confirmation modal with edit capability

### 8. Documentation
- [x] 8.1. Update README.md
- [x] 8.2. Update CONTRIBUTING.md
- [x] 8.3. Update USER_GUIDE.md
- [x] 8.4. OpenAPI/Swagger docs at /docs
- [x] 8.5. Document historical price implementation (HISTORICAL_PRICE_IMPLEMENTATION.md)
- [x] 8.6. Document monthly update setup (MONTHLY_UPDATE_SETUP.md)
- [x] 8.7. Document logging infrastructure (docs/LOGGING.md)
- [x] 8.8. Document launcher scripts (LAUNCHER_GUIDE.md)

### 9. Code Quality & Refactoring
- [x] 9.1. Fix CSV parser to use 'Importe neto' (net amount)
- [x] 9.2. Fix Morningstar service language parameter
- [x] 9.3. Add /api/instruments/refresh endpoint
- [x] 9.4. Add country code → name mapping for dashboard
- [x] 9.5. Fix sell order handling in compute service
- [ ] 9.6. Refactor large price-fetch function (prices.fetch_and_update_prices) [PLR0915: 60 statements]
- [ ] 9.7. Refactor dashboard allocations function [PLR0915: 62 statements]
- [ ] 9.8. Reduce branches in refresh_instrument_metadata [PLR0912: 13 branches]
- [ ] 9.9. Reduce branches in Morningstar get_fund_metadata [PLR0912: 13 branches]
- [ ] 9.10. Extract magic values to constants (ISIN prefix length)

### 10. Resilience & Production Readiness
- [ ] 10.1. Add cache warming task on startup
- [ ] 10.2. Add resilience around Morningstar rate-limiting (retry with exponential backoff)
- [ ] 10.3. Add retry logic for YahooQuery API failures
- [ ] 10.4. Add circuit breaker pattern for external API calls
- [ ] 10.5. Add health check endpoint with dependency status
- [ ] 10.6. Add metrics collection (API latency, cache hit rate, error rate)

### 11. Data Quality & Validation
- [ ] 11.1. Add price validation (compare historical vs calculated, flag discrepancies)
- [ ] 11.2. Add data integrity checks (detect missing ISINs, invalid dates)
- [ ] 11.3. Create admin endpoint to trigger price backfill for specific users/ISINs
- [ ] 11.4. Add instrument metadata validation (check for missing sectors/regions)
- [ ] 11.5. Create data quality dashboard/report

### 12. Final Review & Validation
- [ ] 12.1. Manual walkthrough of all features
- [x] 12.2. Verify all tests pass (130 backend tests)
- [ ] 12.3. Add frontend E2E tests
- [ ] 12.4. Security audit
- [ ] 12.5. Performance review (API < 300ms)
- [x] 12.6. Final linting and formatting check
- [ ] 12.7. Verify launcher scripts
- [ ] 12.8. Test complete user flow
- [ ] 12.9. Review and verify .gitignore (data/, logs/, venv/, node_modules/, etc.)

---

## Current Stats

- **Backend:** 35+ Python files, 130 passing tests, 72% coverage
- **Frontend:** 80+ Vue/TypeScript files with Chart.js integration
- **API Endpoints:** 25+ (auth, portfolio, orders, dashboard, prices, instruments, websocket)
- **Data Sources:** yfinance (prices + historical), mstarpy (Morningstar metadata), yahooquery (sector allocations)
- **Status:** Core features complete (Sections 1-7), refactoring & resilience pending (Sections 10-12)
