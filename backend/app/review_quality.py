# review_quality.py
"""Narrow, source-aware reliability checks for the EHS portfolio demo.

These checks address three observed failure modes, including multiple phrasings of
unsupported label-presence conclusions. They are not a general-purpose
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
  container was unlabeled, was found unlabeled, or that its label was physically
  absent or conclusively missing at review time. The proposed action to replace
  labels does not by itself prove the label was absent. Describe its status
  as unverified and recommend inspection or corroborating records.
- If a supervisor was notified the next morning, report that chronology.
  Do not assert a confirmed reporting-policy violation unless the evidence
  establishes that the event was subject to the specified reporting rule.
- Missing owner, due date, or completion fields in one incident note does not
  prove that no corrective actions occurred elsewhere. Identify a documentation
  gap and ask for the corrective-action tracking record.
- Do not make legal, OSHA-compliance, certification, or safety determinations.

INCIDENT REPORTING:
- Before assessing notification timeliness, determine whether the documented
  event falls within the policy's reporting requirements. If the event
  classification is unclear, request clarification rather than asserting a
  reporting violation.
- The absence of an injury does not establish that incident-reporting
  requirements are inapplicable. Policies may also require reporting of spills
  or near misses.
- When the incident classification is unclear, describe reporting
  applicability as unverified.
- Never conclude that a reporting requirement does not apply solely because
  no injury was reported.
- Distinguish an observed delay in notification from a confirmed violation
  of an applicable notification requirement.

CORRECTIVE ACTIONS:
- When owners, deadlines, or completion records are absent from an incident
  report, describe them as not documented in the available evidence. Do not
  conclude that the actions were never assigned or completed.

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

# Claims that infer a physically absent label from a report that only says
# the label "could not be located". Keep this narrow; the regex does not
# replace verifying whether a quoted passage actually supports a conclusion.
_LABEL_UNSUPPORTED_CLAIM = re.compile(
    r"\b(?:the\s+|a\s+)?(?:secondary\s+(?:chemical\s+)?)?container\s+"
    r"(?:was|is)\s+(?:(?:definitely|clearly|conclusively)\s+)?"
    r"(?:found\s+|observed\s+)?unlabel(?:l)?ed\b"
    r"|\b(?:the\s+|a\s+)?(?:secondary\s+(?:chemical\s+)?)?container(?:'s)?\s+label\s+"
    r"(?:was|is)\s+(?:(?:physically|definitely|clearly|conclusively)\s+)?"
    r"(?:missing|absent|not\s+present)\b"
    r"|\b(?:the\s+|a\s+)?label\s+(?:was|is)\s+"
    r"(?:(?:physically|definitely|clearly|conclusively)\s+)?"
    r"(?:missing|absent|not\s+present)\b"
    r"|\b(?:conclusively|definitively|clearly)\s+(?:found|established|confirmed|proved)\s+"
    r"(?:that\s+)?(?:the\s+)?label\s+(?:(?:was|is)\s+)?(?:missing|absent)\b"
    r"|\babsence\s+of\s+(?:the\s+)?label\s+(?:was|is)\s+"
    r"(?:noted|documented|observed|confirmed)\b",
    re.IGNORECASE,
)

# A local negation check prevents falsely rejecting "does not establish that
# the container was unlabeled". It is deliberately clause-scoped: a separate
# unsupported positive claim elsewhere in the answer will still be caught.
_NEGATED_LABEL_CLAIM = re.compile(
    r"\b(?:cannot|can't|could\s+not|does\s+not|doesn't|did\s+not|"
    r"do\s+not|is\s+not|was\s+not)\s+"
    r"(?:(?:explicitly|definitively|conclusively|clearly)\s+)?"
    r"(?:show|establish|confirm|prove|demonstrate|mean|imply|indicate|"
    r"(?:be\s+)?(?:concluded|established|confirmed|proven))\b"
    r"|\bnot\s+(?:conclusively|definitively)\s+(?:established|confirmed|shown|proven)\b"
    r"|\b(?:unclear|uncertain|unverified|unknown)\s+(?:whether|if)\b"
    r"|\bno\s+evidence\s+(?:to\s+\w+\s+)?that\b",
    re.IGNORECASE,
)


def _asserts_unverified_label_absence(answer: str) -> bool:
    """Detect definite absence claims, not negations or hypothetical questions.

    For example, "determine whether the label was missing" is not a finding.
    Evaluate each claim's immediate clause independently so a cautious sentence
    does not excuse a separate unsupported conclusion later in the answer.
    """
    for match in _LABEL_UNSUPPORTED_CLAIM.finditer(answer):
        left = answer[max(0, match.start() - 160):match.start()]
        # A contrastive turn starts a new assertion even within one sentence:
        # "It is unclear whether ..., but the container was found unlabeled."
        left = re.split(
            r"[.!?;\n]|\b(?:but|however|nevertheless|instead)\b",
            left,
            flags=re.IGNORECASE,
        )[-1]
        if _NEGATED_LABEL_CLAIM.search(left):
            continue
        # A question/condition about label presence is not a positive finding.
        # This also covers "... needed to determine whether the label was missing".
        if re.search(r"\b(?:whether|if)\b", left, flags=re.IGNORECASE):
            continue
        return True
    return False

# THIRD CHECK: catches a narrow causal mistake, rather than any use of
# 'does not apply'. Both a no-injury incident and a policy with OTHER reporting
# triggers must be present before this rule is used.
_NO_INJURY_REASON = (
    r"(?:no\s+injur(?:y|ies)\s+(?:was|were)\s+reported"
    r"|no\s+injur(?:y|ies)\s+occurred"
    r"|there\s+(?:was|were)\s+no\s+injur(?:y|ies))"
)
_REPORTING_EXCLUSION = (
    r"(?:(?:injury|incident|safety)\s+)?(?:reporting|notification)\s+"
    r"(?:requirements?|rules?|obligations?|policy)?\s*(?:do|does|did)\s+not\s+apply\b"
    r"|(?:immediate\s+)?(?:reporting|notification)\s+(?:was|is)\s+not\s+"
    r"(?:required|necessary|mandatory)\b"
    r"|no\s+(?:immediate\s+)?(?:reporting|notification)\s+(?:was|is)\s+"
    r"(?:required|necessary|mandatory)\b"
)
_UNSUPPORTED_REPORTING_EXCLUSION = re.compile(
    rf"{_NO_INJURY_REASON}.{{0,150}}?\b(?:so|therefore|thus|hence|which means|meaning|as a result)\b"
    rf".{{0,150}}?(?:{_REPORTING_EXCLUSION})"
    rf"|\bbecause\s+{_NO_INJURY_REASON}.{{0,150}}?(?:{_REPORTING_EXCLUSION})"
    rf"|(?:{_REPORTING_EXCLUSION}).{{0,100}}?\b(?:because|since)\b"
    rf".{{0,100}}?{_NO_INJURY_REASON}",
    re.IGNORECASE | re.DOTALL,
)
# Allow the model to DENY the invalid inference when explaining uncertainty.
_REJECTED_INFERENCE = re.compile(
    r"\b(?:cannot|can't|could not|does not|doesn't|should not|must not)\s+"
    r"(?:conclude|assume|infer|establish|mean|prove|indicate|show|determine"
    r"|be\s+(?:concluded|assumed|inferred|established|proven|shown|determined))\b"
    r"|\bnot\s+(?:correct|safe|valid)\s+to\s+(?:say|conclude|assume)\b",
    re.IGNORECASE,
)
_POLICY_OTHER_REPORTING_TRIGGERS = re.compile(
    r"\b(?:spills?|near[ -]?miss(?:es)?)\b",
    re.IGNORECASE,
)
_POLICY_REPORTING_VERB = re.compile(r"\b(?:report\w*|notif\w*)\b", re.IGNORECASE)


def review_quality_issues(answer: str, sources: Sequence[Mapping[str, str]]) -> list[str]:
    """Flag three specific overclaims when supporting source conditions are met.

    These are limited wording-pattern checks, NOT semantic fact verification.
    Other unsupported conclusions may still pass.
    """
    incident_text = "\n".join(
        item.get("excerpt", "")
        for item in sources
        if "incident" in item.get("filename", "").lower()
    )
    policy_texts = [
        item.get("excerpt", "")
        for item in sources
        if "policy" in item.get("filename", "").lower()
    ]
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
    if ambiguous_label_evidence and _asserts_unverified_label_absence(answer):
        issues.append("Label status is unverified: 'could not be located' does not prove an absent label.")

    has_other_policy_triggers = any(
        _POLICY_OTHER_REPORTING_TRIGGERS.search(text)
        and _POLICY_REPORTING_VERB.search(text)
        for text in policy_texts
    )
    incident_says_no_injury = bool(re.search(_NO_INJURY_REASON, incident_text, re.I))
    if has_other_policy_triggers and incident_says_no_injury:
        for match in _UNSUPPORTED_REPORTING_EXCLUSION.finditer(answer):
            surrounding_text = answer[max(0, match.start() - 50):match.end()]
            if not _REJECTED_INFERENCE.search(surrounding_text):
                issues.append(
                    "Reporting applicability is unverified: no injury was reported, but "
                    "the policy also covers spills or near misses. Do not say reporting "
                    "requirements are inapplicable solely due to no injury."
                )
                break

    return issues