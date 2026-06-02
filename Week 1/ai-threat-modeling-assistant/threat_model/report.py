"""Report assembly and export helpers.

``create_markdown_report`` wraps the model's raw output with a title, generated
timestamp, and system name. ``save_report`` writes a report to ``outputs/``.
``extract_mermaid_blocks`` pulls any Mermaid diagrams out for in-app rendering.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

# outputs/ lives at the project root, one level above this package.
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "outputs"

# Matches a fenced ```mermaid ... ``` block and captures its body.
_MERMAID_RE = re.compile(r"```mermaid\s*\n(.*?)```", re.DOTALL)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def slugify(name: str) -> str:
    """Turn an arbitrary system name into a filesystem-safe slug."""
    name = (name or "").strip().lower()
    name = re.sub(r"[^a-z0-9]+", "-", name).strip("-")
    return name or "threat-model"


def create_markdown_report(system_name: str, generated_content: str) -> str:
    """Build the final Markdown report.

    Includes a title, the generated date/time, the system name, and the
    model-generated threat-model content.

    Args:
        system_name: Name of the analyzed system (may be empty).
        generated_content: The Markdown threat model produced by the LLM/mock.

    Returns:
        A complete Markdown document ready to display or download.
    """
    title = (system_name or "").strip() or "Threat Model"
    timestamp = _utc_now().strftime("%Y-%m-%d %H:%M UTC")
    header = (
        f"# Threat Model — {title}\n\n"
        "|  |  |\n"
        "|---|---|\n"
        f"| **System** | {title} |\n"
        f"| **Generated** | {timestamp} |\n"
        "| **Tool** | AI Threat Modeling Assistant |\n\n"
        "---\n\n"
    )
    return header + (generated_content or "").strip() + "\n"


# Backwards-compatible alias (earlier code/imports used build_report).
def build_report(markdown_body: str, system_name: str | None = None) -> str:
    """Deprecated alias for :func:`create_markdown_report`."""
    return create_markdown_report(system_name or "", markdown_body)


def extract_mermaid_blocks(markdown: str) -> list[str]:
    """Return the body of every ```mermaid``` block found in ``markdown``."""
    return [m.group(1).strip() for m in _MERMAID_RE.finditer(markdown or "")]


def _node_label(text: str) -> str:
    """Sanitize a node label so it is safe inside a Mermaid `[...]` node."""
    # Mermaid breaks on unescaped brackets/quotes; keep labels simple.
    text = re.sub(r"[\[\]\"|{}()<>]", " ", (text or "").strip())
    text = re.sub(r"\s+", " ", text)
    return text or "Node"


def build_attack_path_diagram(steps: list[str]) -> str:
    """Build a valid Mermaid `flowchart TD` from an ordered list of step labels.

    Each step becomes a node (A, B, C, ...) linked to the next, giving a single
    readable attack path from entry point to target. Returns the diagram body
    *without* the surrounding ```mermaid fences.
    """
    labels = [_node_label(s) for s in (steps or []) if str(s).strip()]
    if not labels:
        labels = ["External Attacker", "Entry Point", "Target Asset"]

    def node_id(i: int) -> str:
        return chr(ord("A") + i) if i < 26 else f"N{i}"

    lines = ["flowchart TD"]
    if len(labels) == 1:
        lines.append(f"    {node_id(0)}[{labels[0]}]")
    else:
        for i in range(len(labels) - 1):
            lines.append(
                f"    {node_id(i)}[{labels[i]}] --> "
                f"{node_id(i + 1)}[{labels[i + 1]}]"
            )
    return "\n".join(lines)


# A generic fallback attack path used when the model output contains no diagram.
DEFAULT_ATTACK_PATH = [
    "External Attacker",
    "Cloud API",
    "TCU (Cellular)",
    "Vehicle Gateway",
    "CAN Network",
    "Target ECU",
]


def attack_path_from_markdown(markdown: str) -> tuple[str, bool]:
    """Return ``(mermaid_body, is_generated)`` for the report's attack path.

    Uses the first ```mermaid``` block in ``markdown`` if present; otherwise
    builds a deterministic fallback diagram. ``is_generated`` is True when the
    fallback was used (i.e. the model did not supply a diagram).
    """
    blocks = extract_mermaid_blocks(markdown)
    if blocks:
        return blocks[0], False
    return build_attack_path_diagram(DEFAULT_ATTACK_PATH), True


def report_filename(system_name: str | None = None) -> str:
    """Build a unique, descriptive ``.md`` filename for a report."""
    stamp = _utc_now().strftime("%Y%m%d-%H%M%S")
    return f"{slugify(system_name or 'threat-model')}-{stamp}.md"


def save_report(
    markdown: str,
    system_name: str | None = None,
    output_dir: Path | str = OUTPUT_DIR,
) -> Path:
    """Write ``markdown`` to ``output_dir`` and return the file path."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / report_filename(system_name)
    path.write_text(markdown, encoding="utf-8")
    return path
