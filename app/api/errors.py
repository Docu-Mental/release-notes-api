"""One error schema for every failure, plus the stable machine-readable codes."""
from enum import StrEnum
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from starlette.exceptions import HTTPException as StarletteHTTPException


class ErrorCode(StrEnum):
    MISSING_API_KEY = "missing_api_key"
    INVALID_API_KEY = "invalid_api_key"
    PROJECT_NOT_FOUND = "project_not_found"
    JOB_NOT_FOUND = "job_not_found"
    JOB_NOT_FINISHED = "job_not_finished"
    VALIDATION_ERROR = "validation_error"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    INTERNAL_ERROR = "internal_error"
    ROUTE_NOT_FOUND = "route_not_found"
    METHOD_NOT_ALLOWED = "method_not_allowed"
    GENERATION_FAILED = "generation_failed"  # only ever appears in job.error


class ErrorResponse(BaseModel):
    """The only error shape this API returns."""

    code: ErrorCode = Field(description="Stable machine-readable code. Safe to branch on.")
    message: str = Field(description="Human-readable explanation. Wording may change; do not parse it.")
    details: dict[str, Any] | None = Field(
        default=None,
        description="Extra context. The shape depends on `code`. Null when there is none.",
    )
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "code": "job_not_found",
                    "message": "No job with ID job_3f9a1c7e2b40.",
                    "details": {"job_id": "job_3f9a1c7e2b40"},
                }
            ]
        }
    )


class ApiError(Exception):
    """Raise this anywhere to return a documented error response."""

    def __init__(
        self,
        status_code: int,
        code: ErrorCode,
        message: str,
        details: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ):
        self.status_code = status_code
        self.body = ErrorResponse(code=code, message=message, details=details)
        self.headers = headers


# code -> (HTTP status, description for the spec, example message, example details)
CATALOG: dict[ErrorCode, tuple[int, str, str, dict[str, Any] | None]] = {
    ErrorCode.MISSING_API_KEY: (401, "The `X-API-Key` header is missing or empty.", "Missing X-API-Key header.", None),
    ErrorCode.INVALID_API_KEY: (403, "The `X-API-Key` header is present but the key is not valid.", "Invalid API key.", None),
    ErrorCode.PROJECT_NOT_FOUND: (404, "The project does not exist.", "Project NOTFOUND does not exist.", {"project_key": "NOTFOUND"}),
    ErrorCode.JOB_NOT_FOUND: (404, "No job with this ID exists, or it was deleted.", "No job with ID job_3f9a1c7e2b40.", {"job_id": "job_3f9a1c7e2b40"}),
    ErrorCode.JOB_NOT_FINISHED: (409, "The job is still queued or running, so it cannot be deleted.", "Job job_3f9a1c7e2b40 is still running.", {"status": "running"}),
    ErrorCode.VALIDATION_ERROR: (
        422,
        "The request body, query parameters or path parameters are invalid.",
        "Request validation failed.",
        {"fields": [{"field": "body.project_key", "message": "String should match pattern '^[A-Z][A-Z0-9_]{1,9}$'"}]},
    ),
    ErrorCode.RATE_LIMIT_EXCEEDED: (429, "Too many requests. Wait `Retry-After` seconds.", "Rate limit exceeded.", {"retry_after_seconds": 12}),
    ErrorCode.INTERNAL_ERROR: (500, "An unexpected server error occurred.", "Internal server error.", None),
}


def errors(*codes: ErrorCode) -> dict[int | str, dict[str, Any]]:
    """Build a route's `responses=` argument, with one spec example per error code."""
    responses: dict[int | str, dict[str, Any]] = {}
    for code in codes:
        status, description, message, details = CATALOG[code]
        entry = responses.setdefault(
            status,
            {"model": ErrorResponse, "description": description, "content": {"application/json": {"examples": {}}}},
        )
        if code is ErrorCode.RATE_LIMIT_EXCEEDED:
            entry["headers"] = {
                "Retry-After": {"description": "Seconds to wait before retrying.", "schema": {"type": "integer"}}
            }
        entry["content"]["application/json"]["examples"][code.value] = {
            "summary": code.value,
            "value": {"code": code.value, "message": message, "details": details},
        }
    return responses


def _json(status: int, body: ErrorResponse, headers: dict[str, str] | None = None) -> JSONResponse:
    return JSONResponse(status_code=status, content=body.model_dump(mode="json"), headers=headers)


def register_error_handlers(app: FastAPI) -> None:
    """Route every failure through the one ErrorResponse schema."""

    @app.exception_handler(ApiError)
    async def api_error(request: Request, exc: ApiError) -> JSONResponse:
        return _json(exc.status_code, exc.body, exc.headers)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        fields = [{"field": ".".join(str(p) for p in e["loc"]), "message": e["msg"]} for e in exc.errors()]
        body = ErrorResponse(
            code=ErrorCode.VALIDATION_ERROR, message="Request validation failed.", details={"fields": fields}
        )
        return _json(422, body)

    @app.exception_handler(StarletteHTTPException)
    async def http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        # Framework-level errors: unknown path (404) or wrong method (405).
        code = {404: ErrorCode.ROUTE_NOT_FOUND, 405: ErrorCode.METHOD_NOT_ALLOWED}.get(
            exc.status_code, ErrorCode.INTERNAL_ERROR
        )
        return _json(exc.status_code, ErrorResponse(code=code, message=str(exc.detail)), exc.headers)

    @app.exception_handler(Exception)
    async def unhandled_error(request: Request, exc: Exception) -> JSONResponse:
        return _json(500, ErrorResponse(code=ErrorCode.INTERNAL_ERROR, message="Internal server error."))