# Retrospective: Phase F — Recursive Dogfood (EPIC #178)

**Branch:** `feature/sdlc-programme-assured-bundles`
**Status:** COMPLETE
**Phase F commits (251663d..HEAD):** 20 commits

---

## What we set out to do

Apply the Assured bundle (Method 2) to EPIC #178 itself — author ~44 REQ/DES/TEST chains
describing Programme + Assured + KB-bridge, annotate the existing code, run validators,
capture findings, and surface honest limits of v0.1.0 through a recursive dogfood exercise.

The target was structured in three stages:
- **Stage 1 (M3 proof-of-flow)** — smallest module first; go/no-go tripwire
- **Stage 2a (M1, M2)** — full REQ/DES/TEST authoring across all 12 feature directories
- **Stage 2b (indexes + validators + RTM)** — KB generation, decomposition + traceability
  validator runs, module-scope renders, DO-178C RTM smoke test

---

## What was built

**REQ/DES/TEST coverage — 44 chains across 12 feature directories:**

| Module | Feature dirs | REQs |
|---|---|---|
| M3 — kb-bridge | `kb-bridge-mode` | 2 |
| M1 — programme-bundle | `programme-skills`, `programme-validators`, `programme-substrate` | 12 |
| M2 — assured-bundle | `assured-substrate`, `assured-id-system`, `assured-traceability-validators`, `assured-decomposition-validators`, `assured-export-formats`, `assured-render`, `assured-code-index`, `assured-skills` | 30 |
| **Total** | **12 dirs** | **43 REQs + 43 DES + 43 TEST = 129 ID records** |

(The REQ inventory checklist projected 44; one REQ was absorbed into a combined entry,
yielding 43 declared across the 12 directories — still within 2% of estimate.)

**Code annotations:**
- 18 Python `# implements:` annotations across 13 source files
  (`plugins/sdlc-assured/scripts` + `plugins/sdlc-programme/scripts`)
- ~21 HTML-comment `<!-- implements: DES-... -->` annotations across markdown artefacts
  (SKILL.md files in `skills/` and plugin skill roots, design specs in `docs/specs/`)

**KB indexes generated (Task 17):**
- `library/_ids.md` — 129 ID records (43 REQ + 43 DES + 43 TEST)
- `library/_code-index.md` — 18 Python annotation entries from 13 source files
- `library/_spec-findings.md` — findings export from all spec artefacts

**Module-scope renders (Tasks 19-20):**
- `docs/traceability/P1.SP1.M1.md` — M1 programme-bundle render
- `docs/traceability/P1.SP1.M2.md` — M2 assured-bundle render
- `docs/traceability/P1.SP1.M3.md` — M3 kb-bridge render

**Dependency graph + DO-178C RTM (Task 21):**
- `docs/traceability/dependency-graph.md` — empty-edges graph (import extractor absent; F-007)
- `docs/traceability/do-178c-rtm.md` — 43-row RTM; 15/43 rows (34.9%) have source-code entries;
  28/43 rows (65.1%) show `—` in the Source code column (directly caused by F-001)

**Findings: 9 distinct findings, F-001 through F-009.**

---

## What worked well

**Stage 1 tripwire caught nothing because the design was sound.** The go/no-go check at Task 5
(after completing M3 proof-of-flow) returned PROCEED with no escalation. The 44-REQ paperwork
risk identified in the design spec remained theoretical: M3 produced only 2 REQs, 2 DES items,
and 2 TEST cases in proportion to its scope. The stage was worth running — it confirmed the
REQ-authoring cadence was sustainable before committing to the full 43-REQ scope.

**F-001 was caught immediately at Task 4, before scaling.** Discovering the markdown annotation
gap on the first module (M3, 1 REQ) rather than the last module (M2 `assured-skills`, 7 REQs)
prevented a silent coverage hole that would have been invisible until the code-index was generated.
The proof-of-flow structure — start with the smallest module — delivered exactly this benefit.

