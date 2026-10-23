"""Citation audit regression tests (no OpenAI calls or real Chroma database)."""
from __future__ import annotations

import io
import zipfile

from app.reports import build_report, citation_audit, parse_report_sections, source_role

SOURCES = [
    {
        "marker": "[1]", "filename": "demo_policy.txt", "locator": "text",
        "excerpt": "Employees handling cleaning chemicals must wear gloves and goggles.",
    },
    {
        "marker": "[2]", "filename": "demo_incident.txt", "locator": "text",
        "excerpt": "Worker wore gloves but not safety goggles.",
    },
]


def test_finding_with_both_sources_has_valid_markers():
    result = citation_audit("No goggles observed [1][2].", SOURCES, comparison=True)
    assert result["policy"] == "[1]"
    assert result["incident"] == "[2]"
    assert result["all"] == "[1], [2]"
    assert result["status"] == "Markers valid — verify excerpt support"


def test_finding_with_incident_only_flags_missing_policy():
    result = citation_audit("Worker lacked goggles [2].", SOURCES, comparison=True)
    assert result["policy"] == ""
    assert result["incident"] == "[2]"
    assert "Missing policy citation" in result["status"]


def test_invalid_marker_is_not_exported_as_a_valid_reference():
    result = citation_audit("Reported [2][999].", SOURCES, comparison=False)
    assert result["all"] == "[2]"
    assert "Unrecognized markers: [999]" in result["status"]


def test_action_without_citations_is_flagged_not_automatically_filled():
    result = citation_audit("Review PPE training logs.", SOURCES, comparison=False)
    assert result["all"] == ""
    assert "No valid supporting citations" in result["status"]


def test_unclassified_filename_is_not_mislabeled_as_policy_or_incident():
    assert source_role({"filename": "day2_duplicate_test.txt"}) == "other"


def test_xlsx_export_includes_citation_audit_columns():
    review = """Preliminary Gap Review
(1) Documented Controls
- Gloves and goggles required [1].
(2) Potential Gaps or Unanswered Questions
- Incident reports no goggles but policy requires them [1][2].
- Training status is unverified [2].
(3) Follow-up Actions
- Review PPE training records [1][2].
- Confirm labeling records.
Summary: Human verification required.
"""
    sections = parse_report_sections(review)
    assert len(sections["Potential gaps"]) == 2
    assert len(sections["Follow-up actions"]) == 2

    payload, mime, extension = build_report("EHS Review", review, SOURCES, "xlsx")
    assert payload.startswith(b"PK")
    assert extension == "xlsx"
    assert "spreadsheetml" in mime
    with zipfile.ZipFile(io.BytesIO(payload)) as z:
        # Headers, statuses and markers are stored as shared or inline strings.
        xml = "\n".join(z.read(path).decode("utf-8") for path in z.namelist() if path.startswith("xl/worksheets/sheet") or path == "xl/sharedStrings.xml")
    assert "Policy evidence" in xml
    assert "Incident evidence" in xml
    assert "Citation check" in xml
    assert "Missing policy citation" in xml
    assert "No valid supporting citations" in xml
    