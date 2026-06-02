# 🛡️ AI Threat Modeling Assistant

A simple, AI-native Streamlit app that turns a plain-language **system
description** into a structured **threat model** for connected-vehicle systems.
It generates assets, trust boundaries, threats (STRIDE), attack paths, security
requirements, security test cases, and exports the result as Markdown.

Runs out of the box in an **offline mock mode** (no API key required), or against
the **OpenAI API** when a key is configured.

---

## Features

- Paste a system description + optional fields (name, business impact, data
  handled, external interfaces).
- One-click **Generate Threat Model** with a 9-section report:
  1. System Overview
  2. Key Assets
  3. Trust Boundaries
  4. Threats (STRIDE)
  5. Attack Paths
  6. Security Requirements
  7. Security Test Cases
  8. Assumptions
  9. Residual Risks
- **Load Sample Vehicle Gateway System** button to try it instantly.
- **Download .md** and **Save to `outputs/`** export.
- Automotive focus (TCU, cloud API, mobile app, gateway, CAN, OTA, diagnostics).

## Project structure

```
ai-threat-modeling-assistant/
├── app.py                  # Streamlit UI
├── requirements.txt
├── README.md
├── .env.example
├── threat_model/
│   ├── __init__.py
│   ├── prompts.py          # build_threat_model_prompt(...)
│   ├── llm_client.py       # generate_threat_model(...) — OpenAI or offline mock
│   ├── report.py           # build_report(...) / save_report(...)
│   └── sample_data.py      # SAMPLE_SYSTEM
└── outputs/                # exported reports (gitignored)
```

## Quick start

```bash
cd ai-threat-modeling-assistant
pip install -r requirements.txt
cp .env.example .env          # works as-is in mock mode
streamlit run app.py
```

Open the app (Streamlit prints the URL, usually http://localhost:8501), paste a
description or click **Load Sample**, then **Generate Threat Model**.

## Configuration

Set these in `.env` (see [.env.example](.env.example)):

| Variable | Purpose | Default |
|----------|---------|---------|
| `OPENAI_API_KEY` | Your OpenAI key. Blank → mock mode. | _(empty)_ |
| `OPENAI_MODEL` | Model used in OpenAI mode. | `gpt-4o-mini` |
| `USE_MOCK_LLM` | `true` forces the offline mock regardless of key. | `true` |

The sidebar shows which mode is active. In mock mode the app generates a
realistic, structured sample threat model locally so you can develop and demo
without an API key or network access.

> **Note:** This is a training/sample project. The generated content is a
> starting point for human review, not a substitute for a real security
> assessment.
