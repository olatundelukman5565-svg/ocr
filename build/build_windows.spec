# PyInstaller spec for a Windows (or current-platform) ImageOCR Pro build.
#
# Usage:
#   pip install -r requirements.txt
#   pyinstaller build/build_windows.spec
#
# Output executable lands in dist/ImageOCR_Pro/ (onedir build -- recommended
# for a Qt + OpenCV app so startup stays fast and antivirus false-positives
# on a single giant onefile binary are avoided).
import sys
from pathlib import Path

block_cipher = None

PROJECT_ROOT = Path(SPECPATH).parent

hidden_imports = [
    "pytesseract",
    "cv2",
    "PIL",
    "fitz",
    "docx",
    "openpyxl",
    "reportlab",
    "sqlite3",
    "langdetect",
    "spellchecker",
    "cryptography",
]

a = Analysis(
    [str(PROJECT_ROOT / "app" / "main.py")],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=[
        (str(PROJECT_ROOT / "app" / "resources"), "app/resources"),
    ],
    hiddenimports=hidden_imports,
    hookspath=[],
    runtime_hooks=[],
    excludes=["easyocr", "paddleocr", "paddle"],  # opt-in, heavy; add back if bundling GPU engines
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="ImageOCR_Pro",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="ImageOCR_Pro",
)
