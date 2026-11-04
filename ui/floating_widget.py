"""
ui/floating_widget.py
---------------------
Compact, always-on-top, semi-transparent floating widget.
Supports dragging across the screen, direct Windows File Explorer drag-and-drop,
dynamic visual states (Idle, Dragging, Processing), and context menu navigation.
"""

from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import Qt, QPoint, Signal, QTimer, QRectF, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import (
    QColor,
    QPainter,
    QPen,
    QBrush,
    QFont,
    QLinearGradient,
    QRadialGradient,
    QCursor,
    QContextMenuEvent,
    QMouseEvent,
)
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QMenu,
    QGraphicsDropShadowEffect,
)

from core.settings_manager import SettingsManager
from core.file_detector import FileDetector


class FloatingWidget(QWidget):
    """
    Floating desktop widget for rapid file conversion by drag-and-drop.

    Signals:
        files_dropped(list[str]): Emitted when one or more files are dropped.
        open_main_window(): Emitted on double click or context menu action.
        request_close(): Emitted when exiting from the widget context menu.
    """

    files_dropped = Signal(list)
    open_main_window = Signal()
    request_close = Signal()

    # Visual states
    STATE_IDLE = 0
    STATE_DRAGGING = 1
    STATE_PROCESSING = 2

    def __init__(
        self,
        settings: SettingsManager,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._settings = settings
        self._detector = FileDetector()

        # Frameless, translucent, tool window (doesn't clutter taskbar if minimized to tray)
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAcceptDrops(True)

        # Geometry & sizing
        self.setFixedSize(140, 140)

        # Restore saved position
        saved_x = self._settings.get("widget_x", 100)
        saved_y = self._settings.get("widget_y", 150)
        self.move(int(saved_x), int(saved_y))

        # Drag tracking
        self._drag_position = QPoint()
        self._is_moving = False

        # State tracking
        self._state = self.STATE_IDLE
        self._progress = 0
        self._status_text = "Drop file"

        # Idle subtle breathing animation timer
        self._pulse = 0.0
        self._pulse_direction = 1
        self._pulse_timer = QTimer(self)
        self._pulse_timer.setInterval(40)
        self._pulse_timer.timeout.connect(self._on_pulse_tick)
        self._pulse_timer.start()

        # Shadow effect
        self._shadow = QGraphicsDropShadowEffect(self)
        self._shadow.setBlurRadius(24)
        self._shadow.setOffset(0, 4)
        self._shadow.setColor(QColor(0, 0, 0, 160))
        self.setGraphicsEffect(self._shadow)

        self.setToolTip("FileX — Drag & drop any file to convert\nDouble-click to open dashboard")

    # ----------------------------------------------------------------------
    # State Management
    # ----------------------------------------------------------------------
    def set_idle(self) -> None:
        """Switch to idle state."""
        self._state = self.STATE_IDLE
        self._status_text = "Drop file"
        self._progress = 0
        self._shadow.setColor(QColor(124, 77, 255, 120))
        self.update()

    def set_dragging_hover(self, active: bool) -> None:
        """Switch to dragging hover highlight state."""
        if active:
            self._state = self.STATE_DRAGGING
            self._status_text = "Release to Convert"
            self._shadow.setColor(QColor(56, 189, 248, 220))
        else:
            self.set_idle()
        self.update()

    def set_processing(self, progress: int = 0, message: str = "Converting…") -> None:
        """Switch to processing state with a progress percentage."""
        self._state = self.STATE_PROCESSING
        self._progress = progress
        self._status_text = f"{progress}%" if progress > 0 else message
        self._shadow.setColor(QColor(124, 77, 255, 200))
        self.update()

    def _on_pulse_tick(self) -> None:
        """Subtle animated pulsing for idle state."""
        self._pulse += 0.03 * self._pulse_direction
        if self._pulse >= 1.0:
            self._pulse = 1.0
            self._pulse_direction = -1
        elif self._pulse <= 0.0:
            self._pulse = 0.0
            self._pulse_direction = 1
        if self._state == self.STATE_IDLE:
            self.update()

    # ----------------------------------------------------------------------
    # Paint Event — Custom Glassmorphic Circle
    # ----------------------------------------------------------------------
    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = QRectF(self.rect()).adjusted(10, 10, -10, -10)
        center = rect.center()
        radius = rect.width() / 2.0

        opacity = float(self._settings.get("widget_opacity", 0.95))

        if self._state == self.STATE_DRAGGING:
            # Active Drag Hover — Neon blue gradient
            bg_gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
            bg_gradient.setColorAt(0.0, QColor(24, 26, 45, int(240 * opacity)))
            bg_gradient.setColorAt(1.0, QColor(14, 16, 28, int(245 * opacity)))
            border_color = QColor(56, 189, 248, 240)
            border_width = 3.0

        elif self._state == self.STATE_PROCESSING:
            # Processing state — Purple gradient with progress ring
            bg_gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
            bg_gradient.setColorAt(0.0, QColor(28, 24, 48, int(240 * opacity)))
            bg_gradient.setColorAt(1.0, QColor(16, 14, 30, int(245 * opacity)))
            border_color = QColor(124, 77, 255, 180)
            border_width = 2.0

        else:
            # Idle state — Deep dark purple with subtle breathing glow
            bg_gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
            bg_gradient.setColorAt(0.0, QColor(26, 27, 44, int(235 * opacity)))
            bg_gradient.setColorAt(1.0, QColor(17, 18, 30, int(245 * opacity)))
            alpha = int(120 + 80 * self._pulse)
            border_color = QColor(124, 77, 255, alpha)
            border_width = 2.0

        # Draw circle background
        painter.setBrush(QBrush(bg_gradient))
        painter.setPen(QPen(border_color, border_width))
        painter.drawEllipse(center, radius, radius)

        # If processing, draw progress arc
        if self._state == self.STATE_PROCESSING and self._progress > 0:
            arc_pen = QPen(QColor(56, 189, 248), 3.5, Qt.SolidLine, Qt.RoundCap)
            painter.setPen(arc_pen)
            painter.setBrush(Qt.NoBrush)
            # Qt drawArc uses 1/16th of a degree, starting at 3 o'clock (90 is top)
            start_angle = 90 * 16
            span_angle = -int((self._progress / 100.0) * 360 * 16)
            painter.drawArc(rect.adjusted(3, 3, -3, -3), start_angle, span_angle)

        # Draw Center Branding & Text
        if self._state == self.STATE_PROCESSING:
            # Progress percentage
            painter.setPen(QColor(241, 245, 249))
            font_pct = QFont("Segoe UI", 16, QFont.Bold)
            painter.setFont(font_pct)
            painter.drawText(
                QRectF(rect.left(), rect.top() + 32, rect.width(), 26),
                Qt.AlignCenter,
                f"{self._progress}%",
            )
            painter.setPen(QColor(148, 163, 184))
            font_sub = QFont("Segoe UI", 9)
            painter.setFont(font_sub)
            painter.drawText(
                QRectF(rect.left(), rect.top() + 60, rect.width(), 20),
                Qt.AlignCenter,
                "Converting",
            )

        elif self._state == self.STATE_DRAGGING:
            # Active Drag icon
            painter.setPen(QColor(56, 189, 248))
            font_icon = QFont("Segoe UI Emoji", 26)
            painter.setFont(font_icon)
            painter.drawText(
                QRectF(rect.left(), rect.top() + 24, rect.width(), 32),
                Qt.AlignCenter,
                "⚡",
            )
            painter.setPen(QColor(226, 232, 240))
            font_sub = QFont("Segoe UI", 9, QFont.Bold)
            painter.setFont(font_sub)
            painter.drawText(
                QRectF(rect.left(), rect.top() + 62, rect.width(), 20),
                Qt.AlignCenter,
                "Release",
            )

        else:
            # Idle logo
            painter.setPen(QColor(167, 139, 250))
            font_logo = QFont("Segoe UI", 18, QFont.ExtraBold)
            painter.setFont(font_logo)
            painter.drawText(
                QRectF(rect.left(), rect.top() + 26, rect.width(), 28),
                Qt.AlignCenter,
                "FX",
            )
            painter.setPen(QColor(148, 163, 184))
            font_sub = QFont("Segoe UI", 9, QFont.DemiBold)
            painter.setFont(font_sub)
            painter.drawText(
                QRectF(rect.left(), rect.top() + 58, rect.width(), 20),
                Qt.AlignCenter,
                "Drop file",
            )

    # ----------------------------------------------------------------------
    # Mouse Dragging Across Screen
    # ----------------------------------------------------------------------
    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            self._is_moving = True
            self._drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._is_moving and event.buttons() == Qt.LeftButton:
            new_pos = event.globalPosition().toPoint() - self._drag_position
            self.move(new_pos)
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton and self._is_moving:
            self._is_moving = False
            # Persist the new location in settings
            self._settings.set("widget_x", self.x())
            self._settings.set("widget_y", self.y())
            event.accept()

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            self.open_main_window.emit()
            event.accept()

    # ----------------------------------------------------------------------
    # Drag and Drop from Windows File Explorer
    # ----------------------------------------------------------------------
    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.set_dragging_hover(True)
        else:
            event.ignore()

    def dragMoveEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragLeaveEvent(self, event) -> None:
        self.set_dragging_hover(False)
        super().dragLeaveEvent(event)

    def dropEvent(self, event) -> None:
        self.set_dragging_hover(False)
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
    # Context Menu
    # ----------------------------------------------------------------------
    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        menu = QMenu(self)
        menu.setStyleSheet(
            """
            QMenu {
                background-color: #1a1b2b;
                border: 1px solid #32354f;
                border-radius: 8px;
                padding: 6px;
                color: #f1f5f9;
            }
            QMenu::item {
                padding: 6px 18px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #7c4dff;
                color: #ffffff;
            }
            """
        )

        act_dashboard = menu.addAction("📊 Open Dashboard")
        act_dashboard.triggered.connect(self.open_main_window.emit)

        menu.addSeparator()

        always_top = self._settings.get("always_on_top", True)
        act_top = menu.addAction("📌 Always on Top")
        act_top.setCheckable(True)
        act_top.setChecked(always_top)
        act_top.triggered.connect(self._toggle_always_on_top)

        menu.addSeparator()

        act_hide = menu.addAction("👁️ Hide Floating Widget")
        act_hide.triggered.connect(self.hide)

        act_exit = menu.addAction("🚪 Exit FileX")
        act_exit.triggered.connect(self.request_close.emit)

        menu.exec(event.globalPos())

    def _toggle_always_on_top(self, checked: bool) -> None:
        self._settings.set("always_on_top", checked)
        self.setWindowFlag(Qt.WindowStaysOnTopHint, checked)
        self.show()
