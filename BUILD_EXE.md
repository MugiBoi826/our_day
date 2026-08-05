# Our Day – Windows build

## EXE készítése

```powershell
powershell.exe -ExecutionPolicy Bypass -File .\build_exe.ps1
```

Kimenet:

```text
dist\OurDay.exe
```

## Telepítő készítése

1. Telepítsd az Inno Setup 6-ot.
2. Futtasd:

```powershell
powershell.exe -ExecutionPolicy Bypass -File .\build_installer.ps1
```

Kimenet:

```text
installer-dist\OurDay-Setup-0.21.0.exe
```

A telepítő automatikusan létrehozza az asztali és Start menü parancsikont.

## GitHubon

A `Build Windows installer` workflow kézzel indítható az Actions oldalon. A kész telepítő az `OurDay-Windows-Installer` artifactban tölthető le.


## GitHub Release készítése

A repositoryban található workflow verziótag pusholásakor automatikusan elkészíti és publikálja a Windows telepítőt:

```powershell
git tag v0.21.0
git push origin v0.21.0
```

A kész telepítő a repository `Releases` oldalán jelenik meg. Új verzióhoz mindig új taget használj, például `v0.21.1`, `v0.22.0`.
