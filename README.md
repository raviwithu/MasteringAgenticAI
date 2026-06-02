# Mastering Agentic AI Certification

A **pre-read course workspace** that teaches how Large Language Models work — from
raw text all the way up to tool-using agents — through a series of small, runnable
Jupyter notebooks. Every concept is connected back to *why it matters for building
agentic AI*.

The repo ships with a ready-to-use **Dev Container** so the notebooks (and later,
real agent labs) run anywhere with no local setup.

---

## What you'll learn

The notebooks follow the **LLM lifecycle**, each stage building on the last:

```
  [1] PRE-TRAINING        learns language + world knowledge   (self-supervised, huge data)
        |
  [2] FINE-TUNING / SFT   instruction-following               (curated, labelled examples)
        |
  [3] ALIGNMENT           helpful, honest, harmless           (RLHF / DPO / Constitutional AI)
        |
  [4] AGENTIC USE         tools, reasoning, multi-step action (prompting patterns, ReAct, chains)
```

Each notebook uses the same teaching template: a "complete picture" diagram →
concepts with tables/math → a **runnable toy demo** (pure Python/NumPy, no API keys
or downloads) → "how this contributes to agentic AI" → key takeaways.

---

## Curriculum map

All material lives under [`Pre read/`](Pre%20read/). The recommended reading order:

| # | Lesson | Notebook | Covers |
|---|--------|----------|--------|
| 1 | **Pre-training** | [Phase 1 · Lesson 1](Pre%20read/Phase%201/Lesson%201%20-%20Pre-training.ipynb) | Self-supervised next-token prediction, what a "label" is, tokenization, a toy bigram model |
| 2 | **Transformer mechanics — Embeddings** | [Lesson 2 · Phase 1](Pre%20read/Lesson%202/Phase%201%20-%20Text%2C%20Tokens%2C%20IDs%20%26%20Embeddings.ipynb) | Text → tokens → IDs → embeddings; "meaning = geometry" via cosine similarity |
| 3 | **Transformer mechanics — Forward pass** | [Lesson 2 · Phase 2](Pre%20read/Lesson%202/Phase%202%20-%20Neurons%2C%20Weights%2C%20Activations%20%26%20Predictions.ipynb) | Neurons, weights, activations; a full `W·x+b → ReLU → softmax` forward pass in NumPy |
| 4 | **Transformer mechanics — Training** | [Lesson 2 · Phase 3](Pre%20read/Lesson%202/Phase%203%20-%20Gradients%2C%20Backprop%20%26%20Failure%20Modes.ipynb) | Loss, gradients, backprop (chain rule), vanishing/exploding gradients + fixes |
| 5 | **Fine-tuning** | [Phase 2 · Lesson 2](Pre%20read/Phase%202/Lesson%202%20-%20Fine-tuning.ipynb) | SFT / instruction tuning, LoRA / PEFT, same loss on curated labelled data |
| 6 | **Alignment** | [Phase 3 · Lesson 3](Pre%20read/Phase%203/Lesson%203%20-%20Alignment.ipynb) | The 3 H's, preferences vs. labels, RLHF vs. DPO vs. Constitutional AI |
| 7 | **Prompting — Foundations** | [Lesson 3 · Phase 1](Pre%20read/Lesson%203/Phase%201%20-%20Foundations%20%28Zero-shot%2C%20Role%2C%20Few-shot%29.ipynb) | Zero-shot, role/system, few-shot — in-context conditioning (no weight change) |
| 8 | **Prompting — Reasoning** | [Lesson 3 · Phase 2](Pre%20read/Lesson%203/Phase%202%20-%20Reasoning%20%28CoT%2C%20Self-Consistency%2C%20Tree%20of%20Thoughts%29.ipynb) | Chain of Thought, Self-Consistency (majority vote), Tree of Thoughts (search) |
| 9 | **Prompting — Agentic patterns** | [Lesson 3 · Phase 3](Pre%20read/Lesson%203/Phase%203%20-%20Agentic%20Patterns%20%28ReAct%2C%20Prompt%20Chaining%29.ipynb) | ReAct (Thought→Action→Observation loop with tools), Prompt Chaining (fixed pipeline) |

> **Note on folder names:** the directory names (`Phase 1`, `Lesson 2`, …) don't
> match the conceptual order one-to-one. Follow the table above, not the folder
> ordering.

---

## What's inside the dev container

- **Python 3.12** (Debian bookworm base image)
- **LLM SDKs:** Anthropic, OpenAI, Google Generative AI
- **Agent frameworks:** LangChain, LangGraph, CrewAI, AutoGen, LlamaIndex
- **RAG:** ChromaDB, FAISS, tiktoken
- **App frameworks:** FastAPI, Uvicorn, Streamlit
- **Notebooks:** JupyterLab + ipykernel
- **Dev tooling:** pytest, ruff, black, Docker-in-Docker, GitHub CLI

> The notebook demos themselves only need **Python + NumPy + matplotlib** — they run
> with no API keys. The SDKs and frameworks above are pre-installed for the hands-on
> agent labs that follow this pre-read.

## Getting started

1. Install [Docker](https://www.docker.com/) and the
   [Dev Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)
   VS Code extension.
2. Open this folder in VS Code → **Reopen in Container** (or run
   *Dev Containers: Rebuild and Reopen in Container* from the command palette).
3. The container builds the image and runs `pip install -r requirements.txt`
   automatically.
4. Copy `.env.example` to `.env` and add your API keys (only needed for the later
   agent labs, not the pre-read notebooks).
5. Open any notebook under [`Pre read/`](Pre%20read/) and run the cells top to bottom.

## Forwarded ports

| Port | Use |
|------|-----|
| 8888 | JupyterLab |
| 8501 | Streamlit |
| 8000 | FastAPI / Uvicorn |
| 8080 | General web apps |

## Quick checks

```bash
# Verify the toolchain
python -c "import anthropic, openai, langchain, langgraph, crewai; print('OK')"

# Start JupyterLab
jupyter lab --ip=0.0.0.0 --no-browser

# Run a Streamlit app
streamlit run app.py
```

## Repository layout

```
.
├── Pre read/              # the course notebooks (see Curriculum map above)
├── .devcontainer/         # Dev Container image, features, and Jupyter startup script
├── .env.example           # API-key template (copy to .env)
├── requirements.txt       # Python dependencies for the container
└── README.md              # this file
```
