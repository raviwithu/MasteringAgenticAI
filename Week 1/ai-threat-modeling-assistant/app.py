"""AI Threat Modeling Assistant — Streamlit UI.

Paste a system description (optionally with name, business impact, data handled,
and external interfaces), click **Generate Threat Model**, and the app builds a
prompt, calls the LLM (OpenAI or an offline mock), and renders + exports a
structured Markdown threat model.
"""

from __future__ import annotations

import streamlit as st

from threat_model.llm_client import active_mode, generate_threat_model
from threat_model.prompts import build_threat_model_prompt
from threat_model.report import build_report, save_report
from threat_model.sample_data import SAMPLE_SYSTEM

# --------------------------------------------------------------------------- #
# Page setup & state
# --------------------------------------------------------------------------- #
st.set_page_config(
    page_title="AI Threat Modeling Assistant",
    page_icon="🛡️",
    layout="wide",
)

# Input fields are bound to session_state keys so the "Load Sample" button can
# pre-fill them via a callback before the widgets render.
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
# Sidebar
# --------------------------------------------------------------------------- #
with st.sidebar:
    st.header("About")
    st.write(
        "Generate a structured **automotive product security** threat model from "
        "a plain-language system description."
    )
    mode = active_mode()
    if mode == "mock":
        st.info("**Mode:** offline mock LLM\n\nNo API key needed. Set "
                "`OPENAI_API_KEY` and `USE_MOCK_LLM=false` in `.env` to use OpenAI.")
    else:
        st.success("**Mode:** OpenAI\n\nUsing your configured API key.")
    st.caption("Sections: Overview · Assets · Trust Boundaries · Threats · "
               "Attack Paths · Requirements · Test Cases · Assumptions · Residual Risks")

# --------------------------------------------------------------------------- #
# Header
# --------------------------------------------------------------------------- #
st.title("🛡️ AI Threat Modeling Assistant")
st.markdown(
    "Describe a connected-vehicle system and get a structured threat model: "
    "**assets, trust boundaries, threats (STRIDE), attack paths, security "
    "requirements, and test cases** — exportable as Markdown."
)

# --------------------------------------------------------------------------- #
# Inputs
# --------------------------------------------------------------------------- #
btn_sample, btn_clear, _ = st.columns([1, 1, 4])
btn_sample.button(
    "📋 Load Sample Vehicle Gateway System",
    on_click=load_sample,
    use_container_width=True,
)
btn_clear.button("🧹 Clear", on_click=clear_fields, use_container_width=True)

st.text_area(
    "System description *",
    key="description",
    height=180,
    placeholder="e.g. Vehicle Gateway communicates with TCU, Cloud API, Mobile "
    "App, and in-vehicle ECUs over CAN/Ethernet. It supports remote commands, "
    "telemetry upload, OTA status, and diagnostic access.",
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

generate = st.button("🚀 Generate Threat Model", type="primary",
                     use_container_width=True)

# --------------------------------------------------------------------------- #
# Generate
# --------------------------------------------------------------------------- #
if generate:
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
            st.session_state["report_md"] = build_report(
                raw, inputs["system_name"]
            )

# --------------------------------------------------------------------------- #
# Output
# --------------------------------------------------------------------------- #
report_md = st.session_state.get("report_md", "")
if report_md:
    st.divider()
    st.subheader("Generated Threat Model")

    name = st.session_state["system_name"].strip() or "threat-model"
    dl_col, save_col = st.columns([1, 3])
    dl_col.download_button(
        "⬇️ Download .md",
        data=report_md,
        file_name=f"{name.lower().replace(' ', '-')}-threat-model.md",
        mime="text/markdown",
        use_container_width=True,
    )
    if save_col.button("💾 Save to outputs/", use_container_width=False):
        try:
            path = save_report(report_md, st.session_state["system_name"])
            st.success(f"Saved to `{path}`")
        except OSError as exc:
            st.warning(f"Could not save report: {exc}")

    st.markdown(report_md)
