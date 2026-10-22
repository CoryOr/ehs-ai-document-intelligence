# Interview demo script — 75–90 seconds

**0:00–0:15 — Problem**
"EHS teams work with fragmented policies, training records, and incident notes. I built a prototype that helps reviewers find relevant evidence and prepare preliminary summaries, without treating the AI as the final compliance authority."

**0:15–0:30 — Ingestion**
"I'm uploading two fictional files: a safety policy and an incident note. FastAPI parses each document, LangChain chunks the text, OpenAI generates embeddings, and Chroma stores them locally."

**0:30–0:50 — Retrieval**
"When I ask about handling requirements, the app searches relevant passages and asks the model to answer from retrieved evidence. It displays citation markers and the actual text so I can verify claims."

**0:50–1:10 — Analysis**
"The review workflow compares the synthetic incident against the synthetic policy, highlighting missing information such as action ownership or training records. The tool explicitly avoids claiming legal noncompliance."

**1:10–1:25 — Report and engineering**
"I can export the result to PDF, Word, or Excel. I added basic tests, a Vue 3/TypeScript UI, and an automated CI workflow. Next improvements would be retrieval evaluation, access controls, and stronger prompt-injection protection."

**Don't overclaim:** Do not call this a fully autonomous agent unless you have added, demonstrated, and tested actual model-directed tool selection. Explain any functionality that is mocked or uses synthetic inputs.
