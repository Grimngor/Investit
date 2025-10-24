# InvestIt - Task Tracker

**Last Updated:** October 24, 2025

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

### 8. Documentation
- [x] 8.1. Update README.md
- [x] 8.2. Update CONTRIBUTING.md
- [x] 8.3. Update USER_GUIDE.md
- [x] 8.4. OpenAPI/Swagger docs at /docs
- [ ] 8.5. Document data migration process
- [ ] 8.6. Create GitHub issue templates (optional)
- [ ] 8.7. Create GitHub PR template (optional)

### 9. Final Review & Validation
- [ ] 9.1. Manual walkthrough of all features
- [x] 9.2. Verify all tests pass (130 backend tests)
- [ ] 9.3. Add frontend E2E tests
- [ ] 9.4. Security audit
- [ ] 9.5. Performance review (API < 300ms)
- [x] 9.6. Final linting and formatting check
- [ ] 9.7. Verify launcher scripts
- [ ] 9.8. Test complete user flow

---

## Current Stats

- **Backend:** 33+ Python files, 130 passing tests, 72% coverage
- **Frontend:** 80+ Vue/TypeScript files with Chart.js integration
- **API Endpoints:** 20+ (auth, portfolio, orders, dashboard, websocket)
- **Status:** Section 7 & 8 mostly complete, Section 9 in progress
