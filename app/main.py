"""Application entry point: API metadata and wiring."""
from fastapi import FastAPI

from app.api.errors import register_error_handlers
from app.api.routes import health_router, notes_router
from app.config import API_VERSION

TAGS = [
    {
        "name": "Release Notes",
        "description": "Create, poll, list and delete release-notes generation jobs.",
    },
    {"name": "Health", "description": "Service status. No authentication required."},
]

DESCRIPTION = """
Generates release notes from Jira tickets as asynchronous jobs. Submit a job, poll its status, then read the Markdown result.
Mock mode returns fictitious sample release notes without Jira or Anthropic calls.

### Authentication
Send your API key in the `X-API-Key` header on every request except `GET /v1/health`.

### Job lifecycle
1. `POST /v1/release-notes` returns `202` immediately. The job is `queued`, and the `Location` header holds its URL.
2. Poll `GET /v1/release-notes/{job_id}` until `status` is `succeeded` or `failed`.
3. Read `result.content` (Markdown) from a succeeded job, or `error` from a failed one.

Jobs are held in memory and are lost when the server restarts.
"""
app = FastAPI(
    title="Release Notes API",
    version=API_VERSION,
    description=DESCRIPTION,
    openapi_tags=TAGS,
)
register_error_handlers(app)
app.include_router(health_router)
app.include_router(notes_router)