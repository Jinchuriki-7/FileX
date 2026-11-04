"""
converters/image_converter.py
------------------------------
Converts raster images between formats using Pillow.
Supported: JPG, PNG, BMP, GIF, TIFF, WEBP, ICO, PDF (image-based).
"""

from pathlib import Path
from typing import Optional

from PIL import Image


# Pillow save format names differ from file extensions in some cases
_EXT_TO_PIL_FORMAT: dict[str, str] = {
    "jpg":  "JPEG",
    "jpeg": "JPEG",
    "png":  "PNG",
    "bmp":  "BMP",
    "gif":  "GIF",
    "tiff": "TIFF",
    "tif":  "TIFF",
    "webp": "WEBP",
    "ico":  "ICO",
    "pdf":  "PDF",
}

# Formats that require an RGB image (no alpha channel)
_RGB_ONLY_FORMATS = {"jpg", "jpeg", "bmp", "pdf"}

# Formats that support multiple frames (animated)
_ANIMATED_FORMATS = {"gif", "webp"}


class ImageConverter:
    """
    Pillow-backed image format converter.

    Usage::

        converter = ImageConverter()
        out_path = converter.convert("photo.png", "photo.jpg", "jpg")
    """

    def convert(
        self,
        source_path:  str,
        output_path:  str,
        target_ext:   str,
        quality:      int = 92,
        optimize:     bool = True,
    ) -> str:
        """
        Convert *source_path* to *output_path* in *target_ext* format.

        Args:
            source_path: Input image file.
            output_path: Desired output file path (extension already set by caller).
            target_ext:  Lowercase target extension without dot (e.g. 'png').
            quality:     JPEG/WEBP quality 1-95.
            optimize:    Enable Pillow's optimize flag where applicable.

        Returns:
            Absolute path of the written output file.

        Raises:
            ValueError: If the target format is not supported.
            OSError:    If the source file cannot be read.
        """
        target_ext = target_ext.lower().lstrip(".")
        pil_format = _EXT_TO_PIL_FORMAT.get(target_ext)
        if pil_format is None:
            raise ValueError(f"Unsupported image output format: {target_ext}")

        with Image.open(source_path) as img:
            # Handle animated GIF/WEBP — save with all frames
            if hasattr(img, "is_animated") and img.is_animated and target_ext in _ANIMATED_FORMATS:
                frames = self._extract_frames(img)
                frames[0].save(
                    output_path,
                    format=pil_format,
                    save_all=True,
                    append_images=frames[1:],
                    loop=0,
                    optimize=optimize,
                )
                return str(output_path)

            # Convert to appropriate colour mode
            converted = self._prepare_image(img, target_ext)

            # Save with format-specific options
            save_kwargs: dict = {"format": pil_format}
            if target_ext in ("jpg", "jpeg"):
                save_kwargs["quality"] = quality
                save_kwargs["optimize"] = optimize
            elif target_ext == "png":
                save_kwargs["optimize"] = optimize
            elif target_ext == "webp":
                save_kwargs["quality"] = quality
                save_kwargs["method"] = 4
            elif target_ext == "ico":
                # ICO supports multiple sizes; include common icon sizes
                save_kwargs["sizes"] = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
            elif target_ext == "pdf":
                save_kwargs["resolution"] = 100.0

            converted.save(output_path, **save_kwargs)

        return str(output_path)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _prepare_image(img: Image.Image, target_ext: str) -> Image.Image:
        """
        Convert colour mode as required by the target format.

        - RGBA → RGB for JPEG/BMP/PDF (drop alpha by compositing on white)
        - Palette/LA → RGBA or RGB as appropriate
        """
        # Ensure we're working with a decoded (non-lazy) copy
        img.load()

        if target_ext in _RGB_ONLY_FORMATS:
            if img.mode in ("RGBA", "LA", "P"):
                # Composite onto a white background
                background = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode == "P":
                    img = img.convert("RGBA")
                if img.mode in ("RGBA", "LA"):
                    background.paste(img, mask=img.split()[-1])
                    return background
            if img.mode != "RGB":
                return img.convert("RGB")
            return img

        # For PNG/GIF/WEBP/TIFF — keep alpha if present
        if img.mode == "P":
            return img.convert("RGBA")
        return img

    @staticmethod
    def _extract_frames(img: Image.Image) -> list[Image.Image]:
        """Extract all frames from an animated image."""
        frames = []
        try:
            while True:
                frames.append(img.copy())
                img.seek(img.tell() + 1)
        except EOFError:
            pass
        return frames
