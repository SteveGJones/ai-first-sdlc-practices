# Validation Infrastructure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the SDLC validation pipeline work on fresh plugin installs by replacing wrapper script dependencies with inline tool invocations, adding a CI/CD template skill, and automating constitution sync.

**Architecture:** The validate skill becomes a self-contained markdown instruction set that calls standard tools (ruff, mypy, pytest, bandit) directly, with preflight checks for each tool. A new setup-ci skill generates GitHub Actions workflows that mirror the same checks. The release-plugin pipeline copies CONSTITUTION.md into the plugin automatically.

**Tech Stack:** Markdown skills (SKILL.md files), YAML (GitHub Actions workflow template), YAML (release-mapping.yaml)

---

### Task 1: Constitution Sync — Release Mapping (#79)

**Files:**
- Modify: `release-mapping.yaml:19` — add constitution source mapping
- Modify: `.github/workflows/validation.yml` — add drift check step

- [ ] **Step 1: Add constitution to release mapping**

In `release-mapping.yaml`, the `sdlc-core.skills` section already has `constitution.md` referenced:

```yaml
    - source: skills/rules/constitution.md
```

This maps the *plugin's own copy* as the source, not the root `CONSTITUTION.md`. Change it to map from the authoritative source. Replace line 19:

```yaml
    - source: skills/rules/constitution.md
```

with:

```yaml
    - source: CONSTITUTION.md
      dest: skills/rules/constitution.md
```

This tells release-plugin to copy the root `CONSTITUTION.md` into the plugin's `skills/rules/constitution.md` on every release.

- [ ] **Step 2: Add drift check to CI**

In `.github/workflows/validation.yml`, add a new step to the `sdlc-validation` job, after the "Technical Debt Check" step (line 64). Insert after that step:

```yaml
    - name: Constitution Sync Check
      run: |
        if ! diff -q CONSTITUTION.md plugins/sdlc-core/skills/rules/constitution.md > /dev/null 2>&1; then
          echo "::error::CONSTITUTION.md and plugins/sdlc-core/skills/rules/constitution.md have drifted apart."
          echo "Run /sdlc-core:release-plugin to sync, or manually copy CONSTITUTION.md to the plugin."
          diff CONSTITUTION.md plugins/sdlc-core/skills/rules/constitution.md || true
          exit 1
        fi
        echo "Constitution sync: OK"
```

- [ ] **Step 3: Sync the files now**

Copy the current root constitution into the plugin to eliminate the existing drift:

```bash
cp CONSTITUTION.md plugins/sdlc-core/skills/rules/constitution.md
```

- [ ] **Step 4: Verify**

```bash
diff CONSTITUTION.md plugins/sdlc-core/skills/rules/constitution.md
```

Expected: no output (files are identical).

- [ ] **Step 5: Commit**

```bash
git add release-mapping.yaml .github/workflows/validation.yml plugins/sdlc-core/skills/rules/constitution.md
git commit -m "fix: automate constitution sync between source and plugin (#79)

- release-mapping.yaml copies CONSTITUTION.md → plugin on release
- CI drift check fails if source and plugin diverge
- Synced current content"
```

---

### Task 2: Validate Skill Rewrite (#76 + #77)

**Files:**
- Rewrite: `plugins/sdlc-core/skills/validate/SKILL.md`

- [ ] **Step 1: Write the new validate skill**

Replace the entire contents of `plugins/sdlc-core/skills/validate/SKILL.md` with:

```markdown
---
name: validate
description: Run the SDLC validation pipeline using direct tool invocations. No wrapper scripts required. Use when checking code quality before commits or PRs.
disable-model-invocation: true
argument-hint: "[--syntax | --quick | --pre-push]"
---

# SDLC Validation

Run the validation pipeline at the specified level. Each check calls standard tools directly — no wrapper scripts needed.

## Arguments

- `--syntax` — Syntax only (fast, after every edit)
- `--quick` — Syntax + lint + tests (before commits)
- `--pre-push` — Full pipeline (before PRs). This is the default.

## Preflight

Before running any check, verify the tool is available. Report missing tools clearly:

```
[SKIP] <tool> — not installed (run: <install command>)
```

Missing tools at `--syntax` level: warn but continue.
Missing tools at `--quick` or `--pre-push` level: report all missing tools, then stop.

### Preflight checks

| Tool | Check command | Install command |
|------|--------------|-----------------|
| ruff | `which ruff` | `pip install ruff` |
| pytest | `which pytest` | `pip install pytest` |
| mypy | `which mypy` | `pip install mypy` |
| bandit | `which bandit` | `pip install bandit` |

Also check:
- Virtual environment active: `which python` should contain `.venv`. If not, warn: "No virtual environment active. Run: source .venv/bin/activate"
- Test directory exists: `ls tests/` should find test files. If `tests/` missing or empty, report: "No tests found. Tests are mandatory (Constitution Article 10.2)."

## --syntax (after every edit)

Run these checks:

1. **Python AST check** — verify all .py files parse:
```bash
python -c "
import ast, sys, pathlib
errors = []
for f in pathlib.Path('.').rglob('*.py'):
    if '.venv' in str(f):
        continue
    try:
        ast.parse(f.read_text())
    except SyntaxError as e:
        errors.append(f'{f}:{e.lineno}: {e.msg}')
