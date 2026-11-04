"""API-key authentication. Rate limiting is added in a later step."""
import secrets

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


def require_api_key(key: str | None = Security(api_key_header)) -> str:
    if not key:
        raise ApiError(401, ErrorCode.MISSING_API_KEY, "Missing X-API-Key header.")
    # compare_digest takes the same time however many characters match,
    # so response timing doesn't leak the key.
    if not secrets.compare_digest(key.encode(), settings.api_key.encode()):
        raise ApiError(403, ErrorCode.INVALID_API_KEY, "Invalid API key.")
    return key