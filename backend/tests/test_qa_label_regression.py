"""Regression tests for the exact unsupported label conclusion from live Test 2.

The detector tests use no API calls. LLM integration tests mock retrieval and
ChatOpenAI, so they also spend zero API credits when run in the user's venv.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.review_quality import review_quality_issues

# Verbatim answer supplied from the /api/agent 'answer_document_question' test.
EXACT_BAD_TEST_2_ANSWER = (
    'The incident report states that "The label on the smaller container could not be located during the review" [1]. '
    'This indicates that at the time of the incident review, the label was missing or not found. '
    'However, the report does not explicitly confirm whether the container was originally unlabeled '
    'or if the label was lost or removed later. The corrective action proposed was to '
    '"replace secondary-container labels," implying that the container should have had a label '
    'but it was absent or missing during the review [1].\n\n'
    'Therefore, the evidence supports that the secondary chemical container was found unlabeled '
    'during the incident review, but it does not conclusively establish whether it was originally '
    'unlabeled or if the label was lost. The absence of the label was noted, but the report does '
    'not definitively state the container was never labeled.\n\n'
    'In summary, the incident conclusively found the label missing at review time, but it is '
    'not conclusively established that the container was originally unlabeled [1].'
)

INCIDENT = (
    "DEMONSTRATION INCIDENT RECORD — SYNTHETIC, NOT REAL\n"
    "A worker transferred cleaning solution to a small secondary container. "
    "The label on the smaller container could not be located during the review. "
    "The worker used gloves but reported not wearing safety goggles. "
    "No injury was reported. A supervisor was informed the next morning. "
    "Corrective action proposed: replace secondary-container labels and hold "
    "an additional chemical handling briefing."
)
POLICY = (
    "All secondary containers must be labeled. "
    "Workers must notify supervisors immediately after an injury, chemical spill, or near miss."
)
SOURCES = [
    {"marker": "[1]", "filename": "demo_incident.txt", "locator": "text", "excerpt": INCIDENT},
    {"marker": "[2]", "filename": "demo_policy.txt", "locator": "text", "excerpt": POLICY},
]
GOOD_ANSWER = (
    "The label could not be located during the review [1]. This does not "
    "conclusively establish that the container was unlabeled or the label was "
    "physically absent. Verify its status with inspection records [1][2]."
)


def test_verbatim_live_test_2_answer_is_flagged():
    """The original failure must not silently pass again."""
    issues = review_quality_issues(EXACT_BAD_TEST_2_ANSWER, SOURCES)
    assert any("Label status is unverified" in issue for issue in issues)


@pytest.mark.parametrize("bad", [
    "The secondary chemical container was found unlabeled during review [1].",
    "The incident conclusively found the label missing at review time [1].",
    "The label was absent during the review [1].",
    "The absence of the label was noted [1].",
    "The secondary container's label was missing [1].",
])
def test_other_positive_overclaims_are_flagged(bad):
    assert any("Label status is unverified" in x for x in review_quality_issues(bad, SOURCES))


@pytest.mark.parametrize("safe", [
    GOOD_ANSWER,
    "It does not establish that the container was unlabeled [1].",
    "There is no evidence that the label was missing during review [1].",
    "It is unclear whether the container was unlabeled [1].",
    "It cannot be concluded that the label was missing [1].",
])
def test_safe_uncertainty_language_is_allowed(safe):
    assert review_quality_issues(safe, SOURCES) == []


def test_no_flag_without_ambiguous_incident_evidence():
    unrelated = [
        {"filename": "demo_incident.txt", "excerpt": "Gloves were not worn."},
        SOURCES[1],
    ]
    assert review_quality_issues(EXACT_BAD_TEST_2_ANSWER, unrelated) == []


def _mock_question_pipeline(monkeypatch, responses):
    """Install fully local fake vector retrieval and model responses."""
    pytest.importorskip("langchain_core")
    from langchain_core.documents import Document
    from app import services

    class FakeStore:
        def similarity_search(self, query, k):
            return [
                Document(page_content=s["excerpt"],
                         metadata={"source": s["filename"], "locator": "text"})
                for s in SOURCES
            ]

    class FakeModel:
        def __init__(self):
            self.responses = list(responses)
            self.calls = []

        def invoke(self, messages):
            self.calls.append(messages)
            return SimpleNamespace(content=self.responses.pop(0))

    model = FakeModel()
    monkeypatch.setattr(services, "list_documents", lambda: [{"id": "demo"}])
    monkeypatch.setattr(services, "require_key", lambda: None)
    monkeypatch.setattr(services, "vector_store", lambda: FakeStore())
    monkeypatch.setattr(services, "ChatOpenAI", lambda **kwargs: model)
    return services, model


def test_qa_tool_retries_exact_bad_answer_once(monkeypatch):
    services, model = _mock_question_pipeline(
        monkeypatch, [EXACT_BAD_TEST_2_ANSWER, GOOD_ANSWER]
    )
    result = services.answer_question(
        "Did the incident conclusively establish the container was unlabeled?",
        review=False,
    )
    assert result["answer"] == GOOD_ANSWER
    assert result["sources"][0]["filename"] == "demo_incident.txt"
    assert len(model.calls) == 2
    revision_prompt = model.calls[1][-1].content
    assert "Label status is unverified" in revision_prompt
    assert "do not introduce gap-review headings" in revision_prompt
    assert "three numbered sections" not in revision_prompt


def test_qa_tool_does_not_retry_safe_answer(monkeypatch):
    services, model = _mock_question_pipeline(monkeypatch, [GOOD_ANSWER])
    result = services.answer_question("What happened with the label?", review=False)
    assert result["answer"] == GOOD_ANSWER
    assert len(model.calls) == 1


def test_qa_tool_warns_after_one_failed_correction(monkeypatch):
    services, model = _mock_question_pipeline(
        monkeypatch, [EXACT_BAD_TEST_2_ANSWER, EXACT_BAD_TEST_2_ANSWER]
    )
    result = services.answer_question("Was the container unlabeled?", review=False)
    assert len(model.calls) == 2
    assert "AUTOMATED RELIABILITY WARNING" in result["answer"]
    assert "Label status is unverified" in result["answer"]