if errors:
    print('Syntax errors found:')
    for e in errors:
        print(f'  {e}')
    sys.exit(1)
print(f'Syntax OK — {len(list(pathlib.Path(\".\").rglob(\"*.py\")))} files checked')
"
```

2. **Ruff syntax errors only** (if ruff installed):
```bash
ruff check . --select E9,F63,F7,F82
```

Report results:
```
[PASS] Syntax check — N files checked, 0 errors
[PASS] Ruff (syntax) — 0 issues
```

## --quick (before commits)

Run all --syntax checks, then:

3. **Ruff full lint**:
```bash
ruff check .
```

4. **Ruff format check**:
```bash
ruff format --check .
```

5. **Technical debt scan**:
```bash
grep -rn "TODO\|FIXME\|HACK\|XXX" --include="*.py" --exclude-dir=.venv . || true
```
If any matches found, report as failure (Production+) or warning (Prototype).

6. **Test execution**:
```bash
pytest --tb=short -q
```
If pytest is not installed or no tests exist, this is a failure (not a skip).

7. **Import smoke test** — verify the main module imports:
```bash
python -c "import app" 2>/dev/null || python -c "import main" 2>/dev/null || echo "No app/main module found (skipping import check)"
```

Report results:
```
[PASS] Ruff — 0 issues
[PASS] Format — all files formatted
[PASS] Technical debt — 0 markers
[PASS] Pytest — N passed, 0 failed
[PASS] Import check — app module imports cleanly
```

## --pre-push (before PRs)

Run all --quick checks, then:

8. **Type checking**:
```bash
mypy . --ignore-missing-imports
```
Or if mypy.ini or pyproject.toml configures mypy, just:
```bash
mypy .
```

9. **Security scan**:
```bash
bandit -r . --exclude ./.venv -q
```

10. **Smoke test** — start the app and verify it responds:
```bash
# Start the app in background
python app.py &
APP_PID=$!
sleep 3

# Check it's running
if kill -0 $APP_PID 2>/dev/null; then
    echo "[PASS] App started (PID $APP_PID)"
    # Try to hit an endpoint (adjust port to project)
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:18080/ 2>/dev/null || echo "000")
    if [ "$HTTP_CODE" -ge 200 ] && [ "$HTTP_CODE" -lt 400 ]; then
        echo "[PASS] Smoke test — HTTP $HTTP_CODE"
    else
        echo "[WARN] App started but endpoint returned HTTP $HTTP_CODE"
    fi
    kill $APP_PID 2>/dev/null
else
    echo "[FAIL] App failed to start"
fi
```

If no `app.py` or `main.py` exists, skip the smoke test with:
```
[SKIP] Smoke test — no app entry point found (not a web application)
```

## Summary Output

After all checks, print a summary:

```
=== SDLC Validation Summary (--pre-push) ===

[PASS] Syntax check — 12 files, 0 errors
[PASS] Ruff (syntax) — 0 issues
[PASS] Ruff (full) — 0 issues
[PASS] Format — all files formatted
[PASS] Technical debt — 0 markers
[PASS] Pytest — 30 passed, 0 failed
[PASS] Import check — clean
[PASS] Mypy — 0 errors
[PASS] Bandit — 0 issues
[PASS] Smoke test — HTTP 200

Result: 10 PASS, 0 FAIL, 0 SKIP
```

If any check is FAIL:
1. Show the specific failures above the summary
2. Do NOT proceed with commits or PRs
3. Suggest fixes for each failure

## Language Detection

Detect project language by scanning the project root:
- `*.py` files present → use Python checks (ruff, mypy, pytest, bandit)
- `*.ts` or `*.js` files present → use JS checks (eslint, tsc, jest or vitest)
- `*.go` files present → use Go checks (go vet, staticcheck, go test)
- Multiple languages → run checks for each detected language

Python is the primary implementation. Other languages follow the same structure with equivalent tools.
```

- [ ] **Step 2: Verify the skill is valid markdown**

Read back the file and confirm:
- Frontmatter has name, description, disable-model-invocation, argument-hint
- All three tiers (--syntax, --quick, --pre-push) are documented
- Every check has a preflight reference
- Error output format is consistent
- No references to `local-validation.py` or any wrapper script remain