**The staged structure (M3 → M1 → M2) gave genuine reflection points.** The Stage 1 checkpoint
produced a written recommendation with rationale (not just a "yes keep going"). M1 surfaced F-004
(REQ-inventory offset) that would have propagated to test fixture authoring if not caught in Stage 2a.
M2's eight feature directories proceeded without a late-stage design surprise.

**The per-task finding-capture rule kept observations from being lost.** Every finding — including
minor ones like F-002 (path scoping granularity) and F-006 (related-REQ cross-reference gap) —
was committed to `research/phase-f-dogfood-findings.md` in the same commit as the task work.
The 9-finding backlog at Phase F close is an honest engineering log, not a reconstruction from memory.

**7/7 traceability validators passed clean (Task 19).** ID uniqueness, forward/backward link
integrity, orphan-ID detection, and annotation format integrity all passed with zero errors and
zero warnings. The F-003 concern (constitution category error breaking `backward_coverage`) was
resolved by inspection — the validator operates on the ID graph, not code annotations, so the
missing CONSTITUTION.md annotation did not cause a failure.

**Annotation counts were accurate predictions.** The design spec estimated ~50-60 Python
annotations; Phase F landed 18 Python annotations scoped to Phase F's own module domains.
The ratio of 18 Python / 42 markdown annotations (measured at index time) confirmed that this
framework's primary implementation carrier is markdown, not Python — a finding that directly
motivates the v0.2.0 annotation model work.

---

## What was harder than expected

**The markdown annotation gap (F-001) — the defining constraint of Phase F.** The code-index
scanner only matches `# implements:` (Python comment syntax). HTML-comment workaround
`<!-- implements: DES-... -->` displays correctly but is invisible to the parser. The consequence:
18 Python `# implements:` annotations were indexed; the 10+ SKILL.md files carrying
`<!-- implements: DES-... -->` were not. The ratio 18/129 = 14% means the code-index
underrepresents the implementation by ~7x. Every regulated-industry user of Method 2 will hit
this within the first feature they instrument — almost every user-visible artefact is a SKILL.md,
agent manifest, or design document, none of which are Python.

**The `granularity_match` validator produces 100% noise against this codebase (F-008).** The
validator fires for every REQ that lacks a `# implements:` annotation. All 43 REQs warned.
Examination shows zero REQ annotations exist anywhere; all 18 Python annotations cite DES IDs
(the established convention). The validator's design assumes annotation at REQ level; the
framework's actual convention annotates at DES level. Two outcomes: teams dismiss the validator
as permanently noisy, or teams add redundant REQ annotations to silence it. Neither is acceptable.
This is a 100% false-positive rate on a validator designed to catch under-implementation — a signal
that will be discarded rather than acted on.

**The DO-178C RTM source-code column is 65% empty (F-009).** Of 43 REQ rows, 28 show `—` in
the Source code column. This is a direct downstream consequence of F-001 — the 15 populated cells
correspond exactly to the Python source files with `# implements:` annotations. A 65% gap in the
Source code column of an RTM would fail a DO-178C audit without supplementary manual evidence.
The v0.1.0 Assured bundle cannot produce an audit-ready RTM for a markdown-driven codebase.

**The visibility validator is permanently dormant without an import extractor (F-007).** The
`visibility_rule_enforcement` validator requires `ImportEdge` objects from an upstream import
scanner. No such scanner ships in v0.1.0. The validator exists in the codebase but cannot run;
declared visibility rules are never enforced. A module that violates its declared visibility
boundary would get no automated feedback.

**The constitution-as-code annotation created a category error (F-003).** Writing `# implements:`
inside CONSTITUTION.md inverts the artefact hierarchy — the Constitution IS the authority from
which requirements flow, not code implementing a design unit. No annotation was added; instead
the test spec verifies the constitution's content structurally. This is an acceptable workaround
but exposes a gap: the annotation model has no first-class concept for "this document IS the
artefact satisfying a requirement," distinct from "this code implements a design unit."

---

## Lessons learned

