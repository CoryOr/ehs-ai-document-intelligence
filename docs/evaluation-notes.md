# Evaluation notes — observed evidence vs. remaining checks

**Scope:** Local synthetic EHS policy and incident report. These results are **development observations** collected while building the prototype, not a controlled statistical benchmark or external EHS compliance validation.

## Evidence already observed

| Case | Expected behavior | Observed result | Confidence / limitation |
|---|---|---|---|
| Duplicate upload | Same file bytes do not create a second indexed record | Observed duplicate notice and unchanged document count on retest | Demonstrated on local synthetic files; legacy rows needed one-time reindex |
| PPE question | Identify gloves and goggles with source citations | Observed cited response from uploaded policy | Manual response inspection, not retrieval-wide benchmark |
| Reporting applicability | “No injury” alone does not rule out spill/near-miss notification | Live agent review preserved uncertainty about applicability | Tested on one synthetic incident; not all formulations |
| Label uncertainty | “Label could not be located” is not proof of physical absence | Initial failure identified; later live response stated status unverified without spurious warning | Shows value of regression testing and targeted check; not full semantic verification |
| Corrective-action records | Absent owners/dates in incident note ≠ proof actions never occurred | Live review described missing documentation and requested tracking records | One synthetic scenario |
| Agent router | Report request selects report preparation | Live tool selection returned `prepare_report` with citations | Bounded, one-tool-per-request router |
| PDF and Word | Contain draft plus supporting excerpts | Exported and visually inspected | One manual report sample |
| Excel grouped citations | `[1, 3]` maps to separate valid policy and incident markers | New workbook showed 5/5 cited findings and 5/5 cited actions in prior review | Marker-validity checks do not prove evidence actually supports all claims |
| Automated tests | Regression suite exercises core functionality | Developer reported **66 passing backend tests** before later grouped-citation tests were added | Run current `pytest -q` before citing a final total |
| Frontend build | TypeScript checker and Vite build succeed | Developer shared successful production build on Vue integration | Re-run after final code changes |

**Avoid presenting 5/5 exported citations as an accuracy score for the LLM.** It means the particular reviewed report's structural citation markers were recognized, not that each conclusion is legally or semantically validated.

## Evaluation cases to rerun before a recorded demo

| # | Request | Acceptable response | Method | Final result |
|---|---|---|---|---|
| 1 | Which PPE is required when handling cleaning chemicals? | Gloves + goggles with policy excerpt | Live agent + manual citation check | Recheck |
| 2 | Does the incident prove the smaller container was unlabeled? | No: not located, actual status unverified | Live agent + regex regression | Recheck |
| 3 | Does no injury mean no immediate notification was required? | No such inference; clarify event triggers | Live agent + reporting regression | Recheck |
| 4 | Were corrective actions never assigned? | Note lacks fields; external tracking may exist | Live agent | Recheck |
| 5 | Prepare a preliminary gap report | Distinct controls, uncertainties, follow-ups with appropriate citations | Live agent | Recheck |
| 6 | Export same report to three formats | Content consistent; Excel marker columns valid | File inspection | Recheck |
| 7 | Upload identical document twice | No extra record/chunks generated | Live upload | Recheck |
| 8 | Upload invalid/empty/oversize file | Clear validation failure, no corrupted database record | API tests | Not yet manually audited |

## Suggested future measures (not measured yet)

- Retrieval relevance: manually label whether top-k chunks support each question.
- Citation semantic precision: inspect each claim against its quoted source, *not just marker format*.
- Unsupported-claim rate: evaluate a fixed benchmark of deliberately ambiguous EHS cases.
- Router accuracy: compare model-selected tool to a labeled set of requests.
- Latency and API cost: record per-request distribution and typical indexing cost.
- Privacy/security: threat-model file uploads, prompt injection, external API use, and cross-user access.

## Reproducible commands

From the project root:

```bash
source .venv/bin/activate
cd backend
python -m pytest -q
cd ../frontend
npm run build
```

Copy **actual** current results into a portfolio update after running them; do not replace historical observations above with an invented or extrapolated test count.
