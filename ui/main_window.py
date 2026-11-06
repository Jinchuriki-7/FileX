"""
ui/main_window.py
-----------------
Main application window for FileX with:
  - Custom frameless dark title bar with window controls & dragging
  - Sleek modern sidebar navigation with Lucide vector icons
  - Premium Dashboard (Gradient hero card, statistics, format category grid, quick actions)
  - Convert Page (DropZone & live progress cards)
  - History & Settings Pages
  - Standalone, independent floating widget lifecycle and tray icon
"""

import sys
import os
from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QFont, QCursor, QColor, QPainter, QLinearGradient
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
    QSizeGrip,
)

from core.settings_manager import SettingsManager
from core.history_manager import HistoryManager
from core.conversion_manager import ConversionManager
from core.format_registry import FormatRegistry
from core.file_detector import FileDetector

from ui.components.drop_zone import DropZone
from ui.components.progress_card import ProgressCard
from ui.components.title_bar import CustomTitleBar
from ui.floating_widget import FloatingWidget
from ui.conversion_dialog import ConversionDialog
from ui.history_page import HistoryPage
from ui.settings_page import SettingsPage
from utils.file_utils import human_readable_size
from utils.icon_utils import get_svg_icon, get_svg_pixmap


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

        # Frameless Window with Custom Dark Title Bar
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground, False)

        self.setWindowTitle("FileX — Universal File Converter")
        self.resize(1080, 720)
        self.setMinimumSize(880, 600)

        # Center on screen on first launch
        screen = QApplication.primaryScreen()
        if screen:
            screen_geo = screen.availableGeometry()
            self.move(
                (screen_geo.width() - self.width()) // 2,
                (screen_geo.height() - self.height()) // 2,
            )

        # Active progress cards dictionary {source_path: ProgressCard}
        self.active_cards: dict[str, ProgressCard] = {}

        # Initialize Floating Widget as independent top-level window (None parent)
        self.floating_widget = FloatingWidget(self.settings, parent=None)
        self.floating_widget.files_dropped.connect(self._on_files_dropped)
        self.floating_widget.open_main_window.connect(self._restore_and_show)
        self.floating_widget.request_close.connect(self._quit_application)

        if self.settings.get("show_floating_widget", True):
            self.floating_widget.show()

        # Connect ConversionManager signals
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
        central_widget.setObjectName("centralWidget")
        central_widget.setStyleSheet(
            """
            QWidget#centralWidget {
                background-color: #0B0D14;
                border: 1px solid #1D2030;
            }
            """
        )
        self.setCentralWidget(central_widget)

        root_vbox = QVBoxLayout(central_widget)
        root_vbox.setContentsMargins(0, 0, 0, 0)
        root_vbox.setSpacing(0)

        # 1. Custom Dark Title Bar
        self.title_bar = CustomTitleBar(self)
        root_vbox.addWidget(self.title_bar, 0)

        # 2. Main Content Split: Sidebar + Page Container
        body_widget = QWidget(central_widget)
        body_layout = QHBoxLayout(body_widget)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        # 2a. Left Sidebar
        sidebar = self._build_sidebar()
        body_layout.addWidget(sidebar, 0)

        # 2b. Main Pages Stack
        self.stack = QStackedWidget(body_widget)
        self.stack.setStyleSheet("background-color: #0F111A;")

        self.page_dashboard = self._build_dashboard_page()
        self.page_convert = self._build_convert_page()
        self.page_history = HistoryPage(self.history_manager, self)
        self.page_settings = SettingsPage(self.settings, self)

        self.page_settings.widget_visibility_changed.connect(self._toggle_floating_widget)

        self.stack.addWidget(self.page_dashboard)   # Index 0
        self.stack.addWidget(self.page_convert)     # Index 1
        self.stack.addWidget(self.page_history)     # Index 2
        self.stack.addWidget(self.page_settings)    # Index 3

        body_layout.addWidget(self.stack, 1)
        root_vbox.addWidget(body_widget, 1)

        # 3. Bottom Size Grip for Frameless Resizing
        grip_box = QHBoxLayout()
        grip_box.setContentsMargins(0, 0, 2, 2)
        grip_box.addStretch()
        size_grip = QSizeGrip(central_widget)
        size_grip.setStyleSheet("width: 14px; height: 14px; background: transparent;")
        grip_box.addWidget(size_grip)
        root_vbox.addLayout(grip_box)

        # Highlight default page
        self._set_active_nav(0)

    def _build_sidebar(self) -> QFrame:
        sidebar = QFrame(self)
        sidebar.setObjectName("sidebarFrame")
        sidebar.setFixedWidth(224)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(14, 18, 14, 16)
        layout.setSpacing(6)

        # App Logo & Branding
        brand_box = QHBoxLayout()
        brand_box.setSpacing(10)

        lbl_logo = QLabel(sidebar)
        lbl_logo.setPixmap(get_svg_pixmap("zap", "#8957FF", 22))

        title_vbox = QVBoxLayout()
        title_vbox.setSpacing(1)

        title_row = QHBoxLayout()
        title_row.setSpacing(6)
        lbl_title = QLabel("FileX", sidebar)
        lbl_title.setStyleSheet("font-size: 17px; font-weight: 800; color: #FFFFFF; letter-spacing: 0.4px;")

        lbl_badge = QLabel("PRO", sidebar)
        lbl_badge.setStyleSheet(
            "background-color: #1D2030; color: #A78BFA; font-size: 10px; font-weight: 700; border-radius: 4px; padding: 1px 5px; border: 1px solid #292D40;"
        )
        title_row.addWidget(lbl_title)
        title_row.addWidget(lbl_badge)
        title_row.addStretch()

        lbl_sub = QLabel("Universal Converter", sidebar)
        lbl_sub.setStyleSheet("color: #687087; font-size: 11px; font-weight: 500;")

        title_vbox.addLayout(title_row)
        title_vbox.addWidget(lbl_sub)

        brand_box.addWidget(lbl_logo)
        brand_box.addLayout(title_vbox, 1)
        layout.addLayout(brand_box)

        layout.addSpacing(18)

        # Navigation Buttons with Lucide Icons
        self.nav_buttons: List[QPushButton] = []

        self.btn_nav_dashboard = self._create_nav_button("dashboard", "Dashboard", 0)
        self.btn_nav_convert = self._create_nav_button("zap", "Convert Files", 1)
        self.btn_nav_history = self._create_nav_button("history", "History", 2)
        self.btn_nav_settings = self._create_nav_button("settings", "Settings", 3)

        layout.addWidget(self.btn_nav_dashboard)
        layout.addWidget(self.btn_nav_convert)
        layout.addWidget(self.btn_nav_history)
        layout.addWidget(self.btn_nav_settings)

        layout.addStretch()

        # Floating Widget Status Pill at Bottom of Sidebar
        widget_pill = QFrame(sidebar)
        widget_pill.setStyleSheet(
            """
            QFrame {
                background-color: #171A27;
                border: 1px solid #292D40;
                border-radius: 8px;
                padding: 6px;
            }
            """
        )
        pill_layout = QVBoxLayout(widget_pill)
        pill_layout.setContentsMargins(8, 8, 8, 8)
        pill_layout.setSpacing(6)

        header_row = QHBoxLayout()
        header_row.setSpacing(6)
        lbl_dot = QLabel("•", widget_pill)
        lbl_dot.setStyleSheet("color: #22C55E; font-size: 16px; font-weight: bold;")
        lbl_pill_title = QLabel("Floating Widget", widget_pill)
        lbl_pill_title.setStyleSheet("font-size: 11px; font-weight: 600; color: #F5F5FA;")
        header_row.addWidget(lbl_dot)
        header_row.addWidget(lbl_pill_title)
        header_row.addStretch()

        self.btn_toggle_float = QPushButton("Hide Widget", widget_pill)
        self.btn_toggle_float.setFixedHeight(26)
        self.btn_toggle_float.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_toggle_float.setStyleSheet(
            """
            QPushButton {
                background-color: #1D2030;
                color: #A78BFA;
                border: 1px solid #292D40;
                border-radius: 5px;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #25293D;
                color: #FFFFFF;
                border-color: #8957FF;
            }
            """
        )
        self.btn_toggle_float.clicked.connect(self._toggle_floating_widget_button)

        pill_layout.addLayout(header_row)
        pill_layout.addWidget(self.btn_toggle_float)
        layout.addWidget(widget_pill)

        # Version footer
        lbl_version = QLabel("v1.0.0 • Offline Ready", sidebar)
        lbl_version.setAlignment(Qt.AlignCenter)
        lbl_version.setStyleSheet("color: #687087; font-size: 10px; margin-top: 4px;")
        layout.addWidget(lbl_version)

        return sidebar

    def _create_nav_button(self, icon_name: str, text: str, page_index: int) -> QPushButton:
        btn = QPushButton(text, self)
        btn.setObjectName("navButton")
        btn.setIcon(get_svg_icon(icon_name, "#9CA3B8", 16))
        btn.setIconSize(QSize(16, 16))
        btn.setCursor(QCursor(Qt.PointingHandCursor))
        btn.setFixedHeight(38)
        btn.clicked.connect(lambda: self._set_active_nav(page_index))
        btn.icon_name = icon_name
        self.nav_buttons.append(btn)
        return btn

    def _set_active_nav(self, index: int) -> None:
        self.stack.setCurrentIndex(index)
        for i, btn in enumerate(self.nav_buttons):
            if i == index:
                btn.setProperty("active", "true")
                btn.setIcon(get_svg_icon(btn.icon_name, "#8957FF", 16))
            else:
                btn.setProperty("active", "false")
                btn.setIcon(get_svg_icon(btn.icon_name, "#9CA3B8", 16))
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        if index == 2:
            self.page_history.refresh()
        elif index == 0:
            self._update_dashboard_metrics()

    # ----------------------------------------------------------------------
    # Page 0: Premium Dashboard
    # ----------------------------------------------------------------------
    def _build_dashboard_page(self) -> QWidget:
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 24, 28, 28)
        layout.setSpacing(20)

        # 1. Top Header greeting
        header_layout = QVBoxLayout()
        header_layout.setSpacing(2)

        lbl_welcome = QLabel("Welcome back to FileX", page)
        lbl_welcome.setStyleSheet("font-size: 20px; font-weight: 800; color: #F5F5FA;")

        lbl_sub = QLabel("Your files, converted effortlessly directly on your device.", page)
        lbl_sub.setStyleSheet("color: #9CA3B8; font-size: 13px;")

        header_layout.addWidget(lbl_welcome)
        header_layout.addWidget(lbl_sub)
        layout.addLayout(header_layout)

        # 2. Main Hero Section — Elegant Linear Gradient Card
        hero_card = QFrame(page)
        hero_card.setObjectName("heroCard")
        hero_card.setStyleSheet(
            """
            QFrame#heroCard {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1A1035, stop:0.6 #131526, stop:1 #0F111E);
                border: 1px solid #292D40;
                border-radius: 12px;
            }
            """
        )
        hero_layout = QHBoxLayout(hero_card)
        hero_layout.setContentsMargins(24, 22, 24, 22)
        hero_layout.setSpacing(20)

        left_hero = QVBoxLayout()
        left_hero.setSpacing(8)

        lbl_hero_title = QLabel("Convert anything. Keep everything local.", hero_card)
        lbl_hero_title.setStyleSheet("font-size: 18px; font-weight: 700; color: #F5F5FA;")

        lbl_hero_desc = QLabel(
            "Fast, private and powerful file conversion engine with zero cloud dependency.\n"
            "Drag any file onto the floating widget or start a conversion below.",
            hero_card,
        )
        lbl_hero_desc.setStyleSheet("color: #9CA3B8; font-size: 12px; line-height: 1.4;")

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        btn_start = QPushButton("Start Converting", hero_card)
        btn_start.setObjectName("primaryButton")
        btn_start.setIcon(get_svg_icon("zap", "#FFFFFF", 14))
        btn_start.setCursor(QCursor(Qt.PointingHandCursor))
        btn_start.setFixedHeight(34)
        btn_start.clicked.connect(lambda: self._set_active_nav(1))

        btn_history = QPushButton("View History", hero_card)
        btn_history.setObjectName("secondaryButton")
        btn_history.setIcon(get_svg_icon("history", "#F5F5FA", 14))
        btn_history.setCursor(QCursor(Qt.PointingHandCursor))
        btn_history.setFixedHeight(34)
        btn_history.clicked.connect(lambda: self._set_active_nav(2))

        btn_row.addWidget(btn_start)
        btn_row.addWidget(btn_history)
        btn_row.addStretch()

        left_hero.addWidget(lbl_hero_title)
        left_hero.addWidget(lbl_hero_desc)
        left_hero.addSpacing(4)
        left_hero.addLayout(btn_row)

        hero_layout.addLayout(left_hero, 1)

        # Right hero illustration
        lbl_hero_icon = QLabel(hero_card)
        lbl_hero_icon.setPixmap(get_svg_pixmap("zap", "#8957FF", 64))
        lbl_hero_icon.setAlignment(Qt.AlignCenter)
        hero_layout.addWidget(lbl_hero_icon)

        layout.addWidget(hero_card)

        # 3. Statistics Cards Row
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(14)

        self.dash_total = self._create_stat_card("trending-up", "TOTAL CONVERSIONS", "0", "#8957FF")
        self.dash_success = self._create_stat_card("check-circle", "SUCCESSFUL", "0", "#22C55E")
        self.dash_volume = self._create_stat_card("activity", "DATA PROCESSED", "0 MB", "#38BDF8")

        stats_layout.addWidget(self.dash_total)
        stats_layout.addWidget(self.dash_success)
        stats_layout.addWidget(self.dash_volume)
        layout.addLayout(stats_layout)

        # 4. Supported Categories Section
        lbl_cat_title = QLabel("Supported Format Categories", page)
        lbl_cat_title.setObjectName("sectionTitle")
        layout.addWidget(lbl_cat_title)

        grid = QGridLayout()
        grid.setSpacing(12)

        categories = self.format_registry.all_categories()
        cat_badge_map = {
            "image": ["PNG", "JPG", "WEBP", "GIF"],
            "pdf": ["PDF", "TXT", "DOCX", "PNG"],
            "document": ["DOCX", "TXT", "MD", "HTML"],
            "spreadsheet": ["XLSX", "CSV", "ODS"],
            "presentation": ["PPTX", "PDF"],
            "audio": ["MP3", "WAV", "FLAC", "AAC"],
            "video": ["MP4", "MKV", "AVI", "WEBM"],
        }

        for idx, cat in enumerate(categories):
            cat_card = QFrame(page)
            cat_card.setObjectName("cardFrame")
            cat_card.setCursor(QCursor(Qt.PointingHandCursor))
            cat_card.setStyleSheet(
                """
                QFrame#cardFrame {
                    background-color: #171A27;
                    border: 1px solid #292D40;
                    border-radius: 10px;
                }
                QFrame#cardFrame:hover {
                    border: 1px solid #8957FF;
                    background-color: #1D2030;
                }
                """
            )
            c_layout = QVBoxLayout(cat_card)
            c_layout.setContentsMargins(14, 14, 14, 14)
            c_layout.setSpacing(6)

            top_row = QHBoxLayout()
            top_row.setSpacing(8)

            icon_lbl = QLabel(cat_card)
            icon_lbl.setPixmap(get_svg_pixmap(cat.icon, "#8957FF", 20))

            name_lbl = QLabel(cat.label, cat_card)
            name_lbl.setStyleSheet("font-weight: 700; color: #F5F5FA; font-size: 13px;")

            top_row.addWidget(icon_lbl)
            top_row.addWidget(name_lbl)
            top_row.addStretch()

            badges = cat_badge_map.get(cat.name, [f.ext.upper() for f in cat.formats[:4]])
            exts_str = "  •  ".join(badges)
            ext_lbl = QLabel(exts_str, cat_card)
            ext_lbl.setStyleSheet("color: #9CA3B8; font-size: 11px;")

            c_layout.addLayout(top_row)
            c_layout.addWidget(ext_lbl)

            # Clicking a category switches to convert page
            cat_card.mousePressEvent = lambda event: self._set_active_nav(1)

            row = idx // 4
            col = idx % 4
            grid.addWidget(cat_card, row, col)

        layout.addLayout(grid)

        # 5. Quick Actions Section (fills space intelligently)
        quick_card = QFrame(page)
        quick_card.setObjectName("cardFrame")
        quick_card.setStyleSheet(
            """
            QFrame#cardFrame {
                background-color: #171A27;
                border: 1px solid #292D40;
                border-radius: 10px;
            }
            """
        )
        q_layout = QHBoxLayout(quick_card)
        q_layout.setContentsMargins(16, 14, 16, 14)
        q_layout.setSpacing(14)

        q_info = QVBoxLayout()
        q_info.setSpacing(2)
        lbl_q_title = QLabel("Fast Drag-and-Drop Floating Mode", quick_card)
        lbl_q_title.setStyleSheet("font-size: 13px; font-weight: 700; color: #F5F5FA;")

        lbl_q_sub = QLabel("You don't need to keep FileX open. Minimize this window anytime; the floating widget will stay ready on your desktop.", quick_card)
        lbl_q_sub.setStyleSheet("font-size: 11px; color: #9CA3B8;")

        q_info.addWidget(lbl_q_title)
        q_info.addWidget(lbl_q_sub)
        q_layout.addLayout(q_info, 1)

        btn_to_tray = QPushButton("Minimize to Tray", quick_card)
        btn_to_tray.setObjectName("secondaryButton")
        btn_to_tray.setIcon(get_svg_icon("minimize", "#9CA3B8", 12))
        btn_to_tray.setFixedHeight(30)
        btn_to_tray.setCursor(QCursor(Qt.PointingHandCursor))
        btn_to_tray.clicked.connect(self.hide)
        q_layout.addWidget(btn_to_tray)

        layout.addWidget(quick_card)

        layout.addStretch()
        scroll.setWidget(page)
        return scroll

    def _create_stat_card(self, icon_name: str, label: str, value: str, accent: str) -> QFrame:
        card = QFrame(self)
        card.setObjectName("cardFrame")
        card.setStyleSheet(
            """
            QFrame#cardFrame {
                background-color: #171A27;
                border: 1px solid #292D40;
                border-radius: 10px;
            }
            """
        )
        layout = QHBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(14)

        icon_lbl = QLabel(card)
        icon_lbl.setPixmap(get_svg_pixmap(icon_name, accent, 24))
        layout.addWidget(icon_lbl)

        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)

        lbl_val = QLabel(value, card)
        lbl_val.setObjectName("metricValue")
        lbl_val.setStyleSheet(f"color: {accent}; font-size: 26px; font-weight: 800;")

        lbl_desc = QLabel(label, card)
        lbl_desc.setObjectName("metricLabel")

        info_layout.addWidget(lbl_val)
        info_layout.addWidget(lbl_desc)
        layout.addLayout(info_layout, 1)

        card.lbl_val = lbl_val
        return card

    def _update_dashboard_metrics(self) -> None:
        stats = self.history_manager.stats()
        total = stats.get("total", 0)
        success = stats.get("success_count", 0)
        bytes_in = stats.get("bytes_in", 0)

        self.dash_total.lbl_val.setText(str(total))
        self.dash_success.lbl_val.setText(str(success))
        self.dash_volume.lbl_val.setText(human_readable_size(bytes_in))

    # ----------------------------------------------------------------------
    # Page 1: Convert Page
    # ----------------------------------------------------------------------
    def _build_convert_page(self) -> QWidget:
        page = QWidget(self)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 24, 28, 28)
        layout.setSpacing(16)

        # Title
        title_box = QVBoxLayout()
        title_box.setSpacing(2)
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
        base_dir = Path(sys._MEIPASS) if getattr(sys, "frozen", False) else Path(__file__).resolve().parent.parent
        icon_path = base_dir / "assets" / "images" / "logo.png"
        if icon_path.exists():
            self.tray_icon.setIcon(QIcon(str(icon_path)))
        else:
            self.tray_icon.setIcon(get_svg_icon("zap", "#8957FF", 16))

        tray_menu = QMenu()
        tray_menu.setStyleSheet(
            """
            QMenu {
                background-color: #171A27;
                border: 1px solid #292D40;
                border-radius: 8px;
                padding: 6px;
                color: #F5F5FA;
            }
            QMenu::item:selected {
                background-color: #8957FF;
            }
            """
        )

        act_show = tray_menu.addAction(get_svg_icon("dashboard", "#8957FF", 14), "Open FileX Dashboard")
        act_show.triggered.connect(self._restore_and_show)

        act_float = tray_menu.addAction(get_svg_icon("zap", "#A78BFA", 14), "Show/Hide Floating Widget")
        act_float.triggered.connect(self._toggle_floating_widget_button)

        tray_menu.addSeparator()

        act_exit = tray_menu.addAction("Exit FileX")
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

        dialog = ConversionDialog(
            files=paths,
            conversion_manager=self.conversion_manager,
            settings=self.settings,
            parent=self,
        )
        dialog.exec()

    def _on_conversion_started(self, source_path: str, target_format: str) -> None:
        self.floating_widget.set_processing(10, "Converting…")

        ext, category, _ = self.file_detector.detect(source_path)
        cat_icon = category if category in ["image", "pdf", "file-text", "table", "presentation", "music", "video"] else "file-text"

        card = ProgressCard(source_path, target_format, cat_icon, self.cards_container)
        card.set_progress(10)
        self.active_cards[source_path] = card
        self.cards_layout.insertWidget(0, card)

    def _on_conversion_progress(self, source_path: str, percent: int) -> None:
        self.floating_widget.set_processing(percent)
        if source_path in self.active_cards:
            self.active_cards[source_path].set_progress(percent)

    def _on_conversion_complete(self, source_path: str, output_path: str) -> None:
        self.floating_widget.set_idle()
        if source_path in self.active_cards:
            self.active_cards[source_path].set_completed(output_path)

        self.page_history.refresh()
        self._update_dashboard_metrics()

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