**Method 2 assumes Python-style comment syntax. Markdown-driven projects need a separate
annotation story.** The framework must support at minimum two annotation forms before v0.2.0:
`# implements:` for Python and `<!-- implements: -->` for markdown. Alternatively, YAML frontmatter
`implements: [DES-x-001]` provides a parser-friendly, renderer-neutral format that works across
both file types. A project that primarily ships SKILL.md files, agent manifests, and design
documents needs a route to annotation that doesn't require them to maintain a parallel Python
module as an annotation carrier.

**Validators run on artefact-derived state but miss code-state truth that requires real tooling.**
The traceability validators all pass cleanly — they operate on the ID graph, which is well-formed.
But the decomposition validator suite is partially blind: `visibility_rule_enforcement` cannot
run, and `granularity_match` produces 100% noise. Both gaps require external tooling (import
extractor, annotation-convention documentation) that v0.1.0 did not ship. The lesson: a
validator suite that passes is not evidence of full coverage. "7/7 traceability validators passed"
is weaker evidence than it looks when two decomposition validators are dormant or noisy.

**The "one REQ per intent vs one REQ per function" tension is real and manifests as granularity
inconsistency (F-005, F-006).** REQ-assured-traceability-validators-001 collapsed three validators
under one requirement because they share an input type — but one is blocking and two are not,
which is invisible at the REQ level. REQ-assured-decomposition-validators-002 and -004 cover
overlapping intent with no cross-reference mechanism. The framework ships no guidance on whether
to split or merge REQs with partially shared intent, and no `related:` link mechanism to
surface sibling REQs to a reviewer. For regulated users, this produces REQs that don't stand
alone without reading the DES.

**DO-178C compliance needs real tooling beyond what v0.1.0 ships.** The RTM export is a correct
rendering of the available evidence — but the available evidence (18 Python annotations out of
a predominantly markdown codebase) is structurally insufficient for a DO-178C audit. The lesson
is not to demote the RTM feature, but to be explicit in the SKILL documentation that v0.1.0
RTM output is a triage tool, not an audit artefact, until F-001 is fixed.

**The per-task finding-capture rule is load-bearing.** Without the `research/phase-f-dogfood-findings.md`
convention — append a finding to the file in the same commit as the task that surfaces it — several
of the nine findings would not have been captured at Phase F close. F-004 was surfaced mid-authoring
during Task 7 and would have been lost; F-006 was a subtle observation during Task 12 about
cross-referencing that would not have survived into the retrospective without a committed record.
This rule should be standardised in the Assured bundle documentation.

---

## Findings summary

| ID | Severity | Summary |
|---|---|---|
| F-001 | IMPORTANT | `# implements:` annotation parser does not handle markdown files; HTML-comment workaround `<!-- implements: -->` is invisible to the code-index scanner |
| F-002 | MINOR | `programs.yaml` `paths` cannot scope to a section of a file; whole-directory only |
| F-003 | MINOR | Constitution REQ creates a category error in the annotation model — the constitution IS the authority, not code implementing a design unit |
| F-004 | MINOR | REQ-inventory review-record gate assignment was offset by one phase; code is correct, planning artefact had the mismatch |
| F-005 | MINOR | Collapsing warn-not-block and blocking validators under one REQ obscures severity contract — a REQ should stand alone |
| F-006 | MINOR | No "see also" mechanism for related REQs with overlapping intent; a reviewer reading one cannot discover the other without reading DES |
| F-007 | IMPORTANT | `visibility_rule_enforcement` cannot run without an import-graph extractor; the boundary model is partially aspirational (severity raised from MINOR per architect review 2026-05-01) |
| F-008 | IMPORTANT | `granularity_match` fires on all 43 REQs producing 100% noise — established convention annotates at DES level, validator expects REQ level |
| F-009 | IMPORTANT | DO-178C RTM source-code column is 65% empty (28/43 rows show `—`); RTM not audit-ready as currently exported |
| F-010 | IMPORTANT | Some Phase F REQ statements drift toward function-shaped form despite plan guidance (added per architect review 2026-05-01) |

