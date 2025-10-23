# Investit Full-Stack Launcher
# Launches backend and frontend in separate terminal windows

Write-Host "Starting Investit Full-Stack Application..." -ForegroundColor Green
Write-Host ""

# Get the script directory (project root)
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

# Launch Backend in new PowerShell window
Write-Host "Launching Backend Server..." -ForegroundColor Cyan
$backendPath = Join-Path $projectRoot "backend"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$backendPath'; python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

# Wait a moment for backend to initialize
Start-Sleep -Seconds 2

# Launch Frontend in new PowerShell window
Write-Host "Launching Frontend Server..." -ForegroundColor Cyan
$frontendPath = Join-Path $projectRoot "frontend"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$frontendPath'; npm run dev"

# Wait for frontend to start, then open browser
Start-Sleep -Seconds 3
Write-Host "Opening browser..." -ForegroundColor Cyan
Start-Process "http://localhost:5173"

Write-Host ""
Write-Host "Full-stack application launched!" -ForegroundColor Green
Write-Host ""
Write-Host "Backend:  http://localhost:8000" -ForegroundColor Yellow
Write-Host "API Docs: http://localhost:8000/docs" -ForegroundColor Yellow
Write-Host "Frontend: http://localhost:5173" -ForegroundColor Yellow
Write-Host ""
Write-Host "Tip: Close the terminal windows to stop the servers" -ForegroundColor Gray
Write-Host ""
