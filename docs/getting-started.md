# Get started

In this tutorial, you start the Release Notes API, submit a job, wait for it to finish, and read the generated Markdown. It takes about 10 minutes.

The API runs in mock mode, so you need no Jira or Anthropic credentials. Every job returns the same sample release notes.

## Before you begin

You need:

- Python 3.12 or later
- Git
- curl
- A terminal on macOS, Linux, or Windows with WSL

## Step 1: Start the API

Open a terminal and run these commands. They download the code, install the dependencies, and create your configuration file.

```bash
git clone <repository-url>
cd release-notes-api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Open `.env` in a text editor and set your API key. You can use any string:

```text
API_KEY=my-secret-key
```

Start the server:

```bash
uvicorn app.main:app --env-file .env
```

The server is ready when you see this line:

```text
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

Leave this terminal running. Open a second terminal for the rest of the tutorial, and set your key there. Use the same value you put in `.env`:

```bash
export API_KEY=my-secret-key
```

## Step 2: Check that the API is running

Send a request to the health endpoint. This endpoint needs no API key.

```bash
curl http://localhost:8000/v1/health
```

The response confirms that the API is running in mock mode:

```json
{
  "status": "ok",
  "version": "1.0.0",
  "generator": "mock"
}
```

!!! note
    The examples in this tutorial show responses formatted for readability. Your terminal shows each response on one line.

## Step 3: Submit a job

Generating real release notes takes time, so the API works in two stages. You submit a job, then you check back for the result.

Submit a job for the project `DEMO`, version `2.4.0`:

```bash
curl -i -X POST http://localhost:8000/v1/release-notes \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"project_key": "DEMO", "version": "2.4.0"}'
```

The response looks like this:

```http
HTTP/1.1 202 Accepted
location: /v1/release-notes/job_3f9a1c7e2b40

{
  "id": "job_3f9a1c7e2b40",
  "status": "queued",
  "project_key": "DEMO",
  "version": "2.4.0",
  "format": "markdown",
  "created_at": "2026-11-06T10:15:00Z",
  "completed_at": null,
  "error": null
}
```

Note three things:

- The status code `202 Accepted` means the API accepted your job, not that the release notes are ready.
- The job has the status `queued`.
- The `location` header gives the path you use to check the job. The `id` field holds the same job ID.

Save the job ID in a variable. Replace the value with the `id` from your own response:

```bash
export JOB_ID=job_3f9a1c7e2b40
```

## Step 4: Check the job status

Request the job by its ID:

```bash
curl -H "X-API-Key: $API_KEY" http://localhost:8000/v1/release-notes/$JOB_ID
```

The mock generator takes about 2 seconds, so the job has usually finished by now:

```json
{
  "id": "job_3f9a1c7e2b40",
  "status": "succeeded",
  "project_key": "DEMO",
  "version": "2.4.0",
  "format": "markdown",
  "created_at": "2026-11-06T10:15:00Z",
  "completed_at": "2026-11-06T10:15:02Z",
  "error": null,
  "result": {
    "format": "markdown",
    "content": "# DEMO Release Notes — v2.4.0\n\nThis release introduces new security and compliance features...\n..."
  }
}
```

## Step 5: Read the release notes

The release notes are in `result.content`. Because this is JSON, line breaks appear as `\n`. To print the Markdown as readable text, extract the field:

```bash
curl -s -H "X-API-Key: $API_KEY" http://localhost:8000/v1/release-notes/$JOB_ID \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['result']['content'])"
```

The output is the finished release notes:

```text
# DEMO Release Notes — v2.4.0

This release introduces new security and compliance features for the admin portal, expands multi-currency reporting capabilities, and addresses several bugs affecting transaction processing and data exports.

---

## New Features

- Administrators can now enable two-factor authentication (TOTP-based) for admin portal logins, adding an extra layer of account security.
- A new audit log export feature allows administrators to download a complete record of user actions in CSV or PDF format for compliance and regulatory reporting.
- Settlement reports can now be generated in the client's local currency, with exchange rates applied as of the original transaction time.

---

## Improvements

- The v1 payment submission endpoint (`/v1/submit`) is now deprecated and will be retired in v4.0.0; API responses include deprecation headers, and documentation has been updated accordingly.
- The API reference documentation for the v2 transaction endpoint has been updated to reflect new pagination parameters.

---

## Bug Fixes

- Fixed an issue where duplicate transaction entries could appear in the ledger after a failed webhook retry.
- Reconciliation reports now display a validation error when the selected date range exceeds 90 days, rather than generating an empty file.
- The webhook retry limit has been increased from 3 to 5 attempts to reduce missed notifications during brief server outages.
```

