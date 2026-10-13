@echo off
echo ========================================================
echo Starting CivicWatch Platform (Backend + Frontend)
echo ========================================================

:: 1. Launch FastAPI Backend
echo Starting FastAPI Backend on http://127.0.0.1:8000 ...
start "CivicWatch - Backend (FastAPI)" cmd /k "set PYTHONPATH=backend&& python -m uvicorn app.main:app --host 127.0.0.1 --port 8000"

:: 2. Launch Vite Frontend
echo Starting Vite Frontend on http://localhost:3000 ...
start "CivicWatch - Frontend (React/Vite)" cmd /k "cd frontend && npm run dev"

echo.
echo ========================================================
echo CivicWatch is starting!
echo Frontend: http://localhost:3000
echo Backend:  http://127.0.0.1:8000
echo API Docs: http://127.0.0.1:8000/docs
echo ========================================================
