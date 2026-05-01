# v0.2.0 EPIC — `sdlc-assured` Audit-Readiness + Carry-Forward Closure

**EPIC:** to be filed as #188 (verify next available number when issuing)
**Branch:** `feature/sdlc-assured-v020` (new branch — clean slate from main post #178 merge)
**Date:** 2026-05-01
**Author:** Claude (with Steve Jones brainstorming)
**Predecessor EPIC:** #178 (Joint Programme + Assured bundle delivery, merged 2026-05-01 via PR #187, merge commit `e05e446`)

---

## 1. Goal

Make `sdlc-assured` (Method 2) **audit-ready** for regulated-industry use AND clear all known v0.1.0 deferred-debt items. After v0.2.0 ships, no documented v0.1.0 finding or architect-review concern remains open. A regulated-industry team can plausibly use Assured for real audit prep — modulo platform coverage (Swift/Java/etc. dependency extractors are interface-stubbed but not implemented).

## 2. Scope (18 items, all in)

### 2.1 Phase F findings (10)

The 10 findings logged at `research/phase-f-dogfood-findings.md` after the 2026-05-01 architect review correction:

**5 IMPORTANT** — audit-readiness blockers:
- **F-001** Annotation parser is Python-comment-only; markdown SKILL.md and HTML-comment forms are invisible. Only 18 of 129 annotations (14%) parsed during dogfood.
- **F-007** `visibility_rule_enforcement` cannot run without an import-graph extractor. The boundary model is partially aspirational. (Severity raised from MINOR by 2026-05-01 architect review.)
- **F-008** `granularity_match` produces 100% noise (43/43 false-positives) on projects following the DES-level annotation convention.
- **F-009** DO-178C RTM source-code column is 65% empty. RTM emits bare `—` placeholders that conflate "not implemented" / "implemented by config" / "external evidence" / "not applicable".
- **F-010** REQ-quality drift to function-shaped form. Three named drifters: `REQ-assured-decomposition-validators-001`, `REQ-assured-traceability-validators-003`, `REQ-assured-skills-001`.

**5 MINOR** — quality-of-life improvements:
- **F-002** `programs.yaml` `paths` cannot scope to a section of a file (whole-directory only).
- **F-003** Constitution REQ creates a category error in the annotation model — no `satisfies-by-existence` mechanism for governance documents.
- **F-004** REQ-inventory review-record gate assignment was offset by one phase. Documentation-only fix.
- **F-005** Severity-mixed REQs (collapsing warn-not-block + blocking validators under one REQ) obscure the severity contract.
- **F-006** No "see also" / `related:` mechanism for related REQs with overlapping intent.

### 2.2 Deviation-ledger items (2)

From `research/phase-de-deviation-ledger.md`:
- **F1** Phase F Task 9 placed `<!-- implements: -->` annotation INSIDE design-spec.md DES element. Convention unclear.
- **F4** Two timeout-recovery commits (`4aa73d3` Phase E Task 11; `dbff56c` Phase F Task 39) where the controller committed on behalf of timed-out subagents. Re-audit content vs plan prescriptions.

### 2.3 Phase D architect-review carry-forward concerns (3, NOT yet logged as findings)

From `research/sdlc-bundles/dogfood-workflows/programme-bundle-review-output.md` and Phase D retrospective §"Phase gate assessment":
- **D1** `spec_parser` does not skip blockquotes (`>`), inline code (`` `backticks` ``), or HTML comments (`<!-- ... -->`). REQ-IDs in narrative text get extracted as fake declarations.
- **D2** Article 12 ambiguity on "incomplete" — `requirements_gate` validates structure but not non-empty content of mandatory sections. A whitespace-only mandatory section currently passes.
- **D3** `phase-review` skill hard-codes agent paths (`sdlc-team-common:solution-architect`, `sdlc-team-fullstack:backend-architect`). Phase D's manifest `depends_on` fix declared the dependency but the skill itself has no graceful fallback if those plugins aren't loaded at runtime.

### 2.4 Phase E architect-review carry-forward concerns (3, NOT yet logged as findings)

From `research/sdlc-bundles/dogfood-workflows/assured-bundle-review-output.md`:
- **E1** Article 15 `orphan_ids` validator narrow — only checks REQ/DES kinds. An orphan DES that is cited by a TEST but no CODE annotation slips through. Architect: "the constitution should either narrow the claim or the validator should widen."
- **E2** Article 17 forward annotation completeness — `granularity_match` checks REQ→code (backward); no validator checks "every public function has an annotation" (forward). Article 17 promises more than the validators deliver.
- **E3** `remap_ids` only handles prefix-based remapping. Multiple-prefix overlap not handled (a record matching two remappings silently uses the first, no warning).

### 2.5 Total

**18 items. All in v0.2.0.**

## 3. Architecture — 7 phases

Multi-phase EPIC mirroring #178's shape, with containerised architect review at Phase A close (architecture sign-off) and Phase G close (audit-readiness sign-off).

### Phase A — Design decisions (2-3 days)

Settle six architectural calls before any implementation begins. Output: design spec at `docs/superpowers/specs/<date>-v020-design-decisions.md` (an addendum to this scoping spec). **Containerised architect review at close** — same pattern as #178 Phase B re-run, C task 10, D task 14, E task 41.

**Phase A exit criterion (hard gate):** no downstream semantic decision remains open. Phases B-G must not relitigate any of the six decisions; if a decision turns out wrong mid-implementation, escalate to user for tiebreak rather than re-deciding in code review.

The six decisions:

1. **F-008 semantics — pre-committed direction: indirect DES-mediated coverage.** A REQ is implementation-covered when at least one DES that `satisfies` it has valid evidence. This is option (a) from the finding. The architect review's role is to validate/refine the choice, not to pick from scratch. Rationale: this aligns the four downstream items around one coherent model — requirements express intent, designs bind intent to implementation evidence. Phase A confirms; subsequent phases implement against this contract.

2. **F-001 abstraction depth.** Minimal regex extension (`_HTML_IMPLEMENTS_RE` for markdown HTML comments — ~1 day) versus full `EvidenceIndexEntry` abstraction with file-type registry (architect-recommended — ~5-7 days). The abstraction is the right long-term answer; the regex extension is YAGNI-friendly. **Phase A picks the abstraction** unless cost/benefit changes.

3. **F-007 interface shape.** Define dependency-extractor interface generically enough that Swift/Java/Go adapters slot in without changing the validator contract. Python adapter is the primary v0.2.0 deliverable; **a small non-Python proof adapter is also delivered in Phase C** to validate the interface is not Python-shaped (see §3 Phase C below).

4. **E2 scope.** Define the new forward-completeness validator: walks all public functions, checks each has `# implements:`. Must define "non-trivial" precisely (exclude dunder methods, single-line getters, test fixtures). Risk: false-positive rate. Acceptance criterion in Phase A: ≤5% false-positive rate on the verification dogfood corpus.

5. **D1 implementation.** Extend `spec_parser`'s skip-rules from "fenced code blocks only" to also skip blockquotes (`> ...`), inline code (`` `id-token` ``), and HTML comments (`<!-- ... -->`). Decide: do we skip ALL three, or only specific ones? Architect's concern was minor; recommendation is to skip all three for consistency.

6. **F-002/F-003 fit with `EvidenceIndexEntry`.** Does the new abstraction subsume both, or do they need separate v0.2.0 mechanisms? Likely yes:
    - F-002 (paths section-anchor) = file-type registry can encode **named anchors/sections** scoping per file type. **No arbitrary line ranges** — they rot too easily under refactoring.
    - F-003 (satisfies-by-existence for governance docs) = a new `EvidenceIndexEntry` kind with no inline annotation, just a YAML frontmatter declaration
   Phase A confirms or rejects this fit.

### Phase B — Evidence model + parser (5-6 days)

Implements F-001, F-009, F-003, D1, F-002.

- `EvidenceIndexEntry` abstraction with file-type registry: Python (`# implements:`), markdown HTML-comment (`<!-- implements: -->`), YAML frontmatter (`implements: [...]`), plist/XML (path-based), satisfies-by-existence (governance docs).
- Typed evidence statuses on the 4 regulatory exporters (`linked` / `missing` / `not_applicable` / `manual_evidence_required` / `configuration_artifact`). Each cell in the RTM is now a tuple of (status, payload) instead of a bare string.
- `spec_parser` skip-rules extended to blockquotes, inline backticks, HTML comments.
- `programs.yaml` schema extended with optional `paths_sections:` for file-section / line-range scoping (F-002).
- `EvidenceIndexEntry.satisfies_by_existence` mechanism for governance documents (F-003).

### Phase C — Validator improvements (4.5-6 days)

Implements F-007, F-008, E1, E2, D2 plus the non-Python proof adapter.

- Dependency-extractor interface (`DependencyExtractor` protocol): `extract(source_paths: List[Path], programs: Decomposition) -> List[ImportEdge]`.
- Python adapter (`PythonAstExtractor`) that walks Python source trees, resolves imports to owning modules via `programs.yaml` paths, emits `ImportEdge` objects. Wired into `kb-codeindex` build step.
- **Small non-Python proof adapter** (~0.5-1 day): a minimal fixture-backed adapter that proves the interface is not Python-shaped. Candidates: a toy Swift import extractor (regex-based; just walks `.swift` files for `import Foo` lines and resolves to declared modules) OR a generic regex adapter parameterised by file extension and import-pattern. Goal is interface validation, not production-grade extraction; correctness on the v0.2.0 dogfood corpus is sufficient. **Recovery plan:** if the proof adapter discovers the interface is Python-shaped, drop the adapter, document the limitation, and defer cross-platform validation to v0.3.0.
- `granularity_match` rewrite per Phase A's F-008 decision (indirect DES-mediated coverage): a REQ passes when at least one of its `satisfies`-linked DESes has an `EvidenceIndexEntry` of any type.
- `orphan_ids` widening per Phase A's E1 decision (narrow constitution claim OR widen validator coverage).
- New `forward_annotation_completeness` validator per Phase A's E2 scope.
- `requirements_gate` non-empty-content check (Article 12 disambiguation).

### Phase D — ID system + REQ format (2-3 days)

Implements E3, F-006, F-005, F-004.

- `remap_ids` multiple-prefix handling: warn on multiple matches, allow explicit precedence declaration, document the deterministic resolution rule.
- REQ frontmatter schema: optional `related:` field for see-also cross-references (F-006).
- **F-005 — pre-committed direction:** split severity-mixed REQs into separate REQs when severity differs materially (one REQ per severity tier — blocking validators get their own REQ, warn-not-block validators get their own). Parentheticals are acceptable for minor severity nuance within a tier (e.g., "MAY warn under condition X"), but blocking-vs-warning splits MUST be separate REQs.
- REQ inventory documentation update (F-004) — wording fix only.

### Phase E — Quality discipline + skill robustness (3-4 days)

Implements F-010, D3, F1.

- Rewrite the 3 named function-shaped REQs at user-visible-capability level. Audit the remaining ~41 Phase F REQs against the bar; rewrite or accept-with-rationale.
- Candidate REQ-quality lint rule: flag REQ statements opening with a Python identifier or containing the literal word "function" / "method".
- `phase-review` skill: graceful fallback for absent agent plugins — try the configured agent first, fall back to `superpowers:requesting-code-review` pattern, log the fallback.
- Codify `<!-- implements: -->` placement convention: only on the implementing artefact (Python function body, SKILL.md after frontmatter, governance document YAML frontmatter); never inside a design-spec.md DES element. Update the Phase F design-spec where F1 violation occurred.

### Phase F — Audit closure (0.5-1 day)

Implements F4.

- Re-audit timeout-recovery commits `4aa73d3` (Phase E Task 11) and `dbff56c` (Phase F Task 39).
- Compare commit content to plan prescription byte-for-byte (modulo black/flake8 formatting).
- Confirm correctness OR identify drift and fix in a follow-up commit.

### Phase G — Verification dogfood + EPIC closure (3-4 days)

The dogfood is **verification-style** rather than recursive (per #178 Phase F). Re-runs validators on existing Phase F corpus + new validators built in Phases B-E. Faster than Phase F-of-178 (~3 days vs ~9) because the artefacts already exist. **The validation is not "rerun and observe cleaner" — it is a metric-delta + injected-defect protocol.**

**Phase G is structured in three sub-stages:**

1. **Baseline metric capture (~0.5 day).** Re-run all validators on the existing Phase F corpus with the v0.2.0 tooling. Capture: granularity_match noise rate, RTM source-code column gap %, RTM typed-evidence-status distribution, orphan_ids warning count, forward-completeness violation count, validator runtime.

2. **Injected-defect tests (~1.5-2 days).** For each new or rewritten validator, seed deliberate defects on a fixture branch and assert each defect is caught:
    - F-008 (`granularity_match` indirect coverage): seed a REQ whose `satisfies`-linked DESes ALL lack annotations → must fire.
    - F-007 (`visibility_rule_enforcement`): seed an undeclared cross-module Python import → must fire (strict mode) or warn (advisory).
    - F-007 non-Python adapter: seed an equivalent defect in the adapter's target language → must fire.
    - F-009 (typed evidence statuses): seed a REQ whose evidence is `not_applicable` with no justification → must fire.
    - E1 (widened `orphan_ids`): seed an orphan TEST → must fire.
    - E2 (forward-completeness): seed a public function with no `# implements:` annotation → must fire.
    - D1 (`spec_parser` skip-rules): seed a REQ-ID inside a blockquote, an inline-code span, and an HTML comment → none must be extracted.
    - D2 (`requirements_gate` non-empty-content): seed a whitespace-only mandatory section → must fire.
    The injected-defect fixtures live at `tests/fixtures/v020-verification/` and are committed to the branch. Each defect has a corresponding test asserting the validator fires.

3. **Acceptance metric deltas (~0.5-1 day).** Compare baseline (sub-stage 1) to v0.2.0-target metrics:
    - `granularity_match` noise rate: 100% → **≤5%** (hard gate)
    - DO-178C RTM source-code-column gap: 65% → **≤20%** (hard gate), each remaining cell typed via F-009 evidence status (no bare `—` placeholders)
    - `forward_annotation_completeness` (E2) false-positive rate: **≤5%** on the dogfood corpus (hard gate per Phase A acceptance criterion)
    - `visibility_rule_enforcement` runs cleanly on real Python source (no extractor crash, edges resolve to declared modules)
    - All existing tests still pass; new tests for v0.2.0 validators pass

If any hard gate is missed, Phase G does not close. Either fix the validator or rescope (with explicit user approval).

EPIC retro consolidating all 7 phases. Open EPIC PR. **Containerised architect review at close** as audit-readiness sign-off.

## 4. Success criteria

### Per-item resolution
- All 18 items resolved per architect review's audit-ready bar
- F-001/F-008/F-009 cluster: tooling produces a clean DO-178C RTM (verification dogfood §3 G)
- F-007: `visibility_rule_enforcement` runs on real Python source trees
- F-010: 3 named REQs rewritten; remaining 41 audited
- E1/E2/D1/D2/D3: all carry-forward concerns closed

### Test posture
- All existing tests pass (74 assured + 29 programme + 109 kb)
- ~50-80 new tests added per TDD discipline (proportional to the new validators + extractors + abstraction)
- Plugin packaging stays at 14/14

### Architectural sign-off
- Containerised architect review at Phase A close: AGREE on all design decisions, with concerns documented if any
- Containerised architect review at Phase G close: AGREE on audit-readiness claim

### Audit-readiness statement (post-merge)
- v0.2.0 release notes can claim: *"Method 2 / Assured v0.2.0 produces audit-ready evidence under the verification-dogfood corpus. Platform coverage limited to Python; Swift/Java/Go adapters are interface-stubbed but require v0.3.0+ implementation."*

## 5. Out of scope (deferred to v0.3.0+)

- Multi-program coordination (still deferred per #178 §8)
- Swift/Java/Go dependency extractors **beyond the interface stub** (Python adapter only in v0.2.0)
- AST-level code intelligence
- Industry certification itself (still substrate, not certification)
- ASCII DAG / HTML SVG visualisation (still stretch per #178 design spec §9 Q1)
- Bidirectional ReqIF sync
- ALM database integration (Jama / Polarion / Codebeamer)
- Migration of pre-Assured projects' un-annotated code

## 6. Time budget

Phase | Days
---|---
A — Design decisions | 2-3
B — Evidence model + parser | 5-6
C — Validator improvements (incl. non-Python proof adapter) | 4.5-6
D — ID system + REQ format | 2-3
E — Quality discipline + skill robustness | 3-4
F — Audit closure | 0.5-1
G — Verification dogfood + EPIC closure | 3-4
**Total** | **20-27 days**

Smaller than #178 (~25-35 days for D+E+F combined). Concentrated work on existing substrate rather than greenfield. Budget assumes Phase A locks decisions hard — if `EvidenceIndexEntry` or F-008 semantics get relitigated mid-implementation, expect a 3-5 day overrun. The Phase A exit criterion (no downstream semantic decision remains open) is the budget guardrail.

## 7. Risks

| # | Risk | Mitigation |
|---|---|---|
| R1 | Phase A architect review surfaces a design decision the team disagrees with — relitigation extends Phase A to 5+ days | Time-box Phase A at 3 days; if the architect review surfaces a disagreement, escalate to user for tiebreak rather than re-running |
| R2 | `EvidenceIndexEntry` abstraction is bigger than estimated (5-7 days could become 8-12) | Phase A has explicit fallback to minimal regex extension if the abstraction's complexity exceeds budget. Decide at Phase A close, not mid-Phase B |
| R3 | F-008 semantic choice cascades into many places (validator, RTM, lint rule, docs) — change of mind mid-implementation costs 2-3 days | Phase A locks the choice; subsequent phases reference it without revisiting |
| R4 | Verification dogfood reveals new defects in v0.1.0 substrate beyond the 18 items | Log as v0.3.0 candidates; do not block v0.2.0 close unless they're audit-readiness blockers (in which case scope-extend Phase G with explicit user approval) |
| R5 | E2 forward-completeness validator produces high false-positive rate on real codebases (e.g. Python helper modules) | Phase A acceptance criterion of ≤5% false positives; if exceeded, downgrade E2 to warning-only or defer to v0.3.0 |
| R6 | The 3 carry-forward Phase D concerns (D1/D2/D3) discover a deeper substrate defect (e.g. spec_parser's skip-rule extension breaks fixture-based tests) | Phase B/C/E each include "do not regress existing tests" as an acceptance criterion. If a carry-forward fix breaks tests, fix the test convention rather than reverting the fix unless the test exposes a real bug |
| R7 | The 41-REQ audit (Phase E F-010) finds many more drifters than the 3 named — workload overflow | Phase E time-boxed at 4 days; if more than ~10 drifters surface, defer the long tail to v0.3.0 with explicit list |
| R8 | The non-Python proof adapter (Phase C) discovers the dependency-extractor interface IS Python-shaped — assumed-generic interface is actually language-specific | Recovery plan documented in Phase C: drop the proof adapter, document the limitation in the design-decisions addendum, defer cross-platform validation to v0.3.0. Do not block Phase C close on the proof adapter; it is a stretch deliverable, not a hard gate |
| R9 | Phase A exit criterion ("no downstream semantic decision remains open") is breached mid-Phase B/C — implementation surfaces a decision Phase A missed | Escalate to user for tiebreak; do NOT decide-in-code-review. Add the new decision to the design-decisions addendum so the audit trail is complete. Time impact: 1-2 day pause. Acceptable cost compared to silent decision drift |

## 8. Open questions deferred to plan-writing

| # | Question | Resolution path |
|---|---|---|
| Q1 | Where does the `EvidenceIndexEntry` abstraction live — `code_index.py` extended, or new `evidence_index.py`? | Plan-writer decides based on file-size constraints and import dependencies |
| Q2 | Does the RTM exporter typed-evidence-status concept require a new dataclass (`EvidenceStatus`) or just enum? | Plan-writer decides; both viable |
| Q3 | Phase G's "verification dogfood" runs in CI or manually? | Plan-writer decides; manual sufficient for v0.2.0, CI integration is v0.3.0 |
| Q4 | Should D1's spec_parser skip-rule also skip code blocks inside markdown tables? | Plan-writer decides; low priority |
| ~~Q5~~ | ~~F-005 (severity-mixed REQs)~~ | **RESOLVED in spec §3 Phase D:** split severity-mixed REQs when severity differs materially; parentheticals OK for minor nuance only |
| ~~Q6~~ | ~~F-002 line ranges vs named anchors~~ | **RESOLVED in spec §3 Phase A decision 6:** named anchors/sections only; no arbitrary line ranges (rot risk) |

## 9. Issue management

- **File the EPIC issue immediately after spec approval** (not before). Verify next available number; expected #188. The issue points to this spec (and the to-be-written design-decisions addendum) as source of truth.
- Sub-issues per phase: ~7 sub-issues (one per phase A-G), or ~18 sub-issues (one per item) — plan-writer decides at scope time.
- Branch: `feature/sdlc-assured-v020` (already created from main post-#178-merge at `e05e446`; this spec landed at `7594d59`).
- No-PR-until-EPIC-complete model holds (precedent: #164 / PR #177; #178 / PR #187).
- Containerised architect reviews recorded in Archon SQLite (`~/.archon/archon.db` `remote_agent_workflow_runs` table) and verbatim outputs at `research/sdlc-bundles/dogfood-workflows/v020-*-output.md`.

## 10. References

- Predecessor EPIC: #178 (merge commit `e05e446`)
- Phase F findings: `research/phase-f-dogfood-findings.md` (10 findings F-001 to F-010)
- Deviation ledger: `research/phase-de-deviation-ledger.md` (15 deviations, 2 flagged for v0.2.0 review)
- Phase D architect review: `research/sdlc-bundles/dogfood-workflows/programme-bundle-review-output.md`
- Phase E architect review: `research/sdlc-bundles/dogfood-workflows/assured-bundle-review-output.md`
- Phase D retrospective: `retrospectives/186-phase-d-programme-bundle-substrate.md`
- Phase E retrospective: `retrospectives/104-phase-e-assured-bundle-substrate.md`
- Phase F retrospective (corrected): `retrospectives/178-phase-f-dogfood.md`
- Session meta-retrospective: `research/phase-g-session-meta-retrospective.md`
- 2026-05-01 architect reviews: `reviews/2026-05-01-ios-location-services-architect-review.md`, `reviews/20260501T031618Z_review.md`
- Implementation plan (v0.2.0): to be written next at `docs/superpowers/plans/2026-05-01-v020-assured-improvements-plan.md`
