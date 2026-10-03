# Retrospective: Make the pre-push and pre-commit gates real (#244)

**Branch:** `feature/gates-real-244`
**Date:** 2026-10-03
**Tracking Issue:** #244

---

## Summary

Ten commits (nine reviewed plus the fifth-round fix) make the repository's hooks passable, stop `--pre-push` from
mutating the tree, and make CI block on the pinned pre-commit hooks. A run of
`pre-commit run --all-files --show-diff-on-failure` in a throwaway worktree of
the pre-final HEAD exits 0 with all 15 hooks Passed and a clean
`git status --porcelain`.

## What was done

1. Corpus excludes, hook args, `_code-index` trailing space (`025aaca`).
2. Non-mutating gate in a throwaway worktree, tripwire, 17 hermetic tests,
   `pre-commit` in `requirements-test.txt` (`e1f38fa`).
3. 21 mode changes, 15 shebang removals, 5 shellcheck directives, flake8 fixes
   (`6156cf5`).
4. 109-file mechanical normalisation (`7404153`): 64 Python files AST-identical
   (incl. extensionless `mlx-chat`), 30 JSON equal data, 15 Markdown
   whitespace/EOF only; corpus hashes identical; 4 non-corpus files under
   `research/` re-wrapped.
5. Blocking pre-commit in CI; unpinned flake8 and the complexity report dropped
   (this commit).

## Incidents and honest corrections

- **Baseline was worse than first reported.** On a clean tree black would
  reformat about 69 files and pretty-format-json about 40, plus whitespace and
  end-of-file fixes. The earlier "42 shebang + 15 flake8" count was measured
  after hooks had already rewritten files, so it understated the problem.
- **Original incident.** A `--pre-push` run rewrote 144 files, including 38 in
  `research/poker-capstone/`. It was reverted. This is the reason for the
  corpus excludes, the throwaway-worktree gate and the tripwire.
- **Process incident in this work.** Two agents shared one working tree. One
  reverted the other's finished shebang/flake8 work, mistaking it for stray
  changes. It was fixed by redoing the work with a single agent and a rule never
  to restore or reset. Lesson: isolate parallel agents in separate worktrees.

## Decisions

- `research/sdlc-bundles/reviews/` does not exist, so it is not in the exclude
  regex. Add it if the directory is created.
- Part B gave `+x` to scripts with a `__main__` guard even where nothing
  executes them directly; a uniform rule was preferred to per-file archaeology.
  Files only imported or run via pytest lost their shebang instead.
- The standalone flake8 step and the informational complexity report were
  removed rather than kept: the pinned hook (flake8 7.0.0) is the single source.
- Hook timeout is 1800s to allow first-run environment installs.
- Hooks are bumped deliberately with `pre-commit autoupdate`, not via the
  `requirements.txt` pin. Dependabot PR #181 (black>=25.11) conflicts with the
  pinned hook (black 23.12.1) and should be closed.
