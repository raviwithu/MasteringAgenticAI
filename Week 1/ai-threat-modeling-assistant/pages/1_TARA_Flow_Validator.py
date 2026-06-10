"""TARA Flow Validator — a guided ISO/SAE 21434-style threat-modeling workflow.

Walks the user through the TARA flow one stage at a time:

    System / Business Use Case → Item Definition → Assets → Damage Scenarios →
    Impact Rating → Threats → Attack Vectors → Attack Feasibility Rating →
    Risk Value Determination → Risk Treatment Decision →
    Cybersecurity Goals / Requirements → Security Test Cases

As each stage is filled in, the page **checks it against the reference knowledge
base** (the threat-modeling / ISO 21434 books indexed by ``ingest_references.py``):

* **Always (offline):** retrieves the passages describing how that stage *should*
  be defined, plus a keyword-coverage heuristic — so you can see the expected
  structure even with no API key (retrieval is 100% local).
* **OpenAI mode:** adds an LLM verdict — what you covered, what's missing, concrete
  suggestions, and a citation — grounded in those passages.
"""

from __future__ import annotations

import json
import os

import streamlit as st

from threat_model.llm_client import active_mode

st.set_page_config(page_title="TARA Flow Validator", page_icon="🧭", layout="wide")

# --------------------------------------------------------------------------- #
# The TARA flow — one entry per stage
# --------------------------------------------------------------------------- #
STAGES = [
    {"key": "use_case", "label": "System / Business Use Case", "icon": "🚗",
     "help": "Describe the system and its business/operational purpose — what it "
             "does, for whom, and in what context.",
     "kb_query": "business use case and operational context of a system before threat modeling",
     "expects": ["purpose", "function", "users", "context"]},
    {"key": "item_definition", "label": "Item Definition", "icon": "📦",
     "help": "Define the item: boundary, components, interfaces, operational "
             "environment, functions, and assumptions (ISO/SAE 21434 item definition).",
     "kb_query": "how to write an item definition: item boundary components interfaces "
                 "operational environment functions and assumptions in ISO 21434",
     "expects": ["boundary", "components", "interfaces", "environment", "function", "assumption"]},
    {"key": "assets", "label": "Assets", "icon": "💎",
     "help": "Identify the assets in the item and their cybersecurity properties "
             "(confidentiality, integrity, availability).",
     "kb_query": "identifying assets and their cybersecurity properties confidentiality "
                 "integrity availability from an item definition",
     "expects": ["asset", "confidentiality", "integrity", "availability", "property"]},
    {"key": "damage_scenarios", "label": "Damage Scenarios", "icon": "💥",
     "help": "Describe the adverse consequences of compromising an asset's "
             "cybersecurity property (what harm results, to whom).",
     "kb_query": "what is a damage scenario derived from violation of an asset "
                 "cybersecurity property and its consequences",
     "expects": ["consequence", "harm", "compromise", "property", "impact"]},
    {"key": "impact_rating", "label": "Impact Rating", "icon": "📊",
     "help": "Rate each damage scenario's impact across Safety, Financial, "
             "Operational, and Privacy (S/F/O/P), with a severity level.",
     "kb_query": "rating impact of damage scenarios safety financial operational privacy "
                 "severity severe major moderate negligible",
     "expects": ["safety", "financial", "operational", "privacy", "severity"]},
    {"key": "threats", "label": "Threats / Threat Scenarios", "icon": "⚠️",
     "help": "Identify threat scenarios: how an asset's property could be "
             "compromised (e.g. via STRIDE categories).",
     "kb_query": "identifying threat scenarios STRIDE spoofing tampering repudiation "
                 "information disclosure denial of service elevation of privilege",
     "expects": ["threat", "spoofing", "tampering", "disclosure", "attacker"]},
    {"key": "attack_vectors", "label": "Attack Vectors / Paths", "icon": "🪜",
     "help": "Build attack paths / attack trees and identify the attack vectors "
             "that realize each threat.",
     "kb_query": "building attack paths and attack trees and identifying attack vectors "
                 "entry points to realize a threat",
     "expects": ["attack path", "attack vector", "step", "entry", "tree"]},
    {"key": "feasibility", "label": "Attack Feasibility Rating", "icon": "🎚️",
     "help": "Rate attack feasibility — e.g. attack potential (elapsed time, "
             "expertise, knowledge of the item, window of opportunity, equipment) "
             "or a CVSS-based approach.",
     "kb_query": "rating attack feasibility attack potential elapsed time expertise "
                 "knowledge of item equipment window of opportunity or CVSS",
     "expects": ["feasibility", "attack potential", "expertise", "equipment", "time"]},
    {"key": "risk_value", "label": "Risk Value Determination", "icon": "🧮",
     "help": "Determine the risk value by combining impact and attack feasibility "
             "(risk = impact × feasibility), e.g. via a risk matrix.",
     "kb_query": "determining risk value by combining impact rating and attack "
                 "feasibility rating using a risk matrix",
     "expects": ["risk", "impact", "feasibility", "matrix", "level"]},
    {"key": "risk_treatment", "label": "Risk Treatment Decision", "icon": "🧭",
     "help": "Decide a treatment for each risk: avoid, reduce/mitigate, "
             "share/transfer, or retain/accept.",
     "kb_query": "risk treatment options avoid reduce mitigate share transfer retain "
                 "accept a cybersecurity risk",
     "expects": ["avoid", "reduce", "share", "retain", "accept"]},
    {"key": "goals_requirements", "label": "Cybersecurity Goals / Requirements", "icon": "🎯",
     "help": "Derive cybersecurity goals (what to achieve) and refine them into "
             "requirements / controls (how to achieve them).",
     "kb_query": "deriving cybersecurity goals and cybersecurity requirements and "
                 "controls from risk treatment decisions",
     "expects": ["goal", "requirement", "control", "mitigation"]},
    {"key": "test_cases", "label": "Security Test Cases", "icon": "🧪",
     "help": "Define verification test cases that confirm each requirement / "
             "control is met (objective + expected result).",
     "kb_query": "deriving security test cases to verify cybersecurity requirements "
                 "and controls objective expected result",
     "expects": ["test", "verify", "expected", "requirement"]},
]
STAGE_BY_KEY = {s["key"]: s for s in STAGES}

