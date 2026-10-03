# Feature Proposal: KB shelf-index exclusions and bulk-add safety rail

**Proposal Number:** 241
**Status:** Draft
**Author:** Claude (Opus design, Sonnet implementation) + Steve Jones
**Created:** 2026-10-03
**Target Branch:** `feature/kb-index-exclusions-241`
**Tracking Issue:** #241
**Plugin:** `sdlc-knowledge-base`

---

## Problem Statement

`build_shelf_index.py` excluded only a top-level directory named `raw`. Any
other directory under `library/` holding `.md` files, such as a vendored dump
(`library/iso20022/`), was recursively indexed. The result was a ballooning
`_shelf-index.md` and a bogus "N added" line appended to `log.md`. It was
silent, and it happened twice.

## Motivation

The shelf-index is read by the librarian on every query. Polluting it with
hundreds of non-curated files degrades retrieval, inflates context cost, and
corrupts the audit trail in `log.md`. The failure gave no signal at the time it
occurred, so it was only noticed afterwards.

## Proposed Solution

1. **Shared helper** `plugins/sdlc-knowledge-base/scripts/library_files.py`
   that owns "which files in a library count", used by `build_shelf_index`,
   `confidence`, `kb_lint_fix` and `kb_config` so they cannot disagree.
2. **`.kb-index-ignore`** at the library root: one library-relative directory
   per line, optional trailing `/`, `#` comments and blank lines ignored, no
   globs. A path matches that directory and everything under it. `raw` is
   always excluded. `..` and absolute entries are rejected; entries that match
   nothing warn.
3. **Safety rail** in the rebuild: if a run adds >= 50 entries and the index
   would grow >= 2x, refuse to write `_shelf-index.md` and `log.md`, exit with
   code 2, and name the responsible top-level directories (for example
   `iso20022/: 412 added`). A first build with no or an empty index is exempt.
   Overridable with `--force`.
4. **CLI**: new `--force` and `--dry-run` flags; Successful runs and
   `--dry-run` print `Scanned:` and `Excluded:` breakdown lines; a safety-rail
   refusal (including a `--dry-run` that would be refused) instead prints the
   per-directory "added" breakdown. `Excluded:` names only the directories
   that are genuinely excluded (exact-case, existing, non-symlink entries,
   compared in Unicode NFC so macOS NFD names match, plus built-in `raw/`); wrong-case, unmatched, symlink, file and
   unreadable entries are warned about and NOT excluded.
5. **Skill docs**: `kb-rebuild-indexes`, `kb-ingest-bulk` and `kb-ingest-batch`
   document the ignore file and the exit-code-2 refusal. On a refusal the agent
   must show the per-directory breakdown to the user and re-run with `--force`
   only after the user confirms, never automatically.

## Success Criteria

- A directory listed in `.kb-index-ignore` contributes no entries to the index
  or to the added count.
- A run that adds >= 50 entries and grows the index >= 2x exits 2 and writes
  neither `_shelf-index.md` nor `log.md`; `--force` overrides it.
- A first build is not blocked by the rail.
- `--dry-run` writes nothing.
- All four consumers use the shared helper and agree on the file set.
- Skill docs and the plugin copy of `kb-rebuild-indexes` are in sync with the
  `skills/` source; all validators pass with zero technical debt.

## Out of Scope

- Glob or negation patterns in `.kb-index-ignore`.
- Making the 50 / 2x thresholds configurable.
- Cleaning up indexes already polluted by earlier runs (rebuild with `--full`
  after adding the ignore file).
