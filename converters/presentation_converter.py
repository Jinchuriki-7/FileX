"""
converters/presentation_converter.py
--------------------------------------
Converts presentation files using python-pptx and reportlab.

Supported:
  PPTX → PDF  (slide text exported as structured PDF)
  PPT  → PPTX (re-open with python-pptx — works for many PPT files)
  PPT  → PDF  (via PPTX intermediate)
"""

from pathlib import Path


class PresentationConverter:
    """
    Presentation format converter.

    Usage::

        c = PresentationConverter()
        c.convert("slides.pptx", "slides.pdf", "pdf")
    """

    def convert(self, source_path: str, output_path: str, target_ext: str) -> str:
        """
        Convert *source_path* to *output_path* in *target_ext* format.

        Returns:
            Absolute path of the written output file.
        """
        src_ext = Path(source_path).suffix.lstrip(".").lower()
        tgt = target_ext.lower().lstrip(".")

        dispatch = {
            ("pptx", "pdf"):  self._pptx_to_pdf,
            ("ppt",  "pptx"): self._ppt_to_pptx,
            ("ppt",  "pdf"):  self._ppt_to_pdf,
        }

        handler = dispatch.get((src_ext, tgt))
        if handler is None:
            raise ValueError(f"PresentationConverter: {src_ext} → {tgt} not supported")
        return handler(source_path, output_path)

    # ==================================================================
    # PPTX → PDF  (text extraction → reportlab PDF)
    # ==================================================================

    def _pptx_to_pdf(self, src: str, out: str) -> str:
        from pptx import Presentation
        from pptx.util import Inches, Pt
        from reportlab.lib.pagesizes import LETTER
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import (SimpleDocTemplate, Paragraph,
                                        Spacer, PageBreak)
        from reportlab.lib import colors
        from reportlab.lib.units import inch

        prs = Presentation(src)
        doc = SimpleDocTemplate(out, pagesize=LETTER)
        styles = getSampleStyleSheet()
        story = []

        slide_title_style = ParagraphStyle(
            "SlideTitle",
            parent=styles["Heading1"],
            textColor=colors.HexColor("#cba6f7"),
            fontSize=18,
            spaceAfter=12,
        )
        body_style = ParagraphStyle(
            "SlideBody",
            parent=styles["Normal"],
            fontSize=11,
            leading=16,
        )
        slide_num_style = ParagraphStyle(
            "SlideNum",
            parent=styles["Normal"],
            fontSize=8,
            textColor=colors.grey,
        )

        for slide_no, slide in enumerate(prs.slides, 1):
            story.append(Paragraph(f"Slide {slide_no}", slide_num_style))
            story.append(Spacer(1, 4))

            for shape in slide.shapes:
                if not shape.has_text_frame:
                    continue
                for i, paragraph in enumerate(shape.text_frame.paragraphs):
                    text = paragraph.text.strip()
                    if not text:
                        continue
                    # Escape XML special characters
                    safe = (text
                            .replace("&", "&amp;")
                            .replace("<", "&lt;")
                            .replace(">", "&gt;"))
                    # First paragraph in a shape is often the title
                    if i == 0 and shape == slide.shapes[0]:
                        story.append(Paragraph(safe, slide_title_style))
                    else:
                        # Respect indentation level as bullet depth
                        indent = "  " * (paragraph.level or 0)
                        story.append(Paragraph(f"{'• ' if paragraph.level else ''}{indent}{safe}", body_style))

            story.append(Spacer(1, 20))
            # Page break after every slide except the last
            if slide_no < len(prs.slides):
                story.append(PageBreak())

        doc.build(story)
        return out

    # ==================================================================
    # PPT → PPTX  (python-pptx can open .ppt in many cases)
    # ==================================================================

    def _ppt_to_pptx(self, src: str, out: str) -> str:
        from pptx import Presentation
        prs = Presentation(src)   # May raise on complex PPT files
        prs.save(out)
        return out

    # ==================================================================
    # PPT → PDF  (via PPTX intermediate)
    # ==================================================================

    def _ppt_to_pdf(self, src: str, out: str) -> str:
        import tempfile, os
        with tempfile.NamedTemporaryFile(suffix=".pptx", delete=False) as tf:
            tmp_pptx = tf.name
        try:
            self._ppt_to_pptx(src, tmp_pptx)
            return self._pptx_to_pdf(tmp_pptx, out)
        finally:
            if os.path.exists(tmp_pptx):
                os.unlink(tmp_pptx)
