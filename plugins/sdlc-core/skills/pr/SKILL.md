---
name: pr
description: Create a pull request with full validation. Use when ready to submit work for review.
disable-model-invocation: true
argument-hint: "[base-branch]"
---

# Create Pull Request

Run full validation, then create a PR if clean.

## Steps

1. **Run pre-push validation**

```
/sdlc-core:validate --pre-push
```

2. **If validation fails**, report the issues and stop. Do NOT push or create PR.

3. **Re-verify any test counts cited in the PR body.**

   `--pre-push` runs the pytest suite only. If the draft PR body cites results
   from integration smokes, E2E suites, soak tests, container tests, or any
   other harness *outside* `local-validation.py`, re-run those exact suites
   in this session and update the counts in the body to match the fresh run.

   Example: a PR body saying "266 unit tests, 20/20 container smoke, 8/8
   sequential E2E, 18/18 fresh-user-flow" requires `pytest tests/ -q`,
   `bash tests/integration/workforce-smoke/run-containers.sh`,
   `bash tests/integration/workforce-smoke/run-e2e.sh`, and
   `bash tests/integration/workforce-smoke/run-fresh-user-flow.sh` to all
   run *this session* before the PR is opened.

   Session memory of test counts goes stale fast — fixtures grow, assertions
   drift, environments change. Only numbers you have just observed this
   session belong in the body. If a suite cannot run in this environment
   (missing binary, no Docker, etc.), *delete the number from the body* and
   say so explicitly rather than leaving a stale figure that cites another
   machine's result.

   If the PR already exists and counts have drifted post-creation, update
   the body in place rather than closing and recreating:
   ```bash
   gh pr edit <number> --body-file <updated-body.md>
   ```

4. **Verify required artifacts exist:**
   - Feature proposal in `docs/feature-proposals/`
   - Retrospective in `retrospectives/`
   - If either is missing, warn the user and ask whether to proceed.

5. **If validation passes**, proceed:
   - Check if the branch tracks a remote: `git branch -vv`
   - Push to remote with tracking: `git push -u origin <branch>`
   - Base branch defaults to `main` unless `$ARGUMENTS` specifies otherwise

6. **Create the PR** using `gh pr create`:

```bash
gh pr create --title "<short title under 70 chars>" --body "$(cat <<'EOF'
## Summary
<1-3 bullet points summarizing the changes>

## Changes
<List of files modified/created>

## Test plan
- [ ] `/sdlc-core:validate --pre-push` passes
- [ ] CI pipeline passes
<additional test steps as needed>

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

7. **Report** the PR URL to the user.
