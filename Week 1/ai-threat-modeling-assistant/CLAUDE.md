# CLAUDE.md — AI Threat Modeling Assistant

A **Streamlit** app that turns a plain-language description of *any* software
system into a structured **STRIDE threat model** and exports it as Markdown.
Part of the `MasteringAgenticAI` repo (Week 1).

## What it does
Input a system description (+ optional system name, business impact, data handled,
external interfaces) → generates a 9-section report: System Overview, Key Assets,
Trust Boundaries, Threats (STRIDE), Attack Paths (+ diagram), Security
Requirements, Security Test Cases, Assumptions, Residual Risks.

> It is **generic** (web/mobile/API/cloud/IoT), not automotive-specific anymore.

## Layout
```
app.py                      # Streamlit UI: sidebar + Input/Generated/Export tabs
                            # (no config.py — settings come from .env)
threat_model/
  prompts.py                # build_threat_model_prompt(...) — the LLM instruction (STRIDE, 9 sections)
  llm_client.py             # generate_threat_model(): OpenAI OR offline mock; active_mode()
  report.py                 # create_markdown_report, save_report, parse_report,
                            #   extract_mermaid_blocks, mermaid_to_dot, attack_path_from_markdown
  service.py                # generate_threat_model_report(...) — single API method (prompt→generate→report)
  agent_tools.py            # ThreatModelInput + make_threat_model_tool() — the LangChain StructuredTool
  agent.py                  # run_agent(inputs) — bind_tools tool-calling that calls the tool
  references.py             # ReferenceKB (PDF→chunk→GPU embed→ChromaDB) + retrieve_reference_context()
  sample_data.py            # SAMPLE_SYSTEM (Customer Web Portal)
ingest_references.py        # CLI to build the reference index from Reference/Books PDFs
test_reference_ingest.ipynb # standalone notebook to test the ingest pipeline
data/reference_chroma/      # persistent reference vector store (gitignored)
tests/                      # pytest functional-flow test (offline, mock)
docs/BUILD.md               # build writeup (overview, prompts, iterations, learnings)
outputs/                    # exported .md reports (gitignored)
requirements.txt · .env.example · README.md
```

## Run
```bash
pip install -r requirements.txt
cp .env.example .env          # works as-is in mock mode
streamlit run app.py
```
- **Default = offline mock LLM** (`USE_MOCK_LLM=true`) — no API key needed.
- **Live OpenAI:** set `OPENAI_API_KEY` and `USE_MOCK_LLM=false` in `.env`.
  (The user's real key is already in `.env` here — gitignored; never print/commit it.)

## Test
```bash
pip install -r requirements-dev.txt   # pytest
pytest                                # tests/ forces mock mode (no API cost)
```
The key test mirrors the user journey: build prompt → generate → export to file →
verify file → import the same file back.

## Reference knowledge base (threat-modeling books → ChromaDB, GPU)
- `references.py` ingests the PDFs in `Reference/Books` (auto-discovered upward, or
  `REFERENCE_BOOKS_DIR`): PDF → chunk (LangChain) → **local GPU embeddings**
  (`bge-small`, cuda auto-detect) → persistent **ChromaDB** (`data/reference_chroma`,
  collection `threat_modeling_refs`). Incremental via per-file hash in
  `data/reference_index_state.json`.
- Build it: `python ingest_references.py` (`--force`, `--stats`, `--search "..."`),
  or run `test_reference_ingest.ipynb`.
- **Gotcha:** one book is a saved HTTP *multipart upload* (starts with a `-----`
  boundary, not `%PDF`); `_pdf_stream()` strips the wrapper. Per-file read errors
  are skipped, not fatal.
- **Grounding:** in **OpenAI mode**, `service.generate_threat_model_report()` calls
  `references.retrieve_reference_context(description)` and injects top passages into
  the prompt (`build_threat_model_prompt(..., reference_context=...)`). Best-effort:
  if deps/index are missing it silently proceeds without grounding. Skipped in mock
  mode (the mock ignores the prompt).
- Heavy deps (chromadb, sentence-transformers, torch, pypdf) are imported lazily —
  the base app runs without them; references are just unavailable until installed.

## Generation flow (Tab 1 "Generate" button)
- **OpenAI mode:** button → `agent.run_agent(inputs)` → LangChain **tool calling**
  (`ChatOpenAI.bind_tools([generate_threat_model], tool_choice=...)`) → the model
  emits a tool call → we execute the tool → `service.generate_threat_model_report`
  → report markdown → `st.session_state["report_md"]` → Tab 2 renders (unchanged).
- **Mock mode (no key):** tool calling needs a real LLM, so the button **falls
  back to `service.generate_threat_model_report` directly** (fully offline). Same
  fallback if the agent path errors.
- Uses **`bind_tools`**, NOT `AgentExecutor` — the installed LangChain is **1.x**
  where the classic agents moved to `langchain-classic`. `bind_tools` is version-
  stable. Deps: `langchain-openai`, `langchain-core` only (no `langchain` umbrella).
- `agent.py` / `agent_tools.py` are **not** imported by `threat_model/__init__.py`
  (they pull LangChain) — import them directly so the package works without it.

## Conventions / gotchas
- **Diagrams:** rendered **in-app via `st.graphviz_chart`** (offline, reliable);
  the exported `.md` keeps a `mermaid` block (GitHub renders it). Do **not**
  reintroduce CDN-based Mermaid rendering in the app — it failed in some envs.
- `answer_question(query, k, where=None)` and `search_documents` aren't here — this
  app is self-contained (the RAG/ChromaDB project is a *separate* `Practise/RAG/`).
- Keep the **9-section contract** and the `T#`/`SR#`/`TC#` ID schemes stable —
  export, import, and diagram parsing depend on them.
- `.env` is gitignored; `outputs/*` is gitignored (keep `outputs/.gitkeep`).
