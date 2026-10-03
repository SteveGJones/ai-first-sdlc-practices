# Retrospective: kb-query resolves the relative local library path

**Branch:** `feature/kb-query-relative-path-212`
**Date:** 2026-10-03
**Tracking Issue:** #212

---

## Summary

kb-query silently skipped the project's local library because it passed a
relative `Path('library')` to a registry that requires absolute paths. The
resolver now normalises the path, the skill passes a resolved path, and a
rejected local library is reported to the user instead of being reduced to the
generic kb-init message. `sdlc-knowledge-base` is bumped to 0.3.2.

## Root cause

`validate_library_path` rejects relative paths (deliberately; it is a security
check). The only caller that passed a relative path was the kb-query skill
snippet, and the resulting "must be absolute" warning went to stderr while the
user saw only "No knowledge base available". No other caller has this bug.

## Reproduction evidence

An Opus reproduction showed that with a valid `library/_shelf-index.md` the
helper returned `sources: []`, the warning
`Local library: path 'library' must be absolute; skipping.` and
`is_empty_error: true`. `Path('library').resolve()` worked.

## Decisions and rationale

- **Fix in the resolver and the skill.** The resolver uses `absolute()` so the
  bug cannot recur for other callers; the skill also passes `.resolve()`.
- **`absolute()` not `resolve()` in the registry.** `absolute()` keeps the
  stored `local.path` in the form the user would recognise (unresolved but
  absolute), while `validate_library_path` still performs the strict symlink
  resolution and denylist check. This is a presentation choice, NOT a security
  invariant: `resolve()` is idempotent and `validate_library_path` resolves
  again, so resolving early would be equally safe (the skill itself calls
  `Path('library').resolve()`).
- **`validate_library_path` untouched**, including
  `test_validate_library_path_not_absolute`.
- **#209 kept separate** to keep this a small, reviewable patch.
- **Surface local-library warnings** so a rejected-but-present library is not
  misdiagnosed as a missing one. The skill also surfaces `Source '` and
  `Activated source '` rejection warnings, so a stale activation with no
  `library/` no longer gets the kb-init hint because the real cause is shown.

## Known limits (not changed)

- `Path('library')` resolves against the process cwd and nothing discovers the
  project root. If cwd is a subdirectory with no `library/`, the local library
  is reported missing (the user sees the `kb-init` advice although a library
  exists higher up). If cwd is NOT the project root but happens to contain a
  valid `library/`, THAT library is selected. This is pre-existing, not
  introduced by this change (the same step reads `.sdlc/libraries.json`
  relative to cwd; step 2 uses `project_dir=Path('.')`).
- An accepted local source stores the unresolved absolute path (which may
  contain `..`) rather than the validated resolved path. This is a small
  check-then-use gap that external sources already share.
- External-source rejections on an empty result split in two. (i) Loader
  warnings (`Global registry:`, `Project activation:`, `Library ...`) can still
  lead to the misleading `kb-init` text; pre-existing, possibly #209 territory
  (unverified). (ii) Dispatch rejections (`Source '...'`, `Activated source
  '...'`) are already surfaced by the new skill instruction.

## Tests and evidence

Tests were written first and run against the unfixed code. All four failed
before the change:

- `test_resolve_relative_local_library_is_normalised`
- `test_resolve_relative_local_library_symlink_to_denylist_rejected`
- `test_resolve_relative_local_library_without_shelf_index_rejected`
- `test_kb_query_skill_resolves_library_path_and_mirror_matches`

The latter two guard behaviour that must stay; they failed on unfixed code only
because the old message was "must be absolute" (tests 2 and 3) and the skill
lacked `.resolve()` (test 4). The regression test (1) is the one that
demonstrates the bug itself.

## Honest caveats

- CI has no pytest step, so the test evidence is local only.
- The skill-text contract test checks for strings, not for the behaviour of an
  LLM following the skill; the "show the Local library warning" instruction is
  not executed by any test.
- The two-copy skill layout (root source, generated plugin mirror) was updated
  by copying the root file over the mirror and confirming with `diff`.

## Deviations

None from the approved design. The optional new `DispatchList` field was
skipped as agreed.
