# KB v0.3.0 Phase C — Confidence Metadata + Auto-Fix Design

**EPIC:** #197 — sdlc-knowledge-base v0.3.0 operator experience + scale
**Phase:** C (closes EPIC)
**Closes:** #163 (confidence metadata), #165 (kb-lint auto-fix)
**Branch:** `feature/kb-v030-operator-experience` (continues from Phase B)
**Date:** 2026-05-06

---

## Context

Phase A shipped deterministic index rebuild and agent-only enforcement. Phase B shipped layer tags, batch ingestion, and kb-stats. Phase C adds two quality-of-life features:

- **#163 — Confidence metadata**: two-layer signal (source quality + query relevance) that tells operators how much weight to place on each finding *for a specific question*.
- **#165 — Auto-fix**: pure-Python mechanical repair of missing required frontmatter fields, integrated into `kb-lint --auto-fix`.

These close EPIC #197. The branch is ready for its combined Phase B+C PR after Phase C lands.

---

## #163 — Confidence Metadata

### Core insight

Confidence has two independent dimensions:

1. **Source quality** — how good is the underlying evidence, independent of any question? This is a property of the library file itself, stable across queries.
2. **Query relevance** — how directly does this specific source answer *this specific question*? Computed at query time by the research librarian.

A DORA 2024 study (n=32,000, peer-reviewed) is always high-quality evidence. But if the query is "how do agent-based teams handle context window limits?" and the librarian pulls it because it mentions team topologies, the combined confidence for *that finding in that query* should reflect the oblique connection.

Combined confidence = f(source quality, query relevance) via a deterministic lookup table.

---

### Frontmatter field: `confidence:`

Every library file gains a required frontmatter field:

```yaml
---
title: "..."
domain: ...
layer: methodology
confidence: high       # high | medium | low
status: active
cross_references: [...]
---
```

**Scale:**

| Value | Criteria |
|---|---|
| `high` | Peer-reviewed study; named industry research (DORA, Gartner); large sample size (n≥100); DOI/arXiv traceable |
| `medium` | Industry report without full methodology disclosure; practitioner book with empirical basis; named case study; vendor whitepaper with acknowledged bias flag |
| `low` | Blog post; opinion piece; small study (n<10); undated or unattributed source; vendor marketing |

**Permissive default in tooling**: `build_shelf_index.py` records `"unknown"` when `confidence:` is absent — no rebuild failure. `kb-lint --strict-confidence` enforces the field as an error. Without the flag: warning only.

**Auto-set at ingest**: `agent-knowledge-updater` sets `confidence:` when creating or updating library files, using its existing source-type classification:

| Source type | Confidence |
|---|---|
| Academic paper, peer-reviewed study | `high` |
| Industry research report (DORA, Gartner) | `high` |
| Practitioner book chapter with empirical backing | `medium` |
| Named case study with measurable outcomes | `medium` |
| Vendor whitepaper with acknowledged bias flag | `medium` |
| Blog post with original research and citations | `low` |
| Conversation excerpt / informal source | `low` |

When updating an existing file (adding a new finding), the updater does not downgrade an existing `confidence:` value — it records a note in the file if the new source has lower confidence than the file's current rating.

---

### Shelf-index changes

`build_shelf_index.py` gains:

1. `extract_confidence(frontmatter: dict[str, object]) -> str` — returns `"high"`, `"medium"`, or `"low"` if the field holds one of those exact values (stripped, lowercased). Returns `"unknown"` if absent OR if the value is not one of the three valid values. Confidence has a fixed vocabulary unlike layer (which is user-extensible), so invalid values are normalised to `"unknown"` rather than passed through.
2. `IndexEntry.confidence: str` field (default `"unknown"`).
3. `_render_entry` adds `**Confidence:** {entry.confidence}` between `**Layer:**` and `**Terms:**`.
4. Confidence value appended to the Terms list (so librarian queries on "high confidence" or "low confidence" naturally surface relevant files).
5. `format_version` stays at `1` — backward-compatible addition.

