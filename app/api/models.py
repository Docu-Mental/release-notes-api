"""Request and response schemas. These define the public contract."""
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from app.api.errors import ErrorResponse

SUMMARY_EXAMPLE = {
    "id": "job_3f9a1c7e2b40",
    "status": "queued",
    "project_key": "DEMO",
    "version": "2.4.0",
    "format": "markdown",
    "created_at": "2026-11-03T10:15:00Z",
    "completed_at": None,
    "error": None,
}
JOB_EXAMPLE = {
    **SUMMARY_EXAMPLE,
    "status": "succeeded",
    "completed_at": "2026-11-03T10:15:02Z",
    "result": {
        "format": "markdown",
        "content": "# DEMO 2.4.0 release notes\n\n## New features\n\n- DEMO-101: Bulk export of reports\n",
    },
}


class Health(BaseModel):
    status: str = Field(description="Always `ok` while the service is running.", examples=["ok"])
    version: str = Field(description="API version.", examples=["1.0.0"])
    generator: str = Field(
        description="Active generator. `mock` returns fixed sample content.", examples=["mock"]
    )


class JobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class OutputFormat(StrEnum):
    MARKDOWN = "markdown"


class CreateJobRequest(BaseModel):
    project_key: str = Field(
        pattern=r"^[A-Z][A-Z0-9_]{1,9}$",
        description="Jira project key: 2-10 characters, uppercase letters, digits or underscores, "
        "starting with a letter.",
        examples=["DEMO"],
    )
    version: str = Field(
        pattern=r"^\d+\.\d+\.\d+$",
        description="Release version in `MAJOR.MINOR.PATCH` form.",
        examples=["2.4.0"],
    )
    format: OutputFormat = Field(
        default=OutputFormat.MARKDOWN,
        description="Output format. `markdown` is the only supported value.",
    )
    model_config = ConfigDict(
        extra="forbid",  # reject unknown fields, so a typo like "formats" fails loudly
        json_schema_extra={
            "examples": [{"project_key": "DEMO", "version": "2.4.0", "format": "markdown"}]
        },
    )


class Result(BaseModel):
    format: OutputFormat = Field(description="Format of `content`.")
    content: str = Field(description="The generated release notes.")


class JobSummary(BaseModel):
    """A release-notes job without its result."""

    id: str = Field(description="Job ID. Use it to poll or delete the job.")
    status: JobStatus = Field(
        description="`queued` and `running` mean in progress. `succeeded` and `failed` are final and never change."
    )
    project_key: str = Field(description="Jira project key the job was submitted for.")
    version: str = Field(description="Release version the job was submitted for.")
    format: OutputFormat = Field(description="Requested output format.")
    created_at: datetime = Field(description="When the job was accepted (UTC).")
    completed_at: datetime | None = Field(
        description="When the job became `succeeded` or `failed` (UTC). Null while in progress."
    )
    error: ErrorResponse | None = Field(description="Why the job failed. Null unless `status` is `failed`.")
    model_config = ConfigDict(json_schema_extra={"examples": [SUMMARY_EXAMPLE]})


class Job(JobSummary):
    """A release-notes job, including its result once finished."""

    result: Result | None = Field(description="The generated notes. Null unless `status` is `succeeded`.")
    model_config = ConfigDict(json_schema_extra={"examples": [JOB_EXAMPLE]})


class JobList(BaseModel):
    items: list[JobSummary] = Field(description="Jobs on this page, newest first. Results are not included.")
    total: int = Field(description="Total number of jobs, ignoring `limit` and `offset`.")
    limit: int = Field(description="Page size used.")
    offset: int = Field(description="Number of jobs skipped.")
    model_config = ConfigDict(
        json_schema_extra={"examples": [{"items": [SUMMARY_EXAMPLE], "total": 1, "limit": 20, "offset": 0}]}
    )