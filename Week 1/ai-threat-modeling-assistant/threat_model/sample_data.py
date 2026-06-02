"""Sample system used by the 'Load Sample' button in the app."""

SAMPLE_SYSTEM = {
    "system_name": "Customer Web Portal",
    "description": (
        "A customer-facing web application with a single-page frontend, a REST "
        "API backend, and a relational database. Users sign up and log in, manage "
        "their profile, and place orders. The backend integrates with a "
        "third-party payment provider and an email service, and stores data in a "
        "managed cloud database. Admin staff use a separate admin console."
    ),
    "business_impact": (
        "High — the portal handles customer accounts, personal data, and "
        "payments. A compromise could lead to data breach, financial fraud, "
        "regulatory penalties, and loss of customer trust."
    ),
    "data_handled": (
        "User credentials and sessions, personal profile data (PII), order "
        "history, and payment references/tokens (no raw card data stored)."
    ),
    "external_interfaces": (
        "Web browser clients (HTTPS), public REST API, admin console, "
        "third-party payment gateway, transactional email provider, and a "
        "managed cloud database."
    ),
}
