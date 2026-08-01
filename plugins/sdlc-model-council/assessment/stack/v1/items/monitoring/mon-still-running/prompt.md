# Monitoring: is the service ready yet?

You are polling a service's health endpoint while it starts up. Below is everything observed so far. Decide whether to **stop watching** (the service reached a terminal state — ready, or a hard failure) or **keep watching** (it is still starting and has neither become ready nor failed). If you stop, name the line that told you; otherwise leave the trigger empty.

{{INPUT:stream.txt}}

Report your decision as a single JSON object.

Respond with ONLY a single JSON object of the form `{"decision": "stop"|"continue", "trigger": "<the line that fired, or empty>", "reason": "<one sentence>"}` — no prose outside the object.
