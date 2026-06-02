"""AI Threat Modeling Assistant — core package.

Exposes the prompt builder, LLM client, report helpers, and sample data used by
the Streamlit app (``app.py``).
"""

from .prompts import SECTION_ORDER, build_threat_model_prompt
from .llm_client import active_mode, generate_threat_model
from .report import (
    attack_path_from_markdown,
    build_attack_path_diagram,
    build_report,
    create_markdown_report,
    extract_mermaid_blocks,
    save_report,
)
from .sample_data import SAMPLE_SYSTEM

__all__ = [
    "SECTION_ORDER",
    "build_threat_model_prompt",
    "active_mode",
    "generate_threat_model",
    "attack_path_from_markdown",
    "build_attack_path_diagram",
    "build_report",
    "create_markdown_report",
    "extract_mermaid_blocks",
    "save_report",
    "SAMPLE_SYSTEM",
]
