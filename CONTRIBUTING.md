# Contributing

Thanks for your interest in improving **Mastering Agentic AI**! This is a
Dev Container starter workspace for building agentic AI labs. Contributions that
make the environment more useful, reproducible, or easier to get started with are
very welcome.

## Development setup

Open the repo in the bundled **Dev Container** (VS Code → *Reopen in Container*).
The container provisions Python 3.12 plus the LLM SDKs and agent frameworks listed
in [`requirements.txt`](requirements.txt), and starts JupyterLab on port 8888.

For a quick local check without the container:

```bash
pip install ruff
```

## Before opening a pull request

CI validates the container config and lints code. Reproduce it locally:

```bash
# 1. devcontainer.json must be valid JSON
python -c "import json; json.load(open('.devcontainer/devcontainer.json'))"

# 2. the Jupyter startup script must have valid bash syntax
bash -n .devcontainer/start-jupyter.sh

# 3. Python must lint cleanly
ruff check .
```

If you add Python source or notebooks, keep them runnable and avoid committing
large/binary outputs or secrets (`.env` is gitignored — never commit real keys).

## Reporting issues

Open a GitHub issue describing what's wrong, what you expected, and how to
reproduce it. Small fixes (typos, clearer wording) can go straight to a pull
request.
