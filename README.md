# Release Notes API

A REST API that generates release notes from Jira tickets. You submit a job, poll its status, and read the Markdown result.

This is a proof of concept. It wraps the Python pipeline from the [`ai-automated-release-notes-pipeline`](https://github.com/Docu-Mental/ai-automated-release-notes-pipeline) repository (Jira > Claude > Markdown) in a small API with its own documentation.

> **New here? Start with the [Getting started tutorial](docs/getting-started.md).**
> It takes you from zero to your first generated release notes in about 10 minutes. You need no Jira or Anthropic account.

## Documentation

| Document | What it is |
|---|---|
| [Getting started tutorial](docs/getting-started.md) | Start the API, submit a job, poll it, and read the result, with `curl` examples. |
| API reference | Every endpoint, parameter, and error. Download `docs/api-reference.html` and open it in your browser (GitHub shows only its source), or read the raw spec in [`docs/openapi.json`](docs/openapi.json). |
| [Example script](examples/automated-submission-with-polling.py) | Python script that submits a job, polls until it finishes, and prints the result. |

## Endpoints

All endpoints are under `/v1`.

| Method and path | Purpose |
|---|---|
| `POST /release-notes` | Submit a job. Returns `202` and the job ID. |
| `GET /release-notes/{job_id}` | Get a job's status and, when finished, its Markdown result. |
| `GET /release-notes` | List jobs, newest first, with pagination. |
| `DELETE /release-notes/{job_id}` | Delete a finished job. |
| `GET /health` | Check that the service is running. No API key needed. |

## Mock mode and live mode

- **Mock mode (default).** Every job returns the same fixed sample release notes, so anyone can try the API without credentials. Special project keys, such as `SLOW`, trigger specific behavior. See the API reference.
- **Live mode.** Jobs fetch real tickets from Jira and have Claude write the notes. Set `GENERATOR=live` in `.env` and fill in `JIRA_URL`, `JIRA_EMAIL`, `JIRA_TOKEN`, and `ANTHROPIC_API_KEY`. The `version` you send must match the Jira label on the release's tickets exactly. Live jobs use Anthropic credit. The last section of the tutorial walks through this.

## Authentication

Send your API key in the `X-API-Key` header on every request except `GET /v1/health`. The key is the `API_KEY` value in your `.env` file.

- `401 missing_api_key`: the header is missing or empty.
- `403 invalid_api_key`: the header is present but the key is wrong.

Requests are limited to 120 per minute by default (`RATE_LIMIT_PER_MINUTE`). Over the limit, the API returns `429` and a `Retry-After` header.

## Run it

You need Python 3.12 or later.

**Once, after cloning:**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Then open `.env` and set `API_KEY` to any string.

**Each time you open a new terminal:**

```bash
source .venv/bin/activate
uvicorn app.main:app --env-file .env
```

The API runs at `http://localhost:8000`. The interactive docs are at `http://localhost:8000/docs`, and the OpenAPI spec is at `http://localhost:8000/openapi.json`.

## Run the tests

With the virtual environment active:

```bash
pytest
```

## Update the API reference

Run this whenever the API's spec changes, such as new descriptions or fields. The server must be running.

```bash
curl -s http://localhost:8000/openapi.json -o docs/openapi.json && python3 docs/make_reference.py
```

## Project layout

```text
app/
  main.py         App setup and OpenAPI metadata
  config.py       Settings, read from environment variables
  api/            Routes, request and response models, errors, authentication
  services/       Generators (mock and live), the Jira-to-Claude pipeline,
                  sample content, background job runner, job store
docs/             Tutorial, API reference, and the script that builds it
examples/         Example client script
tests/            Automated tests
```

## Design notes

- Generation runs as a background task, so `POST` returns immediately and clients poll for the result.
- Mock and live mode share one interface (`Generator`), so the API contract is identical in both.
- Every error uses one JSON shape with a stable, machine-readable `code`.
- Jobs are stored in memory and are lost when the server restarts.

## Limitations

This project runs locally and is not built for public hosting. It has one shared API key, a single global rate limit, and no persistence.
