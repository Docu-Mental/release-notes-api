"""Submit a release-notes job, poll until it finishes, and print the result.

Prerequisites:
  - The API is running on http://localhost:8000.
  - The API_KEY environment variable holds your API key.
  - The requests library is installed (pip install requests).

Usage:
  python automated-submission-with-polling.py
"""
import os
import time

import requests

BASE_URL = "http://localhost:8000"
HEADERS = {"X-API-Key": os.environ["API_KEY"]}

# 1. Submit the job.
response = requests.post(
    f"{BASE_URL}/v1/release-notes",
    headers=HEADERS,
    json={"project_key": "DEMO", "version": "2.4.0"},
)
response.raise_for_status()
job = response.json()
print(f"Submitted {job['id']} (status: {job['status']})")

# 2. Poll until the job reaches a final status.
while job["status"] in ("queued", "running"):
    time.sleep(1)
    response = requests.get(f"{BASE_URL}/v1/release-notes/{job['id']}", headers=HEADERS)
    response.raise_for_status()
    job = response.json()
    print(f"Status: {job['status']}")

# 3. Use the result.
if job["status"] == "succeeded":
    print(job["result"]["content"])
else:
    print(f"Job failed: {job['error']['code']}: {job['error']['message']}")
