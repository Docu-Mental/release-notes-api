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

app = FastAPI(
    title="Release Notes API",
    version=API_VERSION,
    description="Generates release notes from Jira tickets as asynchronous jobs. "
    "Submit a job, poll for its status, then read the Markdown result.\n\n"
    "All endpoints except `/v1/health` require an `X-API-Key` header.",
    openapi_tags=TAGS,
)
register_error_handlers(app)
app.include_router(health_router)
app.include_router(notes_router)