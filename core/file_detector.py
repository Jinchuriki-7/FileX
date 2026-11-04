"""
core/file_detector.py
----------------------
Detects the type, category, and format of a file by inspecting its extension
and magic bytes (where available). Uses the FormatRegistry as source of truth.
"""

import os
import struct
from pathlib import Path
from typing import Optional, Tuple

from core.format_registry import FormatRegistry, FormatInfo


# ---------------------------------------------------------------------------
# Magic-byte signatures for common formats
# (offset, bytes) — offset is from the start of the file unless noted
# ---------------------------------------------------------------------------
_MAGIC: list[Tuple[int, bytes, str]] = [
    # offset, signature bytes, extension
    (0, b"\xff\xd8\xff",       "jpg"),
    (0, b"\x89PNG\r\n\x1a\n", "png"),
    (0, b"GIF87a",             "gif"),
    (0, b"GIF89a",             "gif"),
    (0, b"BM",                 "bmp"),
    (0, b"II\x2a\x00",        "tiff"),  # little-endian TIFF
    (0, b"MM\x00\x2a",        "tiff"),  # big-endian TIFF
    (0, b"RIFF",               "wav"),  # could also be AVI — disambiguated below
    (0, b"%PDF",               "pdf"),
    (0, b"PK\x03\x04",        "zip"),  # many Office formats are zip-based
    (0, b"\x1a\x45\xdf\xa3",  "mkv"),  # EBML (MKV/WebM)
    (0, b"ID3",                "mp3"),
    (0, b"\xff\xfb",          "mp3"),
    (0, b"\xff\xf3",          "mp3"),
    (0, b"\xff\xf2",          "mp3"),
    (0, b"fLaC",              "flac"),
    (0, b"OggS",              "ogg"),
    (4, b"ftyp",              "mp4"),   # bytes 4-7
    (0, b"\x00\x00\x00\x00",  "mp4"),  # generic mp4 — refined later
]

# RIFF sub-formats (bytes 8-11)
_RIFF_SUBTYPES: dict[bytes, str] = {
    b"WAVE": "wav",
    b"AVI ": "avi",
}

# zip-based Office formats — identified by content type in the zip
_ZIP_OFFICE_MAP: dict[str, str] = {
    "word/":          "docx",
    "xl/":            "xlsx",
    "ppt/":           "pptx",
    "odt":            "odt",
    "ods":            "ods",
    "odp":            "odp",
}


class FileDetector:
    """
    Determine the format and category of a file by extension + magic bytes.

    Usage::

        detector = FileDetector()
        result = detector.detect("/path/to/image.PNG")
        # result -> ("png", "image", <FormatInfo>)
    """

    def __init__(self) -> None:
        self._registry = FormatRegistry()

    # ------------------------------------------------------------------
    def detect(self, file_path: str) -> Tuple[Optional[str], Optional[str], Optional[FormatInfo]]:
        """
        Detect extension, category and FormatInfo for *file_path*.

        Returns:
            (ext, category, FormatInfo) where any element may be None if unknown.
        """
        path = Path(file_path)
        if not path.exists() or not path.is_file():
            return None, None, None

        # 1. Try magic-byte detection first (more reliable)
        ext = self._detect_by_magic(str(path))

        # 2. Fall back to file extension
        if ext is None:
            ext = path.suffix.lstrip(".").lower()

        # Alias jpeg → jpg for consistency
        if ext == "jpeg":
            ext = "jpg"
        if ext == "tif":
            ext = "tiff"
        if ext == "htm":
            ext = "html"

        fmt_info = self._registry.get_format(ext)
        category = fmt_info.category if fmt_info else None
        return ext, category, fmt_info

    # ------------------------------------------------------------------
    def is_supported(self, file_path: str) -> bool:
        """Return True if FileX knows how to convert this file."""
        _, _, fmt_info = self.detect(file_path)
        return fmt_info is not None and fmt_info.can_input

    # ------------------------------------------------------------------
    def get_output_formats(self, file_path: str) -> list[str]:
        """Return valid target extensions for *file_path*."""
        ext, _, _ = self.detect(file_path)
        if ext is None:
            return []
        return self._registry.get_output_formats(ext)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _read_header(file_path: str, num_bytes: int = 16) -> bytes:
        try:
            with open(file_path, "rb") as fh:
                return fh.read(num_bytes)
        except OSError:
            return b""

    def _detect_by_magic(self, file_path: str) -> Optional[str]:
        """Inspect the first few bytes of the file and return the extension."""
        header = self._read_header(file_path, 32)
        if not header:
            return None

        # RIFF disambiguation
        if header[:4] == b"RIFF" and len(header) >= 12:
            sub = header[8:12]
            return _RIFF_SUBTYPES.get(sub, "wav")

        # ftyp box (MP4/M4A/MOV) at offset 4
        if len(header) >= 8 and header[4:8] == b"ftyp":
            brand = header[8:12]
            if brand in (b"qt  ", b"mov "):
                return "mov"
            if brand in (b"M4A ", b"M4B ", b"M4P "):
                return "m4a"
            return "mp4"

        # zip-based Office / ODF
        if header[:4] == b"PK\x03\x04":
            return self._detect_zip_office(file_path)

        # Remaining magic signatures
        for offset, sig, ext in _MAGIC:
            if offset == 0 and header[:len(sig)] == sig:
                return ext
            elif offset > 0 and header[offset:offset + len(sig)] == sig:
                return ext

        return None

    @staticmethod
    def _detect_zip_office(file_path: str) -> str:
        """Peek inside a ZIP archive to detect Office/ODF type."""
        try:
            import zipfile
            with zipfile.ZipFile(file_path, "r") as zf:
                names = zf.namelist()
                names_joined = "/".join(names).lower()
                for key, ext in _ZIP_OFFICE_MAP.items():
                    if key in names_joined:
                        return ext
        except Exception:
            pass
        return "zip"