- Python 3.9 floor: the black hook `language_version: python3.9` and the
  `Framework Tools (Python 3.9)` check remain, so `code-quality` stays on 3.9.
  The floor is not raised here (see #245 and the python-floor note).

## Known gaps and caveats

- **Latent gap, not fixed:** the trailing `# implements:` comment on the `):`
  line in `plugins/sdlc-assured/scripts/assured/traceability_validators.py`
  (line 49 when 6156cf5 was written; around line 57 at HEAD) is never parsed,
  because the regex needs a leading `#`. A `noqa: E501` was added; behaviour is
  unchanged.
- The empty-`**Terms:**` trailing space in `build_shelf_index.py` was deferred
  in the first pass and is FIXED in the review round (see below).
- The pre-push gate validates HEAD (committed state), not uncommitted edits.
- Four files under `research/` outside the protected corpora were re-wrapped;
  nothing pins a hash of them.

## Verification

Local: workflow YAML parses; actionlint reports only the pre-existing
`github.head_ref` finding (~line 52); the hook run in a throwaway worktree
exits 0 and leaves the worktree clean; the pytest suite passes (903 before the
review round, 920 after).

Only the PR's own CI can prove: the blocking `Code Quality Analysis` job on
Ubuntu with a cold hook cache (hook environments install from scratch, Python
3.9 for black), the cache step itself, and `Validation Summary` behaviour when
`code-quality` fails.

## Admin

No new admin step beyond the already-noted `Tests (...)` check names. `Code
Quality Analysis` is already a required check and now actually blocks.

## Deviations

None from the approved plan.

## Review round

An Opus review of the PR found the following; all but the last two were acted on.

- **Auto-committing generators (Important).** `agent-catalog-update.yml`
  regenerates `AGENT-CATALOG.json` and `AGENT-INDEX.md` and commits them to
  `main` with `[skip ci]`. `build-agent-catalog.py` wrote both without a final
  newline (the index with two), so the `end-of-file-fixer` hook would have
  failed on the next unrelated PR now that `pre-commit run --all-files` is
  blocking. Both outputs now end with exactly one newline, the index also
  strips trailing whitespace per line, and `tests/test_agent_catalog_output.py`
  pins both (JSON equals `json.dumps(obj, indent=2, ensure_ascii=False) + "\n"`).
  The sweep of `.github/workflows/` found no other workflow that commits
  generated output from a script: `constitution-sync` and `plugin-packaging-sync`
  only diff/check, `release.yml` publishes a release, and `documentation.yml`
  opens a PR through the third-party `toc-generator` action (not a repo script,
  so not verifiable here).
- **Shelf-index trailing space (was deferred, now fixed).** `_render_entry`
  emitted `**Terms:** ` and `**Links:** ` with a trailing space when empty;
  with the hooks blocking, the next rebuild of a library with such an entry
  would fail CI. Both lines are now emitted without the space when empty and are
  byte-identical when non-empty. `_build_index_content` now always ends with
  exactly one newline (an empty library previously ended with a blank line) and
  `_append_to_log` normalises the join. While checking consumers, `kb_stats`
  used `\s+`/`\s*` after `**Terms:**`/`**Links:**`, which can cross a newline:
  for an EMPTY value the regex captured the next line (`**Facts:**` /
  the next `## N.` heading). Both now use `[ \t]*`. `priming.py` already used
  `[ \t]*`. The KB plugin is bumped 0.3.2 -> 0.3.3 (`plugin.json` and
  `marketplace.json`); the changed scripts ship in place per
  `release-mapping.yaml`, so no mirrored copy needs syncing.
- **`--no-ensure-ascii` was only half the story.** The proposal says the hook
  arg stops `pretty-format-json` undoing the catalog generator. That was only
  half true: the encoding matched, but the missing trailing newline did not.
  Now fixed at the generator.
- **Gate hardening.** `check_pre_commit_hooks` now (a) runs `git worktree prune`
  before as well as after `git worktree add`, so a stale registration from a
  killed run cannot break the add; (b) reports a failed `git worktree remove`
  as an error naming the path and fails the gate; (c) runs children in their own
  session and kills the whole process group on timeout, so hook grandchildren
  do not outlive the worktree (POSIX; Windows falls back to `kill()`). The
  tripwire (d) now snapshots per-file status and content hashes using
  `git status --porcelain -z --untracked-files=all`, so a new file inside an
  already-untracked directory is seen, and reports only the DIFFERENCE between
  before and after. Documented limits: gitignored files are not covered, and a
  concurrent writer to the same checkout would be blamed on the gate.
- **Test hygiene.** `tests/test_pre_push_gate.py` fixtures are isolated from
  the developer's global git config (`GIT_CONFIG_GLOBAL`, `GIT_CONFIG_NOSYSTEM`,
  `-c commit.gpgsign=false -c core.hooksPath=/dev/null`). New tests cover the
  protected-corpus branch of the tripwire, `worktree add` failure,
  `worktree remove` failure, a stale registered worktree, the timeout path
  (no orphan `sleep`), diff-only reporting and new files in untracked dirs.

