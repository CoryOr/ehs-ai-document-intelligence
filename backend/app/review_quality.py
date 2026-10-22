"""Narrow, source-aware reliability checks for the EHS portfolio demo.

These checks address two observed failure modes. They are not a general-purpose
fact checker or a substitute for professional review.
"""
from __future__ import annotations

import re
from typing import Mapping, Sequence

GAP_REVIEW_INSTRUCTIONS = """Produce a concise preliminary gap review using EXACTLY these headings:
(1) Documented Controls
(2) Potential Gaps or Unanswered Questions
(3) Follow-up Actions

Formatting and evidence rules:
- Write one finding or action per bullet, beginning with '- '.
- For each comparison, state (a) the policy requirement, (b) what the incident
  record actually states, and (c) whether this is a documented discrepancy,
  an uncertainty, or simply a missing record.
- Cite BOTH the relevant policy marker and the incident marker when both
  genuinely support the same comparison. Never add an irrelevant citation.
- Cite the evidence motivating EACH follow-up action. If supporting evidence is
  absent, write 'Evidence needed:' and specify what must be checked.
- Cite only markers included in the EVIDENCE excerpts; do not fabricate sources.

Specific factual accuracy safeguards:
- If an incident says 'No injury was reported,' that IS injury-status information.
  Do not claim the record omits injury status, that injury status is unknown,
  or that an injury occurred. You may say that no injury was reported.
- 'The label could not be located during review' does NOT establish that a
  container was unlabeled or that its label was physically absent. Describe
  the status as unverified and recommend inspection or corroborating records.
- If a supervisor was notified the next morning, report that chronology.
  Do not assert a confirmed reporting-policy violation unless the evidence
  establishes that the event was subject to the specified reporting rule.
- Missing owner, due date, or completion fields in one incident note does not
  prove that no corrective actions occurred elsewhere. Identify a documentation
  gap and ask for the corrective-action tracking record.
- Do not make legal, OSHA-compliance, certification, or safety determinations.

INCIDENT REPORTING:
- Before assessing notification timeliness, determine
  whether the documented event falls within the policy's
  reporting requirements. If the event classification is
  unclear, request clarification rather than asserting
  a reporting violation.

CORRECTIVE ACTIONS:
- When owners, deadlines, or completion records are absent
  from an incident report, describe them as not documented
  in the available evidence. Do not conclude that the
  actions were never assigned or completed.

Before responding, check each claim against the quoted source text, including
negative claims that something was NOT documented. Separate facts, uncertainties,
and proposed follow-up actions. Preserve the three headings and provide a short
summary at the end. The output is an AI-generated draft requiring EHS review."""

_INJURY_MISSING_CLAIM = re.compile(
    r"\b(?:injury[- ]status|injury information|injury details)\b\s*"
    r"(?:is|was|remains)\s*(?:missing|unknown|unclear|undocumented|not documented|not reported)\b"
    r"|\b(?:lacks?|missing|omits?)\s+(?:any\s+)?"
    r"(?:injury[- ]status|injury information|injury details)\b"
    r"|\b(?:report|record|note)\b.{0,65}?\b(?:does not|did not|fails to|doesn't)\s+"
    r"(?:mention|report|document|state|specify)\s+(?:whether\s+)?"
    r"(?:an?\s+)?injur(?:y|ies)\b",
    re.IGNORECASE | re.DOTALL,
)

_LABEL_UNSUPPORTED_CLAIM = re.compile(
    r"\b(?:the\s+|a\s+)?(?:secondary\s+)?container\s+(?:was|is)\s+"
    r"(?:definitely\s+)?unlabel(?:l)?ed\b"
    r"|\b(?:the\s+|a\s+)?(?:secondary\s+)?container(?:'s)?\s+label\s+"
    r"(?:was|is)\s+(?:missing|absent)\b"
    r"|\b(?:the\s+|a\s+)?label\s+(?:was|is)\s+(?:missing|absent)\b",
    re.IGNORECASE,
)


def review_quality_issues(answer: str, sources: Sequence[Mapping[str, str]]) -> list[str]:
    """Spot two *specific* overclaims, provided incident evidence supports the check.

    This is intentionally conservative: unrecognized overclaims may pass. A
    clean result is NOT certification that a review is factually accurate.
    """
    incident_text = "\n".join(
        item.get("excerpt", "")
        for item in sources
        if "incident" in item.get("filename", "").lower()
    )
    issues: list[str] = []

    if re.search(r"\bno\s+injur(?:y|ies)\s+(?:was|were)\s+reported\b", incident_text, re.I):
        if _INJURY_MISSING_CLAIM.search(answer):
            issues.append("Injury status is not missing: the incident says no injury was reported.")

    ambiguous_label_evidence = re.search(
        r"\blabel\b.{0,90}?\b(?:could\s+not|couldn't)\s+be\s+(?:located|found)\b"
        r"|\b(?:could\s+not|couldn't)\s+(?:locate|find)\s+(?:the\s+)?label\b",
        incident_text,
        re.IGNORECASE | re.DOTALL,
    )
    if ambiguous_label_evidence and _LABEL_UNSUPPORTED_CLAIM.search(answer):
        issues.append("Label status is unverified: 'could not be located' does not prove an absent label.")

    return issues