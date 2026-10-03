# Monitoring: fatal error or transient retry?

You are watching a registry sync. Below is everything printed so far. Decide whether to **stop watching** (a terminal state — success or a hard, unrecoverable failure — was reached) or **keep watching**. Look carefully: an `ERROR` line that is **being retried** and is followed by fresh progress is **not** a terminal failure.

{{INPUT:stream.txt}}

Report your decision as a single JSON object.

Respond with ONLY a single JSON object of the form `{"decision": "stop"|"continue", "trigger": "<the line that fired, or empty>", "reason": "<one sentence>"}` — no prose outside the object.
