"""
ui/conversion_dialog.py
-----------------------
Elegant popup dialog shown when files are dropped onto FileX.
Displays detected file metadata, available target formats, progress tracking,
and post-conversion actions (Open File, Open Folder). Supports single & batch modes.
"""

import os
from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QCursor, QColor
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QProgressBar,
    QWidget,
    QFileDialog,
    QGraphicsDropShadowEffect,
)

from core.file_detector import FileDetector
from core.format_registry import FormatRegistry
from core.conversion_manager import ConversionManager
from core.settings_manager import SettingsManager
from utils.file_utils import human_readable_size, open_file, open_containing_folder
from ui.components.animated_button import AnimatedButton


class ConversionDialog(QDialog):
    """
    Dialog for reviewing dropped files, selecting the target format,
    and monitoring the live conversion progress.
    """

    conversion_complete = Signal(str)  # emitted with output path

    def __init__(
        self,
        files: List[str],
        conversion_manager: ConversionManager,
        settings: SettingsManager,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.files = files
        self.conversion_manager = conversion_manager
        self.settings = settings
        self.detector = FileDetector()
        self.registry = FormatRegistry()

        self.current_index = 0
        self.output_results: List[str] = []
        self.active_worker = None

        self.setWindowTitle("FileX — Convert File")
        self.setMinimumWidth(440)
        self.setWindowFlags(Qt.Dialog | Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        self._build_ui()
        self._load_file_info()

    # ----------------------------------------------------------------------
    # UI Setup
    # ----------------------------------------------------------------------
    def _build_ui(self) -> None:
        # Container widget with border radius and background
        self.container = QWidget(self)
        self.container.setObjectName("dialogContainer")
        self.container.setStyleSheet(
            """
            QWidget#dialogContainer {
                background-color: #171826;
                border: 1px solid #32354f;
                border-radius: 14px;
            }
            """
        )

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(32)
        shadow.setColor(QColor(0, 0, 0, 180))
        shadow.setOffset(0, 6)
        self.container.setGraphicsEffect(shadow)

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(10, 10, 10, 10)
        outer_layout.addWidget(self.container)

        self.layout = QVBoxLayout(self.container)
        self.layout.setContentsMargins(24, 22, 24, 22)
        self.layout.setSpacing(14)

        # Title bar: App icon + Title + Close [X]
        title_bar = QHBoxLayout()
        title_icon = QLabel("⚡", self)
        title_icon.setFont(QFont("Segoe UI Emoji", 14))
        title_icon.setStyleSheet("color: #7c4dff;")

        self.lbl_heading = QLabel("Convert File", self)
        self.lbl_heading.setStyleSheet("font-size: 15px; font-weight: 700; color: #f8fafc;")

        btn_close = QPushButton("✕", self)
        btn_close.setFixedSize(26, 26)
        btn_close.setCursor(QCursor(Qt.PointingHandCursor))
        btn_close.setStyleSheet(
            """
            QPushButton {
                background: transparent;
                border: none;
                color: #94a3b8;
                font-size: 13px;
                border-radius: 13px;
            }
            QPushButton:hover {
                background-color: #2b2d42;
                color: #ffffff;
            }
            """
        )
        btn_close.clicked.connect(self.reject)

        title_bar.addWidget(title_icon)
        title_bar.addWidget(self.lbl_heading)
        title_bar.addStretch()
        title_bar.addWidget(btn_close)
        self.layout.addLayout(title_bar)

        # File Card Preview
        self.file_card = QWidget(self)
        self.file_card.setStyleSheet(
            """
            background-color: #1f2033;
            border: 1px solid #2d304a;
            border-radius: 10px;
            padding: 8px;
            """
        )
        card_layout = QHBoxLayout(self.file_card)
        card_layout.setContentsMargins(12, 10, 12, 10)
        card_layout.setSpacing(12)

        self.lbl_file_icon = QLabel("📄", self.file_card)
        self.lbl_file_icon.setFont(QFont("Segoe UI Emoji", 26))
        self.lbl_file_icon.setStyleSheet("background: transparent;")

        meta_layout = QVBoxLayout()
        meta_layout.setSpacing(2)

        self.lbl_file_name = QLabel("filename.ext", self.file_card)
        self.lbl_file_name.setStyleSheet(
            "background: transparent; font-weight: 600; color: #f1f5f9; font-size: 13px;"
        )

        self.lbl_file_meta = QLabel("0 KB • Format", self.file_card)
        self.lbl_file_meta.setStyleSheet(
            "background: transparent; color: #94a3b8; font-size: 11px;"
        )

        meta_layout.addWidget(self.lbl_file_name)
        meta_layout.addWidget(self.lbl_file_meta)
        card_layout.addWidget(self.lbl_file_icon)
        card_layout.addLayout(meta_layout, 1)
        self.layout.addWidget(self.file_card)

        # Format Selection Row
        fmt_layout = QVBoxLayout()
        fmt_layout.setSpacing(6)

        lbl_target_prompt = QLabel("Select Target Format:", self)
        lbl_target_prompt.setStyleSheet("color: #cbd5e1; font-size: 12px; font-weight: 600;")

        self.combo_formats = QComboBox(self)
        self.combo_formats.setFixedHeight(36)
        self.combo_formats.setCursor(QCursor(Qt.PointingHandCursor))

        fmt_layout.addWidget(lbl_target_prompt)
        fmt_layout.addWidget(self.combo_formats)
        self.layout.addLayout(fmt_layout)

        # Output Directory Row
        dir_layout = QHBoxLayout()
        dir_layout.setSpacing(8)

        self.lbl_out_dir = QLabel(self.settings.output_folder, self)
        self.lbl_out_dir.setStyleSheet("color: #94a3b8; font-size: 11px;")
        self.lbl_out_dir.setToolTip(self.settings.output_folder)

        btn_browse_dir = QPushButton("Browse…", self)
        btn_browse_dir.setFixedHeight(28)
        btn_browse_dir.setCursor(QCursor(Qt.PointingHandCursor))
        btn_browse_dir.setStyleSheet(
            """
            QPushButton {
                background-color: #24263a;
                border: 1px solid #363956;
                border-radius: 6px;
                color: #cbd5e1;
                font-size: 11px;
                padding: 4px 10px;
            }
            QPushButton:hover {
                background-color: #2f324d;
                color: #ffffff;
            }
            """
        )
        btn_browse_dir.clicked.connect(self._browse_output_dir)

        dir_layout.addWidget(QLabel("Save to:", self), 0)
        dir_layout.addWidget(self.lbl_out_dir, 1)
        dir_layout.addWidget(btn_browse_dir, 0)
        self.layout.addLayout(dir_layout)

        # Progress Section (Initially hidden)
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setVisible(False)
        self.layout.addWidget(self.progress_bar)

        self.lbl_status = QLabel("", self)
        self.lbl_status.setAlignment(Qt.AlignCenter)
        self.lbl_status.setStyleSheet("color: #a78bfa; font-size: 12px; font-weight: 500;")
        self.lbl_status.setVisible(False)
        self.layout.addWidget(self.lbl_status)

        # Post-Conversion Actions (Initially hidden)
        self.success_widget = QWidget(self)
        self.success_widget.setStyleSheet("background: transparent;")
        success_layout = QHBoxLayout(self.success_widget)
        success_layout.setContentsMargins(0, 0, 0, 0)
        success_layout.setSpacing(10)

        self.btn_open_file = QPushButton("Open Converted File", self)
        self.btn_open_file.setFixedHeight(34)
        self.btn_open_file.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_open_file.setStyleSheet(
            """
            QPushButton {
                background-color: #7c4dff;
                border: none;
                border-radius: 6px;
                color: #ffffff;
                font-weight: 600;
                padding: 6px 14px;
            }
            QPushButton:hover {
                background-color: #8f64ff;
            }
            """
        )
        self.btn_open_file.clicked.connect(self._open_result_file)

        self.btn_open_folder = QPushButton("Open Folder", self)
        self.btn_open_folder.setFixedHeight(34)
        self.btn_open_folder.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_open_folder.setStyleSheet(
            """
            QPushButton {
                background-color: #24263a;
                border: 1px solid #363956;
                border-radius: 6px;
                color: #cbd5e1;
                font-weight: 600;
                padding: 6px 14px;
            }
            QPushButton:hover {
                background-color: #2f324d;
                color: #ffffff;
            }
            """
        )
        self.btn_open_folder.clicked.connect(self._open_result_folder)

        success_layout.addWidget(self.btn_open_file)
        success_layout.addWidget(self.btn_open_folder)
        self.success_widget.setVisible(False)
        self.layout.addWidget(self.success_widget)

        # Bottom Button Bar (Convert & Cancel)
        self.button_bar = QWidget(self)
        self.button_bar.setStyleSheet("background: transparent;")
        btn_layout = QHBoxLayout(self.button_bar)
        btn_layout.setContentsMargins(0, 4, 0, 0)
        btn_layout.setSpacing(10)

        self.btn_cancel = QPushButton("Cancel", self)
        self.btn_cancel.setFixedHeight(36)
        self.btn_cancel.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_cancel.setObjectName("secondaryButton")
        self.btn_cancel.clicked.connect(self.reject)

        self.btn_convert = AnimatedButton("Convert Now", self, primary=True)
        self.btn_convert.setFixedHeight(36)
        self.btn_convert.clicked.connect(self._start_conversion)

        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_convert)
        self.layout.addWidget(self.button_bar)

    # ----------------------------------------------------------------------
    # Load File Information
    # ----------------------------------------------------------------------
    def _load_file_info(self) -> None:
        if not self.files:
            return

        current_file = self.files[self.current_index]
        p = Path(current_file)
        self.lbl_file_name.setText(p.name)

        size_str = human_readable_size(p.stat().st_size) if p.exists() else "0 B"
        ext, category, fmt_info = self.detector.detect(current_file)
        category_name = category.capitalize() if category else "Unknown"
        self.lbl_file_meta.setText(f"{size_str} • {category_name} ({ext.upper()})")

        # Category icon
        icon_map = {
            "image": "🖼️",
            "pdf": "📄",
            "document": "📝",
            "spreadsheet": "📊",
            "presentation": "📽️",
            "audio": "🎵",
            "video": "🎬",
        }
        self.lbl_file_icon.setText(icon_map.get(category, "📁"))

        # Populate valid target formats
        self.combo_formats.clear()
        targets = self.registry.get_output_formats(ext)
        if targets:
            for t in targets:
                t_info = self.registry.get_format(t)
                label = f"{t.upper()} — {t_info.label}" if t_info else t.upper()
                self.combo_formats.addItem(label, t)
            self.btn_convert.setEnabled(True)
        else:
            self.combo_formats.addItem("No conversions available", None)
            self.btn_convert.setEnabled(False)

        if len(self.files) > 1:
            self.lbl_heading.setText(f"Convert File ({self.current_index + 1} of {len(self.files)})")

    # ----------------------------------------------------------------------
    # Handlers
    # ----------------------------------------------------------------------
    def _browse_output_dir(self) -> None:
        dir_path = QFileDialog.getExistingDirectory(
            self, "Select Output Directory", self.settings.output_folder
        )
        if dir_path:
            self.settings.set("output_folder", dir_path)
            self.lbl_out_dir.setText(dir_path)
            self.lbl_out_dir.setToolTip(dir_path)

    def _start_conversion(self) -> None:
        target_fmt = self.combo_formats.currentData()
        if not target_fmt:
            return

        current_file = self.files[self.current_index]
        out_dir = self.lbl_out_dir.text()

        # UI State transition to Processing
        self.button_bar.setVisible(False)
        self.combo_formats.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(10)
        self.lbl_status.setVisible(True)
        self.lbl_status.setText(f"Converting to {target_fmt.upper()}…")

        self.active_worker = self.conversion_manager.convert(
            source_path=current_file,
            output_format=target_fmt,
            output_dir=out_dir,
        )

        if self.active_worker:
            self.active_worker.progress.connect(self._on_progress)
            self.active_worker.finished.connect(self._on_finished)
        else:
            self._on_finished(False, "Failed to start conversion.")

    def _on_progress(self, percent: int) -> None:
        self.progress_bar.setValue(percent)

    def _on_finished(self, success: bool, result_or_err: str) -> None:
        if success:
            self.progress_bar.setValue(100)
            self.lbl_status.setText("✓ Conversion Complete!")
            self.lbl_status.setStyleSheet("color: #34d399; font-size: 13px; font-weight: 700;")
            self.output_results.append(result_or_err)
            self.conversion_complete.emit(result_or_err)

            # Check if there are more files in the batch
            if self.current_index + 1 < len(self.files):
                self.current_index += 1
                self.progress_bar.setVisible(False)
                self.lbl_status.setVisible(False)
                self.button_bar.setVisible(True)
                self.combo_formats.setEnabled(True)
                self._load_file_info()
            else:
                # Finished entire batch
                self.success_widget.setVisible(True)
                self.btn_cancel.setText("Close")
                self.button_bar.setVisible(True)
                self.btn_convert.setVisible(False)
        else:
            self.lbl_status.setText(f"✕ Error: {result_or_err}")
            self.lbl_status.setStyleSheet("color: #f87171; font-size: 12px; font-weight: 600;")
            self.button_bar.setVisible(True)
            self.btn_convert.setText("Retry")
            self.btn_convert.setEnabled(True)

    def _open_result_file(self) -> None:
        if self.output_results:
            open_file(self.output_results[-1])

    def _open_result_folder(self) -> None:
        if self.output_results:
            open_containing_folder(self.output_results[-1])
        else:
            open_containing_folder(self.lbl_out_dir.text())
