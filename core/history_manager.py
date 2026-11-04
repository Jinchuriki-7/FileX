"""
core/history_manager.py
------------------------
Persists conversion history in a SQLite database stored at
%APPDATA%/FileX/history.db.  Provides CRUD operations and
simple query helpers used by the History page.
"""

import sqlite3
import os
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class HistoryEntry:
    """One conversion record."""
    id:            int
    source_path:   str
    source_format: str
    output_path:   str
    output_format: str
    status:        str          # 'success' | 'failed' | 'cancelled'
    error_msg:     str
    file_size_in:  int          # bytes
    file_size_out: int          # bytes
    duration_ms:   int          # conversion time in milliseconds
    created_at:    str          # ISO-8601 datetime string


# ---------------------------------------------------------------------------
# Manager
# ---------------------------------------------------------------------------

class HistoryManager:
    """
    SQLite-backed conversion history store.

    Args:
        db_path: Path to the SQLite database file.
                 Defaults to ``%APPDATA%/FileX/history.db``.
    """

    _CREATE_TABLE = """
        CREATE TABLE IF NOT EXISTS history (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            source_path   TEXT    NOT NULL,
            source_format TEXT    NOT NULL,
            output_path   TEXT    NOT NULL,
            output_format TEXT    NOT NULL,
            status        TEXT    NOT NULL DEFAULT 'success',
            error_msg     TEXT    NOT NULL DEFAULT '',
            file_size_in  INTEGER NOT NULL DEFAULT 0,
            file_size_out INTEGER NOT NULL DEFAULT 0,
            duration_ms   INTEGER NOT NULL DEFAULT 0,
            created_at    TEXT    NOT NULL
        )
    """

    def __init__(self, db_path: Optional[str] = None) -> None:
        if db_path:
            self._db_path = Path(db_path)
        else:
            appdata = os.environ.get("APPDATA") or str(Path.home())
            self._db_path = Path(appdata) / "FileX" / "history.db"

        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(self._CREATE_TABLE)
            conn.commit()

    @staticmethod
    def _row_to_entry(row: sqlite3.Row) -> HistoryEntry:
        return HistoryEntry(
            id=row["id"],
            source_path=row["source_path"],
            source_format=row["source_format"],
            output_path=row["output_path"],
            output_format=row["output_format"],
            status=row["status"],
            error_msg=row["error_msg"],
            file_size_in=row["file_size_in"],
            file_size_out=row["file_size_out"],
            duration_ms=row["duration_ms"],
            created_at=row["created_at"],
        )

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------

    def add_entry(
        self,
        source_path:   str,
        source_format: str,
        output_path:   str,
        output_format: str,
        status:        str = "success",
        error_msg:     str = "",
        file_size_in:  int = 0,
        file_size_out: int = 0,
        duration_ms:   int = 0,
    ) -> int:
        """
        Insert a new conversion record.

        Returns:
            The row ID of the inserted record.
        """
        created_at = datetime.now().isoformat(sep=" ", timespec="seconds")
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO history
                    (source_path, source_format, output_path, output_format,
                     status, error_msg, file_size_in, file_size_out, duration_ms, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (source_path, source_format, output_path, output_format,
                 status, error_msg, file_size_in, file_size_out, duration_ms, created_at),
            )
            conn.commit()
            return cursor.lastrowid  # type: ignore[return-value]

    def update_status(
        self,
        entry_id:     int,
        status:       str,
        error_msg:    str = "",
        file_size_out: int = 0,
        duration_ms:  int = 0,
    ) -> None:
        """Update status/result of an existing entry (call after conversion finishes)."""
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE history
                SET status=?, error_msg=?, file_size_out=?, duration_ms=?
                WHERE id=?
                """,
                (status, error_msg, file_size_out, duration_ms, entry_id),
            )
            conn.commit()

    def delete_entry(self, entry_id: int) -> None:
        """Delete a single history record."""
        with self._connect() as conn:
            conn.execute("DELETE FROM history WHERE id=?", (entry_id,))
            conn.commit()

    def clear_all(self) -> None:
        """Delete ALL history records."""
        with self._connect() as conn:
            conn.execute("DELETE FROM history")
            conn.commit()

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    def get_all(self, limit: int = 500, offset: int = 0) -> List[HistoryEntry]:
        """Return recent history entries (newest first)."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM history ORDER BY id DESC LIMIT ? OFFSET ?",
                (limit, offset),
            ).fetchall()
        return [self._row_to_entry(r) for r in rows]

    def get_by_id(self, entry_id: int) -> Optional[HistoryEntry]:
        """Return a single entry by primary key."""
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM history WHERE id=?", (entry_id,)).fetchone()
        return self._row_to_entry(row) if row else None

    def search(self, query: str, limit: int = 200) -> List[HistoryEntry]:
        """
        Full-text search over source/output paths and formats.

        Args:
            query: Substring to search for (case-insensitive).
            limit: Max results.
        """
        like = f"%{query}%"
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM history
                WHERE source_path LIKE ? OR output_path LIKE ?
                   OR source_format LIKE ? OR output_format LIKE ?
                ORDER BY id DESC LIMIT ?
                """,
                (like, like, like, like, limit),
            ).fetchall()
        return [self._row_to_entry(r) for r in rows]

    def total_count(self) -> int:
        """Return total number of history records."""
        with self._connect() as conn:
            return conn.execute("SELECT COUNT(*) FROM history").fetchone()[0]

    def stats(self) -> dict:
        """Return aggregate statistics for the history page."""
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT
                    COUNT(*) AS total,
                    SUM(CASE WHEN status='success'  THEN 1 ELSE 0 END) AS success_count,
                    SUM(CASE WHEN status='failed'   THEN 1 ELSE 0 END) AS fail_count,
                    SUM(file_size_in)  AS bytes_in,
                    SUM(file_size_out) AS bytes_out
                FROM history
                """
            ).fetchone()
        return {
            "total":         row["total"] or 0,
            "success_count": row["success_count"] or 0,
            "fail_count":    row["fail_count"] or 0,
            "bytes_in":      row["bytes_in"] or 0,
            "bytes_out":     row["bytes_out"] or 0,
        }

    def prune_old(self, max_entries: int = 500) -> None:
        """Delete the oldest entries if total exceeds *max_entries*."""
        with self._connect() as conn:
            count = conn.execute("SELECT COUNT(*) FROM history").fetchone()[0]
            if count > max_entries:
                excess = count - max_entries
                conn.execute(
                    "DELETE FROM history WHERE id IN "
                    "(SELECT id FROM history ORDER BY id ASC LIMIT ?)",
                    (excess,),
                )
                conn.commit()