- [ ] **Step 3: Update the new-feature skill to remove wrapper script reference**

In `plugins/sdlc-core/skills/new-feature/SKILL.md`, step 4 currently says:

```bash
python tools/validation/local-validation.py --syntax
```

Replace with:

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

- [ ] **Step 4: Commit**

```bash
git add plugins/sdlc-core/skills/validate/SKILL.md plugins/sdlc-core/skills/new-feature/SKILL.md
git commit -m "feat: rewrite validate skill with inline tool invocations (#76, #77)

Replaces wrapper script dependencies (local-validation.py, validate-pipeline.py)
with direct tool calls (ruff, mypy, pytest, bandit). Each check has a preflight
gate that reports missing tools clearly instead of crashing.

- 3 tiers: --syntax (fast), --quick (commits), --pre-push (PRs)
- Preflight checks with install instructions for missing tools
- Language detection for Python/JS/Go
- Consistent [PASS]/[FAIL]/[SKIP] output format
- new-feature skill updated to use /sdlc-core:validate --syntax"
```

---

### Task 3: Setup-CI Skill (#78)

**Files:**
- Create: `plugins/sdlc-core/skills/setup-ci/SKILL.md`
- Create: `plugins/sdlc-core/skills/setup-ci/templates/python.yml`
- Modify: `plugins/sdlc-core/skills/new-feature/SKILL.md` — add CI prompt
- Modify: `plugins/sdlc-core/.claude-plugin/plugin.json` — register skill
- Modify: `release-mapping.yaml` — add skill to sdlc-core mapping

- [ ] **Step 1: Create the setup-ci skill**

Create `plugins/sdlc-core/skills/setup-ci/SKILL.md`:

```markdown
---
name: setup-ci
description: Generate a GitHub Actions workflow for SDLC validation. Use when setting up CI/CD for a new project.
disable-model-invocation: true
argument-hint: "[python | javascript | go]"
---

# Setup CI/CD

Generate a GitHub Actions workflow that mirrors the SDLC validation pipeline.

## Arguments

- `python` — Python project (ruff, mypy, pytest, bandit). Default if .py files detected.
- `javascript` — JS/TS project (eslint, tsc, jest/vitest).
- `go` — Go project (go vet, staticcheck, go test).

If no argument provided, detect language from project files.

## Steps

1. **Detect language** if not specified:
   - `*.py` files → python
   - `*.ts` or `*.js` files → javascript
   - `*.go` files → go

2. **Check for existing workflow**:
   - If `.github/workflows/sdlc-validate.yml` exists, warn and ask before overwriting.

3. **Create workflow directory**:
```bash
mkdir -p .github/workflows
```

4. **Generate workflow** from the appropriate template:
   - Python: use [templates/python.yml](templates/python.yml)
   - Copy the template to `.github/workflows/sdlc-validate.yml`

5. **Report** the created file and suggest next steps:
   ```
   Created .github/workflows/sdlc-validate.yml

   This workflow runs on push and PR to main:
   - Lint (ruff)
   - Format check (ruff format)
   - Type check (mypy)
   - Tests (pytest)
   - Security (bandit)

   Commit and push to activate CI.
   ```
```

- [ ] **Step 2: Create the Python workflow template**

Create `plugins/sdlc-core/skills/setup-ci/templates/python.yml`:

```yaml
name: SDLC Validation
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

permissions:
  contents: read

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Setup virtual environment
        run: |
          python -m venv .venv
          source .venv/bin/activate
          pip install --upgrade pip

      - name: Install dependencies
        run: |
          source .venv/bin/activate
          pip install -r requirements.txt
          if [ -f requirements-dev.txt ]; then pip install -r requirements-dev.txt; fi

      - name: Lint
        run: |
          source .venv/bin/activate
          ruff check .
          ruff format --check .

      - name: Type check
        run: |
          source .venv/bin/activate
          mypy . --ignore-missing-imports

      - name: Test
        run: |
          source .venv/bin/activate
          pytest -v --tb=short

      - name: Security scan
        run: |
          source .venv/bin/activate
          bandit -r . --exclude ./.venv -q
```

- [ ] **Step 3: Add CI prompt to new-feature skill**

In `plugins/sdlc-core/skills/new-feature/SKILL.md`, add a new step between the current step 4 (syntax validation) and step 5 (report). Insert as the new step 5:

```markdown
5. **Check for CI/CD** (first feature only)

If `.github/workflows/` does not exist or contains no workflow files:

```
No CI/CD workflow found. Run /sdlc-core:setup-ci to add GitHub Actions validation.
```
```

Renumber the current step 5 (Report) to step 6.

