"""
ui/__init__.py
--------------
FileX User Interface package:
  - MainWindow: Full desktop dashboard and shell
  - FloatingWidget: Glassmorphic always-on-top desktop converter
  - ConversionDialog: Drop review and format selector dialog
  - HistoryPage: Conversion logs and metrics
  - SettingsPage: Application preferences
"""

from ui.main_window import MainWindow
from ui.floating_widget import FloatingWidget
from ui.conversion_dialog import ConversionDialog
from ui.history_page import HistoryPage
from ui.settings_page import SettingsPage

__all__ = [
    "MainWindow",
    "FloatingWidget",
    "ConversionDialog",
    "HistoryPage",
    "SettingsPage",
]
