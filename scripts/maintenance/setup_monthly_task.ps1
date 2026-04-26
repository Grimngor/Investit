<#
.SYNOPSIS
    Auto-setup monthly price update scheduled task
.DESCRIPTION
    Registers a Windows Task Scheduler task to run monthly price updates automatically.
    This script should be run once after installing InvestIt.
#>

param(
    [switch]$Uninstall
)

$ErrorActionPreference = "Stop"

$TASK_NAME = "InvestIt Monthly Price Update"

# Determine script directory and monthly update script path
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$SCRIPT_PATH = Join-Path $scriptDir "monthly_price_update.ps1"

# Validate that the monthly update script exists
if (-not (Test-Path $SCRIPT_PATH)) {
    Write-Error "Monthly update script not found at: $SCRIPT_PATH"
    exit 1
}

if ($Uninstall) {
    Write-Host "Removing scheduled task: $TASK_NAME"
    Unregister-ScheduledTask -TaskName $TASK_NAME -Confirm:$false -ErrorAction SilentlyContinue
    Write-Host "Task removed successfully" -ForegroundColor Green
    exit 0
}

Write-Host "Setting up monthly price update scheduled task..." -ForegroundColor Cyan
Write-Host ""

# Check if task already exists (suppress error if not found)
$ErrorActionPreference = "SilentlyContinue"
$existingTask = schtasks /Query /TN $TASK_NAME 2>&1
$taskExists = $LASTEXITCODE -eq 0
$ErrorActionPreference = "Stop"

if ($taskExists) {
    Write-Host "Task already exists. Removing old version..." -ForegroundColor Yellow
    schtasks /Delete /TN $TASK_NAME /F 2>&1 | Out-Null
}

# Create task using schtasks for maximum compatibility
$taskCommand = "PowerShell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$SCRIPT_PATH`""

Write-Host "Creating scheduled task..." -ForegroundColor Gray

# Use schtasks to create monthly task (runs on 1st of every month at 3:00 AM)
$result = schtasks /Create `
    /TN $TASK_NAME `
    /TR $taskCommand `
    /SC MONTHLY `
    /D 1 `
    /ST 03:00 `
    /RU $env:USERNAME `
    /F

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "SUCCESS: Scheduled task created successfully!" -ForegroundColor Green
    Write-Host "  Task Name: $TASK_NAME" -ForegroundColor Gray
    Write-Host "  Schedule: Monthly on the 1st at 3:00 AM" -ForegroundColor Gray
    Write-Host "  Script: $SCRIPT_PATH" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Test the task now with:" -ForegroundColor Cyan
    Write-Host "  schtasks /Run /TN `"$TASK_NAME`"" -ForegroundColor White
    Write-Host ""
    exit 0
}
else {
    Write-Host ""
    Write-Host "ERROR: Failed to create scheduled task" -ForegroundColor Red
    Write-Host "Exit code: $LASTEXITCODE" -ForegroundColor Red
    Write-Host ""
    exit 1
}
