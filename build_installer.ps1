$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

& ".\build_exe.ps1"
if ($LASTEXITCODE -ne 0) { throw "Az EXE build sikertelen." }

$Candidates = @(
    "$env:ProgramFiles(x86)\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe",
    "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe"
)
$ISCC = $Candidates | Where-Object { Test-Path $_ } | Select-Object -First 1

if (-not $ISCC) {
    throw "Az Inno Setup 6 nem található. Telepítsd a https://jrsoftware.org/isdl.php oldalról, majd futtasd újra."
}

Remove-Item -Recurse -Force ".\installer-dist" -ErrorAction SilentlyContinue
& $ISCC ".\installer\OurDay.iss"
if ($LASTEXITCODE -ne 0) { throw "A telepítő build sikertelen." }

$Setup = Get-ChildItem ".\installer-dist\OurDay-Setup-*.exe" | Select-Object -First 1
if (-not $Setup) { throw "A telepítő nem készült el." }
Write-Host "Telepítő elkészült: $($Setup.FullName)" -ForegroundColor Green
