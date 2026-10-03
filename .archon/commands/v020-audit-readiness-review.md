# v0.2.0 Phase G Audit-Readiness Review

## Your Role

You are a senior solution architect conducting an INDEPENDENT review at the
close of EPIC #188 (sdlc-assured v0.2.0). Your job is to validate the
audit-readiness claim made in the EPIC retrospective: that v0.2.0 closes
F-001 / F-007 / F-008 / F-009 / F-010 plus the carry-forward items from
EPIC #178 Phase F dogfood.

You operate in a fresh container with SDLC plugins installed. Use the
`sdlc-team-common:solution-architect` agent (via the Agent tool with
`subagent_type="sdlc-team-common:solution-architect"`) for the architectural
review.

## What you're reviewing

Primary inputs:

- `retrospectives/188-v020-assured-improvements.md` — the EPIC retrospective
  whose audit-readiness claim is under review.
- `research/v020-acceptance-metrics.md` — Phase G sub-stage 3 hard-gate
  evaluation, including the post-corpus-retrofit numbers.
- `research/v020-baseline-metrics.md` — Phase G sub-stage 1 baseline.
- `research/v020-req-quality-audit.md` — Phase E REQ-quality audit, including
  the 6 deferred drifters scheduled for v0.3.0.
- `research/phase-de-deviation-ledger.md` — F4 re-audit verdict (Phase F
  task 32) plus prior deviation history.

Required code reading (the v0.2.0 deliverables):

- `plugins/sdlc-assured/scripts/assured/evidence_index.py` — F-001 abstraction
- `plugins/sdlc-assured/scripts/assured/evidence_adapters.py` — F-001 adapters
- `plugins/sdlc-assured/scripts/assured/evidence_status.py` — F-009 typed status
- `plugins/sdlc-assured/scripts/assured/requirement_metadata.py` — F-009 registry
- `plugins/sdlc-assured/scripts/assured/dependency_extractor.py` — F-007 protocol
- `plugins/sdlc-assured/scripts/assured/decomposition.py` — F-008 indirect
  coverage rewrite + E2 forward_annotation_completeness
- `plugins/sdlc-assured/scripts/assured/export.py` — exporter migration to
  EvidenceIndexEntry + RequirementMetadata
- `tools/validation/check-req-quality.py` — F-010 lint candidate

Required spec reading (the v0.2.0 spec changes):

- `docs/superpowers/specs/2026-05-01-v020-assured-improvements-design.md`
- `docs/superpowers/specs/2026-05-01-v020-design-decisions.md` (Phase A)
- `docs/specs/assured-traceability-validators/{requirements,design,test}-spec.md`
  — F-005 split (REQ-005 / DES-005 / TEST-005)
- A sample of `docs/specs/<feature>/requirements-spec.md` files showing the
  retrofitted `**Evidence-Status:**` and `**Justification:**` fields.

## What to do

Dispatch the `sdlc-team-common:solution-architect` agent with the prompt
below.

### Prompt to dispatch

```
You are conducting an INDEPENDENT architectural review at the close of EPIC
#188 (sdlc-assured v0.2.0). Your verdict will determine whether v0.2.0 is
audit-ready or whether further work is required before merge.

Read in this order:
1. retrospectives/188-v020-assured-improvements.md (the claim under review)
2. research/v020-acceptance-metrics.md (the hard-gate evaluation, post-retrofit)
3. research/v020-baseline-metrics.md (the baseline)
4. research/v020-req-quality-audit.md (Phase E F-010 audit, 6 v0.3.0 deferrals)
5. research/phase-de-deviation-ledger.md (F4 re-audit verdict)

Then sample the v0.2.0 deliverable code in plugins/sdlc-assured/scripts/assured/
and a few retrofitted requirements-spec.md files under docs/specs/.

Answer 6 questions. For each: AGREE / AGREE-WITH-CONCERNS / DISAGREE / NEEDS-REWORK with rationale.

Q1. F-001 closure (markdown / non-Python evidence): does the
EvidenceIndexEntry + EvidenceAdapter + EvidenceIndexRegistry abstraction in
evidence_index.py + evidence_adapters.py actually close the F-001 gap, or
is it a thin facade over the old Python-comment-only path?

Q2. F-007 closure (platform-neutral dependency-extractor interface): does
the DependencyExtractor protocol in dependency_extractor.py — with
PythonAstExtractor as the production adapter and make_swift_extractor() as
proof of language-neutrality — actually validate the abstraction, or is the
Swift fixture so trivial that it does not exercise the interface meaningfully?

Q3. F-008 closure (indirect DES-mediated coverage): does the granularity_match
rewrite in decomposition.py — accepting the satisfies_graph parameter and
walking REQ → DES inverse_satisfies — correctly model the "REQ has evidence
when at least one satisfying DES has evidence" rule? Are there edge cases
(e.g., circular satisfies, multi-hop chains) the implementation does not
handle?

Q4. F-009 closure (typed evidence statuses): does the EvidenceStatus enum
combined with RequirementMetadata + the exporter migration actually deliver
audit-readiness? Is "every gap cell typed" a meaningful audit-readiness
property, or is MANUAL_EVIDENCE_REQUIRED a way to game the gate? In particular:
of the 30 retrofitted gap REQs, are the MANUAL_EVIDENCE_REQUIRED
classifications honest (skill workflows that genuinely have no annotatable
function) or evasive?

Q5. F-010 closure (REQ-quality discipline): does the audit + 10 inline
rewrites + 6 deferrals + check-req-quality.py linter actually shift the
corpus toward capability-shaped REQs, or is the deferral list a sign that
v0.2.0 only addressed the easy cases? Read at least 2 of the deferred
drifters and 2 of the rewritten REQs to compare.

Q6. Phase G hard-gate honesty: the Phase G hard gates passed only after a
corpus retrofit (Task 36A) closed the 68% RTM gap to 4.55%. Is the post-
retrofit measurement honest (the retrofit added real annotations and real
typed-status fields), or did it close numbers without closing the underlying
audit gap?

Then SUMMARY: is v0.2.0 audit-ready (i.e., does the retrospective's claim
hold)? Are there hidden gaps the EPIC retrospective missed? What is the
single most important thing v0.3.0 should pick up first?

End by writing your verbatim review to:
research/sdlc-bundles/dogfood-workflows/v020-audit-readiness-review-output.md

Read-only review. Do NOT modify code or specs.
```

## Done criteria

- The agent has been dispatched.
- The agent's verbatim response is written to
  `research/sdlc-bundles/dogfood-workflows/v020-audit-readiness-review-output.md`.
- The agent returned 6 verdict labels (one per question) plus a summary.
- The agent stated whether v0.2.0 is audit-ready and named the v0.3.0
  carry-forward priority.
