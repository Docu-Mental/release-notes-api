"""Runs one job in the background and records how it ended."""
import logging

from app.services.generators import GenerationError, Generator
from app.services.store import JobStore, utc_now

logger = logging.getLogger("release_notes.runner")


async def run_job(job_id: str, store: JobStore, generator: Generator) -> None:
    job = store.get(job_id)
    if job is None:
        return
    job.status = "running"
    try:
        content = await generator.generate(job.project_key, job.version)
        job.result = {"format": job.format, "content": content}
        final_status = "succeeded"
    except GenerationError as exc:
        job.error = {"code": "generation_failed", "message": str(exc), "details": exc.details}
        final_status = "failed"
    except Exception:
        # Catch everything: a job must never be stuck in "running" forever.
        logger.exception("Unexpected error in job %s", job_id)
        job.error = {
            "code": "internal_error",
            "message": "Unexpected error while generating release notes.",
            "details": None,
        }
        final_status = "failed"
    job.completed_at = utc_now()
    job.status = final_status