"""End-to-end functional test for the threat-modeling flow.

Exercises the whole pipeline a user goes through in the app, with no UI:

    describe a system (+ optional fields)
        -> build the prompt
        -> generate the threat model (offline mock)
        -> assemble the Markdown report
        -> EXPORT it to a file
        -> CHECK the file on disk
        -> IMPORT that same file back

Run it after any code change as a regression check:

    cd "MasteringAgenticAI/Week 1/ai-threat-modeling-assistant"
    pytest
"""

from __future__ import annotations

import pytest

from threat_model.llm_client import active_mode, generate_threat_model
from threat_model.prompts import SECTION_ORDER, build_threat_model_prompt
from threat_model.report import (
    attack_path_from_markdown,
    create_markdown_report,
    mermaid_to_dot,
    parse_report,
    save_report,
)

# A representative system description plus all optional fields — the same kind of
# input a user would type into the app.
SYSTEM = {
    "system_name": "Customer Web Portal",
    "description": (
        "A customer web application with a single-page frontend, a REST API "
        "backend, and a relational database. Users sign up, log in, and place "
        "orders. The backend integrates with a third-party payment provider."
    ),
    "business_impact": "High — handles customer accounts, personal data, and payments.",
    "data_handled": "Credentials, sessions, PII, order history, payment tokens.",
    "external_interfaces": "Web/API clients (HTTPS), payment gateway, email, database.",
}


@pytest.fixture
def generated_report() -> str:
    """Run the generation half of the flow and return the assembled report."""
    prompt = build_threat_model_prompt(**SYSTEM)
    raw = generate_threat_model(prompt, system_inputs=SYSTEM)
    return create_markdown_report(SYSTEM["system_name"], raw)


# --------------------------------------------------------------------------- #
# Generation
# --------------------------------------------------------------------------- #
def test_runs_in_mock_mode():
    """The flow must be exercised offline (no API key required)."""
    assert active_mode() == "mock"


def test_prompt_includes_inputs():
    """The prompt should embed the description and every optional field."""
    prompt = build_threat_model_prompt(**SYSTEM)
    assert SYSTEM["description"] in prompt
    for field in ("business_impact", "data_handled", "external_interfaces"):
        assert SYSTEM[field] in prompt


def test_report_has_all_sections(generated_report):
    """All nine threat-model sections must be present."""
    for section in SECTION_ORDER:
        assert f"## {section}" in generated_report, f"missing section: {section}"


def test_report_header(generated_report):
    """The report carries a title, system name, and generated timestamp."""
    assert generated_report.startswith("# Threat Model — Customer Web Portal")
    assert "**System** | Customer Web Portal" in generated_report
    assert "**Generated**" in generated_report


def test_report_has_parseable_diagram(generated_report):
    """The attack-path diagram must parse and convert to valid Graphviz DOT."""
    diagram, is_fallback = attack_path_from_markdown(generated_report)
    assert not is_fallback, "expected a real diagram from the generated report"
    assert diagram.startswith("flowchart")
    dot = mermaid_to_dot(diagram)
    assert dot.startswith("digraph") and "->" in dot


# --------------------------------------------------------------------------- #
# Export -> check file -> import (the core round-trip)
# --------------------------------------------------------------------------- #
def test_export_check_and_reimport(generated_report, tmp_path):
    """Export the report to a file, verify it, then import the same file back."""
    # --- EXPORT ---
    path = save_report(generated_report, SYSTEM["system_name"], output_dir=tmp_path)

    # --- CHECK THE FILE ---
    assert path.exists(), "export did not create a file"
    assert path.suffix == ".md"
    assert path.parent == tmp_path
    on_disk = path.read_text(encoding="utf-8")
    assert on_disk == generated_report, "file content differs from the report"
    assert on_disk.strip(), "exported file is empty"

    # --- IMPORT THE SAME FILE ---
    meta = parse_report(on_disk)
    assert meta["system_name"] == "Customer Web Portal", "system name not recovered"
    assert meta["markdown"] == on_disk, "import altered the content"

    # Imported content is still complete and renderable.
    for section in SECTION_ORDER:
        assert f"## {section}" in meta["markdown"]
    diagram, is_fallback = attack_path_from_markdown(meta["markdown"])
    assert not is_fallback


def test_filename_is_descriptive(generated_report, tmp_path):
    """Exported filenames should be slugged from the system name."""
    path = save_report(generated_report, SYSTEM["system_name"], output_dir=tmp_path)
    assert path.name.startswith("customer-web-portal-")


# --------------------------------------------------------------------------- #
# Edge cases
# --------------------------------------------------------------------------- #
def test_empty_description_is_flagged_in_prompt():
    """A missing description is surfaced to the model rather than silently dropped."""
    prompt = build_threat_model_prompt("Some System", "")
    assert "no description provided" in prompt.lower()


def test_fallback_diagram_when_report_has_none():
    """Importing a report without a diagram yields the deterministic fallback."""
    diagram, is_fallback = attack_path_from_markdown("# Threat Model\nNo diagram here.")
    assert is_fallback
    assert "flowchart TD" in diagram


def test_import_accepts_plain_markdown():
    """Plain Markdown (not produced by this tool) imports without a system name."""
    meta = parse_report("# Some notes\n\nNot a generated report.")
    assert meta["system_name"] is None
    assert meta["markdown"].startswith("# Some notes")
