# InvestIt Launcher Scripts Guide

This guide explains all the launcher scripts available for the InvestIt project.

## Quick Start

### Launch Full Application (Recommended)
```powershell
.\start-fullstack.ps1
```
This launches both backend and frontend servers in separate terminal windows and **automatically kills any existing Python processes** to avoid conflicts.

## Available Scripts

### PowerShell Scripts (.ps1)

#### `start-fullstack.ps1` - Full Stack Launcher ⭐ RECOMMENDED
Launches both backend and frontend servers in separate PowerShell windows.

**Usage:**
```powershell
.\start-fullstack.ps1
```

**What it does:**
1. **Kills any existing Python processes** (prevents conflicts from stale servers)
2. Opens new terminal for backend server
3. Starts FastAPI with uvicorn on `http://localhost:8000`
4. Opens new terminal for frontend server
5. Starts Vite dev server on `http://localhost:5173`
6. Opens browser automatically

**Access points:**
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Frontend App: http://localhost:5173

---

#### `start-backend.ps1` - Backend Only (PowerShell)
Starts only the FastAPI backend server.

**Usage:**
```powershell
.\start-backend.ps1
```

**What it does:**
1. **Kills any existing Python processes** (prevents port conflicts)
2. Activates virtual environment
3. Starts FastAPI backend on port 8000

**Benefits over .bat version:**
- Better error messages
- Automatic cleanup of stale processes
- Color-coded output

---

#### `stop-all.ps1` - Stop All Servers
Stops all running backend and frontend servers.

**Usage:**
```powershell
.\stop-all.ps1
```

**What it does:**
1. Kills all Python processes (backend)
2. Kills all Node.js processes (frontend)
3. Shows count of stopped processes

**Use this when:**
- You want to clean up before restarting
- Servers are not responding
- You have multiple instances running

---

### Batch Scripts (.bat)

#### `start-backend.bat` - Backend Only (Batch)
Starts only the FastAPI backend server.

**Usage:**
```cmd
start-backend.bat
```

**What it does:**
1. **Checks for and kills existing Python processes**
2. Navigates to `backend/` directory
3. Runs: `python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`

**Note:** Consider using `start-backend.ps1` instead for better output and error handling.
- Auto-reloads on code changes
- Accessible at http://localhost:8000

**When to use:**
- Working only on backend features
- Frontend already running
- Testing API endpoints directly

---

#### `start-frontend.bat` - Frontend Only
Starts only the Vue.js frontend server.

**Usage:**
```cmd
start-frontend.bat
```

**Details:**
- Navigates to `frontend/` directory
- Runs: `npm run dev`
- Hot module replacement (HMR) enabled
- Accessible at http://localhost:5173

**When to use:**
- Working only on frontend features
- Backend already running
- Testing UI components

---

#### `stop-all.bat` - Stop All Servers
Stops all running backend and frontend processes.

**Usage:**
```cmd
stop-all.bat
```

**What it does:**
1. Kills all `node.exe` processes (frontend/Vite)
2. Kills all `python.exe` processes (backend/uvicorn)
3. Displays success messages

**⚠️ Warning:** This will stop ALL Node.js and Python processes, not just InvestIt servers. Use with caution if you have other Node/Python apps running.

---

## Typical Workflows

### Full Stack Development
```powershell
# Start both servers
.\start-fullstack.ps1

# Work on features...

# Stop when done
.\stop-all.bat
```

### Backend-Only Development
```cmd
# Start backend
start-backend.bat

# Test API at http://localhost:8000/docs

# Stop when done (Ctrl+C or stop-all.bat)
```

### Frontend-Only Development
```cmd
# Start frontend
start-frontend.bat

# Work on UI at http://localhost:5173

# Stop when done (Ctrl+C or stop-all.bat)
```

### Separate Backend and Frontend
```cmd
# Terminal 1: Start backend
start-backend.bat

# Terminal 2: Start frontend
start-frontend.bat

# Stop both
.\stop-all.bat
```

---

## Troubleshooting

### Port Already in Use

**Problem:** Error message "Port 8000/5173 already in use"

**Solution:**
```cmd
# Stop all servers first
.\stop-all.bat

# Then restart
.\start-fullstack.ps1
```

### Backend Won't Start

**Check:**
1. Python virtual environment is activated
2. Dependencies are installed: `pip install -r requirements.txt`
3. `.env` file exists in project root
4. Running from `backend/` directory

### Frontend Won't Start

