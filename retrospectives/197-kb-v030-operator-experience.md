# Retrospective: EPIC #197 — sdlc-knowledge-base v0.3.0 Operator Experience + Scale

**Branch:** `feature/kb-v030-operator-experience`
**EPIC:** #197
**Closes:** #155, #196, #154, #161, #162, #163, #165
**Date range:** 2026-05-03 – 2026-05-06 (three sessions)
**Commits on branch:** 49
**Status:** COMPLETE — ready for combined Phase B+C PR

---

## What was built

### Phase A — Deterministic index rebuild + agent-only enforcement

**Issue #155 — `build_shelf_index.py`**: Pure-Python deterministic shelf-index rebuild replacing the prior LLM extraction pass. Key deliverables: `parse_frontmatter`, `extract_terms/facts/links`, `compute_hash`, `build_entry`, `rebuild_shelf_index` (incremental + full mode), SHA-256 change-detection, `_ShelfIndexHeader` reading for library metadata preservation. The rebuild is <1 second for 500 files; no LLM invocation. The kb-rebuild-indexes SKILL.md was rewritten as a thin Bash wrapper that invokes the script.

**Issue #196 — Agent-only enforcement**: `CLAUDE-CONTEXT-knowledge-base.md` added with the routing table distinguishing agent-dispatched operations (kb-query, kb-ingest, kb-lint) from script-based lightweight operations (kb-rebuild-indexes, kb-stats, kb-staleness-check). Guardrail notes added to all 8 kb-* skill files. This addressed the root cause of context degradation observed in the Amkor engagement.

Phase A shipped 34 tests and established the implementation pattern (pure Python module + thin Bash wrapper skill) that Phase B and C followed throughout.

### Phase B — Operator features: layer tags, batch ingestion, kb-stats

**Issue #154 — Layer classification tags**: New required `layer:` frontmatter field on library files (default set: methodology / evidence / domain / development). `build_shelf_index.py` extended with `extract_layer`, `IndexEntry.layer`, and `**Layer:**` in the shelf-index render. `kb_config.py` new module with `allowed_layers()` (reads project-configurable `layers:` from CLAUDE.md `[Knowledge Base]` section) and `check_layer_compliance()`. `kb-lint` gained `--strict-layer` flag (layer compliance pre-check step 0, non-zero exit on violations). This repo's CI gained a `kb-layer-compliance` job (later renamed `kb-compliance` in Phase C). `kb_layers.py` + `kb-layers` skill: safe list/add/remove of the project's layer vocabulary with usage-check on remove and atomic CLAUDE.md write. Starter-pack backfilled with `layer:` on all three library files and shelf-index entries.

**Issue #161 — Batch ingestion**: Two-stage workflow. `kb_prepare_batch.py` + `kb-prepare-batch` skill: stages source files into `library/raw/` converting non-markdown formats via markitdown (PDF/DOCX/PPTX/XLSX/HTML/CSV) or pandoc (TeX/EPUB/RST/ORG); adds provenance YAML frontmatter with `status: raw`; copy or move mode; `--overwrite` flag. `kb_ingest_batch.py` + `kb-ingest-batch` skill: drives `agent-knowledge-updater` over staged files with `.batch-progress.json` resume manifest (atomic write), `--retry-failed` flag, `BATCH_MODE: create-only` dispatch directive (agents create-only, no shelf-index rebuild, no log append per-file; single rebuild + consolidated log entry at end). `agent-knowledge-updater` gained a Batch Mode section documenting the create-only constraints and conflict-existing-file response format.

**Issue #162 — kb-stats dashboard**: `kb_stats.py` + `kb-stats` skill: pure-Python 5-section dashboard (Inventory, Distribution by layer, Distribution by domain, Recent activity, Staleness). `--output <path>` and `--since <ISO-date>` flags. Read-only; no agent dispatch.

Phase B shipped 86 tests (628 → 714 total). 22 tasks, 12 doc-only (agents, skills, starter-pack, CI, release-mapping) and 10 Python implementation + tests.

### Phase C — Confidence metadata + auto-fix

**Issue #163 — Two-dimensional confidence metadata**: Core insight: source quality (inherent evidence quality) and query relevance (how directly the source answers *this* question) are independent. A peer-reviewed DORA study is always high-quality evidence, but if it's pulled tangentially for a question about agent context limits, the combined confidence should reflect the oblique connection.

`confidence.py` new module: `COMBINATION_TABLE` (12 entries covering all source-quality × query-relevance pairs), `combine_confidence()` (case-insensitive lookup, "low" fallback for unrecognised inputs), `parse_finding_confidence()` (extracts source_confidence/query_relevance/combined from a finding block), `check_confidence_compliance()` (scans library files for missing/invalid `confidence:` field), `main()` CLI.

