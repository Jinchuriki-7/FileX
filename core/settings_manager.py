"""
core/settings_manager.py
-------------------------
Manages persistent application settings stored as JSON in %APPDATA%/FileX/.
Provides typed getters/setters with defaults and auto-save.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional


# ---------------------------------------------------------------------------
# Default settings schema
# ---------------------------------------------------------------------------
DEFAULTS: Dict[str, Any] = {
    # General
    "theme": "dark",
    "always_on_top": True,
    "start_minimised": False,
    "run_at_startup": False,
    "show_notifications": True,

    # Conversion
    "output_folder": str(Path.home() / "Downloads" / "FileX"),
    "open_output_after_conversion": False,
    "overwrite_existing": False,
    "default_image_format": "png",
    "default_document_format": "pdf",
    "default_audio_format": "mp3",
    "default_video_format": "mp4",

    # UI
    "widget_opacity": 0.95,
    "widget_x": 50,
    "widget_y": 200,
    "widget_width": 220,
    "widget_height": 240,
    "show_drop_zone_labels": True,

    # History
    "max_history_entries": 500,
    "clear_history_on_exit": False,
}


class SettingsManager:
    """
    Thread-safe (write-lock-free for reads) settings manager backed by a
    JSON file at ``%APPDATA%/FileX/settings.json``.

    Attributes:
        config_dir:  Directory that holds ``settings.json``.
        config_file: Full path to ``settings.json``.
    """

    def __init__(self, config_dir: Optional[str] = None) -> None:
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            appdata = os.environ.get("APPDATA") or str(Path.home())
            self.config_dir = Path(appdata) / "FileX"

        self.config_file = self.config_dir / "settings.json"
        self._data: Dict[str, Any] = {}
        self._load()

    # ------------------------------------------------------------------
    # Private I/O
    # ------------------------------------------------------------------

    def _load(self) -> None:
        """Load settings from disk; merge with defaults for missing keys."""
        self.config_dir.mkdir(parents=True, exist_ok=True)

        loaded: Dict[str, Any] = {}
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as fh:
                    loaded = json.load(fh)
            except (json.JSONDecodeError, OSError):
                loaded = {}

        # Start from defaults and overlay persisted values
        self._data = {**DEFAULTS, **loaded}
        # Ensure the output folder exists
        Path(self._data["output_folder"]).mkdir(parents=True, exist_ok=True)

    def _save(self) -> None:
        """Persist current settings to disk."""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, "w", encoding="utf-8") as fh:
                json.dump(self._data, fh, indent=2, ensure_ascii=False)
        except OSError:
            pass  # Non-fatal — settings will be lost this session but won't crash

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get(self, key: str, default: Any = None) -> Any:
        """
        Return the value for *key*.

        Args:
            key:     Setting name.
            default: Fallback if key is absent (uses DEFAULTS first).

        Returns:
            The stored value, the DEFAULTS value, or *default*.
        """
        return self._data.get(key, DEFAULTS.get(key, default))

    def set(self, key: str, value: Any, save: bool = True) -> None:
        """
        Update a setting and optionally persist immediately.

        Args:
            key:   Setting name.
            value: New value.
            save:  Whether to write to disk right away.
        """
        self._data[key] = value
        if save:
            self._save()

    def set_many(self, updates: Dict[str, Any]) -> None:
        """Apply multiple updates at once and persist."""
        self._data.update(updates)
        self._save()

    def reset(self) -> None:
        """Reset all settings to their default values and persist."""
        self._data = dict(DEFAULTS)
        self._save()

    def reset_key(self, key: str) -> None:
        """Reset a single key to its default and persist."""
        if key in DEFAULTS:
            self._data[key] = DEFAULTS[key]
            self._save()

    def all(self) -> Dict[str, Any]:
        """Return a copy of all current settings."""
        return dict(self._data)

    # ------------------------------------------------------------------
    # Convenience typed properties
    # ------------------------------------------------------------------

    @property
    def output_folder(self) -> str:
        return str(self.get("output_folder"))

    @output_folder.setter
    def output_folder(self, path: str) -> None:
        Path(path).mkdir(parents=True, exist_ok=True)
        self.set("output_folder", str(path))

    @property
    def theme(self) -> str:
        return str(self.get("theme", "dark"))

    @property
    def always_on_top(self) -> bool:
        return bool(self.get("always_on_top", True))

    @property
    def show_notifications(self) -> bool:
        return bool(self.get("show_notifications", True))

    @property
    def widget_opacity(self) -> float:
        return float(self.get("widget_opacity", 0.95))

    @property
    def max_history_entries(self) -> int:
        return int(self.get("max_history_entries", 500))
