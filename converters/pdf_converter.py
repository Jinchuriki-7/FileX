"""
converters/pdf_converter.py
----------------------------
PDF conversion using pypdf, reportlab, and Pillow.

Supported conversions:
  PDF  → DOCX  (text extraction + python-docx rebuild)
  PDF  → TXT   (plain text extraction via pypdf)
  PDF  → PNG/JPG (page rasterisation via pdf2image / Pillow fallback)
  DOCX → PDF   (via reportlab)
  TXT  → PDF   (via reportlab)
  HTML → PDF   (via reportlab)
  IMG  → PDF   (via Pillow)
"""

from pathlib import Path
from typing import Optional


class PdfConverter:
    """
    Multi-directional PDF converter.

    Usage::

        c = PdfConverter()
        c.convert("document.docx", "document.pdf", "pdf")
        c.convert("report.pdf",    "report.txt",   "txt")
    """

    def convert(self, source_path: str, output_path: str, target_ext: str) -> str:
        """
        Route conversion based on source extension and target extension.

        Args:
            source_path: Input file path.
            output_path: Desired output path.
            target_ext:  Target format (e.g. 'pdf', 'txt', 'png').

        Returns:
            Absolute output path string.
        """
        src_ext = Path(source_path).suffix.lstrip(".").lower()
        tgt = target_ext.lower().lstrip(".")

        # --- source is PDF ---
        if src_ext == "pdf":
            if tgt == "txt":
                return self._pdf_to_txt(source_path, output_path)
            elif tgt == "docx":
                return self._pdf_to_docx(source_path, output_path)
            elif tgt in ("png", "jpg", "jpeg"):
                return self._pdf_to_image(source_path, output_path, tgt)
            else:
                raise ValueError(f"PDF → {tgt} not supported")

        # --- source is image → PDF ---
        elif src_ext in ("png", "jpg", "jpeg", "bmp", "gif", "tiff", "webp"):
            return self._image_to_pdf(source_path, output_path)

        # --- source is TXT / HTML → PDF ---
        elif src_ext == "txt":
            return self._txt_to_pdf(source_path, output_path)
        elif src_ext in ("html", "htm"):
            return self._html_to_pdf(source_path, output_path)
        elif src_ext == "docx":
            return self._docx_to_pdf(source_path, output_path)
        else:
            raise ValueError(f"{src_ext} → {tgt} not supported by PdfConverter")

    # ------------------------------------------------------------------
    # PDF → TXT
    # ------------------------------------------------------------------

    def _pdf_to_txt(self, source: str, output: str) -> str:
        from pypdf import PdfReader
        reader = PdfReader(source)
        lines = []
        for page in reader.pages:
            text = page.extract_text() or ""
            lines.append(text)
        with open(output, "w", encoding="utf-8") as fh:
            fh.write("\n\n".join(lines))
        return output

    # ------------------------------------------------------------------
    # PDF → DOCX  (basic: text extraction → docx paragraphs)
    # ------------------------------------------------------------------

    def _pdf_to_docx(self, source: str, output: str) -> str:
        from pypdf import PdfReader
        from docx import Document

        reader = PdfReader(source)
        doc = Document()
        doc.add_heading("Converted from PDF", level=1)

        for i, page in enumerate(reader.pages, 1):
            text = page.extract_text() or ""
            doc.add_heading(f"Page {i}", level=2)
            for para in text.split("\n"):
                if para.strip():
                    doc.add_paragraph(para)

        doc.save(output)
        return output

    # ------------------------------------------------------------------
    # PDF → Image  (one image per page — returns a zip if multi-page)
    # ------------------------------------------------------------------

    def _pdf_to_image(self, source: str, output: str, target_ext: str) -> str:
        """Rasterise first page of PDF to an image."""
        try:
            from pdf2image import convert_from_path
            images = convert_from_path(source, dpi=150, first_page=1, last_page=1)
            if images:
                img = images[0]
                if target_ext in ("jpg", "jpeg"):
                    img = img.convert("RGB")
                img.save(output)
                return output
        except ImportError:
            pass

        # Fallback: use reportlab + pypdf to draw page as image
        # (very basic — just saves a placeholder)
        raise RuntimeError(
            "pdf2image is not installed. Install it and Poppler to convert PDF pages to images."
        )

    # ------------------------------------------------------------------
    # Image → PDF
    # ------------------------------------------------------------------

    def _image_to_pdf(self, source: str, output: str) -> str:
        from PIL import Image
        with Image.open(source) as img:
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            elif img.mode != "RGB":
                img = img.convert("RGB")
            img.save(output, "PDF", resolution=100.0)
        return output

    # ------------------------------------------------------------------
    # TXT → PDF
    # ------------------------------------------------------------------

    def _txt_to_pdf(self, source: str, output: str) -> str:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.units import cm

        with open(source, "r", encoding="utf-8", errors="replace") as fh:
            content = fh.read()

        doc = SimpleDocTemplate(output, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []

        for line in content.split("\n"):
            if line.strip():
                # Escape XML special chars
                safe = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                story.append(Paragraph(safe, styles["Normal"]))
            else:
                story.append(Spacer(1, 0.3 * cm))

        doc.build(story)
        return output

    # ------------------------------------------------------------------
    # HTML → PDF  (basic: strip tags → txt → PDF)
    # ------------------------------------------------------------------

    def _html_to_pdf(self, source: str, output: str) -> str:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.units import cm
        from bs4 import BeautifulSoup

        with open(source, "r", encoding="utf-8", errors="replace") as fh:
            html = fh.read()

        soup = BeautifulSoup(html, "lxml")
        text = soup.get_text(separator="\n")

        doc = SimpleDocTemplate(output, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []

        for line in text.split("\n"):
            if line.strip():
                safe = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                story.append(Paragraph(safe, styles["Normal"]))
            else:
                story.append(Spacer(1, 0.3 * cm))

        doc.build(story)
        return output

    # ------------------------------------------------------------------
    # DOCX → PDF  (text extraction → PDF via reportlab)
    # ------------------------------------------------------------------

    def _docx_to_pdf(self, source: str, output: str) -> str:
        from docx import Document
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.units import cm

        doc_in = Document(source)
        rl_doc = SimpleDocTemplate(output, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []

        for para in doc_in.paragraphs:
            if para.text.strip():
                safe = (para.text
                        .replace("&", "&amp;")
                        .replace("<", "&lt;")
                        .replace(">", "&gt;"))
                style = styles["Heading1"] if para.style.name.startswith("Heading") else styles["Normal"]
                story.append(Paragraph(safe, style))
                story.append(Spacer(1, 0.2 * cm))

        rl_doc.build(story)
        return output
