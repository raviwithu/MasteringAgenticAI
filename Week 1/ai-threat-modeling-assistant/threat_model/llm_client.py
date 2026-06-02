"""LLM client for the AI Threat Modeling Assistant.

Supports two modes:

* **OpenAI** — used when ``OPENAI_API_KEY`` is set and ``USE_MOCK_LLM`` is not
  forcing mock mode.
* **Mock** — a fully offline generator that returns a realistic, structured
  system threat model. This lets the app run with no API key (handy for
  training/demos) and is the default in ``.env.example``.
"""

from __future__ import annotations

import os

from dotenv import load_dotenv

_TRUTHY = {"1", "true", "yes", "on"}


def _force_mock() -> bool:
    return os.getenv("USE_MOCK_LLM", "").strip().lower() in _TRUTHY


def _have_key() -> bool:
    return bool(os.getenv("OPENAI_API_KEY", "").strip())


def active_mode() -> str:
    """Return ``"mock"`` or ``"openai"`` for the current configuration."""
    load_dotenv()
    if _force_mock() or not _have_key():
        return "mock"
    return "openai"


def generate_threat_model(
    prompt: str,
    system_inputs: dict | None = None,
    model: str | None = None,
) -> str:
    """Generate a threat-model Markdown report from a prompt.

    Args:
        prompt: The prompt produced by ``build_threat_model_prompt``.
        system_inputs: Optional dict of the raw input fields (system_name,
            description, ...). Used to make the offline mock output specific.
        model: Optional model override (defaults to ``OPENAI_MODEL`` or gpt-4o-mini).

    Returns:
        The generated report as a Markdown string. Falls back to the mock
        generator if the OpenAI call fails for any reason.
    """
    load_dotenv()
    system_inputs = system_inputs or {}

    if active_mode() == "mock":
        return _mock_threat_model(system_inputs)

    try:
        from openai import OpenAI

        client = OpenAI()
        model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        response = client.chat.completions.create(
            model=model,
            temperature=0.2,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a product/application security threat modeling "
                        "assistant. Respond only in GitHub-flavored Markdown."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
        )
        return response.choices[0].message.content or _mock_threat_model(system_inputs)
    except Exception as exc:  # noqa: BLE001 - surface any failure, then degrade gracefully
        fallback = _mock_threat_model(system_inputs)
        return (
            f"> ⚠️ Live LLM call failed ({type(exc).__name__}: {exc}).\n"
            "> Showing offline mock output instead.\n\n" + fallback
        )


