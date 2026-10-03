# Retrospective: Feature #69 — Wire Logging Compliance into Enforcement Pipeline

**Branch**: `feature/enforce-logging-compliance`
**Date**: 2026-02-10
**Issue**: #71

## What Went Well

- **Discovery was the key insight**: The logging infrastructure already existed (Feature #11, v1.7.0) — it just needed wiring into enforcement. This turned a "build from scratch" task into a "connect existing pieces" task.
- **Bug fix was high-value**: The swapped `_check_sensitive_data(content, file_path)` arguments meant sensitive data detection was silently broken since v1.7.0. A one-line fix restored a critical security feature.
- **Framework auto-detection pattern reuse**: Copying the proven pattern from `check-technical-debt.py` made framework/application context detection reliable and consistent.
- **Configuration support is forward-looking**: The `.ai-sdlc.json` config allows teams to specify their logging backend (structlog, OpenTelemetry, Winston) without modifying the checker.

## What Could Improve

- **The original Feature #11 should have wired into enforcement from the start**: Building a validator without integrating it into the enforcement pipeline meant it sat unused for multiple versions.
- **Sensitive data detection bug went unnoticed**: No test coverage caught the argument swap — highlights the need for integration tests on validation tools.

## Lessons Learned

1. **Validation tools need enforcement wiring at creation time**: A checker that nobody invokes provides zero value. Future validators should be wired into local-validation.py, CI, and git hooks as part of their initial feature.
2. **Framework repos need special handling**: The AI-First SDLC repo contains framework tools, not application code. Every checker needs context-aware detection to avoid false positives.
3. **Argument order bugs are silent killers**: Python doesn't enforce parameter names at call sites. When two parameters have the same type (both strings/paths), swapping them compiles fine but produces wrong results.
4. **Enforcement surfaces cascade**: CONSTITUTION.md (rules) -> CLAUDE-CORE.md (commands) -> local-validation.py (pre-push) -> CI workflow (pipeline) -> git hooks (automated). All must be updated together.

## Changes Made

- `tools/validation/check-logging-compliance.py`: Fixed `_check_sensitive_data()` argument order, added framework auto-detection, added `.ai-sdlc.json` config support, added `--context` CLI argument
- `tools/validation/local-validation.py`: Added `check_logging_compliance()` as 8th check in pre-push validation
- `.github/workflows/validation.yml`: Added "Logging Compliance Check" step to sdlc-validation job
- `CONSTITUTION.md`: Added rule 7.3 with checker command reference
- `CLAUDE-CORE.md`: Added logging checker to Logging section and Essential Commands
- `tools/automation/setup-sdlc-git-hooks.py`: Added logging compliance check to pre-push hook template

## Metrics

- **Bug fixed**: 1 critical argument-order bug (sensitive data detection restored)
- **Enforcement surfaces wired**: 4 (local-validation, CI, git hooks, documentation)
- **New capabilities**: Framework auto-detection, `.ai-sdlc.json` config support
- **Files modified**: 6
- **Files created**: 2 (proposal + retrospective)