`build_shelf_index.py` extended: `extract_confidence` returns high/medium/low for valid values, "unknown" for absent or invalid; `IndexEntry.confidence`; `**Confidence:**` between `**Layer:**` and `**Terms:**` in rendered entries; confidence value appended to Terms list.

`research-librarian` agent gains three mandatory structured tags per retrieval finding block: `**Source confidence:**` (from the shelf-index), `**Query relevance:**` (direct / supporting / tangential, assessed by the librarian), `**Confidence:**` (combined via the table). Caveats line explains relevance when supporting/tangential.

`agent-knowledge-updater` gains confidence-setting instructions: table mapping source types to confidence values; rules for new-file creation vs. updating existing files (no downgrading existing rating).

`kb-lint` gained `--strict-confidence` (symmetric with `--strict-layer`) and Step 0 extended to run confidence compliance alongside layer compliance. CI job renamed `kb-compliance`.

`kb-stats` extended: "Files lacking confidence tag" in Inventory; "Distribution by confidence" table section.

Starter-pack library files backfilled with `confidence: high` (all three are peer-reviewed Agentic SDLC research).

**Issue #165 — kb-lint auto-fix**: `kb_lint_fix.py` + `kb-lint --auto-fix` flag. Mechanical-only scope (no judgment required): adds `layer: uncategorized`, `confidence: medium`, `cross_references: []` to files missing those fields. For files with NO frontmatter at all: inserts a stub block with `confidence: low` (no source metadata to calibrate from), `status: draft`, and title derived from filename (hyphens/underscores → spaces, title-cased). Atomic write (.tmp + rename). `--dry-run` reports without writing. `kb-lint --auto-fix` runs the fixer, rebuilds the shelf-index, then proceeds with normal lint.

Phase C shipped 43 tests (714 → 757 total).

---

## What worked well

**Subagent-driven development with two-stage review caught every significant gap before it accumulated.** Across 22 implementation tasks in Phase B and 10 in Phase C, the spec compliance review (first) caught: `kb_stats.py` using ASCII bar charts instead of the spec's markdown tables (spec gap); `mark_failed` not removing from pending (spec gap — the symmetric `mark_completed` had the correct pattern); `build_manifest` inflating the `total` count with failed entries (spec gap); `fields_added` undercounted in `kb_lint_fix.py` stub creation (spec gap); missing `_index.md` exclusion test in two modules (spec gap). The code quality review then caught: TypedDict needed instead of `dict[str, object]` for `list_layers` return type (mypy errors in `main()`); unused imports and dead symbols flagged by ruff; `_materialise_layers_in_claude_md` over 50 lines (debt checker threshold). Without the two-stage gate, several of these would have been discovered as regressions later.

**The "permissive default, strict opt-in" pattern is the right UX model for new required fields.** Both `layer:` and `confidence:` follow this pattern: `build_shelf_index.py` is permissive (records "uncategorized" or "unknown" for missing values, never fails the rebuild), while `kb-lint --strict-layer` and `--strict-confidence` provide the enforcement gate. Operators can add the feature to an existing library and adopt strict mode when they're ready, rather than being forced to backfill all files before the rebuild works. The CI dogfood gate uses strict mode; user-installed libraries default to lenient.

**The two-dimensional confidence model came from a genuine user insight mid-brainstorming.** The initial design (option A in brainstorming) proposed a single `confidence:` field on library files. The user's observation — "a very good high-confidence source that is only tangentially relevant to the subject isn't a HIGH quality source FOR THAT QUERY even if it is a high quality source as a source" — clarified that these are two orthogonal signals. The design that resulted (source quality on file frontmatter, query relevance assessed by the librarian at runtime, combination via a deterministic table) is both machine-testable and conceptually clean. `test_combine_all_table_entries` tests all 12 table entries in a single assertion loop; any future table drift will fail fast.

**The `check-plugin-packaging.py` validator is functioning as designed.** It caught the plugin-dir divergence in Phase B (subagents edited plugin-dir copies instead of root sources) and again in Phase C (same pattern). Both times the fix was mechanical: copy the edited content back to the root source path. The validator made the problem visible immediately rather than silently shipping a diverged plugin.

**The `kb_lint_fix.py` stub frontmatter decision — `confidence: low` + `status: draft` rather than refusing to fix — is correct.** The brainstorming discussion landed on: "stub it and make it low with the explanation." Files without any frontmatter are real content that needs curation, not errors to skip. A stub at `status: draft` and `confidence: low` signals to operators that the file needs human attention while keeping it processable by the toolchain. `kb-lint` will surface these stubs in any subsequent run, which is exactly the right behaviour.

