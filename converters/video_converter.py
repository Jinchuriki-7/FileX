"""
converters/video_converter.py
------------------------------
Converts video files between formats using ffmpeg-python.

Supported input:  MP4, AVI, MKV, MOV, WMV, FLV, WEBM
Supported output: MP4, AVI, MKV, MOV, WMV, WEBM, GIF

Requires FFmpeg to be installed and available on the system PATH.
"""

from pathlib import Path


# Quality presets
_CRF_DEFAULT = 23           # H.264 CRF (lower = better quality)
_GIF_FPS     = 12           # FPS for GIF output
_GIF_WIDTH   = 480          # Width for GIF (maintain aspect ratio)


class VideoConverter:
    """
    ffmpeg-python-based video format converter.

    Usage::

        c = VideoConverter()
        c.convert("clip.avi", "clip.mp4", "mp4")
        c.convert("clip.mp4", "animation.gif", "gif")
    """

    def convert(
        self,
        source_path: str,
        output_path: str,
        target_ext:  str,
        crf:         int = _CRF_DEFAULT,
        preset:      str = "medium",
    ) -> str:
        """
        Convert *source_path* to *output_path* in *target_ext* format.

        Args:
            source_path: Input video file path.
            output_path: Desired output path.
            target_ext:  Target format extension (e.g. 'mp4', 'gif').
            crf:         Constant rate factor for H.264 (18-28 typical).
            preset:      FFmpeg encoding preset ('ultrafast'…'veryslow').

        Returns:
            Absolute output file path.

        Raises:
            ValueError:  Unsupported target format.
            RuntimeError: FFmpeg not found or conversion error.
        """
        tgt = target_ext.lower().lstrip(".")

        if tgt == "gif":
            return self._to_gif(source_path, output_path)
        else:
            return self._transcode(source_path, output_path, tgt, crf, preset)

    # ------------------------------------------------------------------
    # Generic transcode (video + audio)
    # ------------------------------------------------------------------

    def _transcode(
        self,
        source: str,
        output: str,
        target_ext: str,
        crf: int,
        preset: str,
    ) -> str:
        import ffmpeg

        # Format-specific codec choices
        vcodec, acodec = self._pick_codecs(target_ext)

        try:
            (
                ffmpeg
                .input(source)
                .output(
                    output,
                    vcodec=vcodec,
                    acodec=acodec,
                    crf=crf,
                    preset=preset if vcodec == "libx264" else None,
                    **{"movflags": "+faststart"} if target_ext == "mp4" else {},
                )
                .overwrite_output()
                .run(quiet=True)
            )
        except ffmpeg.Error as exc:
            stderr = exc.stderr.decode("utf-8", errors="replace") if exc.stderr else ""
            raise RuntimeError(
                f"FFmpeg transcoding failed: {stderr[:500]}\n"
                "Ensure FFmpeg is installed and on your system PATH."
            ) from exc

        return output

    # ------------------------------------------------------------------
    # Video → GIF
    # ------------------------------------------------------------------

    def _to_gif(self, source: str, output: str) -> str:
        """Convert video to an optimised animated GIF using FFmpeg palette."""
        import ffmpeg
        import tempfile, os

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tf:
            palette_path = tf.name

        try:
            # Step 1: generate palette for better colour quality
            (
                ffmpeg
                .input(source)
                .filter("fps", _GIF_FPS)
                .filter("scale", _GIF_WIDTH, -1, flags="lanczos")
                .filter("palettegen")
                .output(palette_path)
                .overwrite_output()
                .run(quiet=True)
            )

            # Step 2: render GIF using palette
            in_stream  = ffmpeg.input(source)
            palette_in = ffmpeg.input(palette_path)
            (
                ffmpeg
                .filter(
                    [in_stream.filter("fps", _GIF_FPS)
                              .filter("scale", _GIF_WIDTH, -1, flags="lanczos"),
                     palette_in],
                    "paletteuse"
                )
                .output(output)
                .overwrite_output()
                .run(quiet=True)
            )
        except ffmpeg.Error as exc:
            stderr = exc.stderr.decode("utf-8", errors="replace") if exc.stderr else ""
            raise RuntimeError(
                f"GIF conversion failed: {stderr[:500]}\n"
                "Ensure FFmpeg is installed and on your system PATH."
            ) from exc
        finally:
            if os.path.exists(palette_path):
                os.unlink(palette_path)

        return output

    # ------------------------------------------------------------------
    # Codec selection per output format
    # ------------------------------------------------------------------

    @staticmethod
    def _pick_codecs(target_ext: str) -> tuple[str, str]:
        """
        Return (video_codec, audio_codec) for the given output container.
        """
        mapping = {
            "mp4":  ("libx264", "aac"),
            "avi":  ("libx264", "mp3"),
            "mkv":  ("libx264", "aac"),
            "mov":  ("libx264", "aac"),
            "wmv":  ("wmv2",    "wmav2"),
            "webm": ("libvpx-vp9", "libopus"),
            "flv":  ("flv",     "mp3"),
        }
        return mapping.get(target_ext, ("libx264", "aac"))

    # ------------------------------------------------------------------
    # Utility: probe video info
    # ------------------------------------------------------------------

    @staticmethod
    def probe(source_path: str) -> dict:
        """
        Return FFmpeg probe metadata for a video file.

        Returns:
            dict with format and streams info.
        """
        import ffmpeg
        try:
            return ffmpeg.probe(source_path)
        except ffmpeg.Error as exc:
            raise RuntimeError(f"FFmpeg probe failed: {exc}") from exc
