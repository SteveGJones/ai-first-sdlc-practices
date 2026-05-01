# v0.2.0 Phase G Sub-stage 1 — Baseline Metrics

**Date:** 2026-05-01
**Corpus:** docs/specs/ + plugins/ in this repo (Phase F #178 corpus)
**Tooling version:** v0.2.0 validators (post-task-33)
**Captured by:** Phase G sub-stage 1, EPIC #188 task 34

## Numbers

| Metric | Value | Notes |
|---|---|---|
| `granularity_match` warnings | 14 | of 44 REQs with `granularity=requirement` |
| RTM source-code gap | 31.82% | 30 of 44 REQs have DES-mediated or direct evidence |
| Typed-evidence-status: LINKED | 0 | |
| Typed-evidence-status: MISSING | 0 | |
| Typed-evidence-status: NOT_APPLICABLE | 0 | |
| Typed-evidence-status: MANUAL_EVIDENCE_REQUIRED | 0 | |
| Typed-evidence-status: CONFIGURATION_ARTIFACT | 0 | |
| Typed-evidence-status: UNSET (no `**Evidence-Status:**` field) | 44 | All REQs predate v0.2.0 F-009 — field not yet added to specs |
| `orphan_ids` warnings | 44 | Post-E1 widening (REQ/DES/TEST/CODE); all 44 TEST records are orphans |
| `forward_annotation_completeness` violations | 25 | Public functions in plugins/sdlc-assured/ and plugins/sdlc-programme/ without `# implements:` |
| Validator runtime (wall-clock) | 0.058s | |

## Methodology

**ID and metadata registry:** `build_id_registry(Path("."))` walks `docs/specs/**/*.md` and collects all 132 ID records (44 REQ, 44 DES, 44 TEST, 0 CODE). `build_requirement_metadata_registry` walks `docs/specs/**/requirements-spec.md` and collects `**Evidence-Status:**` fields; all 44 REQs have no such field (UNSET) because the existing specs predate the v0.2.0 F-009 feature.

**Evidence collection:** `EvidenceIndexRegistry.with_default_adapters()` scanned 36 spec `.md` files (under `docs/specs/`) and 46 code files (under `plugins/sdlc-programme/`, `plugins/sdlc-assured/`, `plugins/sdlc-knowledge-base/agents/`), yielding 43 `EvidenceIndexEntry` records. The spec-to-module mapping used a feature-name heuristic (flat IDs with `assured-*` → `P1.SP1.M2`, `programme-*` → `P1.SP1.M1`, `kb-bridge-*` → `P1.SP1.M3`) because the flat-format IDs live in `docs/specs/` which is not under any declared module path in `programs.yaml`. This heuristic is documented as a corpus limitation; Task 36's injected-defect tests are not affected because they will introduce spec-format IDs into the fixture spec files under the same naming conventions.

**`granularity_match`:** Called with `declared_reqs=[44 flat REQ IDs]`, `annotations=[CodeAnnotation list from evidence entries]`, `satisfies_graph={DES-id: [REQ satisfies]}`. 14 warnings = REQs in declared-module granularity=requirement modules with no direct or DES-mediated `# implements:` annotation. Breakdown: 13 in M2 (sdlc-assured), 1 in M1 (sdlc-programme). These are VALID warnings — the phase F corpus genuinely lacks complete annotation coverage.

**RTM gap:** For each REQ, checked for direct annotation (`req_id in annotated_ids`) or indirect coverage via `inverse_satisfies` (DES that satisfies REQ is itself annotated). 30/44 covered → 31.82% gap. This exceeds the ≤20% acceptance criterion; this is the BASELINE before Task 36's injected-defect / delta measurement.

**`orphan_ids`:** E1-widened check (REQ/DES/TEST/CODE). All 44 TEST records are orphans — no CODE records exist that cite TEST IDs in `satisfies` links. This is the authentic state of the Phase F corpus.

**`forward_annotation_completeness`:** Walked all `.py` files under the three declared module paths. 25 public non-trivial functions are missing `# implements:` annotations, concentrated in `plugins/sdlc-assured/scripts/assured/`.

## Anomalies / observations

1. **RTM gap exceeds the ≤20% gate (31.82%):** This is expected for the existing Phase F corpus — it is a BASELINE, not a pass/fail result. The Phase F corpus was not annotated to v0.2.0 standards. Task 36 will show the delta when injected-defect tests exercise the validators.

2. **Typed-evidence-status all UNSET:** The `**Evidence-Status:**` field is a new v0.2.0 addition (F-009). None of the 44 existing REQs include it yet. The five EvidenceStatus values (LINKED, MISSING, NOT_APPLICABLE, MANUAL_EVIDENCE_REQUIRED, CONFIGURATION_ARTIFACT) will be populated incrementally as specs are updated. Task 36 injected-defect tests will add explicit `**Evidence-Status:**` lines to fixture specs to exercise the parser.

3. **All 44 TEST records are orphans:** No CODE-kind records exist in this corpus (CODE count = 0). TEST IDs are never cited by CODE satisfies links, producing 44 orphan-TEST warnings. This is genuine corpus state, not a validator bug.

4. **spec_module_lookup uses feature-name heuristic:** The programs.yaml module paths declare code directories (`plugins/sdlc-*/`), not doc directories (`docs/specs/`). Flat-format IDs live in docs, so no source-path-based matching is possible. The heuristic (feature name contains `assured` → M2, `programme` → M1, `kb-bridge` → M3) correctly maps all 132 records and is deterministic for this corpus.

5. **`granularity_match` 0 warnings in first script run:** Initial measurement script used source-path-based module lookup, which mapped all flat IDs to no module (docs/specs/ not under plugins/). Corrected by adopting the feature-name heuristic. Final 14 warnings are accurate.

## Hard-gate context

These baseline numbers will be compared to a post-Phase-G acceptance run in Task 36. The Phase G hard gates are:

- `granularity_match` noise ≤5% false-positive rate among warnings
- RTM source-code gap ≤20%
- `forward_annotation_completeness` false-positive rate ≤5%

The baseline alone does NOT decide pass/fail — Task 36 will compute deltas after the injected-defect tests prove the validators fire as intended.

## Validator self-check

Mandatory validators confirmed passing on the same corpus:

| Validator | Result |
|---|---|
| `id_uniqueness` | PASS |
| `cited_ids_resolve` | PASS |
| `forward_link_integrity` | PASS |
