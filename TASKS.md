# TASKS.md

## Project Cleanup & Alignment Plan (per PRD v2)

### CRITICAL FINDINGS (COMPLETED)
- [x] ✅ All backend test files were corrupted (null bytes) - DELETED
- [x] ✅ Project is not a git repository - needs initialization
- [x] ✅ Current data model uses `holdings` instead of `orders` (PRD mismatch)
- [x] ✅ Services naming differs from PRD (finnhub.py vs pricing_service.py)
- [x] ✅ Missing utils/ directory for parsers and validators
- [x] ✅ Missing isin_ticker_mapping.json file

### 1. Project Cleanup & File Review
- [x] 1.1. List all files and directories in the project.
- [x] 1.2. Review each file for relevance, removing obsolete or unused files.
- [x] 1.3. Check for duplicate, temporary, or backup files and remove them.
- [x] 1.4. Ensure all code files have minimal, clean, and consistent formatting (Black for Python, Prettier for JS/Vue).
- [ ] 1.5. Validate that all scripts (e.g., .bat, .ps1, .py) execute without errors.
- [x] 1.6. Initialize git repository for version control.

### 2. Data Model & Structure Alignment
- [ ] 2.1. Update data model from `holdings` to `orders` as per PRD.
- [ ] 2.2. Create data migration script for existing users.
- [ ] 2.3. Add missing JSON files: orders.json, instruments.json, prices.json, settings.json.
- [ ] 2.4. Implement atomic JSON writes with file locking.
- [ ] 2.5. Add backup/export functionality.

### 3. Service Layer Refactoring
- [ ] 3.1. Create utils/ directory with csv_parser.py and validators.py.
- [ ] 3.2. Rename/refactor services to match PRD (pricing_service, storage_service, compute_service).
- [ ] 3.3. Implement CSV import with proper Spanish format handling.
- [ ] 3.4. Add ISIN mapping JSON file and update mapper service.
- [ ] 3.5. Implement position calculation and PnL computation.

### 4. Testing & Verification
- [ ] 4.1. Create new test files (deleted corrupted ones).
- [ ] 4.2. Write unit tests for CSV parsing and validation.
- [ ] 4.3. Write integration tests for API endpoints.
- [ ] 4.4. Write E2E tests for portfolio management flow.
- [ ] 4.5. Add test coverage reporting.
- [ ] 4.6. Target: 70% unit, 20% integration, 10% E2E coverage.

### 5. PRD Feature Alignment
- [ ] 5.1. Implement CSV import endpoint (Spanish format support).
- [ ] 5.2. Add manual order CRUD endpoints.
- [ ] 5.3. Implement orders history endpoint.
- [ ] 5.4. Add dashboard KPI calculations.
- [ ] 5.5. Implement allocation pie charts (instrument, geography, sector, asset type).
- [ ] 5.6. Add line chart data (invested vs current value over time).
- [ ] 5.7. Implement WebSocket broadcasts for real-time updates.

### 6. Code Quality & Simplification
- [ ] 6.1. Run Black formatter on all Python files (140 char line length).
- [ ] 6.2. Run Prettier on frontend files.
- [ ] 6.3. Add type hints to all Python functions.
- [ ] 6.4. Add docstrings (one-line minimum) to all functions/classes.
- [ ] 6.5. Remove unused imports and dead code.
- [ ] 6.6. Consolidate duplicate logic.

### 7. Documentation & Open-Source Readiness
- [ ] 7.1. Update README.md with current architecture.
- [ ] 7.2. Update CONTRIBUTING.md with development workflow.
- [ ] 7.3. Create issue and PR templates.
- [ ] 7.4. Document API endpoints in OpenAPI/Swagger.
- [ ] 7.5. Update USER_GUIDE.md to match current features.

### 8. Final Review
- [ ] 8.1. Manual walkthrough of all features.
- [ ] 8.2. Verify all tests pass.
- [ ] 8.3. Check for security issues (secrets in code, etc.).
- [ ] 8.4. Performance review (API response times < 300ms).
- [ ] 8.5. Final linting and formatting check.

---

## Current Project Structure Analysis

**Backend:**
- ✅ FastAPI app with proper CORS and routers
- ✅ Authentication with JWT tokens
- ✅ Portfolio CRUD operations
- ✅ Finnhub integration for price fetching
- ✅ ISIN mapper service (needs data file)
- ❌ Missing CSV import functionality
- ❌ Missing utils/ directory
- ❌ Using `holdings` instead of `orders` model
- ❌ Missing atomic JSON writes with locking
- ❌ Missing compute_service for PnL calculations

**Frontend:**
- ✅ Vue 3 with TypeScript
- ✅ Proper component structure
- ✅ Charts integration
- ⚠️ Needs verification against PRD features

**Data:**
- ❌ Only users.json exists (should have orders.json, instruments.json, prices.json, settings.json)
- ❌ Missing isin_ticker_mapping.json

**Tests:**
- ❌ All backend tests corrupted and deleted
- ⚠️ Frontend tests need verification

**Scripts:**
- ✅ Launcher scripts (.bat, .ps1)
- ✅ Utility scripts (clear_holdings.py, create_test_user.py)
- ⚠️ Need validation

Progress will be tracked by checking off each item as it is completed.
