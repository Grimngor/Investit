# Stop All Investit Servers
# Kills all Python and Node processes

Write-Host "Stopping Investit Servers..." -ForegroundColor Yellow
Write-Host ""

# Stop Python processes (backend)
Write-Host "Checking for Python processes (backend)..." -ForegroundColor Cyan
$pythonProcesses = Get-Process | Where-Object { $_.ProcessName -like "*python*" }
if ($pythonProcesses) {
	Write-Host "Stopping $($pythonProcesses.Count) Python process(es)..." -ForegroundColor Yellow
	$pythonProcesses | Stop-Process -Force -ErrorAction SilentlyContinue
	Write-Host "Backend servers stopped." -ForegroundColor Green
} else {
	Write-Host "No Python processes found." -ForegroundColor Gray
}

# Stop Node processes (frontend)
Write-Host ""
Write-Host "Checking for Node processes (frontend)..." -ForegroundColor Cyan
$nodeProcesses = Get-Process | Where-Object { $_.ProcessName -like "*node*" }
if ($nodeProcesses) {
	Write-Host "Stopping $($nodeProcesses.Count) Node process(es)..." -ForegroundColor Yellow
	$nodeProcesses | Stop-Process -Force -ErrorAction SilentlyContinue
	Write-Host "Frontend servers stopped." -ForegroundColor Green
} else {
	Write-Host "No Node processes found." -ForegroundColor Gray
}

Write-Host ""
Write-Host "All servers stopped." -ForegroundColor Green
