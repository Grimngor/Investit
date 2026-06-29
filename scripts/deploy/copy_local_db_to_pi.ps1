param(
    [string]$Remote = "javi@pi5.tailfc2d4f.ts.net",
    [string]$RemoteRoot = "~/services/investit",
    [string]$LocalDatabase = "data/investit.sqlite3",
    [string]$SshConfigPath = "NUL",
    [string]$IdentityFile = "$HOME\.ssh\id_ed25519_pi5",
    [string]$StrictHostKeyChecking = "accept-new",
    [switch]$SkipRemoteBackup
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "==> $Message"
}

function Invoke-Remote {
    param([string]$Command)
    & ssh @SshArgs $Remote $Command
    if ($LASTEXITCODE -ne 0) {
        throw "Remote command failed with exit code $LASTEXITCODE"
    }
}

function Require-Command {
    param([string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Missing required command: $Name"
    }
}

$localDbPath = Resolve-Path -LiteralPath $LocalDatabase
$SshArgs = @()
if ($SshConfigPath) {
    $SshArgs += @("-F", $SshConfigPath)
}
if ($IdentityFile -and (Test-Path -LiteralPath $IdentityFile)) {
    $SshArgs += @("-i", $IdentityFile)
}
if ($StrictHostKeyChecking) {
    $SshArgs += @("-o", "StrictHostKeyChecking=$StrictHostKeyChecking")
}

Write-Step "Preflight"
Require-Command ssh
Require-Command scp
Write-Host "Local database: $localDbPath"
Write-Host "Remote target: ${Remote}:$RemoteRoot"
Write-Host "SSH config: $SshConfigPath"
if ($IdentityFile -and (Test-Path -LiteralPath $IdentityFile)) {
    Write-Host "Identity file: $IdentityFile"
}

Write-Step "Remote repository check"
Invoke-Remote "cd $RemoteRoot && test -f compose.yaml && mkdir -p data/backups"

if (-not $SkipRemoteBackup) {
    Write-Step "Stop stack and back up remote database"
    Invoke-Remote @"
cd $RemoteRoot &&
docker compose down &&
mkdir -p data/backups &&
if [ -f data/investit.sqlite3 ]; then
  cp data/investit.sqlite3 data/backups/investit_before_local_restore_`$(date -u +%Y%m%d_%H%M%S).sqlite3;
  echo 'Remote backup created.';
else
  echo 'No existing remote database to back up.';
fi
"@
} else {
    Write-Step "Stop stack"
    Invoke-Remote "cd $RemoteRoot && docker compose down"
    Write-Warning "Skipped remote backup because -SkipRemoteBackup was provided."
}

Write-Step "Copy local SQLite database to Pi"
$destination = "${Remote}:$RemoteRoot/data/investit.sqlite3"
& scp @SshArgs $localDbPath $destination
if ($LASTEXITCODE -ne 0) {
    throw "scp failed with exit code $LASTEXITCODE"
}

Write-Step "Remove remote SQLite WAL/SHM files and restart"
Invoke-Remote "cd $RemoteRoot && rm -f data/investit.sqlite3-wal data/investit.sqlite3-shm && docker compose up -d"

Write-Step "Health check"
Invoke-Remote "cd $RemoteRoot && web_port=`$(grep -E '^INVESTIT_WEB_PORT=' .env | tail -n 1 | cut -d '=' -f 2-); web_port=`${web_port:-8080}; curl -fsS http://127.0.0.1:`${web_port}/health"

Write-Step "Done"
Write-Host "Local database restored to the Pi."
