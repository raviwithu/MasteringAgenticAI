# Build Documentation — AI Threat Modeling Assistant

A writeup of what was built, how, and what was learned. Created as the Week 1
deliverable for the *Mastering Agentic AI* course.

---

## 1. Project overview

The **AI Threat Modeling Assistant** is a Streamlit app that turns a
plain-language description of *any* software system into a structured security
**threat model**. Given a system description (plus optional context), it produces
a 9-section Markdown report:

1. System Overview
2. Key Assets
3. Trust Boundaries
4. Threats (classified with **STRIDE**)
5. Attack Paths (with a rendered diagram)
6. Security Requirements
7. Security Test Cases
8. Assumptions
9. Residual Risks

It can run two ways:

- **Offline mock mode** (default) — a hand-authored generator returns a realistic
  threat model with no API key or network. This makes development, demos, and
  automated tests fully deterministic.
- **OpenAI mode** — set `OPENAI_API_KEY` and `USE_MOCK_LLM=false` to generate with
  a real model.

### Architecture at a glance

```
app.py (Streamlit UI: Input / Generated / Export tabs, sidebar guide)
   │
   ├── threat_model/prompts.py     build_threat_model_prompt(...)   ← the LLM instruction
   ├── threat_model/llm_client.py  generate_threat_model(...)       ← OpenAI OR offline mock
   ├── threat_model/report.py      report assembly, export, import, diagram parsing
   └── threat_model/sample_data.py SAMPLE_SYSTEM (one-click example)

tests/  end-to-end functional flow (pytest, offline)
outputs/  exported .md reports (gitignored)
```

Design principle throughout: **the prompt and the mock stay in sync** on the same
fixed section list, so the offline experience mirrors the real one.

---

## 2. Datasets used

This project is **prompt-driven, not data-trained** — there is no ML training set.
The "data" involved is:

| "Dataset" | What it is | Where |
|-----------|------------|-------|
| **Sample system** | One realistic example input (Customer Web Portal) used by the *Load Sample* button | `threat_model/sample_data.py` |
| **Mock knowledge** | A hand-authored, generic STRIDE threat model (assets, threats, requirements, test cases) the offline mode returns | `threat_model/llm_client.py` |
| **User input** | The system description + optional fields typed at runtime | entered in the app |
| **Exported reports** | Generated `.md` files; also re-ingested by the Import feature | `outputs/` |

No external corpora, no scraping, no fine-tuning. The intelligence is in the
**prompt** (for OpenAI mode) and the **curated mock** (for offline mode).

---

## 3. Prompts used during vibe coding

The app was built conversationally ("vibe coding"). Two kinds of prompts mattered:
the **build prompts** (instructions to the coding assistant) and the **product
prompt** (what the app sends to the LLM).

### 3a. Build prompts (to the coding assistant)

Roughly in order:

1. **Basic Streamlit app** — "Create a Streamlit app *AI Threat Modeling
   Assistant*: title/description, a large system-description text area, optional
   fields (system name, business impact, data handled, external interfaces), a
   *Generate Threat Model* button, placeholder result sections; clean structure
   with `app.py` + helper modules."
2. **Project structure** — the `app.py` / `threat_model/*` / `outputs/` layout.
3. **Requirements** — "minimal: streamlit, openai, python-dotenv, pydantic."
4. **Prompt template** — "`build_threat_model_prompt(...)` that instructs the AI to
   act as a security threat-modeling assistant and emit the 9 Markdown sections."
5. **LLM client (implied)** — generate via OpenAI *or* a local mock mode.
6. **Connect UI to LLM** — "validate non-empty description, build prompt, call
   `generate_threat_model()`, render Markdown, add a download button."
7. **Sample input** — "`sample_data.py` with one example; a *Load Sample* button."
8. **Report export helper** — "`create_markdown_report(system_name, content)` with
   title, date/time, system name; use it before download."
9. **Mermaid attack-path diagram** — "enhance the prompt to also emit a Mermaid
   `flowchart TD` attack path; render it in the app."
10. **README** — "professional README: overview, features, stack, setup, run, env
    vars, example use case, future improvements, demo script."
11. **Final polish** — "sidebar instructions; tabs for Input / Generated / Export;
    success/error messages; spinner; demo-ready."

Then iterative requests: organize into `Week 1/`, add **import of `.md` reports**,
**fix the diagram rendering**, **generalize from automotive to any system**,
**add an automated test flow**, and this document.

### 3b. The product prompt (what the app sends to the model)

Built by `build_threat_model_prompt(...)`. Its shape (abridged):

