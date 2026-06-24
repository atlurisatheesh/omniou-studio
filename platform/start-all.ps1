# Startup script for Ominou Studio Platform (Windows PowerShell)
# Two servers: Backend (port 1993) + Frontend (port 2102)

$ErrorActionPreference = "Continue"
$PythonExe = "python"

Write-Host "`n=== Ominou Studio Platform ===" -ForegroundColor Cyan
Write-Host "Starting servers...`n" -ForegroundColor Yellow

$jobs = @()

# Server 1: Backend (Gateway + Video engine built-in)
$gatewayPath = Join-Path $PSScriptRoot "gateway"
Write-Host "  Starting Backend on port 1993..." -ForegroundColor Green
$backendJob = Start-Process -FilePath $PythonExe -ArgumentList "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "1993" -WorkingDirectory $gatewayPath -PassThru -WindowStyle Hidden
$jobs += $backendJob

# Server 2: Frontend (Next.js)
$frontendPath = Join-Path $PSScriptRoot "frontend"
Write-Host "  Starting Frontend on port 2102..." -ForegroundColor Green
$frontendJob = Start-Process -FilePath "npx" -ArgumentList "next", "dev", "--port", "2102" -WorkingDirectory $frontendPath -PassThru -WindowStyle Hidden
$jobs += $frontendJob

Write-Host "`nAll servers started!" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Backend:  http://localhost:1993" -ForegroundColor White
Write-Host "  Frontend: http://localhost:2102" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C to stop all servers" -ForegroundColor Yellow

try {
    while ($true) { Start-Sleep -Seconds 1 }
} finally {
    Write-Host "`nStopping all servers..." -ForegroundColor Red
    foreach ($job in $jobs) {
        if (!$job.HasExited) { Stop-Process -Id $job.Id -Force -ErrorAction SilentlyContinue }
    }
    Write-Host "All servers stopped." -ForegroundColor Yellow
}