**Frequent small commits (49 total) with clear per-issue prefixes made git history legible.** Every commit follows `feat(#N)`, `fix(#N)`, `docs(#N)`, or `chore` with the relevant issue number. Reviewing the branch history is straightforward because each commit closes one specific thing.

---

## What was harder than expected

**The plugin-dir vs. root-source pattern confused subagents on every doc-editing task.** This repo has a dual-copy structure: skill files and agent files are authored in root directories (`skills/`, `agents/`) and packaged into plugin directories (`plugins/sdlc-knowledge-base/skills/`, `plugins/sdlc-knowledge-base/agents/`). When subagents were asked to edit `kb-lint/SKILL.md` or `agent-knowledge-updater.md`, they consistently found and edited the plugin-dir copy, leaving the root source stale. The `check-plugin-packaging.py` validator caught this both in Phase B and Phase C, requiring a copy-back step and an additional commit. The plan's file map documented "ROOT SOURCE" for agent and skill files, but subagents read the plugin-dir path first since it appeared first in find results.

**`kb_stats.py` required a full spec-compliance fix pass.** The implementer's first delivery used ASCII bar charts for both layer and confidence distribution, omitted "Files lacking layer tag" and "Files lacking cross-references" from the Inventory section, and had a "Recent activity" heading with a parenthetical suffix that broke the spec's exact-match expectation. Three of five required sections were non-compliant. The spec reviewer caught all of this; the fix pass (converting to markdown tables, adding the two inventory metrics, correcting the heading) was mechanical once identified but represented significant re-work.

**`kb_ingest_batch.py` had two independent symmetric bugs.** `mark_failed` was missing the `pending` removal step (the spec says "removes from pending, adds to failed" — the same operation `mark_completed` performs correctly). Separately, `build_manifest` included failed entries in the `total` count, inflating it on resume. Both were caught by the spec reviewer. The root cause in both cases was that the implementer had `mark_completed` as the reference but didn't verify `mark_failed` was symmetric, and the `total` calculation wasn't reconciled against the spec's manifest structure definition.

**`confidence.py` needed robustness fixes the plan didn't explicitly call out.** The spec reviewer flagged: CRLF line endings would silently fail the frontmatter regex; `read_text` without exception handling would crash on non-UTF-8 files; `rel.parts[0]` had a theoretical IndexError on zero-part paths; `_index.md` exclusion was present in the constant but untested. The fixes were all straightforward (CRLF-safe regex, try/except on read, length guard, additional test case), but none were in the original plan. The pattern: any module that scans a filesystem directory needs these defensive cases, and they should be in the plan template for scanner functions.

**`kb_lint_fix.py`'s `fields_added` counter was undercounted for stubs.** `_create_stub_frontmatter` returned `["stub"]` (one item) even though the stub writes six fields. The fix was to return the actual field names. The code quality reviewer caught this; the spec reviewer had not checked the counter semantics closely because the tests didn't assert the exact `fields_added` count for the stub case.

---

## Lessons learned

**Embed the root-source rule directly in every plan task that touches agent or skill files.** The plan's file map said "ROOT SOURCE" for agent and skill files, but that alone didn't prevent the pattern. A more effective approach: in the implementer prompt, explicitly say "Do NOT edit `plugins/sdlc-knowledge-base/agents/...` or `plugins/sdlc-knowledge-base/skills/...` — those are plugin-dir copies. Edit ONLY `agents/knowledge-base/...` and `skills/...`. Verify with `python tools/validation/check-plugin-packaging.py` after committing." Making it a step in the task (not just a file map note) would prevent the regression.

**Scanner functions (any function that iterates `.rglob("*.md")`) need a standard defensive checklist.** Every scanner in this codebase needs: CRLF-safe frontmatter regex; `try/except (OSError, UnicodeDecodeError)` on `read_text`; `len(rel.parts) > 0` guard before indexing; exclusion test coverage for `_index.md` (not just `_shelf-index.md` and `log.md`). This should be a checklist item in the plan template for any new scanner module, rather than discovered per-task by the spec reviewer.

**"Symmetric operations" should be verified symmetrically.** When a module has `mark_completed` and `mark_failed`, the plan should explicitly state "verify `mark_failed` is symmetric to `mark_completed` in its treatment of the `pending` list." Symmetric API pairs are a common source of one-sided bugs because the first implementation establishes a pattern that the reviewer trusts the second to follow.

