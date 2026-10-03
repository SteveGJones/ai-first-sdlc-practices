# Feature Proposal: Wire Logging Compliance into Enforcement Pipeline

**Proposal Number:** 69
**Status:** Complete
**Author:** Claude (AI Agent)
**Created:** 2026-02-10
**Target Branch:** `feature/enforce-logging-compliance`
**Issue:** #71

---

## Executive Summary

Wire the existing `check-logging-compliance.py` (built in v1.7.0, Feature #11) into every enforcement surface — local validation, CI, git hooks, and documentation — so logging compliance is enforced at the same level as technical debt and architecture compliance.

---

## Motivation

### Problem Statement

The logging compliance infrastructure was built in v1.7.0 but is completely disconnected from enforcement:
- CONSTITUTION.md Article 7 defines 10 mandatory logging points
- `check-logging-compliance.py` (717 lines) performs AST-based validation
- `CLAUDE-CONTEXT-logging.md` provides detailed instructions
- But nothing actually invokes the checker during development, validation, or CI

Additionally, a critical bug was discovered: `_check_sensitive_data()` was called with swapped arguments, meaning sensitive data detection was silently broken since v1.7.0.

### User Stories

- As a developer, I want logging compliance enforced automatically so I don't ship code without proper observability
- As a framework user, I want the checker to auto-detect framework repos and exempt them from application-level requirements

---

## Proposed Solution

1. **Fix argument-order bug** in `_check_sensitive_data()` call (line 237)
2. **Add framework-aware context detection** — auto-detect framework repos vs application code, matching `check-technical-debt.py`'s pattern
3. **Add project-level configuration** — support `.ai-sdlc.json` for custom logging backends (structlog, OpenTelemetry, Winston, etc.)
4. **Wire into `local-validation.py`** — add as 8th check in `run_pre_push_validation()`
5. **Add to CI workflow** — new step in `sdlc-validation` job
6. **Update documentation** — CONSTITUTION.md rule 7.3, CLAUDE-CORE.md validation commands
7. **Add to git hooks** — logging compliance check in pre-push hook template

### Acceptance Criteria

Given the logging checker exists but is disconnected
When all enforcement wiring is applied
Then logging compliance runs in local validation, CI, and git hooks

Given a framework repo (like this one)
When the checker auto-detects framework context
Then framework files are exempt from application logging requirements

Given a project with `.ai-sdlc.json` logging config
When the checker runs
Then custom logging patterns are recognized alongside defaults

---

## Success Criteria

- [x] `_check_sensitive_data()` bug fixed (argument order)
- [x] Framework auto-detection works (79 framework, 0 application files)
- [x] `local-validation.py --pre-push` shows "Logging Compliance" as 8th check
- [x] CI workflow has "Logging Compliance Check" step
- [x] CONSTITUTION.md Article 7.3 references the checker command
- [x] CLAUDE-CORE.md lists logging checker in validation commands
- [x] Git hooks pre-push template includes logging compliance
- [x] All Python files compile (`local-validation.py --syntax` passes)

---

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| False positives in application projects | Medium | Framework auto-detection exempts non-app code |
| Custom logging patterns not recognized | Low | `.ai-sdlc.json` config allows adding patterns |
| CI step slows pipeline | Low | Checker runs in < 5 seconds |

---

## Changes Made

| Action | File |
|--------|------|
| Modify | `tools/validation/check-logging-compliance.py` (bug fix + framework detection + config) |
| Modify | `tools/validation/local-validation.py` (add 8th check) |
| Modify | `.github/workflows/validation.yml` (add CI step) |
| Modify | `CONSTITUTION.md` (add rule 7.3) |
| Modify | `CLAUDE-CORE.md` (add checker to validation commands) |
| Modify | `tools/automation/setup-sdlc-git-hooks.py` (add to pre-push hook) |
| Create | `docs/feature-proposals/69-enforce-logging-compliance.md` |
| Create | `retrospectives/69-enforce-logging-compliance.md` |
