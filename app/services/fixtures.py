"""Sample release-notes content for mock mode. Same input always gives the same output."""

SECTIONS = {
    "New features": [
        (101, "Bulk export of reports"),
        (108, "Saved filters on the dashboard"),
    ],
    "Changes": [
        (112, "Search results now sort by relevance by default"),
        (115, "Session timeout increased from 15 to 30 minutes"),
    ],
    "Fixed bugs": [
        (120, "Export no longer fails for reports with more than 10,000 rows"),
        (123, "Dashboard filters reset after a browser refresh"),
        (127, "Monthly summary showed wrong totals for 31-day months"),
    ],
    "Known issues": [
        (131, "PDF export may omit custom fonts on some systems"),
    ],
}


def render_notes(project_key: str, version: str) -> str:
    lines = [f"# {project_key} {version} release notes", ""]
    for title, items in SECTIONS.items():
        lines += [f"## {title}", ""]
        lines += [f"- {project_key}-{number}: {text}" for number, text in items]
        lines.append("")
    return "\n".join(lines)