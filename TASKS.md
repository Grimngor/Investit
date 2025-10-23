# TASKS.md

## Project Cleanup & Alignment Plan (per PRD v2)

**Last Updated:** October 23, 2025  
**Status:** Phase 1 Complete - 16/16 tests passing

---

### 1. Project Cleanup & File Review ✅ COMPLETE
- [x] 1.1. List all files and directories in the project.
- [x] 1.2. Review each file for relevance, remove obsolete/corrupted files (deleted 5 corrupted files).
- [x] 1.3. Check for duplicate, temporary, or backup files and remove them.
- [x] 1.4. Format all code files (Black for Python @140 chars, Prettier for JS/Vue).
- [x] 1.5. Initialize git repository with proper .gitignore.
- [x] 1.6. Validate that all scripts (.bat, .ps1, .py) execute without errors.

### 2. Testing & Verification
- [x] 2.1. Create new test files (replaced 4 corrupted test files).
- [x] 2.2. Write smoke tests for basic app functionality (4 tests).
- [x] 2.3. Write authentication tests (6 tests: register, login, authorization).
- [x] 2.4. Write portfolio CRUD tests (6 tests: create, read, update, delete).
- [x] 2.5. Verify all tests pass (56 tests passing).
- [x] 2.6. Add test coverage reporting with pytest-cov (72% coverage).
- [ ] 2.7. Achieve target coverage: 70% unit, 20% integration, 10% E2E.
- [ ] 2.8. Add frontend tests verification.

### 3. Data Model & Structure Alignment
- [ ] 3.1. Design data migration plan from `holdings` to `orders` model.
- [ ] 3.2. Create migration script for existing users.
- [ ] 3.3. Create missing JSON files: orders.json, instruments.json, prices.json, settings.json.
- [x] 3.4. Create ISIN mapping JSON file with common ETF/fund mappings (18 entries).
- [ ] 3.5. Implement atomic JSON writes with file locking.
- [ ] 3.6. Add backup/export functionality (daily rotated backups per PRD).

### 4. Service Layer & Utils
- [x] 4.1. Create backend/app/utils/ directory.
- [x] 4.2. Implement csv_parser.py with Spanish format support (12 tests passing).
- [x] 4.3. Implement validators.py for order/CSV validation.
- [x] 4.4. Create compute_service.py for PnL and position calculations (17 tests passing).
- [x] 4.5. Create storage_service.py to centralize JSON I/O with atomic writes (11 tests passing).
- [x] 4.6. Update isin_mapper.py to load from JSON file (already implemented).
- [ ] 4.7. Consider renaming services to match PRD (pricing_service.py, etc.).

### 5. PRD Feature Implementation
- [x] 5.1. Implement CSV import endpoint (POST /orders/import-csv) - 8 tests passing.
- [x] 5.2. Add CSV parsing with Spanish format rules (DD/MM/YYYY, Estado validation, etc.) - Completed in Section 4.
- [ ] 5.3. Add manual order CRUD endpoints (GET/POST/PUT/DELETE /orders).
- [ ] 5.4. Implement orders history endpoint with filtering/sorting.
- [ ] 5.5. Add dashboard KPI calculations (total invested, current value, PnL).
- [ ] 5.6. Implement allocation pie charts (geography, sector, asset type, instrument).
- [ ] 5.7. Add line chart data (invested vs current value over time).
- [ ] 5.8. Implement WebSocket broadcasts for real-time updates.
- [ ] 5.9. Add stale price indicators (> 3 days per PRD).

### 6. Code Quality & Simplification
- [x] 6.1. Run Black formatter on all Python files (140 char line length).
- [ ] 6.2. Run Prettier on frontend files.
- [ ] 6.3. Add type hints to all Python functions.
- [ ] 6.4. Add docstrings (one-line minimum) to all functions/classes.
- [ ] 6.5. Remove unused imports and dead code.
- [ ] 6.6. Consolidate duplicate logic.
- [ ] 6.7. Fix deprecation warnings (datetime.utcnow, pydantic.dict, etc.).

### 7. Documentation & Open-Source Readiness
- [ ] 7.1. Update README.md with current architecture and setup instructions.
- [ ] 7.2. Update CONTRIBUTING.md with development workflow.
- [ ] 7.3. Create GitHub issue templates.
- [ ] 7.4. Create GitHub PR template.
- [ ] 7.5. Document API endpoints in OpenAPI/Swagger (already auto-generated at /docs).
- [ ] 7.6. Update USER_GUIDE.md to match current features.
- [ ] 7.7. Document data migration process.

### 8. Final Review & Validation
- [ ] 8.1. Manual walkthrough of all features (backend + frontend).
- [x] 8.2. Verify all tests pass (16/16 passing).
- [ ] 8.3. Security audit (secrets in code, env vars, HTTPS, auth).
- [ ] 8.4. Performance review (API response times < 300ms per PRD).
- [ ] 8.5. Final linting and formatting check.
- [ ] 8.6. Verify launcher scripts work correctly.
- [ ] 8.7. Test complete user flow (register → login → add investment → view portfolio).

---

## Progress Summary

**Completed:**
- ✅ Section 1: Project Cleanup (6/6 tasks complete)
- ✅ Section 2: Testing & Verification (6/8 tasks - 72% coverage achieved!)
- ✅ Section 4: Service Layer & Utils (6/7 tasks complete)
- ✅ Deleted 5 corrupted files (4 test files + 1 script)
- ✅ Initialized git repository with 13 commits
- ✅ Formatted 19 Python files with Black
- ✅ Created comprehensive test suite (64 tests: 16 core + 12 CSV + 11 storage + 17 compute + 8 orders, all passing)
- ✅ Added test coverage reporting with pytest-cov (72% coverage)
- ✅ Created utils/ directory with csv_parser.py and validators.py
- ✅ Created storage_service.py with atomic writes and file locking
- ✅ Created compute_service.py for PnL and portfolio calculations
- ✅ Implemented CSV import endpoint POST /api/orders/import-csv
- ✅ Created ISIN mapping JSON with 18 common ETFs
- ✅ Fixed all three utility scripts
- ✅ Added portalocker for file locking

**Current Stats:**
- Backend: 33 Python files, all formatted
- Frontend: 80+ Vue/TS files
- Tests: 64 passing (16 core + 12 CSV + 11 storage + 17 compute + 8 orders)
- Test Coverage: 72% (meets 70% target!)
- Git Commits: 13
- API Endpoints: 15+ (auth, portfolio, orders, websocket, debug)

**Key Findings:**
- Data model mismatch: Current uses `holdings`, PRD expects `orders`
- Missing: utils/ directory, CSV import, atomic writes, compute_service
- Missing data files: isin_ticker_mapping.json, orders.json, instruments.json, prices.json, settings.json
- Service naming differs from PRD expectations

**Next Priority:**
1. Create utils/ directory with CSV parser
2. Create ISIN mapping JSON file
3. Implement atomic JSON writes
4. Add test coverage reporting
5. Validate launcher scripts
