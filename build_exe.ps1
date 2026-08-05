$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$Python = ".\.venv\Scripts\python.exe"
$ExePath = Join-Path $PSScriptRoot "dist\OurDay.exe"

if (-not (Test-Path $Python)) {
    Write-Host "Virtuális környezet létrehozása..." -ForegroundColor Yellow
    py -3.13 -m venv .venv
}

& $Python -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw "A pip frissítése sikertelen." }
& $Python -m pip install -r requirements.txt -r requirements-build.txt
if ($LASTEXITCODE -ne 0) { throw "A build függőségeinek telepítése sikertelen." }

Get-Process -Name "OurDay" -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Milliseconds 500

Remove-Item -Recurse -Force ".\build" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force ".\dist" -ErrorAction SilentlyContinue

& $Python -m PyInstaller --noconfirm --clean ".\OurDay.spec"
if ($LASTEXITCODE -ne 0) { throw "A PyInstaller build hibával leállt." }
if (-not (Test-Path $ExePath)) { throw "A dist\OurDay.exe nem készült el." }

Write-Host "EXE elkészült: $ExePath" -ForegroundColor Green
