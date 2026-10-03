# Feature Proposal: Make the pre-push and pre-commit gates real (#244)

**Proposal Number:** 244
**Status:** In Progress
**Author:** Claude + Steve Jones
**Created:** 2026-10-03
**Target Branch:** `feature/gates-real-244`
**Tracking Issue:** #244

---

## Problem Statement

The repository's own quality gates could not pass and, worse, could damage the
tree. `local-validation.py --pre-push` ran `pre-commit` with auto-fixing hooks
inside the developer's own checkout and silently rewrote 144 tracked files in a
single run, including 38 under `research/poker-capstone/` (verbatim model
output that must stay byte-identical; the run was reverted). Separately, the
pinned hooks failed on a clean tree, and CI ran `pre-commit` with
`|| echo "::warning::..."` plus an unpinned `flake8`, so no hook failure could
ever block a merge.

Measured on a clean tree (not after hooks had already rewritten files, which is
how the first, rosier count was taken): black would reformat about 69 files,
pretty-format-json about 40, and trailing-whitespace / end-of-file-fixer more,
on top of the shebang and flake8 findings. The earlier "42 shebang + 15 flake8"
figure understated the baseline.

## Motivation

A gate that mutates the tree it guards, fails on a clean checkout, or only warns
is not a gate. The aim is: the hooks pass on `main`, the local pre-push check
cannot change the working tree, and CI blocks on the same pinned hooks.

## Proposed Solution

Five commits on this branch (after `631a626`):

1. **Corpus excludes and hook args** (`025aaca`). A top-level `exclude:` in
   `.pre-commit-config.yaml` makes every hook skip `research/poker-capstone/runs`,
   `broken-variants`, `plugins/*/assessment` and `research/sdlc-bundles/outputs`;
   `setup.cfg` flake8 exclude gains the same paths. `trailing-whitespace` gets
   `--markdown-linebreak-ext=md`; `pretty-format-json` gets `--no-ensure-ascii`
   (matching the `AGENT-CATALOG.json` generator). The `_code-index` generator no
   longer emits a trailing space after an empty `**Terms:**`. No hook revisions
   bumped.
2. **Non-mutating pre-push gate** (`e1f38fa`). `check_pre_commit_hooks` runs the
   hooks in a throwaway detached worktree of HEAD and always removes it; any
   non-zero exit or diff is a failure. `run_pre_push_validation` snapshots
   `git status --porcelain`, `git diff` and the poker-capstone `git ls-files -s`
   hash before and after and fails with a TRIPWIRE error naming changed paths.
   Hook timeout 1800s. 17 hermetic tests in `tests/test_pre_push_gate.py`
   (`repo: local`, `language: system` hooks, nothing downloaded).
   `requirements-test.txt` gains `pre-commit`.
3. **Shebang / mode / flake8** (`6156cf5`). 21 files gain the executable bit
   (8 `sdlc-workflows` scripts, 4 `tools/` entry points, 9 model-council
   `test-*.sh`); 15 shebangs removed (13 `tests/test_*.py`, `override_logger.py`,
   `resolve_plugin_paths.py`); 5 sourced shell files get
   `# shellcheck shell=bash` instead of a shebang; flake8 7.0.0 findings fixed
   (late imports merged, unused imports removed, F541, E305, `noqa` where
   justified).
4. **Mechanical normalisation** (`7404153`). The pinned hooks applied once, in a
   throwaway worktree, to 109 files: 63 Python (AST-identical, including the
   extensionless `mlx-chat`), 30 JSON (parse to equal data), 15 Markdown
   (whitespace-only lines and end-of-file newlines). Corpus hashes identical
   before and after. Four non-corpus files under `research/` (two poker-capstone
   harness scripts, two sdlc-bundles synthesis notes) were re-wrapped.
5. **Blocking pre-commit in CI** (this commit). In `validation.yml` job
   `code-quality`: install only `pre-commit`; drop the unpinned `Flake8 Linting`
   step (and its informational complexity report); cache `~/.cache/pre-commit`
   with `actions/cache@v4`; run `pre-commit run --all-files --show-diff-on-failure`
   with no `|| echo`. In `summary`, `Code Quality` renders Pass/Fail and fails
   the job when `code-quality` did not succeed, following the existing `tests`
   pattern.

## Success Criteria

- `pre-commit run --all-files --show-diff-on-failure` exits 0 on a clean
  worktree of the branch with no modifications (verified in a throwaway
  worktree).
- `local-validation.py --pre-push` cannot change the working tree; a tripwire
  proves it.
- Byte-identical corpora are untouched.
- `pytest tests` passes (903 tests).
- The workflow YAML parses; actionlint reports only the pre-existing
  `github.head_ref` finding.
- `Code Quality Analysis` and `Validation Summary` block on hook failures.

## Decisions and Notes

- `research/sdlc-bundles/reviews/` does not exist, so it is not in the exclude
  regex.
- Scripts with a `__main__` guard received `+x` even where nothing executes them
  directly (Part B decision, favouring a uniform rule over per-file archaeology).
- The pre-push gate validates committed state (HEAD), not uncommitted edits.
- Python floor: the black hook keeps `language_version: python3.9` and the
  `Framework Tools (Python 3.9)` check remains. The floor is NOT raised here
  (see #245).
- Hooks are bumped deliberately with `pre-commit autoupdate`, not through
  `requirements.txt`. Dependabot PR #181 (black>=25.11) conflicts with the pinned
  hook and should be closed.

## Out of Scope

- Raising the Python floor.
- Fixing the latent `# implements:` parsing gap and the `build_shelf_index.py`
  empty-`**Terms:**` trailing space (see the retrospective).
- Any change to `Framework Tools` or `Tests (...)` jobs.
