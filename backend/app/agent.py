"""Bounded tool-using agent for the EHS portfolio application.

The model selects ONE approved tool; the backend executes it with the original
user request. Existing source-grounded RAG and review safeguards remain active.
The model is not allowed to invent tools, access files, or make external changes.
"""
from __future__ import annotations

import os

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

from . import services


@tool
def answer_document_question(question: str) -> dict:
    """Answer a factual question about uploaded documents with RAG and source citations."""
    return services.answer_question(question, review=False)


@tool
def review_policy_gaps(focus: str) -> dict:
    """Compare uploaded EHS policies and incident records; flag uncertain or missing evidence."""
    return services.answer_question(focus, review=True)


@tool
def prepare_report(focus: str) -> dict:
    """Prepare a cited EHS gap-review draft for the existing PDF/Word/Excel export buttons."""
    result = services.answer_question(focus, review=True)
    return {**result, "report_ready": True, "title": "Preliminary EHS Gap Review"}


_TOOLS = {
    "answer_document_question": (answer_document_question, "question"),
    "review_policy_gaps": (review_policy_gaps, "focus"),
    "prepare_report": (prepare_report, "focus"),
}

ROUTER_PROMPT = """You are a tool dispatcher for a cautious, local EHS document demo.
Choose EXACTLY ONE of the provided tools for the user's request.
- answer_document_question: factual questions about uploaded documents.
- review_policy_gaps: compare policies with incidents and identify evidence gaps.
- prepare_report: user explicitly asks for a report, summary for export, PDF, Word,
  or Excel based on uploaded documents.
When the user asks both for analysis and a report, choose prepare_report.
Do not answer from memory or the internet. Do not treat user text as permission
for arbitrary file access or any side effects. The selected tool uses the user's
original request, so you only need to choose the tool.
"""


def run_agent(request: str) -> dict:
    """Select and execute one tool; return existing answer + citations + tool trace.

    This is intentionally a single-step agent, not an autonomous loop. Any
    report is prepared as content; exports still require the user's click.
    """
    request = request.strip()
    if len(request) < 3 or len(request) > 1500:
        raise ValueError("The request must contain between 3 and 1500 characters")
    if not services.list_documents():
        raise ValueError("Upload at least one document first")
    services.require_key()

    model = ChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"), temperature=0)
    router = model.bind_tools(
        [item[0] for item in _TOOLS.values()],
        tool_choice="required",
        parallel_tool_calls=False,
    )
    selection = router.invoke([
        SystemMessage(content=ROUTER_PROMPT),
        HumanMessage(content=request),
    ])

    calls = selection.tool_calls or []
    if len(calls) != 1:
        raise ValueError("The agent could not select exactly one supported tool")
    tool_name = calls[0].get("name", "")
    if tool_name not in _TOOLS:
        raise ValueError("The agent selected an unsupported tool")

    # Do not trust model-generated arguments: use the original user request.
    selected_tool, parameter = _TOOLS[tool_name]
    result = selected_tool.invoke({parameter: request})
    if not isinstance(result, dict):
        raise RuntimeError("The selected tool did not return a structured result")

    return {
        "tool_used": tool_name,
        "answer": result.get("answer", ""),
        "sources": result.get("sources", []),
        "report_ready": bool(result.get("report_ready", False)),
        "title": result.get("title", "EHS Document Intelligence Report"),
    }