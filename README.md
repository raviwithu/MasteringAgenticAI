# Mastering Agentic AI

A ready-to-use **Dev Container workspace** for building and running **agentic AI
labs** — LLM apps, tool-using agents, and RAG pipelines — with no local setup.
Open it in VS Code, reopen in the container, add your API keys, and start building.

---

## What's inside the dev container

- **Python 3.12** (Debian bookworm base image)
- **LLM SDKs:** Anthropic, OpenAI, Google Generative AI
- **Agent frameworks:** LangChain, LangGraph, CrewAI, AutoGen, LlamaIndex
- **RAG:** ChromaDB, FAISS, tiktoken
- **App frameworks:** FastAPI, Uvicorn, Streamlit
- **Notebooks:** JupyterLab + ipykernel (auto-started on port 8888)
- **Dev tooling:** pytest, ruff, black, Docker-in-Docker, GitHub CLI, graphviz

## Getting started

1. Install [Docker](https://www.docker.com/) and the
   [Dev Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)
   VS Code extension.
2. Open this folder in VS Code → **Reopen in Container** (or run
   *Dev Containers: Rebuild and Reopen in Container* from the command palette).
3. The container builds the image and runs `pip install -r requirements.txt`
   automatically.
4. Copy `.env.example` to `.env` and add your API keys.
5. JupyterLab starts automatically on **port 8888** — open it from the VS Code
   **Ports** panel, or start your own app (FastAPI / Streamlit) as needed.

## Forwarded ports

| Port | Use |
|------|-----|
| 8888 | JupyterLab (auto-started) |
| 8501 | Streamlit |
| 8000 | FastAPI / Uvicorn |
| 8080 | General web apps |

> **JupyterLab** is launched on container start by
> [`.devcontainer/start-jupyter.sh`](.devcontainer/start-jupyter.sh). It runs
> **token-less and open** for convenience — handy for a training lab, but do not
> expose real secrets/keys while the port is public. Re-enable the login token by
> removing the `--ServerApp.token`/`--ServerApp.password` flags in that script.

## Quick checks

```bash
# Verify the toolchain
python -c "import anthropic, openai, langchain, langgraph, crewai; print('OK')"

# Start JupyterLab manually (if needed)
jupyter lab --ip=0.0.0.0 --no-browser

# Run a Streamlit app
streamlit run app.py
```

## Repository layout

```
.
├── .devcontainer/         # Dev Container image, features, and Jupyter startup script
├── .github/workflows/     # CI: validates the container config and lints code
├── .env.example           # API-key template (copy to .env)
├── requirements.txt       # Python dependencies for the container
├── ruff.toml              # Lint configuration
├── CONTRIBUTING.md         # How to contribute
└── README.md              # this file
```

## License

[MIT](LICENSE)
