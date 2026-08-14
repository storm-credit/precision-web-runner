$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

if (-not (Test-Path ".venv\Scripts\python.exe")) {
  throw "Run .\scripts\setup_windows.ps1 first."
}

& .\.venv\Scripts\python.exe -m precision_runner --host 127.0.0.1 --port 8765
