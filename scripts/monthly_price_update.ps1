<#
.SYNOPSIS
    Monthly price update task for InvestIt
.DESCRIPTION
    Fetches latest prices and fund metadata for all users in the InvestIt system.
    Designed to be run as a Windows Task Scheduler task on the 1st of each month.
.NOTES
    Requires:
    - Backend API running on localhost:8000
    - Valid test user credentials (update if changed)
#>

$ErrorActionPreference = "Stop"

# Configuration
$API_URL = "http://localhost:8000"
$LOG_FILE = "E:\JaviProyects\Proyects\Programming\Investit\logs\monthly_price_update.log"

# Logging function
function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "$timestamp - $Message"
    Write-Host $logMessage
    Add-Content -Path $LOG_FILE -Value $logMessage
}

try {
    Write-Log "=== Monthly Price Update Task Started ==="
    
    # Check if backend is running
    Write-Log "Checking backend health..."
    try {
        $healthResponse = Invoke-RestMethod -Uri "$API_URL/health" -Method Get -TimeoutSec 5
        if ($healthResponse.status -ne "healthy") {
            throw "Backend health check failed: $($healthResponse.status)"
        }
        Write-Log "Backend is healthy"
    }
    catch {
        Write-Log "ERROR: Backend is not running or unreachable: $_"
        Write-Log "Please ensure the backend server is started before running this task"
        exit 1
    }
    
    # Load users and trigger price fetch for each
    $usersFile = "E:\JaviProyects\Proyects\Programming\Investit\data\users.json"
    
    if (Test-Path $usersFile) {
        $users = Get-Content $usersFile | ConvertFrom-Json
        $userCount = ($users.PSObject.Properties | Measure-Object).Count
        Write-Log "Found $userCount users in system"
        
        $successCount = 0
        $failureCount = 0
        
        foreach ($userProp in $users.PSObject.Properties) {
            $username = $userProp.Name
            $userData = $userProp.Value
            
            # Skip test users and users without orders
            if ($username -match "^test_" -or !$userData.orders) {
                Write-Log "Skipping user: $username (test account or no orders)"
                continue
            }
            
            Write-Log "Processing user: $username"
            
            # For security, in production you should use proper auth tokens
            # This example assumes a default password or environment variable
            $password = $env:INVESTIT_DEFAULT_PASSWORD
            if (!$password) {
                $password = "test123"  # CHANGE THIS in production!
            }
            
            try {
                # Login
                $loginBody = @{
                    username = $username
                    password = $password
                } | ConvertTo-Json
                
                $loginResponse = Invoke-RestMethod `
                    -Uri "$API_URL/api/auth/login" `
                    -Method Post `
                    -Body "username=$username&password=$password" `
                    -ContentType "application/x-www-form-urlencoded" `
                    -TimeoutSec 30
                
                $token = $loginResponse.access_token
                
                # Trigger price fetch
                $headers = @{
                    "Authorization" = "Bearer $token"
                }
                
                $priceResponse = Invoke-RestMethod `
                    -Uri "$API_URL/api/prices/fetch" `
                    -Method Post `
                    -Headers $headers `
                    -TimeoutSec 60
                
                Write-Log "Success for $username`: $($priceResponse.message)"
                $successCount++
            }
            catch {
                Write-Log "ERROR for $username`: $_"
                $failureCount++
            }
        }
        
        Write-Log "=== Price Update Complete ==="
        Write-Log "Successful: $successCount, Failed: $failureCount"
    }
    else {
        Write-Log "ERROR: users.json not found at $usersFile"
        exit 1
    }
}
catch {
    Write-Log "FATAL ERROR: $_"
    Write-Log $_.ScriptStackTrace
    exit 1
}
