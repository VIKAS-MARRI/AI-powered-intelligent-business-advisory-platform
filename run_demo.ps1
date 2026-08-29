Param(
  [switch]$OpenBrowser
)

Write-Host "Starting RuralBiz AI demo (development mode)"

$root = Split-Path -Parent $MyInvocation.MyCommand.Definition
$backend = Join-Path $root 'backend'

if (-not (Test-Path (Join-Path $backend '.venv'))) {
  Write-Host "Warning: backend/.venv not found. Create venv with: py -3.12 -m venv backend/.venv" -ForegroundColor Yellow
}

Write-Host "Launching backend and frontend in new terminals..."

# Start backend in a new PowerShell window
$backendCmd = "Set-Location -LiteralPath '$backend'; .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000 --host 127.0.0.1"
Start-Process powershell -ArgumentList ('-NoExit','-Command', $backendCmd)

# Start frontend in a new PowerShell window
$frontend = Join-Path $root 'frontend'
$frontendCmd = "Set-Location -LiteralPath '$frontend'; npm run dev"
Start-Process powershell -ArgumentList ('-NoExit','-Command', $frontendCmd)

Write-Host "Started backend on http://localhost:8000 and frontend on http://localhost:5173"

if ($OpenBrowser) {
  Start-Process "http://localhost:5173/demo"
}

Write-Host "Use CTRL+C in the opened terminals to stop servers."
