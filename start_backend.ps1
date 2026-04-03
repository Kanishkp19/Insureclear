# ============================================================
# InsureClear Integrated - Backend Startup Script
# ============================================================
# Run this from the InsureClear_Integrated folder:
#   .\start_backend.ps1

Set-Location "$PSScriptRoot\backend"

# Check if venv exists, activate it
if (Test-Path "$PSScriptRoot\backend\venv\Scripts\Activate.ps1") {
    Write-Host "🐍 Activating virtual environment..." -ForegroundColor Cyan
    & "$PSScriptRoot\backend\venv\Scripts\Activate.ps1"
} else {
    Write-Host "⚠️  No venv found. Using system Python." -ForegroundColor Yellow
}

Write-Host "🚀 Starting InsureClear backend on http://localhost:8000" -ForegroundColor Green
python -m uvicorn api_server:server --host 0.0.0.0 --port 8000 --reload
