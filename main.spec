# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for tosun-geehy-can-uds-collector-tool.

The build is configured as onedir because the application depends on external
CAN adapter libraries (libTSCANAPI DLL/SO set) and QML resources.
"""

from __future__ import annotations

from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules


APP_NAME = "tosun-geehy-can-uds-collector-tool"
PROJECT_ROOT = Path(SPECPATH).resolve()
ENTRY_SCRIPT = PROJECT_ROOT / "main.py"

QML_ROOT = PROJECT_ROOT / "ui" / "qml"
LIB_TSCAN_WINDOWS_ROOT = PROJECT_ROOT / "libTSCANAPI" / "windows"
LIB_TSCAN_LINUX_ROOT = PROJECT_ROOT / "libTSCANAPI" / "linux"
FIRMWARE_ROOT = PROJECT_ROOT / "firmware"


def collect_tree(src_root: Path, dst_root: str, patterns: tuple[str, ...]) -> list[tuple[str, str]]:
    """Recursively collects files from src_root into destination tree."""
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
# QML UI + assets.
datas += collect_tree(
    QML_ROOT,
    "ui/qml",
    ("*.qml", "*.js", "*.json", "*.png", "*.svg", "*.qm", "*.ttf", "*.otf"),
)
# Firmware samples and docs shipped with the app.
datas += collect_tree(FIRMWARE_ROOT, "firmware", ("*.bin", "*.hex"))
for doc_name in ("README.md", "requirements.txt"):
    doc_path = PROJECT_ROOT / doc_name
    if doc_path.exists():
        datas.append((str(doc_path), "."))

binaries: list[tuple[str, str]] = []
binaries += collect_tree(LIB_TSCAN_WINDOWS_ROOT, "libTSCANAPI/windows", ("*.dll",))
binaries += collect_tree(LIB_TSCAN_LINUX_ROOT, "libTSCANAPI/linux", ("*.so",))

# Explicit + discovered imports to avoid runtime misses with dynamic loading.
hiddenimports = [
    "PySide6.QtQml",
    "PySide6.QtQuick",
    "PySide6.QtQuickControls2",
    "ui.qml.app_controller",
    "ui.qml.collector_csv_manager",
    "app_can.CanDevice",
    "j1939.j1939_can_identifier",
    "uds.bootloader",
    "uds.data_identifiers",
    "uds.uds_identifiers",
]
hiddenimports += collect_submodules("ui.qml.app_controller_parts")
hiddenimports += collect_submodules("uds.services")

excludes = ["PyQt5", "PyQt6", "tkinter", "matplotlib.tests", "numpy.tests"]

a = Analysis(
    [str(ENTRY_SCRIPT)],
    pathex=[str(PROJECT_ROOT)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
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
    upx=False,
    upx_exclude=[],
    name=APP_NAME,
)
