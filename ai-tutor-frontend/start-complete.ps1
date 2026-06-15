Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  AI Tutor - Starting Complete System" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$root = "C:\SMIT Teaching Assisstant"

# Start Python FastAPI backend
Write-Host "[1/3] Starting Python backend (port 8000)..." -ForegroundColor Yellow
$backendJob = Start-Job -ScriptBlock {
    param($dir)
    Set-Location $dir
    python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
} -ArgumentList $root

Start-Sleep -Seconds 3
Write-Host "[2/3] Backend starting..." -ForegroundColor Green

# Start Next.js frontend
Write-Host "[3/3] Starting Next.js frontend (port 3000)..." -ForegroundColor Yellow
$frontendDir = Join-Path $root "ai-tutor-frontend"
$frontendJob = Start-Job -ScriptBlock {
    param($dir)
    Set-Location $dir
    npm run dev
} -ArgumentList $frontendDir

Start-Sleep -Seconds 4

# Open browser
Write-Host "Opening browser..." -ForegroundColor Yellow
Start-Process "http://localhost:3000"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  System Running!" -ForegroundColor Green
Write-Host "  Frontend: http://localhost:3000" -ForegroundColor Green
Write-Host "  Backend:  http://localhost:8000" -ForegroundColor Green
Write-Host "  API Docs: http://localhost:8000/docs" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop both servers."

try {
    while ($true) {
        Start-Sleep -Seconds 1
    }
} finally {
    Write-Host "Stopping servers..." -ForegroundColor Yellow
    Stop-Job $backendJob -ErrorAction SilentlyContinue
    Stop-Job $frontendJob -ErrorAction SilentlyContinue
    Remove-Job $backendJob -ErrorAction SilentlyContinue
    Remove-Job $frontendJob -ErrorAction SilentlyContinue
    Write-Host "Servers stopped." -ForegroundColor Green
}