### Findings not acted on (known limits)

- The `black` hook is pinned `language_version: python3.9`, so it needs a
  `python3.9` interpreter locally. It works here only because `/usr/bin/python3`
  is 3.9.6; CI uses `setup-python` 3.9.
- The `# noqa: E501` in `traceability_validators.py` sits after the unparsed
  `# implements:` IDs. If that parsing gap is ever fixed, the `.+$` in the
  regex would swallow the `noqa` comment.

## Second review round

A second review found the following. The pytest suite is now 935 tests.

- **Tripwire blamed the gate for its own log (Important).** The tripwire hashed
  the CONTENT of every untracked file, so `--pre-push --verbose | tee
  command-runs/cmd-3.log` (an untracked, non-ignored file inside the repo)
  grew during the run and the gate reported `TRIPWIRE: files changed during the
  run`. Untracked files are now compared by PATH SET only (paths that newly
  appear or disappear); content and status hashing is kept for tracked files
  and the protected-corpus index entries. Documented limits: untracked content
  and gitignored files are not covered, and a concurrent writer that adds or
  removes untracked paths, or edits tracked files, during the run would be
  blamed on the gate. Tracked files are now hashed in 1 MiB chunks, and the
  status parser skips the rename/copy source record when `R`/`C` is in either
  status column.
- **AGENT-INDEX.md finding (Important), resolved.** The committed
  `AGENT-INDEX.md` carried hand-written content the generator did not emit (a
  "manual notes re-added" header, a richer counts line, a `Note` paragraph and
  an "SDLC method bundles" paragraph). It had already been wiped by one
  regeneration and re-added by hand on 2026-07-23, and merging this PR would
  trigger `agent-catalog-update.yml` again (the script is in its `paths:`).
  Decision: lose nothing. The two paragraphs now live in
  `tools/automation/agent-index-notes.md` and the generator includes them
  verbatim; the three counts inside the `Note` paragraph are placeholders filled
  from the data. The counts line is computed (total entries; entries in the
  `agents/` source directory; entries published in plugins; plugins with a
  manifest; plugins that ship agents), giving 160 / 87 / 73 / 20 / 18 on the
  current tree, equal to the committed numbers. The notes file is added to the
  workflow's `paths:`. Both committed outputs were regenerated in a throwaway
  worktree; the committed catalog was stale (158 entries; the two
  `sdlc-model-council` agents were missing from the JSON, and the keywords of
  `play-store-release-specialist` lacked `python`). A second generator run
  differs only by the timestamp line.
- **SIGTERM, decode and post-kill hardening.** `start_new_session=True` meant a
  SIGTERM to the gate (CI cancel, outer timeout) left the children running and
  the worktree in place. `check_pre_commit_hooks` now installs a SIGTERM handler
  (POSIX, main thread, restored afterwards) that raises `GateTerminated`, so the
  existing `finally` kills the process group and removes the worktree.
  `run_command` decodes with `errors="replace"` (a `UnicodeDecodeError` used to
  traceback instead of failing the check), and after killing the group on
  timeout waits at most 10 seconds for the pipes before giving up.
- **Output-only fixes.** `render_code_index` emitted `**Links:** ` with a
  trailing space when `cited_ids` was empty; `_append_to_log` on an EMPTY
  `log.md` started the file with two blank lines. Both fixed with tests.

### Version bumps

Formatting- and mode-only changes to plugin files (`sdlc-workflows`,
`sdlc-model-council`, `sdlc-assured`, black re-wraps, the `plugin.json`
reformat) are intentionally NOT version-bumped: behaviour is unchanged.
`sdlc-knowledge-base` IS bumped to 0.3.3 because its behaviour changed
(`kb_stats` parsing and `build_shelf_index.py` output). The `sdlc-assured`
`code_index.py` trailing-space change only affects generated output whitespace
and is NOT bumped.

