"""Regression tests for a false alarm on a correct, cautious label answer.

No API calls or external services required for the detector checks.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.review_quality import review_quality_issues

SOURCES = [
    {
        "filename": "demo_incident.txt",
        "locator": "text",
        "excerpt": (
            "The label on the smaller container could not be located during the review. "
            "Corrective action proposed: replace secondary-container labels."
        ),
    },
    {
        "filename": "demo_policy.txt",
        "locator": "text",
        "excerpt": "All secondary containers must be labeled with their contents.",
    },
]

# Verbatim answer returned by the live /api/agent test BEFORE the application
# appended the erroneous automated warning.
LIVE_CORRECT_ANSWER = (
    'The incident did not conclusively establish that the secondary chemical '
    'container was unlabeled. According to the incident record, the label on '
    'the smaller container "could not be located during the review," but this '
    'does not prove that the label was physically absent or that the container '
    'was definitively unlabeled [1]. The evidence only indicates that the '
    'label was not found at the time of review, leaving the actual label '
    'status unverified. Additional information or inspection would be needed '
    'to determine whether the label was missing or simply not observed.'
)


def test_exact_live_corrected_answer_does_not_trigger_false_alarm():
    assert review_quality_issues(LIVE_CORRECT_ANSWER, SOURCES) == []


@pytest.mark.parametrize("safe", [
    "We need to determine whether the label was missing during review.",
    "It is unclear if the label was missing or was overlooked.",
    "We cannot prove that the container was found unlabeled.",
    "The incident does not establish that the label was physically absent.",
])
def test_questions_and_negations_do_not_trigger_alarm(safe):
    assert review_quality_issues(safe, SOURCES) == []


@pytest.mark.parametrize("unsafe", [
    "The container was found unlabeled during review.",
    "The incident conclusively found the label missing at review time.",
    "It remains unclear whether the label was missing, but the container was found unlabeled.",
    "It is unclear whether the label was missing; however, the label was absent.",
])
def test_distinct_positive_assertions_still_trigger_alarm(unsafe):
    assert any("Label status is unverified" in issue
               for issue in review_quality_issues(unsafe, SOURCES))


def test_no_label_check_without_ambiguous_source():
    documents = [{"filename": "demo_incident.txt", "excerpt": "Worker wore gloves."}]
    assert review_quality_issues("The label was missing.", documents) == []


def test_normal_qa_returns_answer_without_warning_or_retry(monkeypatch):
    """Mock an ordinary Q&A pipeline to ensure no false correction request."""
    pytest.importorskip("langchain_core")
    from langchain_core.documents import Document
    from app import services

    class FakeStore:
        def similarity_search(self, query, k):
            return [Document(page_content=x["excerpt"],
                             metadata={"source": x["filename"], "locator": "text"})
                    for x in SOURCES]

    class FakeModel:
        def __init__(self):
            self.calls = 0

        def invoke(self, messages):
            self.calls += 1
            return SimpleNamespace(content=LIVE_CORRECT_ANSWER)

    model = FakeModel()
    monkeypatch.setattr(services, "list_documents", lambda: [{"id": "sample"}])
    monkeypatch.setattr(services, "require_key", lambda: None)
    monkeypatch.setattr(services, "vector_store", lambda: FakeStore())
    monkeypatch.setattr(services, "ChatOpenAI", lambda **kwargs: model)
    result = services.answer_question("Was the container unlabeled?", review=False)
    assert result["answer"] == LIVE_CORRECT_ANSWER
    assert "AUTOMATED RELIABILITY WARNING" not in result["answer"]
    assert model.calls == 1