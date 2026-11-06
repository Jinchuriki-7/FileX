"""
ui/components/drop_zone.py
--------------------------
Modern drag-and-drop target zone widget with animated dashed borders,
hover highlights, and direct integration with native Windows File Explorer.
"""

from pathlib import Path
from typing import List, Optional
from PySide6.QtCore import Qt, Signal, QRectF
from PySide6.QtGui import QColor, QPainter, QPen, QFont, QCursor
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QFileDialog,
)
from utils.icon_utils import get_svg_pixmap


class DropZone(QWidget):
    """
    Interactive drop zone that receives dragged files from Windows File Explorer
    or opens a file picker on click.

    Signals:
        files_dropped(list[str]): Emitted when one or more valid files are dropped.
    """

    files_dropped = Signal(list)

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        title: str = "Drop files here to convert",
        subtitle: str = "or click to browse from your computer",
    ) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setMinimumHeight(190)

        self._is_drag_over = False
        self._title_text = title
        self._subtitle_text = subtitle

        # Internal Layout
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(6)

        # Vector Icon Label
        self.icon_label = QLabel(self)
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setPixmap(get_svg_pixmap("upload", "#8957FF", 36))
        self.icon_label.setStyleSheet("background: transparent;")

        # Title Label
        self.lbl_title = QLabel(self._title_text, self)
        self.lbl_title.setAlignment(Qt.AlignCenter)
        self.lbl_title.setStyleSheet(
            "background: transparent; color: #F5F5FA; font-size: 16px; font-weight: 700;"
        )

        # Subtitle Label
        self.lbl_subtitle = QLabel(self._subtitle_text, self)
        self.lbl_subtitle.setAlignment(Qt.AlignCenter)
        self.lbl_subtitle.setStyleSheet(
            "background: transparent; color: #9CA3B8; font-size: 13px;"
        )

        # Formats Hint
        self.lbl_formats = QLabel(
            "Supported: Images • Documents • PDFs • Spreadsheets • Audio • Video", self
        )
        self.lbl_formats.setAlignment(Qt.AlignCenter)
        self.lbl_formats.setStyleSheet(
            "background: transparent; color: #687087; font-size: 11px; margin-top: 4px;"
        )

        layout.addWidget(self.icon_label)
        layout.addWidget(self.lbl_title)
        layout.addWidget(self.lbl_subtitle)
        layout.addWidget(self.lbl_formats)

    # ----------------------------------------------------------------------
    # Paint Event — Custom dashed border and background
    # ----------------------------------------------------------------------
    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = QRectF(self.rect()).adjusted(2, 2, -2, -2)
        corner_radius = 12.0

        if self._is_drag_over:
            bg_color = QColor(137, 87, 255, 30)
            border_color = QColor(137, 87, 255, 230)
            pen = QPen(border_color, 2, Qt.DashLine)
        else:
            bg_color = QColor(18, 20, 31, 200)
            border_color = QColor(41, 45, 64, 220)
            pen = QPen(border_color, 1.5, Qt.DashLine)

        painter.setBrush(bg_color)
        painter.setPen(pen)
        painter.drawRoundedRect(rect, corner_radius, corner_radius)

    # ----------------------------------------------------------------------
    # Drag and Drop Events
    # ----------------------------------------------------------------------
    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self._is_drag_over = True
            self.lbl_title.setText("Release to start conversion!")
            self.lbl_title.setStyleSheet(
                "background: transparent; color: #A78BFA; font-size: 16px; font-weight: 700;"
            )
            self.icon_label.setPixmap(get_svg_pixmap("upload", "#38BDF8", 36))
            self.update()
        else:
            event.ignore()

    def dragMoveEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragLeaveEvent(self, event) -> None:
        self._is_drag_over = False
        self.lbl_title.setText(self._title_text)
        self.lbl_title.setStyleSheet(
            "background: transparent; color: #F5F5FA; font-size: 16px; font-weight: 700;"
        )
        self.icon_label.setPixmap(get_svg_pixmap("upload", "#8957FF", 36))
        self.update()
        super().dragLeaveEvent(event)

    def dropEvent(self, event) -> None:
        self._is_drag_over = False
        self.lbl_title.setText(self._title_text)
        self.lbl_title.setStyleSheet(
            "background: transparent; color: #F5F5FA; font-size: 16px; font-weight: 700;"
        )
        self.icon_label.setPixmap(get_svg_pixmap("upload", "#8957FF", 36))
        self.update()

        paths: List[str] = []
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                local_path = url.toLocalFile()
                if local_path and Path(local_path).is_file():
                    paths.append(local_path)

        if paths:
            event.acceptProposedAction()
            self.files_dropped.emit(paths)
        else:
            event.ignore()

    # ----------------------------------------------------------------------
    # Click to Browse Files
    # ----------------------------------------------------------------------
    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            selected_files, _ = QFileDialog.getOpenFileNames(
                self,
                "Select Files to Convert",
                "",
                "All Supported Files (*.*);;Images (*.png *.jpg *.jpeg *.webp *.bmp *.tiff *.ico);;Documents (*.docx *.txt *.pdf *.html *.md);;Spreadsheets (*.xlsx *.csv *.ods);;Media (*.mp4 *.mkv *.mp3 *.wav *.flac)",
            )
            if selected_files:
                self.files_dropped.emit(selected_files)
        super().mousePressEvent(event)