# --------------------------------------------------------------------------- #
# Knowledge base + validation helpers
# --------------------------------------------------------------------------- #
@st.cache_resource(show_spinner=False)
def get_kb():
    """One ReferenceKB instance per app session (single ChromaDB client)."""
    from threat_model.references import ReferenceKB
    return ReferenceKB()


def kb_retrieve(query: str, k: int = 5):
    """Return reference passages for a query, or [] if the KB is unavailable/empty."""
    try:
        kb = get_kb()
        if kb.count() == 0:
            return []
        return kb.search(query, k=k)
    except Exception as exc:  # noqa: BLE001 - KB is best-effort
        st.session_state["_kb_error"] = f"{type(exc).__name__}: {exc}"
        return []


def _format_passages(hits) -> str:
    return "\n\n".join(
        f"[{h['metadata'].get('source', 'book')} p.{h['metadata'].get('page', '?')}] "
        + " ".join(h["text"].split())[:400]
        for h in hits
    )


def heuristic_coverage(stage: dict, text: str) -> dict:
    """Offline signal: which expected aspects (keywords) appear in the text."""
    low = text.lower()
    present = [kw for kw in stage["expects"] if kw.lower() in low]
    missing = [kw for kw in stage["expects"] if kw.lower() not in low]
    frac = len(present) / max(1, len(stage["expects"]))
    status = "follows" if frac >= 0.6 else "partial" if frac >= 0.3 else "missing"
    return {"status": status, "score": round(frac * 100),
            "present": present, "missing": missing, "suggestions": [],
            "citation": "", "mode": "offline (keyword coverage)"}


