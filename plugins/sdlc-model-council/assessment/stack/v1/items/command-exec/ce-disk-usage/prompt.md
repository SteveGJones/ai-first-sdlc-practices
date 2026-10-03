# Command-line execution: find the biggest directory

Disk is filling up under `/var/log`. You need to find **which immediate subdirectory of `/var/log` is consuming the most space**, largest first. A directory listing is shown below for context.

{{INPUT:listing.txt}}

Give the single next shell command (a pipeline is fine) that reports the size of each subdirectory of `/var/log` sorted with the largest first. This is a read-only investigation — do not delete anything.

Respond with ONLY a single JSON object of the form `{"commands": ["<next shell command>"], "reason": "<one sentence>"}` — no prose outside the object.
