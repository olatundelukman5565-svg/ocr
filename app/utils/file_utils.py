"""Filesystem helpers: type detection, hashing, and safe temp files."""
from __future__ import annotations

import hashlib
import logging
import tempfile
import uuid
from pathlib import Path
from typing import Iterable, Iterator

from app.config.constants import SUPPORTED_IMAGE_EXTENSIONS, SUPPORTED_PDF_EXTENSIONS

logger = logging.getLogger(__name__)


def is_supported_image(path: str | Path) -> bool:
    return Path(path).suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS


def is_supported_pdf(path: str | Path) -> bool:
    return Path(path).suffix.lower() in SUPPORTED_PDF_EXTENSIONS


def is_supported_file(path: str | Path) -> bool:
    return is_supported_image(path) or is_supported_pdf(path)


def iter_supported_files(root: str | Path) -> Iterator[Path]:
    """Recursively yield every supported image/PDF file under ``root``."""
    root_path = Path(root)
    if root_path.is_file():
        if is_supported_file(root_path):
            yield root_path
        return
    for candidate in sorted(root_path.rglob("*")):
        if candidate.is_file() and is_supported_file(candidate):
            yield candidate


def compute_file_hash(path: str | Path, chunk_size: int = 65536) -> str:
    """Return the SHA-256 hex digest of a file, used for duplicate detection."""
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def find_duplicates(paths: Iterable[str | Path]) -> dict[str, list[str]]:
    """Group input paths by content hash; groups with >1 entry are duplicates."""
    by_hash: dict[str, list[str]] = {}
    for path in paths:
        try:
            file_hash = compute_file_hash(path)
        except OSError:
            logger.warning("Could not hash file for duplicate detection: %s", path)
            continue
        by_hash.setdefault(file_hash, []).append(str(path))
    return {h: files for h, files in by_hash.items() if len(files) > 1}


class SafeTempDir:
    """Context manager creating a private temp directory that is always cleaned up.

    Used for intermediate rendered pages / preprocessed images so nothing
    sensitive lingers in the shared OS temp directory after processing.
    """

    def __init__(self, prefix: str = "imageocr_") -> None:
        self.prefix = prefix
        self._path: Path | None = None

    def __enter__(self) -> Path:
        base = Path(tempfile.gettempdir()) / f"{self.prefix}{uuid.uuid4().hex}"
        base.mkdir(parents=True, exist_ok=False, mode=0o700)
        self._path = base
        return base

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._path is None:
            return
        import shutil

        shutil.rmtree(self._path, ignore_errors=True)


def unique_output_path(directory: str | Path, base_name: str, extension: str) -> Path:
    """Return a non-clashing output path, appending ``(n)`` if needed."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    extension = extension if extension.startswith(".") else f".{extension}"
    candidate = directory / f"{base_name}{extension}"
    counter = 1
    while candidate.exists():
        candidate = directory / f"{base_name} ({counter}){extension}"
        counter += 1
    return candidate
