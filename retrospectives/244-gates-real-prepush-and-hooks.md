# Retrospective: Make the pre-push and pre-commit gates real (#244)

**Branch:** `feature/gates-real-244`
**Date:** 2026-10-03
**Tracking Issue:** #244

---

## Summary

Five commits make the repository's hooks passable, stop `--pre-push` from
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
4. 109-file mechanical normalisation (`7404153`): 63 Python files AST-identical
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
