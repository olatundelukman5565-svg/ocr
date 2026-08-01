"""Dark and light Qt stylesheets: rounded buttons, flat modern palette."""
from __future__ import annotations

_COMMON = """
QWidget { font-family: 'Segoe UI', 'Inter', 'Helvetica Neue', Arial, sans-serif; font-size: 13px; }
QPushButton {
    border-radius: 8px;
    padding: 8px 16px;
    border: none;
    font-weight: 600;
}
QPushButton:disabled { opacity: 0.5; }
QLineEdit, QComboBox, QSpinBox, QTextEdit, QPlainTextEdit, QListWidget, QTableWidget {
    border-radius: 6px;
    padding: 4px 8px;
    border: 1px solid palette(mid);
}
QProgressBar { border-radius: 6px; text-align: center; height: 16px; }
QProgressBar::chunk { border-radius: 6px; }
QToolTip { border-radius: 4px; padding: 4px; }
QTabBar::tab { border-radius: 6px; padding: 6px 14px; margin: 2px; }
"""

DARK_QSS = _COMMON + """
QMainWindow, QWidget { background-color: #1e1f26; color: #e8e8ec; }
QWidget#Sidebar { background-color: #16171d; }
QPushButton#NavButton {
    text-align: left;
    padding: 10px 16px;
    background: transparent;
    color: #c7c9d1;
    border-radius: 8px;
}
QPushButton#NavButton:hover { background-color: #262833; }
QPushButton#NavButton:checked { background-color: #3d5afe; color: white; }
QPushButton { background-color: #3d5afe; color: white; }
QPushButton:hover { background-color: #5169ff; }
QPushButton:pressed { background-color: #2f46cc; }
QPushButton#SecondaryButton { background-color: #2b2d38; color: #e8e8ec; }
QPushButton#SecondaryButton:hover { background-color: #363845; }
QPushButton#DangerButton { background-color: #e5484d; }
QPushButton#DangerButton:hover { background-color: #f2666a; }
QFrame#Card { background-color: #262833; border-radius: 12px; padding: 12px; }
QLineEdit, QComboBox, QSpinBox, QTextEdit, QPlainTextEdit, QListWidget, QTableWidget {
    background-color: #262833; border: 1px solid #363845; color: #e8e8ec;
}
QHeaderView::section { background-color: #262833; color: #c7c9d1; border: none; padding: 6px; }
QProgressBar { background-color: #262833; border: 1px solid #363845; }
QProgressBar::chunk { background-color: #3d5afe; }
QStatusBar { background-color: #16171d; color: #9a9caa; }
QLabel#SectionTitle { font-size: 20px; font-weight: 700; }
QLabel#StatValue { font-size: 26px; font-weight: 700; color: #3d5afe; }
QLabel#Muted { color: #9a9caa; }
"""

LIGHT_QSS = _COMMON + """
QMainWindow, QWidget { background-color: #f5f6fa; color: #1a1b1f; }
QWidget#Sidebar { background-color: #ffffff; border-right: 1px solid #e4e5eb; }
QPushButton#NavButton {
    text-align: left;
    padding: 10px 16px;
    background: transparent;
    color: #3a3c46;
    border-radius: 8px;
}
QPushButton#NavButton:hover { background-color: #eef0fb; }
QPushButton#NavButton:checked { background-color: #3d5afe; color: white; }
QPushButton { background-color: #3d5afe; color: white; }
QPushButton:hover { background-color: #5169ff; }
QPushButton:pressed { background-color: #2f46cc; }
QPushButton#SecondaryButton { background-color: #eceef5; color: #1a1b1f; }
QPushButton#SecondaryButton:hover { background-color: #dfe2ee; }
QPushButton#DangerButton { background-color: #e5484d; }
QPushButton#DangerButton:hover { background-color: #f2666a; }
QFrame#Card { background-color: #ffffff; border: 1px solid #e4e5eb; border-radius: 12px; padding: 12px; }
QLineEdit, QComboBox, QSpinBox, QTextEdit, QPlainTextEdit, QListWidget, QTableWidget {
    background-color: #ffffff; border: 1px solid #dcdfe8; color: #1a1b1f;
}
QHeaderView::section { background-color: #f0f1f7; color: #3a3c46; border: none; padding: 6px; }
QProgressBar { background-color: #eceef5; border: 1px solid #dcdfe8; }
QProgressBar::chunk { background-color: #3d5afe; }
QStatusBar { background-color: #ffffff; color: #6b6d78; border-top: 1px solid #e4e5eb; }
QLabel#SectionTitle { font-size: 20px; font-weight: 700; }
QLabel#StatValue { font-size: 26px; font-weight: 700; color: #3d5afe; }
QLabel#Muted { color: #6b6d78; }
"""


def stylesheet_for(theme: str) -> str:
    return DARK_QSS if theme == "dark" else LIGHT_QSS