> You are an expert **product/application security** threat-modeling assistant…
> Classify threats using **STRIDE**. Apply OWASP/NIST practice where relevant.
>
> **System under analysis:** *(system name, business impact, data handled,
> external interfaces, and the description)*
>
> Produce a threat model in **GitHub-flavored Markdown only**, using these
> sections in this exact order: *(the 9 sections)*. For each section, follow the
> per-section guidance (tables for Assets/Threats/Test Cases, STRIDE IDs `T1…`,
> requirement IDs `SR1…` mapped back to threats, a single Mermaid `flowchart TD`
> attack path, etc.). Be specific to the described system.

Key prompt-design choices:
- **Fixed, numbered section contract** → predictable, parseable output.
- **Tables with stable ID schemes** (`T#`, `SR#`, `TC#`) → cross-references hold.
- **STRIDE framing** → consistent threat taxonomy.
- **"Markdown only, no preamble"** → output is directly displayable/exportable.

---

## 4. Iterations tried

The build was incremental, and several approaches were revised:

| Area | First attempt | Problem | Final approach |
|------|---------------|---------|----------------|
| **LLM access** | OpenAI only | Needs a key/network; bad for demos & tests | Added an **offline mock** as the default; OpenAI optional |
| **Diagram rendering** | Mermaid.js via CDN inside an iframe | Didn't execute in some environments → the diagram showed as **raw code** | Convert Mermaid → **Graphviz DOT** and render with native `st.graphviz_chart` (offline); strip the raw block from the in-app body but keep it in the export |
| **Diagram source** | Trust the model to always emit a diagram | Sometimes absent/malformed | Added `attack_path_from_markdown()` with a **deterministic fallback** and label sanitization |
| **Domain** | Automotive-specific (TCU, CAN, OTA, ECUs; ISO 21434/UNECE R155) | Too narrow | **Generalized** to any system (web/mobile/API/cloud/IoT) using STRIDE + OWASP/NIST |
| **Report export** | `build_report()` wrapper | Wanted explicit metadata | `create_markdown_report()` with title + timestamp + system-name table |
| **Round-tripping** | Export only | Couldn't reopen a report | Added **Import** (`parse_report()`) that recovers the system name from the exported format |
| **UI** | Single scrolling page | Cluttered | **Tabs** (Input/Generated/Export) + sidebar guide + spinner + messages |
| **Layout** | Project at repo root | Course wants weekly structure | Moved under `Week 1/` with `git mv` (history preserved) |
| **Quality gate** | Manual checks | Risk of regressions | **pytest functional flow** + CI job |

---

## 5. Learnings & observations from the workflow

**Mock-first design pays off.** Making the offline mock the default unblocked
everything downstream — instant demos, deterministic tests, and CI with no
secrets. The discipline of keeping the mock and the real prompt on the *same
section contract* meant either backend produced interchangeable output.

**"Renders on GitHub" ≠ "renders in the app."** Streamlit's `st.markdown` shows a
` ```mermaid ` block as plain text, and the CDN-based Mermaid renderer was
unreliable. Converting to Graphviz DOT for `st.graphviz_chart` (which Streamlit
renders natively/offline) was the robust fix. Lesson: prefer the platform's
**native, offline** rendering path over an external CDN.

**Structured output is a contract.** Fixing the nine sections and the `T#`/`SR#`/
`TC#` ID schemes in the prompt made the output both readable *and* machine-
parseable — that's what let export, import, and diagram extraction work reliably.

**Streamlit state has ordering rules.** Pre-filling widget-bound `session_state`
(Load Sample, Import) only works cleanly *before* the widget is instantiated in a
run, so those controls live at the top of the Input tab and use callbacks.

**Generalizing late is cheap when structure is stable.** Because the section
contract and the parsing were domain-agnostic, swapping automotive content for
generic content touched mostly *text* (prompt, mock, sample, docs) — no
structural changes.

**Test the user's actual journey.** The most valuable test mirrors the real flow:
describe → generate → export → check the file → import the same file. It would
catch a break in any link of that chain, which is exactly what's wanted "whenever
new code changes happen."

**Small, reversible steps + git hygiene.** Each change was a focused commit;
`git mv` preserved history during reorganization; `.gitignore` kept secrets
(`.env`) and generated artifacts (`outputs/`) out of the repo.

---

## 6. Running it

```bash
cd "MasteringAgenticAI/Week 1/ai-threat-modeling-assistant"
pip install -r requirements.txt
streamlit run app.py            # offline mock mode by default

# regression tests (offline)
pip install -r requirements-dev.txt
pytest
```

> This is a training/sample project. Generated content is a **starting point for
> human review**, not a substitute for a professional security assessment.
