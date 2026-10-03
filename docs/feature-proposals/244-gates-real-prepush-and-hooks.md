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

Ten commits on this branch (after `631a626`; nine reviewed plus the fifth-round fix): the five steps below plus five review-round fix commits:

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
   throwaway worktree, to 109 files: 64 Python (AST-identical, including the
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
- Fixing the latent `# implements:` parsing gap (see the retrospective). The
  `build_shelf_index.py` empty-`**Terms:**` trailing space was originally listed
  here and was fixed in the review round.
- Any change to `Framework Tools` or `Tests (...)` jobs.

## Review round

An Opus review added the following to the scope; details are in the
retrospective.

- The statement above that `--no-ensure-ascii` stops the JSON hook undoing the
  catalog generator was only half true: the encoding matched but the generator
  omitted the final newline. `agent-catalog-update.yml` commits the regenerated
  `AGENT-CATALOG.json` and `AGENT-INDEX.md` to `main`, so with the hooks
  blocking it would have turned the next unrelated PR red. The generator now
  emits exactly one trailing newline in both files (tested).
- The `build_shelf_index.py` trailing space after an empty `**Terms:**` /
  `**Links:**` is fixed (previously deferred), `kb_stats` no longer lets its
  Terms/Links regexes cross a newline on an empty value, and the
  `sdlc-knowledge-base` plugin is bumped 0.3.2 -> 0.3.3.
- Gate hardening: `git worktree prune` before the add, a failed worktree removal
  is an error, a timeout kills the whole process group, and the tripwire
  reports only the before/after difference and sees new files in untracked
  directories (documented limits: gitignored files, concurrent writers).
- Known limits recorded, not acted on: the `black` hook needs a `python3.9`
  interpreter locally, and the `# noqa: E501` at `traceability_validators.py`
  would be swallowed by the `# implements:` regex if that parsing gap is fixed.

## Second review round

- **Tripwire**: untracked files are compared by path set only (new/removed
  paths trip it), not by content, because the gate's own output may be
  redirected into an untracked file inside the repo and grow during the run.
  Tracked files and the protected-corpus index entries keep content hashing.
  Untracked content and gitignored files are not covered.
- **AGENT-INDEX.md**: the committed index carried hand-written notes that the
  generator did not emit and a regeneration would wipe (it already did once).
  The notes now live in `tools/automation/agent-index-notes.md` and are emitted
  verbatim by `build-agent-catalog.py`; the counts line is computed; both
  committed outputs were regenerated (a second run changes only the timestamp).
- **Gate hardening**: SIGTERM raises so the process group is killed and the
  worktree removed; undecodable output no longer raises; the post-kill drain has
  a 10 second limit.
- **Output-only fixes**: no trailing space after an empty `**Links:**` in
  `code_index.py`; no leading blank lines when appending to an empty `log.md`.
- **Versions**: formatting/mode-only plugin changes (`sdlc-workflows`,
  `sdlc-model-council`, `sdlc-assured`, black re-wraps, `plugin.json` reformat)
  are intentionally not bumped; `sdlc-knowledge-base` is bumped to 0.3.3
  because its behaviour changed; the `sdlc-assured` `code_index.py` whitespace
  change is output-only and not bumped.
- **Known limits**: `documentation.yml`'s third-party `toc-generator` action
  opens a PR and could not be verified locally; the black hook needs
  `python3.9` locally; the `noqa: E501` placement in
  `traceability_validators.py` depends on the `# implements:` parsing gap.

## Fourth review round

- **Gate worktree lifecycle**: each gate call owns a unique worktree
  (`prepush-gate-<pid>-<8 hex>`); cleanup removes only that path and handles a
  registration left LOCKED as `initializing` by a creation killed mid-checkout
  (unlock, retry, delete the directory, prune). `repo_root` is resolved to an
  absolute path. A second SIGTERM can no longer skip the cleanup or the signal
  handler restore.
- **Tests**: process markers in `tests/test_pre_push_gate.py` are unique per
  invocation (the previous host-wide `sleep 31337` patterns made concurrent runs
  interfere); waits are polling loops. The repo-env variable list is memoised.

## Fifth review round

Opus verified a swallowed-SIGTERM regression introduced by the previous round, a
thread bug in the shared mute flag, and an unguarded deletion (it deleted a whole
throwaway checkout); Codex returned a second NO-GO (deletion safety,
concurrency). The branch now has ten commits: nine reviewed plus this fix.

- **Signal handling replaced, not patched again.** No module-level signal state.
  A module lock serialises gate calls; the SIGTERM handler is installed only in
  the main thread on POSIX; the handler blocks further SIGTERM then raises
  `GateTerminated`; cleanup blocks SIGTERM, kills the hook's process group,
  removes the worktree, restores the previous handler, then unblocks, so a
  SIGTERM that arrives during cleanup (even a plain one) is delivered to the
  original disposition afterwards and is never dropped. A previous `SIG_IGN`
  stays ignored by the caller's choice. The earlier statement that further
  SIGTERMs were "recorded" was wrong: they were dropped.
- **Residual window**: a signal handled between the end of the `try` body and the
  first statement of the `finally` still raises from inside the `finally` and
  would skip that call's cleanup. Nothing more is claimed.
- **Deletion guard**: `_remove_worktree` only touches a non-symlink path directly
  under the real `<repo>/tmp`, named `prepush-gate-<pid>-<8 hex>`, minted by this
  call; creation refuses a symlinked `tmp`. Anything else is refused with an
  error naming the failed check.
- **Tests**: new tests for each of the above, each seen to fail first; the timeout
  test re-verifies the marker before killing recorded pids.
