"""The seam: routes talk to a Generator and never know which one they have."""
import asyncio
from typing import Any, Protocol

from app.config import settings
from app.services.fixtures import render_notes

# Special project keys that trigger specific mock behavior.
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
    """Any class with these two methods qualifies. A live Jira + Anthropic generator
    will implement the same two methods, so the API contract does not change."""

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


def build_generator() -> Generator:
    # config.py has already rejected anything but "mock". A "live" branch goes here later.
    return MockGenerator(delay=settings.mock_delay_seconds)


generator = build_generator()