"""
converters/__init__.py
-----------------------
Converters package for FileX.

Each sub-module exposes a class with a `convert(source, output, target_ext)` method
that performs the actual file conversion and returns the output path string.

Available converters:
  - ImageConverter       — Pillow-based raster image conversion
  - PdfConverter         — PDF ↔ doc/image/text via pypdf + reportlab
  - DocumentConverter    — DOCX/TXT/HTML/MD/ODT via python-docx + markdown
  - SpreadsheetConverter — XLSX/CSV/ODS via openpyxl + pandas
  - PresentationConverter— PPTX → PDF/images via python-pptx
  - AudioConverter       — MP3/WAV/AAC/FLAC/OGG via pydub + ffmpeg
  - VideoConverter       — MP4/AVI/MKV/MOV via ffmpeg-python
"""
