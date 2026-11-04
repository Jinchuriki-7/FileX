"""
core/conversion_manager.py
---------------------------
Orchestrates file conversions:
  1. Detects the source format
  2. Selects the appropriate converter
  3. Runs the conversion in a background QThread
  4. Records the result in history
  5. Emits Qt signals for progress and completion
"""

import os
import time
from pathlib import Path
from typing import Optional, Callable

from PySide6.QtCore import QThread, Signal, QObject

from core.file_detector import FileDetector
from core.history_manager import HistoryManager
from core.settings_manager import SettingsManager
from utils.file_utils import build_output_path, human_readable_size
from utils.notifications import notify


# ---------------------------------------------------------------------------
# Worker thread
# ---------------------------------------------------------------------------

class ConversionWorker(QThread):
    """
    Runs a single file conversion in a background thread.

    Signals:
        progress(int):         Emitted with 0-100 progress percentage.
        status_update(str):    Human-readable status message.
        finished(bool, str):   Emitted when done: (success, output_path_or_error).
    """

    progress      = Signal(int)
    status_update = Signal(str)
    finished      = Signal(bool, str)

    def __init__(
        self,
        source_path:   str,
        output_format: str,
        output_dir:    str,
        converter_fn:  Callable,         # the actual converter callable
        parent:        Optional[QObject] = None,
    ) -> None:
        super().__init__(parent)
        self.source_path   = source_path
        self.output_format = output_format
        self.output_dir    = output_dir
        self.converter_fn  = converter_fn
        self._cancelled    = False

    # ------------------------------------------------------------------
    def run(self) -> None:
        """Thread body: call converter_fn and emit signals."""
        self.progress.emit(10)
        self.status_update.emit("Starting conversion…")
        try:
            output_path = build_output_path(
                self.source_path,
                self.output_format,
                self.output_dir,
            )
            self.progress.emit(30)
            self.status_update.emit(f"Converting to {self.output_format.upper()}…")

            # Run the actual conversion
            result_path = self.converter_fn(
                self.source_path,
                str(output_path),
                self.output_format,
            )

            self.progress.emit(90)
            self.status_update.emit("Finalising…")
            self.progress.emit(100)
            self.finished.emit(True, result_path or str(output_path))

        except Exception as exc:
            self.finished.emit(False, str(exc))

    def cancel(self) -> None:
        self._cancelled = True
        self.requestInterruption()


# ---------------------------------------------------------------------------
# Conversion Manager
# ---------------------------------------------------------------------------

