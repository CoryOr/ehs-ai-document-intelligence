# Day 3 — portfolio finalization checklist

Work in a dedicated documentation branch based on the latest `main`; the AI Agent and Vue integration have already been merged into `main`.

## Documentation and visual presentation

- [ ] Replace the outdated root README with the current agent-aware README from this package.
- [ ] Add `.env.example` containing placeholders only; ensure `.env` stays ignored.
- [ ] Add architecture diagram and engineering tradeoffs in `docs/architecture.md`.
- [ ] Add approved **synthetic-only** screenshots in `docs/images/`.
- [ ] Add updated 90-second demo script, evaluation notes, and portfolio description.
- [ ] Preview README on GitHub to check image paths and Mermaid diagram rendering.

## Verification

- [ ] From the repo root, run backend `python -m pytest -q` and record the actual count.
- [ ] From `frontend/`, run `npm run build`.
- [ ] Confirm `.env`, `backend/data/`, frontend dependencies, and local reports are not being staged.
- [ ] Confirm documentation instructions work from a clean clone, especially `.env.example` and the feature-branch checkout.
- [ ] Record a 75–90 second demonstration using only synthetic data.
- [ ] Reinspect one fresh Excel export; cite at least one finding with policy + incident markers.

## GitHub presentation

- [ ] Commit Day 3 docs in a separate branch and push to GitHub.
- [ ] Open a pull request from your documentation branch into **`main`**, review the diff and GitHub Actions checks, then merge.
- [ ] Verify that the README's “clone” instructions describe whichever branch is the default on GitHub.
- [ ] Set the repo description, topics (`fastapi`, `vue`, `rag`, `langchain`, `chromadb`, `ai-agent`, `document-intelligence`), and pin the repo on your GitHub profile if desired.
- [ ] Add a short demo video link only after recording and hosting it; do not invent a live application URL.

## Interview readiness

- [ ] Explain the single-tool router honestly (not a multi-step autonomous agent).
- [ ] Explain SHA-256 deduplication, Chroma retrieval, and citation limitations.
- [ ] Discuss the actual hallucination test that initially failed and how the regression test improved it.
- [ ] Explain what security and governance are missing before any production EHS use.
