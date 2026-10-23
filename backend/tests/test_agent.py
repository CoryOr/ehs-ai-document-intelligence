"""Tests for LLM tool selection; no API requests or embeddings."""
from types import SimpleNamespace

import pytest

from app import agent


class FakeChatModel:
    chosen = "answer_document_question"

    def __init__(self, **kwargs):
        pass

    def bind_tools(self, tools, **kwargs):
        assert kwargs["tool_choice"] == "required"
        assert kwargs["parallel_tool_calls"] is False
        assert {tool.name for tool in tools} == {
            "answer_document_question", "review_policy_gaps", "prepare_report"
        }
        return self

    def invoke(self, messages):
        return SimpleNamespace(tool_calls=[{"name": self.chosen, "args": {}}])


@pytest.fixture(autouse=True)
def mock_prerequisites(monkeypatch):
    monkeypatch.setattr(agent.services, "list_documents", lambda: [{"id": "demo"}])
    monkeypatch.setattr(agent.services, "require_key", lambda: None)
    monkeypatch.setattr(agent, "ChatOpenAI", FakeChatModel)


@pytest.mark.parametrize("chosen, review, report", [
    ("answer_document_question", False, False),
    ("review_policy_gaps", True, False),
    ("prepare_report", True, True),
])
def test_routes_to_expected_workflow(monkeypatch, chosen, review, report):
    FakeChatModel.chosen = chosen
    received = []

    def fake_answer(question, *, review=False):
        received.append((question, review))
        return {"answer": "Grounded answer [1]", "sources": [
            {"marker": "[1]", "filename": "demo_policy.txt", "locator": "text", "excerpt": "policy"}
        ]}

    monkeypatch.setattr(agent.services, "answer_question", fake_answer)
    result = agent.run_agent("  Review the incident   ")
    assert received == [("Review the incident", review)]
    assert result["tool_used"] == chosen
    assert result["report_ready"] is report
    assert result["sources"][0]["marker"] == "[1]"


def test_no_documents(monkeypatch):
    monkeypatch.setattr(agent.services, "list_documents", lambda: [])
    with pytest.raises(ValueError, match="Upload"):
        agent.run_agent("Review my incident")


def test_unknown_tool_rejected():
    FakeChatModel.chosen = "read_arbitrary_file"
    with pytest.raises(ValueError, match="unsupported tool"):
        agent.run_agent("Read secrets")


def test_short_request_rejected():
    with pytest.raises(ValueError, match="between 3 and 1500"):
        agent.run_agent("a")
