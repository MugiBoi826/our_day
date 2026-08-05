# Our Day

Windows asztali esküvőszervező alkalmazás PySide6 és SQLite alapon.

## Fejlesztői indítás

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:PYTHONPATH = "src"
python -m our_day.main
```

## Windows EXE

```powershell
powershell.exe -ExecutionPolicy Bypass -File .uild_exe.ps1
```

Kimenet: `dist\OurDay.exe`.

## Windows telepítő

Telepítsd az Inno Setup 6-ot, majd:

```powershell
powershell.exe -ExecutionPolicy Bypass -File .uild_installer.ps1
```

Kimenet: `installer-dist\OurDay-Setup-0.21.0.exe`.

A telepítő automatikusan létrehoz:

- asztali Our Day parancsikont;
- Start menü parancsikont;
- eltávolítási bejegyzést a Windows Alkalmazások között.

## Adatok

A telepített alkalmazás adatbázisa:

```text
%LOCALAPPDATA%\Our Day\data\our_day.db
```

Első indításkor üres adatbázis készül. A demóadatok a **Beállítások → Adatbázis → Demóadatok betöltése** gombbal tölthetők be.

## GitHub Actions

A `.github/workflows/build-windows-installer.yml` workflow kézzel vagy `v*` tag pusholásakor elkészíti a Windows telepítőt, és letölthető artifactként feltölti.
