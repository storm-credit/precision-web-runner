$ErrorActionPreference = "Continue"
Set-Location (Split-Path $PSScriptRoot -Parent)

Write-Host "Precision Runner Windows Preflight" -ForegroundColor Cyan
Write-Host ""

Write-Host "[1] Python"
py -3 --version

Write-Host ""
Write-Host "[2] Chrome"
$chromeCandidates = @(
  "$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
  "$env:ProgramFiles(x86)\Google\Chrome\Application\chrome.exe",
  "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe"
)
$chrome = $chromeCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if ($chrome) { Write-Host "Chrome OK: $chrome" -ForegroundColor Green } else { Write-Warning "Google Chrome not found in common paths." }

Write-Host ""
Write-Host "[3] Windows Time"
w32tm /query /status

Write-Host ""
Write-Host "[4] Active power scheme"
powercfg /getactivescheme

Write-Host ""
Write-Host "[5] Runner environment"
if (Test-Path ".venv\Scripts\python.exe") {
  & .\.venv\Scripts\python.exe -c "import sys; print(sys.version); import precision_runner; print('precision_runner', precision_runner.__version__)"
} else {
  Write-Warning "Virtual environment missing. Run .\scripts\setup_windows.ps1"
}

Write-Host ""
Write-Host "Review sleep/hibernate manually before the live window. This script does not change system power settings." -ForegroundColor Yellow
