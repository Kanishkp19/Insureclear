# ============================================================
# InsureClear Integrated - Frontend Startup Script
# ============================================================
# Run this from the InsureClear_Integrated folder:
#   .\start_frontend.ps1

Set-Location "$PSScriptRoot\frontend"

Write-Host "📦 Starting InsureClear frontend (Vite dev server)..." -ForegroundColor Green
npm run dev
