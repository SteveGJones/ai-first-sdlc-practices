# Retrospective: KB shelf-index exclusions and bulk-add safety rail

**Branch:** `feature/kb-index-exclusions-241`
**Date:** 2026-10-03
**Tracking Issue:** #241

---

## Summary

Added a `.kb-index-ignore` mechanism, a shared library-file enumeration helper,
and a bulk-add safety rail to the `sdlc-knowledge-base` rebuild, so a vendored
dump under `library/` can no longer silently flood the shelf-index and `log.md`.

## Root cause

`build_shelf_index.py` special-cased exactly one directory name, `raw`, and
recursed over everything else. Any other directory of `.md` files was treated
as curated library content. Worse, the "added" count was written to `log.md`
without any sanity check, so the damage was recorded as if it were a legitimate
ingest. Several modules also each had their own idea of which files count,
which made the exclusion rule easy to get wrong in one place.

## Issue-wording correction

Issue #241 described JSON files being indexed. They never were: the scanner
only globs `*.md`. The `iso20022/` dump must therefore have contained `.md`
files (or had them generated alongside), and that is what was indexed. The fix
is unaffected, but the issue text was wrong about the mechanism and the
proposal states it correctly.

## Decisions and rationale

- **Ignore file over a hard-coded list.** The set of vendored directories is
  per-project, so it belongs in the library, not the plugin.
- **No globs.** Directory-prefix matching covers the observed case and keeps
  semantics trivial to explain and test.
- **Shared helper.** One definition of "which files count", consumed by four
  modules, instead of four copies of an exclusion rule.
- **Safety rail rather than only an ignore file.** The ignore file requires
  the user to know about the problem in advance; the rail catches the next
  unanticipated dump.
- **Refuse both writes.** If the index is refused but `log.md` is still
  appended, the audit trail lies. Neither is written.
- **Agent must not self-override.** The skills say `--force` is used only after
  the user has seen the per-directory breakdown and confirmed.

## Honest caveats

- **The thresholds (50 entries and 2x growth) are judgement calls**, not
  derived from data. They sit comfortably above normal ingest batches seen so
  far and far below the observed incidents, but a legitimately large first
  import into an existing small library will trip the rail. That is the
  intended trade: a confirmation prompt is cheap, a polluted index is not.
  They are not configurable in this change.
- A dump that adds fewer than 50 entries, or lands in a large index, passes
  the rail. The ignore file is the primary defence; the rail is a backstop.
- The rail does not repair an already-polluted index; that needs the ignore
  file plus a `--full` rebuild.
- Symlinked directories: `os.walk(followlinks=False)` and `Path.rglob("*.md")`
  were compared on a fixture (`real/a.md` plus `link -> real`). Tested on Python
  3.8.20, 3.9.6, 3.11.15, 3.12.13, 3.13.14 and 3.14.6: every version returned
  only `real/a.md` from both, i.e. neither descended into the symlinked
  directory. No behaviour difference was found, so no index drop-out is expected
  from the switch. Versions not listed (3.10, 3.15) were not tested and are
  unverified.
- Correction: an earlier draft claimed `rglob` followed symlinked directories on
  Python <= 3.12. That claim was corrected after Codex review and verified
  empirically as above.
- Ignore entries are validated against real directory names (listed, not
  probed with `is_dir()`), because case-insensitive filesystems such as macOS
  APFS report a wrong-case entry as existing while pruning stays case-sensitive.
  A wrong-case entry warns, names the real-cased path, and is NOT applied: the
  directory stays indexed and is not listed under `Excluded:`. Unmatched,
  file, symlink (distinct "not followed, unnecessary" warning) and unreadable
  (distinct "could not read" warning) entries are likewise warned about and
  dropped from the exclusion set.
- The `Excluded:` line names excluded directories rather than counting files,
  so a rebuild never walks raw/ or a vendored dump just to print a number.

## Process notes

- Design was done by Opus; implementation by Sonnet agents working in
  parallel with a separate documentation agent, split by file ownership (code
  and tests versus docs) to avoid conflicts.
- Skill-source discovery: `skills/kb-rebuild-indexes/SKILL.md` is the source
  of truth listed in `release-mapping.yaml`, with
  `plugins/sdlc-knowledge-base/skills/kb-rebuild-indexes/SKILL.md` a packaged
  copy. `kb-ingest-bulk` and `kb-ingest-batch` are authored in the plugin
  directory. Both locations were updated by hand and kept identical.

## Lessons

- A count that gets written to an audit log needs a plausibility check; silent
  success is the dangerous failure mode.
- When several modules need the same filter, give it one home before adding a
  new rule to it.

## Review round

An Opus review of the first implementation found: refusal output omitted
exclusion warnings; case-insensitive filesystems silently accepted wrong-case
entries; the `Excluded:` count walked the whole excluded trees; a UTF-8 BOM
broke the first ignore entry; backslash entries gave a misleading warning; and
the `kb-rebuild-indexes` skill sample and `args` block lagged the real CLI.
All were fixed test-first.

A second review round found that wrong-case, unmatched and symlink entries were
still added to the exclusion set, so `Excluded:` could list directories that
were not pruned on case-insensitive filesystems; symlink and unreadable
directories were also misreported as "matches no directory". Fixed test-first:
only exact, real-cased directory entries are kept, and `Excluded:` derives from
the same exact check.

A third review round found NFC/NFD mismatches on macOS (an NFC-typed entry got
a false "matches no directory" warning and was never applied), a symlink warning
that named the entry rather than the symlinked component (and a wrong-case
symlink component misreported as unmatched), and a sample-spacing error in the
`kb-rebuild-indexes` skill. Fixed test-first; the sample was regenerated from
real CLI output. Finding S1 from that review (`confidence.py`, `kb_config.py` and
`kb_lint_fix.py` call `discover_library_files` without collecting warnings, so
bad ignore entries are dropped silently outside the rebuild) is a deliberate,
recorded follow-up.
