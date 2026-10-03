You are performing an architecture review of a Python task tracker at /workspace.

Read src/app.py and check for:
- Class design (single responsibility, clear API)
- Data structure choices
- Extensibility concerns

This node runs in parallel with other reviewers.  Do NOT commit — the
workspace git index is a single-writer resource and concurrent committers
race on `.git/index.lock`.  Write your findings to your own subdirectory:

    mkdir -p /workspace/reports/qa-architecture
    # Write review content to /workspace/reports/qa-architecture/review.md

Content should have ## Summary, ## Issues, ## Recommendation sections.
The downstream synthesise node will read every reports/*/review.md and
produce a single commit covering all reviews.
