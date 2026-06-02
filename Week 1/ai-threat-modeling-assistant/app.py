"""AI Threat Modeling Assistant — Streamlit UI.

Paste a system description (optionally with name, business impact, data handled,
and external interfaces), generate a structured automotive threat model (with a
Mermaid attack-path diagram), and export it as Markdown.

Layout:
- Sidebar: instructions and the active LLM mode.
- Tabs: Input · Generated Threat Model · Export.
"""

from __future__ import annotations

import json

import streamlit as st
import streamlit.components.v1 as components

from threat_model.llm_client import active_mode, generate_threat_model
from threat_model.prompts import build_threat_model_prompt
from threat_model.report import (
    attack_path_from_markdown,
    create_markdown_report,
    report_filename,
    save_report,
)
from threat_model.sample_data import SAMPLE_SYSTEM

# --------------------------------------------------------------------------- #
# Page setup & state
# --------------------------------------------------------------------------- #
st.set_page_config(
    page_title="AI Threat Modeling Assistant",
    page_icon="🛡️",
    layout="wide",
)

_FIELD_DEFAULTS = {
    "system_name": "",
    "description": "",
    "business_impact": "",
    "data_handled": "",
    "external_interfaces": "",
}
for _key, _val in _FIELD_DEFAULTS.items():
    st.session_state.setdefault(_key, _val)
st.session_state.setdefault("report_md", "")


def load_sample() -> None:
    """Populate the input fields with the sample Vehicle Gateway system."""
    for key in _FIELD_DEFAULTS:
        st.session_state[key] = SAMPLE_SYSTEM.get(key, "")


def clear_fields() -> None:
    """Reset all input fields and any previous report."""
    for key in _FIELD_DEFAULTS:
        st.session_state[key] = ""
    st.session_state["report_md"] = ""


def render_mermaid(code: str, height: int = 360) -> None:
    """Render a Mermaid diagram in-app via the Mermaid.js CDN.

    Uses the explicit ``mermaid.render()`` API (more reliable than
    ``startOnLoad`` for dynamically injected content) and shows the parse error
    in-place if the diagram is malformed, so failures are never silent.
    """
    code_json = json.dumps(code)  # safely embed arbitrary text into the script
    components.html(
        f"""
        <div id="diagram">Rendering diagram…</div>
        <script type="module">
          import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';
          mermaid.initialize({{ startOnLoad: false, theme: 'default', securityLevel: 'loose' }});
          const code = {code_json};
          const el = document.getElementById('diagram');
          try {{
            const {{ svg }} = await mermaid.render('attackPath', code);
            el.innerHTML = svg;
          }} catch (err) {{
            el.innerHTML =
              '<pre style="color:#c0392b;white-space:pre-wrap">' +
              'Could not render Mermaid diagram:\\n' + (err && err.message) +
              '</pre>';
          }}
        </script>
        """,
        height=height,
        scrolling=True,
    )


# --------------------------------------------------------------------------- #
# Sidebar — instructions
# --------------------------------------------------------------------------- #
with st.sidebar:
    st.header("🛡️ How to use")
    st.markdown(
        "1. Open the **Input** tab.\n"
        "2. Paste a **system description** (or click *Load Sample*).\n"
        "3. Optionally add system name, business impact, data, interfaces.\n"
        "4. Click **Generate Threat Model**.\n"
        "5. Review the **Generated Threat Model** tab.\n"
        "6. Download or save from the **Export** tab."
    )
    st.divider()
    mode = active_mode()
    if mode == "mock":
        st.info("**LLM mode:** offline mock\n\nNo API key needed. Set "
                "`OPENAI_API_KEY` and `USE_MOCK_LLM=false` in `.env` for OpenAI.")
    else:
        st.success("**LLM mode:** OpenAI\n\nUsing your configured API key.")
    st.caption(
        "Sections: Overview · Assets · Trust Boundaries · Threats · Attack Paths "
        "(+ Mermaid diagram) · Requirements · Test Cases · Assumptions · "
        "Residual Risks."
    )
    st.caption("⚠️ Output is a starting point for human review, not a formal "
               "security assessment.")

