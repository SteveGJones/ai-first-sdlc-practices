---
name: validate
description: Run the SDLC validation pipeline. Use when checking code quality before commits or PRs.
disable-model-invocation: true
argument-hint: "[--syntax | --quick | --pre-push]"
---

# SDLC Validation

Run the validation pipeline with the specified level. Default is `--pre-push` (full 8-check pipeline).

## Arguments

- `--syntax` — Syntax checking only (fast, run after every edit)
- `--quick` — Quick validation (syntax + technical debt, run before commits)
- `--pre-push` — Full 8-check pipeline (run before PRs). This is the default.

## Execution

Run the validation script. The script path is relative to the project root:

```bash
python tools/validation/local-validation.py $ARGUMENTS
```

If no arguments are provided, default to `--pre-push`:

```bash
python tools/validation/local-validation.py --pre-push
```

## Pipeline Checks (--pre-push)

The full pipeline runs 8 checks in sequence:

1. **Syntax Check** — Python AST validation
2. **Pre-commit Hooks** — Black formatting, flake8 linting
3. **Technical Debt** — Zero-debt policy enforcement
4. **Architecture** — Required docs validation
5. **Type Safety** — mypy/pyright checks
6. **Security** — Bandit, dependency scanning
7. **Logging Compliance** — 10 mandatory logging points
8. **Static Analysis** — Code quality metrics

## On Failure

If any check fails:
1. Report which checks failed and why
2. Show the specific violations
3. Suggest fixes for each violation
4. Do NOT proceed with commits or PRs until all checks pass