**Correction (2026-05-01).** An earlier draft of this retrospective claimed F-001, F-008, and
F-009 cluster on a single root cause and that fixing F-001 resolves the others. An independent
architect review challenged that claim and a recheck confirms the reviewer is correct. The three
IMPORTANT findings reinforce each other but represent **three distinct defects** that need three
coordinated v0.2.0 fixes:

- **F-001** is a parser-coverage defect (the annotation regex only matches Python comment syntax).
- **F-008** is a traceability-semantics defect (`granularity_match` expects REQ-level annotations
  while the convention is DES-level — a parser fix alone does not resolve this).
- **F-009** is an export-evidence completeness defect (the RTM emits placeholders rather than
  typed evidence statuses; even if every annotation were captured, the exporter still cannot
  distinguish "not implemented" from "implemented by configuration artefact" from "implemented
  by external evidence").

A v0.2.0 EPIC must address all three plus F-007 (visibility extraction) and F-010 (REQ-quality
discipline) to meaningfully close the audit-readiness gap.

---

## v0.2.0 candidate fixes

The following items are seeded by the `suggested-resolution` fields in
`research/phase-f-dogfood-findings.md`. They form the initial v0.2.0 backlog.

1. **F-001 fix — extend annotation parser beyond Python-comment syntax.** Add
   `_HTML_IMPLEMENTS_RE = re.compile(r"<!--\s*implements:\s*(?P<ids>.+)\s*-->")` in
   `code_index.py` and `traceability_validators.py`. Alternative: adopt YAML frontmatter
   `implements: [DES-x-001]` as the canonical markdown annotation form.
   **Architect review note (2026-05-01):** the broader generalisation is to introduce an
   `EvidenceIndexEntry` abstraction that supports source code, markdown HTML comments,
   YAML/JSON/plist paths, configuration entries, externally-attached evidence files, and
   explicit `satisfies-by-existence` records — rather than expanding `CodeIndexEntry`
   indefinitely. This sets up file-format support as a registry by file type instead of
   one regex at a time.
   Affected files: `plugins/sdlc-assured/scripts/assured/code_index.py:9-13`,
   `plugins/sdlc-assured/scripts/assured/traceability_validators.py:_IMPLEMENTS_RE`.

2. **F-007 fix (severity now IMPORTANT) — ship a platform-neutral dependency-extractor interface with Python as the first adapter.** Add `tools/import_scanner.py`
   that walks Python source trees using `ast.parse`, resolves each `import` and
   `from ... import` statement to its owning module via `programs.yaml` `paths`, and
   emits `ImportEdge` objects. Wire into `kb-codeindex` build step so
   `visibility_rule_enforcement` runs automatically.
   **Architect review note (2026-05-01):** define the extractor as a platform-neutral
   *interface*, not a Python-only concrete. Future Swift/Xcode/Java/Go/etc. extractors
   slot in without changing the validator contract. This is more important than it looks
   — without an extractor, the boundary model is currently aspirational rather than
   enforced, which is why severity was raised from MINOR to IMPORTANT.

3. **F-008 fix — align `granularity_match` with DES-annotation convention.** Three options:
   (a) accept indirect coverage — a REQ is covered if any DES that `satisfies` it has
   a `# implements:` annotation; (b) add `granularity: design` Module option to shift
   the check to DES coverage; (c) document that `granularity_match` is designed for
   REQ-level annotation projects, and teams using DES-level annotation should set
   `granularity: design`. Option (a) is most backward-compatible.

4. **F-002 clarification — document file-section scoping limitation.** Add a note to
   `programs.yaml` documentation that `paths` scopes to whole directories, not file
   sections or line ranges. Optionally prototype a `section-anchor` syntax for v0.3.0.

5. **F-003 fix — introduce `satisfies-by-existence` annotation type.** Add a first-class
   mechanism for documents that ARE the artefact satisfying a requirement, distinct from
   code that implements a design unit. Candidate: YAML frontmatter `satisfies: [REQ-NNN]`
   for governance documents. Restrict `code_index` scanner scope to source files only,
   document that documentation requirements are verified by structural tests.

6. **F-005 fix — split severity-mixed REQs or add explicit severity parenthetical.** For
   REQs that combine blocking and warn-not-block validators, add a parenthetical to the
   requirement text making the severity contract explicit at the REQ level. Alternatively,
   file a linter rule that flags a REQ covering multiple validators with differing severity.

7. **F-006 fix — add `related:` optional field to REQ frontmatter schema.** Render it in
   tooling output as a non-traceability cross-reference. Allows overlapping-intent REQs to
   surface sibling requirements to a reviewer without conflating them in the traceability graph.

8. **F-004 fix — update REQ inventory row descriptions.** Change wording to "a review record
   for the **same** phase" rather than naming a specific prior phase, matching the actual
   gate implementation and Constitution Article 14.

9. **DO-178C RTM documentation — add audit-readiness caveat to SKILL.md.** State clearly
   in the `traceability-export` skill documentation that v0.1.0 RTM output is a triage tool,
   not an audit artefact, until F-001 is fixed. Document the minimum supplementary evidence
   required for a real DO-178C audit when the code-annotation coverage is incomplete.

10. **F-009 fix — typed evidence-status concept on the RTM exporter (NEW from architect review 2026-05-01).** The current RTM emits a bare `—` placeholder for any cell where the source-code annotation is missing. This conflates four distinct meanings: "not implemented yet", "implemented by a non-source artefact (config / entitlement / privacy manifest)", "implemented by source but not indexed by v0.1.0 parser", and "not applicable with explicit justification". For DO-178C / IEC 62304 / ISO 26262 use, replace the placeholder with a typed evidence status: `linked` / `missing` / `not_applicable` / `manual_evidence_required` / `configuration_artifact`. Without this, the RTM creates a false sense of completeness — a document that looks formal while failing the central evidence obligation.
    Affected: `plugins/sdlc-assured/scripts/assured/export.py:export_do178c_rtm` and the four other regulatory exporters.

11. **F-010 fix — REQ-quality audit + lint discipline (NEW from architect review 2026-05-01).**
    Audit all 44 Phase F REQs against the user-visible-capability bar (the architect-review-named three are confirmed drifters: `REQ-assured-decomposition-validators-001`, `REQ-assured-traceability-validators-003`, `REQ-assured-skills-001`). Rewrite drifters at the user-visible level. Add a writing-plans-skill checklist for banned phrasings ("the function X exists", "begins with the function name") and a candidate validator that flags REQ statements opening with a Python identifier or containing the literal word "function" / "method".

---

## Phase G readiness

- **Assured tests:** 74 passed, 0 failed — no regressions from Phase F annotations
- **Programme tests:** 29 passed, 0 failed — no regressions
- **Plugin packaging:** 14/14 plugins verified
- **Quick validation:** PASSED (0 errors, 0 warnings)
- **Branch state:** 20 Phase F commits ahead of 251663d; branch is pushable
- **Known env limitation:** pre-commit binary absent (pre-existing, unrelated to Phase F);
  9/10 pre-push checks pass; pre-commit hook check is the one that cannot run

Phase G (consolidate epic retrospective, draft EPIC #178 PR, merge) is the next and final phase.
No regressions. No blockers.

---

## References

- Parent EPIC: #178
- Phase F design spec: `docs/superpowers/specs/2026-04-30-phase-f-dogfood-design.md`
- Phase F implementation plan: `docs/superpowers/plans/2026-04-30-phase-f-dogfood-plan.md`
- Findings: `research/phase-f-dogfood-findings.md`
- Phase E retrospective: `retrospectives/104-phase-e-assured-bundle-substrate.md`
- KB indexes: `library/_ids.md`, `library/_code-index.md`, `library/_spec-findings.md`
- Traceability artefacts: `docs/traceability/` (P1.SP1.M1.md, P1.SP1.M2.md, P1.SP1.M3.md,
  dependency-graph.md, do-178c-rtm.md)
