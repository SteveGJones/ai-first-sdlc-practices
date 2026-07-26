# Monitoring: is the whole deploy finished?

You are watching a **multi-stage** deploy. Below is everything printed so far. The deploy is only finished when **all** stages complete. Decide whether to **stop watching** (the deploy reached a terminal state) or **keep watching** (stages remain). Look carefully — an early stage reporting success is **not** the whole deploy finishing.

{{INPUT:stream.txt}}

Report your decision as a single JSON object.

Respond with ONLY a single JSON object of the form `{"decision": "stop"|"continue", "trigger": "<the line that fired, or empty>", "reason": "<one sentence>"}` — no prose outside the object.
