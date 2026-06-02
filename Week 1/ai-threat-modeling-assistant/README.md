# 🛡️ AI Threat Modeling Assistant

An AI-native Streamlit app that turns a plain-language **system description** into
a structured **threat model** for connected-vehicle systems — complete with a
Mermaid **attack-path diagram** and one-click Markdown export.

It runs out of the box in an **offline mock mode** (no API key required) or
against the **OpenAI API** when a key is configured.

---

## Project overview

Threat modeling is often a slow, expert-driven workshop. This tool gives engineers
a fast first draft: describe the system, and the assistant produces a STRIDE-based
threat model covering assets, trust boundaries, threats, attack paths, security
requirements, and test cases. The output is a starting point for human review —
not a replacement for a formal security assessment.

The domain focus is **automotive product security** (TCU, vehicle gateway, ECUs,
cloud API, mobile app, OTA, diagnostics, CAN/Automotive Ethernet), aligned in
spirit with ISO/SAE 21434 and UNECE R155.

## Features

- 📝 Paste a system description plus optional fields (name, business impact, data
  handled, external interfaces).
- 🤖 One-click generation of a 9-section threat model:
  System Overview · Key Assets · Trust Boundaries · Threats (STRIDE) ·
  Attack Paths · Security Requirements · Security Test Cases · Assumptions ·
  Residual Risks.
- 🔀 **Mermaid attack-path diagram** rendered in-app and embedded in the report.
- 📋 **Load Sample Vehicle Gateway System** to try it instantly.
- 📤 Export: **Download .md** or **Save to `outputs/`**.
- 🧰 **Offline mock mode** — develop and demo with no API key or network.
- 🗂️ Clean, tabbed UI (Input · Generated Threat Model · Export) with a sidebar guide.

## Tech stack

| Layer | Choice |
|-------|--------|
| Language | Python 3.12 |
| UI | Streamlit |
| LLM | OpenAI API (or built-in offline mock) |
| Config | python-dotenv, pydantic |
| Diagrams | Mermaid.js (rendered via CDN) |
| Export | Markdown |

## Project structure

```
ai-threat-modeling-assistant/
├── app.py                  # Streamlit UI (tabs + sidebar + Mermaid render)
├── requirements.txt
├── README.md
├── .env.example
├── threat_model/
│   ├── __init__.py
│   ├── prompts.py          # build_threat_model_prompt(...)
│   ├── llm_client.py       # generate_threat_model(...) — OpenAI or offline mock
│   ├── report.py           # create_markdown_report(...) / save_report(...) / mermaid
│   └── sample_data.py      # SAMPLE_SYSTEM
└── outputs/                # exported reports (gitignored)
```

## Setup

```bash
cd "MasteringAgenticAI/Week 1/ai-threat-modeling-assistant"

# (recommended) create and activate a virtualenv
python -m venv .venv && source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env        # works as-is in mock mode
```

## How to run

```bash
streamlit run app.py
```

Streamlit prints a local URL (usually http://localhost:8501). Open it, go to the
**Input** tab, click **Load Sample** (or paste your own description), then
**Generate Threat Model**.

## Environment variables

Set these in `.env` (see [.env.example](.env.example)):

| Variable | Purpose | Default |
|----------|---------|---------|
| `OPENAI_API_KEY` | Your OpenAI key. Blank → mock mode. | _(empty)_ |
| `OPENAI_MODEL` | Model used in OpenAI mode. | `gpt-4o-mini` |
| `USE_MOCK_LLM` | `true` forces the offline mock regardless of the key. | `true` |

The sidebar shows which mode is active.

## Example use case

> **Connected Vehicle Gateway.** A security engineer is reviewing a gateway that
> bridges the cloud, the mobile app, and the in-vehicle CAN bus. They paste the
> architecture, click generate, and immediately get: the key assets (remote
> command channel, OTA mechanism, keys), the trust boundaries (cloud↔TCU,
> gateway↔CAN), a STRIDE threat table, an attack path (stolen mobile token →
> cloud API → TCU → gateway → CAN → ECU) visualized as a Mermaid diagram, plus
> mapped security requirements and test cases — then exports it to Markdown for
> the design review.

## Future improvements

- Per-threat risk scoring (e.g. CVSS / automotive risk rating) and sortable tables.
- Multiple diagram types (data-flow diagram with trust boundaries, not just attack paths).
- Support for additional providers (Anthropic, Google) behind the same client.
- Persist and compare threat models across revisions of a system.
- Export to PDF/HTML and DOCX in addition to Markdown.
- Library of reusable system templates beyond the vehicle gateway.

## Demo script

A 60-second walkthrough:

1. **Open the app** — `streamlit run app.py`. Point out the sidebar instructions
   and the **LLM mode** badge (mock by default — no key needed).
2. **Load the sample** — Input tab → **Load Sample** fills in the Vehicle Gateway
   system. Mention the optional fields that sharpen the result.
3. **Generate** — click **Generate Threat Model**; the spinner runs and a success
   message appears.
4. **Review** — Generated Threat Model tab: scroll through the 9 sections, then
   highlight the **rendered Mermaid attack-path diagram**.
5. **Export** — Export tab: **Download .md** (show the titled, timestamped report)
   or **Save to outputs/**.
6. **Switch to live mode** (optional) — set `OPENAI_API_KEY` and
   `USE_MOCK_LLM=false` in `.env`, rerun, and regenerate to show real LLM output.

---

> **Disclaimer:** This is a training/sample project. Generated content assists
> human analysis and is not a substitute for a professional security review.
