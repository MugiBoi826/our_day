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

Kimenet: `installer-dist\OurDay-Setup-0.22.0.exe`.

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
git tag v0.22.0
git push origin v0.22.0
```

A `Build Windows installer` workflow ezután automatikusan:

1. elkészíti az `OurDay.exe` alkalmazást;
2. elkészíti az Inno Setup telepítőt;
3. feltölti a telepítőt Actions artifactként;
4. létrehozza az `Our Day v0.22.0` GitHub Release-t;
5. a telepítőt közvetlenül letölthető release assetként csatolja;
6. automatikusan generált release notes-ot készít.

A kézzel indított `workflow_dispatch` futás továbbra is csak artifactot készít, GitHub Release-t nem.


## 0.22.0 Esküvő alapadatai

- aktív esküvői projekt külön adatmodellben
- menyasszony és vőlegény neve
- esküvő dátuma, helyszíne és címe
- teljes tervezett költségkeret
- megjegyzések
- dashboardon pár neve és automatikus visszaszámlálás
- költségkeret összevetése a tervezett szolgáltatási költségekkel
- meglévő adatbázisok automatikus, adatvesztés nélküli migrációja


## 0.22.1 Meghívási csoport mentési javítás

- javítva az invitation_groups INSERT mező- és értékszám eltérése
- 9 oszlophoz most 9 SQL helykitöltő tartozik
- új meghívási csoport létrehozása ismét működik


## 0.22.2 Meglévő személyek csoporthoz rendelése

- utólag létrehozott csoportokhoz csoport nélküli személyek rendelhetők
- több személy egyszerre kijelölhető
- név szerinti keresés és gyors kijelölés


## 0.22.3 Adatbázis export és import

- teljes SQLite adatbázis exportálása választható fájlba
- adatbázis importálása fájlválasztóval
- import előtt automatikus biztonsági mentés
- SQLite integritás- és Our Day struktúraellenőrzés
- hibás vagy idegen adatbázis nem tölthető be
- import után az alkalmazás teljes felülete azonnal frissül


## 0.23.0 Dashboard 2.0

- központi esküvői fejléc visszaszámlálással
- költségkeret, tervezett költség, rendezett és fizetendő összegek
- sürgős figyelmeztetések feladatokra, fizetésekre, RSVP-re és ültetésre
- közös 45 napos eseménylista
- vendég- és ültetési összesítő
- gyors új szolgáltatás, feladat, vendég és csoport műveletek
- közvetlen vendéglista-export és adatbázis-backup
- görgethető, reszponzívabb kezdőoldal


## 0.23.1 Állapotalapú pénzügyi számítás

- a foglalás előtti szolgáltatások nem számítanak bele a költségekbe
- Ötlet és Ajánlatkérés állapotban minden pénzügyi érték kimarad
- a számítás Lefoglalva állapottól indul
- Részben fizetve állapotnál a foglaló rendezett összegként jelenik meg
- Kifizetve állapotnál a teljes összeg rendezett
- Lemondva állapot továbbra sem számít bele
- a közelgő fizetések listája csak aktív, lefoglalt szolgáltatásokat mutat
