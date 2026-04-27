# Feature Proposal: Phase B — Decomposition Spike

**Proposal Number:** 180
**Status:** In Progress
**Author:** Steve Jones (commissioning), Claude (drafting)
**Created:** 2026-04-26
**Target Branch:** `feature/sdlc-programme-assured-bundles`
**EPIC:** #178 (Joint Programme + Assured bundle delivery)
**Sub-feature:** #180 (Phase B of #178)

---

## Summary

Propose a candidate `programs` block decomposition for the `ai-first-sdlc-practices` repository itself. This is the spike that derisks Phases D-E (Programme + Assured bundle implementation) by establishing that **declared decomposition is workable on a real codebase before we build the validators that enforce it**.

Output is a markdown document at `research/sdlc-bundles/decomposition-spike.md` with the candidate decomposition, DDD bounded-context analysis, visibility rules, granularity targets, a worked example against an existing skill or agent, and an honest failure-mode assessment.

## Sub-features

None — Phase B is a single deliverable.

## Motivation

Method 2's promise depends on someone declaring a sensible decomposition. The framework explicitly does NOT suggest decompositions; the team declares them. When we dogfood Programme + Assured on this repo (Phase F), we have to decompose this repo into programs / sub-programs / modules — and we do not yet have an answer for that.

Doing the spike before Phase D-E surfaces three classes of issue early:

1. **Decomposition declaration is hard work.** Where do module boundaries actually go in our repo? The framework's commissioning guidance will say "defer decomposition; start P1.SP1.M1.*" but at some point teams *do* decompose. We need to do it once for our own repo to learn the actual cost.
2. **Anaemic-context risk is real.** The decomposition spike will surface places where logic *is* scattered today (across plugins, across sdlc-core/team/lang plugins). Method 2's validators would flag these as anaemic. The spike either reshapes the decomposition or accepts the anaemia as a known limitation.
3. **The validator design surface gets concrete.** Until we have a real `programs` block, the validators are abstractions. With a real decomposition, we know exactly what the validators must check.

## Proposed Solution

### Single deliverable: `research/sdlc-bundles/decomposition-spike.md`

Document containing:

**1. Candidate `programs` block** — the proposed decomposition in the YAML form expected by Method 2's commissioning. Example shape:

```yaml
programs:
  framework-core:
    sub-programs:
      enforcement:
        modules:
          constitution:
            paths: [CONSTITUTION.md]
            granularity: requirement
          validators:
            paths: [tools/validation/]
            granularity: function
      knowledge-base:
        modules:
          librarian:
            paths: [agents/knowledge-base/, plugins/sdlc-knowledge-base/agents/]
            granularity: requirement
          kb-skills:
            paths: [skills/kb-*/, plugins/sdlc-knowledge-base/skills/]
            granularity: function
  team-plugins:
    sub-programs:
      role-agents:
        modules:
          # ... etc.
```

