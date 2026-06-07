"""LangChain tool definition for threat-model generation.

Exposes the service as a single ``generate_threat_model`` StructuredTool with a
typed argument schema, so a tool-calling agent can invoke it with structured
arguments.
"""

from __future__ import annotations

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from .service import generate_threat_model_report


class ThreatModelInput(BaseModel):
    """Arguments describing the system to threat-model."""

    description: str = Field(
        description="Plain-language description of the system / architecture."
    )
    system_name: str = Field(
        default="", description="Short name of the system (optional)."
    )
    business_impact: str = Field(
        default="", description="Business impact / criticality, if known (optional)."
    )
    data_handled: str = Field(
        default="", description="Sensitive data the system handles, if known (optional)."
    )
    external_interfaces: str = Field(
        default="", description="External interfaces / entry points, if known (optional)."
    )


def _run_tool(
    description: str,
    system_name: str = "",
    business_impact: str = "",
    data_handled: str = "",
    external_interfaces: str = "",
) -> str:
    """Tool body: generate the report and return its Markdown."""
    result = generate_threat_model_report(
        description=description,
        system_name=system_name,
        business_impact=business_impact,
        data_handled=data_handled,
        external_interfaces=external_interfaces,
    )
    return result["report_md"]


def make_threat_model_tool() -> StructuredTool:
    """Build the ``generate_threat_model`` tool for an agent to call."""
    return StructuredTool.from_function(
        func=_run_tool,
        name="generate_threat_model",
        description=(
            "Generate a structured STRIDE threat model for a described software "
            "system. Covers assets, trust boundaries, threats, attack paths, "
            "security requirements, and test cases. Returns a Markdown report. "
            "Call this whenever the user wants a threat model for a system."
        ),
        args_schema=ThreatModelInput,
    )
