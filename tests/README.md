# Release Notes API

Generates release notes from Jira tickets as asynchronous jobs. Submit a job, poll its status, read the Markdown result.

**Status:** mock mode only. No Jira or Anthropic calls yet. Every job returns the same fixed sample notes.

## Run it

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then set API_KEY
uvicorn app.main:app --env-file .env --reload
```

- Interactive docs: http://localhost:8000/docs
- OpenAPI spec: http://localhost:8000/openapi.json

## Try it

```bash
export KEY=change-me   # the API_KEY from your .env
H="X-API-Key: $KEY"

# Health (no key needed)
curl localhost:8000/v1/health

# Submit a job: 202 plus a Location header
curl -i -X POST localhost:8000/v1/release-notes -H "$H" \
  -H "Content-Type: application/json" \
  -d '{"project_key": "DEMO", "version": "2.4.0"}'

# Save the job ID, then poll until status is succeeded or failed
ID=$(curl -s "localhost:8000/v1/release-notes?limit=1" -H "$H" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['items'][0]['id'])")
curl -H "$H" localhost:8000/v1/release-notes/$ID

# List jobs (newest first)
curl -H "$H" "localhost:8000/v1/release-notes?limit=5&offset=0"

# Delete a finished job: 204, no body
curl -i -X DELETE -H "$H" localhost:8000/v1/release-notes/$ID
```

## Test

```bash
pytest
```

## Export the spec

```bash
curl -s localhost:8000/openapi.json -o openapi.json
```