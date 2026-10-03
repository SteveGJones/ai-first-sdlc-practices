# Validation Infrastructure for Plugin Consumers

**Date**: 2026-04-04
**Status**: Approved
**Epic**: #75 — Plugin Ecosystem Integration Test Findings
**Issues**: #76, #77, #78, #79

## Problem

The SDLC plugin validation pipeline is non-functional on fresh project installs. The `validate` skill calls Python wrapper scripts (`local-validation.py`, `validate-pipeline.py`, `check-logging-compliance.py`) that exist in the source repo but aren't bundled with the plugin. This is the #1 blocker for external use.

Additionally:
- Validation failures don't distinguish missing tools from code errors (#77)
- No CI/CD template is provided (#78)
- The Constitution has two manually-synced copies that can drift (#79)

## Evidence

Ralph loop integration test (2026-04-04) on a blank project:
> "Full `--pre-push` validation blocked: helper scripts `validate-pipeline.py` and `check-logging-compliance.py` are missing from the sdlc-core 0.1.0 plugin installation. This is an environment defect."

## Solution: Inline Tool Invocations

Replace wrapper scripts with direct tool calls in the validate skill. No Python code to maintain. Each check includes a preflight gate that verifies the tool is available before running it.

### Validate Skill Rewrite (#76 + #77)

Three validation tiers, each a list of direct commands:

#### `--syntax` (after every edit)

Fast syntax-only check. No external tools required beyond Python itself.

```
1. Python AST check — parse all .py files with ast.parse()
2. Ruff select E,F only — syntax errors and undefined names (if ruff installed)
```

Preflight: Python is always available. Ruff is optional at this tier (warn if missing, don't fail).

#### `--quick` (before commits)

Includes syntax, plus formatting and tests.

```
1. All --syntax checks
2. Ruff full check — ruff check .
3. Ruff format check — ruff format --check .
4. Test execution — pytest --tb=short -q
5. Import smoke test — python -c "import <main_module>"
```

Preflight for each:
- `ruff` not found → "ruff not installed. Run: pip install ruff"
- `pytest` not found → "pytest not installed. Run: pip install pytest"
- No `tests/` directory → "No tests directory found. Tests are mandatory (Article 10.2)."
- No test files → "tests/ exists but contains no test files. Tests are mandatory."

#### `--pre-push` (before PRs)

Full pipeline. Includes quick, plus type checking, security, and runtime verification.

```
1. All --quick checks
2. Type checking — mypy . (or mypy <source_files>)
3. Security scan — bandit -r . --exclude .venv
4. Smoke test — start app, curl one endpoint, verify HTTP 200, stop app
```

Preflight:
- `mypy` not found → "mypy not installed. Run: pip install mypy"
- `bandit` not found → "bandit not installed. Run: pip install bandit"
- No app entry point found → "Cannot smoke test: no app.py or main.py found. Skip or create entry point."

#### Language Detection

The skill detects project language by scanning file extensions:
- `*.py` dominant → Python checks (ruff, mypy, pytest, bandit)
- `*.ts`/`*.js` dominant → JS checks (eslint, tsc, jest/vitest)
- `*.go` dominant → Go checks (go vet, staticcheck, go test)

Python is the primary target for this implementation. Other languages use the same structure but different tool names.

#### Error Output Format

Each check reports in a consistent format:

```
[PASS] Syntax check — 12 files checked, 0 errors
[PASS] Ruff — 0 issues
[FAIL] Pytest — 2 failed, 18 passed (see output above)
[SKIP] Mypy — not installed (run: pip install mypy)
[FAIL] Smoke test — app crashed on startup (see error above)

Result: 2 FAIL, 1 SKIP, 2 PASS — fix failures before proceeding
```

The `[SKIP]` status with install instructions is the key difference from the current approach, which just crashes with a Python traceback.

### CI/CD Template (#78)

New skill: `/sdlc-core:setup-ci`

Generates `.github/workflows/sdlc-validate.yml` that mirrors the validate skill's `--pre-push` checks. Same tools, same order, same pass/fail criteria.

**Python template**:

```yaml
name: SDLC Validation
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Setup venv and install dependencies
        run: |
          python -m venv .venv
          source .venv/bin/activate
          pip install -r requirements.txt
          pip install -r requirements-dev.txt 2>/dev/null || true
      - name: Lint
        run: |
          source .venv/bin/activate
          ruff check .
          ruff format --check .
      - name: Type check
        run: |
          source .venv/bin/activate
          mypy . || mypy $(find . -name "*.py" -not -path "./.venv/*")
      - name: Test
        run: |
          source .venv/bin/activate
          pytest -v --tb=short
      - name: Security
        run: |
          source .venv/bin/activate
          bandit -r . --exclude ./.venv -q
```

The `new-feature` skill is updated: on the first feature (no `.github/workflows/` exists), it suggests running `/sdlc-core:setup-ci`.

### Constitution Sync (#79)

Two changes:

1. **Release mapping**: Add entry to `release-mapping.yaml` so `release-plugin` copies `CONSTITUTION.md` → `plugins/sdlc-core/skills/rules/constitution.md` automatically.

2. **Drift check**: Add to the repo's own CI workflow:
```yaml
- name: Check constitution sync
  run: diff CONSTITUTION.md plugins/sdlc-core/skills/rules/constitution.md
```

This catches drift at PR time in the source repo.

## Dependency Order

```
#79 (constitution sync) — standalone, quick
    ↓
#76+77 (validate skill rewrite) — the core change
    ↓
#78 (CI/CD template) — mirrors validate checks
```

## Files Changed

| Issue | Action | File |
|-------|--------|------|
| #79 | Edit | `release-mapping.yaml` — add constitution copy rule |
| #79 | Edit | `.github/workflows/*.yml` — add drift check step |
| #76+77 | Rewrite | `plugins/sdlc-core/skills/validate/SKILL.md` |
| #78 | Create | `plugins/sdlc-core/skills/setup-ci/SKILL.md` |
| #78 | Create | `plugins/sdlc-core/skills/setup-ci/templates/python.yml` |
| #78 | Edit | `plugins/sdlc-core/skills/new-feature/SKILL.md` — add CI prompt |
| #78 | Edit | `plugins/sdlc-core/.claude-plugin/plugin.json` — register new skill |

## Success Criteria

1. Run PROMPT.md integration test on a fresh blank project
2. `/sdlc-core:validate --pre-push` completes with clear output for every check
3. Missing tools show `[SKIP]` with install instructions, not crashes
4. CI workflow runs and passes on the test project's PR
5. Constitution changes in source automatically propagate to plugin on release

## What This Does NOT Change

- `tools/validation/local-validation.py` in the source repo — still used for validating this repo
- Existing agents — untouched
- The verification-enforcer agent — works independently
- Plugin install mechanism — unchanged, just the skill content is different
