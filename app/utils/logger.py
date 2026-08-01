"""Central logging configuration.

Every OCR run, export, error and warning is logged to a rotating log
file under ``app/logs`` as well as to the console, so support issues can
be diagnosed from the log alone.
"""
from __future__ import annotations

import logging
import logging.handlers
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"

_configured = False


def setup_logger(log_dir: Path | None = None, level: int = logging.INFO) -> logging.Logger:
    """Configure the root logger once per process and return it.

    Safe to call multiple times; subsequent calls are no-ops so importing
    this module from tests or multiple entry points does not duplicate
    handlers.
    """
    global _configured
    root = logging.getLogger()
    if _configured:
        return root

    target_dir = log_dir or LOG_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    log_file = target_dir / "imageocr_pro.log"

    root.setLevel(level)

    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    file_handler.setLevel(level)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    console_handler.setLevel(level)

    root.addHandler(file_handler)
    root.addHandler(console_handler)

    _configured = True
    logging.getLogger(__name__).info("Logging initialized -> %s", log_file)
    return root
