"""Settings: theme, default engine/language, GPU/CPU, export folder,
autosave, and a read-only hotkey reference.
"""
from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.config.constants import OCR_ENGINES, SUPPORTED_LANGUAGES
from app.config.settings import SettingsManager


class SettingsPage(QWidget):
    theme_changed = Signal(str)

    def __init__(self, settings: SettingsManager, parent=None) -> None:
        super().__init__(parent)
        self.settings = settings
        self._build_ui()
        self._load_values()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        title = QLabel("Settings")
        title.setObjectName("SectionTitle")
        root.addWidget(title)

        form = QFormLayout()

        theme_row = QHBoxLayout()
        self.dark_radio = QRadioButton("Dark")
        self.light_radio = QRadioButton("Light")
        theme_row.addWidget(self.dark_radio)
        theme_row.addWidget(self.light_radio)
        form.addRow("Theme:", theme_row)

        self.engine_combo = QComboBox()
        self.engine_combo.addItems(OCR_ENGINES)
        form.addRow("Default OCR engine:", self.engine_combo)

        self.language_combo = QComboBox()
        for name in SUPPORTED_LANGUAGES:
            self.language_combo.addItem(name)
        form.addRow("Default language:", self.language_combo)

        self.gpu_checkbox = QCheckBox("Use GPU when available")
        form.addRow("GPU:", self.gpu_checkbox)

        self.cpu_threads_spin = QSpinBox()
        self.cpu_threads_spin.setRange(1, 64)
        form.addRow("CPU threads:", self.cpu_threads_spin)

        export_row = QHBoxLayout()
        self.export_folder_edit = QLineEdit()
        browse_btn = QPushButton("Browse…")
        browse_btn.setObjectName("SecondaryButton")
        browse_btn.clicked.connect(self._browse_export_folder)
        export_row.addWidget(self.export_folder_edit)
        export_row.addWidget(browse_btn)
        form.addRow("Default export folder:", export_row)

        self.autosave_checkbox = QCheckBox("Automatically save every OCR run to history")
        form.addRow("Autosave:", self.autosave_checkbox)

        root.addLayout(form)

        hotkeys_label = QLabel("Keyboard Shortcuts")
        hotkeys_label.setObjectName("SectionTitle")
        root.addWidget(hotkeys_label)
        hotkeys_form = QFormLayout()
        for action, keys in self.settings.get("hotkeys", {}).items():
            hotkeys_form.addRow(action.replace("_", " ").title() + ":", QLabel(keys))
        root.addLayout(hotkeys_form)

        buttons_row = QHBoxLayout()
        save_btn = QPushButton("Save Settings")
        save_btn.clicked.connect(self._save)
        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.setObjectName("DangerButton")
        reset_btn.clicked.connect(self._reset)
        buttons_row.addWidget(save_btn)
        buttons_row.addWidget(reset_btn)
        buttons_row.addStretch(1)
        root.addLayout(buttons_row)
        root.addStretch(1)

    def _load_values(self) -> None:
        theme = self.settings.get("theme", "dark")
        self.dark_radio.setChecked(theme == "dark")
        self.light_radio.setChecked(theme == "light")

        engine_index = self.engine_combo.findText(self.settings.get("default_ocr_engine", "tesseract"))
        self.engine_combo.setCurrentIndex(max(engine_index, 0))

        default_lang_code = self.settings.get("default_language", "en")
        lang_name = next((name for name, code in SUPPORTED_LANGUAGES.items() if code == default_lang_code), "English")
        lang_index = self.language_combo.findText(lang_name)
        self.language_combo.setCurrentIndex(max(lang_index, 0))

        self.gpu_checkbox.setChecked(bool(self.settings.get("use_gpu", False)))
        self.cpu_threads_spin.setValue(int(self.settings.get("cpu_threads", 4)))
        self.export_folder_edit.setText(self.settings.get("default_export_folder", ""))
        self.autosave_checkbox.setChecked(bool(self.settings.get("autosave", True)))

    def _browse_export_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select default export folder", self.export_folder_edit.text())
        if folder:
            self.export_folder_edit.setText(folder)

    def _save(self) -> None:
        theme = "dark" if self.dark_radio.isChecked() else "light"
        self.settings.update(
            {
                "theme": theme,
                "default_ocr_engine": self.engine_combo.currentText(),
                "default_language": SUPPORTED_LANGUAGES.get(self.language_combo.currentText(), "en"),
                "use_gpu": self.gpu_checkbox.isChecked(),
                "cpu_threads": self.cpu_threads_spin.value(),
                "default_export_folder": self.export_folder_edit.text(),
                "autosave": self.autosave_checkbox.isChecked(),
            }
        )
        self.theme_changed.emit(theme)
        QMessageBox.information(self, "Settings", "Settings saved.")

    def _reset(self) -> None:
        self.settings.reset_to_defaults()
        self._load_values()
        self.theme_changed.emit(self.settings.get("theme", "dark"))
