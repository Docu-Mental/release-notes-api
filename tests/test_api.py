from dataclasses import replace

from app.api import security
from app.services.store import store

URL = "/v1/release-notes"
BODY = {"project_key": "DEMO", "version": "2.4.0"}


def test_health_needs_no_key(client):
    r = client.get("/v1/health", headers={"X-API-Key": ""})
    assert r.status_code == 200
    assert r.json()["generator"] == "mock"


def test_missing_key_is_401(client):
    r = client.get(URL, headers={"X-API-Key": ""})
    assert r.status_code == 401
    assert r.json()["code"] == "missing_api_key"


def test_wrong_key_is_403(client):
    r = client.get(URL, headers={"X-API-Key": "wrong"})
    assert r.status_code == 403
    assert r.json()["code"] == "invalid_api_key"


def test_submit_then_poll_succeeds(client):
    r = client.post(URL, json=BODY)
    assert r.status_code == 202
    job = r.json()
    assert job["status"] == "queued"
    assert r.headers["Location"] == f"{URL}/{job['id']}"

    # TestClient finishes background tasks before returning, so the job is already done.
    done = client.get(r.headers["Location"]).json()
    assert done["status"] == "succeeded"
    assert done["completed_at"] is not None
    assert done["result"]["content"].startswith("# DEMO Release Notes — 2.4.0")


def test_fail_key_gives_failed_job_with_http_200(client):
    job_id = client.post(URL, json={**BODY, "project_key": "FAIL"}).json()["id"]
    r = client.get(f"{URL}/{job_id}")
    assert r.status_code == 200
    job = r.json()
    assert job["status"] == "failed"
    assert job["error"]["code"] == "generation_failed"
    assert job["result"] is None


def test_notfound_key_is_404(client):
    r = client.post(URL, json={**BODY, "project_key": "NOTFOUND"})
    assert r.status_code == 404
    assert r.json()["code"] == "project_not_found"


def test_bad_version_and_unknown_field_are_422(client):
    r = client.post(URL, json={**BODY, "version": "2.4 0"})
    assert r.status_code == 422
    assert r.json()["code"] == "validation_error"
    assert client.post(URL, json={**BODY, "formats": "markdown"}).status_code == 422


def test_unknown_job_is_404_and_malformed_id_is_422(client):
    assert client.get(f"{URL}/job_000000000000").json()["code"] == "job_not_found"
    assert client.get(f"{URL}/nope").status_code == 422


def test_list_pagination_newest_first(client):
    ids = [client.post(URL, json=BODY).json()["id"] for _ in range(3)]
    page = client.get(URL, params={"limit": 2, "offset": 0}).json()
    assert page["total"] == 3
    assert [j["id"] for j in page["items"]] == [ids[2], ids[1]]
    assert "result" not in page["items"][0]
    assert client.get(URL, params={"limit": 0}).status_code == 422


def test_delete_finished_job(client):
    job_id = client.post(URL, json=BODY).json()["id"]
    assert client.delete(f"{URL}/{job_id}").status_code == 204
    assert client.get(f"{URL}/{job_id}").status_code == 404


def test_delete_unfinished_job_is_409(client):
    job = store.create("DEMO", "2.4.0", "markdown")  # stays "queued"
    r = client.delete(f"{URL}/{job.id}")
    assert r.status_code == 409
    assert r.json()["code"] == "job_not_finished"


def test_rate_limit_is_429(client, monkeypatch):
    monkeypatch.setattr(security, "settings", replace(security.settings, rate_limit_per_minute=2))
    assert client.get(URL).status_code == 200
    assert client.get(URL).status_code == 200
    r = client.get(URL)
    assert r.status_code == 429
    assert r.json()["code"] == "rate_limit_exceeded"
    assert int(r.headers["Retry-After"]) > 0


def test_spec_has_no_default_fastapi_validation_schema(client):
    spec = client.get("/openapi.json").json()
    assert spec["info"]["version"] == "1.0.0"
    assert "HTTPValidationError" not in spec["components"]["schemas"]


def test_version_is_used_exactly_as_given(client):
    job_id = client.post(URL, json={**BODY, "version": "Q1-2.0.0"}).json()["id"]
    content = client.get(f"{URL}/{job_id}").json()["result"]["content"]
    assert content.startswith("# DEMO Release Notes — Q1-2.0.0")