@echo off
echo Starting Interview Agent...
echo.

echo [Backend] Starting on http://localhost:8003
start "Backend" cmd /c "uvicorn web.api:app --host 0.0.0.0 --port 8003 --reload"

timeout /t 2 /nobreak >nul

echo [Frontend] Starting on http://localhost:3000
start "Frontend" cmd /c "python frontend/server.py"

echo.
echo Backend:  http://localhost:8003
echo Frontend: http://localhost:3000
echo.
echo Close the terminal windows to stop services.
pause
