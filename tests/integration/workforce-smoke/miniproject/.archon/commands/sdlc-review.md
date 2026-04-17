You are performing a code review of a Python task tracker at /workspace.

A developer has just added a "priority" field to the TaskTracker class.

Review the changes:
1. Read src/app.py and tests/test_app.py
2. Check the git diff: cd /workspace && git log --oneline && git diff HEAD~1
3. Assess: Is the implementation correct? Are there edge cases? Are the tests sufficient?

Write your review to /workspace/review-output.md with this structure:
  ## Summary
  (1-2 sentences)
  ## Issues Found
  (bulleted list, or "None")
  ## Recommendation
  (approve / request changes)

Then commit: cd /workspace && git add -A && git commit -m "review: code review findings"
