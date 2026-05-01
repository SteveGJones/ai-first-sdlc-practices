# Phase F — Recursive Dogfood Design

**EPIC:** #178 (Joint Programme + Assured bundle delivery)
**Phase:** F (Real dogfood)
**Branch:** `feature/sdlc-programme-assured-bundles` (continues, no PR until Phase G)
**Date:** 2026-04-30
**Author:** Claude (with Steve Jones brainstorming)

---

## 1. Goal

Apply the Assured bundle (Method 2) to EPIC #178 itself — recursively dogfood the framework on the code that built the framework. Surface gaps in Method 2 by using it on real code; capture findings; defer fixes to v0.2.0 unless blocking.

## 2. Why this target

The design spec at `docs/superpowers/specs/2026-04-26-programme-assured-bundles-design.md` Phase F section recommended applying Assured to EPIC #142 sub-features 3-8. That recommendation is **stale** — those sub-features were merged in PR #153 on 2026-04-10, three weeks before the Phase E design spec was written.

Open candidates considered:
- **Retrospective on already-shipped #142.** Tests `code-annotate` and `kb-codeindex` against existing un-annotated code. Doesn't exercise `commission-assured`.
- **Apply to a small open feature (e.g., #161 batch ingestion).** Tests full pipeline on greenfield. Smaller surface, weaker recursion signal.
- **Recursive on #178 itself.** Highest signal — we know the code intimately, every gap is felt directly. Selected.

Recursive dogfood on #178 is the densest signal-per-day. We wrote the bundles; we feel every annotation friction, every validator gap, every workflow rough edge as a personal cost.

## 3. Architecture

### Decomposition

One program, three modules:

| Module ID | Name | Path | Notes |
|---|---|---|---|
| `P1.SP1.M1` | `programme-bundle` | `plugins/sdlc-programme/` | Method 1 substrate (Phase D output) |
| `P1.SP1.M2` | `assured-bundle` | `plugins/sdlc-assured/` | Method 2 substrate (Phase E output) |
| `P1.SP1.M3` | `kb-bridge` | `plugins/sdlc-knowledge-base/agents/synthesis-librarian.md` (the `SYNTHESISE-ACROSS-SPEC-TYPES` section only) | The Method 2 → KB integration point added in Phase E task 23 |

### Visibility rules

```yaml
visibility:
  - from: P1.SP1.M1
    to: []                  # Programme is a leaf — depends on nothing in this decomposition
  - from: P1.SP1.M2
    to: [P1.SP1.M1, P1.SP1.M3]   # Assured layers on Programme + uses KB-bridge
  - from: P1.SP1.M3
    to: []                  # KB-bridge is a leaf
```

### Settings

| Setting | Value | Reason |
|---|---|---|
| Granularity per module | `requirement` | Default; one annotation per REQ; no module-level or function-level overrides |
| Visibility mode | `advisory` | Self-dogfood; no external regulator |
| `change-impact-gate` | `disabled` | No regulatory context (IEC 62304 / FDA / ISO 26262 ASIL C/D doesn't apply to a self-dogfood) |
| `structure` per module | `flat` | None of the three modules use hexagonal architecture |

## 4. Scope

Approach 3 (full coverage realistic) — ~44 REQs across the three modules.

### M1 programme-bundle (~12 REQs)

| REQ area | REQ count | Components covered |
|---|---|---|
| Skills | 5 | commission-programme, phase-init, phase-gate, phase-review, traceability-export |
| Phase-gate validators | 4 | requirements_gate, design_gate, test_gate, code_gate |
| spec_parser | 1 | parse_spec, extracts REQ/DES/TEST IDs and satisfies references |
| Traceability matrix | 1 | build_matrix, export_csv, export_markdown |
| Constitution articles 12-14 | 1 | Phase-gate compliance + cross-phase reference integrity + mandatory phase-review |

### M2 assured-bundle (~30 REQs)

| REQ area | REQ count | Components covered |
|---|---|---|
| Skills | 8 | commission-assured, req-add, req-link, code-annotate, module-bound-check, kb-codeindex, change-impact-annotate, traceability-render |
| Traceability validators | 6 | id_uniqueness, cited_ids_resolve, orphan_ids, forward_link_integrity, backward_coverage, index_regenerability, annotation_format_integrity, change_impact_gate |
| Decomposition validators | 5 | req_has_module_assignment, code_annotation_maps_to_module, visibility_rule_enforcement, anaemic_context_detection, granularity_match |
| Export formats | 6 | DO-178C RTM, IEC 62304 matrix, ISO 26262 ASIL matrix, FDA DHF, csv, markdown |
| ID system | 2 | parse_id / format_id / is_positional / build_id_registry / render_id_registry / remap_ids |
| Render pipeline | 2 | render_module_scope, render_module_dependency_graph |
| Code index + spec emitter | 2 | parse_code_annotations, render_code_index, render_spec_findings |
| Constitution articles 15-17 | 1 | ID/traceability integrity + decomposition discipline + KB-for-code completeness |

### M3 kb-bridge (~2 REQs)

| REQ area | REQ count | Components covered |
|---|---|---|
| Mode behaviour | 1 | SYNTHESISE-ACROSS-SPEC-TYPES dispatch logic + REQ→DES→TEST→CODE attribution |
| valid_handles | 1 | Pseudo-handle whitelist extension for spec-type queries |

**Note:** Each REQ gets ≥1 DES, ≥1 TEST, ≥1 `# implements:` CODE annotation. Some components will share REQs where they share intent (e.g., the 4 phase-gate validators may collapse into 1 REQ if their behaviour is described as a single capability).

## 5. Workflow

1. **Commission** — run `commission-assured` on a fresh worktree (or in a clearly-marked dogfood subdirectory). Real scaffolding: `programs.yaml`, `library/`, `docs/specs/`, `docs/change-impacts/` (empty since gate is disabled).
2. **Enumerate** — walk each of the three module paths, list public functions/classes/skills/validators, draft REQ inventory per module.
3. **Author REQ artefacts** — group into ~10-12 feature directories (e.g., `docs/specs/programme-skills/`, `docs/specs/assured-validators/`, `docs/specs/assured-exports/`, `docs/specs/kb-bridge/`). Each feature dir gets `requirements-spec.md` with multiple REQs.
4. **Author DES artefacts** — `design-spec.md` per feature; each DES cites its REQ via `**satisfies:**`.
5. **Author TEST artefacts** — `test-spec.md` per feature; each TEST cites both REQ and DES via `**satisfies:**`.
6. **Annotate code** — add `# implements: <ID>` annotations to every public function/method that implements a DES. Use `code-annotate` skill where it helps; hand-annotate otherwise.
7. **Build code index** — run `kb-codeindex`; emit `library/_code-index.md`.
8. **Build ID registry** — run `kb-rebuild-indexes`-equivalent for assured (call `build_id_registry` and write `library/_ids.md`).
9. **Run module-bound-check** — all 5 decomposition validators in advisory mode.
10. **Run traceability validators** — all 6 mandatory validators (skip change-impact-gate since disabled).
11. **Render** — `traceability-render` for each of M1, M2, M3; output goes to `docs/traceability/<module-id>.md`.
12. **One regulatory export smoke test** — `traceability-export do-178c-rtm` on the full registry; verify it produces a coherent matrix.
13. **Capture findings** — every friction, validator surprise, missing skill, unclear error message goes into `research/phase-f-dogfood-findings.md`.

## 6. Gap-capture method

Single findings file at `research/phase-f-dogfood-findings.md`. Each finding entry:

```markdown
### F-NNN — <Short title>

**Severity:** BLOCKER / IMPORTANT / MINOR
**Surfaced during:** <step from §5 above>
**Reproduction:** <how to reproduce>
**Impact on regulated-industry users:** <high / medium / low / none>
**Suggested resolution:** <fix in v0.2.0 / defer / clarify in docs / no action>
**Related code/skill/validator:** <pointer>
```

**Findings accumulate; fixes ship in v0.2.0** (a separate post-Phase-G phase) unless a finding is a true blocker that prevents Phase F closure. The retrospective at Phase F closure quotes findings into a summary section and seeds GitHub issues for v0.2.0.

## 7. Out of scope

- **Cross-program coordination** — only one program (P1) per design spec §8.
- **Strict visibility mode** — advisory only.
- **`change-impact-gate`** — disabled.
- **Industry certification artefacts beyond one worked example** — only DO-178C RTM smoke test; not full IEC 62304 / ISO 26262 / FDA outputs.
- **Automation of REQ-authoring** — manual (or skill-assisted) authoring; no spec generation from code. Otherwise the dogfood doesn't surface real friction.
- **Fixing bundle code in response to findings** — Phase F surfaces; v0.2.0 fixes. Exception: a true BLOCKER fix can land in Phase F.
- **Phase A/B/C of #178** — those are research/design work, not code; applying REQ/DES/TEST to a research artefact is awkward.
- **Other plugins (sdlc-team-*, sdlc-core, sdlc-workflows, etc.)** — only the three modules listed in §3.

## 8. Success criteria

- `programs.yaml` committed; `module-bound-check` passes in advisory mode (warnings allowed).
- ~44 REQ artefacts committed across ~10-12 feature directories.
- Every REQ has ≥1 DES via `**satisfies:**`; every DES has ≥1 TEST via `**satisfies:**`; every TEST has ≥1 `# implements:` CODE annotation.
- All 6 mandatory traceability validators pass on the project state (`id_uniqueness`, `cited_ids_resolve`, `orphan_ids` warns-not-blocks, `forward_link_integrity`, `backward_coverage`, `index_regenerability`, `annotation_format_integrity`).
- `traceability-render` produces a coherent module-scoped doc for each of M1, M2, M3.
- `traceability-export do-178c-rtm` produces a complete RTM with no `—` placeholders for any cited REQ.
- ≥5 substantive findings captured in `research/phase-f-dogfood-findings.md` (with severities and resolutions).
- Phase F retrospective at `retrospectives/178-phase-f-dogfood.md` summarises findings and tags v0.2.0 follow-ups.
- Branch pushable; existing tests still green (Programme + Assured + kb tests at the count they were when Phase E closed); plugin packaging 14/14.

## 9. Time budget and staging

~8-12 days of focused work, staged:

| Stage | Days | Deliverable |
|---|---|---|
| 1 | 1-2 | Commission scaffolding + programs.yaml + REQ inventory drafted + 1 module's worth of REQs (likely M3 kb-bridge or M1 programme-bundle as proof-of-flow) |
| 2 | 3-4 | Remaining REQ artefacts across all 3 modules |
| 3 | 2-3 | DES + TEST artefacts + code annotations |
| 4 | 1 | Run validators + render + export + capture findings |
| 5 | 1 | Phase F retrospective + closure commit |

After each stage, a checkpoint: are findings accumulating fast enough to suggest a Phase F mid-course correction? If a true blocker surfaces, pause stage progression and triage.

## 10. Inputs and outputs

### Inputs (existing)

- `plugins/sdlc-assured/` — substrate from Phase E (HEAD `8e1f238`)
- `plugins/sdlc-programme/` — substrate from Phase D (HEAD `0140008`)
- `plugins/sdlc-knowledge-base/agents/synthesis-librarian.md` — kb-bridge
- All 8 Assured skills, 5 Programme skills, 6 Python modules under `scripts/assured/`, 5 Python modules under `scripts/programme/`
- The fixture at `tests/fixtures/assured/feature-sample/` (reference but not the dogfood target)

### Outputs (new)

- `programs.yaml` — repo root or under `docs/architecture/` depending on commission-assured's preference
- `docs/specs/<feature-id>/{requirements,design,test}-spec.md` × ~10-12 feature directories
- `library/_ids.md` — auto-generated registry
- `library/_code-index.md` — auto-generated code index
- `library/_spec-findings.md` — auto-generated spec-as-finding output
- `docs/traceability/{P1.SP1.M1,P1.SP1.M2,P1.SP1.M3}.md` — module-scoped renders
- `docs/traceability/dependency-graph.md` — Q1 markdown edge-list across modules
- `docs/traceability/do-178c-rtm.md` — one regulatory export smoke test
- `research/phase-f-dogfood-findings.md` — accumulated findings
- `retrospectives/178-phase-f-dogfood.md` — Phase F retrospective
- `# implements: <ID>` annotations across ~80-150 functions in `plugins/sdlc-programme/scripts/programme/*.py` and `plugins/sdlc-assured/scripts/assured/*.py` (kb-bridge has no Python code, just the markdown section)

### Boundary discipline

This phase **does not modify** the existing bundle code in response to findings (with one exception: BLOCKER findings). The bundle code is the dogfood target; touching it during Phase F would invalidate the signal.

The bundle code IS modified to add `# implements:` annotations — those are the dogfood artefact, not a fix.

If a finding requires a fix to make Phase F itself terminate (e.g., a validator crash), that fix is a separate commit with severity BLOCKER and rationale logged.

## 11. Risks

| Risk | Mitigation |
|---|---|
| ~44 REQs is more paperwork than dogfood signal value justifies | Stage 1 acts as a tripwire — if 1-module's-worth feels overwhelming, escalate to user for scope cut |
| Authoring REQs that just paraphrase function docstrings doesn't surface design-level friction | Aim for REQ statements at the user-visible-capability level, not the implementation level — e.g., "REQ: The id_uniqueness validator MUST report duplicate IDs with their source files" not "REQ: The function id_uniqueness exists" |
| Code annotations on private/internal functions add noise | Annotate only PUBLIC API of each module — module-level functions, exported skills, validator entry points. Private helpers (`_module_paths`, `_flush`) skip annotation |
| Validators surface findings that turn out to be plan/design errors, not Method 2 bugs | The findings file requires "impact on regulated-industry users" — that field forces honest triage |
| Recursive ID namespace collisions if Phase F's REQs accidentally use IDs that were sample data in Phase E test fixtures | Use distinct feature-id prefixes (e.g., REQ-progskill-001, REQ-assvalid-001) that don't collide with `auth` (the fixture's feature-id) |
| Time runs over the 8-12 day estimate | Stages 4 and 5 are firm deadlines; if stages 1-3 overrun, scope-cut at stage 3 (some REQs ship without full DES/TEST chains, captured as v0.2.0 backlog) |

## 12. Open questions deferred to plan-writing

| # | Question | Notes |
|---|---|---|
| Q1 | Where does `programs.yaml` live — repo root or `docs/architecture/`? | `commission-assured`'s scaffold position is the authoritative answer; plan-writer reads the skill |
| Q2 | Do the existing `tests/test_assured_*.py` files count as "test specs" for the satisfies chain, or do we need new `test-spec.md` files describing test intent? | Plan-writer decides. Recommendation: separate `test-spec.md` describes intent; `tests/test_*.py` is the implementation artefact that the test-spec satisfies |
| Q3 | How many feature directories should ~44 REQs be split across? | Plan-writer proposes 10-12 (REQs grouped by capability area); scope-tunable in Stage 1 |
| Q4 | Are private helper functions worth annotating (negative test for `granularity_match` warning rate)? | Recommendation: skip private helpers in v0.1.0 dogfood. If `granularity_match` fires too many false-positives on private helpers, that's a finding worth capturing |

## 13. References

- Parent EPIC: #178 (Joint Programme + Assured bundle delivery)
- Phase E spec: `docs/superpowers/specs/2026-04-26-programme-assured-bundles-design.md` §F
- Phase D retrospective: `retrospectives/186-phase-d-programme-bundle-substrate.md`
- Phase E retrospective: `retrospectives/104-phase-e-assured-bundle-substrate.md`
- Implementation plan (Phase F): to be written next at `docs/superpowers/plans/2026-04-30-phase-f-dogfood-plan.md`
