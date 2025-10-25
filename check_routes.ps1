# Simple route checker that lists all registered API endpoints
$openapi = Invoke-RestMethod -Uri "http://localhost:8000/openapi.json" -Method Get
$paths = $openapi.paths.PSObject.Properties.Name | Sort-Object
Write-Host "Registered API routes:" -ForegroundColor Cyan
$paths | ForEach-Object { Write-Host "  $_" }
