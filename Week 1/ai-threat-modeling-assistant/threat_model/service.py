"""Service layer — one call that produces a full threat-model report.

Wraps the prompt builder, the LLM client, and report assembly behind a single
function so both the Streamlit UI and the LangChain tool share one entry point.
"""

from __future__ import annotations

import logging
from typing import Any

from .llm_client import generate_threat_model
from .prompts import build_threat_model_prompt
from .report import create_markdown_report

logger = logging.getLogger(__name__)


def generate_threat_model_report(
    description: str,
    system_name: str = "",
    business_impact: str = "",
    data_handled: str = "",
    external_interfaces: str = "",
) -> dict[str, Any]:
    """Generate a complete threat-model report from system details.

    Args:
        description: Plain-language description of the system (required).
        system_name: Short name of the system.
        business_impact: Business impact / criticality, if known.
        data_handled: Sensitive data the system handles, if known.
        external_interfaces: External interfaces / entry points, if known.

    Returns:
        ``{"report_md": str, "system_name": str, "inputs": dict}``.

    Raises:
        ValueError: if ``description`` is empty.
    """
    if not description or not description.strip():
        raise ValueError("description is required")

    inputs = {
        "system_name": system_name,
        "description": description,
        "business_impact": business_impact,
        "data_handled": data_handled,
        "external_interfaces": external_interfaces,
    }
    logger.info("Generating threat model for system '%s'", system_name or "(unnamed)")
    prompt = build_threat_model_prompt(
        system_name=system_name,
        description=description,
        business_impact=business_impact,
        data_handled=data_handled,
        external_interfaces=external_interfaces,
    )
    raw = generate_threat_model(prompt, system_inputs=inputs)
    report_md = create_markdown_report(system_name, raw)
    return {"report_md": report_md, "system_name": system_name, "inputs": inputs}
