# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path


PROJECT_ROOT = Path(SPECPATH).resolve()


def collect_tree(src_root: Path, dst_root: str, patterns: tuple[str, ...]) -> list[tuple[str, str]]:
    items: list[tuple[str, str]] = []
    if not src_root.exists():
        return items

    for pattern in patterns:
        for src_file in src_root.rglob(pattern):
            if not src_file.is_file():
                continue
            relative_parent = src_file.relative_to(src_root).parent
            dst_dir = Path(dst_root) / relative_parent
            items.append((str(src_file), str(dst_dir)))

    return items


datas: list[tuple[str, str]] = []
datas += collect_tree(PROJECT_ROOT / "ui" / "qml", "ui/qml", ("*.qml", "*.js", "*.png", "*.svg", "*.json"))

binaries: list[tuple[str, str]] = []
binaries += collect_tree(PROJECT_ROOT / "libTSCANAPI" / "windows", "libTSCANAPI/windows", ("*.dll",))
binaries += collect_tree(PROJECT_ROOT / "libTSCANAPI" / "linux", "libTSCANAPI/linux", ("*.so",))

hiddenimports = [
    "PySide6.QtQml",
    "PySide6.QtQuick",
    "PySide6.QtQuickControls2",
]

a = Analysis(
    ["main.py"],
    pathex=[str(PROJECT_ROOT)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["PyQt5", "PyQt6"],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="tosun-geehy-can-uds-collector-tool",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="tosun-geehy-can-uds-collector-tool",
)
