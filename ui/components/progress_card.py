"""
ui/components/progress_card.py
------------------------------
Modern card widget displaying live conversion progress, file metrics,
and post-conversion actions (Open File, Open Folder).
"""

import os
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import (
    QWidget,
    QFrame,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
)

from utils.file_utils import open_file, open_containing_folder, human_readable_size
from utils.icon_utils import get_svg_icon, get_svg_pixmap


class ProgressCard(QFrame):
    """
    Card presenting the state of a single conversion task:
    progress bar, error or success state, and action buttons.

    Signals:
        cancelled(str): Emitted with source_path if the user cancels.
    """

    cancelled = Signal(str)

    def __init__(
        self,
        source_path: str,
        target_format: str,
        category_icon: str = "file-text",
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.source_path = source_path
        self.target_format = target_format.upper()
        self.output_path: Optional[str] = None
        self.category_icon = category_icon

        self.setObjectName("cardFrame")
        self.setStyleSheet(
            """
            QFrame#cardFrame {
                background-color: #171A27;
                border: 1px solid #292D40;
                border-radius: 10px;
                padding: 10px;
            }
            QFrame#cardFrame:hover {
                border-color: #383D56;
            }
            """
        )

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 12, 14, 12)
        main_layout.setSpacing(8)

        # Header: Icon + File Details + Format Badge
        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)

        # Category Vector Icon
        self.icon_label = QLabel(self)
        icon_name = category_icon if category_icon in ["image", "pdf", "file-text", "table", "presentation", "music", "video"] else "file-text"
        self.icon_label.setPixmap(get_svg_pixmap(icon_name, "#8957FF", 22))
        self.icon_label.setStyleSheet("background: transparent;")
        header_layout.addWidget(self.icon_label)

        # File Info block
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)

        file_name = Path(source_path).name
        self.lbl_filename = QLabel(file_name, self)
        self.lbl_filename.setStyleSheet(
            "background: transparent; color: #F5F5FA; font-weight: 600; font-size: 13px;"
        )

        size_str = (
            human_readable_size(os.path.getsize(source_path))
            if os.path.exists(source_path)
            else "Unknown"
        )
        src_ext = Path(source_path).suffix.lstrip(".").upper()
        self.lbl_meta = QLabel(f"{size_str} • {src_ext} → {self.target_format}", self)
        self.lbl_meta.setStyleSheet(
            "background: transparent; color: #9CA3B8; font-size: 11px;"
        )

        info_layout.addWidget(self.lbl_filename)
        info_layout.addWidget(self.lbl_meta)
        header_layout.addLayout(info_layout, 1)

        # Status badge
        self.lbl_status = QLabel("Queued", self)
        self.lbl_status.setStyleSheet(
            """
            background-color: #1D2030;
            color: #9CA3B8;
            border: 1px solid #292D40;
            border-radius: 6px;
            padding: 4px 10px;
            font-size: 11px;
            font-weight: 600;
            """
        )
        header_layout.addWidget(self.lbl_status)
        main_layout.addLayout(header_layout)

        # Progress Bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setTextVisible(False)
        main_layout.addWidget(self.progress_bar)

        # Action Buttons Layout (Hidden initially until conversion finishes)
        self.actions_widget = QWidget(self)
        self.actions_widget.setStyleSheet("background: transparent;")
        self.actions_layout = QHBoxLayout(self.actions_widget)
        self.actions_layout.setContentsMargins(0, 4, 0, 0)
        self.actions_layout.setSpacing(8)

        self.btn_open_file = QPushButton("Open File", self)
        self.btn_open_file.setIcon(get_svg_icon("external-link", "#F5F5FA", 13))
        self.btn_open_file.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_open_file.setFixedHeight(28)
        self.btn_open_file.setStyleSheet(
            """
            QPushButton {
                background-color: #8957FF;
                border: 1px solid #9D71FF;
                border-radius: 6px;
                color: #FFFFFF;
                font-size: 11px;
                font-weight: 600;
                padding: 4px 12px;
            }
            QPushButton:hover {
                background-color: #9D71FF;
            }
            """
        )
        self.btn_open_file.clicked.connect(self._on_open_file)

        self.btn_open_folder = QPushButton("Open Folder", self)
        self.btn_open_folder.setIcon(get_svg_icon("folder-open", "#9CA3B8", 13))
        self.btn_open_folder.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_open_folder.setFixedHeight(28)
        self.btn_open_folder.setStyleSheet(
            """
            QPushButton {
                background-color: #1D2030;
                border: 1px solid #292D40;
                border-radius: 6px;
                color: #9CA3B8;
                font-size: 11px;
                font-weight: 600;
                padding: 4px 12px;
            }
            QPushButton:hover {
                background-color: #25293D;
                color: #F5F5FA;
                border-color: #383D56;
            }
            """
        )
        self.btn_open_folder.clicked.connect(self._on_open_folder)

        self.actions_layout.addStretch()
        self.actions_layout.addWidget(self.btn_open_file)
        self.actions_layout.addWidget(self.btn_open_folder)
        self.actions_widget.setVisible(False)
        main_layout.addWidget(self.actions_widget)

    # ----------------------------------------------------------------------
    # Status Updaters
    # ----------------------------------------------------------------------
    def set_progress(self, percent: int) -> None:
        """Update the progress bar value and status text."""
        self.progress_bar.setValue(percent)
        self.lbl_status.setText(f"Converting… {percent}%")
        self.lbl_status.setStyleSheet(
            """
            background-color: #1D2030;
            color: #8957FF;
            border: 1px solid #383D56;
            border-radius: 6px;
            padding: 4px 10px;
            font-size: 11px;
            font-weight: 600;
            """
        )

    def set_completed(self, output_path: str) -> None:
        """Mark conversion as successfully completed."""
        self.output_path = output_path
        self.progress_bar.setValue(100)
        self.progress_bar.setStyleSheet(
            """
            QProgressBar::chunk {
                background-color: #22C55E;
                border-radius: 5px;
            }
            """
        )
        self.lbl_status.setText("✓ Completed")
        self.lbl_status.setStyleSheet(
            """
            background-color: #14281E;
            color: #22C55E;
            border: 1px solid #1E4631;
            border-radius: 6px;
            padding: 4px 10px;
            font-size: 11px;
            font-weight: 600;
            """
        )
        self.actions_widget.setVisible(True)

    def set_failed(self, error_message: str) -> None:
        """Mark conversion as failed with an error message."""
        self.progress_bar.setValue(100)
        self.progress_bar.setStyleSheet(
            """
            QProgressBar::chunk {
                background-color: #EF4444;
                border-radius: 5px;
            }
            """
        )
        short_err = error_message[:35] + "…" if len(error_message) > 35 else error_message
        self.lbl_status.setText(f"✕ {short_err}")
        self.lbl_status.setToolTip(error_message)
        self.lbl_status.setStyleSheet(
            """
            background-color: #2D141A;
            color: #EF4444;
            border: 1px solid #4C1E26;
            border-radius: 6px;
            padding: 4px 10px;
            font-size: 11px;
            font-weight: 600;
            """
        )

    # ----------------------------------------------------------------------
    # Actions
    # ----------------------------------------------------------------------
    def _on_open_file(self) -> None:
        if self.output_path and os.path.exists(self.output_path):
            open_file(self.output_path)

    def _on_open_folder(self) -> None:
        target = self.output_path or self.source_path
        if target:
            open_containing_folder(target)
