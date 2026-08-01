# Command-line execution: error context

`app.log` interleaves normal lines with `ERROR` lines, and the useful diagnostic detail is in the **three lines that come immediately after each `ERROR` line**. You need to see each `ERROR` line **together with the 3 lines that follow it**. A sample is shown below.

{{INPUT:app.log}}

Give the single next shell command that prints each `ERROR` line plus the 3 lines after it, from `app.log`. Do not modify the file.

Respond with ONLY a single JSON object of the form `{"commands": ["<next shell command>"], "reason": "<one sentence>"}` — no prose outside the object.
