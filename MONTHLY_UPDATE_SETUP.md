# Monthly Price Update - Setup Guide

This guide explains how to configure Windows Task Scheduler to automatically fetch updated fund prices and metadata on the 1st of each month.

## Prerequisites

- Backend API running on `localhost:8000`
- PowerShell script: `scripts/monthly_price_update.ps1`
- Administrator access to create scheduled tasks

## Option 1: Quick Setup (PowerShell)

Run this PowerShell command **as Administrator**:

```powershell
$action = New-ScheduledTaskAction `
    -Execute "PowerShell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"E:\JaviProyects\Proyects\Programming\Investit\scripts\monthly_price_update.ps1`""

$trigger = New-ScheduledTaskTrigger `
    -Monthly `
    -DaysOfMonth 1 `
    -At 3:00AM

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable

Register-ScheduledTask `
    -TaskName "InvestIt Monthly Price Update" `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Description "Automatically fetch fund prices and metadata on the 1st of each month" `
    -User $env:USERNAME
```

## Option 2: Manual Setup (GUI)

1. Open **Task Scheduler** (`taskschd.msc`)
2. Click **Create Basic Task...** in the right panel
3. Configure as follows:

### General Tab
- **Name**: `InvestIt Monthly Price Update`
- **Description**: `Automatically fetch fund prices and metadata on the 1st of each month`
- **Security options**: 
  - ☑ Run only when user is logged on
  - ☑ Run with highest privileges

### Triggers Tab
- Click **New...**
- **Begin the task**: On a schedule
- **Settings**: Monthly
  - **Months**: <all>
  - **Days**: 1
  - **Start**: 3:00 AM (or preferred time)
- ☑ **Enabled**

### Actions Tab
- Click **New...**
- **Action**: Start a program
- **Program/script**: `PowerShell.exe`
- **Add arguments**: 
  ```
  -NoProfile -ExecutionPolicy Bypass -File "E:\JaviProyects\Proyects\Programming\Investit\scripts\monthly_price_update.ps1"
  ```
- **Start in**: `E:\JaviProyects\Proyects\Programming\Investit`

### Conditions Tab
- ☐ Start the task only if the computer is on AC power
- ☑ Wake the computer to run this task

### Settings Tab
- ☑ Allow task to be run on demand
- ☑ Run task as soon as possible after a scheduled start is missed
- ☑ If the task fails, restart every 1 hour (Attempt to restart up to 3 times)

## Test the Task

Before waiting a month, test the task manually:

```powershell
# Run the script directly
E:\JaviProyects\Proyects\Programming\Investit\scripts\monthly_price_update.ps1

# OR trigger the scheduled task
Start-ScheduledTask -TaskName "InvestIt Monthly Price Update"
```

Check the log file for results:
```powershell
Get-Content E:\JaviProyects\Proyects\Programming\Investit\logs\monthly_price_update.log -Tail 50
```

## Important Notes

### Security
The script uses a default password (`test123`) for authentication. In production:

1. Set an environment variable with the actual password:
   ```powershell
   [System.Environment]::SetEnvironmentVariable("INVESTIT_DEFAULT_PASSWORD", "YourSecurePassword", "User")
   ```

2. OR use Windows Credential Manager to store credentials securely

### Backend Availability
- The task assumes the backend is running on `localhost:8000`
- If the backend is not running, the task will log an error and exit
- Consider creating another scheduled task to start the backend before this task runs

### Logs
- All output is logged to `logs/monthly_price_update.log`
- Logs are appended (not overwritten), so you can track history
- Clean up old logs periodically

## Automatic Backend Startup

If you also want to auto-start the backend, create another scheduled task:

```powershell
$action = New-ScheduledTaskAction `
    -Execute "PowerShell.exe" `
    -Argument "-NoProfile -File `"E:\JaviProyects\Proyects\Programming\Investit\start-backend.ps1`""

$trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME

Register-ScheduledTask `
    -TaskName "InvestIt Backend Auto-Start" `
    -Action $action `
    -Trigger $trigger `
    -Description "Automatically start InvestIt backend on login" `
    -User $env:USERNAME
```

This ensures the backend is always running for the monthly update task.

## Troubleshooting

### Task runs but nothing happens
- Check PowerShell execution policy: `Get-ExecutionPolicy`
- Should be `RemoteSigned` or `Bypass` 
- Set with: `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser`

### "Backend not running" error
- Ensure backend is started before the task runs
- OR set up the auto-start task above
- OR change the monthly update task time to after you typically start your computer

### Authentication failures
- Verify the password in the script matches your actual user password
- OR set the `INVESTIT_DEFAULT_PASSWORD` environment variable

### Task doesn't run at all
- Check Task Scheduler History: Right-click task → **Properties** → **History** tab
- Ensure triggers are enabled
- Verify task is not set to "Run only when user is logged on" if you want it to run while logged off
