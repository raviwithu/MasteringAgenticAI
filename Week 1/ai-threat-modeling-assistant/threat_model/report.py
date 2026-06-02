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

# Matches the "| **System** | <name> |" metadata row written by create_markdown_report.
_SYSTEM_ROW_RE = re.compile(r"^\|\s*\*\*System\*\*\s*\|\s*(.+?)\s*\|", re.MULTILINE)
# Matches the "# Threat Model — <name>" title written by create_markdown_report.
_TITLE_RE = re.compile(r"^#\s+Threat Model\s+[—-]\s+(.+?)\s*$", re.MULTILINE)

# Parses Mermaid flowchart edges like `A[Label] --> B[Other]` (labels optional).
_MM_EDGE_RE = re.compile(
    r"([A-Za-z0-9_]+)(?:\[[^\]]*\])?\s*-->\s*([A-Za-z0-9_]+)(?:\[[^\]]*\])?"
)
# Parses Mermaid node label declarations like `A[External Attacker]`.
_MM_NODE_RE = re.compile(r"([A-Za-z0-9_]+)\[([^\]]*)\]")


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


def strip_mermaid_blocks(
    markdown: str,
    note: str = "_(see the rendered Attack Path Diagram above)_",
) -> str:
    """Replace ```mermaid``` blocks with a short note (for in-app display).

    Streamlit's ``st.markdown`` shows a mermaid code block as raw text, so we
    remove it from the displayed body and render the diagram separately. The
    exported report keeps the mermaid block intact (GitHub renders it).
    """
    return _MERMAID_RE.sub(note + "\n", markdown or "")


def mermaid_to_dot(mermaid: str, rankdir: str = "TB") -> str:
    """Convert a simple Mermaid ``flowchart`` into Graphviz DOT.

    Streamlit renders DOT natively via ``st.graphviz_chart`` (offline, no CDN),
    which is far more reliable than embedding Mermaid.js. Only the basic
    ``A[Label] --> B[Label]`` flowchart syntax used by this app is supported.
    """
    labels: dict[str, str] = {}
    edges: list[tuple[str, str]] = []
    for line in (mermaid or "").splitlines():
        line = line.strip()
        if not line or line.lower().startswith(("flowchart", "graph")):
            continue
        for node_id, label in _MM_NODE_RE.findall(line):
            labels[node_id] = label.strip()
        for src, dst in _MM_EDGE_RE.findall(line):
            edges.append((src, dst))

    # Make sure every endpoint that appears in an edge has a label.
    for src, dst in edges:
        labels.setdefault(src, src)
        labels.setdefault(dst, dst)

    def esc(text: str) -> str:
        return text.replace("\\", "\\\\").replace('"', '\\"')

    out = [
        "digraph AttackPath {",
        f"  rankdir={rankdir};",
        '  node [shape=box, style="rounded,filled", fillcolor="#eaf1fb", '
        'color="#4178be", fontname="Helvetica"];',
        '  edge [color="#c0392b", penwidth=1.4];',
    ]
    for node_id, label in labels.items():
        out.append(f'  {node_id} [label="{esc(label)}"];')
    for src, dst in edges:
        out.append(f"  {src} -> {dst};")
    out.append("}")
    return "\n".join(out)


def parse_report(markdown: str) -> dict:
    """Parse a report previously produced by :func:`create_markdown_report`.

    Recovers the system name from the metadata table (falling back to the title),
    so an imported ``.md`` file can repopulate the app. Plain Markdown that wasn't
    produced by this tool is still accepted — ``system_name`` is simply ``None``.

    Args:
        markdown: The full Markdown text of an exported report.

    Returns:
        ``{"system_name": str | None, "markdown": str}``.
    """
    md = markdown or ""
    name = None
    match = _SYSTEM_ROW_RE.search(md) or _TITLE_RE.search(md)
    if match:
        candidate = match.group(1).strip()
        # "Threat Model" is the default title used when no name was given.
        if candidate and candidate.lower() != "threat model":
            name = candidate
    return {"system_name": name, "markdown": md}


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
    "Web Frontend",
    "API Gateway",
    "Application Server",
    "Database",
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
