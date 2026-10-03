# Retrospective: CI runs the pytest suite (PR1 of #245)

**Branch:** `feature/gates-real-244-245`
**Date:** 2026-10-03
**Tracking Issue:** #245

---

## Summary

CI did not run the test suite. This PR adds a `tests` job (Python 3.11,
3.12, 3.13) to `validation.yml`, makes `Validation Summary` fail when it fails,
adds `requirements-test.txt`, scopes bare `pytest` to `tests/`, and fixes three
Python 3.9 collection errors. The maintainer chose to drop 3.9 from the new job,
so that fix is no longer needed for CI; it is kept for floor consistency.

## Reproduction evidence

Before any code change, `uv run --python 3.9 --with pyyaml --with pytest python
-m pytest tests -q --ignore=research` gave 3 collection errors, all
`TypeError: unsupported operand type(s) for |: 'type' and 'NoneType'`:
`tests/test_preprocess_workflow.py` (line 374) and, via
`tools/validation/check_workflow_teams.py` (line 181),
`tests/test_team_extend_validation.py` and `tests/test_workflow_team_validation.py`.
Two source files were therefore the root cause. The fix is
`from __future__ import annotations` in each. This evidence is why the future
imports exist; they are kept (harmless) so the files stay importable on 3.9.

## Decisions and rationale

- **`from __future__ import annotations`, not `Optional[...]`.** Smallest diff,
  no reformatting, and annotations are never evaluated at runtime in these files.
- **Dedicated `requirements-test.txt`.** The suite needs only pytest and PyYAML;
  `requirements.txt` pulls in safety, mkdocs and others, which slows CI and adds
  failure modes.
- **No `paths:` filters.** A required check that does not run leaves PRs stuck.
- **Clean-tree step.** Fails the job if the tests write into the repository.
- **Dropped 3.9 from the new job (maintainer decision, non-default).** The repo's
  declared floor is NOT changed by this PR. Remaining 3.9 pins: the required
  `Framework Tools (Python 3.9/3.11/3.12)` check, `.pre-commit-config.yaml` black
  `language_version: python3.9`, and `plugins/sdlc-knowledge-base/pyproject.toml`
  `requires-python >=3.9` (other plugin pyprojects are already `>=3.10`). Raising
  the floor formally is a separate sequenced change needing an admin to adjust
  required checks; to be tracked on #244/#245. Consequence: no CI job runs the
  pytest suite on 3.9, so 3.9 regressions in tests are no longer caught.
- **`testpaths = tests`.** Stops bare `pytest` collecting `tmp/` and `research/`.

## Honest caveats

- Only a CI run on Ubuntu can prove the workflow itself: the cache settings,
  the clean-tree step (a local checkout has untracked files that CI does not),
  and the 3.13 matrix leg on `ubuntu-latest`. Locally the suite was run
  with `uv` on macOS.
- Python 3.9 and 3.10 are not in the new job's matrix; 3.10 was verified in the design phase only, and 3.9 was dropped by maintainer decision.
- **Branch protection is an admin step outside this PR.** The new check names
  `Tests (Python 3.11)` etc. are not required until an admin adds them.
- However, `Validation Summary` is already a required check and now depends on
  `tests`, so the suite is enforced as soon as this merges.
- Coverage of `tests/` is unchanged; this PR does not fix any failing or
  skipped tests beyond the collection errors.

## Deviations

Python 3.9 removed from the `tests` matrix by maintainer decision (originally 3.9/3.11/3.12/3.13).