def llm_validate(stage: dict, text: str, passages: str, prior: str) -> dict:
    """LLM verdict grounded in the retrieved passages (OpenAI mode)."""
    from openai import OpenAI

    client = OpenAI()
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    system = (
        "You are an automotive cybersecurity reviewer (ISO/SAE 21434 TARA). Judge "
        "whether the user's content for a given TARA stage follows the expected "
        "structure/definition. Use the knowledge-base passages as primary evidence; "
        "you may add well-established ISO/SAE 21434 practice but stay concrete and "
        "constructive."
    )
    user = f"""TARA stage: {stage['label']}
Expected (per the framework): {stage['help']}

Knowledge-base passages:
{passages or '(none retrieved)'}

Earlier stages already filled (for consistency checks):
{prior or '(none)'}

The user's content for THIS stage:
\"\"\"{text}\"\"\"

Assess how well the content follows the expected structure for this stage and reply
as JSON with keys:
  "status": "follows" | "partial" | "missing"
  "score": integer 0-100
  "present": [aspects the content covers well]
  "missing": [expected aspects that are absent or weak]
  "suggestions": [up to 4 concrete improvements]
  "citation": "book p.N" taken from the passages, or "" if they were thin"""
    resp = client.chat.completions.create(
        model=model, temperature=0.1, max_tokens=600,
        response_format={"type": "json_object"},
        messages=[{"role": "system", "content": system},
                  {"role": "user", "content": user}])
    out = json.loads(resp.choices[0].message.content)
    out["mode"] = f"OpenAI · {model}"
    return out


def prior_context(upto_key: str) -> str:
    parts = []
    for s in STAGES:
        if s["key"] == upto_key:
            break
        val = st.session_state.get(f"in_{s['key']}", "").strip()
        if val:
            parts.append(f"- {s['label']}: {val[:200]}")
    return "\n".join(parts)


def validate_stage(stage: dict):
    text = st.session_state.get(f"in_{stage['key']}", "").strip()
    if not text:
        st.session_state[f"res_{stage['key']}"] = {
            "status": "empty", "score": 0, "present": [], "missing": stage["expects"],
            "suggestions": ["Fill in this stage before checking."], "citation": "",
            "passages": [], "mode": "—"}
        return
    hits = kb_retrieve(stage["kb_query"], k=5)
    if active_mode() == "openai":
        try:
            verdict = llm_validate(stage, text, _format_passages(hits), prior_context(stage["key"]))
        except Exception as exc:  # noqa: BLE001 - degrade to the offline heuristic
            verdict = heuristic_coverage(stage, text)
            verdict["mode"] = f"offline fallback (LLM error: {type(exc).__name__})"
    else:
        verdict = heuristic_coverage(stage, text)
    verdict["passages"] = hits
    st.session_state[f"res_{stage['key']}"] = verdict


# --------------------------------------------------------------------------- #
# UI
# --------------------------------------------------------------------------- #
_BADGE = {"follows": ("✅", "success"), "partial": ("🟡", "warning"),
          "missing": ("🔴", "error"), "empty": ("⚪", "info")}

st.title("🧭 TARA Flow Validator")
st.caption(
    "Work the threat-modeling flow stage by stage. Each stage is checked against "
    "the reference knowledge base so you can see whether your content follows the "
    "expected structure."
)

mode = active_mode()
c1, c2, c3 = st.columns([1.2, 1.2, 1])
with c1:
    st.metric("LLM mode", "OpenAI (AI verdict)" if mode == "openai" else "Mock (offline)")
with c2:
    try:
        cnt = get_kb().count()
        st.metric("Knowledge base", f"{cnt:,} chunks" if cnt else "empty")
    except Exception:
        cnt = 0
        st.metric("Knowledge base", "unavailable")
with c3:
    if st.button("🔍 Validate all filled stages", use_container_width=True):
        for s in STAGES:
            if st.session_state.get(f"in_{s['key']}", "").strip():
                validate_stage(s)

