"""Sample automotive system used by the 'Load Sample' button in the app."""

SAMPLE_SYSTEM = {
    "system_name": "Vehicle Gateway",
    "description": (
        "Vehicle Gateway communicates with TCU, Cloud API, Mobile App, and "
        "in-vehicle ECUs over CAN/Ethernet. It supports remote commands, "
        "telemetry upload, OTA status, and diagnostic access."
    ),
    "business_impact": (
        "High — the gateway routes remote commands toward in-vehicle ECUs and "
        "brokers cloud connectivity. A compromise could affect vehicle safety, "
        "customer privacy, fleet availability, and brand trust."
    ),
    "data_handled": (
        "Vehicle telemetry, GPS location, diagnostic trouble codes, remote "
        "command payloads, OTA metadata/status, and vehicle/user identifiers."
    ),
    "external_interfaces": (
        "TCU (cellular), Cloud API (HTTPS), Mobile App (BLE + cloud), in-vehicle "
        "CAN bus, Automotive Ethernet, OBD-II diagnostics, and the OTA update channel."
    ),
}