You have now made a complete round trip: submit, poll, read.

## Step 6: Test a slow job

A real job can take much longer than 2 seconds. In mock mode, the project key `SLOW` simulates a job taking ten times as long, about 20 seconds. Use it to see how your client behaves while a job is still in progress.

Submit a job for `SLOW`:

```bash
curl -X POST http://localhost:8000/v1/release-notes \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"project_key": "SLOW", "version": "1.0.0"}'
```

Set `JOB_ID` to the new job's ID:

```bash
export JOB_ID=<id from the response>
```

Wait a few seconds, then request the job. It is still running:

```bash
curl -H "X-API-Key: $API_KEY" http://localhost:8000/v1/release-notes/$JOB_ID
```

```json
{
  "id": "job_1d1681e815f7",
  "status": "running",
  "project_key": "SLOW",
  "version": "1.0.0",
  "format": "markdown",
  "created_at": "2026-11-06T10:20:00Z",
  "completed_at": null,
  "error": null,
  "result": null
}
```

While the job is in progress, `completed_at` and `result` are `null`. Your code must keep polling until `status` is `succeeded` or `failed`. The Python script at the end of this tutorial shows a polling loop.

Now try to delete the job before it finishes:

```bash
curl -i -X DELETE -H "X-API-Key: $API_KEY" http://localhost:8000/v1/release-notes/$JOB_ID
```

The API refuses, because you can only delete a job that has finished:

```http
HTTP/1.1 409 Conflict

{
  "code": "job_not_finished",
  "message": "Job job_1d1681e815f7 is still running.",
  "details": {
    "status": "running"
  }
}
```

After about 20 seconds in total, request the job again. Its status is now `succeeded`.

## Step 7: List and delete jobs

List your jobs, newest first:

```bash
curl -H "X-API-Key: $API_KEY" "http://localhost:8000/v1/release-notes?limit=5"
```

The response has an `items` array of jobs (without their results) and a `total` count of all jobs.

Delete the job from step 6. It has now finished, so the delete succeeds:

```bash
curl -i -X DELETE -H "X-API-Key: $API_KEY" http://localhost:8000/v1/release-notes/$JOB_ID
```

The API responds with `204 No Content` and an empty body. You can only delete jobs that have finished.

## If something goes wrong

- **`Connection refused`**: the server isn't running. Start it again with the command from step 1.
- **`401` with `missing_api_key`**: your request has no `X-API-Key` header. In the second terminal, check that you ran `export API_KEY=...`.
- **`403` with `invalid_api_key`**: the key you sent doesn't match the `API_KEY` value in `.env`. Check both values, and restart the server if you changed `.env`.
- **`422` with `validation_error`**: the request body is invalid. The `details.fields` array names the field that failed.
- **None of the above explains it:** run the [example script](../examples/automated-submission-with-polling.py), which makes the same calls as this tutorial. If it prints the release notes, the API is working and the problem is in your `curl` command, usually the quoting or a missing header. If it fails, read the last line of the error. `KeyError: 'API_KEY'` means `API_KEY` isn't set in that terminal. `Connection refused` means the server isn't running. `401` or `403` means the same as in the entries above.

## Next steps

- Browse every endpoint, parameter, and error in the [API reference](api-reference.html).
- Automate the submit-and-poll flow with the [example script](../examples/automated-submission-with-polling.py).
- Tailor the release notes to your product. In `app/services/pipeline.py`, set `PRODUCT_GUIDANCE` to a sentence about your product, for example `PRODUCT_GUIDANCE = "These release notes are for a B2B payment processing platform."`. Restart the server and submit a new job. This only affects live mode.