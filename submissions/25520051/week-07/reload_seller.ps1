# Reload the market seller with the current seller.py without restarting the kit (the tunnel URL stays).
#   powershell -File reload_seller.ps1 -Port <seller port from the kit log>
# With SELLER_RELOAD=1 the uvicorn reloader owns the port and runs the seller in a worker process. On this
# Windows/Google Drive folder its file watcher missed changes made by cp or sed (20:5x-21:1x), so instead we
# stop the worker: the reloader starts a fresh one from the current seller.py on the same port.
param([Parameter(Mandatory = $true)][int]$Port)
$reloader = (Get-NetTCPConnection -State Listen -LocalPort $Port).OwningProcess | Select-Object -First 1
$workers = Get-CimInstance Win32_Process -Filter "ParentProcessId=$reloader"
$workers | ForEach-Object { Stop-Process -Id $_.ProcessId -Force; "stopped worker $($_.ProcessId)" }
Start-Sleep -Seconds 10
Get-CimInstance Win32_Process -Filter "ParentProcessId=$reloader" | ForEach-Object { "new worker $($_.ProcessId)" }
