@echo off
REM Start the Investit backend server

echo Starting FastAPI backend...
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
