# Verification script for InvestIt backend
# Run this after starting the backend to verify all routes are registered

Write-Host "`nChecking if backend is running..." -ForegroundColor Cyan

try {
    $health = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get
    Write-Host "SUCCESS: Backend is running - $($health.status)" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Backend is NOT running. Please start it first." -ForegroundColor Red
    exit 1
}

Write-Host "`nVerifying API routes..." -ForegroundColor Cyan

$openapi = Invoke-RestMethod -Uri "http://localhost:8000/openapi.json" -Method Get
$paths = $openapi.paths.PSObject.Properties.Name

$requiredRoutes = @(
    "/api/auth/login",
    "/api/orders/",
    "/api/orders/all",
    "/api/prices/fetch",
    "/api/prices/status",
    "/api/dashboard/kpis",
    "/api/dashboard/time-series",
    "/api/dashboard/allocations"
)

$missing = @()
foreach ($route in $requiredRoutes) {
    if ($paths -contains $route) {
        Write-Host "OK: $route" -ForegroundColor Green
    } else {
        Write-Host "MISSING: $route" -ForegroundColor Red
        $missing += $route
    }
}

if ($missing.Count -gt 0) {
    Write-Host "`nWARNING: $($missing.Count) route(s) are missing!" -ForegroundColor Yellow
    Write-Host "Missing routes:" -ForegroundColor Yellow
    $missing | ForEach-Object { Write-Host "  - $_" -ForegroundColor Yellow }
    Write-Host "`nPlease restart the backend server to register all routes." -ForegroundColor Yellow
} else {
    Write-Host "`nSUCCESS: All required routes are registered!" -ForegroundColor Green
    Write-Host "Backend is ready to use." -ForegroundColor Green
}