Shelf-index entry format after Phase C:

```markdown
## 1. agent-suitability-rubric.md

**Hash:** <sha256-hex>
**Layer:** methodology
**Confidence:** high
**Terms:** methodology, high, agent, suitability, ...
**Facts:**
- 14-dimension weighted rubric, ...
**Links:** library/agentic-sdlc-options.md
```

---

### Combination table

Lives in `plugins/sdlc-knowledge-base/scripts/confidence.py` as the authoritative constant. The librarian is instructed to apply the same table when computing the combined label.

| Source confidence | Query relevance | Combined |
|---|---|---|
| `high` | `direct` | **`high`** |
| `high` | `supporting` | **`medium`** |
| `high` | `tangential` | **`medium`** |
| `medium` | `direct` | **`medium`** |
| `medium` | `supporting` | **`medium`** |
| `medium` | `tangential` | **`low`** |
| `low` | `direct` | **`low`** |
| `low` | `supporting` | **`low`** |
| `low` | `tangential` | **`low`** |
| `unknown` | `direct` | **`medium`** |
| `unknown` | `supporting` | **`low`** |
| `unknown` | `tangential` | **`low`** |

Relevance definitions (applied by the librarian at query time):
- `direct` — source directly addresses the question asked; findings are on-point
- `supporting` — source addresses a closely related topic or provides context; requires one inferential step
- `tangential` — source has peripheral connection; useful as background but not as primary evidence

---

### `confidence.py` — new module

```
plugins/sdlc-knowledge-base/scripts/confidence.py
```

Public interface:

- `COMBINATION_TABLE: dict[tuple[str, str], str]` — the authoritative lookup (source_confidence, query_relevance) → combined
- `combine_confidence(source: str, relevance: str) -> str` — looks up the table; returns `"low"` for unknown inputs as a safe fallback
- `parse_finding_confidence(text: str) -> tuple[str, str, str]` — extracts `(source_confidence, query_relevance, combined)` from a finding block string; returns `("unknown", "unknown", "unknown")` if tags are absent
- `check_confidence_compliance(library_path: Path) -> list[tuple[str, str]]` — scans library .md files (same exclusions as `kb_config.check_layer_compliance`), returns `(rel_path, error_msg)` for files missing `confidence:` frontmatter
- `main(args=None) -> int` — CLI for direct invocation; reports compliance like `kb_config.main`

---

### Research-librarian agent changes

Three new structured lines added to every retrieval finding block:

```
**Source confidence:** high
**Query relevance:** direct
**Confidence:** high
```

Positioned after `**Source library:**` and before `**Finding:**`. The librarian:

1. Reads `**Confidence:**` from the shelf-index entry to get the source quality.
2. Assesses query relevance using the definitions above.
3. Looks up the combination table to compute the combined label.
4. Emits all three tags in the finding block.
5. Explains relevance judgment in the existing `**Caveats:**` line when relevance is `supporting` or `tangential` — no new prose section added.

When the shelf-index entry has no `**Confidence:**` field (pre-Phase-C libraries), the librarian uses `unknown` as the source confidence.

---

### `kb-lint` — `--strict-confidence` flag

Symmetric with `--strict-layer` from Phase B:

- Without flag: missing `confidence:` values are warnings in the Lint report.
- With flag: missing `confidence:` → error, non-zero exit.
- This repo's CI runs `--strict-confidence` (alongside `--strict-layer`) against the starter-pack library.

The Layer Compliance check (Step 0 of kb-lint) is extended to also run confidence compliance using `confidence.check_confidence_compliance()`. The combined Step 0 checks both layer and confidence in one pass.

The CI job in `validation.yml` that runs `check_layer_compliance` is updated to also call `check_confidence_compliance` in the same step.

---

### `kb-stats` — Confidence distribution

The Inventory section gains two new lines:

