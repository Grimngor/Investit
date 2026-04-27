<#
Enhanced Backend Launcher (PowerShell)
 - Ensures .venv exists (creates if missing)
 - Installs requirements on first run
 - Kills only uvicorn processes related to this project (best effort)
 - Provides clear output & environment setup
#>

Write-Host "=== Investit Backend Launcher ===" -ForegroundColor Green
Write-Host "Project Root: $(Split-Path -Parent $MyInvocation.MyCommand.Path)" -ForegroundColor DarkGray
Write-Host ""

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"

# Ensure virtual environment
if (-not (Test-Path $venvPython)) {
	Write-Host "Virtual environment not found. Creating..." -ForegroundColor Yellow
	python -m venv (Join-Path $projectRoot '.venv')
	if (-not (Test-Path $venvPython)) { Write-Host "Failed to create venv." -ForegroundColor Red; exit 1 }
	Write-Host "Upgrading pip..." -ForegroundColor Cyan
	& $venvPython -m pip install --upgrade pip | Out-Null
	if (Test-Path (Join-Path $projectRoot 'requirements.txt')) {
		Write-Host "Installing requirements..." -ForegroundColor Cyan
		& $venvPython -m pip install -r (Join-Path $projectRoot 'requirements.txt')
	}
}

if ($args -contains '--sync') {
	if (Test-Path (Join-Path $projectRoot 'requirements.txt')) {
		Write-Host "--sync flag detected: reinstalling requirements" -ForegroundColor Yellow
		& $venvPython -m pip install -r (Join-Path $projectRoot 'requirements.txt')
	}
}

# Kill existing uvicorn processes (limit scope)
Write-Host "Scanning for existing uvicorn instances..." -ForegroundColor Cyan
$existing = Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -like 'python*' }
foreach ($p in $existing) {
	try {
		if ($p.MainWindowTitle -like '*uvicorn*' -or $p.Path -like "*$projectRoot*") {
			Write-Host "Stopping process $($p.Id) ($($p.ProcessName))" -ForegroundColor Yellow
			$p | Stop-Process -Force -ErrorAction SilentlyContinue
		}
	} catch { }
}
Write-Host ""

# Environment variables
$env:PYTHONUNBUFFERED = '1'
$env:UVICORN_WORKERS = '1'

Write-Host "Starting FastAPI: http://localhost:8000" -ForegroundColor Green
Write-Host "API Docs:     http://localhost:8000/docs" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop." -ForegroundColor DarkGray
Write-Host ""

Set-Location (Join-Path $projectRoot 'backend')
try {
	& $venvPython -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
} finally {
	Write-Host "Backend server stopped." -ForegroundColor Yellow
}
