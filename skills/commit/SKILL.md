---
name: commit
description: Validated commit — runs quick checks before committing. Use when ready to commit changes.
disable-model-invocation: true
argument-hint: "[commit message]"
---

# Validated Commit

Run quick validation, then commit if clean.

## Steps

1. **Run quick validation**

```
/sdlc-core:validate --quick
```

2. **Run tests and smoke test** (if application code was changed)

```bash
# Run test suite if configured
pytest --tb=short -q 2>/dev/null || echo "No pytest configured"

# Smoke test: verify the app's main module imports cleanly
python -c "import app" 2>/dev/null || python -c "import main" 2>/dev/null || echo "No app module found"
```

If tests fail or the app cannot import, stop. Fix the issue before committing. Static analysis passing does not mean the code works.

3. **If validation or tests fail**, report the issues and stop. Do NOT commit.

4. **If all checks pass**, proceed:
   - Review all changed files with `git status` and `git diff`
   - Stage the relevant files (prefer specific files over `git add -A`)
   - If `$ARGUMENTS` is provided, use it as the commit message
   - If no message provided, draft a concise commit message based on the changes
   - Use conventional commit format: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`

5. **Commit** using a heredoc for proper formatting:

```bash
git commit -m "$(cat <<'EOF'
<type>: <description>

<optional body>

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

6. **Run git status** after commit to verify success.
