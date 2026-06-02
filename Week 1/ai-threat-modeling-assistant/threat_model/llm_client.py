"""LLM client for the AI Threat Modeling Assistant.

Supports two modes:

* **OpenAI** — used when ``OPENAI_API_KEY`` is set and ``USE_MOCK_LLM`` is not
  forcing mock mode.
* **Mock** — a fully offline generator that returns a realistic, structured
  automotive threat model. This lets the app run with no API key (handy for
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
                        "You are an automotive product security threat modeling "
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
    """Produce a realistic automotive threat model without calling any API."""
    name = (system_inputs.get("system_name") or "Connected Vehicle System").strip()
    description = (
        system_inputs.get("description")
        or "A connected automotive system exposing remote and in-vehicle interfaces."
    ).strip()
    business_impact = (system_inputs.get("business_impact") or "").strip()
    data_handled = (
        system_inputs.get("data_handled")
        or "Telemetry, location, diagnostics, and remote command data."
    ).strip()
    external_interfaces = (
        system_inputs.get("external_interfaces")
        or "Cloud API (HTTPS), Mobile App (BLE/Cloud), Cellular (TCU), CAN, OBD-II, OTA."
    ).strip()

    impact_line = (
        f"Business impact: {business_impact}\n\n" if business_impact else ""
    )

    return f"""## System Overview
**{name}** — {description}

{impact_line}This system bridges external networks (cloud, mobile, cellular) and the
in-vehicle network (CAN / Automotive Ethernet), making it a high-value target: it
can route remote commands toward safety-relevant ECUs and exposes diagnostic and
OTA functionality.

**External interfaces:** {external_interfaces}
**Data handled:** {data_handled}

## Key Assets
| Asset | Description | Sensitivity |
|-------|-------------|-------------|
| Remote command channel | Path that delivers remote actions to in-vehicle ECUs | Critical |
| OTA update mechanism | Firmware/software delivery and status reporting | Critical |
| Cryptographic keys / certificates | TLS, code-signing, and mutual-auth credentials | Critical |
| Vehicle telemetry & GPS | Location and operational data uploaded to cloud | High |
| Diagnostic access (OBD-II/UDS) | Read/write access to ECU diagnostics | High |
| CAN / in-vehicle bus access | Gateway position on the internal network | Critical |

## Trust Boundaries
- **Internet ↔ Cloud API:** untrusted clients reaching backend services (authN/authZ, input validation).
- **Cloud ↔ TCU (cellular):** remote commands crossing from backend into the vehicle.
- **Mobile App ↔ Cloud / BLE:** user device that may be rooted or impersonated.
- **Gateway ↔ in-vehicle network (CAN/Ethernet):** the most critical boundary — external requests must never reach safety ECUs unfiltered.
- **Diagnostics/OTA ↔ ECUs:** privileged maintenance paths that bypass normal flows.

## Threats
| ID | STRIDE | Threat | Affected Asset/Component | Likelihood | Impact |
|----|--------|--------|--------------------------|------------|--------|
| T1 | Spoofing | Forged remote command impersonating the cloud backend | Remote command channel / TCU | Medium | High |
| T2 | Tampering | Malicious or rolled-back OTA image accepted by the vehicle | OTA update mechanism | Medium | High |
| T3 | Information disclosure | Telemetry/location intercepted via weak TLS or logging | Vehicle telemetry & GPS | Medium | Medium |
| T4 | Elevation of privilege | Diagnostic (UDS) session unlocks privileged ECU functions | Diagnostic access | Medium | High |
| T5 | Tampering | Injection of CAN frames through the gateway to actuate ECUs | CAN / in-vehicle bus | Low | High |
| T6 | Denial of service | Flooding cellular/CAN interface to disrupt remote features | TCU / gateway | Medium | Medium |
| T7 | Spoofing | Cloned/rooted mobile app or stolen token issuing commands | Mobile App ↔ Cloud | Medium | Medium |
| T8 | Repudiation | Missing audit trail for remote actions and OTA events | Backend logging | Medium | Medium |

## Attack Paths
1. **Remote command injection (T7 → T1 → T5):** attacker steals a mobile session token → calls the cloud command API as the user → backend relays the command to the TCU → gateway forwards an unfiltered frame onto CAN, actuating an ECU.
2. **Malicious OTA (T2):** attacker compromises an OTA artifact or its metadata → vehicle fails to verify the signature/version → tampered firmware is installed on the gateway/ECU.
3. **Diagnostics abuse (physical/near-field) (T4):** attacker with OBD-II or BLE proximity opens a UDS session → weak seed/key unlock → reads keys or writes ECU memory.
4. **Telemetry interception (T3):** attacker on a hostile network downgrades/inspects TLS → harvests location and identifiers for tracking or correlation.

```mermaid
flowchart TD
    A[External Attacker] --> B[Mobile App / Stolen Token]
    B --> C[Cloud API]
    C --> D[TCU - Cellular]
    D --> E[Vehicle Gateway]
    E --> F[CAN Network]
    F --> G[Target ECU]
```

## Security Requirements
- **SR1 (T1, T7):** Mutually authenticate cloud↔TCU and enforce per-command authorization with short-lived, scoped tokens.
- **SR2 (T2):** Verify OTA images with code signing **and** anti-rollback (monotonic version counters) before install.
- **SR3 (T3):** Enforce TLS 1.2+ with certificate pinning; never log raw location/PII; encrypt sensitive data at rest.
- **SR4 (T4):** Require strong UDS security-access (per-ECU keys, attempt lockout); gate write/flash routines behind hardware-backed auth.
- **SR5 (T5):** Gateway must allow-list and rate-limit messages crossing to CAN; reject externally sourced safety-critical frames.
- **SR6 (T6):** Rate-limit and prioritize traffic on cellular/CAN; fail safe and degrade gracefully under load.
- **SR7 (T8):** Produce tamper-evident audit logs for all remote commands and OTA events, exported to the backend.

## Security Test Cases
| ID | Linked Requirement/Threat | Test objective | Expected result |
|----|---------------------------|----------------|-----------------|
| TC1 | SR1 / T1 | Replay a captured remote command without valid auth | Command rejected; event logged |
| TC2 | SR2 / T2 | Attempt to install an unsigned and an older-version OTA image | Both rejected by signature/anti-rollback checks |
| TC3 | SR3 / T3 | Connect with an invalid/self-signed server cert | Connection refused (pinning enforced) |
| TC4 | SR4 / T4 | Brute-force the UDS security-access seed/key | Lockout after N attempts; no unlock |
| TC5 | SR5 / T5 | Send an external safety-critical frame toward CAN via the gateway | Frame filtered/dropped at the boundary |
| TC6 | SR6 / T6 | Flood the cellular/CAN interface with traffic | Service remains responsive or fails safe |
| TC7 | SR7 / T8 | Issue a remote command and inspect logs | Action recorded with actor, time, and result |

## Assumptions
- The vehicle and backend support secure boot and a hardware security module / secure element for key storage.
- Cloud services already enforce baseline authentication; this model focuses on the vehicle-facing surface.
- Physical access is possible but not continuous (e.g. workshop, OBD-II dongle).
- OTA is delivered over an authenticated channel originating from a trusted build pipeline.

## Residual Risks
- A sufficiently resourced attacker with **prolonged physical access** may still extract keys via side channels.
- **Supply-chain compromise** of an OTA artifact before signing is out of scope of vehicle-side controls.
- **Zero-day vulnerabilities** in third-party stacks (TLS, BLE, cellular baseband) remain until patched via OTA.
- Insider misuse of legitimate backend command privileges is only partially mitigated by auditing.
"""
