"""In-memory job storage. Everything is lost when the server restarts."""
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


def utc_now() -> datetime:
    return datetime.now(UTC).replace(microsecond=0)


@dataclass
class JobRecord:
    """What we store. Plain strings and dicts, so this layer never imports the API layer."""

    id: str
    project_key: str
    version: str
    format: str
    status: str = "queued"
    created_at: datetime = field(default_factory=utc_now)
    completed_at: datetime | None = None
    result: dict[str, Any] | None = None
    error: dict[str, Any] | None = None


class JobStore:
    def __init__(self) -> None:
        self._jobs: dict[str, JobRecord] = {}

    def create(self, project_key: str, version: str, output_format: str) -> JobRecord:
        job = JobRecord(
            id=f"job_{uuid.uuid4().hex[:12]}",
            project_key=project_key,
            version=version,
            format=output_format,
        )
        self._jobs[job.id] = job
        return job

    def get(self, job_id: str) -> JobRecord | None:
        return self._jobs.get(job_id)

    def delete(self, job_id: str) -> None:
        self._jobs.pop(job_id, None)

    def list_jobs(self, limit: int, offset: int) -> tuple[list[JobRecord], int]:
        """Newest first. Returns one page plus the total count."""
        jobs = list(self._jobs.values())[::-1]
        return jobs[offset : offset + limit], len(jobs)


store = JobStore()