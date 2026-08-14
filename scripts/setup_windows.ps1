$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
  throw "Python launcher 'py' was not found. Install Python 3.11+ first."
}

if (-not (Test-Path ".venv")) {
  py -3 -m venv .venv
}

& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -e ".[browser]"

Write-Host ""
Write-Host "Setup complete." -ForegroundColor Green
Write-Host "Next: .\scripts\run_windows.ps1"
Write-Host "Precision Runner will launch Google Chrome with its own local profile. Log in to T1 there once."
