# KB v0.3.0 Phase B — Operator Features Design

**EPIC:** #197 — sdlc-knowledge-base v0.3.0 operator experience + scale
**Phase:** B (operator features)
**Closes:** #154 (layer tags), #161 (batch ingestion), #162 (kb-stats)
**Branch:** `feature/kb-v030-operator-experience` (continues from Phase A)
**Date:** 2026-05-03

---

## Context

Phase A shipped the deterministic index rebuild (`build_shelf_index.py`) and agent-only enforcement guardrails. Phase B builds three operator-facing features on top of that foundation:

- **Layer classification tags** so library files are categorised, lintable, and reportable.
- **Batch ingestion** so operators can process tens-to-hundreds of source documents without one-by-one tedium, with format conversion and resume support.
- **kb-stats dashboard** so operators get a one-shot view of library health without writing custom queries against the shelf-index.

These three features are independent enough to build in any order but ship as a single Phase B PR (continuing the EPIC branch model — no PR until the EPIC is complete; the Phase A PR #198 is the exception we accepted).

---

## #154 — Layer Classification Tags

### Schema

A new **required** frontmatter field in library files:

```yaml
---
title: ...
domain: ...
layer: methodology   # default set: methodology | evidence | domain | development
status: active
cross_references: [...]
---
```

The default set, used when the project has not declared its own:

| Layer | Meaning |
|---|---|
| `methodology` | How-we-work files: process frameworks, decision rules, rubrics, methodology comparisons |
| `evidence` | Empirical findings: studies, reports, citations, quantified thresholds |
| `domain` | Subject-matter context: regulatory frameworks, industry vocabulary, problem-space description |
| `development` | Engineering knowledge: architectural patterns, code-level practices, tooling |

### Project-configurable layer set

Projects override or extend the default by declaring `layers:` in the `[Knowledge Base]` section of `CLAUDE.md`:

```markdown
## Knowledge Base

library_path: library/
shelf_index_path: library/_shelf-index.md
layers:
  - methodology
  - evidence
  - domain
  - development
  - regulatory          # custom
  - clinical-evidence   # custom
```

Rules:
- **Absent `layers:`** — the four defaults are the allowed set.
- **Present `layers:`** — the listed values are the **complete** allowed set (replace, not extend). Projects that want to keep the defaults must list them explicitly. This keeps semantics simple: there's exactly one source of truth for the project's layer vocabulary.
- Each value must match `^[a-z][a-z0-9-]*$` (lowercase, hyphenated). Invalid entries in the config trigger a kb-lint error.
- The framework's own `CLAUDE.md` does **not** declare `layers:` — the four defaults stand, and CI runs `kb-lint --strict-layer` against them.

A small helper module (`plugins/sdlc-knowledge-base/scripts/kb_config.py` — or extend an existing config-reading utility) parses `[Knowledge Base]` and exposes `allowed_layers(project_dir: Path) -> list[str]`. This is consumed by `kb-lint`. `build_shelf_index.py` does **not** read the config — it stays permissive.

### Lenient default in tooling, strict via opt-in

`build_shelf_index.py` is permissive: when `layer` is missing or has an invalid value, it records `layer: uncategorized` in the shelf-index entry and continues. The rebuild path does not fail.

`kb-lint` gains a `--strict-layer` flag that turns missing/invalid `layer` values into a lint failure (non-zero exit). Without the flag, lint reports them as warnings only.

This repo's CI runs `kb-lint --strict-layer`, enforcing the rule for the framework's own library. User-installed libraries default to lenient mode and adopt strict opt-in when they're ready.

### Shelf-index entry format change

The shelf-index entry gains a dedicated `**Layer:**` field, positioned between `**Hash:**` and `**Terms:**`. The layer value is also folded into the `Terms:` list so librarian queries naturally match it.

```markdown
## 1. agent-suitability-rubric.md

**Hash:** <sha256-hex>
**Layer:** methodology
**Terms:** methodology, agent, suitability, rubric, sdlc, ...
**Facts:**
- 14-dimension rubric, top 4 dimensions account for 35% of weight
- ...
**Links:** library/agentic-sdlc-options.md
```

`format_version` stays at `1` — this is a backward-compatible addition. `parse_existing_index` continues to read only the path → hash mapping it needs, ignoring the new field.

### Backfill

The three starter-pack library files in `plugins/sdlc-knowledge-base/skills/kb-init/templates/starter-pack/library/` get explicit `layer:` values:

| File | Layer |
|---|---|
| `agent-suitability-rubric.md` | methodology |
| `agentic-sdlc-options.md` | methodology |
| `specification-formality-and-agent-performance.md` | evidence |

The starter-pack `_shelf-index.md` placeholder gets a one-time rebuild (or is left for kb-rebuild-indexes to refresh on first install).

---

## #161 — Batch Ingestion

Two new skills implementing a clean staging-then-ingestion pipeline:

### `kb-prepare-batch` — staging + format conversion

```
/sdlc-knowledge-base:kb-prepare-batch [--copy|--move] [--from sources.txt | files...] [--force-pandoc] [--force-markitdown] [--overwrite]
```

**Purpose:** stage source files into `library/raw/`, converting non-markdown formats to markdown along the way. Does not invoke any agent; pure file-system + CLI shellout work.

**Modes:**
- `--copy` (default): leaves source files in place, copies into raw/
- `--move`: moves source files into raw/ (deletes from origin)
- Default mode is configurable via `default_prepare_mode: copy|move` in the `[Knowledge Base]` section of `CLAUDE.md`

**Inputs:**
- xargs-style positional args: `kb-prepare-batch *.md *.pdf`
- Manifest file: `kb-prepare-batch --from sources.txt` (one path or URL per line)
- Both forms can be combined

**Format routing:**

| Input extension | Converter |
|---|---|
| `.md` | Pass-through (just stage, no conversion) |
| `.pdf`, `.docx`, `.pptx`, `.xlsx`, `.html`, `.csv` | `markitdown` CLI |
| `.tex`, `.epub`, `.rst`, `.org` | `pandoc` CLI |
| Anything else | Reported as preflight error per file; the rest of the batch continues |

`--force-pandoc` / `--force-markitdown` override the routing for the entire invocation.

**Output filename:** `library/raw/<basename>.md` with extension swapped. `--overwrite` allows re-conversion of already-staged files; default refuses overwrite to protect existing work.

**Provenance frontmatter** added to every converted file:

```markdown
---
source: ~/Downloads/dora-2024-report.pdf
converted_by: markitdown
converted_at: 2026-05-03T10:00:00Z
status: raw
---

<converted body>
```

The `status: raw` field signals that this is a staged source, not a curated library file — `agent-knowledge-updater` recognises it and produces the curated version on ingest.

**Preflight checks:**
- Both `markitdown` and `pandoc` CLIs are checked at start
- If neither is available: refuse non-`.md` inputs with install hint (`pip install markitdown` / `brew install pandoc`)
- If only one is available: the unavailable converter's formats fail per-file; other formats proceed

**Reporting:** prints a summary of staged / converted / skipped / failed files, with per-file reasons for failures.

### `kb-ingest-batch` — ingestion with resume

```
/sdlc-knowledge-base:kb-ingest-batch [<dir-or-manifest>] [--parallel <N>] [--retry-failed]
```

**Purpose:** drive `agent-knowledge-updater` over a batch of staged files. Wraps the existing per-file ingest flow with progress tracking, resume support, and a final shelf-index rebuild.

**Inputs:**
- No argument: process everything in `library/raw/` that has `status: raw` provenance
- Directory path: process every `.md` file in that directory
- Manifest file path: process the paths listed in the manifest

**Resume manifest** at `library/raw/.batch-progress.json`:

```json
{
  "started_at": "2026-05-03T10:00:00Z",
  "total": 47,
  "completed": [
    {"path": "library/raw/dora-2024.md",
     "completed_at": "2026-05-03T10:02:15Z",
     "status": "ingested"}
  ],
  "failed": [
    {"path": "library/raw/broken.md",
     "error": "malformed YAML frontmatter at line 3",
     "attempted_at": "2026-05-03T10:05:00Z"}
  ],
  "pending": ["library/raw/forsgren-update.md", "..."]
}
```

On re-invocation:
1. If `.batch-progress.json` exists: load it, treat `completed` files as done, append any new files in raw/ to `pending`.
2. Without `--retry-failed`: leave `failed` files alone (operator must inspect manually).
3. With `--retry-failed`: move `failed` entries back to `pending`.
4. Process `pending` to completion, updating the manifest after each file.

The manifest is written atomically (write to `.batch-progress.json.tmp`, rename on success) so a crash mid-batch leaves the manifest valid.

**Sequential vs parallel:**
- Default: process one file at a time. Each `agent-knowledge-updater` dispatch sees one source, completes, then the next is dispatched. Safe — no shared-state races.
- `--parallel <N>`: dispatch up to N agents concurrently using the parallel-tool-call pattern from `kb-query`.

**Batch-mode-create-only constraint** (applied to all dispatches in a batch, sequential or parallel):

The dispatch prompt to `agent-knowledge-updater` includes a new directive: `BATCH_MODE: create-only`. In this mode the agent:
1. Does not modify existing library files. If the source touches an existing file, the agent records the conflict and exits with `status: conflict-existing-file` rather than performing the update.
2. Does not run `kb-rebuild-indexes`. The shelf-index rebuild is deferred to the batch driver.
3. Does not append to `log.md` per file. The batch driver writes one consolidated entry at the end.

This makes parallel dispatch safe (no concurrent writes to `_shelf-index.md` or `log.md`) and keeps the batch's effects easy to audit. Conflicts surface in the failed list with a clear reason; operators can run individual `kb-ingest` calls for those files later.

**Final phase** (after all dispatches finish):
1. Run `build_shelf_index.py` once to rebuild the shelf-index from the updated library.
2. Append a single batch summary entry to `log.md`: `## [YYYY-MM-DD] ingest-batch | <total>/<succeeded>/<failed>`.
3. Print a markdown summary table of the run.

### Agent change: BATCH_MODE in agent-knowledge-updater

The existing `agent-knowledge-updater.md` agent prompt gains one new section documenting the `BATCH_MODE: create-only` directive and the three behaviours it triggers (no existing-file modification, no shelf-index rebuild, no log append). The agent's tools (Read/Write/Edit/Glob/Grep/Bash/WebFetch) are unchanged — the constraint is enforced by prompt discipline, with the test that conflict cases produce a recognisable status string.

---

## #162 — kb-stats Dashboard

A single command that surfaces library health metrics in markdown.

### Implementation

Pure Python script `plugins/sdlc-knowledge-base/scripts/kb_stats.py`, mirroring the `build_shelf_index.py` pattern: importable as a module, callable via `main()`, no LLM. The skill `kb-stats` is a thin Bash wrapper that resolves config, invokes the script, and surfaces output.

**Inputs read by the script:**
- `library/_shelf-index.md` (for inventory and per-file metadata)
- `library/log.md` (for recent activity)
- `library/` directory listing (for orphan / staleness checks)

**Output structure:**

```markdown
# Knowledge Base Statistics

Generated: 2026-05-03T10:00:00Z
Library: local (library/)

## Inventory
- Total files: 47
- Total findings: 183
- Files lacking layer tag: 3
- Files lacking cross-references (orphans): 2

## Distribution by layer
| Layer | Files | Findings | Avg findings/file |
|---|---|---|---|
| methodology  | 15 | 62 | 4.1 |
| evidence     | 22 | 98 | 4.5 |
| domain       |  7 | 18 | 2.6 |
| development  |  3 |  5 | 1.7 |
| uncategorized|  0 |  0 | -   |

## Distribution by domain
| Domain | Files |
|---|---|
| sdlc | 12 |
| testing | 8 |
| ... | ... |

## Recent activity (last 30 days from log.md)
| Date | Operation | Subject |
|---|---|---|
| 2026-05-01 | ingest | dora-2024-update.md |
| 2026-04-28 | rebuild-indexes | 22/3/1/0 |

## Staleness
- Shelf-index last rebuilt: 2026-05-01T08:00:00Z (2 days ago)
- Files modified since last rebuild: 0
- Status: ✅ fresh
```

**Flags:**
- `--output <path>`: write to a file instead of stdout
- `--since <ISO-date>`: override the recent-activity window (default: 30 days)

**Read-only:** kb-stats never modifies the library, the shelf-index, or log.md.

### What kb-stats does NOT do

- Does not validate citations (that's `kb-validate-citations`)
- Does not detect contradictions or orphans deeply (that's `kb-lint`)
- Does not query findings (that's `kb-query`)
- Does not invoke any agent — pure script execution

### Skill guardrail

Per the agent-only enforcement context module, kb-stats falls into the **lightweight** category:

> **Lightweight**: This skill reads only index metadata (shelf-index + log.md). Inline execution is acceptable.

---

## Cross-cutting changes

### `build_shelf_index.py` updates

1. `extract_layer(frontmatter: dict) -> str` — new function returning the `layer` value as a stripped lowercase string if present, else `"uncategorized"`. **Does not validate against any allowed set** — that's kb-lint's job. The rebuild path stays permissive so the index can always be built regardless of layer-config drift.
2. `IndexEntry` dataclass gains `layer: str` field.
3. `_render_entry` adds the `**Layer:**` line between `**Hash:**` and `**Terms:**`.
4. `extract_terms` continues to operate as today; the layer value is appended to the term list as part of the standard frontmatter scan (it's already covered if we add `layer` to the list of frontmatter fields whose values are tokenised). Implementation detail: include `layer` alongside `domain` in the term-extraction priority list.
5. Tests added for layer extraction (valid value, missing, invalid value), shelf-index rendering with layer line, term inclusion.

### `kb-lint` updates

1. New flag `--strict-layer`. When set, missing or invalid `layer` values upgrade from warning to error and the lint exits non-zero.
2. Reads the project's `layers:` config from CLAUDE.md `[Knowledge Base]` section via the `kb_config.allowed_layers(project_dir)` helper. Falls back to the four defaults when no config is declared.
3. Validates the config first: each entry must match `^[a-z][a-z0-9-]*$`. Config errors surface as a single top-of-report finding before per-file checks run.
4. Lint output gains a "Layer compliance" section listing per-file violations (missing `layer`, value not in allowed set, malformed value).
5. Tests added for: lenient default, strict failure, config-defined layer set (extended and replaced), malformed config entries, file with allowed custom layer, file with disallowed value.

### `agent-knowledge-updater.md` updates

1. New "Batch Mode" section documenting the `BATCH_MODE: create-only` directive and its three behaviours.
2. Examples added showing the conflict-existing-file response format.
3. The agent's `examples` frontmatter section is unchanged — batch mode is a parameter, not a separate role.

### Starter-pack backfill

The three starter-pack library files get `layer:` values. The starter-pack `_shelf-index.md` is regenerated to match (or left to the operator's first kb-rebuild-indexes — `build_shelf_index.py` is fast enough that this happens transparently).

### `CLAUDE-CONTEXT-knowledge-base.md` updates

1. Add `layer` to the frontmatter schema documentation.
2. Add a "Batch Workflow" section describing the prepare-then-ingest two-stage pattern with a worked example.
3. Update the routing table to include `kb-prepare-batch` (Bash, no agent) and `kb-ingest-batch` (Agent tool — dispatches `agent-knowledge-updater`).
4. Update the `kb-stats` row to reflect the new dashboard.

### `release-mapping.yaml` updates

Register the new files under `sdlc-knowledge-base`:
- New scripts: `plugins/sdlc-knowledge-base/scripts/kb_stats.py`
- New skills: `plugins/sdlc-knowledge-base/skills/kb-prepare-batch/SKILL.md`, `kb-ingest-batch/SKILL.md`, `kb-stats/SKILL.md`

### CI changes

This repo's CI gains a `kb-lint --strict-layer` step against the framework's own library (the starter-pack used as a self-test fixture). Failure on missing layer is the dogfood gate.

---

## File map

| Action | Path | Purpose |
|---|---|---|
| Modify | `plugins/sdlc-knowledge-base/scripts/build_shelf_index.py` | Add `extract_layer`, `IndexEntry.layer`, render `**Layer:**` field |
| Create | `plugins/sdlc-knowledge-base/scripts/kb_stats.py` | Pure-Python stats generator |
| Create | `plugins/sdlc-knowledge-base/scripts/kb_config.py` | Helper: read `[Knowledge Base]` from CLAUDE.md, expose `allowed_layers()` |
| Create | `tests/test_kb_config.py` | Unit tests for `allowed_layers()` |
| Modify | `tests/test_kb_build_shelf_index.py` | Layer extraction + rendering tests |
| Create | `tests/test_kb_stats.py` | Stats generator unit + integration tests |
| Create | `plugins/sdlc-knowledge-base/skills/kb-prepare-batch/SKILL.md` | Prepare-batch skill |
| Create | `plugins/sdlc-knowledge-base/skills/kb-ingest-batch/SKILL.md` | Ingest-batch skill |
| Create | `plugins/sdlc-knowledge-base/skills/kb-stats/SKILL.md` | Stats skill (Bash wrapper) |
| Modify | `plugins/sdlc-knowledge-base/skills/kb-lint/SKILL.md` | Add `--strict-layer` flag and check |
| Modify | `plugins/sdlc-knowledge-base/agents/agent-knowledge-updater.md` | Add Batch Mode section |
| Modify | `plugins/sdlc-knowledge-base/skills/kb-init/templates/starter-pack/library/agent-suitability-rubric.md` | Backfill `layer: methodology` |
| Modify | `plugins/sdlc-knowledge-base/skills/kb-init/templates/starter-pack/library/agentic-sdlc-options.md` | Backfill `layer: methodology` |
| Modify | `plugins/sdlc-knowledge-base/skills/kb-init/templates/starter-pack/library/specification-formality-and-agent-performance.md` | Backfill `layer: evidence` |
| Modify | `plugins/sdlc-knowledge-base/skills/kb-init/templates/starter-pack/library/_shelf-index.md` | Refresh entries with `**Layer:**` |
| Modify | `CLAUDE-CONTEXT-knowledge-base.md` | Document layer, batch workflow, kb-stats |
| Modify | `release-mapping.yaml` | Register new scripts and skills |
| Modify | `.github/workflows/<existing-CI>.yml` | Add `kb-lint --strict-layer` step |

---

## Acceptance criteria

| AC | Test |
|---|---|
| Library files with `layer: methodology\|evidence\|domain\|development` parse cleanly | Unit test on `extract_layer` |
| Missing `layer` produces `uncategorized` in shelf-index, no script failure | Unit test on `extract_layer`, integration on `rebuild_shelf_index` |
| Invalid `layer` value produces `uncategorized` and a warning | Unit test |
| `kb-lint --strict-layer` exits non-zero when any file lacks valid `layer` (default set) | Integration test with fixture library |
| `kb-lint --strict-layer` honours project-defined `layers:` from CLAUDE.md | Integration test with custom layers config |
| `kb-lint --strict-layer` flags malformed entries in `layers:` config | Integration test |
| `kb_config.allowed_layers()` returns defaults when no config declared | Unit test |
| `kb_config.allowed_layers()` returns project values when `layers:` is declared | Unit test |
| Shelf-index entries render `**Layer:** <value>` between Hash and Terms | Integration test on rendered output |
| Layer value appears in Terms list | Integration test |
| `kb-prepare-batch` copies/moves `.md` files into `raw/` correctly | Integration test |
| `kb-prepare-batch` converts `.pdf` via `markitdown` (mock the CLI) | Integration test with mock subprocess |
| `kb-prepare-batch` converts `.tex` via `pandoc` (mock the CLI) | Integration test with mock subprocess |
| `kb-prepare-batch` writes provenance frontmatter on converted files | Integration test |
| `kb-prepare-batch` refuses unknown extensions with clear error | Integration test |
| `kb-ingest-batch` writes/reads `.batch-progress.json` correctly | Integration test |
| `kb-ingest-batch` resumes after simulated mid-batch crash | Integration test |
| `kb-ingest-batch --retry-failed` re-queues failed entries | Integration test |
| `kb-ingest-batch` runs `build_shelf_index.py` once at the end | Integration test |
| `kb-ingest-batch` writes one consolidated `log.md` entry | Integration test |
| Batch-mode dispatch prompt includes `BATCH_MODE: create-only` directive | Integration test on dispatch-prompt formatting |
| `kb_stats.py` produces all five report sections (Inventory, Layer, Domain, Activity, Staleness) | Integration test |
| `kb_stats.py --output <path>` writes to file | Integration test |
| Starter-pack files have valid `layer:` values | Self-test in CI |
| Repo CI fails if any framework library file lacks `layer` | CI dogfood test |

Test additions: roughly 45–60 new tests across `test_kb_build_shelf_index.py` (layer additions), `test_kb_stats.py` (new), `test_kb_prepare_batch.py` (new), `test_kb_ingest_batch.py` (new), plus a small extension to existing kb-lint tests.

---

## Out of scope (deferred to Phase C or later)

- **#163 confidence metadata** — Phase C
- **#165 kb-lint auto-fix** — Phase C
- **Multi-format conversion plugins** — operator can shell out to additional CLIs, but the routing table is fixed at markitdown/pandoc for v0.3.0
- **Parallel batch ingestion with shared-file conflict resolution** — v0.3.0 uses create-only batch mode; merging concurrent updates to existing files is a v0.4.0 concern
- **Stats time-series / trends** — v0.3.0 is point-in-time; trend analysis is a v0.4.0 concern
- **Layer-aware librarian retrieval ranking** — librarian sees `layer` as a Terms entry today; explicit layer-filter parameters are deferred

---

## Open risks

1. **markitdown / pandoc binary availability** — operators on locked-down workstations may have neither. Mitigation: clear preflight error with install hints, and `.md`-only operation continues to work fully.
2. **Parallel batch dispatch model in Claude Code** — the parallel-Agent pattern is established in `kb-query`, but at higher concurrency (N=10+) it may hit harness limits. Mitigation: cap `--parallel` at 5 by default, document the cap, encourage operators to start sequential and ramp up.
3. **Resume-manifest write atomicity on Windows filesystems** — atomic rename semantics differ. Mitigation: explicit fallback to copy-and-delete-original if rename fails, with a brief race window documented.
4. **Layer set drift** — projects can extend the layer set freely via `layers:` in CLAUDE.md, so a malformed or inconsistent config could cause kb-lint failures across all files. Mitigation: kb-lint validates the config itself before validating files, so config errors are flagged once and clearly. Operators removing a previously-used layer from `layers:` will see lint failures on every file using the dropped value — this is desired behaviour (it surfaces orphaned layer references).

---

## Phase B closure

Phase B closes when all four sub-issues (#154, #161, #162) are implemented, all acceptance criteria pass, and the EPIC branch is ready for Phase C work. No PR is opened until the full EPIC is complete (per the EPIC branch model). Phase A's PR #198 remains open as the early closure for the foundation work.
