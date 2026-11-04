"""
ui/main_window.py
-----------------
Main application window for FileX.
Provides a modern Windows 11 dark dashboard with sidebar navigation:
  - Dashboard: Metrics, supported formats grid, quick actions
  - Convert: Drag-and-drop zone, live conversion queue, progress cards
  - History: Complete conversion log and stats
  - Settings: Configuration and Windows integration
Also hosts the system tray icon and floating widget lifecycle.
"""

import sys
import os
from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QFont, QCursor, QColor
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QStackedWidget,
    QPushButton,
    QLabel,
    QFrame,
    QSystemTrayIcon,
    QMenu,
    QApplication,
    QScrollArea,
    QGridLayout,
)

from core.settings_manager import SettingsManager
from core.history_manager import HistoryManager
from core.conversion_manager import ConversionManager
from core.format_registry import FormatRegistry
from core.file_detector import FileDetector

from ui.components.drop_zone import DropZone
from ui.components.progress_card import ProgressCard
from ui.components.animated_button import AnimatedButton
from ui.floating_widget import FloatingWidget
from ui.conversion_dialog import ConversionDialog
from ui.history_page import HistoryPage
from ui.settings_page import SettingsPage
from utils.file_utils import human_readable_size


class MainWindow(QMainWindow):
    """
    Main application shell and dashboard for FileX.
    """

    def __init__(self, settings: SettingsManager) -> None:
        super().__init__()
        self.settings = settings
        self.history_manager = HistoryManager()
        self.conversion_manager = ConversionManager(self.settings, self.history_manager)
        self.format_registry = FormatRegistry()
        self.file_detector = FileDetector()

        self.setWindowTitle("FileX — Universal File Converter")
        self.resize(1020, 680)
        self.setMinimumSize(850, 560)

        # Active progress cards dictionary {source_path: ProgressCard}
        self.active_cards: dict[str, ProgressCard] = {}

        # Initialize Floating Widget
        self.floating_widget = FloatingWidget(self.settings)
        self.floating_widget.files_dropped.connect(self._on_files_dropped)
        self.floating_widget.open_main_window.connect(self._restore_and_show)
        self.floating_widget.request_close.connect(self._quit_application)
        self.floating_widget.show()

        # Connect ConversionManager signals to update floating widget and cards
        self.conversion_manager.conversion_started.connect(self._on_conversion_started)
        self.conversion_manager.conversion_progress.connect(self._on_conversion_progress)
        self.conversion_manager.conversion_complete.connect(self._on_conversion_complete)
        self.conversion_manager.conversion_failed.connect(self._on_conversion_failed)

        self._build_ui()
        self._setup_system_tray()

    # ----------------------------------------------------------------------
    # UI Setup
    # ----------------------------------------------------------------------
    def _build_ui(self) -> None:
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        root_layout = QHBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # 1. Left Sidebar
        sidebar = self._build_sidebar()
        root_layout.addWidget(sidebar, 0)

        # 2. Main Content Area (Stacked pages)
        self.stack = QStackedWidget(self)
        self.page_dashboard = self._build_dashboard_page()
        self.page_convert = self._build_convert_page()
        self.page_history = HistoryPage(self.history_manager, self)
        self.page_settings = SettingsPage(self.settings, self)

        # Wire settings page floating widget toggle
        self.page_settings.widget_visibility_changed.connect(self._toggle_floating_widget)

        self.stack.addWidget(self.page_dashboard)   # Index 0
        self.stack.addWidget(self.page_convert)     # Index 1
        self.stack.addWidget(self.page_history)     # Index 2
        self.stack.addWidget(self.page_settings)    # Index 3

        root_layout.addWidget(self.stack, 1)

    def _build_sidebar(self) -> QFrame:
        sidebar = QFrame(self)
        sidebar.setObjectName("sidebarFrame")
        sidebar.setFixedWidth(230)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(16, 20, 16, 20)
        layout.setSpacing(6)

        # App Logo & Branding
        brand_box = QHBoxLayout()
        brand_box.setSpacing(10)
        lbl_logo = QLabel("⚡", sidebar)
        lbl_logo.setFont(QFont("Segoe UI Emoji", 18))
        lbl_logo.setStyleSheet("color: #7c4dff;")

        lbl_title = QLabel("FileX", sidebar)
        lbl_title.setStyleSheet("font-size: 19px; font-weight: 800; color: #ffffff; letter-spacing: 0.5px;")

        lbl_badge = QLabel("PRO", sidebar)
        lbl_badge.setStyleSheet(
            "background-color: #272844; color: #a78bfa; font-size: 10px; font-weight: 700; border-radius: 4px; padding: 2px 6px;"
        )

        brand_box.addWidget(lbl_logo)
        brand_box.addWidget(lbl_title)
        brand_box.addWidget(lbl_badge)
        brand_box.addStretch()
        layout.addLayout(brand_box)
        layout.addSpacing(20)

        # Navigation Buttons
        self.nav_buttons: List[QPushButton] = []

        self.btn_nav_dashboard = self._create_nav_button("📊  Dashboard", 0)
        self.btn_nav_convert = self._create_nav_button("⚡  Convert", 1)
        self.btn_nav_history = self._create_nav_button("🕒  History", 2)
        self.btn_nav_settings = self._create_nav_button("⚙  Settings", 3)

        layout.addWidget(self.btn_nav_dashboard)
        layout.addWidget(self.btn_nav_convert)
        layout.addWidget(self.btn_nav_history)
        layout.addWidget(self.btn_nav_settings)

        layout.addStretch()

        # Floating Widget Status Pill in Sidebar
        widget_pill = QFrame(sidebar)
        widget_pill.setStyleSheet(
            "background-color: #1a1b2b; border: 1px solid #292b3e; border-radius: 10px; padding: 8px;"
        )
        pill_layout = QVBoxLayout(widget_pill)
        pill_layout.setContentsMargins(8, 8, 8, 8)
        pill_layout.setSpacing(6)

        lbl_pill_title = QLabel("Floating Widget", widget_pill)
        lbl_pill_title.setStyleSheet("font-size: 11px; font-weight: 600; color: #cbd5e1;")

        self.btn_toggle_float = QPushButton("Hide Widget", widget_pill)
        self.btn_toggle_float.setFixedHeight(28)
        self.btn_toggle_float.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_toggle_float.setStyleSheet(
            "background-color: #252840; color: #a78bfa; border: none; border-radius: 6px; font-size: 11px; font-weight: 600;"
        )
        self.btn_toggle_float.clicked.connect(self._toggle_floating_widget_button)

        pill_layout.addWidget(lbl_pill_title)
        pill_layout.addWidget(self.btn_toggle_float)
        layout.addWidget(widget_pill)

        # Highlight default page
        self._set_active_nav(0)
        return sidebar

    def _create_nav_button(self, text: str, page_index: int) -> QPushButton:
        btn = QPushButton(text, self)
        btn.setObjectName("navButton")
        btn.setCursor(QCursor(Qt.PointingHandCursor))
        btn.setFixedHeight(40)
        btn.clicked.connect(lambda: self._set_active_nav(page_index))
        self.nav_buttons.append(btn)
        return btn

    def _set_active_nav(self, index: int) -> None:
        self.stack.setCurrentIndex(index)
        for i, btn in enumerate(self.nav_buttons):
            if i == index:
                btn.setProperty("active", "true")
            else:
                btn.setProperty("active", "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        # If switching to History, trigger data refresh
        if index == 2:
            self.page_history.refresh()

    # ----------------------------------------------------------------------
    # Page 0: Dashboard Page
    # ----------------------------------------------------------------------
    def _build_dashboard_page(self) -> QWidget:
        page = QWidget(self)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(22)

        # Header Banner
        banner = QFrame(page)
        banner.setObjectName("cardFrame")
        banner.setStyleSheet(
            """
            QFrame#cardFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #221c3b, stop:1 #171b30);
                border: 1px solid #372f5c;
                border-radius: 14px;
            }
            """
        )
        banner_layout = QVBoxLayout(banner)
        banner_layout.setContentsMargins(24, 20, 24, 20)
        banner_layout.setSpacing(8)

        lbl_greeting = QLabel("Welcome to FileX", banner)
        lbl_greeting.setStyleSheet("font-size: 20px; font-weight: 800; color: #ffffff;")

        lbl_sub = QLabel(
            "Fast, offline, and modern file conversions directly from Windows Explorer.\n"
            "Drag any file onto the floating desktop widget or use the conversion tab.",
            banner,
        )
        lbl_sub.setStyleSheet("color: #cbd5e1; font-size: 13px; line-height: 1.4;")

        btn_start = AnimatedButton("Start Converting Files", banner, primary=True)
        btn_start.setFixedWidth(200)
        btn_start.clicked.connect(lambda: self._set_active_nav(1))

        banner_layout.addWidget(lbl_greeting)
        banner_layout.addWidget(lbl_sub)
        banner_layout.addSpacing(4)
        banner_layout.addWidget(btn_start)
        layout.addWidget(banner)

        # Supported Categories Grid
        lbl_cat_title = QLabel("Supported Format Categories", page)
        lbl_cat_title.setObjectName("sectionTitle")
        layout.addWidget(lbl_cat_title)

        grid = QGridLayout()
        grid.setSpacing(12)

        categories = self.format_registry.all_categories()
        for idx, cat in enumerate(categories):
            cat_card = QFrame(page)
            cat_card.setObjectName("cardFrame")
            c_layout = QVBoxLayout(cat_card)
            c_layout.setContentsMargins(14, 12, 14, 12)
            c_layout.setSpacing(4)

            icon_lbl = QLabel(cat.icon, cat_card)
            icon_lbl.setFont(QFont("Segoe UI Emoji", 20))

            name_lbl = QLabel(cat.label, cat_card)
            name_lbl.setStyleSheet("font-weight: 700; color: #f1f5f9; font-size: 14px;")

            exts = ", ".join(f.ext.upper() for f in cat.formats[:4])
            ext_lbl = QLabel(f"{exts}…", cat_card)
            ext_lbl.setStyleSheet("color: #94a3b8; font-size: 11px;")

            c_layout.addWidget(icon_lbl)
            c_layout.addWidget(name_lbl)
            c_layout.addWidget(ext_lbl)

            row = idx // 4
            col = idx % 4
            grid.addWidget(cat_card, row, col)

        layout.addLayout(grid)
        layout.addStretch()
        return page

    # ----------------------------------------------------------------------
    # Page 1: Convert Page
    # ----------------------------------------------------------------------
    def _build_convert_page(self) -> QWidget:
        page = QWidget(self)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(18)

        # Title
        title_box = QVBoxLayout()
        title_box.setSpacing(4)
        lbl_title = QLabel("Convert Files", page)
        lbl_title.setObjectName("titleLabel")

        lbl_desc = QLabel(
            "Drag & drop any supported file from File Explorer or browse from your computer.",
            page,
        )
        lbl_desc.setObjectName("subtitleLabel")

        title_box.addWidget(lbl_title)
        title_box.addWidget(lbl_desc)
        layout.addLayout(title_box)

        # Native Drop Zone
        self.drop_zone = DropZone(page)
        self.drop_zone.files_dropped.connect(self._on_files_dropped)
        layout.addWidget(self.drop_zone)

        # Conversion Tasks Queue Header
        queue_header = QHBoxLayout()
        lbl_queue = QLabel("Active & Recent Conversions", page)
        lbl_queue.setObjectName("sectionTitle")
        queue_header.addWidget(lbl_queue)
        queue_header.addStretch()
        layout.addLayout(queue_header)

        # Scroll area for ProgressCards
        scroll = QScrollArea(page)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(10)
        self.cards_layout.addStretch()

        scroll.setWidget(self.cards_container)
        layout.addWidget(scroll, 1)

        return page

    # ----------------------------------------------------------------------
    # System Tray Integration
    # ----------------------------------------------------------------------
    def _setup_system_tray(self) -> None:
        self.tray_icon = QSystemTrayIcon(self)
        icon_path = Path(__file__).resolve().parent.parent / "assets" / "images" / "logo.png"
        if icon_path.exists():
            self.tray_icon.setIcon(QIcon(str(icon_path)))
        else:
            self.tray_icon.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_DriveHDIcon))

        tray_menu = QMenu()
        tray_menu.setStyleSheet(
            """
            QMenu {
                background-color: #1a1b2b;
                border: 1px solid #32354f;
                border-radius: 8px;
                padding: 6px;
                color: #f1f5f9;
            }
            QMenu::item:selected {
                background-color: #7c4dff;
            }
            """
        )

        act_show = tray_menu.addAction("📊 Open FileX Dashboard")
        act_show.triggered.connect(self._restore_and_show)

        act_float = tray_menu.addAction("⚡ Show/Hide Floating Widget")
        act_float.triggered.connect(self._toggle_floating_widget_button)

        tray_menu.addSeparator()

        act_exit = tray_menu.addAction("🚪 Exit")
        act_exit.triggered.connect(self._quit_application)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.show()

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.Trigger:
            self._restore_and_show()

    def _restore_and_show(self) -> None:
        self.showNormal()
        self.activateWindow()

    # ----------------------------------------------------------------------
    # Floating Widget Controls
    # ----------------------------------------------------------------------
    def _toggle_floating_widget(self, show: bool) -> None:
        if show:
            self.floating_widget.show()
            self.btn_toggle_float.setText("Hide Widget")
        else:
            self.floating_widget.hide()
            self.btn_toggle_float.setText("Show Widget")

    def _toggle_floating_widget_button(self) -> None:
        is_visible = self.floating_widget.isVisible()
        self._toggle_floating_widget(not is_visible)
        self.page_settings.chk_widget_visible.setChecked(not is_visible)

    # ----------------------------------------------------------------------
    # Conversion Workflow Handlers
    # ----------------------------------------------------------------------
    def _on_files_dropped(self, paths: List[str]) -> None:
        """Invoked when files are dropped onto FloatingWidget or DropZone."""
        if not paths:
            return

        # Open Conversion Dialog
        dialog = ConversionDialog(
            files=paths,
            conversion_manager=self.conversion_manager,
            settings=self.settings,
            parent=self,
        )
        dialog.exec()

    def _on_conversion_started(self, source_path: str, target_format: str) -> None:
        # Update floating widget to processing state
        self.floating_widget.set_processing(10, "Converting…")

        # Create or update progress card in Convert page queue
        ext, category, _ = self.file_detector.detect(source_path)
        icon_map = {
            "image": "🖼️",
            "pdf": "📄",
            "document": "📝",
            "spreadsheet": "📊",
            "presentation": "📽️",
            "audio": "🎵",
            "video": "🎬",
        }
        icon = icon_map.get(category, "📁")

        card = ProgressCard(source_path, target_format, icon, self.cards_container)
        card.set_progress(10)
        self.active_cards[source_path] = card
        # Insert card at top of stack (before the stretch item)
        self.cards_layout.insertWidget(0, card)

    def _on_conversion_progress(self, source_path: str, percent: int) -> None:
        self.floating_widget.set_processing(percent)
        if source_path in self.active_cards:
            self.active_cards[source_path].set_progress(percent)

    def _on_conversion_complete(self, source_path: str, output_path: str) -> None:
        self.floating_widget.set_idle()
        if source_path in self.active_cards:
            self.active_cards[source_path].set_completed(output_path)

        # Refresh history
        self.page_history.refresh()

    def _on_conversion_failed(self, source_path: str, error_msg: str) -> None:
        self.floating_widget.set_idle()
        if source_path in self.active_cards:
            self.active_cards[source_path].set_failed(error_msg)

    # ----------------------------------------------------------------------
    # Clean Exit Handling
    # ----------------------------------------------------------------------
    def closeEvent(self, event) -> None:
        """When main window is closed, minimize to tray and keep floating widget alive."""
        event.ignore()
        self.hide()
        if self.tray_icon.isVisible():
            self.tray_icon.showMessage(
                "FileX is running in background",
                "The floating widget and tray icon are still active. Right-click the tray icon to exit.",
                QSystemTrayIcon.Information,
                2000,
            )

    def _quit_application(self) -> None:
        """Terminate all background tasks, close windows, and exit."""
        self.floating_widget.close()
        self.tray_icon.hide()
        QApplication.quit()
