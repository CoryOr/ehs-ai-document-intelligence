# reports.py
"""Export analysis results in formats mentioned in the ERM posting."""
from __future__ import annotations

from html import escape
from io import BytesIO

from docx import Document as WordDocument
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

DISCLAIMER = "AI-generated draft for demonstration only. Requires professional EHS review."


def excel_text(text: str) -> str:
    """Write untrusted text as text, never as a spreadsheet formula."""
    return "'" + text if text.lstrip().startswith(("=", "+", "-", "@")) else text


def build_report(title: str, answer: str, sources: list[dict], format: str) -> tuple[bytes, str, str]:
    if format == "docx":
        doc = WordDocument()
        doc.add_heading(title, 0)
        doc.add_paragraph(DISCLAIMER)
        for paragraph in answer.split("\n"):
            if paragraph.strip():
                doc.add_paragraph(paragraph)
        doc.add_heading("Retrieved evidence", level=1)
        for s in sources:
            doc.add_heading(f"{s['marker']} {s['filename']} — {s['locator']}", level=2)
            doc.add_paragraph(s["excerpt"])
        buffer = BytesIO()
        doc.save(buffer)
        return buffer.getvalue(), "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "docx"

    if format == "pdf":
        buffer = BytesIO()
        styles = getSampleStyleSheet()
        pdf = SimpleDocTemplate(buffer, pagesize=letter, title=title)
        story = [Paragraph(escape(title), styles["Title"]),
                 Paragraph(escape(DISCLAIMER), styles["Italic"]), Spacer(1, 16)]
        for line in answer.split("\n"):
            if line.strip():
                story.append(Paragraph(escape(line), styles["BodyText"]))
                story.append(Spacer(1, 7))
        story.append(Spacer(1, 12))
        story.append(Paragraph("Retrieved evidence", styles["Heading2"]))
        for s in sources:
            story.append(Paragraph(escape(f"{s['marker']} {s['filename']} — {s['locator']}"), styles["Heading3"]))
            story.append(Paragraph(escape(s["excerpt"]), styles["BodyText"]))
            story.append(Spacer(1, 8))
        pdf.build(story)
        return buffer.getvalue(), "application/pdf", "pdf"

    if format == "xlsx":
        book = Workbook()
        overview = book.active
        overview.title = "Analysis"
        overview.append(["Title", excel_text(title)])
        overview.append(["Notice", DISCLAIMER])
        overview.append(["Analysis", excel_text(answer)])
        overview.column_dimensions["A"].width = 20
        overview.column_dimensions["B"].width = 95
        overview["B3"].alignment = Alignment(wrap_text=True, vertical="top")
        overview.row_dimensions[3].height = min(380, max(80, len(answer) // 6))
        evidence = book.create_sheet("Evidence")
        evidence.append(["Citation", "Document", "Location", "Retrieved excerpt"])
        for s in sources:
            evidence.append([excel_text(s["marker"]), excel_text(s["filename"]), excel_text(s["locator"]), excel_text(s["excerpt"])])
        for cell in evidence[1]:
            cell.font = Font(color="FFFFFF", bold=True)
            cell.fill = PatternFill("solid", fgColor="153D57")
        for col, width in {"A": 15, "B": 32, "C": 25, "D": 95}.items():
            evidence.column_dimensions[col].width = width
        for row in evidence.iter_rows(min_row=2):
            for cell in row:
                cell.alignment = Alignment(wrap_text=True, vertical="top")
        evidence.freeze_panes = "A2"
        buffer = BytesIO()
        book.save(buffer)
        return buffer.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "xlsx"
    raise ValueError("Unsupported report format")