```markdown
## Inventory
- Total files: 47
- Total findings: 183
- Files lacking layer tag: 0
- Files lacking confidence tag: 3
- Files lacking cross-references (orphans): 2
```

The Distribution by layer section is joined by a new Distribution by confidence section:

```markdown
## Distribution by confidence
| Confidence | Files |
|---|---|
| high | 22 |
| medium | 18 |
| low | 4 |
| unknown | 3 |
```

---

### Starter-pack backfill

All three starter-pack library files are research from the Agentic SDLC research programme — peer-reviewed quality. They get `confidence: high`.

The starter-pack `_shelf-index.md` entries get `**Confidence:** high`.

---

## #165 — kb-lint Auto-Fix

### `kb_lint_fix.py` — new script

Pure Python. No LLM invocation. Follows the `build_shelf_index.py` pattern (importable module + `main()` CLI).

```
plugins/sdlc-knowledge-base/scripts/kb_lint_fix.py
```

**Scope: mechanical-only.** Fixes structural frontmatter defects that require no judgment — a missing required key gets a safe default value. Does not attempt to repair contradiction findings, stale claims, or orphan files.

Three fixes applied in a single pass over library files (excluding `_shelf-index.md`, `log.md`, `_index.md`, `raw/`):

| Missing field | Value added |
|---|---|
| `layer:` | `layer: uncategorized` |
| `confidence:` | `confidence: medium` |
| `cross_references:` | `cross_references: []` |

**Insertion position**: new fields are appended at the end of the existing frontmatter block (before the closing `---`), preserving all existing fields and body content exactly. Atomic write (`.tmp` + rename).

**Files without parseable frontmatter** (no `---` delimiters, or malformed YAML): the script inserts a stub frontmatter block at the top of the file. The stub uses the filename (hyphen/underscore → spaces, title-cased) as the title, `domain: unknown`, and `confidence: low` — low because no source metadata exists to calibrate from. The fix output reports the stub creation and explains why confidence is `low`:

```
Fixed library/unfronted-file.md:
  + stub frontmatter created (no existing frontmatter found)
    title: Unfronted File  (derived from filename — please update)
    domain: unknown        (please update)
    layer: uncategorized
    confidence: low        (no source metadata; update after reviewing source quality)
    status: draft
    cross_references: []
```

`status: draft` (not `active`) signals the file needs human review before it is treated as curated library content.

**`--dry-run`**: reports what would be changed without writing. Output format:
```
Would fix library/old-file.md:
  + layer: uncategorized
  + confidence: medium

Would fix library/another-file.md:
  + cross_references: []

Total: 2 files would be modified, 3 fields would be added.
```

**Public interface:**

```python
@dataclass
class FixResult:
    files_fixed: int = 0
    fields_added: int = 0
    files_skipped: int = 0
    errors: list[str]   # field(default_factory=list)

def fix_missing_fields(
    library_path: Path,
    dry_run: bool = False,
) -> FixResult: ...

def main(args: list[str] | None = None) -> int: ...
```

CLI flags: `<library_path>` (positional), `--dry-run`.

---

### `kb-lint` — `--auto-fix` flag

When `--auto-fix` is passed:

1. **Run `kb_lint_fix.py`** over the library path. Report what was fixed (or "nothing to fix").
2. **Run `kb-rebuild-indexes`** — the patched files have new content; the shelf-index must reflect them.
3. **Proceed with normal lint** (Step 0 layer+confidence check, then Steps 1–6 via the librarian).

The `--auto-fix` flag can be combined with `--strict-layer`, `--strict-confidence`, and `--scope`:

```
/sdlc-knowledge-base:kb-lint --auto-fix --strict-layer --strict-confidence
```

This single command: patches mechanical issues → rebuilds index → enforces layer + confidence compliance → runs full LLM lint report.

