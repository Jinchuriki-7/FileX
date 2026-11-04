"""
converters/document_converter.py
---------------------------------
Converts between document formats using python-docx, markdown, and BeautifulSoup.

Supported paths:
  DOCX → TXT, HTML, MD, ODT, PDF
  TXT  → DOCX, HTML, MD, PDF
  HTML → DOCX, TXT, MD, PDF
  MD   → HTML, DOCX, TXT, PDF
  ODT  → DOCX, TXT, HTML, PDF
  RTF  → TXT, DOCX, PDF  (text extraction only)
"""

from pathlib import Path


class DocumentConverter:
    """
    Text/document format converter.

    Usage::

        c = DocumentConverter()
        c.convert("report.docx", "report.txt", "txt")
        c.convert("notes.md",    "notes.html", "html")
    """

    def convert(self, source_path: str, output_path: str, target_ext: str) -> str:
        """
        Convert *source_path* → *output_path* in *target_ext* format.

        Returns:
            Absolute path of the written output file.
        """
        src_ext = Path(source_path).suffix.lstrip(".").lower()
        tgt = target_ext.lower().lstrip(".")

        dispatch = {
            # (src, tgt) → method
            ("docx", "txt"):  self._docx_to_txt,
            ("docx", "html"): self._docx_to_html,
            ("docx", "md"):   self._docx_to_md,
            ("docx", "odt"):  self._docx_to_odt,
            ("docx", "pdf"):  self._any_to_pdf,
            ("doc",  "txt"):  self._docx_to_txt,
            ("doc",  "html"): self._docx_to_html,
            ("doc",  "docx"): self._docx_to_txt,  # best-effort via text
            ("doc",  "pdf"):  self._any_to_pdf,
            ("txt",  "docx"): self._txt_to_docx,
            ("txt",  "html"): self._txt_to_html,
            ("txt",  "md"):   self._txt_to_md,
            ("txt",  "pdf"):  self._any_to_pdf,
            ("html", "docx"): self._html_to_docx,
            ("html", "txt"):  self._html_to_txt,
            ("html", "md"):   self._html_to_md,
            ("html", "pdf"):  self._any_to_pdf,
            ("htm",  "docx"): self._html_to_docx,
            ("htm",  "txt"):  self._html_to_txt,
            ("htm",  "md"):   self._html_to_md,
            ("htm",  "pdf"):  self._any_to_pdf,
            ("md",   "html"): self._md_to_html,
            ("md",   "docx"): self._md_to_docx,
            ("md",   "txt"):  self._md_to_txt,
            ("md",   "pdf"):  self._any_to_pdf,
            ("odt",  "docx"): self._odt_to_docx,
            ("odt",  "txt"):  self._odt_to_txt,
            ("odt",  "html"): self._odt_to_html,
            ("odt",  "pdf"):  self._any_to_pdf,
            ("rtf",  "txt"):  self._rtf_to_txt,
            ("rtf",  "docx"): self._rtf_to_docx,
            ("rtf",  "pdf"):  self._any_to_pdf,
        }

        key = (src_ext, tgt)
        handler = dispatch.get(key)
        if handler is None:
            raise ValueError(f"DocumentConverter: {src_ext} → {tgt} not supported")
        return handler(source_path, output_path)

    # ==================================================================
    # DOCX → X
    # ==================================================================

    def _docx_to_txt(self, src: str, out: str) -> str:
        from docx import Document
        doc = Document(src)
        text = "\n".join(p.text for p in doc.paragraphs)
        Path(out).write_text(text, encoding="utf-8")
        return out

    def _docx_to_html(self, src: str, out: str) -> str:
        from docx import Document
        doc = Document(src)
        lines = ["<!DOCTYPE html><html><body>"]
        for para in doc.paragraphs:
            tag = "p"
            if para.style.name.startswith("Heading"):
                level = "".join(filter(str.isdigit, para.style.name)) or "1"
                tag = f"h{min(int(level), 6)}"
            escaped = (para.text
                       .replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
            lines.append(f"<{tag}>{escaped}</{tag}>")
        lines.append("</body></html>")
        Path(out).write_text("\n".join(lines), encoding="utf-8")
        return out

    def _docx_to_md(self, src: str, out: str) -> str:
        from docx import Document
        doc = Document(src)
        lines = []
        for para in doc.paragraphs:
            if para.style.name.startswith("Heading"):
                level = "".join(filter(str.isdigit, para.style.name)) or "1"
                prefix = "#" * min(int(level), 6)
                lines.append(f"{prefix} {para.text}")
            else:
                lines.append(para.text)
        Path(out).write_text("\n\n".join(lines), encoding="utf-8")
        return out

    def _docx_to_odt(self, src: str, out: str) -> str:
        """DOCX → ODT via odfpy (text paragraphs only)."""
        from docx import Document
        from odf.opendocument import OpenDocumentText
        from odf.style import Style, TextProperties
        from odf.text import P, H

        doc_in = Document(src)
        odt = OpenDocumentText()

        for para in doc_in.paragraphs:
            if para.style.name.startswith("Heading"):
                level = int("".join(filter(str.isdigit, para.style.name)) or 1)
                h = H(outlinelevel=min(level, 6), text=para.text)
                odt.text.addElement(h)
            else:
                p = P(text=para.text)
                odt.text.addElement(p)

        odt.save(out)
        return out

    # ==================================================================
    # TXT → X
    # ==================================================================

    def _txt_to_docx(self, src: str, out: str) -> str:
        from docx import Document
        content = Path(src).read_text(encoding="utf-8", errors="replace")
        doc = Document()
        for line in content.split("\n"):
            doc.add_paragraph(line)
        doc.save(out)
        return out

    def _txt_to_html(self, src: str, out: str) -> str:
        content = Path(src).read_text(encoding="utf-8", errors="replace")
        paragraphs = "".join(
            f"<p>{line.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')}</p>\n"
            for line in content.split("\n")
        )
        html = f"<!DOCTYPE html><html><body>\n{paragraphs}</body></html>"
        Path(out).write_text(html, encoding="utf-8")
        return out

    def _txt_to_md(self, src: str, out: str) -> str:
        # TXT is already valid Markdown — just copy
        import shutil
        shutil.copy2(src, out)
        return out

    # ==================================================================
    # HTML → X
    # ==================================================================

    def _html_to_txt(self, src: str, out: str) -> str:
        from bs4 import BeautifulSoup
        html = Path(src).read_text(encoding="utf-8", errors="replace")
        text = BeautifulSoup(html, "lxml").get_text(separator="\n")
        Path(out).write_text(text, encoding="utf-8")
        return out

    def _html_to_docx(self, src: str, out: str) -> str:
        from bs4 import BeautifulSoup
        from docx import Document
        html = Path(src).read_text(encoding="utf-8", errors="replace")
        soup = BeautifulSoup(html, "lxml")
        doc = Document()
        for tag in soup.find_all(["h1","h2","h3","h4","h5","h6","p","li"]):
            if tag.name.startswith("h"):
                level = int(tag.name[1])
                doc.add_heading(tag.get_text(strip=True), level=level)
            else:
                doc.add_paragraph(tag.get_text(strip=True))
        doc.save(out)
        return out

    def _html_to_md(self, src: str, out: str) -> str:
        import html2text
        h = html2text.HTML2Text()
        h.ignore_links = False
        html = Path(src).read_text(encoding="utf-8", errors="replace")
        md = h.handle(html)
        Path(out).write_text(md, encoding="utf-8")
        return out

    # ==================================================================
    # Markdown → X
    # ==================================================================

    def _md_to_html(self, src: str, out: str) -> str:
        import markdown as md_lib
        text = Path(src).read_text(encoding="utf-8", errors="replace")
        body = md_lib.markdown(text, extensions=["extra", "toc"])
        html = f"<!DOCTYPE html><html><body>\n{body}\n</body></html>"
        Path(out).write_text(html, encoding="utf-8")
        return out

    def _md_to_docx(self, src: str, out: str) -> str:
        # MD → HTML → DOCX
        import tempfile, os
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8") as tf:
            tmp_html = tf.name
        try:
            self._md_to_html(src, tmp_html)
            return self._html_to_docx(tmp_html, out)
        finally:
            os.unlink(tmp_html)

    def _md_to_txt(self, src: str, out: str) -> str:
        from bs4 import BeautifulSoup
        import markdown as md_lib
        text = Path(src).read_text(encoding="utf-8", errors="replace")
        html = md_lib.markdown(text)
        plain = BeautifulSoup(html, "lxml").get_text(separator="\n")
        Path(out).write_text(plain, encoding="utf-8")
        return out

    # ==================================================================
    # ODT → X
    # ==================================================================

    def _odt_to_txt(self, src: str, out: str) -> str:
        from odf.opendocument import load
        from odf.text import P
        odt = load(src)
        texts = [str(p) for p in odt.text.getElementsByType(P)]
        Path(out).write_text("\n".join(texts), encoding="utf-8")
        return out

    def _odt_to_docx(self, src: str, out: str) -> str:
        # ODT → TXT → DOCX (safe fallback)
        import tempfile, os
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tf:
            tmp = tf.name
        try:
            self._odt_to_txt(src, tmp)
            return self._txt_to_docx(tmp, out)
        finally:
            os.unlink(tmp)

    def _odt_to_html(self, src: str, out: str) -> str:
        import tempfile, os
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tf:
            tmp = tf.name
        try:
            self._odt_to_txt(src, tmp)
            return self._txt_to_html(tmp, out)
        finally:
            os.unlink(tmp)

    # ==================================================================
    # RTF → X  (text-only via regex stripping)
    # ==================================================================

    @staticmethod
    def _strip_rtf(rtf_text: str) -> str:
        import re
        # Remove RTF control words and groups
        text = re.sub(r"\\\*.*?;", "", rtf_text)
        text = re.sub(r"\\[a-z]+\d* ?", "", text)
        text = re.sub(r"[{}]", "", text)
        return text.strip()

    def _rtf_to_txt(self, src: str, out: str) -> str:
        content = Path(src).read_text(encoding="latin-1", errors="replace")
        plain = self._strip_rtf(content)
        Path(out).write_text(plain, encoding="utf-8")
        return out

    def _rtf_to_docx(self, src: str, out: str) -> str:
        import tempfile, os
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tf:
            tmp = tf.name
        try:
            self._rtf_to_txt(src, tmp)
            return self._txt_to_docx(tmp, out)
        finally:
            os.unlink(tmp)

    # ==================================================================
    # → PDF  (delegate to PdfConverter)
    # ==================================================================

    def _any_to_pdf(self, src: str, out: str) -> str:
        from converters.pdf_converter import PdfConverter
        return PdfConverter().convert(src, out, "pdf")
