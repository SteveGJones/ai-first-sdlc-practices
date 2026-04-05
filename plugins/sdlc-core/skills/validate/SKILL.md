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
