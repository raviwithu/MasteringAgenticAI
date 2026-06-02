# Contributing

Thanks for your interest in improving **Mastering Agentic AI**! This repo is a
teaching resource, so contributions that make the lessons clearer, more correct,
or more runnable are very welcome.

## Ground rules for the notebooks

The pre-read notebooks are deliberately **self-contained and dependency-light** —
every demo runs with only `numpy` and `matplotlib`, no API keys or model
downloads. Please keep it that way:

- Toy demos should run **offline** and finish in seconds.
- Don't add heavy frameworks (LangChain, CrewAI, etc.) to a pre-read notebook —
  those belong in the later hands-on labs.
- Keep the house style: a "complete picture" diagram → concepts → a runnable
  demo → "how this contributes to agentic AI" → key takeaways.

## Development setup

1. Open the repo in the bundled **Dev Container** (VS Code → *Reopen in
   Container*), or create a local environment:
   ```bash
   pip install jupyter nbconvert ipykernel numpy matplotlib ruff
   ```
2. Edit notebooks under [`Pre read/`](Pre%20read/).

## Before opening a pull request

CI lints the code and **executes every notebook**. Reproduce it locally:

```bash
# Lint for real errors (syntax / undefined names)
ruff check .

# Execute every notebook headlessly — must succeed end to end
MPLBACKEND=Agg find . -name '*.ipynb' -not -path '*/.ipynb_checkpoints/*' \
  -exec jupyter nbconvert --to notebook --execute --stdout \
  --ExecutePreprocessor.timeout=120 {} \; > /dev/null
```

Please also **clear large/binary cell outputs** before committing (re-running the
notebook top to bottom and saving is fine) to keep diffs reviewable.

## Reporting issues

Open a GitHub issue describing the lesson, the cell, and what's wrong or unclear.
Small fixes (typos, clearer wording) can go straight to a pull request.
