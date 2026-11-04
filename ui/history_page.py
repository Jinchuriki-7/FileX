"""
ui/history_page.py
------------------
History dashboard view showcasing past conversion metrics, searchable
records table, status indicators, and direct actions (Open File, Open Folder).
"""

import os
from pathlib import Path
from typing import Optional, List

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QCursor, QColor
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QFrame,
)

from core.history_manager import HistoryManager, HistoryEntry
from utils.file_utils import open_file, open_containing_folder, human_readable_size


class HistoryPage(QWidget):
    """
    Conversion History page displaying aggregate statistics,
    searchable conversion logs, and quick file/folder openers.
    """

    def __init__(
        self,
        history_manager: HistoryManager,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.history_manager = history_manager

        self._build_ui()
        self.refresh()

    # ----------------------------------------------------------------------
    # UI Setup
    # ----------------------------------------------------------------------
    def _build_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(28, 28, 28, 28)
        main_layout.setSpacing(20)

        # Header Title
        title_box = QVBoxLayout()
        title_box.setSpacing(4)
        lbl_title = QLabel("Conversion History", self)
        lbl_title.setObjectName("titleLabel")

        lbl_desc = QLabel(
            "Review past conversion tasks, track converted files, and view output locations.",
            self,
        )
        lbl_desc.setObjectName("subtitleLabel")

        title_box.addWidget(lbl_title)
        title_box.addWidget(lbl_desc)
        main_layout.addLayout(title_box)

        # Metric Cards Row
        metrics_layout = QHBoxLayout()
        metrics_layout.setSpacing(16)

        self.card_total = self._create_metric_card("TOTAL CONVERSIONS", "0", "#7c4dff")
        self.card_success = self._create_metric_card("SUCCESS RATE", "100%", "#10b981")
        self.card_volume = self._create_metric_card("DATA PROCESSED", "0 MB", "#38bdf8")

        metrics_layout.addWidget(self.card_total)
        metrics_layout.addWidget(self.card_success)
        metrics_layout.addWidget(self.card_volume)
        main_layout.addLayout(metrics_layout)

        # Search Bar & Actions Row
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(12)

        self.txt_search = QLineEdit(self)
        self.txt_search.setPlaceholderText("🔍  Search history by filename or format…")
        self.txt_search.setFixedHeight(38)
        self.txt_search.textChanged.connect(self._on_search_changed)

        btn_refresh = QPushButton("↻ Refresh", self)
        btn_refresh.setFixedHeight(38)
        btn_refresh.setCursor(QCursor(Qt.PointingHandCursor))
        btn_refresh.clicked.connect(self.refresh)

        btn_clear = QPushButton("🗑 Clear History", self)
        btn_clear.setFixedHeight(38)
        btn_clear.setCursor(QCursor(Qt.PointingHandCursor))
        btn_clear.setObjectName("dangerButton")
        btn_clear.clicked.connect(self._clear_history)

        filter_layout.addWidget(self.txt_search, 1)
        filter_layout.addWidget(btn_refresh, 0)
        filter_layout.addWidget(btn_clear, 0)
        main_layout.addLayout(filter_layout)

        # History Table
        self.table = QTableWidget(self)
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "File Name",
            "Conversion",
            "Date & Time",
            "Size",
            "Status",
            "Actions",
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)

        main_layout.addWidget(self.table, 1)

    def _create_metric_card(self, label: str, value: str, accent: str) -> QFrame:
        card = QFrame(self)
        card.setObjectName("cardFrame")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(4)

        lbl_val = QLabel(value, card)
        lbl_val.setObjectName("metricValue")
        lbl_val.setStyleSheet(f"color: {accent};")

        lbl_desc = QLabel(label, card)
        lbl_desc.setObjectName("metricLabel")

        layout.addWidget(lbl_val)
        layout.addWidget(lbl_desc)
        card.lbl_val = lbl_val  # Store reference for updating
        return card

    # ----------------------------------------------------------------------
    # Data Refresh & Table Population
    # ----------------------------------------------------------------------
    def refresh(self) -> None:
        """Fetch stats and records from history database and update view."""
        # Update metrics
        stats = self.history_manager.stats()
        total = stats.get("total", 0)
        success = stats.get("success_count", 0)
        bytes_in = stats.get("bytes_in", 0)

        self.card_total.lbl_val.setText(str(total))
        rate = int((success / total * 100)) if total > 0 else 100
        self.card_success.lbl_val.setText(f"{rate}%")
        self.card_volume.lbl_val.setText(human_readable_size(bytes_in))

        # Fetch records
        query = self.txt_search.text().strip()
        if query:
            entries = self.history_manager.search(query)
        else:
            entries = self.history_manager.get_all(limit=200)

        self._populate_table(entries)

    def _populate_table(self, entries: List[HistoryEntry]) -> None:
        self.table.setRowCount(len(entries))

        for row, entry in enumerate(entries):
            # Column 0: File Name
            src_name = Path(entry.source_path).name if entry.source_path else "Unknown"
            item_name = QTableWidgetItem(src_name)
            item_name.setToolTip(entry.source_path)
            self.table.setItem(row, 0, item_name)

            # Column 1: Conversion (SRC -> DST)
            fmt_str = f"{entry.source_format.upper()} → {entry.output_format.upper()}"
            item_fmt = QTableWidgetItem(fmt_str)
            item_fmt.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 1, item_fmt)

            # Column 2: Date & Time
            item_date = QTableWidgetItem(entry.created_at)
            item_date.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 2, item_date)

            # Column 3: Output Size
            size_str = human_readable_size(entry.file_size_out) if entry.file_size_out else "—"
            item_size = QTableWidgetItem(size_str)
            item_size.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 3, item_size)

            # Column 4: Status Badge
            status_item = QTableWidgetItem()
            if entry.status == "success":
                status_item.setText("✓ Success")
                status_item.setForeground(QColor("#34d399"))
            elif entry.status == "failed":
                status_item.setText("✕ Failed")
                status_item.setForeground(QColor("#f87171"))
                status_item.setToolTip(entry.error_msg)
            else:
                status_item.setText("⏳ Pending")
                status_item.setForeground(QColor("#60a5fa"))
            status_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 4, status_item)

            # Column 5: Action Buttons (Open File / Open Folder / Delete)
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 2, 4, 2)
            actions_layout.setSpacing(6)

            if entry.output_path and os.path.exists(entry.output_path):
                btn_open = QPushButton("Open", actions_widget)
                btn_open.setCursor(QCursor(Qt.PointingHandCursor))
                btn_open.setFixedHeight(24)
                btn_open.setStyleSheet(
                    "background: #252840; color: #a78bfa; border: none; border-radius: 4px; padding: 2px 8px;"
                )
                btn_open.clicked.connect(lambda _, p=entry.output_path: open_file(p))
                actions_layout.addWidget(btn_open)

            btn_folder = QPushButton("Folder", actions_widget)
            btn_folder.setCursor(QCursor(Qt.PointingHandCursor))
            btn_folder.setFixedHeight(24)
            btn_folder.setStyleSheet(
                "background: #202235; color: #94a3b8; border: none; border-radius: 4px; padding: 2px 8px;"
            )
            target_path = entry.output_path or entry.source_path
            btn_folder.clicked.connect(lambda _, p=target_path: open_containing_folder(p))
            actions_layout.addWidget(btn_folder)

            btn_del = QPushButton("✕", actions_widget)
            btn_del.setCursor(QCursor(Qt.PointingHandCursor))
            btn_del.setFixedSize(24, 24)
            btn_del.setStyleSheet(
                "background: transparent; color: #64748b; border: none; border-radius: 12px;"
            )
            btn_del.setToolTip("Delete this record")
            btn_del.clicked.connect(lambda _, eid=entry.id: self._delete_entry(eid))
            actions_layout.addWidget(btn_del)

            self.table.setCellWidget(row, 5, actions_widget)

    # ----------------------------------------------------------------------
    # Event Handlers
    # ----------------------------------------------------------------------
    def _on_search_changed(self, text: str) -> None:
        self.refresh()

    def _delete_entry(self, entry_id: int) -> None:
        self.history_manager.delete_entry(entry_id)
        self.refresh()

    def _clear_history(self) -> None:
        reply = QMessageBox.question(
            self,
            "Clear History",
            "Are you sure you want to delete all conversion history records?\n(Your actual files on disk will NOT be deleted).",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.history_manager.clear_all()
            self.refresh()