class ConversionManager(QObject):
    """
    Public API for triggering and tracking file conversions.

    Signals:
        conversion_started(str, str):    (source_path, target_format)
        conversion_progress(str, int):   (source_path, percent)
        conversion_complete(str, str):   (source_path, output_path)
        conversion_failed(str, str):     (source_path, error_message)
    """

    conversion_started  = Signal(str, str)
    conversion_progress = Signal(str, int)
    conversion_complete = Signal(str, str)
    conversion_failed   = Signal(str, str)

    def __init__(
        self,
        settings: SettingsManager,
        history:  HistoryManager,
        parent:   Optional[QObject] = None,
    ) -> None:
        super().__init__(parent)
        self._settings  = settings
        self._history   = history
        self._detector  = FileDetector()
        self._workers:  list[ConversionWorker] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def convert(
        self,
        source_path:   str,
        output_format: str,
        output_dir:    Optional[str] = None,
    ) -> Optional[ConversionWorker]:
        """
        Kick off an asynchronous conversion.

        Args:
            source_path:   Absolute path of the file to convert.
            output_format: Target format extension (e.g. 'mp4', 'pdf').
            output_dir:    Override output directory; uses settings default if None.

        Returns:
            The ConversionWorker thread, or None if the source format is unsupported.
        """
        if not os.path.exists(source_path):
            self.conversion_failed.emit(source_path, "Source file not found.")
            return None

        ext, category, fmt_info = self._detector.detect(source_path)
        if fmt_info is None:
            self.conversion_failed.emit(source_path, f"Unsupported file format: {ext}")
            return None

        # Resolve output directory
        out_dir = output_dir or self._settings.output_folder

        # Pick the right converter function
        converter_fn = self._get_converter(category, ext, output_format)
        if converter_fn is None:
            self.conversion_failed.emit(
                source_path,
                f"No converter available for {ext} → {output_format}"
            )
            return None

        # Record "pending" history entry
        src_size = os.path.getsize(source_path)
        history_id = self._history.add_entry(
            source_path=source_path,
            source_format=ext or "",
            output_path="",
            output_format=output_format,
            status="pending",
            file_size_in=src_size,
        )

        # Build and wire up worker
        worker = ConversionWorker(source_path, output_format, out_dir, converter_fn, self)
        start_time = time.monotonic()

        def on_progress(pct: int) -> None:
            self.conversion_progress.emit(source_path, pct)

        def on_finished(success: bool, result: str) -> None:
            elapsed_ms = int((time.monotonic() - start_time) * 1000)
            if success:
                out_size = os.path.getsize(result) if os.path.exists(result) else 0
                self._history.update_status(
                    history_id,
                    status="success",
                    file_size_out=out_size,
                    duration_ms=elapsed_ms,
                )
                # Prune old records
                self._history.prune_old(self._settings.max_history_entries)
                # Windows notification
                if self._settings.show_notifications:
                    notify(
                        "FileX — Conversion Complete",
                        f"{Path(source_path).name} → {output_format.upper()} ✔",
                    )
                self.conversion_complete.emit(source_path, result)
            else:
                self._history.update_status(
                    history_id,
                    status="failed",
                    error_msg=result,
                    duration_ms=elapsed_ms,
                )
                if self._settings.show_notifications:
                    notify(
                        "FileX — Conversion Failed",
                        f"{Path(source_path).name}: {result[:80]}",
                    )
                self.conversion_failed.emit(source_path, result)

            # Clean up finished worker
            if worker in self._workers:
                self._workers.remove(worker)

        worker.progress.connect(on_progress)
        worker.finished.connect(on_finished)

        self._workers.append(worker)
        self.conversion_started.emit(source_path, output_format)
        worker.start()
        return worker

    def cancel_all(self) -> None:
        """Cancel all running conversion workers."""
        for w in list(self._workers):
            w.cancel()

    # ------------------------------------------------------------------
    # Converter routing
    # ------------------------------------------------------------------

    def _get_converter(
        self, category: Optional[str], source_ext: Optional[str], target_ext: str
    ) -> Optional[Callable]:
        """
        Return the converter callable for the given category/format combo.
        Each converter is a function: (source_path, output_path, target_ext) → str
        """
        try:
            if category == "image":
                from converters.image_converter import ImageConverter
                return ImageConverter().convert

            elif category == "pdf" or (category == "document" and target_ext == "pdf"):
                from converters.pdf_converter import PdfConverter
                c = PdfConverter()
                # Route: pdf→X uses pdf_converter; X→pdf also goes through pdf_converter
                if source_ext == "pdf" or target_ext == "pdf":
                    return c.convert

            if category == "document":
                from converters.document_converter import DocumentConverter
                return DocumentConverter().convert

            elif category == "spreadsheet":
                from converters.spreadsheet_converter import SpreadsheetConverter
                return SpreadsheetConverter().convert

            elif category == "presentation":
                from converters.presentation_converter import PresentationConverter
                return PresentationConverter().convert

            elif category == "audio":
                from converters.audio_converter import AudioConverter
                return AudioConverter().convert

            elif category == "video":
                from converters.video_converter import VideoConverter
                return VideoConverter().convert

        except ImportError as e:
            # Return a lambda that raises the import error at runtime
            msg = str(e)
            return lambda s, o, t: (_ for _ in ()).throw(RuntimeError(f"Converter unavailable: {msg}"))

        return None
