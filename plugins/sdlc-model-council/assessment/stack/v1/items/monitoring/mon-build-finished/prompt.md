# Monitoring: has the build finished?

You are watching the streaming output of a build. Below is everything printed so far. Decide whether to **stop watching** (the build reached a terminal success state) or **keep watching** (it is still running). If you stop, name the exact line that told you it finished.

{{INPUT:stream.txt}}

Report your decision as a single JSON object.

Respond with ONLY a single JSON object of the form `{"decision": "stop"|"continue", "trigger": "<the line that fired, or empty>", "reason": "<one sentence>"}` — no prose outside the object.
