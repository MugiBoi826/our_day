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


## Automatikus GitHub Release

A Windows telepítő GitHub Release-be történő publikálásához hozz létre és pusholj egy verziótaget:

```powershell
git tag v0.21.0
git push origin v0.21.0
```

A `Build Windows installer` workflow ezután automatikusan:

1. elkészíti az `OurDay.exe` alkalmazást;
2. elkészíti az Inno Setup telepítőt;
3. feltölti a telepítőt Actions artifactként;
4. létrehozza az `Our Day v0.21.0` GitHub Release-t;
5. a telepítőt közvetlenül letölthető release assetként csatolja;
6. automatikusan generált release notes-ot készít.

A kézzel indított `workflow_dispatch` futás továbbra is csak artifactot készít, GitHub Release-t nem.
