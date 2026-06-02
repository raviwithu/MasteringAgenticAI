# Contributing

Thanks for your interest in improving **Mastering Agentic AI**! This is a minimal
Python project skeleton for building agentic AI labs. Contributions that make the
setup more useful, reproducible, or easier to start from are very welcome.

## Development setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install ruff            # linter used by CI
cp .env.example .env        # add your API keys (never commit .env)
```

## Before opening a pull request

CI lints Python code. Reproduce it locally:

```bash
ruff check .
```

Keep any code you add runnable, and avoid committing large/binary outputs or
secrets (`.env` is gitignored — never commit real keys).

## Reporting issues

Open a GitHub issue describing what's wrong, what you expected, and how to
reproduce it. Small fixes (typos, clearer wording) can go straight to a pull
request.
