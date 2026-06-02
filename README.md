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
