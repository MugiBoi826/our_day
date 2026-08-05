# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path


project_root = Path(SPECPATH)
source_root = project_root / "src"

datas = [
    (
        str(project_root / "resources" / "demo" / "our_day_demo.db"),
        "resources/demo",
    ),
    (
        str(project_root / "assets" / "our_day.ico"),
        "assets",
    ),
]

analysis = Analysis(
    [str(project_root / "run_our_day.py")],
    pathex=[str(source_root)],
    binaries=[],
    datas=datas,
    hiddenimports=[
        "xlsxwriter",
        "xlsxwriter.workbook",
        "xlsxwriter.worksheet",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(analysis.pure)

exe = EXE(
    pyz,
    analysis.scripts,
    analysis.binaries,
    analysis.datas,
    [],
    name="OurDay",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(project_root / "assets" / "our_day.ico"),
    version=str(project_root / "build_config" / "version_info.txt"),
)
