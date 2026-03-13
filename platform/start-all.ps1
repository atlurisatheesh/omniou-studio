# Startup script for Ominou Studio Platform (Windows PowerShell)
# Starts all backend services + gateway

$ErrorActionPreference = "Continue"
$PythonExe = "python"

Write-Host "`n=== Ominou Studio Platform ===" -ForegroundColor Cyan
Write-Host "Starting all services...`n" -ForegroundColor Yellow

$services = @(
    @{ Name = "Auth";     Port = 8001; Path = "services/auth" },
    @{ Name = "Voice";    Port = 8002; Path = "services/voice" },
    @{ Name = "Design";   Port = 8003; Path = "services/design" },
    @{ Name = "Code";     Port = 8004; Path = "services/code" },
    @{ Name = "Video";    Port = 8005; Path = "services/video" },
    @{ Name = "Writer";   Port = 8006; Path = "services/writer" },
    @{ Name = "Music";    Port = 8007; Path = "services/music" },
    @{ Name = "Workflow"; Port = 8008; Path = "services/workflow" },
    @{ Name = "Billing";  Port = 8009; Path = "services/billing" }
)

$jobs = @()

foreach ($svc in $services) {
    $svcPath = Join-Path $PSScriptRoot $svc.Path
    Write-Host "  Starting $($svc.Name) service on port $($svc.Port)..." -ForegroundColor Green
    $job = Start-Process -FilePath $PythonExe -ArgumentList "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", $svc.Port -WorkingDirectory $svcPath -PassThru -WindowStyle Hidden
    $jobs += $job
}

# Start Gateway
$gatewayPath = Join-Path $PSScriptRoot "gateway"
Write-Host "  Starting API Gateway on port 8080..." -ForegroundColor Green
$gatewayJob = Start-Process -FilePath $PythonExe -ArgumentList "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080" -WorkingDirectory $gatewayPath -PassThru -WindowStyle Hidden
$jobs += $gatewayJob

Write-Host "`nAll services started!" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Gateway:  http://localhost:8080" -ForegroundColor White
Write-Host "  Auth:     http://localhost:8001" -ForegroundColor White
Write-Host "  Voice:    http://localhost:8002" -ForegroundColor White
Write-Host "  Design:   http://localhost:8003" -ForegroundColor White
Write-Host "  Code:     http://localhost:8004" -ForegroundColor White
Write-Host "  Video:    http://localhost:8005" -ForegroundColor White
Write-Host "  Writer:   http://localhost:8006" -ForegroundColor White
Write-Host "  Music:    http://localhost:8007" -ForegroundColor White
Write-Host "  Workflow: http://localhost:8008" -ForegroundColor White
Write-Host "  Billing:  http://localhost:8009" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C to stop all services" -ForegroundColor Yellow

try {
    while ($true) { Start-Sleep -Seconds 1 }
} finally {
    Write-Host "`nStopping all services..." -ForegroundColor Red
    foreach ($job in $jobs) {
        if (!$job.HasExited) { Stop-Process -Id $job.Id -Force -ErrorAction SilentlyContinue }
    }
    Write-Host "All services stopped." -ForegroundColor Yellow
}
