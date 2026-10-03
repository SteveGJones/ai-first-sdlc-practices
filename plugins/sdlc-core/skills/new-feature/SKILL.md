---
name: new-feature
description: Create a new feature with proposal, retrospective, and branch. Use when starting new development work.
disable-model-invocation: false
argument-hint: "<number> <name> [title]"
---

# New Feature Setup

Create a new feature with all required artifacts. Arguments:

- `$0` — Feature number (e.g., `70`)
- `$1` — Feature name for branch (e.g., `plugin-migration`)
- `$2+` — Optional title (defaults to name with spaces)

## Steps

1. **Create the feature proposal** at `docs/feature-proposals/$0-$1.md`
   - Use the template from [templates/proposal.md](templates/proposal.md)
   - Replace placeholders:
     - `FEATURE_NUMBER` → `$0`
     - `FEATURE_NAME` → `$1`
     - `FEATURE_TITLE` → `$2` (or derive from `$1` by replacing hyphens with spaces)
     - `CREATED_DATE` → today's date (YYYY-MM-DD)

2. **Create the retrospective** at `retrospectives/$0-$1.md`
   - Use the template from [templates/retrospective.md](templates/retrospective.md)
   - Replace the same placeholders

3. **Create the feature branch**

```bash
git checkout main
git pull
git checkout -b feature/$1
```

4. **Run syntax validation**

```
/sdlc-core:validate --syntax
```

If the validate skill is not available (e.g., first-time setup), run the inline fallback:

```bash
python -c "
import ast, pathlib
for f in pathlib.Path('.').rglob('*.py'):
    if '.venv' in str(f): continue
    ast.parse(f.read_text())
print('Syntax OK')
"
```

5. **Check for CI/CD** (first feature only)

If `.github/workflows/` does not exist or contains no workflow files:

```
No CI/CD workflow found. Run /sdlc-core:setup-ci to add GitHub Actions validation.
```

6. **Report** the created files and branch name to the user.