### Known limits (all of those promised by the previous commit message)

- **AGENT-INDEX.md hand-written content:** resolved above (the generator now
  emits it). The `Note` and bundle paragraphs remain hand-maintained text in
  `agent-index-notes.md`, including the versions and skill counts in the bundle
  paragraph, which can go stale.
- **`documentation.yml`:** its third-party `toc-generator` action opens a PR;
  it could not be run or verified locally and its output is not checked against
  the hooks.
- **black / python3.9:** the black hook needs a `python3.9` interpreter locally
  (works here only because `/usr/bin/python3` is 3.9.6; CI uses `setup-python`
  3.9).
- **`noqa` placement:** the `# noqa: E501` in `traceability_validators.py` sits
  after the unparsed `# implements:` IDs and would be swallowed by the `.+$` in
  the regex if that parsing gap is ever fixed.
- Untracked file content and gitignored files are not covered by the tripwire.

## Third review round

Codex reviewed the branch and returned **NO-GO**; an earlier Fable review
returned GO. Fable ran everything with PyYAML installed and outside a git-hook
environment, so it could not see any of the three blocking findings. Codex's
sandbox could not create worktrees, so it reviewed by reading the code plus a
read-only git probe (it confirmed that inherited `GIT_DIR`/`GIT_WORK_TREE`
override another working directory). Its findings were not reproduced by
running the gate in its sandbox; they were reproduced and fixed here.

