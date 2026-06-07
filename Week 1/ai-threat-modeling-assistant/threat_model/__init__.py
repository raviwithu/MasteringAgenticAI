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
    mermaid_to_dot,
    parse_report,
    save_report,
    strip_mermaid_blocks,
)
from .sample_data import SAMPLE_SYSTEM
from .service import generate_threat_model_report

# Note: `agent` / `agent_tools` are intentionally NOT imported here — they pull in
# LangChain. Import them directly (``from threat_model.agent import run_agent``)
# so the rest of the package stays usable without LangChain installed.

__all__ = [
    "SECTION_ORDER",
    "build_threat_model_prompt",
    "active_mode",
    "generate_threat_model",
    "generate_threat_model_report",
    "attack_path_from_markdown",
    "build_attack_path_diagram",
    "build_report",
    "create_markdown_report",
    "extract_mermaid_blocks",
    "mermaid_to_dot",
    "parse_report",
    "save_report",
    "strip_mermaid_blocks",
    "SAMPLE_SYSTEM",
]
