"""The seam: routes talk to a Generator and never know which one they have."""
import asyncio
from typing import Any, Protocol

import anthropic
import requests

from app.config import settings
from app.services import pipeline
from app.services.fixtures import render_notes

# Special project keys that trigger specific mock behavior. Live mode ignores them.
FAIL_KEY = "FAIL"
SLOW_KEY = "SLOW"
NOT_FOUND_KEY = "NOTFOUND"
SLOW_MULTIPLIER = 10


class GenerationError(Exception):
    """Raised by a generator when a job cannot be completed."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.details = details


class Generator(Protocol):
    """Any class with these two methods qualifies. MockGenerator and LiveGenerator both do,
    so the API contract is the same in both modes."""

    async def project_exists(self, project_key: str) -> bool: ...

    async def generate(self, project_key: str, version: str) -> str:
        """Return release notes as Markdown, or raise GenerationError."""
        ...


class MockGenerator:
    def __init__(self, delay: float):
        self.delay = delay

    async def project_exists(self, project_key: str) -> bool:
        return project_key != NOT_FOUND_KEY

    async def generate(self, project_key: str, version: str) -> str:
        await asyncio.sleep(self.delay * (SLOW_MULTIPLIER if project_key == SLOW_KEY else 1))
        if project_key == FAIL_KEY:
            raise GenerationError(
                "Mock failure: the generator could not complete this job.",
                {"project_key": project_key},
            )
        return render_notes(project_key, version)


class LiveGenerator:
    """Runs the Jira -> Claude pipeline. The pipeline blocks, so it runs in a thread."""

    async def project_exists(self, project_key: str) -> bool:
        return await asyncio.to_thread(pipeline.get_project, project_key) is not None

    async def generate(self, project_key: str, version: str) -> str:
        try:
            return await asyncio.to_thread(pipeline.generate_release_notes, project_key, version)
        except pipeline.NoTicketsError as exc:
            raise GenerationError(
                                f"No Jira tickets in project {project_key} are labelled {version}.",
            ) from exc
        except (requests.RequestException, anthropic.APIError) as exc:
            raise GenerationError(f"A Jira or Anthropic request failed ({type(exc).__name__}).") from exc


def build_generator() -> Generator:
    # config.py has already validated GENERATOR and, for "live", the credentials.
    if settings.generator == "live":
        return LiveGenerator()
    return MockGenerator(delay=settings.mock_delay_seconds)


generator = build_generator()