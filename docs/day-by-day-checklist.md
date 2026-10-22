# Three-day build checklist

Follow these checks in order. Do not try to build an unconstrained autonomous agent before the retrieval system works.

## Day 1 — Data ingestion and source-grounded Q&A

- [ ] Install Python and Node, create `.env` with a valid API key.
- [ ] Start FastAPI; verify `http://localhost:8000/docs` loads.
- [ ] Start Vite; verify `http://localhost:5173` loads.
- [ ] Upload `samples/demo_policy.txt` and `samples/demo_incident.txt`.
- [ ] Query: `What does the policy say about safety goggles?`.
- [ ] Open an evidence accordion; check the quoted passage actually exists in the source.
- [ ] Change the question to something not present in the documents; inspect whether the model expresses uncertainty.
- [ ] Commit your changes to GitHub with a clear message.

## Day 2 — Analysis, evaluation and optional agent tooling

- [ ] Use the gap-review button to compare the policy and incident report.
- [ ] Check that it identifies missing goggles and an unlabeled container as *potential* gaps.
- [ ] Check that it identifies a missing corrective-action owner and due date.
- [ ] Ensure it does not claim a specific law was violated.
- [ ] Evaluate at least five questions from README; record pass/fail and corrections in `docs/evaluation-notes.md`.
- [ ] Add retrieval filtering by document type or a simple reranking strategy if relevant.
- [ ] Optional true-agent upgrade: provide `search_documents` and `summarize_findings` as safe tools to a LangChain agent. Do not give the model unrestricted file access, shell access, or external-network tools.
- [ ] Write a short note distinguishing your deterministic RAG path from agentic tool selection.

## Day 3 — Full stack, reports and interview packaging

- [ ] Test upload/ask/review/export through the Vue interface.
- [ ] Open the PDF, Word and Excel outputs and check citations, readability, and the disclaimer.
- [ ] Run `python -m pytest -q` from `backend/`.
- [ ] Run `npm run build` from `frontend/`.
- [ ] Capture screenshots of a source-grounded answer and an exported report.
- [ ] Record a 60–90 second walkthrough using `docs/demo-script.md`.
- [ ] Update the README's limitations with what actually works.
- [ ] Add the project to your resume only after you have verified the claims.
