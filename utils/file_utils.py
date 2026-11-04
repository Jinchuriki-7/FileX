"""
utils/file_utils.py
-------------------
General-purpose file and path utility helpers used across FileX.
"""

import os
import re
import shutil
import hashlib
import mimetypes
from pathlib import Path
from datetime import datetime
from typing import Optional


# ---------------------------------------------------------------------------
# Human-readable size formatting
# ---------------------------------------------------------------------------

def human_readable_size(num_bytes: int) -> str:
    """Convert a byte count to a human-readable string (e.g. '3.4 MB')."""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(num_bytes) < 1024.0:
            return f"{num_bytes:3.1f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.1f} PB"


# ---------------------------------------------------------------------------
# Output path helpers
# ---------------------------------------------------------------------------

def build_output_path(
    source_path: str,
    target_ext: str,
    output_dir: Optional[str] = None,
    suffix: str = ""
) -> Path:
    """
    Build a unique output file path for the converted file.

    Args:
        source_path: Absolute path of the source file.
        target_ext:  Target extension WITHOUT the leading dot (e.g. 'mp4').
        output_dir:  Directory to save the output. Defaults to source file's directory.
        suffix:      Optional suffix to append before the extension (e.g. '_converted').

    Returns:
        A Path object guaranteed not to overwrite an existing file.
    """
    src = Path(source_path)
    out_dir = Path(output_dir) if output_dir else src.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    # Sanitise extension
    ext = target_ext.lstrip(".").lower()
    stem = src.stem + suffix
    candidate = out_dir / f"{stem}.{ext}"

    # Avoid overwriting existing files by appending a counter
    counter = 1
    while candidate.exists():
        candidate = out_dir / f"{stem}_{counter}.{ext}"
        counter += 1

    return candidate


# ---------------------------------------------------------------------------
# Extension / MIME helpers
# ---------------------------------------------------------------------------

def get_extension(file_path: str) -> str:
    """Return the lowercase extension of a file (without the dot)."""
    return Path(file_path).suffix.lstrip(".").lower()


def get_mime_type(file_path: str) -> str:
    """Return the MIME type of the file (best-guess via mimetypes)."""
    mime, _ = mimetypes.guess_type(file_path)
    return mime or "application/octet-stream"


def is_valid_file(file_path: str) -> bool:
    """Return True if the path points to an existing, readable file."""
    p = Path(file_path)
    return p.exists() and p.is_file() and os.access(str(p), os.R_OK)


# ---------------------------------------------------------------------------
# Safe filename creation
# ---------------------------------------------------------------------------

def sanitise_filename(name: str) -> str:
    """
    Strip characters that are illegal in Windows file names and limit length.

    Args:
        name: Proposed file name (stem only, no extension).

    Returns:
        A safe, non-empty filename stem.
    """
    # Remove illegal Windows filename characters
    name = re.sub(r'[\\/:*?"<>|]', "_", name)
    # Collapse multiple spaces / underscores
    name = re.sub(r"[\s_]+", "_", name).strip("_")
    # Limit length (Windows MAX_PATH minus room for dir and ext)
    name = name[:200] or "converted_file"
    return name


# ---------------------------------------------------------------------------
# File checksum
# ---------------------------------------------------------------------------

def md5_checksum(file_path: str, chunk_size: int = 65536) -> str:
    """
    Compute the MD5 hex-digest of a file (useful for de-dup checks).

    Args:
        file_path:  Path to the file.
        chunk_size: Read chunk size in bytes.

    Returns:
        Hex-encoded MD5 string.
    """
    hasher = hashlib.md5()
    with open(file_path, "rb") as fh:
        for chunk in iter(lambda: fh.read(chunk_size), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


# ---------------------------------------------------------------------------
# Directory helpers
# ---------------------------------------------------------------------------

def ensure_dir(directory: str) -> Path:
    """Create *directory* (and all parents) if it does not exist."""
    p = Path(directory)
    p.mkdir(parents=True, exist_ok=True)
    return p


def open_file(file_path: str) -> bool:
    """
    Open a file with the default associated application on Windows.

    Args:
        file_path: Path to the file to open.

    Returns:
        True if launched successfully, False otherwise.
    """
    try:
        p = Path(file_path)
        if not p.exists():
            return False
        os.startfile(str(p.resolve()))
        return True
    except Exception:
        try:
            import subprocess
            subprocess.Popen(["explorer.exe", str(Path(file_path).resolve())])
            return True
        except Exception:
            return False


def open_containing_folder(target_path: str) -> bool:
    """
    Open the containing directory in Windows Explorer.
    If target_path is a file, selects/highlights the file in Explorer.

    Args:
        target_path: Path to a file or directory.

    Returns:
        True if opened successfully, False otherwise.
    """
    try:
        p = Path(target_path).resolve()
        if p.is_file():
            import subprocess
            subprocess.Popen(["explorer.exe", f"/select,{str(p)}"])
            return True
        elif p.is_dir():
            os.startfile(str(p))
            return True
        elif p.parent.exists():
            os.startfile(str(p.parent))
            return True
        return False
    except Exception:
        try:
            p = Path(target_path).resolve()
            folder = str(p.parent if p.is_file() else p)
            os.startfile(folder)
            return True
        except Exception:
            return False


def open_in_explorer(path: str) -> None:
    """Open the containing folder in Windows Explorer and select the file."""
    open_containing_folder(path)


# ---------------------------------------------------------------------------
# Timestamp helper
# ---------------------------------------------------------------------------

def timestamp_string() -> str:
    """Return a filesystem-safe timestamp string: 'YYYYMMDD_HHMMSS'."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")
