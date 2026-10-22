# EHS Document Intelligence Assistant

A 3-day portfolio project aimed at a Software Developer role involving LLMs, RAG, Python, APIs, vector databases, Vue 3, and programmatic report generation.

**What it does:** Upload PDF, DOCX, XLSX or TXT documents; ask source-grounded questions; run an evidence-based preliminary gap review; export results as PDF, Word or Excel. Includes a Vue 3/TypeScript dashboard.

> ⚠️ Demonstration only. This app does **not** determine regulatory compliance or replace trained EHS professionals. Use the included synthetic sample documents, not confidential employer/client files. Uploaded content is sent to a paid external embeddings/LLM API. OCR is not included.

## Quick start

Requirements: Python 3.11+, Node.js 20.19+ / 22.12+, an OpenAI API key (billed separately from ChatGPT).

**1. Backend** (terminal A, from this repo root)

```bash
python -m venv .venv
source .venv/bin/activate               # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
cp .env.example .env                   # On Windows, use: copy .env.example .env
# Edit .env and paste your real OPENAI_API_KEY
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

Test the backend at http://localhost:8000/docs ; `GET /api/health` should return `{ "status": "ok" }`.

**2. Frontend** (terminal B, from the repo root)

```bash
cd frontend
npm install
npm run dev
```

Visit http://localhost:5173 . The Vite dev proxy forwards `/api` to the backend at `http://localhost:8000`.

**3. Try the demo:** Upload `samples/demo_policy.txt` and `samples/demo_incident.txt`. Ask: **"Which controls were described in the policy, and what information is missing from the incident note?"** Then click **Run preliminary gap review** and export to PDF/Word/Excel.

**4. Run tests**

```bash
cd backend
python -m pytest -q
```

## Architecture

```
Vue 3 + TypeScript  -->  FastAPI
                            |-- PDF / Word / Excel / TXT parser
                            |-- LangChain chunker --> OpenAI embeddings --> persistent Chroma
                            |-- Retrieval --> ChatOpenAI --> source-grounded answer
                            |-- Preliminary gap-review workflow
                            `-- PDF / Word / Excel report generators

SQLite stores document metadata; local Chroma stores embeddings and excerpts.
```

The current implementation is a **RAG workflow**, not a fully autonomous agent. For the Day 2 enhancement, add a constrained tool-using agent that selects between `search_policy`, `search_incidents`, and `draft_report`, while keeping human review for all conclusions. Do not claim autonomous-agent capability until that is implemented.

## Three-day checkpoints

| Day | Focus | Acceptance criteria |
| --- | --- | --- |
| 1 | Ingest + retrieval | Upload two synthetic documents, chunks indexed to Chroma, ask a question, see numbered evidence references |
| 2 | Reliable analysis | Prompted gap review, at least 5 evaluation questions, add a genuine tool-using step only if core RAG is stable |
| 3 | Portfolio polish | Vue dashboard, PDF/Word/Excel exports, unit tests, clean README, deployment plan, 90-second walkthrough |

### Suggested Day 2 evaluation cases

1. What PPE does the policy require for chemical handling?
2. According to the incident record, was eye protection mentioned?
3. Does the incident record name a corrective-action owner?
4. Which questions about training remain unanswered?
5. Is the employer definitely in violation of a specific law? (Expected: **cannot determine from these documents**.)

Manually score each case for groundedness, citation accuracy, and appropriate uncertainty. Add your measured results to a portfolio write-up. Do not invent metrics.

## API summary

- `GET /api/health` — service check
- `GET /api/documents` — indexed document metadata
- `POST /api/upload` — multipart `file`
- `POST /api/chat` — `{ "question": "..." }`
- `POST /api/analyze` — `{ "focus": "..." }`
- `POST /api/export` — `{ "title": "...", "answer": "...", "sources": [...], "format": "pdf|docx|xlsx" }`

## Known limitations / future improvements

- Only text-based PDFs are supported (not scanned/OCR PDFs).
- Citation markers refer to *retrieved chunks*; source passages are displayed to allow independent checking. LLM citations still require evaluation.
- RAG retrieval has no confidence threshold, reranker, or per-user access controls yet.
- Local demo does not include authentication, rate limits, virus scanning, or privacy controls. Do not expose directly to the public internet.
- Input document text could contain prompt-injection attacks; the system prompt instructs the model to treat it as untrusted, but more protections are needed in production.
- SQLite/Chroma files are stored in `backend/data/` and excluded from git. Delete that directory to reset the demo.
- Model calls cost money and can fail due to provider rate limits.

## Interview talking points

**Tradeoffs:** local Chroma vs hosted vector DB; chunk size and overlap; citation faithfulness; synchronous requests vs background queues; document security and governance; structured analysis vs unconstrained agency.

**Most important:** Explain why a cautious, auditable retrieval workflow is appropriate for safety-related material. Never represent hypothetical gaps as confirmed compliance violations.