**No `--dry-run` on the skill** — the `--dry-run` behaviour is available by invoking `kb_lint_fix.py` directly. The `--auto-fix` skill flag is an intentional write operation.

---

## Cross-Cutting Changes

### `CLAUDE-CONTEXT-knowledge-base.md` updates

1. Add `confidence:` to the frontmatter schema documentation.
2. Add `**Confidence:**` to the shelf-index format Fields table.
3. Extend the "Layer Classification" section with a "Confidence Classification" subsection documenting the three values and auto-set-at-ingest behaviour.
4. Add a note about the two-dimensional confidence model (source quality × query relevance) in the "Query" operation description.
5. Add `--auto-fix` and `--strict-confidence` to the kb-lint routing table row.

### `release-mapping.yaml` updates

Add under `sdlc-knowledge-base:` scripts block:
- `plugins/sdlc-knowledge-base/scripts/confidence.py`
- `plugins/sdlc-knowledge-base/scripts/kb_lint_fix.py`

No new skills — both features extend existing skills (`kb-lint`) or are invisible to users (`confidence.py` is an internal module).

### CI changes (`validation.yml`)

The existing `kb-layer-compliance` job is extended to also check confidence compliance:

```python
from sdlc_knowledge_base_scripts.confidence import check_confidence_compliance
conf_violations = check_confidence_compliance(library_path)
if conf_violations:
    # exit 1
```

The job is renamed to `kb-compliance` to reflect its broader scope.

---

## File Map

> **Important**: For files that have a root source (skills/, agents/) AND a plugin-dir copy (plugins/sdlc-knowledge-base/), edit the ROOT SOURCE only. Run `/sdlc-core:release-plugin` after to sync plugin directories. The file map lists root sources for such files.

| Action | Path | Purpose |
|---|---|---|
| Create | `plugins/sdlc-knowledge-base/scripts/confidence.py` | Combination table, parse helpers, compliance checker |
| Create | `tests/test_kb_confidence.py` | Unit tests for confidence module |
| Modify | `plugins/sdlc-knowledge-base/scripts/build_shelf_index.py` | `extract_confidence`, `IndexEntry.confidence`, render `**Confidence:**` |
| Modify | `tests/test_kb_build_shelf_index.py` | Confidence extraction + rendering tests |
| Modify | `plugins/sdlc-knowledge-base/agents/agent-knowledge-updater.md` | Add confidence-setting instructions + source-type table |
| Modify | `agents/knowledge-base/agent-knowledge-updater.md` | Root source (same change) |
| Modify | `plugins/sdlc-knowledge-base/agents/research-librarian.md` | Add confidence tag instructions + combination table |
| Modify | `agents/knowledge-base/research-librarian.md` | Root source (same change) |
| Modify | `plugins/sdlc-knowledge-base/scripts/kb_stats.py` | Add confidence distribution section |
| Modify | `tests/test_kb_stats.py` | Test confidence distribution in stats output |
| Modify | `plugins/sdlc-knowledge-base/skills/kb-lint/SKILL.md` | Add `--strict-confidence` and `--auto-fix` flags |
| Modify | `skills/kb-lint/SKILL.md` | Root source (same change) |
| Create | `plugins/sdlc-knowledge-base/scripts/kb_lint_fix.py` | Mechanical frontmatter auto-fix |
| Create | `tests/test_kb_lint_fix.py` | Tests for auto-fix (dry-run + write modes) |
| Modify | `plugins/sdlc-knowledge-base/skills/kb-init/templates/starter-pack/library/agent-suitability-rubric.md` | Backfill `confidence: high` |
| Modify | `plugins/sdlc-knowledge-base/skills/kb-init/templates/starter-pack/library/agentic-sdlc-options.md` | Backfill `confidence: high` |
| Modify | `plugins/sdlc-knowledge-base/skills/kb-init/templates/starter-pack/library/specification-formality-and-agent-performance.md` | Backfill `confidence: high` |
| Modify | `plugins/sdlc-knowledge-base/skills/kb-init/templates/starter-pack/library/_shelf-index.md` | Add `**Confidence:**` to all 3 entries |
| Modify | `skills/kb-init/templates/starter-pack/library/` (root sources) | Same changes |
| Modify | `CLAUDE-CONTEXT-knowledge-base.md` | Document confidence field, auto-fix |
| Modify | `release-mapping.yaml` | Register confidence.py, kb_lint_fix.py |
| Modify | `.github/workflows/validation.yml` | Extend kb-compliance job with confidence check; rename job |

