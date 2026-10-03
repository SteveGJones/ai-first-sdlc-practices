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
- The same empty-`**Terms:**` trailing-space pattern exists at
  `plugins/sdlc-knowledge-base/scripts/build_shelf_index.py` (line 279,
  `f"**Terms:** {', '.join(entry.terms)}\n"`). It is NOT fixed here; only the
  `_code-index` generator was.
- The pre-push gate validates HEAD (committed state), not uncommitted edits.
- Four files under `research/` outside the protected corpora were re-wrapped;
  nothing pins a hash of them.

## Verification

Local: workflow YAML parses; actionlint reports only the pre-existing
`github.head_ref` finding (~line 52); the hook run in a throwaway worktree
exits 0 and leaves the worktree clean; the pytest suite passes (903).

Only the PR's own CI can prove: the blocking `Code Quality Analysis` job on
Ubuntu with a cold hook cache (hook environments install from scratch, Python
3.9 for black), the cache step itself, and `Validation Summary` behaviour when
`code-quality` fails.

## Admin

No new admin step beyond the already-noted `Tests (...)` check names. `Code
Quality Analysis` is already a required check and now actually blocks.

## Deviations

None from the approved plan.
