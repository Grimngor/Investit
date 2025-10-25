@echo off
REM Investit Frontend Launcher (Vue + Vite)

set ROOT=%~dp0
echo =============================================
echo   Investit Frontend Launcher
echo =============================================
echo Project Root: %ROOT%
echo.
cd /d "%ROOT%frontend"

IF NOT EXIST node_modules (
	echo node_modules missing. Running npm install...
	call npm install
	if errorlevel 1 (
		echo npm install failed. Exiting.
		exit /b 1
	)
)

echo Starting Vite dev server at http://localhost:5173 ...
call npm run dev
echo Frontend server stopped.
