# Mastering Agentic AI

A minimal **Python project skeleton** for building agentic AI labs — LLM apps,
tool-using agents, and RAG pipelines. It bundles a curated dependency set, an
environment-variable template, lint config, and CI so you can start coding fast.

> The full Dev Container that provisions Python and these dependencies lives in
> the surrounding workspace, not in this repo.

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
├── .github/workflows/     # CI: lints Python with ruff
├── .env.example           # API-key template (copy to .env)
├── requirements.txt       # Python dependencies
├── ruff.toml              # Lint configuration
├── CONTRIBUTING.md         # How to contribute
└── README.md              # this file
```

## License

[MIT](LICENSE)
