# Stop all Ominou Studio services
Write-Host "Stopping Ominou Studio services..." -ForegroundColor Red

# Kill processes on specific ports
$ports = @(8001, 8002, 8003, 8004, 8005, 8006, 8007, 8008, 8009, 8080)
foreach ($port in $ports) {
    $connections = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    foreach ($conn in $connections) {
        if ($conn.OwningProcess -ne 0) {
            Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
            Write-Host "  Stopped process on port $port (PID: $($conn.OwningProcess))" -ForegroundColor Yellow
        }
    }
}

Write-Host "All services stopped." -ForegroundColor Green
