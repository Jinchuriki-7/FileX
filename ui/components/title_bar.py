"""
ui/components/title_bar.py
--------------------------
Custom dark Windows title bar for FileX with window controls,
logo, title, double-click to maximize, and smooth dragging support.
"""

from typing import Optional
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QMouseEvent, QFont, QCursor
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QMainWindow,
)
from utils.icon_utils import get_svg_icon, get_svg_pixmap


class CustomTitleBar(QWidget):
    """
    Modern dark title bar matching Windows 11 Fluent dark aesthetics.
    """

    def __init__(self, parent_window: QMainWindow) -> None:
        super().__init__(parent_window)
        self.parent_window = parent_window
        self._drag_pos: Optional[QPoint] = None

        self.setFixedHeight(38)
        self.setObjectName("customTitleBar")
        self.setStyleSheet(
            """
            QWidget#customTitleBar {
                background-color: #0B0D14;
                border-bottom: 1px solid #1D2030;
            }
            QLabel {
                background: transparent;
            }
            QPushButton.windowControlBtn {
                background-color: transparent;
                border: none;
                border-radius: 4px;
                padding: 4px;
                margin: 2px 2px;
                min-width: 38px;
                max-width: 38px;
                min-height: 28px;
                max-height: 28px;
            }
            QPushButton.windowControlBtn:hover {
                background-color: #1D2030;
            }
            QPushButton.windowControlBtn:pressed {
                background-color: #292D40;
            }
            QPushButton#btnClose:hover {
                background-color: #EF4444;
            }
            QPushButton#btnClose:pressed {
                background-color: #DC2626;
            }
            """
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 6, 0)
        layout.setSpacing(8)

        # 1. Left: Logo & App Title
        self.lbl_logo = QLabel(self)
        self.lbl_logo.setPixmap(get_svg_pixmap("zap", "#8957FF", 16))
        layout.addWidget(self.lbl_logo)

        self.lbl_title = QLabel("FileX", self)
        self.lbl_title.setStyleSheet("font-size: 13px; font-weight: 700; color: #F5F5FA; letter-spacing: 0.3px;")
        layout.addWidget(self.lbl_title)

        self.lbl_divider = QLabel("•", self)
        self.lbl_divider.setStyleSheet("color: #292D40; font-size: 12px;")
        layout.addWidget(self.lbl_divider)

        self.lbl_sub = QLabel("Universal File Converter", self)
        self.lbl_sub.setStyleSheet("font-size: 11px; color: #687087; font-weight: 500;")
        layout.addWidget(self.lbl_sub)

        layout.addStretch()

        # 2. Right: Minimize, Maximize, Close Buttons
        self.btn_min = QPushButton(self)
        self.btn_min.setObjectName("btnMin")
        self.btn_min.setProperty("class", "windowControlBtn")
        self.btn_min.setIcon(get_svg_icon("minimize", "#9CA3B8", 14))
        self.btn_min.setToolTip("Minimize")
        self.btn_min.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_min.clicked.connect(self.parent_window.showMinimized)

        self.btn_max = QPushButton(self)
        self.btn_max.setObjectName("btnMax")
        self.btn_max.setProperty("class", "windowControlBtn")
        self.btn_max.setIcon(get_svg_icon("maximize", "#9CA3B8", 13))
        self.btn_max.setToolTip("Maximize")
        self.btn_max.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_max.clicked.connect(self._toggle_maximize)

        self.btn_close = QPushButton(self)
        self.btn_close.setObjectName("btnClose")
        self.btn_close.setProperty("class", "windowControlBtn")
        self.btn_close.setIcon(get_svg_icon("close", "#9CA3B8", 14))
        self.btn_close.setToolTip("Close to Tray")
        self.btn_close.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_close.clicked.connect(self.parent_window.close)

        layout.addWidget(self.btn_min)
        layout.addWidget(self.btn_max)
        layout.addWidget(self.btn_close)

    def _toggle_maximize(self) -> None:
        if self.parent_window.isMaximized():
            self.parent_window.showNormal()
            self.btn_max.setIcon(get_svg_icon("maximize", "#9CA3B8", 13))
            self.btn_max.setToolTip("Maximize")
        else:
            self.parent_window.showMaximized()
            self.btn_max.setIcon(get_svg_icon("restore", "#9CA3B8", 13))
            self.btn_max.setToolTip("Restore Down")

    # ----------------------------------------------------------------------
    # Drag & Double-Click Handlers
    # ----------------------------------------------------------------------
    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.parent_window.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if event.buttons() == Qt.LeftButton and self._drag_pos is not None:
            if not self.parent_window.isMaximized():
                self.parent_window.move(event.globalPosition().toPoint() - self._drag_pos)
                event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._drag_pos = None

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            self._toggle_maximize()
