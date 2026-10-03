# Command-line execution: recent large files

Something recently filled the disk under `/var/log`. You need to find the files under `/var/log` that are **both** larger than **100 MB** **and** were **modified within the last 7 days** — both conditions must hold. Context on the tree is shown below.

{{INPUT:context.txt}}

Give the single next shell command that lists exactly those files (regular files under `/var/log`, size > 100 MB, modified in the last 7 days). Read-only — do not delete anything.

Respond with ONLY a single JSON object of the form `{"commands": ["<next shell command>"], "reason": "<one sentence>"}` — no prose outside the object.