---

## Acceptance Criteria

| AC | Test |
|---|---|
| `extract_confidence()` returns `high/medium/low` for valid values, `unknown` for missing | Unit test on `extract_confidence` |
| Missing `confidence:` produces `unknown` in shelf-index, no rebuild failure | Integration test on `rebuild_shelf_index` |
| `IndexEntry.confidence` field present with default `"unknown"` | Unit test |
| `**Confidence:**` appears in shelf-index entry between `**Layer:**` and `**Terms:**` | Integration test on rendered output |
| `confidence` value appears in Terms list | Unit test on `extract_terms` |
| `combine_confidence("high", "direct") == "high"` | Unit tests for all 12 table entries |
| `combine_confidence` returns `"low"` for unrecognised inputs (safe fallback) | Unit test |
| `check_confidence_compliance` returns violations for missing field, empty for all valid | Integration test |
| `kb-lint --strict-confidence` exits non-zero when any file lacks `confidence:` | Integration test with fixture library |
| `kb-stats` output includes "Distribution by confidence" section | Integration test |
| `kb-stats` Inventory includes "Files lacking confidence tag" count | Integration test |
| Starter-pack files have valid `confidence:` values | Self-test in CI |
| `fix_missing_fields` adds `layer: uncategorized` to files missing `layer:` | Integration test |
| `fix_missing_fields` adds `confidence: medium` to files missing `confidence:` | Integration test |
| `fix_missing_fields` adds `cross_references: []` to files missing `cross_references:` | Integration test |
| `fix_missing_fields --dry-run` reports changes without writing | Integration test (check file unchanged) |
| `fix_missing_fields` preserves all existing frontmatter fields and body content | Integration test |
| `fix_missing_fields` writes atomically (no `.tmp` file left on success) | Integration test |
| `fix_missing_fields` creates stub frontmatter for files with no frontmatter at all | Integration test |
| Stub frontmatter has `confidence: low` and `status: draft` | Integration test |
| Stub title is derived from filename (hyphen→space, title-cased) | Unit test on title derivation |
| `kb-lint --auto-fix` runs fix script, then rebuilds index, then runs lint | Skill integration (SKILL.md review) |
| `kb-lint --auto-fix --strict-confidence` fails after fix if confidence still missing | Integration test |
| CI `kb-compliance` job fails if starter-pack files lack `confidence:` | Dogfood gate |

Test additions: ~40–50 new tests across `test_kb_confidence.py` (new), `test_kb_lint_fix.py` (new), `test_kb_build_shelf_index.py` (confidence extensions), `test_kb_stats.py` (confidence distribution).

---

## Out of Scope (deferred)

- **Confidence on cross-library query results** — external libraries may not have `confidence:` fields. The librarian uses `unknown` for their entries; no special handling needed beyond what's already designed.
- **Confidence trend over time** — point-in-time only; tracking confidence drift across ingestion events is v0.4.0.
- **Auto-fix for LLM-identified cross-references** — Check 4 (missing cross-references) findings come from the LLM lint run. Auto-applying those additions requires post-processing the lint report, which is judgment-adjacent. Out of scope for #165's mechanical-only charter.
- **Confidence override at query time by operator** — operators can update `confidence:` in frontmatter manually; no query-time override mechanism.
- **`--strict-confidence` in user-installed libraries** — users opt in; this repo's CI enforces it on the starter-pack only.
