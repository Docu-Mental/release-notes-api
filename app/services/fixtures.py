"""Sample release-notes content for mock mode. Same input always gives the same output.
The layout mirrors what the live pipeline produces: an intro sentence, then three sections."""

INTRO = (
    "This release introduces new security and compliance features for the admin portal, "
    "expands multi-currency reporting capabilities, and addresses several bugs affecting "
    "transaction processing and data exports."
)

SECTIONS = {
    "New Features": [
        "Administrators can now enable two-factor authentication (TOTP-based) for admin portal logins, adding an extra layer of account security.",
        "A new audit log export feature allows administrators to download a complete record of user actions in CSV or PDF format for compliance and regulatory reporting.",
        "Settlement reports can now be generated in the client's local currency, with exchange rates applied as of the original transaction time.",
    ],
    "Improvements": [
        "The v1 payment submission endpoint (`/v1/submit`) is now deprecated and will be retired in v4.0.0; API responses include deprecation headers, and documentation has been updated accordingly.",
        "The API reference documentation for the v2 transaction endpoint has been updated to reflect new pagination parameters.",
    ],
    "Bug Fixes": [
        "Fixed an issue where duplicate transaction entries could appear in the ledger after a failed webhook retry.",
        "Reconciliation reports now display a validation error when the selected date range exceeds 90 days, rather than generating an empty file.",
        "The webhook retry limit has been increased from 3 to 5 attempts to reduce missed notifications during brief server outages.",
    ],
}


def render_notes(project_key: str, version: str) -> str:
    lines = [f"# {project_key} Release Notes — {version}", "", INTRO, ""]
    for title, items in SECTIONS.items():
        lines += ["---", "", f"## {title}", ""]
        lines += [f"- {text}" for text in items]
        lines.append("")
    return "\n".join(lines)