if cnt == 0:
    st.warning(
        "The reference knowledge base is empty or unavailable. Run "
        "`python ingest_references.py` (and make sure no other process holds "
        "`data/reference_chroma` open). Retrieval-based checks need it; you can "
        "still type your content meanwhile.",
        icon="⚠️")
if mode != "openai":
    st.info(
        "Running offline (mock) — checks use **local retrieval + keyword coverage**. "
        "Set `OPENAI_API_KEY` and `USE_MOCK_LLM=false` in `.env` for a full AI "
        "verdict (what's covered, what's missing, suggestions).", icon="💡")
if st.session_state.get("_kb_error"):
    st.error(f"Knowledge base error: {st.session_state['_kb_error']}", icon="🛑")

# Sidebar progress checklist
with st.sidebar:
    st.header("Flow progress")
    for i, s in enumerate(STAGES, 1):
        res = st.session_state.get(f"res_{s['key']}")
        filled = bool(st.session_state.get(f"in_{s['key']}", "").strip())
        icon = _BADGE.get(res["status"], ("•", ""))[0] if res else ("✏️" if filled else "⬜")
        st.write(f"{icon} **{i}.** {s['label']}")

st.divider()

# Stage-by-stage
for i, stage in enumerate(STAGES, 1):
    key = stage["key"]
    st.markdown(f"### {stage['icon']} Step {i} · {stage['label']}")
    st.caption(f"**Expected:** {stage['help']}")
    st.text_area("Your content", key=f"in_{key}", height=120,
                 placeholder=f"Describe the {stage['label'].lower()} here…",
                 label_visibility="collapsed")

    bcol, scol = st.columns([1, 3])
    with bcol:
        if st.button("Check against knowledge base", key=f"btn_{key}",
                     use_container_width=True):
            validate_stage(stage)

    res = st.session_state.get(f"res_{key}")
    if res:
        badge, kind = _BADGE.get(res["status"], ("•", "info"))
        verdict_line = f"{badge} **{res['status'].upper()}** · score {res['score']}/100 · _{res['mode']}_"
        getattr(st, kind if kind in {"success", "warning", "error", "info"} else "info")(verdict_line)
        vc1, vc2 = st.columns(2)
        with vc1:
            if res.get("present"):
                st.markdown("**✓ Present**\n" + "\n".join(f"- {p}" for p in res["present"]))
        with vc2:
            if res.get("missing"):
                st.markdown("**✗ Missing / weak**\n" + "\n".join(f"- {m}" for m in res["missing"]))
        if res.get("suggestions"):
            st.markdown("**💡 Suggestions**\n" + "\n".join(f"- {s}" for s in res["suggestions"]))
        if res.get("citation"):
            st.caption(f"📚 Grounded in: {res['citation']}")
        if res.get("passages"):
            with st.expander(f"📚 Knowledge-base references ({len(res['passages'])})"):
                for h in res["passages"]:
                    m = h["metadata"]
                    st.markdown(
                        f"**{m.get('source', 'book')} · p.{m.get('page', '?')}** "
                        f"(score {h.get('score', 0):.3f})")
                    st.write(" ".join(h["text"].split())[:500] + " …")
    st.divider()

# Export the worksheet
def _worksheet_md() -> str:
    lines = ["# TARA Flow Worksheet\n"]
    for i, s in enumerate(STAGES, 1):
        text = st.session_state.get(f"in_{s['key']}", "").strip() or "_(empty)_"
        res = st.session_state.get(f"res_{s['key']}")
        lines.append(f"## {i}. {s['label']}\n\n{text}\n")
        if res and res["status"] != "empty":
            lines.append(f"> **Check:** {res['status'].upper()} ({res['score']}/100, {res['mode']})  ")
            if res.get("missing"):
                lines.append(f"> Missing/weak: {', '.join(res['missing'])}  ")
            if res.get("citation"):
                lines.append(f"> Source: {res['citation']}  ")
            lines.append("")
    return "\n".join(lines)


st.download_button("⬇️ Download worksheet (Markdown)", data=_worksheet_md(),
                   file_name="tara_flow_worksheet.md", mime="text/markdown")
