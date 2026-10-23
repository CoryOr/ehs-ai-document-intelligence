# Portfolio and resume copy — EHS Insight

## GitHub / portfolio project description

**EHS Insight — AI Document Intelligence Assistant**

A full-stack prototype for analyzing synthetic environmental, health, and safety (EHS) records. Users upload a safety policy and incident report, ask evidence-grounded questions, or request a preliminary gap review. A bounded LLM tool router selects document Q&A, gap analysis, or report preparation. The application uses FastAPI, Vue 3/TypeScript, LangChain, OpenAI embeddings, persistent ChromaDB, and SQLite, and exports cited drafts to PDF, Word, and structured Excel workbooks.

The project emphasizes traceability rather than automatic compliance judgments: it displays retrieved evidence, flags known unsupported claim patterns, retries a flagged response at most once, and explicitly separates incomplete documentation from established facts.

[Source code](https://github.com/CoryOr/ehs-ai-document-intelligence)

## Resume-ready bullet (concise)

- Built **EHS Insight**, a full-stack Vue 3/FastAPI document-intelligence prototype with Chroma-backed RAG, bounded LLM tool selection, SHA-256 duplicate detection, source-grounded analysis, and PDF/Word/Excel report exports; added pytest regression checks for unsupported EHS conclusions.

## Resume-ready bullet (engineering emphasis)

- Engineered a Python/FastAPI + TypeScript/Vue AI workflow that ingests multi-format documents, retrieves evidence via OpenAI embeddings and ChromaDB, routes requests to approved analysis tools, and validates citation markers in structured Excel reports.

## Three interview talking points

1. **Design boundary:** “I used exactly-one-tool routing deliberately. The LLM chooses the approved workflow; it cannot run arbitrary actions or chain tools autonomously.”
2. **A failure I caught:** “The model initially treated an unlocated label as conclusively absent. I created a regression case with the actual incorrect output, added targeted source-aware checks, then fixed a false-positive case triggered by hypothetical wording.”
3. **What I would ship next:** “More robust retrieval evaluation, structured finding-to-source grounding, access controls, security scanning, observability, and background ingestion before considering real client documents.”

## Avoid these claims

- “The app ensures OSHA compliance” — it does not.
- “Every AI answer is hallucination-free” — citation and regex safeguards are limited.
- “Multi-agent autonomous workflow” — only bounded single-tool selection is implemented.
- “Deployed enterprise product” — currently a local portfolio demonstration.
- Any exact performance/accuracy percentage that has not been measured with a defined evaluation set.
