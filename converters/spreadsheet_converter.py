"""
converters/spreadsheet_converter.py
-------------------------------------
Converts between spreadsheet formats using openpyxl, pandas, and odfpy.

Supported:
  XLSX → CSV, ODS, PDF
  XLS  → XLSX, CSV, PDF
  CSV  → XLSX, ODS, PDF
  ODS  → XLSX, CSV, PDF
"""

from pathlib import Path


class SpreadsheetConverter:
    """
    Spreadsheet format converter.

    Usage::

        c = SpreadsheetConverter()
        c.convert("data.xlsx", "data.csv", "csv")
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
            ("xlsx", "csv"):  self._xlsx_to_csv,
            ("xlsx", "ods"):  self._xlsx_to_ods,
            ("xlsx", "pdf"):  self._xlsx_to_pdf,
            ("xls",  "xlsx"): self._xls_to_xlsx,
            ("xls",  "csv"):  self._xls_to_csv,
            ("xls",  "pdf"):  self._xls_to_pdf,
            ("csv",  "xlsx"): self._csv_to_xlsx,
            ("csv",  "ods"):  self._csv_to_ods,
            ("csv",  "pdf"):  self._csv_to_pdf,
            ("ods",  "xlsx"): self._ods_to_xlsx,
            ("ods",  "csv"):  self._ods_to_csv,
            ("ods",  "pdf"):  self._ods_to_pdf,
        }

        handler = dispatch.get((src_ext, tgt))
        if handler is None:
            raise ValueError(f"SpreadsheetConverter: {src_ext} → {tgt} not supported")
        return handler(source_path, output_path)

    # ==================================================================
    # Helpers: load into pandas DataFrame
    # ==================================================================

    @staticmethod
    def _load_df(src: str):
        """Load any supported spreadsheet into a pandas DataFrame."""
        import pandas as pd
        ext = Path(src).suffix.lstrip(".").lower()
        if ext == "csv":
            # Detect encoding and separator
            import chardet
            raw = Path(src).read_bytes()
            enc = chardet.detect(raw[:4096]).get("encoding") or "utf-8"
            # Try comma, then semicolon, then tab
            for sep in (",", ";", "\t"):
                try:
                    df = pd.read_csv(src, sep=sep, encoding=enc)
                    if len(df.columns) > 1 or sep == "\t":
                        return df
                except Exception:
                    continue
            return pd.read_csv(src, encoding=enc)
        elif ext in ("xls",):
            return pd.read_excel(src, engine="xlrd")
        elif ext in ("xlsx",):
            return pd.read_excel(src, engine="openpyxl")
        elif ext == "ods":
            return pd.read_excel(src, engine="odf")
        else:
            raise ValueError(f"Cannot load format: {ext}")

    # ==================================================================
    # XLSX → X
    # ==================================================================

    def _xlsx_to_csv(self, src: str, out: str) -> str:
        df = self._load_df(src)
        df.to_csv(out, index=False, encoding="utf-8-sig")
        return out

    def _xlsx_to_ods(self, src: str, out: str) -> str:
        df = self._load_df(src)
        df.to_excel(out, index=False, engine="odf")
        return out

    def _xlsx_to_pdf(self, src: str, out: str) -> str:
        return self._df_to_pdf(self._load_df(src), out)

    # ==================================================================
    # XLS → X
    # ==================================================================

    def _xls_to_xlsx(self, src: str, out: str) -> str:
        df = self._load_df(src)
        df.to_excel(out, index=False, engine="openpyxl")
        return out

    def _xls_to_csv(self, src: str, out: str) -> str:
        df = self._load_df(src)
        df.to_csv(out, index=False, encoding="utf-8-sig")
        return out

    def _xls_to_pdf(self, src: str, out: str) -> str:
        return self._df_to_pdf(self._load_df(src), out)

    # ==================================================================
    # CSV → X
    # ==================================================================

    def _csv_to_xlsx(self, src: str, out: str) -> str:
        df = self._load_df(src)
        df.to_excel(out, index=False, engine="openpyxl")
        return out

    def _csv_to_ods(self, src: str, out: str) -> str:
        df = self._load_df(src)
        df.to_excel(out, index=False, engine="odf")
        return out

    def _csv_to_pdf(self, src: str, out: str) -> str:
        return self._df_to_pdf(self._load_df(src), out)

    # ==================================================================
    # ODS → X
    # ==================================================================

    def _ods_to_xlsx(self, src: str, out: str) -> str:
        df = self._load_df(src)
        df.to_excel(out, index=False, engine="openpyxl")
        return out

    def _ods_to_csv(self, src: str, out: str) -> str:
        df = self._load_df(src)
        df.to_csv(out, index=False, encoding="utf-8-sig")
        return out

    def _ods_to_pdf(self, src: str, out: str) -> str:
        return self._df_to_pdf(self._load_df(src), out)

    # ==================================================================
    # DataFrame → PDF  (table via reportlab)
    # ==================================================================

    @staticmethod
    def _df_to_pdf(df, out: str) -> str:
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet

        # Limit columns for readability on A4
        max_cols = 10
        if len(df.columns) > max_cols:
            df = df.iloc[:, :max_cols]

        # Limit rows to avoid huge PDFs
        max_rows = 500
        df = df.head(max_rows)

        doc = SimpleDocTemplate(out, pagesize=landscape(A4))
        styles = getSampleStyleSheet()
        story = []

        story.append(Paragraph("Spreadsheet Export", styles["Heading1"]))
        story.append(Spacer(1, 12))

        # Build table data: header + rows
        header = [str(c) for c in df.columns.tolist()]
        data = [header]
        for _, row in df.iterrows():
            data.append([str(v) if v is not None else "" for v in row.tolist()])

        col_width = (landscape(A4)[0] - 60) / max(len(header), 1)
        table = Table(data, colWidths=[col_width] * len(header), repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND",  (0, 0), (-1, 0),  colors.HexColor("#313244")),
            ("TEXTCOLOR",   (0, 0), (-1, 0),  colors.white),
            ("FONTNAME",    (0, 0), (-1, 0),  "Helvetica-Bold"),
            ("FONTSIZE",    (0, 0), (-1, -1), 8),
            ("GRID",        (0, 0), (-1, -1), 0.5, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f0f8")]),
            ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(table)
        doc.build(story)
        return out
