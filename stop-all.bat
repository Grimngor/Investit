@echo off
REM Stop all Investit servers (backend and frontend)

echo Stopping all Investit servers...

REM Kill all node processes (frontend)
echo Stopping frontend (Node.js/Vite)...
taskkill /F /IM node.exe 2>nul
if %errorlevel% equ 0 (
    echo Frontend stopped successfully
) else (
    echo No frontend process found
)

REM Kill all Python/uvicorn processes (backend)
echo Stopping backend (Python/uvicorn)...
taskkill /F /IM python.exe 2>nul
if %errorlevel% equ 0 (
    echo Backend stopped successfully
) else (
    echo No backend process found
)

echo.
echo All servers stopped!
pause
