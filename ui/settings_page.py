"""
ui/settings_page.py
-------------------
Settings dashboard view for configuring conversion preferences, floating widget
behavior, system startup integration, notifications, and output directories.
"""

import shutil
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QCheckBox,
    QLineEdit,
    QPushButton,
    QFileDialog,
    QSlider,
    QSpinBox,
    QFrame,
    QScrollArea,
    QMessageBox,
)

from core.settings_manager import SettingsManager
from utils.windows_utils import add_to_startup, remove_from_startup, is_in_startup
from utils.icon_utils import get_svg_icon, get_svg_pixmap


class SettingsPage(QWidget):
    """
    Application Settings configuration page.

    Signals:
        widget_visibility_changed(bool): Emitted when floating widget toggle changes.
        theme_changed(str): Emitted when UI theme selection changes.
    """

    widget_visibility_changed = Signal(bool)
    theme_changed = Signal(str)

    def __init__(
        self,
        settings: SettingsManager,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.settings = settings

        self._build_ui()
        self._load_values()

    # ----------------------------------------------------------------------
    # UI Setup
    # ----------------------------------------------------------------------
    def _build_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)

        # Scroll Area for responsive settings list
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        content = QWidget()
        self.layout = QVBoxLayout(content)
        self.layout.setContentsMargins(28, 24, 28, 28)
        self.layout.setSpacing(18)

        # Page Header
        header_box = QVBoxLayout()
        header_box.setSpacing(4)
        lbl_title = QLabel("Settings & Preferences", content)
        lbl_title.setObjectName("titleLabel")

        lbl_desc = QLabel(
            "Configure floating widget behavior, Windows startup, and file output rules.",
            content,
        )
        lbl_desc.setObjectName("subtitleLabel")

        header_box.addWidget(lbl_title)
        header_box.addWidget(lbl_desc)
        self.layout.addLayout(header_box)

        # Section 1: Floating Widget
        self.layout.addWidget(self._build_widget_section(content))

        # Section 2: Conversion & Output
        self.layout.addWidget(self._build_output_section(content))

        # Section 3: Windows & System Integration
        self.layout.addWidget(self._build_system_section(content))

        # Section 4: Engine Status (FFmpeg & LibreOffice)
        self.layout.addWidget(self._build_engine_section(content))

        # Section 5: About FileX
        self.layout.addWidget(self._build_about_section(content))

        self.layout.addStretch()
        scroll.setWidget(content)
        root_layout.addWidget(scroll)

    def _create_card(self, title: str, parent: QWidget) -> tuple[QFrame, QVBoxLayout]:
        card = QFrame(parent)
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
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 16, 20, 16)
        card_layout.setSpacing(12)

        lbl_section = QLabel(title, card)
        lbl_section.setObjectName("sectionTitle")
        card_layout.addWidget(lbl_section)

        return card, card_layout

    # ----------------------------------------------------------------------
    # Section Builders
    # ----------------------------------------------------------------------
    def _build_widget_section(self, parent: QWidget) -> QFrame:
        card, layout = self._create_card("Floating Desktop Widget", parent)

        # Toggle widget visible
        self.chk_widget_visible = QCheckBox("Show Floating Widget on desktop", card)
        self.chk_widget_visible.setChecked(True)
        self.chk_widget_visible.toggled.connect(self._on_widget_visible_toggled)
        layout.addWidget(self.chk_widget_visible)

        # Always on top
        self.chk_always_top = QCheckBox("Always on top (floats above other windows)", card)
        self.chk_always_top.toggled.connect(
            lambda v: self.settings.set("always_on_top", v)
        )
        layout.addWidget(self.chk_always_top)

        # Widget Opacity Slider
        opacity_box = QHBoxLayout()
        lbl_op = QLabel("Widget Opacity:", card)
        lbl_op.setStyleSheet("color: #9CA3B8;")
        self.slider_opacity = QSlider(Qt.Horizontal, card)
        self.slider_opacity.setRange(40, 100)
        self.slider_opacity.setValue(95)
        self.lbl_opacity_val = QLabel("95%", card)
        self.lbl_opacity_val.setFixedWidth(40)
        self.lbl_opacity_val.setStyleSheet("color: #8957FF; font-weight: 700;")
        self.slider_opacity.valueChanged.connect(self._on_opacity_changed)

        opacity_box.addWidget(lbl_op)
        opacity_box.addWidget(self.slider_opacity, 1)
        opacity_box.addWidget(self.lbl_opacity_val)
        layout.addLayout(opacity_box)

        return card

    def _build_output_section(self, parent: QWidget) -> QFrame:
        card, layout = self._create_card("Output & File Rules", parent)

        # Output Directory
        dir_label = QLabel("Default Output Directory:", card)
        dir_label.setStyleSheet("color: #9CA3B8; font-size: 12px;")
        layout.addWidget(dir_label)

        dir_box = QHBoxLayout()
        self.txt_out_dir = QLineEdit(card)
        self.txt_out_dir.setReadOnly(True)

        btn_browse = QPushButton("Browse…", card)
        btn_browse.setIcon(get_svg_icon("folder-open", "#F5F5FA", 14))
        btn_browse.setCursor(QCursor(Qt.PointingHandCursor))
        btn_browse.clicked.connect(self._browse_dir)

        dir_box.addWidget(self.txt_out_dir, 1)
        dir_box.addWidget(btn_browse)
        layout.addLayout(dir_box)

        # Options checkboxes
        self.chk_open_after = QCheckBox("Open folder automatically after conversion finishes", card)
        self.chk_open_after.toggled.connect(
            lambda v: self.settings.set("open_output_after_conversion", v)
        )
        layout.addWidget(self.chk_open_after)

        self.chk_overwrite = QCheckBox("Overwrite existing files without renaming", card)
        self.chk_overwrite.toggled.connect(
            lambda v: self.settings.set("overwrite_existing", v)
        )
        layout.addWidget(self.chk_overwrite)

        return card

    def _build_system_section(self, parent: QWidget) -> QFrame:
        card, layout = self._create_card("System & Windows Integration", parent)

        # Start with Windows
        self.chk_startup = QCheckBox("Start FileX automatically with Windows", card)
        self.chk_startup.toggled.connect(self._on_startup_toggled)
        layout.addWidget(self.chk_startup)

        # Show Notifications
        self.chk_notifications = QCheckBox("Show Windows desktop notifications when conversion finishes", card)
        self.chk_notifications.toggled.connect(
            lambda v: self.settings.set("show_notifications", v)
        )
        layout.addWidget(self.chk_notifications)

        # Start minimized
        self.chk_minimized = QCheckBox("Start minimized to System Tray", card)
        self.chk_minimized.toggled.connect(
            lambda v: self.settings.set("start_minimised", v)
        )
        layout.addWidget(self.chk_minimized)

        # Max History Entries
        history_box = QHBoxLayout()
        lbl_hist = QLabel("Max history records to retain:", card)
        lbl_hist.setStyleSheet("color: #9CA3B8;")
        self.spin_history = QSpinBox(card)
        self.spin_history.setRange(50, 5000)
        self.spin_history.setSingleStep(50)
        self.spin_history.setValue(500)
        self.spin_history.valueChanged.connect(
            lambda v: self.settings.set("max_history_entries", v)
        )

        history_box.addWidget(lbl_hist)
        history_box.addWidget(self.spin_history)
        history_box.addStretch()
        layout.addLayout(history_box)

        return card

    def _build_engine_section(self, parent: QWidget) -> QFrame:
        card, layout = self._create_card("Conversion Engines Status", parent)

        # Check FFmpeg
        ffmpeg_found = shutil.which("ffmpeg") is not None or Path("bin/ffmpeg.exe").exists()
        lbl_ffmpeg = QLabel(
            f"FFmpeg (Audio / Video): {'✓ Ready & Accelerated' if ffmpeg_found else '⚠ Missing from PATH'}",
            card,
        )
        lbl_ffmpeg.setStyleSheet(
            f"color: {'#22C55E' if ffmpeg_found else '#EF4444'}; font-weight: 600; font-size: 12px;"
        )
        layout.addWidget(lbl_ffmpeg)

        # Check LibreOffice
        lo_found = (
            shutil.which("soffice") is not None
            or shutil.which("libreoffice") is not None
            or Path(r"C:\Program Files\LibreOffice\program\soffice.exe").exists()
        )
        lbl_lo = QLabel(
            f"Office Engine (DOCX/PPTX to PDF): {'✓ Detected' if lo_found else 'ℹ Optional (Native PyMuPDF & docx active)'}",
            card,
        )
        lbl_lo.setStyleSheet(
            f"color: {'#22C55E' if lo_found else '#9CA3B8'}; font-weight: 500; font-size: 12px;"
        )
        layout.addWidget(lbl_lo)

        return card

    def _build_about_section(self, parent: QWidget) -> QFrame:
        card, layout = self._create_card("About FileX", parent)

        about_box = QHBoxLayout()
        about_box.setSpacing(14)

        logo_lbl = QLabel(card)
        logo_lbl.setPixmap(get_svg_pixmap("zap", "#8957FF", 32))
        about_box.addWidget(logo_lbl)

        info_layout = QVBoxLayout()
        info_layout.setSpacing(3)

        title_lbl = QLabel("FileX v1.0.0 — Universal File Converter", card)
        title_lbl.setStyleSheet("color: #F5F5FA; font-weight: 700; font-size: 14px;")

        desc_lbl = QLabel(
            "Commercial-grade desktop conversion engine. 100% offline & local processing.\n"
            "GitHub Repository: https://github.com/Jinchuriki-7/FileX",
            card,
        )
        desc_lbl.setStyleSheet("color: #9CA3B8; font-size: 11px;")

        info_layout.addWidget(title_lbl)
        info_layout.addWidget(desc_lbl)
        about_box.addLayout(info_layout, 1)

        layout.addLayout(about_box)
        return card

    # ----------------------------------------------------------------------
    # Loaders & Events
    # ----------------------------------------------------------------------
    def _load_values(self) -> None:
        self.chk_always_top.setChecked(self.settings.get("always_on_top", True))
        self.chk_open_after.setChecked(
            self.settings.get("open_output_after_conversion", False)
        )
        self.chk_overwrite.setChecked(self.settings.get("overwrite_existing", False))
        self.chk_notifications.setChecked(
            self.settings.get("show_notifications", True)
        )
        self.chk_minimized.setChecked(self.settings.get("start_minimised", False))
        self.txt_out_dir.setText(self.settings.output_folder)

        op = int(self.settings.get("widget_opacity", 0.95) * 100)
        self.slider_opacity.setValue(op)
        self.lbl_opacity_val.setText(f"{op}%")

        self.spin_history.setValue(self.settings.get("max_history_entries", 500))

        try:
            self.chk_startup.setChecked(is_in_startup())
        except Exception:
            pass

    def _browse_dir(self) -> None:
        dir_path = QFileDialog.getExistingDirectory(
            self, "Select Output Directory", self.settings.output_folder
        )
        if dir_path:
            self.settings.set("output_folder", dir_path)
            self.txt_out_dir.setText(dir_path)

    def _on_opacity_changed(self, val: int) -> None:
        self.lbl_opacity_val.setText(f"{val}%")
        self.settings.set("widget_opacity", val / 100.0)

    def _on_widget_visible_toggled(self, checked: bool) -> None:
        self.widget_visibility_changed.emit(checked)

    def _on_startup_toggled(self, checked: bool) -> None:
        self.settings.set("run_at_startup", checked)
        if checked:
            success = add_to_startup()
            if not success:
                QMessageBox.warning(
                    self,
                    "Windows Startup",
                    "Could not register FileX to start with Windows. Run as administrator or check registry permissions.",
                )
        else:
            remove_from_startup()
