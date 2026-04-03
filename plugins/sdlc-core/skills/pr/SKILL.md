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

```bash
python tools/validation/local-validation.py --pre-push
```

2. **If validation fails**, report the issues and stop. Do NOT push or create PR.

3. **Verify required artifacts exist:**
   - Feature proposal in `docs/feature-proposals/`
   - Retrospective in `retrospectives/`
   - If either is missing, warn the user and ask whether to proceed.

4. **If validation passes**, proceed:
   - Check if the branch tracks a remote: `git branch -vv`
   - Push to remote with tracking: `git push -u origin <branch>`
   - Base branch defaults to `main` unless `$ARGUMENTS` specifies otherwise

5. **Create the PR** using `gh pr create`:

```bash
gh pr create --title "<short title under 70 chars>" --body "$(cat <<'EOF'
## Summary
<1-3 bullet points summarizing the changes>

## Changes
<List of files modified/created>

## Test plan
- [ ] `python tools/validation/local-validation.py --pre-push` passes
- [ ] CI pipeline passes
<additional test steps as needed>

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

6. **Report** the PR URL to the user.
