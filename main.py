"""
FileX — Floating Universal File Converter for Windows
Entry point: initialises the QApplication, applies theme, and launches the main window.
"""

import sys
import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Ensure the project root is on sys.path so all sub-packages resolve correctly
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(sys._MEIPASS) if getattr(sys, chr(102)+chr(114)+chr(111)+chr(122)+chr(101)+chr(110), False) else Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

# ---------------------------------------------------------------------------
# Qt / PySide6 imports
# ---------------------------------------------------------------------------
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QCoreApplication
from PySide6.QtGui import QIcon, QFont

# ---------------------------------------------------------------------------
# Internal imports (resolved after sys.path is set)
# ---------------------------------------------------------------------------
from core.settings_manager import SettingsManager
from ui.main_window import MainWindow


def apply_stylesheet(app: QApplication, settings: SettingsManager) -> None:
    """Load and apply the QSS dark theme from the assets directory."""
    qss_path = PROJECT_ROOT / "assets" / "styles" / "dark_theme.qss"
    if qss_path.exists():
        with open(qss_path, "r", encoding="utf-8") as fh:
            app.setStyleSheet(fh.read())
    else:
        # Minimal inline fallback so the app is still usable
        app.setStyleSheet(
            "QWidget { background-color: #1e1e2e; color: #cdd6f4; }"
            "QPushButton { background-color: #313244; border-radius: 6px; padding: 6px 14px; }"
            "QPushButton:hover { background-color: #45475a; }"
        )


def main() -> int:
    """
    Application entry point.

    Returns:
        int: Exit code returned to the OS.
    """
    # High-DPI support (must be set before QApplication is created)
    QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QCoreApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("FileX")
    app.setApplicationDisplayName("FileX — Universal File Converter")
    app.setOrganizationName("FileX")
    app.setOrganizationDomain("filex.app")

    # Set a clean default font
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    # Optionally set taskbar icon
    icon_path = PROJECT_ROOT / "assets" / "images" / "logo.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    # Initialise settings (creates %APPDATA%/FileX/settings.json if absent)
    settings = SettingsManager()

    # Apply QSS theme
    apply_stylesheet(app, settings)

    # Create and show main window (which embeds the floating widget)
    window = MainWindow(settings)
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
