"""
core/format_registry.py
------------------------
Central registry of every file format FileX understands:
  - Which category it belongs to (image / pdf / document / spreadsheet /
    presentation / audio / video)
  - What output formats it can be converted TO
  - Human-readable display labels
  - File-extension → category mapping for quick lookup
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class FormatInfo:
    """Metadata for a single file format."""
    ext: str                   # Lowercase extension without dot, e.g. 'mp4'
    label: str                 # Human-readable name, e.g. 'MPEG-4 Video'
    category: str              # One of: image|pdf|document|spreadsheet|presentation|audio|video
    mime_type: str             # Primary MIME type
    can_input: bool = True     # Can this format be used as a conversion SOURCE?
    can_output: bool = True    # Can this format be used as a conversion TARGET?


@dataclass
class CategoryInfo:
    """Groups of formats belonging to the same conversion category."""
    name: str                        # e.g. 'image'
    label: str                       # Human-readable, e.g. 'Image'
    icon: str                        # Emoji or icon name used in UI
    formats: List[FormatInfo] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Format definitions
# ---------------------------------------------------------------------------

_FORMATS: List[FormatInfo] = [
    # ---- Images ------------------------------------------------------------
    FormatInfo("jpg",  "JPEG Image",        "image",        "image/jpeg"),
    FormatInfo("jpeg", "JPEG Image",        "image",        "image/jpeg"),
    FormatInfo("png",  "PNG Image",         "image",        "image/png"),
    FormatInfo("bmp",  "Bitmap Image",      "image",        "image/bmp"),
    FormatInfo("gif",  "GIF Image",         "image",        "image/gif"),
    FormatInfo("tiff", "TIFF Image",        "image",        "image/tiff"),
    FormatInfo("tif",  "TIFF Image",        "image",        "image/tiff"),
    FormatInfo("webp", "WebP Image",        "image",        "image/webp"),
    FormatInfo("ico",  "Icon File",         "image",        "image/x-icon"),

    # ---- PDF ---------------------------------------------------------------
    FormatInfo("pdf",  "PDF Document",      "pdf",          "application/pdf"),

    # ---- Documents ---------------------------------------------------------
    FormatInfo("docx", "Word Document",     "document",     "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
    FormatInfo("doc",  "Word 97-2003",      "document",     "application/msword",          can_output=False),
    FormatInfo("txt",  "Plain Text",        "document",     "text/plain"),
    FormatInfo("html", "HTML File",         "document",     "text/html"),
    FormatInfo("htm",  "HTML File",         "document",     "text/html"),
    FormatInfo("md",   "Markdown",          "document",     "text/markdown"),
    FormatInfo("odt",  "OpenDocument Text", "document",     "application/vnd.oasis.opendocument.text"),
    FormatInfo("rtf",  "Rich Text Format",  "document",     "application/rtf"),

    # ---- Spreadsheets ------------------------------------------------------
    FormatInfo("xlsx", "Excel Workbook",    "spreadsheet",  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
    FormatInfo("xls",  "Excel 97-2003",     "spreadsheet",  "application/vnd.ms-excel",    can_output=False),
    FormatInfo("csv",  "CSV File",          "spreadsheet",  "text/csv"),
    FormatInfo("ods",  "OpenDocument Sheet","spreadsheet",  "application/vnd.oasis.opendocument.spreadsheet"),

    # ---- Presentations -----------------------------------------------------
    FormatInfo("pptx", "PowerPoint",        "presentation", "application/vnd.openxmlformats-officedocument.presentationml.presentation"),
    FormatInfo("ppt",  "PowerPoint 97-2003","presentation", "application/vnd.ms-powerpoint", can_output=False),

    # ---- Audio -------------------------------------------------------------
    FormatInfo("mp3",  "MP3 Audio",         "audio",        "audio/mpeg"),
    FormatInfo("wav",  "WAV Audio",         "audio",        "audio/wav"),
    FormatInfo("aac",  "AAC Audio",         "audio",        "audio/aac"),
    FormatInfo("flac", "FLAC Audio",        "audio",        "audio/flac"),
    FormatInfo("ogg",  "OGG Audio",         "audio",        "audio/ogg"),
    FormatInfo("m4a",  "M4A Audio",         "audio",        "audio/mp4",                   can_output=False),
    FormatInfo("wma",  "WMA Audio",         "audio",        "audio/x-ms-wma",              can_output=False),

    # ---- Video -------------------------------------------------------------
    FormatInfo("mp4",  "MPEG-4 Video",      "video",        "video/mp4"),
    FormatInfo("avi",  "AVI Video",         "video",        "video/x-msvideo"),
    FormatInfo("mkv",  "Matroska Video",    "video",        "video/x-matroska"),
    FormatInfo("mov",  "QuickTime Video",   "video",        "video/quicktime"),
    FormatInfo("wmv",  "WMV Video",         "video",        "video/x-ms-wmv"),
    FormatInfo("flv",  "Flash Video",       "video",        "video/x-flv",                 can_output=False),
    FormatInfo("webm", "WebM Video",        "video",        "video/webm"),
]


# ---------------------------------------------------------------------------
# Output format maps — ext → list of target exts
# ---------------------------------------------------------------------------

_OUTPUT_MAP: Dict[str, List[str]] = {
    # Images → any raster format
    "jpg":  ["png", "bmp", "gif", "tiff", "webp", "ico", "pdf"],
    "jpeg": ["png", "bmp", "gif", "tiff", "webp", "ico", "pdf"],
    "png":  ["jpg", "bmp", "gif", "tiff", "webp", "ico", "pdf"],
    "bmp":  ["jpg", "png", "gif", "tiff", "webp"],
    "gif":  ["jpg", "png", "bmp", "tiff", "webp"],
    "tiff": ["jpg", "png", "bmp", "gif", "webp"],
    "tif":  ["jpg", "png", "bmp", "gif", "webp"],
    "webp": ["jpg", "png", "bmp", "gif", "tiff"],
    "ico":  ["png", "jpg", "bmp"],

    # PDF
    "pdf":  ["docx", "txt", "png", "jpg"],

    # Documents
    "docx": ["pdf", "txt", "html", "md", "odt"],
    "doc":  ["pdf", "txt", "html", "docx"],
    "txt":  ["pdf", "docx", "html", "md"],
    "html": ["pdf", "docx", "txt", "md"],
    "htm":  ["pdf", "docx", "txt", "md"],
    "md":   ["html", "pdf", "docx", "txt"],
    "odt":  ["pdf", "docx", "txt", "html"],
    "rtf":  ["pdf", "docx", "txt"],

    # Spreadsheets
    "xlsx": ["csv", "pdf", "ods"],
    "xls":  ["xlsx", "csv", "pdf"],
    "csv":  ["xlsx", "pdf", "ods"],
    "ods":  ["xlsx", "csv", "pdf"],

    # Presentations
    "pptx": ["pdf"],
    "ppt":  ["pptx", "pdf"],

    # Audio
    "mp3":  ["wav", "aac", "flac", "ogg"],
    "wav":  ["mp3", "aac", "flac", "ogg"],
    "aac":  ["mp3", "wav", "flac", "ogg"],
    "flac": ["mp3", "wav", "aac", "ogg"],
    "ogg":  ["mp3", "wav", "aac", "flac"],
    "m4a":  ["mp3", "wav", "aac", "flac", "ogg"],
    "wma":  ["mp3", "wav", "aac", "flac", "ogg"],

    # Video
    "mp4":  ["avi", "mkv", "mov", "wmv", "webm", "gif"],
    "avi":  ["mp4", "mkv", "mov", "wmv", "webm"],
    "mkv":  ["mp4", "avi", "mov", "wmv", "webm"],
    "mov":  ["mp4", "avi", "mkv", "wmv", "webm"],
    "wmv":  ["mp4", "avi", "mkv", "mov", "webm"],
    "flv":  ["mp4", "avi", "mkv", "mov"],
    "webm": ["mp4", "avi", "mkv", "mov"],
}


# ---------------------------------------------------------------------------
# FormatRegistry class
# ---------------------------------------------------------------------------

class FormatRegistry:
    """
    Single source of truth for all file format metadata.

    Usage::

        reg = FormatRegistry()
        info = reg.get_format("mp4")
        targets = reg.get_output_formats("mp4")  # ['avi', 'mkv', …]
    """

    def __init__(self) -> None:
        # Build lookup tables
        self._by_ext: Dict[str, FormatInfo] = {}
        for fmt in _FORMATS:
            self._by_ext[fmt.ext] = fmt

        # Build category groupings
        self._categories: Dict[str, CategoryInfo] = {
            "image":        CategoryInfo("image",        "Image",        "🖼️"),
            "pdf":          CategoryInfo("pdf",          "PDF",          "📄"),
            "document":     CategoryInfo("document",     "Document",     "📝"),
            "spreadsheet":  CategoryInfo("spreadsheet",  "Spreadsheet",  "📊"),
            "presentation": CategoryInfo("presentation", "Presentation", "📽️"),
            "audio":        CategoryInfo("audio",        "Audio",        "🎵"),
            "video":        CategoryInfo("video",        "Video",        "🎬"),
        }
        for fmt in _FORMATS:
            if fmt.category in self._categories:
                self._categories[fmt.category].formats.append(fmt)

    # ------------------------------------------------------------------
    def get_format(self, ext: str) -> Optional[FormatInfo]:
        """Return FormatInfo for a given extension (case-insensitive), or None."""
        return self._by_ext.get(ext.lower().lstrip("."))

    def get_category(self, ext: str) -> Optional[str]:
        """Return the category name for the given extension, or None."""
        fmt = self.get_format(ext)
        return fmt.category if fmt else None

    def get_output_formats(self, source_ext: str) -> List[str]:
        """
        Return the list of valid target extensions for *source_ext*.

        Args:
            source_ext: Source file extension (e.g. 'mp4', '.MP4').

        Returns:
            List of lowercase target extensions (may be empty).
        """
        return _OUTPUT_MAP.get(source_ext.lower().lstrip("."), [])

    def get_output_format_infos(self, source_ext: str) -> List[FormatInfo]:
        """Return FormatInfo objects for every valid output format."""
        return [
            self._by_ext[ext]
            for ext in self.get_output_formats(source_ext)
            if ext in self._by_ext
        ]

    def all_input_extensions(self) -> List[str]:
        """Return every extension that can be used as a conversion source."""
        return [f.ext for f in _FORMATS if f.can_input]

    def category_info(self, category: str) -> Optional[CategoryInfo]:
        """Return CategoryInfo for a category name."""
        return self._categories.get(category)

    def all_categories(self) -> List[CategoryInfo]:
        """Return all CategoryInfo objects."""
        return list(self._categories.values())

    def is_supported(self, ext: str) -> bool:
        """Return True if the extension is recognised by FileX."""
        return ext.lower().lstrip(".") in self._by_ext
