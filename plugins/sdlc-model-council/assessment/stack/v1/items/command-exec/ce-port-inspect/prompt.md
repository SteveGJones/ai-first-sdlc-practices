# Command-line execution: find who holds a port

Starting the server fails because **TCP port 8080 is already in use**. You need to find out **which process is listening on port 8080** so you can decide what to do. The failed start-up output is shown below.

{{INPUT:startup.txt}}

Give the single next shell command that identifies the process listening on port 8080. Only inspect — do not kill anything yet.

Respond with ONLY a single JSON object of the form `{"commands": ["<next shell command>"], "reason": "<one sentence>"}` — no prose outside the object.
