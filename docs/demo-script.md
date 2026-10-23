# EHS Insight — 90-second interview demo

**Preparation:** Start FastAPI and Vite. Index only `samples/demo_policy.txt` and `samples/demo_incident.txt`, or index them once beforehand to avoid spending demo time waiting on the API. Open the dashboard in a browser. Have one validated sample PDF/Excel export ready in case a live API request hits a rate limit.

### 0:00–0:15 — The problem

> “EHS information often lives in separate safety policies and incident notes. I built EHS Insight, a local full-stack prototype that helps a reviewer compare those documents and prepare an evidence-backed draft, without pretending the AI can determine legal compliance.”

**On screen:** Dashboard headline and two indexed sample documents.

### 0:15–0:30 — Architecture

> “The UI is Vue 3 and TypeScript, the API is FastAPI, and documents are chunked and embedded into local Chroma. SQLite records upload metadata and SHA-256 fingerprints, so repeating the same file doesn't create unnecessary embeddings.”

**On screen:** Knowledge base card and indexed filenames.

### 0:30–0:55 — Agent tool choice

Type this into the prompt and click **Ask AI Agent**:

> Prepare a preliminary EHS report comparing the uploaded safety policy and incident record. Identify documented discrepancies, uncertainties, and recommended follow-up actions with citations.

> “The model chooses one of three approved tools: document Q&A, policy-gap review, or report preparation. The request you see chose report preparation. It's real tool selection, but intentionally only one tool per request.”

**On screen:** “Selected tool: Report preparation.”

### 0:55–1:15 — Evidence and safeguards

> “The response compares goggles use with policy, notes that a container label could not be located without claiming it was conclusively absent, and requests follow-up where reporting or corrective-action records are incomplete. Citations are linked to retrieved excerpts, and narrow reliability checks can trigger one revision.”

**On screen:** Expand a policy excerpt and an incident excerpt.

### 1:15–1:30 — Exports and reflection

> “The same draft exports to PDF, Word, or a structured Excel workbook with separate Findings, Follow-up Actions, and Evidence sheets. I used regression tests to catch unsupported inferences, like interpreting ‘no injury’ as ‘no reporting requirement.’ Next I'd add deeper retrieval evaluation and production security.”

**On screen:** Export controls; optionally display a previously exported workbook.

## Two-minute fallback if the live API fails

If the API is rate-limited, don't invent a successful execution. Show the last saved screenshots in `docs/images/`, explain the tool-selection flow using `docs/architecture.md`, and open a previously downloaded synthetic report while clearly identifying it as a recorded output.

## Interview prompts to prepare for

- **Why not a fully autonomous agent?** Safety-adjacent workflows benefit from bounded tool choices and human review; multi-step autonomy would require stronger evaluation and authorization.
- **How do you handle hallucinations?** Source-grounded prompts, citations, narrow regression detectors, one correction retry, and explicit uncertainty. None guarantees factual correctness.
- **Why both SQLite and Chroma?** SQLite handles document records and duplicate fingerprints; Chroma stores vectors for semantic retrieval.
- **What would change in production?** Authentication, tenancy, sensitive-data handling, queued ingestion, observability, retrieval evaluation, and hardened security controls.
