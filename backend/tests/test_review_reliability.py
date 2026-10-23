"""Two regression tests for real failure modes found in the demo gap review.

Tests mock the OpenAI model/vector retrieval; no API calls or credits are used.
They verify that a suspect draft triggers one targeted revision. They do not
prove that all other factual claims are accurate.
"""
from __future__ import annotations

from types import SimpleNamespace

from langchain_core.documents import Document

from app import services
from app.review_quality import GAP_REVIEW_INSTRUCTIONS, review_quality_issues

POLICY = (
    "1. PPE: Wear chemical-resistant gloves and safety goggles for cleaning chemicals. "
    "2. Chemical storage: Secondary containers must be labeled. "
    "3. Incident reporting: Workers must immediately report injuries, spills or near misses. "
    "4. Corrective actions require an owner and due date."
)
INCIDENT = (
    "The worker wore gloves but reported not wearing safety goggles. "
    "The label on the smaller container could not be located during the review. "
    "No injury was reported. The supervisor was informed the next morning. "
    "The incident note lacks a named action owner and due date."
)


class FakeSearch:
    def similarity_search(self, query, k):
        return [
            Document(page_content=POLICY, metadata={"source": "demo_policy.txt", "locator": "text"}),
            Document(page_content=INCIDENT, metadata={"source": "demo_incident.txt", "locator": "text"}),
        ]


class SequencedModel:
    def __init__(self, first: str, corrected: str):
        self.responses = [first, corrected]
        self.calls: list[list] = []

    def invoke(self, messages):
        self.calls.append(messages)
        if not self.responses:
            raise AssertionError("Unexpected extra model call")
        return SimpleNamespace(content=self.responses.pop(0))


def run_fake_review(monkeypatch, first: str, corrected: str):
    model = SequencedModel(first, corrected)
    monkeypatch.setattr(services, "list_documents", lambda: [{"id": "sample"}])
    monkeypatch.setattr(services, "require_key", lambda: None)
    monkeypatch.setattr(services, "vector_store", lambda: FakeSearch())
    monkeypatch.setattr(services, "ChatOpenAI", lambda **kwargs: model)
    result = services.answer_question("Compare the incident and safety policy.", review=True)
    return result, model


def test_injury_status_is_not_falsely_described_as_missing(monkeypatch):
    """An explicit 'no injury was reported' is not missing injury information."""
    bad = """(1) Documented Controls
- Reporting policy [1].
(2) Potential Gaps or Unanswered Questions
- The incident report lacks injury-status information [2].
(3) Follow-up Actions
- Check incident records [1][2]."""
    good = """(1) Documented Controls
- Reporting policy [1].
(2) Potential Gaps or Unanswered Questions
- The incident explicitly says no injury was reported [2]; whether this event triggered immediate-reporting requirements needs separate verification [1][2].
(3) Follow-up Actions
- Check event classification and timing in the incident log [1][2]."""
    result, model = run_fake_review(monkeypatch, bad, good)
    assert len(model.calls) == 2, "Unsafe draft should trigger exactly one revision"
    assert result["answer"] == good
    assert review_quality_issues(result["answer"], result["sources"]) == []
    assert "No injury was reported" in GAP_REVIEW_INSTRUCTIONS
    assert "Injury status is not missing" in model.calls[1][-1].content


def test_unlocated_label_is_not_asserted_to_be_absent(monkeypatch):
    """A label not found during review does not prove the container was unlabeled."""
    bad = """(1) Documented Controls
- Containers require labels [1].
(2) Potential Gaps or Unanswered Questions
- The container was unlabeled [1][2].
(3) Follow-up Actions
- Review the container [1][2]."""
    good = """(1) Documented Controls
- Containers require labels [1].
(2) Potential Gaps or Unanswered Questions
- The label could not be located during review; the label's actual status is unverified [1][2].
(3) Follow-up Actions
- Inspect the affected container and check inspection records [1][2]."""
    result, model = run_fake_review(monkeypatch, bad, good)
    assert len(model.calls) == 2, "Unsafe draft should trigger exactly one revision"
    assert result["answer"] == good
    assert review_quality_issues(result["answer"], result["sources"]) == []
    assert "could not be located" in GAP_REVIEW_INSTRUCTIONS
    assert "does not prove an absent label" in model.calls[1][-1].content