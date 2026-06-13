@echo off
echo ========================================
echo BOM Normalizer - Starting All Services
echo ========================================
echo.

echo [1/3] Starting Ollama (AI)...
start "Ollama AI" ollama serve
timeout /t 3 >nul

echo [2/3] Starting Backend Server (Port 7860)...
cd /d "%~dp0"
start "Backend Server" cmd /k "python -m uvicorn bom_normalizer.server:app --host 0.0.0.0 --port 7860"
timeout /t 3 >nul

echo [3/3] Starting Frontend UI (Port 3001)...
cd frontend
start "Frontend UI" cmd /k "npm run dev"
cd ..

echo.
echo ========================================
echo All Services Started!
echo ========================================
echo.
echo Wait 10 seconds, then open:
echo   http://localhost:3001
echo.
echo Three windows will open:
echo   1. Ollama (AI brain)
echo   2. Backend (API server)
echo   3. Frontend (Web interface)
echo.
echo To stop: Close all three windows
echo.
pause
