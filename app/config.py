"""Settings, read from environment variables once at startup."""
import os
from dataclasses import dataclass

API_VERSION = "1.0.0"


@dataclass(frozen=True)
class Settings:
    api_key: str
    generator: str
    mock_delay_seconds: float
    rate_limit_per_minute: int


def load_settings() -> Settings:
    # Fail at startup, not on the first request, if the config is unusable.
    api_key = os.environ.get("API_KEY", "")
    if not api_key:
        raise RuntimeError("API_KEY is not set. Copy .env.example to .env and set it.")
    generator = os.environ.get("GENERATOR", "mock")
    if generator != "mock":
        raise RuntimeError(f"GENERATOR={generator!r} is not supported yet. Use 'mock'.")
    return Settings(
        api_key=api_key,
        generator=generator,
        mock_delay_seconds=float(os.environ.get("MOCK_DELAY_SECONDS", "2")),
        rate_limit_per_minute=int(os.environ.get("RATE_LIMIT_PER_MINUTE", "120")),
    )


settings = load_settings()