(Exact shape is the spike's output; the example is illustrative.)

**2. DDD bounded-context analysis per module** — for each proposed module:
- Ubiquitous language (what terms mean *in this context*)
- Domain model (what concepts are first-class)
- Team responsibility scope (who owns this module's evolution)
- Boundary with neighbouring modules (where the seams are)

**3. Visibility rules** — DAG of which modules may depend on which. Express as a markdown table or simple list. Initial proposal acceptable; ratification at Phase D-E.

**4. Granularity targets per module** — `granularity: [requirement | function | module]` for each module in the decomposition. Default `requirement`; deviations explicitly justified.

**5. Worked example** — pick one existing skill or agent (candidates: `kb-query` skill, `sdlc-enforcer` agent, `phase-review` from Programme bundle when it exists) and walk through:
- What REQ-IDs would be assigned
- What DES-IDs would be assigned
- What TEST-IDs would link to which REQ + DES
- Where annotations would land in the existing code
- What `traceability-render` output would look like for that module

This is the most important section — it's the proof-of-concept for the whole approach.

**6. Failure-mode honest assessment** — does this decomposition trigger the failure modes from `library/decomposition-failure-modes.md`?
- Anaemic contexts: where is logic likely to scatter?
- Premature decomposition: are we over-decomposing already?
- Cross-module dependency proliferation: what's the dependency density?
- Boundary leaks: which proposed modules have hand-wavy boundaries?

If the assessment shows the decomposition is brittle, **say so**. The spike's value is honest signal — a "this won't work" finding is as useful as a "this will work" finding.

### Definition of "good enough"

Either:
- **(a) Plausible decomposition**: proceeding with Phase D-E carries acceptable risk, OR
- **(b) Decomposition reshapes the framework**: the spike shows the repo can't sensibly be decomposed under the proposed primitive, which is itself a finding that informs Method 2's commissioning guidance ("not every project benefits from decomposition; here's how to recognise yours doesn't")

Either outcome resolves the spike. Failure mode of the spike is *not deciding* — that pushes uncertainty into Phase D-E.

## Success Criteria

- [ ] Candidate `programs` block covers all directories in the repo (no orphan paths)
- [ ] Each module has a clear domain owner (single team or sub-team responsibility)
- [ ] Visibility rules form a DAG (no circular dependencies between programs)
- [ ] Worked example cites real existing files (skill or agent already in the repo)
- [ ] Failure-mode assessment is honest — brittle decomposition acknowledged where present
- [ ] Spike output reviewed against `library/decomposition-ddd-bazel.md` and `library/decomposition-failure-modes.md`
- [ ] Final assessment states clearly: (a) proceed with Phase D-E, or (b) reshape Method 2's commissioning guidance based on what the spike learned
- [ ] Pre-push validation passes (documentation only)

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Decomposition spike reveals fundamental issues with our repo's structure | Phase D-E plan needs reshaping | This is the spike's purpose; reshape decision lands in Phase A's design spec update |
| Spike is too theoretical without code annotations | Worked example doesn't validate the approach | Worked example must reference real existing files; if no real file fits, that's a finding |
| Team scope of modules is unclear (we're solo-developing this repo) | Module boundaries become "what's near each other" rather than "responsibility scope" | Acknowledge in failure-mode assessment; commissioning guidance for solo-developed projects becomes its own consideration |
| Spike effort exceeds half a day | Phase A and Phase B run together longer than expected | Time-box: 1 day max for spike; if not converged, ship the work-in-progress as the spike output and call out unresolved questions |

## Out of scope

- Implementing the decomposition (no validator changes, no `programs` block in `.sdlc/team-config.json`)
- Dogfooding the bundles against this decomposition (Phase F)
- Settling visibility-rule arguments definitively (initial proposal acceptable)
- Authoring all code annotations for the worked-example module (worked example demonstrates pattern, not full coverage)

## Dependencies

- Phase A design spec update (#179) — recommended completion first so spike works against current scope, but not a hard blocker
- DDD + Bazel decomposition primitive: `library/decomposition-ddd-bazel.md` — ✅ committed
- Decomposition failure modes: `library/decomposition-failure-modes.md` — ✅ committed
- Synthesis Section 5 (decomposition primitive — final call): `research/sdlc-bundles/synthesis/overall-scope-update.md` — ✅ committed

## Implementation plan

Single phase, executed inline:

1. Walk the repo's top-level directories and characterise their domain content
2. Group directories into proposed modules; group modules into sub-programs; group sub-programs into programs
3. For each module, write the DDD analysis (ubiquitous language, domain model, team scope)
4. Construct the visibility-rule DAG and verify acyclicity
5. Set granularity targets per module with justification
6. Pick a worked example (skill or agent), trace REQ/DES/TEST/CODE annotations
7. Run the failure-mode assessment honestly
8. Commit `research/sdlc-bundles/decomposition-spike.md`
9. Complete Phase B retrospective

## Closing the phase

When all Success Criteria are checked, mark issue #180 closed and reference the commit SHA(s). The decomposition spike output informs (but does not gate) Phase D-E plan-writing.

## References

- Parent EPIC: #178
- Phase A: #179 (recommended to complete first; not a hard prerequisite)
- DDD + Bazel decomposition: `library/decomposition-ddd-bazel.md`
- Decomposition failure modes: `library/decomposition-failure-modes.md`
- Synthesis Section 5: `research/sdlc-bundles/synthesis/overall-scope-update.md`