- **B1: inherited repository-selection variables (blocking).** The gate ran
  `git worktree ...` and `pre-commit` with the inherited environment. A git
  hook exports `GIT_DIR`/`GIT_WORK_TREE`, which override `cwd=<worktree>`, so
  pre-commit could discover the MAIN checkout and its formatters rewrite it.
  Fix: `sanitized_git_env()` removes the variables listed by
  `git rev-parse --local-env-vars` (with a hard-coded fallback list) from the
  environment of every git/pre-commit child (`run_command`) and of the
  tripwire's own git snapshots; `GIT_CONFIG_GLOBAL` and `GIT_CONFIG_NOSYSTEM`
  are deliberately kept. Proof: a hermetic test points `GIT_DIR`/`GIT_WORK_TREE`
  at a temp "main" repo with a mutating hook and gates a second temp repo; it
  FAILED before the fix (the main repo's tracked file gained `mutated`) and
  passes after, with both repos' tracked bytes, status and worktree lists
  unchanged. Further tests that failed first: the gated repo's own hook output
  is reported, the tripwire snapshot reads the gated repo, and the sanitiser
  drops/keeps the right variables (with and without git's own list).
- **B2: worktree creation outside the cleanup scope (blocking).** `git worktree
  add` ran before the SIGTERM handler was installed and outside `try/finally`,
  so a signal, timeout or exception during creation skipped cleanup (the child
  git runs in its own session and survives; a registered worktree could leak).
  Fix: the handler is installed first, creation and use share one
  `try/finally`, and cleanup (`_remove_worktree`) removes only what exists,
  always prunes. (An earlier draft said it "never raises"; it catches
  `Exception` only, see the fifth round.) Proof: a subprocess test runs a slow `git
  worktree add` and sends SIGTERM mid-creation; it FAILED before (worktree
  leaked, `sleep` orphan survived) and passes after. A unit test that an
  exception raised right after creation still removes the worktree FAILED
  first. Two further tests (a failing cleanup does not mask the original error;
  the SIGTERM handler is restored) passed before the fix and are
  characterisation tests. Process-signal tests are skipped on Windows.
- **B3: catalog workflow without PyYAML (blocking).** `agent-catalog-update.yml`
  never installed PyYAML, so on a clean runner `build-agent-catalog.py` silently
  used its naive front-matter fallback and wrote degraded data (for example
  `ai-devops-engineer` got an EMPTY description). The previous claim that
  regenerating is "timestamp-only" was true ONLY with PyYAML installed. Fix: the
  workflow now runs `pip install pyyaml` before the generator, the generator
  prints a `WARNING` to stderr when it falls back, and a test covers the warning
  (it FAILED first; a test that the workflow installs PyYAML first also FAILED).
  Proof: in a throwaway worktree under Python 3.9 (the workflow's version) with
  only PyYAML, regeneration differs from the committed files in the two
  `generated` timestamp lines only. Without PyYAML all 160 descriptions differ
  (72 become empty), 8 capability lists differ and 2 names differ
  (`example-security-architect`, `example-python-expert`).
- **B4: documentation.** Commit count (Eight, not Five) and the normalised
  Python file count (64, including the extensionless `mlx-chat`, not 63) were
  corrected in this retrospective and the feature proposal.

## Fourth review round

Codex returned a second **NO-GO** and Opus reviewed the third-round fix; a Haiku
verification run, which happened to overlap an Opus run on the same machine,
found a flaky test. The branch then had nine commits: eight reviewed plus this
fourth-round fix (the fifth-round fix below makes ten).

- **Locked "initializing" worktree (Codex, blocking).** While `git worktree add`
  checks out, git holds a lock on the new registration (reason `initializing`).
  If the gate is terminated then, its process-group cleanup SIGKILLs git, so
  git's own cleanup never runs and the registration stays locked. A single
  `git worktree remove --force` refuses it and `git worktree prune` skips
  locked entries. Codex reasoned this from git's source; it was REPRODUCED here:
  a repo whose new-worktree checkout blocks inside a smudge filter (configured
  after the commit, so only the later checkout is slow) holds the lock
  deterministically. SIGKILL of git leaves `locked` containing `initializing`,
  prune keeps the entry, `remove --force` is refused. Fix: `_remove_worktree`
  tries `remove --force`, then `worktree unlock` and a second remove, then
  deletes the directory and prunes; it also detects a registration whose
  directory is already gone (via `git worktree list --porcelain`). Tests that
  FAILED first: cleanup of a worktree locked as initializing, the same with the
  directory gone, the SIGKILL reproduction (its premises hold on the old code;
  the cleanup assertion fails), and the end-to-end test (SIGTERM to the gate
  during a blocked checkout; the old gate left a locked worktree).
- **Three regressions from the previous fix (Opus).** (1) A second SIGTERM
  during cleanup raised `GateTerminated` out of the `finally` before the
  handler restore, leaking the worktree and leaving the handler installed. Now
  further SIGTERMs were made to `return` from the handler once the first was
  handled or cleanup began (CORRECTION: this was written up as "only set a flag"
  / "recorded", but nothing recorded them: they were DROPPED, which the fifth
  round shows is a regression), and the restore sits in its own nested
  `try/finally`. What was claimed at the time: cleanup does not raise `Exception`; a second signal cannot
  skip the removal or the restore; a `KeyboardInterrupt` can still propagate but
  cannot skip the restore. The test with a second SIGTERM during a slowed
  cleanup FAILED first (handler not restored, worktree leaked); the variant
  with the signals sent back to back passed before the fix (characterisation).
  (2) Cleanup force-removed any existing path, and threads of one process share
  a pid and therefore a path. Each call now uses
  `prepush-gate-<pid>-<8 hex of uuid4>` and cleans up only that path. Tests: unique
  paths and concurrent gate calls in threads FAILED first (a shared path); the
  "failed add does not touch another call's live worktree" test passed before
  (characterisation; the old path never matched its name). (3) A relative
  `repo_root` made `Path.exists()` disagree with git (the worktree was created
  under `target/target/...` and leaked). `repo_root` is now resolved; the test
  FAILED first.
- **Flaky test (Haiku run + Opus).** `test_gate_timeout_fails_removes_worktree_and_
  kills_grandchildren` failed on Python 3.12 (a surviving `sleep 31337`) and
  3.13 (exit -15, no "timed out" message) while other agents ran the same tests.
  Root cause, confirmed: the tests identified processes with host-wide patterns
  (`pgrep -f "sleep 31337"`, `pkill -f "sleep 31337"`), so concurrent runs saw
  and killed each other's processes. Reproduced both symptoms against the old
  test: a `pkill` loop from outside makes the hook die early (hook fails with
  a signal exit and no "timed out"; this is the 3.13 symptom, not a gate bug:
  the timeout path was never reached), and a foreign `sleep 31337` makes the
  "grandchild outlived the gate" assertion fail (the 3.12 symptom). The Haiku
  report called this pre-existing; it was not, the test was added in this PR.
  Fix: every marker process uses a per-invocation unique sleep duration, only
  that token is matched, cleanup in `finally` kills only pids carrying it, the
  timeout test records that the hook actually started, and fixed sleeps became
  polling loops with generous deadlines.
- **Nit.** `sanitized_git_env()` no longer runs `git rev-parse
  --local-env-vars` per command; the list is memoised per process.
- **Proof of reliability.** `tests/test_pre_push_gate.py` (53 tests) was run 20 times
  on each of Python 3.11, 3.12 and 3.13 (60 runs, 0 failures) while three further
  copies of the same file looped on the same machine (183 concurrent runs, 0
  failures), alongside unrelated agents' work. Afterwards no `sleep <digits>`
  process remained and `git worktree list` showed only the main checkout.
- **Not reproduced / limits.** A SIGTERM landing in the few instructions between
  the handler's entry and the flag assignment is not covered (nested handler
  invocations in that window would still raise). A locked registration left by
  an older run is not cleaned by later runs (their paths are unique); it is
  harmless but remains until `git worktree unlock` and prune.

## Fifth review round

Opus reviewed the fourth-round fix and Codex returned a second **NO-GO**. The
branch now has ten commits: nine reviewed plus this fifth-round fix.

- **A swallowed SIGTERM (Opus, verified, serious regression from the previous
  round).** `_ignore_further_sigterm()` muted SIGTERM on the SUCCESS path too and
  nothing recorded or re-delivered it. A SIGTERM arriving during normal cleanup
  (no earlier signal) was dropped: the gate returned True and the script exited
  0, where the pre-fix version terminated. A CI cancel or outer timeout landing
  in that window would have been lost and a push could have gone ahead. The
  earlier statements in this document that further SIGTERMs "only set a flag" and
  were "recorded" were wrong: they were dropped.
- **Module-level flag shared across threads (Opus + Codex, verified).**
  `_sigterm_handled` was process-wide state: a worker thread's gate call
  finishing muted the main thread's SIGTERM (the main gate ran to its timeout and
  exited 0), and a worker could clear it during the main call's cleanup.
- **Unguarded deletion (Opus + Codex, verified).** `_remove_worktree` deleted
  whatever it was given: `_remove_worktree(repo_root)` on a throwaway repo
  deleted the whole checkout including `.git` and returned success. Codex also
  showed that a pre-existing symlink at the chosen path, or a symlinked `tmp`,
  could make git or `rmtree` act on a different worktree or path. Codex's
  concurrency concerns (shared process-wide signal disposition and `tmp/`
  between concurrent calls) are the same root cause as the flag.
- **Design change: mask-based, flag-free handling.** The patched flag design is
  replaced, not patched again. (a) A module-level `threading.Lock` is held for
  the whole of `check_pre_commit_hooks`, so concurrent calls queue. (b) A SIGTERM
  handler is installed only in the main thread on POSIX (`pthread_sigmask`
  available); otherwise nothing is installed. All handler state lives in a
  per-call `_SigtermScope`, none at module level. (c) The handler blocks further
  SIGTERM for the thread (`pthread_sigmask`) before raising `GateTerminated`, so
  a second signal stays pending in the kernel instead of interrupting the
  unwinding. (d) Cleanup runs in a fixed order, each step nested so a failure
  cannot skip a later one: block SIGTERM, kill the hook's process group if still
  running, remove the worktree, restore the PREVIOUS handler, unblock. Because
  the previous handler is back before the unblock, a SIGTERM that arrived at any
  point in cleanup, including a plain one with no earlier signal, is delivered to
  the original disposition afterwards (normally terminating the process). It is
  honoured after cleanup, never dropped. If the caller's own previous disposition
  was `SIG_IGN` it stays ignored, so a pending SIGTERM is then discarded by that
  choice. Installation blocks SIGTERM while swapping the handler, so no signal
  lands between the swap and the bookkeeping.
- **Containment guard on deletion.** Before any `git worktree remove`, `unlock` or
  `rmtree`, `_remove_worktree` requires: the path's real parent equals the real
  `<repo_root>/tmp` (itself not a symlink); the name matches
  `^prepush-gate-\d+-[0-9a-f]{8}$`; the path is not a symlink and is not, or an
  ancestor of, the repo root; and the path is one this runner minted via
  `_gate_worktree_path()`. Otherwise nothing is touched and an error naming the
  path and the failed check is recorded. Creation refuses a symlinked `tmp` (or a
  `tmp` that resolves outside the repo) and a path that already exists, and only
  a path that creation actually claimed is ever removed.
- **Residual window, stated honestly.** A SIGTERM whose Python handler runs after
  the `try` body ends but before the first statement of the `finally` raises
  `GateTerminated` from inside the `finally` before the block is in place, which
  skips that call's cleanup. The cleanup is the first statement of the `finally`
  so this is a single bytecode boundary, but it is not closed. Children spawned
  during cleanup (the git removal commands) inherit the blocked SIGTERM mask. A
  `KeyboardInterrupt` is not handled by this scheme.
- **Tests.** Tests that FAILED first (each run against the old code): SIGTERM
  during normal cleanup is honoured (old: exit 0 and `STILL ALIVE`); a worker
  thread's gate call does not mute the main-thread gate (old: the SIGTERM was
  swallowed and the gate ran on to its timeout); two SIGTERMs separated by a
  confirmed delay still clean up, restore the handler and end the process by
  signal (old: exit 143, second signal dropped); concurrent gate calls serialise
  (old: all three overlapped); and six refusal tests (repo root, a path outside
  `tmp`, a non-matching name, a matching name this call did not choose, a symlink
  at the chosen path, a symlinked `tmp`), each asserting file bytes intact.
  The timeout test's cleanup now re-verifies that a recorded pid still carries
  the unique marker before SIGKILL (a hardening change, not a failing test). The
  `second_sigterm[immediately]` case was removed: two back-to-back SIGTERMs merge
  into one signal, so it could not detect a regression. Three tests that called
  `_remove_worktree` with hand-made paths now use a path the runner minted.

## Process incident: unexplained reset of the working files (fifth round)

While the fifth-round fix agent was running reliability loops against the main
checkout, its four edited files (`tools/validation/local-validation.py`,
`tests/test_pre_push_gate.py`, this retrospective and the feature proposal)
were reset to `HEAD` at 19:54:55 local time. All four files carry the same
modification time to the second and no other file was touched, which is the
signature of one bulk checkout or restore of the modified files rather than of
an editor or of the agent's own writes. The agent had not run such a command;
the stash list was empty and the reflog showed no reset. Several other agents
(reviewers and verification runs) were active in the same repository at the
time, so the cause could not be attributed and is not claimed here.

The work survived because the agent had already committed it in a throwaway
worktree (commit 698cd5b) and saved a patch. It was re-applied to the clean
tree, shown to be byte-identical to the verified commit (an empty diff against
698cd5b), and committed immediately. This is the second time files in this
checkout were reverted under a running agent (the first, Part A reverting
Part B's work, is described above and was attributable).

Lessons recorded for future work: give every parallel agent its own throwaway
worktree for BOTH editing and verification (not just for running hooks);
have agents commit to a throwaway branch early; and treat the main checkout as
read-only for everything except the final integration step.
