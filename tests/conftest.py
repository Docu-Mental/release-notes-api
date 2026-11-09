import os

# Must be set before importing the app: config.py reads the environment at import time.
os.environ["API_KEY"] = "test-key"
os.environ["GENERATOR"] = "mock"
os.environ["MOCK_DELAY_SECONDS"] = "0"
os.environ["RATE_LIMIT_PER_MINUTE"] = "1000"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.api import security  # noqa: E402
from app.main import app  # noqa: E402
from app.services.store import store  # noqa: E402


@pytest.fixture
def client():
    store._jobs.clear()
    security._hits.clear()
    return TestClient(app, headers={"X-API-Key": "test-key"})