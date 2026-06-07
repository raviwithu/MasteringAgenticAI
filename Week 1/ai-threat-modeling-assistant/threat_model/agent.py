"""LangChain tool-calling that drives threat-model generation.

The model is bound to a single tool — ``generate_threat_model`` — and asked to
call it for the system it is given (we force the tool for determinism). We then
execute the tool with the model's chosen arguments and return the report.

We use the ``bind_tools`` pattern (stable across LangChain versions) rather than
the classic ``AgentExecutor`` (which moved to ``langchain-classic`` in LangChain
1.x). Heavy imports are deferred to :func:`run_agent`, so importing this module
is cheap and works even when LangChain isn't installed (the UI falls back to
direct generation in that case).
"""

from __future__ import annotations

import logging
import os
from typing import Any

from .agent_tools import make_threat_model_tool

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "You are a product/application security assistant. When given a system to "
    "analyze, call the `generate_threat_model` tool with the provided details to "
    "produce the report. Do not write the threat model yourself; rely on the "
    "tool's output."
)


def _format_input(inputs: dict[str, Any]) -> str:
    """Turn the form fields into a single instruction for the model."""
    lines = ["Generate a threat model for the following system."]
    labels = [
        ("System name", "system_name"),
        ("Description", "description"),
        ("Business impact", "business_impact"),
        ("Data handled", "data_handled"),
        ("External interfaces", "external_interfaces"),
    ]
    for label, key in labels:
        value = (inputs.get(key) or "").strip()
        if value:
            lines.append(f"{label}: {value}")
    return "\n".join(lines)


def run_agent(inputs: dict[str, Any]) -> dict[str, Any]:
    """Bind the tool to the model, let it call the tool, and run it.

    Returns ``{"report_md": str|None, "answer": str, "tool_called": bool}``.
    ``report_md`` is None if no tool call was produced (caller should fall back
    to direct generation).
    """
    from langchain_core.messages import HumanMessage, SystemMessage
    from langchain_openai import ChatOpenAI

    tool = make_threat_model_tool()
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    llm = ChatOpenAI(model=model, temperature=0)
    messages = [
        SystemMessage(content=_SYSTEM_PROMPT),
        HumanMessage(content=_format_input(inputs)),
    ]

    # Force our single tool for determinism; fall back to auto if the provider
    # rejects a forced tool_choice.
    try:
        ai = llm.bind_tools([tool], tool_choice=tool.name).invoke(messages)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Forced tool_choice failed (%s); retrying with auto.", exc)
        ai = llm.bind_tools([tool]).invoke(messages)

    report_md: str | None = None
    for call in getattr(ai, "tool_calls", None) or []:
        if call.get("name") == tool.name:
            report_md = tool.invoke(call.get("args", {}))
            break

    return {
        "report_md": report_md,
        "answer": getattr(ai, "content", "") or "",
        "tool_called": report_md is not None,
    }
