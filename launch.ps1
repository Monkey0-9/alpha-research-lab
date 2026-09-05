Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "  QUANTALPHA INSTITUTIONAL WORKSTATION LAUNCHER" -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan

Write-Host "Starting FastAPI Backend on http://127.0.0.1:8000..." -ForegroundColor Green
Start-Process -FilePath "powershell.exe" -ArgumentList "-NoExit", "-Command", ".\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload"

Start-Sleep -Seconds 2

Write-Host "Starting Next.js Frontend UI on http://localhost:3000..." -ForegroundColor Green
Start-Process -FilePath "powershell.exe" -ArgumentList "-NoExit", "-Command", "npm run dev"

Write-Host "`nAll services active!" -ForegroundColor Yellow
Write-Host "Bloomberg UI Terminal:        http://localhost:3000" -ForegroundColor White
Write-Host "Quantitative Engine API:      http://127.0.0.1:8000" -ForegroundColor White
Write-Host "Interactive API Docs:         http://127.0.0.1:8000/docs" -ForegroundColor White
