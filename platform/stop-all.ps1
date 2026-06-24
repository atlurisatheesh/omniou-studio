# Stop all Ominou Studio servers
Write-Host "Stopping Ominou Studio servers..." -ForegroundColor Red

# Kill processes on the two server ports
$ports = @(1993, 2102)
foreach ($port in $ports) {
    $connections = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    foreach ($conn in $connections) {
        if ($conn.OwningProcess -ne 0) {
            Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
            Write-Host "  Stopped process on port $port (PID: $($conn.OwningProcess))" -ForegroundColor Yellow
        }
    }
}

Write-Host "All servers stopped." -ForegroundColor Green
