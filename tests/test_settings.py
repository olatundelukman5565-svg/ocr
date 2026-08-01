from __future__ import annotations

from app.config.settings import SettingsManager


def test_defaults_loaded_when_no_file_exists(tmp_path):
    settings = SettingsManager(config_dir=tmp_path)
    assert settings.get("theme") == "dark"
    assert settings.get("default_ocr_engine") == "tesseract"


def test_set_and_persist_round_trip(tmp_path):
    settings = SettingsManager(config_dir=tmp_path)
    settings.set("theme", "light")

    reloaded = SettingsManager(config_dir=tmp_path)
    assert reloaded.get("theme") == "light"


def test_add_recent_file_dedupes_and_orders(tmp_path):
    settings = SettingsManager(config_dir=tmp_path)
    settings.add_recent_file("a.png")
    settings.add_recent_file("b.png")
    settings.add_recent_file("a.png")
    assert settings.get("recent_files")[:2] == ["a.png", "b.png"]


def test_reset_to_defaults(tmp_path):
    settings = SettingsManager(config_dir=tmp_path)
    settings.set("theme", "light")
    settings.reset_to_defaults()
    assert settings.get("theme") == "dark"


def test_settings_file_is_not_plaintext_json_when_crypto_available(tmp_path):
    settings = SettingsManager(config_dir=tmp_path)
    settings.set("theme", "light")
    if settings._fernet is not None:
        raw = settings.settings_path.read_bytes()
        assert b'"theme"' not in raw
