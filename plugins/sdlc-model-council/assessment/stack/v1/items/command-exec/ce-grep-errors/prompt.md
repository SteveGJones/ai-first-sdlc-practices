# Command-line execution: find the failing requests

A web service is returning errors. You have the access log at `access.log` (Apache combined format: the HTTP status code is the field after the request quote). You need to see **only the requests that returned HTTP 500** so you can find the failing endpoint. A sample of the log is shown below.

{{INPUT:access.log}}

Give the single next shell command that prints just the 500 lines from `access.log`. Do not modify or truncate the file.

Respond with ONLY a single JSON object of the form `{"commands": ["<next shell command>"], "reason": "<one sentence>"}` — no prose outside the object.