**The two-dimensional confidence model is the right framework for quality signals on retrieval.** Source quality (stable, set at ingest) and query relevance (dynamic, assessed at query time) are genuinely independent. The combination table makes the final label deterministic and auditable. Future quality signals that the KB system might surface (e.g., citation recency, sample-size magnitude) should follow the same pattern: a stable attribute on the library file, a query-time relevance signal from the librarian, and a deterministic combination. Avoid adding more axes to the combination table — keep it two-dimensional.

**Stub frontmatter at `confidence: low` + `status: draft` is the right failure mode for the auto-fixer.** The alternative (skipping files without frontmatter or reporting them as errors) would leave real content in an invisible state — `kb-lint` and `kb-rebuild-indexes` would silently ignore it. Inserting a stub means the file appears in the shelf-index, gets flagged by `kb-lint --strict-confidence`, and prompts the operator to update the title and domain rather than leaving the file as an invisible orphan. The `status: draft` field is the correct signal to the `agent-knowledge-updater` that this file needs curation, not automatic inclusion in a batch ingest.

---

## What was deferred

Phase C's spec explicitly lists these as out of scope for v0.3.0:
- **Confidence trend over time** — point-in-time; tracking confidence drift across ingestion events is v0.4.0.
- **Confidence on cross-library query results** — external libraries may lack `confidence:` fields; the librarian uses "unknown" for their entries, which maps to the correct "low" combined confidence for tangential relevance. No additional handling needed now.
- **Auto-fix for LLM-identified cross-references** — Check 4 of `kb-lint` (missing cross-references) comes from the LLM's analysis of what should reference what. Auto-applying those additions requires post-processing the lint report, which is judgment-adjacent. The mechanical-only charter of `kb_lint_fix.py` was right to exclude this.
- **Confidence override at query time** — operators can update `confidence:` in frontmatter manually; no query-time override mechanism was added.
- **`--strict-confidence` in user-installed libraries by default** — users opt in; this repo's CI enforces it on the starter-pack only.

Also deferred from the broader EPIC scope but captured in issue tracker:
- **#118 — Codebase-index value-add**: the KB plugin focuses on curated library files; a codebase-index (for `# implements:` style annotations) is a separate capability.
- **#133/#134 — User-path test harness**: automated verification that skill invocations produce the right output; out of scope for this EPIC.

---

## Validation evidence

- `python -m pytest tests/ -q` → **757 / 757 PASS** (baseline before EPIC: 628; net additions: 129)
- `python tools/validation/check-plugin-packaging.py` → **PASS (14/14 plugins verified)**
- `python tools/validation/local-validation.py --quick` → **PASS (0 errors, 0 warnings)**
- `python tools/validation/local-validation.py --syntax` → PASS throughout all phases
- `python -m ruff check` → clean on all Phase B and C scripts
- `python3 -c "import yaml; yaml.safe_load(open('release-mapping.yaml').read())"` → YAML valid
- `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/validation.yml').read())"` → YAML valid
- Pre-commit: known env gap — `pre-commit` binary absent from local environment; all other 9 local-validation checks pass individually. Not introduced by this EPIC; pre-existing.

### New deliverables summary

| Deliverable | Type | Issue |
|---|---|---|
| `build_shelf_index.py` | New Python script | #155 |
| `kb_config.py` | New Python script | #154 |
| `kb_layers.py` | New Python script | #154 |
| `kb_stats.py` | New Python script | #162 |
| `kb_prepare_batch.py` | New Python script | #161 |
| `kb_ingest_batch.py` | New Python script | #161 |
| `confidence.py` | New Python script | #163 |
| `kb_lint_fix.py` | New Python script | #165 |
| `kb-rebuild-indexes` SKILL.md | Rewritten (Bash wrapper) | #155 |
| `kb-layers` SKILL.md | New skill | #154 |
| `kb-prepare-batch` SKILL.md | New skill | #161 |
| `kb-ingest-batch` SKILL.md | New skill | #161 |
| `kb-stats` SKILL.md | New skill | #162 |
| `CLAUDE-CONTEXT-knowledge-base.md` | New context module | #196 |
| `kb-lint --strict-layer` | Flag extension | #154 |
| `kb-lint --strict-confidence` | Flag extension | #163 |
| `kb-lint --auto-fix` | Flag extension | #165 |
| `agent-knowledge-updater.md` | Agent extension (2 sections) | #161, #163 |
| `research-librarian.md` | Agent extension (confidence tags) | #163 |
| CI `kb-compliance` job | New CI check | #154, #163 |
