"""Persistent, encrypted application settings.

Settings are stored as an encrypted JSON blob under the user's home
directory (``~/.imageocr_pro/settings.enc``) so that local configuration
(export paths, API-free operation, etc.) is not left as plain text on
disk. Encryption uses a locally generated Fernet key; if the
``cryptography`` package is unavailable the manager transparently falls
back to plain JSON so the application keeps working offline.
"""
from __future__ import annotations

import json
import logging
import threading
from pathlib import Path
from typing import Any, Dict

from app.config.constants import (
    DEFAULT_CONFIG_DIR_NAME,
    DEFAULT_KEY_FILENAME,
    DEFAULT_SETTINGS_FILENAME,
)

logger = logging.getLogger(__name__)

try:
    from cryptography.fernet import Fernet

    _HAS_CRYPTO = True
except ImportError:  # pragma: no cover - exercised when cryptography is absent
    _HAS_CRYPTO = False

DEFAULT_SETTINGS: Dict[str, Any] = {
    "theme": "dark",
    "ui_language": "English",
    "default_ocr_engine": "tesseract",
    "default_language": "auto",
    "default_mode": "balanced",
    "confidence_threshold": 60,
    "use_gpu": False,
    "cpu_threads": 4,
    "default_export_folder": str(Path.home() / "ImageOCR_Pro" / "Exports"),
    "autosave": True,
    "preprocessing": {
        "deskew": True,
        "denoise": True,
        "clahe_contrast": True,
        "sharpen": False,
        "adaptive_threshold": False,
        "remove_shadows": True,
        "perspective_correction": False,
        "grayscale": True,
    },
    "recent_files": [],
    "hotkeys": {
        "open_file": "Ctrl+O",
        "open_folder": "Ctrl+Shift+O",
        "run_ocr": "Ctrl+R",
        "export": "Ctrl+E",
        "find": "Ctrl+F",
        "save": "Ctrl+S",
    },
}


class SettingsManager:
    """Loads, persists and mutates application settings.

    Thread-safe: batch workers and the UI thread can both touch settings
    without corrupting the on-disk file.
    """

    def __init__(self, config_dir: Path | None = None) -> None:
        self._lock = threading.RLock()
        self.config_dir = config_dir or (Path.home() / DEFAULT_CONFIG_DIR_NAME)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.settings_path = self.config_dir / DEFAULT_SETTINGS_FILENAME
        self.key_path = self.config_dir / DEFAULT_KEY_FILENAME
        self._fernet = self._load_or_create_key() if _HAS_CRYPTO else None
        self._data: Dict[str, Any] = self._load()

    # -- key / crypto -----------------------------------------------------
    def _load_or_create_key(self) -> "Fernet":
        if self.key_path.exists():
            key = self.key_path.read_bytes()
        else:
            key = Fernet.generate_key()
            self.key_path.write_bytes(key)
            try:
                self.key_path.chmod(0o600)
            except OSError:
                pass
        return Fernet(key)

    # -- persistence --------------------------------------------------------
    def _load(self) -> Dict[str, Any]:
        data = json.loads(json.dumps(DEFAULT_SETTINGS))  # deep copy
        if not self.settings_path.exists():
            return data
        try:
            raw = self.settings_path.read_bytes()
            if self._fernet is not None:
                raw = self._fernet.decrypt(raw)
            loaded = json.loads(raw.decode("utf-8"))
            data.update(loaded)
        except Exception:  # noqa: BLE001 - corrupted/unreadable settings must not crash the app
            logger.exception("Failed to load settings from %s; using defaults", self.settings_path)
        return data

    def save(self) -> None:
        with self._lock:
            try:
                payload = json.dumps(self._data, indent=2).encode("utf-8")
                if self._fernet is not None:
                    payload = self._fernet.encrypt(payload)
                tmp_path = self.settings_path.with_suffix(".tmp")
                tmp_path.write_bytes(payload)
                tmp_path.replace(self.settings_path)
            except OSError:
                logger.exception("Failed to persist settings to %s", self.settings_path)

    # -- accessors ------------------------------------------------------------
    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            return self._data.get(key, default)

    def set(self, key: str, value: Any, autosave: bool = True) -> None:
        with self._lock:
            self._data[key] = value
            if autosave:
                self.save()

    def update(self, values: Dict[str, Any], autosave: bool = True) -> None:
        with self._lock:
            self._data.update(values)
            if autosave:
                self.save()

    def all(self) -> Dict[str, Any]:
        with self._lock:
            return json.loads(json.dumps(self._data))

    def add_recent_file(self, path: str, limit: int = 20) -> None:
        with self._lock:
            recents = self._data.setdefault("recent_files", [])
            if path in recents:
                recents.remove(path)
            recents.insert(0, path)
            del recents[limit:]
            self.save()

    def reset_to_defaults(self) -> None:
        with self._lock:
            self._data = json.loads(json.dumps(DEFAULT_SETTINGS))
            self.save()


_settings_instance: SettingsManager | None = None


def get_settings() -> SettingsManager:
    """Return the process-wide singleton :class:`SettingsManager`."""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = SettingsManager()
    return _settings_instance
