# Feature Proposal: CI runs the pytest suite (PR1 of #245)

**Proposal Number:** 245
**Status:** In Progress
**Author:** Claude + Steve Jones
**Created:** 2026-10-03
**Target Branch:** `feature/gates-real-244-245`
**Tracking Issue:** #245

---

## Problem Statement

CI has no pytest step. The repository carries roughly 885 tests, but nothing in
`.github/workflows/validation.yml` runs them, so a change can merge with a red
suite. The existing `Framework Tools` job only runs `--help` and `py_compile`.
Bare `pytest` at the repo root also collects `tmp/` and `research/` and fails
with 24 collection errors, and on Python 3.9 (still the declared floor in
several places, see below) three test modules cannot even be collected.

## Motivation

A test suite that CI does not run is not a gate. `Validation Summary` is already
a required status check, so wiring the tests into it makes the suite enforced
without any new branch-protection entry.

## Proposed Solution

1. **Python 3.9 import fix (kept for floor consistency).** Add `from __future__ import annotations` as the first
   statement after the module docstring in `tools/validation/check_workflow_teams.py`
   and `tests/test_preprocess_workflow.py`. Both use PEP 604 `X | None` in
   signatures, which raises `TypeError` at import on 3.9. The new pytest job does
   not run on 3.9 (see item 4), so this is not needed to make CI green; it is
   kept because it is harmless and keeps these files importable on 3.9 while 3.9
   remains the declared floor elsewhere. Neither file is mirrored into a plugin
   copy (`release-mapping.yaml` does not reference them).
2. **`pytest.ini`**: add `testpaths = tests` so bare `pytest` stops collecting
   `tmp/` and `research/`. Existing settings are unchanged.
3. **`requirements-test.txt`**: `pytest>=7.4.0` and `PyYAML>=6.0`, the only
   packages the suite needs, matching the pin style of `requirements.txt`. The
   full `requirements.txt` is deliberately not used in CI.
4. **`validation.yml`**: new `tests` job, matrix Python 3.11 / 3.12 / 3.13
   (the maintainer chose to drop 3.9 from this new job; see Python floor below),
   `fail-fast: false`, 10 minute timeout, pip cache keyed on
   `requirements-test.txt`, running
   `python -m pytest tests -q -ra --strict-markers -p no:cacheprovider`, followed
   by a step that fails if the run left the working tree dirty. No `paths:`
   filters, so the check always runs. `Validation Summary` gains `tests` in
   `needs:` and fails when the tests job does not succeed.

## Success Criteria

- `pytest tests` passes fully on Python 3.11, 3.12 and 3.13.
- Bare `pytest` at the repo root collects only `tests/`.
- The workflow YAML parses and `Validation Summary` fails when `tests` fails.
- All validators pass with zero technical debt.

## Python floor (not changed by this PR)

The maintainer chose, as a non-default decision, to drop Python 3.9 from the new
`tests` job. This PR does **not** change the repository's declared floor. Other
3.9 pins remain:

- `Framework Tools (Python 3.9/3.11/3.12)` job in `validation.yml`, a required
  status check (matrix `['3.9', '3.11', '3.12']`).
- `.pre-commit-config.yaml` black hook `language_version: python3.9`.
- `plugins/sdlc-knowledge-base/pyproject.toml` `requires-python = ">=3.9"`
  (the other plugin pyprojects checked, sdlc-core, sdlc-workflows,
  sdlc-programme and sdlc-assured, already say `>=3.10`).
- `python-version: '3.9'` in other jobs of `validation.yml`.

Formally raising the floor is a separate, sequenced change: it needs an admin to
adjust the required status checks (removing the 3.9 Framework Tools check would
otherwise leave a required check that never reports and block every merge). To be
tracked on #244/#245.

## Out of Scope

- The flake8 and pre-commit steps in `code-quality` (tracked as #244, the follow-up PR).
- Adding the new `Tests (Python ...)` check names to branch protection (admin
  step, see the retrospective).
- Coverage reporting.
