$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    py -3.13 -m venv .venv
}

$Python = ".\.venv\Scripts\python.exe"

& $Python -m pip install -r requirements.txt
& $Python ".\run_our_day.py"
