"""Regression coverage for unsupported 'no injury -> no reporting' reasoning.

Pure detector tests require no AI calls. Integration tests mock LLM and vector
retrieval and verify that the existing one-retry correction pipeline runs.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.review_quality import GAP_REVIEW_INSTRUCTIONS, review_quality_issues

POLICY = (
    "Incident reporting: Workers must notify supervisors immediately after "
    "an injury, chemical spill, or near miss."
)
INCIDENT = (
    "A worker transferred cleaning solution. No injury was reported. "
    "The supervisor was informed the next morning."
)
SOURCES = [
    {"marker": "[1]", "filename": "demo_policy.txt", "excerpt": POLICY},
    {"marker": "[2]", "filename": "demo_incident.txt", "excerpt": INCIDENT},
]


@pytest.mark.parametrize("unsafe_answer", [
    "No injury was reported in the incident [2], so injury reporting requirements do not apply here.",
    "No injury was reported. Therefore notification requirements do not apply.",
    "Because no injury was reported, immediate notification was not required.",
    "No injury was reported; hence no immediate reporting was necessary.",
    "Incident reporting requirements do not apply because no injury was reported.",
])
def test_flags_unsupported_reporting_exclusion(unsafe_answer):
    issues = review_quality_issues(unsafe_answer, SOURCES)
    assert any("Reporting applicability" in issue for issue in issues)


@pytest.mark.parametrize("safe_answer", [
    "No injury was reported [2], but reporting applicability is unclear because the policy also covers spills or near misses [1].",
    "The supervisor was informed the next morning [2]. Whether that violated the policy requires incident classification [1].",
    "No injury was reported, so it cannot be concluded that notification requirements do not apply.",
    "The policy requires reporting of injuries, spills, or near misses [1]. No injury was reported [2].",
])
def test_does_not_flag_cautious_reporting_language(safe_answer):
    assert review_quality_issues(safe_answer, SOURCES) == []


def test_no_false_alarm_when_policy_only_covers_injuries():
    injury_only_sources = [
        {"filename": "demo_policy.txt", "excerpt": "Report all workplace injuries immediately."},
        SOURCES[1],
    ]
    unsafe_for_sample_policy = (
        "No injury was reported, so reporting requirements do not apply."
    )
    assert review_quality_issues(unsafe_for_sample_policy, injury_only_sources) == []


def test_requires_source_evidence_of_no_injury():
    unclear_incident = [
        SOURCES[0],
        {"filename": "demo_incident.txt", "excerpt": "The supervisor was notified next morning."},
    ]
    assert review_quality_issues(
        "No injury was reported, so reporting requirements do not apply.",
        unclear_incident,
    ) == []


def test_instruction_explicitly_covers_noninjury_triggers():
    assert "spills" in GAP_REVIEW_INSTRUCTIONS
    assert "near misses" in GAP_REVIEW_INSTRUCTIONS
    assert "solely because" in GAP_REVIEW_INSTRUCTIONS


def test_unsafe_llm_draft_triggers_one_revision(monkeypatch):
    """Run through services.answer_question, the path used by the agent tools."""
    pytest.importorskip("langchain_core")
    from langchain_core.documents import Document
    from app import services

    class FakeSearch:
        def similarity_search(self, query, k):
            return [
                Document(page_content=POLICY, metadata={"source": "demo_policy.txt", "locator": "text"}),
                Document(page_content=INCIDENT, metadata={"source": "demo_incident.txt", "locator": "text"}),
            ]

    bad = "No injury was reported [2], so reporting requirements do not apply [1][2]."
    good = (
        "No injury was reported [2]. The policy also covers spills and near misses "
        "[1], so whether immediate notification was required needs verification [1][2]."
    )

    class FakeModel:
        def __init__(self):
            self.responses = [bad, good]
            self.calls = []

        def invoke(self, messages):
            self.calls.append(messages)
            return SimpleNamespace(content=self.responses.pop(0))

    model = FakeModel()
    monkeypatch.setattr(services, "list_documents", lambda: [{"id": "demo"}])
    monkeypatch.setattr(services, "require_key", lambda: None)
    monkeypatch.setattr(services, "vector_store", lambda: FakeSearch())
    monkeypatch.setattr(services, "ChatOpenAI", lambda **kwargs: model)

    result = services.answer_question("Review notification applicability.", review=True)
    assert len(model.calls) == 2
    assert result["answer"] == good
    assert review_quality_issues(result["answer"], result["sources"]) == []
    assert "Reporting applicability" in model.calls[1][-1].content


def test_still_unsafe_after_retry_yields_warning(monkeypatch):
    pytest.importorskip("langchain_core")
    from langchain_core.documents import Document
    from app import services

    class FakeSearch:
        def similarity_search(self, query, k):
            return [
                Document(page_content=POLICY, metadata={"source": "demo_policy.txt", "locator": "text"}),
                Document(page_content=INCIDENT, metadata={"source": "demo_incident.txt", "locator": "text"}),
            ]

    bad = "No injury was reported, so reporting requirements do not apply."

    class FakeModel:
        def __init__(self):
            self.calls = 0

        def invoke(self, messages):
            self.calls += 1
            return SimpleNamespace(content=bad)

    model = FakeModel()
    monkeypatch.setattr(services, "list_documents", lambda: [{"id": "demo"}])
    monkeypatch.setattr(services, "require_key", lambda: None)
    monkeypatch.setattr(services, "vector_store", lambda: FakeSearch())
    monkeypatch.setattr(services, "ChatOpenAI", lambda **kwargs: model)

    result = services.answer_question("Review incident reporting.", review=True)
    assert model.calls == 2  # Retry is bounded.
    assert "AUTOMATED RELIABILITY WARNING" in result["answer"]
    assert "Reporting applicability" in result["answer"]