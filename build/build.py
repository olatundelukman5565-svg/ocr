"""Convenience wrapper around PyInstaller for building a distributable
ImageOCR Pro executable (Windows/macOS/Linux -- PyInstaller targets
whichever platform it runs on).

Usage:
    python build/build.py
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SPEC_FILE = Path(__file__).resolve().parent / "build_windows.spec"


def main() -> int:
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        str(SPEC_FILE),
        "--distpath",
        str(PROJECT_ROOT / "dist"),
        "--workpath",
        str(PROJECT_ROOT / "build" / "work"),
        "--noconfirm",
    ]
    print("Running:", " ".join(cmd))
    return subprocess.call(cmd, cwd=str(PROJECT_ROOT))


if __name__ == "__main__":
    raise SystemExit(main())
