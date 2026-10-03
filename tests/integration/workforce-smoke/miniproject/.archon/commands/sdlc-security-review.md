You are performing a security review of a Python task tracker at /workspace.

Read src/app.py and check for:
- Input validation (are parameters validated?)
- Error handling (are exceptions caught properly?)
- Any potential injection or data integrity issues

This node runs in parallel with other reviewers.  Do NOT commit — the
workspace git index is a single-writer resource and concurrent committers
race on `.git/index.lock`.  Write your findings to your own subdirectory:

    mkdir -p /workspace/reports/qa-security
    # Write review content to /workspace/reports/qa-security/review.md

Content should have ## Summary, ## Issues, ## Recommendation sections.
The downstream synthesise node will read every reports/*/review.md and
produce a single commit covering all reviews.
