"""These tests do not call an LLM or require an API key."""
import io

import pytest
from docx import Document as WordDocument
from pypdf import PdfReader
from app.reports import build_report
from app.services import parse_document


def test_plain_text_parsing():
    docs = parse_document(b"Eye protection is required in the lab.", "safety.txt")
    assert len(docs) == 1
    assert "Eye protection" in docs[0].page_content
    assert docs[0].metadata["locator"] == "text"


def test_reject_unsupported_files():
    with pytest.raises(ValueError, match="Supported"):
        parse_document(b"unsafe", "bad.exe")


def test_word_parsing():
    doc = WordDocument()
    doc.add_paragraph("Incident reporting is required.")
    output = io.BytesIO()
    doc.save(output)
    docs = parse_document(output.getvalue(), "policy.docx")
    assert "Incident reporting" in docs[0].page_content


@pytest.mark.parametrize("kind", ["pdf", "docx", "xlsx"])
def test_export_formats(kind):
    result, mime, ext = build_report(
        "Demo", "Observed control in [1]", [
            {"marker": "[1]", "filename": "policy.txt", "locator": "text", "excerpt": "Use PPE."}
        ], kind,
    )
    assert result and mime and ext == kind
    if kind == "pdf":
        assert PdfReader(io.BytesIO(result)).pages
