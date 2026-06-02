"""AI Threat Modeling Assistant — Streamlit UI.

Paste a system description (optionally with name, business impact, data handled,
and external interfaces), generate a structured automotive threat model (with a
Mermaid attack-path diagram), and export it as Markdown.

Layout:
- Sidebar: instructions and the active LLM mode.
- Tabs: Input · Generated Threat Model · Export.
"""

from __future__ import annotations

import streamlit as st

from threat_model.llm_client import active_mode, generate_threat_model
from threat_model.prompts import build_threat_model_prompt
from threat_model.report import (
    attack_path_from_markdown,
    create_markdown_report,
    mermaid_to_dot,
    parse_report,
    report_filename,
    save_report,
    strip_mermaid_blocks,
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


# --------------------------------------------------------------------------- #
# Sidebar — instructions
# --------------------------------------------------------------------------- #
with st.sidebar:
    st.header("🛡️ How to use")
    st.markdown(
        "**Generate a new threat model**\n"
        "1. Open the **📝 Input** tab.\n"
        "2. Paste a **system description**, or click **📋 Load Sample**.\n"
        "3. *(Optional)* add system name, business impact, data handled, and "
        "external interfaces — these sharpen the result.\n"
        "4. Click **🚀 Generate Threat Model** and wait for the success message.\n"
        "5. Open **📊 Generated Threat Model** to review the report and the "
        "rendered **attack-path diagram**.\n"
        "6. Go to **📤 Export** to **download** the `.md` or **save** it to "
        "`outputs/`."
    )
    st.markdown(
        "**Reopen a saved report**\n"
        "- In the **📝 Input** tab, expand **📥 Import a saved report (.md)**, "
        "upload a previously exported file, and click **Load imported report**."
    )
    st.divider()
    mode = active_mode()
    if mode == "mock":
        st.info("**LLM mode:** offline mock\n\nNo API key needed. Set "
                "`OPENAI_API_KEY` and `USE_MOCK_LLM=false` in `.env` for OpenAI.")
    else:
        st.success("**LLM mode:** OpenAI\n\nUsing your configured API key.")
    st.caption(
        "Report sections: Overview · Assets · Trust Boundaries · Threats · "
        "Attack Paths (+ diagram) · Requirements · Test Cases · Assumptions · "
        "Residual Risks."
    )
    st.caption("⚠️ Output is a starting point for human review, not a formal "
               "security assessment.")

# --------------------------------------------------------------------------- #
# Header
# --------------------------------------------------------------------------- #
st.title("🛡️ AI Threat Modeling Assistant")
st.markdown(
    "**This tool turns a plain-language description of a connected-vehicle system "
    "into a structured security threat model.** It identifies assets, trust "
    "boundaries, STRIDE threats, attack paths (with a diagram), security "
    "requirements, and test cases — ready to review and export as Markdown."
)

tab_input, tab_result, tab_export = st.tabs(
    ["📝 Input", "📊 Generated Threat Model", "📤 Export"]
)

# --------------------------------------------------------------------------- #
# Tab 1 — Input
# --------------------------------------------------------------------------- #
with tab_input:
    # --- Import an existing report (same format as the Export tab produces) ---
    # Placed before the field widgets so it can repopulate the system name.
    with st.expander("📥 Import a saved report (.md)", expanded=False):
        uploaded = st.file_uploader(
            "Upload a previously exported Markdown report",
            type=["md", "markdown"],
            key="import_file",
            help="Loads the report into the Generated Threat Model and Export tabs.",
        )
        if uploaded is not None and st.button("Load imported report", key="do_import"):
            try:
                text = uploaded.getvalue().decode("utf-8")
            except UnicodeDecodeError:
                st.error("That file isn't valid UTF-8 text. Please upload a .md report.")
            else:
                if not text.strip():
                    st.error("The uploaded file is empty.")
                else:
                    st.session_state["report_md"] = text
                    meta = parse_report(text)
                    if meta.get("system_name"):
                        st.session_state["system_name"] = meta["system_name"]
                    name = meta.get("system_name") or "the imported report"
                    st.success(f"Imported **{name}**. Open the **Generated Threat "
                               "Model** or **Export** tab to view it.")

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
        st.graphviz_chart(mermaid_to_dot(diagram), use_container_width=True)
        if is_fallback:
            st.caption("ℹ️ The model did not include a diagram, so a generic "
                       "attack path is shown.")
        else:
            st.caption("Parsed from the report's attack-path diagram.")
        with st.expander("Show diagram source (Mermaid)"):
            st.code(diagram, language="text")
        st.divider()
        # Hide the raw mermaid code block from the displayed body (it would show
        # as plain text); the diagram is rendered above and kept in the export.
        st.markdown(strip_mermaid_blocks(report_md))

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
