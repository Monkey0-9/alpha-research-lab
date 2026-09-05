@echo off
echo ===================================================
echo   QUANTALPHA INSTITUTIONAL WORKSTATION LAUNCHER
echo ===================================================
echo Starting FastAPI Backend on http://127.0.0.1:8000 ...
start "QuantAlpha Backend" cmd /k ".\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload"

timeout /t 2 /nobreak >nul

echo Starting Next.js Frontend UI on http://localhost:3000 ...
start "QuantAlpha Frontend" cmd /k "npm run dev"

echo.
echo ===================================================
echo Services initiated successfully!
echo - Bloomberg UI Terminal: http://localhost:3000
echo - Quantitative Engine API: http://127.0.0.1:8000
echo - Swagger API Documentation: http://127.0.0.1:8000/docs
echo ===================================================