- [ ] **Step 4: Register the skill in plugin.json**

The `plugins/sdlc-core/.claude-plugin/plugin.json` doesn't list individual skills — they're discovered from the `skills/` directory structure. Verify this by checking that the plugin loads the `setup-ci` skill from the directory:

```bash
ls plugins/sdlc-core/skills/setup-ci/SKILL.md
```

Expected: file exists.

- [ ] **Step 5: Add to release mapping**

In `release-mapping.yaml`, add to the `sdlc-core.skills` section:

```yaml
    - source: skills/setup-ci/SKILL.md
    - source: skills/setup-ci/templates/python.yml
```

- [ ] **Step 6: Commit**

```bash
git add plugins/sdlc-core/skills/setup-ci/ plugins/sdlc-core/skills/new-feature/SKILL.md release-mapping.yaml
git commit -m "feat: add setup-ci skill for GitHub Actions generation (#78)

New skill /sdlc-core:setup-ci generates .github/workflows/sdlc-validate.yml
with language-appropriate checks that mirror the validate skill pipeline.

- Python template: ruff, mypy, pytest, bandit
- new-feature skill now prompts for CI setup on first feature
- Added to release-mapping.yaml"
```

---

### Task 4: Update Release Mapping for New Agent

**Files:**
- Modify: `release-mapping.yaml` — add verification-enforcer agent

- [ ] **Step 1: Add verification-enforcer to release mapping**

In `release-mapping.yaml`, add to the `sdlc-core.agents` section (after line 24):

```yaml
    - source: agents/core/verification-enforcer.md
```

Note: the source agent was created at `plugins/sdlc-core/agents/verification-enforcer.md` during this session. For the release mapping, the canonical source location should be `agents/core/verification-enforcer.md`. Copy the agent to the source location:

```bash
cp plugins/sdlc-core/agents/verification-enforcer.md agents/core/verification-enforcer.md
```

- [ ] **Step 2: Commit**

```bash
git add release-mapping.yaml agents/core/verification-enforcer.md
git commit -m "chore: add verification-enforcer to release mapping

New agent created during integration test review session.
Adds to sdlc-core plugin packaging."
```

---

### Task 5: Integration Verification

**Files:** None (verification only)

- [ ] **Step 1: Verify no wrapper script references remain in plugin skills**

```bash
grep -r "local-validation.py\|validate-pipeline.py\|check-logging-compliance.py\|check-technical-debt.py" plugins/sdlc-core/skills/ --include="*.md"
```

Expected: no output. All wrapper script references should be eliminated from plugin consumer-facing skills.

Note: `release-mapping.yaml` and the source repo's own `tools/validation/` still reference these scripts — that's correct. They're used for validating *this* repo.

- [ ] **Step 2: Verify constitution is in sync**

```bash
diff CONSTITUTION.md plugins/sdlc-core/skills/rules/constitution.md
```

Expected: no output (files identical).

- [ ] **Step 3: Verify all new files exist**

```bash
ls plugins/sdlc-core/skills/validate/SKILL.md
ls plugins/sdlc-core/skills/setup-ci/SKILL.md
ls plugins/sdlc-core/skills/setup-ci/templates/python.yml
ls plugins/sdlc-core/agents/verification-enforcer.md
ls agents/core/verification-enforcer.md
```

Expected: all files exist.

- [ ] **Step 4: Verify release mapping is valid YAML**

```bash
python -c "import yaml; yaml.safe_load(open('release-mapping.yaml'))" 2>/dev/null || python3 -c "import yaml; yaml.safe_load(open('release-mapping.yaml'))"
```

Expected: no error.

- [ ] **Step 5: Commit verification results (if any fixes needed)**

If any issues found, fix and commit. Otherwise, this step is a no-op.

---

### Task 6: Update Epic Issue

**Files:** None (GitHub only)

- [ ] **Step 1: Update #75 with Tier 2 completion status**

```bash
gh issue comment 75 --body "Tier 2 implementation complete:
- #79 Constitution sync: automated via release-mapping + CI drift check
- #76 + #77 Validate skill: rewritten with inline tools + preflight checks
- #78 CI/CD template: new /sdlc-core:setup-ci skill with Python workflow template

Remaining: #80 (Tier 3 — integration test as reusable skill, deferred)"
```

- [ ] **Step 2: Close Tier 2 issues**

```bash
gh issue close 76 --comment "Fixed: validate skill rewritten with inline tool invocations"
gh issue close 77 --comment "Fixed: preflight checks report missing tools with install instructions"
gh issue close 78 --comment "Fixed: new /sdlc-core:setup-ci skill generates GitHub Actions workflow"
gh issue close 79 --comment "Fixed: release-mapping copies CONSTITUTION.md to plugin, CI checks for drift"
```
