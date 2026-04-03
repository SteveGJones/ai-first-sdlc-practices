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

```bash
python tools/validation/local-validation.py --quick
```

2. **If validation fails**, report the issues and stop. Do NOT commit.

3. **If validation passes**, proceed:
   - Review all changed files with `git status` and `git diff`
   - Stage the relevant files (prefer specific files over `git add -A`)
   - If `$ARGUMENTS` is provided, use it as the commit message
   - If no message provided, draft a concise commit message based on the changes
   - Use conventional commit format: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`

4. **Commit** using a heredoc for proper formatting:

```bash
git commit -m "$(cat <<'EOF'
<type>: <description>

<optional body>

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

5. **Run git status** after commit to verify success.
