"""Jira -> Claude pipeline, adapted from ai-automated-release-notes-pipeline.
This code blocks while it waits on the network, so LiveGenerator runs it in a thread."""
import requests
from anthropic import Anthropic

from app.config import settings

MODEL = "claude-opus-4-5"
JIRA_TIMEOUT = 30  # seconds, per Jira call
CLAUDE_TIMEOUT = 60  # seconds, per Claude call

# Optional guidance about your product, added to the prompt. For example:
# PRODUCT_GUIDANCE = "These release notes are for a B2B payment processing platform."
PRODUCT_GUIDANCE = ""


class NoTicketsError(Exception):
    """No Jira tickets carry the release label."""


def _jira_get(path: str, **kwargs) -> requests.Response:
    return requests.get(
        f"{settings.jira_url}{path}",
        auth=(settings.jira_email, settings.jira_token),
        headers={"Accept": "application/json"},
        timeout=JIRA_TIMEOUT,
        **kwargs,
    )


def get_project(project_key: str) -> dict | None:
    """Return the Jira project, or None if it does not exist."""
    response = _jira_get(f"/rest/api/3/project/{project_key}")
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return response.json()


def get_jira_tickets(project_key: str, label: str) -> list[dict]:
    """Fetch all tickets in the project that carry the release label."""
    response = _jira_get(
        "/rest/api/3/search/jql",
        params={
            "jql": f'project = {project_key} AND labels = "{label}"',
            "fields": ["summary", "description", "issuetype", "status"],
            "maxResults": 50,
        },
    )
    response.raise_for_status()
    return response.json()["issues"]


def format_tickets_for_prompt(tickets: list[dict]) -> str:
    """Convert Jira tickets into plain text for the Claude prompt."""
    lines = []
    for ticket in tickets:
        key = ticket["key"]
        summary = ticket["fields"]["summary"]
        itype = ticket["fields"]["issuetype"]["name"]

        # Description is in Atlassian Document Format - extract plain text
        desc_field = ticket["fields"]["description"]
        if desc_field and "content" in desc_field:
            desc_parts = []
            for block in desc_field["content"]:
                if block.get("type") == "paragraph":
                    for inline in block.get("content", []):
                        if inline.get("type") == "text":
                            desc_parts.append(inline["text"])
            description = " ".join(desc_parts)
        else:
            description = "No description provided."

        lines.append(f"[{key}] ({itype}) {summary}\n  Description: {description}")

    return "\n\n".join(lines)


def write_notes(product: str, label: str, tickets_text: str) -> str:
    """Send tickets to Claude and get back formatted release notes."""
    client = Anthropic(api_key=settings.anthropic_api_key, timeout=CLAUDE_TIMEOUT)

    guidance = f"{PRODUCT_GUIDANCE}\n\n" if PRODUCT_GUIDANCE else ""
    prompt = f"""You are a technical writer producing release notes for {product}.

{guidance}Below is a list of Jira tickets included in release {label}.
Write professional release notes in the following format:

- A short introductory sentence for the release
- Three sections: Bug Fixes, Improvements, New Features
- Each item should be one clear sentence written for a technical but non-developer audience
- Do not use Jira ticket keys in the output
- Use plain Markdown formatting

Tickets:
{tickets_text}"""

    message = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


def generate_release_notes(project_key: str, version: str) -> str:
    """Return the finished release notes as Markdown. `version` is the Jira label, exactly as written."""
    project = get_project(project_key)
    tickets = get_jira_tickets(project_key, version)
    if not tickets:
        raise NoTicketsError(version)
    notes = write_notes(project["name"], version, format_tickets_for_prompt(tickets))
    return f"# {project['name']} Release Notes — {version}\n\n{notes}"