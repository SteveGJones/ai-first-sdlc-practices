# Monitoring: did the migration fail?

You are watching a database migration stream. Below is everything printed so far. Decide whether to **stop watching** (a terminal state — success or a hard failure — was reached) or **keep watching**. If you stop, name the exact line that told you.

{{INPUT:stream.txt}}

Report your decision as a single JSON object.

Respond with ONLY a single JSON object of the form `{"decision": "stop"|"continue", "trigger": "<the line that fired, or empty>", "reason": "<one sentence>"}` — no prose outside the object.
