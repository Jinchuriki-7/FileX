"""
ui/components/animated_button.py
--------------------------------
Custom interactive button with smooth hover effects, glowing borders,
and click animations tailored for the FileX dark UI theme.
"""

from typing import Optional
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, Property, QPoint
from PySide6.QtGui import QColor, QPainter, QBrush, QPen, QCursor
from PySide6.QtWidgets import QPushButton, QWidget, QGraphicsDropShadowEffect


class AnimatedButton(QPushButton):
    """
    Enhanced QPushButton featuring animated transitions, hover glow effects,
    and distinct styling variants (primary, secondary, danger).
    """

    def __init__(
        self,
        text: str = "",
        parent: Optional[QWidget] = None,
        primary: bool = False,
        danger: bool = False,
    ) -> None:
        super().__init__(text, parent)
        self._primary = primary
        self._danger = danger
        self._hover_progress = 0.0

        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setFixedHeight(38)

        # Subtle shadow effect for elevated look
        self._shadow = QGraphicsDropShadowEffect(self)
        self._shadow.setBlurRadius(12)
        self._shadow.setOffset(0, 3)

        if self._primary:
            self._shadow.setColor(QColor(124, 77, 255, 120))  # Purple glow
            self.setProperty("primary", True)
            self.setObjectName("primaryButton")
        elif self._danger:
            self._shadow.setColor(QColor(239, 68, 68, 80))   # Red glow
            self.setObjectName("dangerButton")
        else:
            self._shadow.setColor(QColor(0, 0, 0, 80))
            self.setObjectName("secondaryButton")

        self.setGraphicsEffect(self._shadow)

        # Hover animation setup
        self._anim = QPropertyAnimation(self, b"hoverProgress", self)
        self._anim.setDuration(160)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)

    # ----------------------------------------------------------------------
    # Qt Property for Hover Transition
    # ----------------------------------------------------------------------
    @Property(float)
    def hoverProgress(self) -> float:
        return self._hover_progress

    @hoverProgress.setter
    def hoverProgress(self, val: float) -> None:
        self._hover_progress = val
        if self._primary:
            glow = int(120 + 80 * val)
            self._shadow.setColor(QColor(124, 77, 255, glow))
            self._shadow.setBlurRadius(12 + 8 * val)
        elif self._danger:
            glow = int(80 + 70 * val)
            self._shadow.setColor(QColor(239, 68, 68, glow))
            self._shadow.setBlurRadius(12 + 6 * val)
        else:
            blur = 12 + 6 * val
            self._shadow.setBlurRadius(blur)

    # ----------------------------------------------------------------------
    # Event Handlers
    # ----------------------------------------------------------------------
    def enterEvent(self, event) -> None:
        self._anim.stop()
        self._anim.setStartValue(self._hover_progress)
        self._anim.setEndValue(1.0)
        self._anim.start()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._anim.stop()
        self._anim.setStartValue(self._hover_progress)
        self._anim.setEndValue(0.0)
        self._anim.start()
        super().leaveEvent(event)
