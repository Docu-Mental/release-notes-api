"""API-key authentication and a simple rate-limit stub."""
import secrets
import time
from collections import deque

from fastapi import Security
from fastapi.security import APIKeyHeader

from app.api.errors import ApiError, ErrorCode
from app.config import settings

api_key_header = APIKeyHeader(
    name="X-API-Key",
    scheme_name="ApiKeyAuth",
    auto_error=False,  # we raise our own 401, in our own error schema
    description="API key, sent in the `X-API-Key` request header.",
)

WINDOW_SECONDS = 60
_hits: deque[float] = deque()  # timestamps of requests inside the window. One key, so one bucket.


def _check_rate_limit() -> None:
    now = time.monotonic()
    while _hits and now - _hits[0] >= WINDOW_SECONDS:
        _hits.popleft()
    if len(_hits) >= settings.rate_limit_per_minute:
        retry_after = int(WINDOW_SECONDS - (now - _hits[0])) + 1
        raise ApiError(
            429,
            ErrorCode.RATE_LIMIT_EXCEEDED,
            "Rate limit exceeded.",
            {"retry_after_seconds": retry_after},
            headers={"Retry-After": str(retry_after)},
        )
    _hits.append(now)


def require_api_key(key: str | None = Security(api_key_header)) -> str:
    if not key:
        raise ApiError(401, ErrorCode.MISSING_API_KEY, "Missing X-API-Key header.")
    # compare_digest takes the same time however many characters match,
    # so response timing doesn't leak the key.
    if not secrets.compare_digest(key.encode(), settings.api_key.encode()):
        raise ApiError(403, ErrorCode.INVALID_API_KEY, "Invalid API key.")
    _check_rate_limit()  # only authenticated requests count
    return key