**Check:**
1. Node modules are installed: `cd frontend && npm install`
2. Node.js version is compatible (v18+)
3. No conflicting processes on port 5173

### Scripts Won't Run (PowerShell)

**Problem:** "Execution policy" error

**Solution:**
```powershell
# Allow script execution (run as Administrator)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## Environment Requirements

### Backend Requirements
- Python 3.12+
- Virtual environment activated
- `.env` file with required variables
- Dependencies installed from `requirements.txt`

### Frontend Requirements
- Node.js 18+
- npm or yarn package manager
- Dependencies installed from `package.json`

---

## Script Details

### What Happens When You Start the Backend?

1. Navigates to `backend/` directory
2. Activates Python environment (if needed)
3. Runs uvicorn with these flags:
   - `--reload`: Auto-reload on code changes
   - `--host 0.0.0.0`: Accept connections from any IP
   - `--port 8000`: Listen on port 8000

### What Happens When You Start the Frontend?

1. Navigates to `frontend/` directory
2. Runs Vite dev server via `npm run dev`
3. Vite provides:
   - Hot Module Replacement (HMR)
   - Lightning-fast builds
   - Auto-open browser (optional)

### What Happens with start-fullstack.ps1?

1. Displays startup message
2. Opens new PowerShell window for backend
   - Changes to backend directory
   - Starts uvicorn server
   - Window stays open
3. Waits 2 seconds (backend initialization)
4. Opens new PowerShell window for frontend
   - Changes to frontend directory
   - Starts Vite dev server
   - Window stays open
5. Both servers run independently

---

## Troubleshooting

### Common Issues

#### "Port 8000 is already in use"
**Cause:** Another Python/backend process is still running from a previous session.

**Solution:**
```powershell
# Option 1: Use stop-all script
.\stop-all.ps1

# Option 2: Manual cleanup
Get-Process | Where-Object { $_.ProcessName -like "*python*" } | Stop-Process -Force

# Then restart
.\start-fullstack.ps1
```

**Prevention:** Always use `start-fullstack.ps1` or `start-backend.ps1` - they automatically kill old processes!

---

#### "Frontend shows 404 or 'Not Found' errors"
**Cause:** Backend was started with old code before routes were registered.

**Solution:**
```powershell
# 1. Stop all servers
.\stop-all.ps1

# 2. Verify no Python processes running
Get-Process | Where-Object { $_.ProcessName -like "*python*" } | Measure-Object

# 3. Start fresh
.\start-fullstack.ps1

# 4. Hard refresh browser (Ctrl+F5)
```

---

#### Multiple Backend Instances Running
**Symptom:** Routes not working, old data showing, inconsistent behavior.

**Check:**
```powershell
# Count Python processes
Get-Process | Where-Object { $_.ProcessName -like "*python*" } | Measure-Object
```

**Fix:**
```powershell
.\stop-all.ps1
.\start-fullstack.ps1
```

---

#### Verification Script to Check Routes
After starting backend, verify routes are registered:

```powershell
# Run this in a NEW terminal (don't close backend terminal!)
.\check_routes.ps1
```

Look for these critical routes:
- `/api/prices/fetch`
- `/api/prices/status`
- `/api/orders/all`
- `/api/dashboard/kpis`

---

## Advanced Usage

### Custom Ports

Edit scripts to use different ports:

**Backend:**
```bat
REM In start-backend.bat, change:
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

**Frontend:**
```json
// In frontend/package.json, modify:
"scripts": {
  "dev": "vite --port 3000"
}
```

### Production Mode

For production builds:

**Backend:**
```bash
# Remove --reload flag
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd frontend
npm run build
npm run preview
```

---

## Tips & Best Practices

1. **Always use `start-fullstack.ps1`** for normal development
2. **Use individual scripts** only when working on specific parts
3. **Use `stop-all.bat`** to clean up all processes
4. **Check the terminal output** for error messages
5. **Keep both terminals open** to see logs and errors
6. **Use API docs** at http://localhost:8000/docs for backend testing

---

## Quick Reference

| Script | Purpose | Command |
|--------|---------|---------|
| `start-fullstack.ps1` | Launch both servers | `.\start-fullstack.ps1` |
| `start-backend.bat` | Backend only | `start-backend.bat` |
| `start-frontend.bat` | Frontend only | `start-frontend.bat` |
| `stop-all.bat` | Stop all servers | `.\stop-all.bat` |

---

**Last Updated**: October 23, 2025
**Project Version**: 1.0.0
