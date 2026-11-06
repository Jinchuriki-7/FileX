"""
utils/icon_utils.py
-------------------
Vector Lucide SVG icon generator for FileX.
Renders crisp, scale-independent SVG icons with dynamic color tinting
for dark theme UI consistency.
"""

from typing import Dict
from PySide6.QtCore import QByteArray, QSize, Qt
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor
from PySide6.QtSvg import QSvgRenderer

# ---------------------------------------------------------------------------
# Lucide SVG Icon Path Data (24x24 viewBox, stroke-width 2, stroke-linecap round)
# ---------------------------------------------------------------------------
_SVG_PATHS: Dict[str, str] = {
    "dashboard": """
        <rect width="7" height="9" x="3" y="3" rx="1"/>
        <rect width="7" height="5" x="14" y="3" rx="1"/>
        <rect width="7" height="9" x="14" y="12" rx="1"/>
        <rect width="7" height="5" x="3" y="16" rx="1"/>
    """,
    "zap": """
        <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
    """,
    "history": """
        <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/>
        <path d="M3 3v5h5"/>
        <path d="M12 7v5l4 2"/>
    """,
    "settings": """
        <path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/>
        <circle cx="12" cy="12" r="3"/>
    """,
    "image": """
        <rect width="18" height="18" x="3" y="3" rx="2" ry="2"/>
        <circle cx="9" cy="9" r="2"/>
        <path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21"/>
    """,
    "file-text": """
        <path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/>
        <path d="M14 2v4a2 2 0 0 0 2 2h4"/>
        <path d="M10 9H8"/>
        <path d="M16 13H8"/>
        <path d="M16 17H8"/>
    """,
    "pdf": """
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
        <polyline points="14 2 14 8 20 8"/>
        <path d="M10 12h2a1.5 1.5 0 0 1 0 3h-2v3"/>
        <path d="M16 18h-1.5a1.5 1.5 0 0 1-1.5-1.5v-3a1.5 1.5 0 0 1 1.5-1.5H16"/>
    """,
    "table": """
        <rect width="18" height="18" x="3" y="3" rx="2"/>
        <path d="M3 9h18"/>
        <path d="M3 15h18"/>
        <path d="M9 3v18"/>
        <path d="M15 3v18"/>
    """,
    "presentation": """
        <path d="M2 3h20"/>
        <path d="M21 3v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V3"/>
        <path d="m7 21 5-5 5 5"/>
    """,
    "music": """
        <path d="M9 18V5l12-2v13"/>
        <circle cx="6" cy="18" r="3"/>
        <circle cx="18" cy="16" r="3"/>
    """,
    "video": """
        <path d="m22 8-6 4 6 4V8Z"/>
        <rect width="14" height="12" x="2" y="6" rx="2" ry="2"/>
    """,
    "upload": """
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
        <polyline points="17 8 12 3 7 8"/>
        <line x1="12" x2="12" y1="3" y2="15"/>
    """,
    "arrow-right": """
        <path d="M5 12h14"/>
        <path d="m12 5 7 7-7 7"/>
    """,
    "check-circle": """
        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
        <path d="m9 11 3 3L22 4"/>
    """,
    "alert-circle": """
        <circle cx="12" cy="12" r="10"/>
        <line x1="12" x2="12" y1="8" y2="12"/>
        <line x1="12" x2="12" y1="16" y2="16.01"/>
    """,
    "folder-open": """
        <path d="m6 14 1.45-2.9A2 2 0 0 1 9.24 10H20a2 2 0 0 1 1.94 2.5l-1.55 6a2 2 0 0 1-1.94 1.5H4a2 2 0 0 1-2-2V5c0-1.1.9-2 2-2h3.93a2 2 0 0 1 1.66.9l.82 1.2a2 2 0 0 0 1.66.9H18a2 2 0 0 1 2 2v2"/>
    """,
    "external-link": """
        <path d="M15 3h6v6"/>
        <path d="M10 14 21 3"/>
        <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
    """,
    "search": """
        <circle cx="11" cy="11" r="8"/>
        <path d="m21 21-4.3-4.3"/>
    """,
    "trash": """
        <path d="M3 6h18"/>
        <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/>
        <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/>
    """,
    "minimize": """
        <path d="M5 12h14"/>
    """,
    "maximize": """
        <rect width="14" height="14" x="5" y="5" rx="1"/>
    """,
    "restore": """
        <path d="M9 5h10v10"/>
        <rect width="10" height="10" x="5" y="9" rx="1"/>
    """,
    "close": """
        <path d="M18 6 6 18"/>
        <path d="m6 6 12 12"/>
    """,
    "file": """
        <path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/>
        <path d="M14 2v4a2 2 0 0 0 2 2h4"/>
    """,
    "activity": """
        <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
    """,
    "trending-up": """
        <polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/>
        <polyline points="16 7 22 7 22 13"/>
    """,
}


def build_svg_xml(name: str, color: str = "#F5F5FA", stroke_width: float = 2.0) -> str:
    """Return full standalone SVG XML string for a Lucide icon."""
    path_data = _SVG_PATHS.get(name, _SVG_PATHS["file"])
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24"
        fill="none" stroke="{color}" stroke-width="{stroke_width}" stroke-linecap="round" stroke-linejoin="round">
        {path_data}
    </svg>"""


def get_svg_pixmap(name: str, color: str = "#F5F5FA", size: int = 20, stroke_width: float = 2.0) -> QPixmap:
    """Render a vector Lucide icon to a transparent QPixmap at the requested size."""
    svg_xml = build_svg_xml(name, color, stroke_width)
    byte_array = QByteArray(svg_xml.encode("utf-8"))
    renderer = QSvgRenderer(byte_array)

    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing, True)
    renderer.render(painter)
    painter.end()

    return pixmap


def get_svg_icon(name: str, color: str = "#F5F5FA", size: int = 20, stroke_width: float = 2.0) -> QIcon:
    """Return a QIcon generated from vector Lucide SVG data."""
    pixmap = get_svg_pixmap(name, color, size, stroke_width)
    return QIcon(pixmap)
