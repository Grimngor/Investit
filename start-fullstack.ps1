# Investit Full-Stack Launcher
# Launches backend and frontend in separate terminal windows

Write-Host "Starting Investit Full-Stack Application..." -ForegroundColor Green
Write-Host ""

# Kill any existing Python processes to avoid conflicts
Write-Host "Checking for existing Python processes..." -ForegroundColor Cyan
$pythonProcesses = Get-Process | Where-Object { $_.ProcessName -like "*python*" }
if ($pythonProcesses) {
	Write-Host "Found $($pythonProcesses.Count) Python process(es). Stopping them..." -ForegroundColor Yellow
	$pythonProcesses | Stop-Process -Force -ErrorAction SilentlyContinue
	Start-Sleep -Seconds 1
	Write-Host "Stopped existing Python processes." -ForegroundColor Green
} else {
	Write-Host "No existing Python processes found." -ForegroundColor Green
}
Write-Host ""

# Get the script directory (project root)
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

<# Enhanced full-stack launcher:
 - Ensures backend venv and installs requirements if missing
 - Ensures frontend node_modules installed
 - Uses venv python explicitly
 - Launches in separate windows
#>

# Ensure backend venv
$venvPython = Join-Path $projectRoot "venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
	Write-Host "Virtual environment missing. Creating..." -ForegroundColor Yellow
	python -m venv (Join-Path $projectRoot 'venv')
	& $venvPython -m pip install --upgrade pip | Out-Null
	if (Test-Path (Join-Path $projectRoot 'requirements.txt')) {
		Write-Host "Installing backend requirements..." -ForegroundColor Cyan
		& $venvPython -m pip install -r (Join-Path $projectRoot 'requirements.txt')
	}
}

# Ensure frontend dependencies
$frontendPath = Join-Path $projectRoot "frontend"
if (-not (Test-Path (Join-Path $frontendPath 'node_modules'))) {
	Write-Host "Installing frontend dependencies (npm install)..." -ForegroundColor Cyan
	Start-Process -Wait -WorkingDirectory $frontendPath npm -ArgumentList 'install'
}

# Launch Backend in new PowerShell window using venv python
Write-Host "Launching Backend Server..." -ForegroundColor Cyan
$backendPath = Join-Path $projectRoot "backend"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$backendPath'; `$env:PYTHONUNBUFFERED='1'; & '$venvPython' -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8100"

# Wait a moment for backend to initialize
Start-Sleep -Seconds 2

Write-Host "Launching Frontend Server..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$frontendPath'; npm run dev"

# Wait for frontend to start, then open browser
Start-Sleep -Seconds 4
Write-Host "Opening browser..." -ForegroundColor Cyan
# Frontend auto-selects port 5174 when 5173 is busy
Start-Process "http://localhost:5174"

Write-Host ""
Write-Host "Full-stack application launched!" -ForegroundColor Green
Write-Host ""
Write-Host "Backend:  http://localhost:8100" -ForegroundColor Yellow
Write-Host "API Docs: http://localhost:8100/docs" -ForegroundColor Yellow
Write-Host "Frontend: http://localhost:5174" -ForegroundColor Yellow
Write-Host ""
Write-Host "Tip: Close the terminal windows to stop the servers" -ForegroundColor Gray
Write-Host ""
