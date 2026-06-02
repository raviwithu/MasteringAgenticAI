"""Prompt construction for the AI Threat Modeling Assistant.

The single public function, :func:`build_threat_model_prompt`, assembles a clear,
detailed instruction that asks the model to act as a *product/application security*
threat-modeling assistant and to return a well-structured Markdown report.
"""

# The exact sections (in order) the model is asked to produce. Kept as a constant
# so other modules (e.g. the mock LLM) can stay in sync with the prompt.
SECTION_ORDER = [
    "System Overview",
    "Key Assets",
    "Trust Boundaries",
    "Threats",
    "Attack Paths",
    "Security Requirements",
    "Security Test Cases",
    "Assumptions",
    "Residual Risks",
]


def _field(label: str, value: str | None) -> str:
    """Render an optional input field, or note that it was not provided."""
    value = (value or "").strip()
    return f"- **{label}:** {value}" if value else f"- **{label}:** (not provided)"


def build_threat_model_prompt(
    system_name: str,
    description: str,
    business_impact: str = "",
    data_handled: str = "",
    external_interfaces: str = "",
) -> str:
    """Build the LLM prompt for generating a structured threat model.

    Args:
        system_name: Short name of the system under analysis.
        description: Free-text description of the system / architecture.
        business_impact: Optional business-impact context.
        data_handled: Optional description of the data the system processes.
        external_interfaces: Optional list of external interfaces / entry points.

    Returns:
        A complete prompt string ready to send to the LLM.
    """
    system_name = (system_name or "Unnamed System").strip()
    description = (description or "").strip()

    numbered_sections = "\n".join(
        f"{i}. {name}" for i, name in enumerate(SECTION_ORDER, start=1)
    )

    inputs_block = "\n".join(
        [
            _field("System name", system_name),
            _field("Business impact", business_impact),
            _field("Data handled", data_handled),
            _field("External interfaces", external_interfaces),
        ]
    )

    return f"""You are an expert **product/application security** threat-modeling assistant.
You help engineers analyze any kind of software or system (web and mobile apps,
APIs and microservices, cloud and on-prem infrastructure, data stores, IoT and
embedded devices, third-party integrations) and produce actionable threat models.
Apply established practice (OWASP, NIST) where relevant, and classify threats
using **STRIDE** (Spoofing, Tampering, Repudiation, Information disclosure,
Denial of service, Elevation of privilege).

## System under analysis

{inputs_block}

### System description
{description if description else "(no description provided)"}

## Your task

Produce a thorough but concise **threat model** for the system above. Respond in
**GitHub-flavored Markdown only** (no preamble, no code fences around the whole
report). Use these sections, in this exact order, each as a level-2 heading (`##`):

{numbered_sections}

### Guidance per section
- **System Overview** — restate the system, its purpose, and main components.
- **Key Assets** — what attackers want to reach/abuse (data, keys, functions,
  safety-relevant capabilities). Use a Markdown table: Asset | Description | Sensitivity.
- **Trust Boundaries** — where trust changes (e.g. internet↔frontend,
  frontend↔API, app↔database, service↔third-party, user device↔backend).
  Explain why each matters.
- **Threats** — a Markdown table: ID | STRIDE | Threat | Affected Asset/Component |
  Likelihood (Low/Med/High) | Impact (Low/Med/High). Use IDs like T1, T2, ...
  Reference concrete entry points and interfaces (network/HTTP, authentication,
  APIs, file/object storage, message queues, third-party services) where useful.
- **Attack Paths** — 2–4 realistic multi-step paths (numbered steps) showing how an
  attacker chains threats from an entry point to an asset. **Then include one
  simple Mermaid attack-path diagram** based on the system description, using a
  `flowchart TD` from the external entry point through intermediate components to
  the target asset. Use this exact fenced format:

  ```mermaid
  flowchart TD
      A[External Attacker] --> B[Web Frontend]
      B --> C[API Gateway]
      C --> D[Application Server]
      D --> E[Database]
  ```

  Adapt the node labels to the actual system. Keep it to a single, readable path.
- **Security Requirements** — concrete, testable controls mapped back to threat IDs.
- **Security Test Cases** — a Markdown table: ID | Linked Requirement/Threat |
  Test objective | Expected result. Use IDs like TC1, TC2, ...
- **Assumptions** — what you assumed about the system/environment.
- **Residual Risks** — risks that remain after the proposed controls.

Be specific to the described system. Prefer concrete, realistic examples over
vague advice. Keep each section focused and useful to an engineer.
"""