# --------------------------------------------------------------------------- #
# Header
# --------------------------------------------------------------------------- #
st.title("🛡️ AI Threat Modeling Assistant")
st.caption("Turn a connected-vehicle system description into a structured, "
           "STRIDE-based threat model with an attack-path diagram.")

tab_input, tab_result, tab_export = st.tabs(
    ["📝 Input", "📊 Generated Threat Model", "📤 Export"]
)

# --------------------------------------------------------------------------- #
# Tab 1 — Input
# --------------------------------------------------------------------------- #
with tab_input:
    c1, c2, _ = st.columns([1, 1, 3])
    c1.button("📋 Load Sample", on_click=load_sample, use_container_width=True)
    c2.button("🧹 Clear", on_click=clear_fields, use_container_width=True)

    st.text_area(
        "System description *",
        key="description",
        height=170,
        placeholder="e.g. Vehicle Gateway communicates with TCU, Cloud API, "
        "Mobile App, and in-vehicle ECUs over CAN/Ethernet. It supports remote "
        "commands, telemetry upload, OTA status, and diagnostic access.",
    )

    with st.expander("Optional details (improve the result)", expanded=True):
        col_a, col_b = st.columns(2)
        col_a.text_input("System name", key="system_name",
                         placeholder="Vehicle Gateway")
        col_b.text_input("Data handled", key="data_handled",
                         placeholder="Telemetry, GPS, diagnostics, command payloads")
        col_c, col_d = st.columns(2)
        col_c.text_input("Business impact", key="business_impact",
                         placeholder="High — routes remote commands to ECUs")
        col_d.text_input("External interfaces", key="external_interfaces",
                         placeholder="TCU (cellular), Cloud API, Mobile App, CAN, OTA")

    if st.button("🚀 Generate Threat Model", type="primary",
                 use_container_width=True):
        if not st.session_state["description"].strip():
            st.error("Please enter a system description before generating.")
        else:
            inputs = {key: st.session_state[key] for key in _FIELD_DEFAULTS}
            with st.spinner("Analyzing system and generating threat model…"):
                prompt = build_threat_model_prompt(
                    system_name=inputs["system_name"],
                    description=inputs["description"],
                    business_impact=inputs["business_impact"],
                    data_handled=inputs["data_handled"],
                    external_interfaces=inputs["external_interfaces"],
                )
                raw = generate_threat_model(prompt, system_inputs=inputs)
                st.session_state["report_md"] = create_markdown_report(
                    inputs["system_name"], raw
                )
            st.success("Threat model generated! Open the "
                       "**Generated Threat Model** tab to review it.")
            st.balloons()

# --------------------------------------------------------------------------- #
# Tab 2 — Generated Threat Model
# --------------------------------------------------------------------------- #
with tab_result:
    report_md = st.session_state.get("report_md", "")
    if not report_md:
        st.info("No threat model yet. Generate one from the **Input** tab.")
    else:
        diagram, is_fallback = attack_path_from_markdown(report_md)
        st.subheader("Attack Path Diagram")
        render_mermaid(diagram)
        if is_fallback:
            st.caption("ℹ️ The model did not include a diagram, so a generic "
                       "attack path is shown. The full report is below.")
        else:
            st.caption("Parsed from the Mermaid block in the generated report below.")
        with st.expander("Show diagram source (Mermaid)"):
            st.code(diagram, language="text")
        st.divider()
        st.markdown(report_md)

# --------------------------------------------------------------------------- #
# Tab 3 — Export
# --------------------------------------------------------------------------- #
with tab_export:
    report_md = st.session_state.get("report_md", "")
    if not report_md:
        st.info("Nothing to export yet. Generate a threat model first.")
    else:
        system_name = st.session_state["system_name"]
        fname = report_filename(system_name)
        st.download_button(
            "⬇️ Download Markdown (.md)",
            data=report_md,
            file_name=fname,
            mime="text/markdown",
            use_container_width=True,
        )
        if st.button("💾 Save to outputs/ folder", use_container_width=True):
            try:
                path = save_report(report_md, system_name)
                st.success(f"Saved to `{path}`")
            except OSError as exc:
                st.error(f"Could not save report: {exc}")

        st.divider()
        st.caption("Preview of the Markdown that will be exported:")
        st.code(report_md, language="markdown")
