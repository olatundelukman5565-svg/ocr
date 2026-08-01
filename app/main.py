"""ImageOCR Pro entry point."""
from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from app.config.constants import APP_NAME, ORG_NAME
from app.utils.logger import setup_logger


def main() -> int:
    setup_logger()

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(ORG_NAME)

    from app.ui.main_window import MainWindow  # deferred: needs QApplication first

    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
