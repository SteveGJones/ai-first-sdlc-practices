Synthesise the parallel reviewer reports.

Read every file matching /workspace/reports/*/review.md (each reviewer
writes to its own subdirectory to avoid racing on the git index).

Write a unified summary to /workspace/synthesis.md with:
## Combined Summary
## Critical Issues (from all reviewers)
## Recommendation

This is the single commit point for the parallel review block — include
the reviewer reports and your synthesis together:

  cd /workspace && git add -A && git commit -m "reviews + synthesis"
