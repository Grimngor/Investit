# Investit Development & Testing Guide

## Running the Backend Tests

Tests import the `app` package from the `backend` directory. This is handled automatically:
- `backend/tests/conftest.py` injects the backend path into `sys.path`.
- Helper scripts under `scripts/` add the path explicitly for pre-commit.

### Quick Options

1. Fast subset (fail-fast):
   ```pwsh
   python scripts/pytest_fast.py
   ```
2. Full suite:
   ```pwsh
   python scripts/pytest_full.py
   ```
3. Direct from backend directory:
   ```pwsh
   cd backend
   ..\venv\Scripts\pytest.exe -q
   ```

### Running a Single Test File
```pwsh
cd backend
..\venv\Scripts\pytest.exe tests/test_orders.py -q
```

### Common Issues
- ModuleNotFoundError: app
  - Ensure you are either in `backend/` or using one of the helper scripts.
- Environment not activated
  - Activate the venv: `./venv/Scripts/Activate.ps1` before running tests.

### Coverage
To generate coverage HTML:
```pwsh
cd backend
..\venv\Scripts\pytest.exe --cov=app --cov-report=html -q
```
Output appears in `backend/htmlcov/`.

### Lint & Format
Ruff handles both:
```pwsh
python scripts/format_python.py
```

## Frontend Tests
(Playwright/Vitest specifics can be added here later.)

## Recommended Workflow
1. Edit code
2. Run fast tests: `python scripts/pytest_fast.py`
3. Format: `python scripts/format_python.py`
4. Commit (pre-commit runs fast tests again)
5. Push (pre-push runs full tests)

## Troubleshooting
If tests behave differently in CI vs local:
- Confirm `backend/tests/conftest.py` exists and includes path injection.
- Verify Python version matches project target (3.12).

---
Minimal, consistent, typed. Update this guide as tooling evolves.
