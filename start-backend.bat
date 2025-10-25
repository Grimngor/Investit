@echo off
REM Investit Backend Launcher (Windows CMD)
REM Ensures virtual environment, installs dependencies (if first run), then starts FastAPI with reload.

SETLOCAL ENABLEDELAYEDEXPANSION
set ROOT=%~dp0
echo =============================================
echo   Investit Backend Launcher
echo =============================================
echo Project Root: %ROOT%
echo.

REM Ensure virtual environment exists
if not exist "%ROOT%venv\Scripts\python.exe" (
    echo Virtual environment not found. Creating venv...
    py -3 -m venv "%ROOT%venv"
    if errorlevel 1 (
        echo Failed to create virtual environment. Aborting.
        exit /b 1
    )
    echo Upgrading pip...
    call "%ROOT%venv\Scripts\python.exe" -m pip install --upgrade pip >NUL
    if exist "%ROOT%requirements.txt" (
        echo Installing backend requirements...
        call "%ROOT%venv\Scripts\python.exe" -m pip install -r "%ROOT%requirements.txt"
    )
)

REM Optional: update dependencies if user passes --sync flag
if /i "%1"=="--sync" (
    if exist "%ROOT%requirements.txt" (
        echo Syncing Python dependencies from requirements.txt...
        call "%ROOT%venv\Scripts\python.exe" -m pip install -r "%ROOT%requirements.txt"
    )
)

REM Kill existing uvicorn processes for this project only (best effort)
echo Checking for existing uvicorn/python processes...
for /f "tokens=2" %%p in ('tasklist /FI "IMAGENAME eq python.exe" /V ^| find /I "uvicorn"') do (
    echo Stopping uvicorn process PID %%p
    taskkill /PID %%p /F >NUL 2>&1
)
echo.

set PYTHONUNBUFFERED=1
set UVICORN_WORKERS=1
echo Starting FastAPI backend at http://localhost:8000 (Press Ctrl+C to stop)...
echo API Docs: http://localhost:8000/docs
echo.
cd /d "%ROOT%backend"
call "%ROOT%venv\Scripts\python.exe" -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
REM When uvicorn exits
echo Server stopped.
ENDLOCAL
