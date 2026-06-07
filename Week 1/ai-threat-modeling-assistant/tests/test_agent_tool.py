"""Tests for the service API and the LangChain tool (offline / mock mode).

These exercise the tool-calling plumbing *without* a live LLM:
- the service entry point used by both the UI and the tool;
- the `generate_threat_model` tool's schema and that invoking it produces a report.

The full agent (the LLM *deciding* to call the tool) needs a real tool-calling
model, so it is exercised manually with an API key, not in offline CI.
"""

from __future__ import annotations

import pytest

from threat_model.prompts import SECTION_ORDER
from threat_model.service import generate_threat_model_report

SYSTEM = {
    "system_name": "Customer Web Portal",
    "description": (
        "A customer web app with a single-page frontend, a REST API, and a "
        "relational database. Users sign up, log in, and place orders; the backend "
        "integrates with a third-party payment provider."
    ),
    "business_impact": "High — customer accounts, personal data, and payments.",
    "data_handled": "Credentials, sessions, PII, order history, payment tokens.",
    "external_interfaces": "Web/API clients, payment gateway, email, database.",
}


# --------------------------------------------------------------------------- #
# Service (no LangChain needed)
# --------------------------------------------------------------------------- #
def test_service_generates_full_report():
    out = generate_threat_model_report(**SYSTEM)
    assert set(out) >= {"report_md", "system_name", "inputs"}
    report = out["report_md"]
    assert report.startswith("# Threat Model — Customer Web Portal")
    for section in SECTION_ORDER:
        assert f"## {section}" in report, f"missing section: {section}"


def test_service_requires_description():
    with pytest.raises(ValueError):
        generate_threat_model_report(description="   ")


# --------------------------------------------------------------------------- #
# Tool (needs langchain_core; skipped if not installed)
# --------------------------------------------------------------------------- #
def test_tool_schema_and_name():
    pytest.importorskip("langchain_core")
    from threat_model.agent_tools import ThreatModelInput, make_threat_model_tool

    tool = make_threat_model_tool()
    assert tool.name == "generate_threat_model"
    fields = ThreatModelInput.model_fields
    assert "description" in fields                      # required input
    for opt in ("system_name", "business_impact", "data_handled", "external_interfaces"):
        assert opt in fields


def test_tool_invoke_returns_report():
    pytest.importorskip("langchain_core")
    from threat_model.agent_tools import make_threat_model_tool

    tool = make_threat_model_tool()
    report = tool.invoke({
        "description": SYSTEM["description"],
        "system_name": SYSTEM["system_name"],
    })
    assert isinstance(report, str)
    assert report.startswith("# Threat Model")
    assert "## Threats" in report
