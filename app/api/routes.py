"""Endpoints: the public contract. Business logic lives in app/services."""
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Path, Query, Response

from app.api.errors import ApiError, errors
from app.api.errors import ErrorCode as E
from app.api.models import CreateJobRequest, Health, Job, JobList, JobSummary
from app.api.security import require_api_key
from app.config import API_VERSION, settings
from app.services.generators import generator
from app.services.runner import run_job
from app.services.store import store

# Two routers: health is public, everything under /release-notes requires the key.
health_router = APIRouter(prefix="/v1", tags=["Health"])
notes_router = APIRouter(
    prefix="/v1/release-notes", tags=["Release Notes"], dependencies=[Depends(require_api_key)]
)

JobId = Annotated[
    str,
    Path(description="ID returned when the job was submitted.", examples=["job_3f9a1c7e2b40"]),
]


@health_router.get(
    "/health",
    operation_id="getHealth",
    summary="Check service health",
    description="Returns `200` while the service is running. Requires no authentication.",
    response_model=Health,
)
def get_health() -> Health:
    return Health(status="ok", version=API_VERSION, generator=settings.generator)


@notes_router.post(
    "",
    operation_id="createReleaseNotesJob",
    status_code=202,
    summary="Submit a release-notes job",
    description="Starts generating release notes in the background and returns immediately. "
    "The response body is the new job in status `queued`. Poll the URL in the `Location` header "
    "(or call `getReleaseNotesJob` with the returned `id`) until `status` is `succeeded` or `failed`.",
    response_model=JobSummary,
    responses={
        202: {
            "description": "Job accepted. Poll the URL in the `Location` header.",
            "headers": {
                "Location": {
                    "description": "URL of the new job.",
                    "schema": {"type": "string", "examples": ["/v1/release-notes/job_3f9a1c7e2b40"]},
                }
            },
        },
        **errors(E.MISSING_API_KEY, E.INVALID_API_KEY, E.PROJECT_NOT_FOUND, E.VALIDATION_ERROR),
    },
)
async def create_job(
    body: CreateJobRequest, background: BackgroundTasks, response: Response
) -> JobSummary:
    if not await generator.project_exists(body.project_key):
        raise ApiError(
            404,
            E.PROJECT_NOT_FOUND,
            f"Project {body.project_key} does not exist.",
            {"project_key": body.project_key},
        )
    job = store.create(body.project_key, body.version, body.format.value)
    background.add_task(run_job, job.id, store, generator)  # runs after the response is sent
    response.headers["Location"] = f"/v1/release-notes/{job.id}"
    return JobSummary.model_validate(job, from_attributes=True)


@notes_router.get(
    "",
    operation_id="listReleaseNotesJobs",
    summary="List release-notes jobs",
    description="Returns jobs newest first, with `total` for pagination. "
    "Results are omitted here; fetch a single job to get its Markdown.",
    response_model=JobList,
    responses=errors(E.MISSING_API_KEY, E.INVALID_API_KEY, E.VALIDATION_ERROR),
)
async def list_jobs(
    limit: Annotated[int, Query(ge=1, le=100, description="Maximum number of jobs to return.")] = 20,
    offset: Annotated[int, Query(ge=0, description="Number of jobs to skip.")] = 0,
) -> JobList:
    jobs, total = store.list_jobs(limit, offset)
    items = [JobSummary.model_validate(job, from_attributes=True) for job in jobs]
    return JobList(items=items, total=total, limit=limit, offset=offset)


@notes_router.get(
    "/{job_id}",
    operation_id="getReleaseNotesJob",
    summary="Get a release-notes job",
    description="Returns the job's current status. When `status` is `succeeded`, `result` holds the "
    "Markdown. A `failed` job still returns `200`: the failure is described in `error`, "
    "not in the HTTP status.",
    response_model=Job,
    responses=errors(E.MISSING_API_KEY, E.INVALID_API_KEY, E.JOB_NOT_FOUND),
)
async def get_job(job_id: JobId) -> Job:
    job = store.get(job_id)
    if job is None:
        raise ApiError(404, E.JOB_NOT_FOUND, f"No job with ID {job_id}.", {"job_id": job_id})
    return Job.model_validate(job, from_attributes=True)