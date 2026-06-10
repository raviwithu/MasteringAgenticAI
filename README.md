# Mastering Agentic AI

A workspace for building agentic AI labs — LLM apps, tool-using agents, and RAG
pipelines. It bundles a curated dependency set, an environment-variable template,
lint config, and CI, plus week-by-week hands-on projects.

> The full Dev Container that provisions Python and these dependencies lives in
> the surrounding workspace, not in this repo.

---

## Projects

| Week | Project | Description |
|------|---------|-------------|
| 1 | [AI Threat Modeling Assistant](Week%201/ai-threat-modeling-assistant/) | Streamlit app that turns a system description into a structured threat model (assets, trust boundaries, STRIDE threats, attack paths + diagram, requirements, test cases) with Markdown export. Runs offline (mock) or against OpenAI. |
| 2 | [Graph RAG with Neo4j](Week%202/graph-rag-neo4j/) | Notebook that builds a Graph RAG pipeline over the threat-modeling books using Neo4j as both the **vector database** (native vector index) and **knowledge graph** (`Book`/`Chunk`/`Entity` nodes + `HAS_CHUNK`/`NEXT`/`MENTIONS` edges): query → encode → vector seed → graph expansion → optional grounded answer. |
| 2 | [Linux System Threat Model (RAG + TARA)](Week%202/linux-threat-model-rag/) | Ingests the Linux security PDFs in `Week 2/Data/Linux` into **ChromaDB** (hash-based), then generates a fully traceable 12-entity Linux threat model — each entity via embed → retrieve → metadata-filter → rerank → LLM, persisted in a **SQLite** relational DB with parent→child links + ChromaDB source provenance, plus a relationship graph and end-to-end traceability report. |

---

## Dependencies

[`requirements.txt`](requirements.txt) pins a loosely-versioned, reproducible set:

- **LLM SDKs:** Anthropic, OpenAI, Google Generative AI
- **Agent frameworks:** LangChain, LangGraph, CrewAI, AutoGen, LlamaIndex
- **RAG:** ChromaDB, FAISS, tiktoken
- **App frameworks:** FastAPI, Uvicorn, Streamlit
- **Notebooks & tooling:** JupyterLab, pytest, ruff, black

## Getting started

```bash
pip install -r requirements.txt   # ideally in a virtualenv
cp .env.example .env              # then add your API keys
```

Add your code, then run whatever you're building (a Streamlit app, FastAPI
service, or notebook).

## Quick check

```bash
python -c "import anthropic, openai, langchain, langgraph, crewai; print('OK')"
```

## Repository layout

```
.
├── Week 1/                # hands-on projects
│   └── ai-threat-modeling-assistant/
├── .github/workflows/     # CI: lints Python with ruff
├── .env.example           # API-key template (copy to .env)
├── requirements.txt       # Python dependencies
├── ruff.toml              # Lint configuration
├── CONTRIBUTING.md         # How to contribute
└── README.md              # this file
```

## License

[MIT](LICENSE)
