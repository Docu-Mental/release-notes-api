"""Settings, read from environment variables once at startup."""
import os
from dataclasses import dataclass

API_VERSION = "1.0.0"
GENERATORS = ("mock", "live")
LIVE_VARS = ("JIRA_URL", "JIRA_EMAIL", "JIRA_TOKEN", "ANTHROPIC_API_KEY")


@dataclass(frozen=True)
class Settings:
    api_key: str
    generator: str
    mock_delay_seconds: float
    rate_limit_per_minute: int
    jira_url: str = ""
    jira_email: str = ""
    jira_token: str = ""
    anthropic_api_key: str = ""


def load_settings() -> Settings:
    # Fail at startup, not on the first request, if the config is unusable.
    api_key = os.environ.get("API_KEY", "")
    if not api_key:
        raise RuntimeError("API_KEY is not set. Copy .env.example to .env and set it.")
    generator = os.environ.get("GENERATOR", "mock")
    if generator not in GENERATORS:
        raise RuntimeError(f"GENERATOR={generator!r} is not supported. Use 'mock' or 'live'.")
    if generator == "live":
        missing = [name for name in LIVE_VARS if not os.environ.get(name)]
        if missing:
            raise RuntimeError(f"GENERATOR=live needs these variables: {', '.join(missing)}.")
    return Settings(
        api_key=api_key,
        generator=generator,
        mock_delay_seconds=float(os.environ.get("MOCK_DELAY_SECONDS", "2")),
        rate_limit_per_minute=int(os.environ.get("RATE_LIMIT_PER_MINUTE", "120")),
        jira_url=os.environ.get("JIRA_URL", "").rstrip("/"),
        jira_email=os.environ.get("JIRA_EMAIL", ""),
        jira_token=os.environ.get("JIRA_TOKEN", ""),
        anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
    )


settings = load_settings()