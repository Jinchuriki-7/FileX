"""
converters/audio_converter.py
------------------------------
Converts audio files between formats using pydub (which wraps FFmpeg).

Supported input:  MP3, WAV, AAC, FLAC, OGG, M4A, WMA
Supported output: MP3, WAV, AAC, FLAC, OGG

Requires FFmpeg to be installed and available on the system PATH.
"""

from pathlib import Path


# pydub ↔ FFmpeg format name overrides
_EXT_TO_PYDUB: dict[str, str] = {
    "mp3":  "mp3",
    "wav":  "wav",
    "aac":  "aac",
    "flac": "flac",
    "ogg":  "ogg",
    "m4a":  "mp4",    # pydub uses 'mp4' codec container for m4a
    "wma":  "asf",    # pydub/ffmpeg calls WMA 'asf'
}

# Export format names for pydub's export() method
_EXT_TO_EXPORT_FORMAT: dict[str, str] = {
    "mp3":  "mp3",
    "wav":  "wav",
    "aac":  "adts",   # AAC in raw ADTS container
    "flac": "flac",
    "ogg":  "ogg",
}


class AudioConverter:
    """
    pydub-based audio format converter.

    Usage::

        c = AudioConverter()
        c.convert("song.flac", "song.mp3", "mp3")
    """

    def convert(
        self,
        source_path: str,
        output_path: str,
        target_ext:  str,
        bitrate:     str = "192k",
    ) -> str:
        """
        Convert *source_path* to *output_path* in *target_ext* format.

        Args:
            source_path: Input audio file path.
            output_path: Desired output path.
            target_ext:  Target format extension (e.g. 'mp3', 'flac').
            bitrate:     Output bitrate for lossy formats (default '192k').

        Returns:
            Absolute path of the written output file.

        Raises:
            ValueError: Unsupported target format.
            RuntimeError: FFmpeg not found or conversion error.
        """
        from pydub import AudioSegment

        src_ext = Path(source_path).suffix.lstrip(".").lower()
        tgt = target_ext.lower().lstrip(".")

        if tgt not in _EXT_TO_EXPORT_FORMAT:
            raise ValueError(
                f"Unsupported audio output format: {tgt}. "
                f"Supported: {', '.join(_EXT_TO_EXPORT_FORMAT)}"
            )

        # Determine pydub import format
        import_fmt = _EXT_TO_PYDUB.get(src_ext, src_ext)

        try:
            audio = AudioSegment.from_file(source_path, format=import_fmt)
        except Exception as exc:
            raise RuntimeError(
                f"Failed to read audio file '{source_path}': {exc}\n"
                "Ensure FFmpeg is installed and on your system PATH."
            ) from exc

        export_fmt = _EXT_TO_EXPORT_FORMAT[tgt]

        # Build export kwargs
        export_kwargs: dict = {"format": export_fmt}

        # Apply bitrate only for lossy formats
        if tgt in ("mp3", "aac", "ogg"):
            export_kwargs["bitrate"] = bitrate

        # For MP3: include ID3 tags if available
        if tgt == "mp3":
            tags = {}
            # Try to copy metadata from source if pydub exposes it
            if hasattr(audio, "metadata") and audio.metadata:
                tags = audio.metadata
            if tags:
                export_kwargs["tags"] = tags

        try:
            audio.export(output_path, **export_kwargs)
        except Exception as exc:
            raise RuntimeError(
                f"Audio export failed: {exc}\n"
                "Ensure FFmpeg is installed and on your system PATH."
            ) from exc

        return output_path

    # ------------------------------------------------------------------
    # Utility: get audio info
    # ------------------------------------------------------------------

    @staticmethod
    def get_info(source_path: str) -> dict:
        """
        Return basic metadata about an audio file.

        Returns:
            dict with keys: duration_sec, channels, frame_rate, sample_width
        """
        from pydub import AudioSegment
        src_ext = Path(source_path).suffix.lstrip(".").lower()
        import_fmt = _EXT_TO_PYDUB.get(src_ext, src_ext)
        audio = AudioSegment.from_file(source_path, format=import_fmt)
        return {
            "duration_sec":  len(audio) / 1000.0,
            "channels":      audio.channels,
            "frame_rate":    audio.frame_rate,
            "sample_width":  audio.sample_width,
        }