# --------------------------------------------------------------------------- #
# Offline mock generator
# --------------------------------------------------------------------------- #
def _mock_threat_model(system_inputs: dict) -> str:
    """Produce a realistic, generic threat model without calling any API."""
    name = (system_inputs.get("system_name") or "Target System").strip()
    description = (
        system_inputs.get("description")
        or "A software system exposing user-facing and backend interfaces."
    ).strip()
    business_impact = (system_inputs.get("business_impact") or "").strip()
    data_handled = (
        system_inputs.get("data_handled")
        or "User accounts, credentials, personal data, and application records."
    ).strip()
    external_interfaces = (
        system_inputs.get("external_interfaces")
        or "Web/Mobile clients (HTTPS), public API, database, third-party services."
    ).strip()

    impact_line = (
        f"Business impact: {business_impact}\n\n" if business_impact else ""
    )

    return f"""## System Overview
**{name}** — {description}

{impact_line}This system exposes an external attack surface (clients and public
APIs) that reaches backend services and data stores, making it a high-value
target: it authenticates users, processes requests, and stores sensitive data.

**External interfaces:** {external_interfaces}
**Data handled:** {data_handled}

## Key Assets
| Asset | Description | Sensitivity |
|-------|-------------|-------------|
| User credentials & sessions | Passwords, tokens, and session identifiers | Critical |
| Personal / customer data | PII and business records stored by the system | High |
| Secrets & keys | API keys, signing keys, DB credentials, TLS certs | Critical |
| Application database | Primary data store behind the services | Critical |
| Admin / privileged functions | Configuration and elevated operations | High |
| Audit & logging data | Records used for accountability and detection | Medium |

## Trust Boundaries
- **Internet ↔ Web/API frontend:** untrusted clients reaching the application (authN/authZ, input validation).
- **Frontend ↔ Application/API services:** request handling and session validation.
- **Application ↔ Database / object storage:** access to sensitive data at rest.
- **Service ↔ Third-party integrations:** data shared with or trust placed in external providers.
- **User/admin ↔ Privileged operations:** the boundary protecting elevated functions.

## Threats
| ID | STRIDE | Threat | Affected Asset/Component | Likelihood | Impact |
|----|--------|--------|--------------------------|------------|--------|
| T1 | Spoofing | Credential stuffing or stolen token used to impersonate a user | User credentials & sessions | High | High |
| T2 | Tampering | Injection (SQL/command) or parameter tampering alters data/logic | Application services / DB | Medium | High |
| T3 | Information disclosure | Sensitive data exposed via weak TLS, misconfig, or verbose errors | Personal / customer data | Medium | High |
| T4 | Elevation of privilege | Broken access control lets a user reach admin functions | Admin / privileged functions | Medium | High |
| T5 | Information disclosure | Hard-coded or leaked secrets grant backend access | Secrets & keys | Medium | High |
| T6 | Denial of service | Resource exhaustion / flooding makes the service unavailable | Application services | Medium | Medium |
| T7 | Repudiation | Missing or tamperable audit logs hide malicious actions | Audit & logging data | Medium | Medium |
| T8 | Tampering | Compromised third-party dependency or integration injects code/data | Third-party integrations | Low | High |

## Attack Paths
1. **Account takeover → data theft (T1 → T3):** attacker reuses leaked credentials or steals a session token → authenticates as the victim → reads or exports their personal data.
2. **Injection → privilege escalation (T2 → T4):** attacker submits crafted input that the app fails to validate → manipulates a query/logic → reaches data or functions beyond their role.
3. **Secret leakage → backend access (T5):** attacker finds a secret in a repo, log, or response → uses it to call internal services or the database directly.
4. **Supply-chain compromise (T8):** attacker compromises a dependency or integration → malicious code runs inside the trusted application.

```mermaid
flowchart TD
    A[External Attacker] --> B[Stolen Credentials / Token]
    B --> C[Web Frontend]
    C --> D[API Gateway]
    D --> E[Application Server]
    E --> F[Database]
```

## Security Requirements
- **SR1 (T1):** Enforce MFA, rate-limit logins, detect credential stuffing, and use short-lived, scoped session tokens.
- **SR2 (T2):** Use parameterized queries/ORM, validate and encode all input/output, and apply least-privilege DB accounts.
- **SR3 (T3):** Enforce TLS 1.2+, encrypt sensitive data at rest, return generic errors, and never log secrets/PII.
- **SR4 (T4):** Enforce server-side authorization on every request (deny by default); cover object-level access control.
- **SR5 (T5):** Store secrets in a managed vault, rotate regularly, and keep them out of code, logs, and client responses.
- **SR6 (T6):** Apply rate limiting, quotas, timeouts, and autoscaling; fail safe under load.
- **SR7 (T7):** Produce tamper-evident, centralized audit logs for security-relevant actions (actor, time, result).
- **SR8 (T8):** Pin and scan dependencies, verify integrity, and constrain third-party permissions.

## Security Test Cases
| ID | Linked Requirement/Threat | Test objective | Expected result |
|----|---------------------------|----------------|-----------------|
| TC1 | SR1 / T1 | Attempt login reuse / token replay without MFA | Blocked; rate-limited; event logged |
| TC2 | SR2 / T2 | Submit SQL/command injection and tampered parameters | Input rejected/escaped; no data leak or logic change |
| TC3 | SR3 / T3 | Connect over weak TLS and trigger an error | Weak TLS refused; errors reveal no sensitive detail |
| TC4 | SR4 / T4 | Access an admin endpoint / another user's object as a normal user | Denied by server-side authorization |
| TC5 | SR5 / T5 | Search code, logs, and responses for secrets | No secrets exposed; vault-backed retrieval only |
| TC6 | SR6 / T6 | Flood the service with requests | Throttled; remains available or fails safe |
| TC7 | SR7 / T7 | Perform an action and inspect the audit log | Recorded with actor, timestamp, and outcome |

## Assumptions
- The platform provides baseline hardening (patched OS, network segmentation, WAF where applicable).
- A secrets manager and centralized logging are available to the application.
- Authentication is handled by the application or a trusted identity provider.
- Third-party services are reputable but treated as untrusted boundaries.

## Residual Risks
- **Zero-day vulnerabilities** in frameworks or dependencies remain until patched.
- **Insider misuse** of legitimate privileges is only partially mitigated by auditing.
- **Sophisticated phishing/social engineering** can still yield valid credentials despite MFA.
- **Supply-chain compromise** upstream of the build may evade application-side controls.
"""
