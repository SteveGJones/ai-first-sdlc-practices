---
name: kb-staleness-check
description: Check whether the knowledge base shelf-index is stale relative to the library files. Reports drifted entries without rebuilding. Designed to be invoked from environment validation or pre-push hooks as an opt-in check. Default mode is warning; strict mode fails with non-zero exit when any drift is detected.
disable-model-invocation: true
argument-hint: "[--strict]"
---

# Knowledge Base Staleness Check

Verify that the knowledge base shelf-index reflects the current state of the library files. Reports drifted entries without making changes. Designed as the touch-point between the knowledge base plugin and existing SDLC validation operations.

This is the **opt-in environment validation extension** described in the EPIC. The plugin does not modify the existing `validate` skill in `sdlc-core` directly — instead, this skill is shipped as a standalone check that users can invoke manually or wire into their pre-push validation when they want it.

## Argument

- (no argument) — **warning mode** (default). Reports stale entries; exits 0 regardless. Informational only.
- `--strict` — **strict mode**. Reports stale entries and exits 1 if any drift is found. Use this when wired into pre-push hooks where stale indexes should block the push.

## Preflight

- Verify the knowledge base is configured (the `[Knowledge Base]` section exists in `CLAUDE.md`).
- Verify the shelf-index file exists at the configured path.
- If neither exists, exit 0 silently with a single-line note: "No knowledge base configured; skipping staleness check." This makes the skill safe to wire into pre-push hooks unconditionally — projects without a knowledge base see no impact.

## Steps

### 1. Read the configured paths

Parse the `[Knowledge Base]` section from `CLAUDE.md` for:
- `library_path` (default `library/`)
- `shelf_index_path` (default `library/_shelf-index.md`)

### 2. Compute current hashes

Use the same logic as `kb-rebuild-indexes`:

```bash
find <library_path> -name "*.md" \
  ! -name "_shelf-index.md" \
  ! -name "_index.md" \
  ! -name "log.md" \
  ! -path "<library_path>/raw/*" \
  -exec sha256sum {} \;
```

Build `{file_path → current_hash}`.

### 3. Read recorded hashes from the shelf-index

Parse the shelf-index, extracting each entry's `**Hash:**` field. Build `{file_path → recorded_hash}`.

### 4. Compare and classify

For each file:

| Recorded | Current | Classification |
|---|---|---|
| Missing | Present | **Added** (file exists but no index entry) |
| Present | Missing | **Removed** (index entry but file deleted) |
| Present | Differs | **Modified** (file changed since index) |
| Present | Matches | **Fresh** |

### 5. Report

```
Knowledge base staleness check: <library_path>

  Files in library:    N
  Index entries:       M
  Fresh:               F  ✓
  Modified:            X  (drifted)
  Added:               Y  (not in index)
  Removed:             Z  (deleted from library)

  Shelf-index path:    <path>
  Last regenerated:    <date if available>

Drift detected: X + Y + Z entries
```

If no drift: report "Shelf-index is fresh." and exit 0.

If drift detected:

**Warning mode (default):**
```
Drift detected (warning only). Run /sdlc-core:kb-rebuild-indexes to refresh.
```
Exit 0.

**Strict mode (`--strict`):**
```
Drift detected. Strict mode is enabled — failing.
Run /sdlc-core:kb-rebuild-indexes to refresh, then re-run validation.
```
Exit 1.

### 6. Append to log.md (if present)

```markdown
## [YYYY-MM-DD] staleness-check | drift=<X+Y+Z>

Mode: warning (or strict)
Fresh: F
Modified: X
Added: Y
Removed: Z
```

## How to wire this into pre-push validation

The plugin does not automatically wire itself into `validate --pre-push`. Wiring is opt-in by the user. Two paths:

### Path A: Manual invocation as part of your validation routine

Add to your project's CONTRIBUTING.md or pre-push checklist:

```bash
/sdlc-core:validate --pre-push
/sdlc-core:kb-staleness-check --strict
```

Both must pass before pushing.

### Path B: Custom pre-push hook

If your project uses a git pre-push hook, add the staleness check after the validation pipeline:

```bash
#!/bin/bash
# .git/hooks/pre-push
set -e
# Existing validation
claude /sdlc-core:validate --pre-push
# Knowledge base staleness (opt-in)
claude /sdlc-core:kb-staleness-check --strict
```

### Path C: Composite validation skill

Create a project-specific skill (`skills/my-validate/SKILL.md`) that wraps both:

```markdown
---
name: my-validate
description: Project validation including knowledge base staleness check
---

Run /sdlc-core:validate --pre-push
Then run /sdlc-core:kb-staleness-check --strict
Exit non-zero if either fails.
```

The plugin's job is to provide the staleness check as a standalone tool. The choice of when and how to run it stays with the user.

## What this skill does NOT do

- It does not rebuild the shelf-index — that's `kb-rebuild-indexes`
- It does not modify the existing `validate` skill in sdlc-core
- It does not check anything other than shelf-index drift (no logical checks; that's `kb-lint`)
- It does not validate citations (that's `kb-validate-citations`)
- It does not block on missing knowledge base — exits 0 silently if not configured

## Why this is its own skill rather than a flag on validate

Two reasons:

1. **No cross-plugin coupling.** The `validate` skill lives in `sdlc-core`. Modifying it from `sdlc-knowledge-base` would create a coupling that makes both plugins harder to evolve. A standalone skill that the user wires in keeps the plugins orthogonal.

2. **User retains the wiring decision.** Different projects want different integration points: warning-only, strict-mode, conditional on a config flag, only in CI but not local pre-push. A standalone skill that returns the right exit code lets the user wire it however they want.

The recommendation in the schema template (in CLAUDE.md) tells users this skill exists and how to wire it. The plugin doesn't wire itself.

## Errors

- **No knowledge base configured** — exit 0 with informational note (safe to wire into pre-push unconditionally)
- **Shelf-index missing entirely** — fail with "Shelf-index does not exist at <path>. Run kb-rebuild-indexes first." (this is a different failure than staleness — the index is absent, not stale)
- **Shelf-index is malformed (cannot parse hashes)** — fail with the parse error and recommend rebuilding

## Example

```
/sdlc-core:kb-staleness-check

Knowledge base staleness check: library/

  Files in library:    22
  Index entries:       22
  Fresh:               18  ✓
  Modified:             3  (drifted)
  Added:                1  (not in index)
  Removed:              0  (deleted from library)

  Shelf-index path:    library/_shelf-index.md
  Last regenerated:    2026-04-01

Drift detected: 4 entries
Drift detected (warning only). Run /sdlc-core:kb-rebuild-indexes to refresh.
```

```
/sdlc-core:kb-staleness-check --strict
# (same report, but exit 1 because strict mode and drift detected)
```
