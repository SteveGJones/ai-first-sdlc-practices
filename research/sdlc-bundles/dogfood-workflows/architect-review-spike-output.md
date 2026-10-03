# Independent Critical Review of Decomposition Spike

**Reviewer**: `sdlc-team-common:solution-architect` (independent dispatch)
**Date**: 2026-04-27
**Input**: `research/sdlc-bundles/decomposition-spike.md` Sections 0-8, then Section 9
**Required reading**: METHODS.md, library/decomposition-ddd-bazel.md, library/decomposition-failure-modes.md

---

## 1. DDD bounded-context soundness

**Verdict: AGREE-WITH-CONCERNS**

The four content sub-programs (`framework-core`, `knowledge-base-system`, `workflows-system`, `framework-meta-sdlc`) are genuine bounded contexts. They have distinct ubiquitous languages that do not substantially overlap, and the domain models they describe are coherent. Section 9's reclassification of `team-agent-library` as `pragmatic-grouping` and `documentation-and-examples` as `derivative-projection` was correct and I agree those are not real bounded contexts.

However, I have two concerns that Section 9 only partially addressed:

(a) The ubiquitous language overlap between `librarians` and `kb-skills-and-orchestration` is more significant than the spike acknowledges. Both modules use "attribution", "finding", "citation", "synthesis", and "shelf-index". The spike's response that "they operate at different abstraction levels" is asserted but not demonstrated structurally -- there is no context map declaring the relationship between these two modules within the same sub-program. The hexagonal `structure: hexagonal` annotation on both modules hints at port/adapter separation, but that is within-module structure, not between-module boundary definition. This is not fatal -- they are within the same sub-program, so coupling is expected -- but the DDD analysis should be honest that these two modules share a ubiquitous language and are separated by implementation concern (agents vs skills+Python), not by domain boundary.

(b) The `framework-core / core-agents` module's boundary claim that it "does NOT depend on core-skills directly -- invokes them by command name" is structurally correct for markdown agents but is a DDD sleight-of-hand. Command-name invocation IS a dependency; it just happens to be loosely coupled. The DAG captures this correctly (core-agents depends on constitution-and-rules and validators), but the prose in Section 3 understates the relationship.

## 2. Acyclicity check

**Verdict: AGREE-WITH-CONCERNS**

The source-code DAG holds. Section 9 correctly identified the runtime data-flow cycle between `framework-research` and `kb-skills-and-orchestration`, and the spike now documents it and flags it for Phase E `known-violation` handling. I agree with that analysis.

However, there is a second quasi-cycle that neither the spike author nor Section 9 surfaced: `release-packaging` is classified as a `cross-cutting-producer` that "writes into other sub-programs' distribution paths via release-mapping." But the plugin-dir mirrors it produces are then declared as `paths:` (or `derived-paths:` in the case of `kb-skills-and-orchestration`) belonging to those other sub-programs' modules. Meanwhile, `release-packaging / plugin-validation` (`check-plugin-packaging.py`) reads the output of `release-packaging / release-mapping` to verify it. This is not truly circular in the code sense, but the data-flow is: release-packaging reads sources from all sub-programs, produces derived paths that are attributed to those sub-programs, and then release-packaging's validator reads those derived paths to verify consistency. The `source-paths` / `derived-paths` split deferred to Phase E will partially address this, but the spike should acknowledge that the `cross-cutting-producer` classification creates a special validator challenge: any module-bound-check that naively scans `derived-paths` will find code "owned" by modules that did not produce it. Section 9's deferral to Phase E is reasonable, but it underestimates the subtlety.

## 3. Cross-cutting concerns classification

**Verdict: AGREE**

`release-packaging` as `cross-cutting-producer` is correct. It reads from all other sub-programs and produces derived outputs. It is not a consumer in the DDD sense (it does not depend on the domain models of other sub-programs; it depends only on their filesystem layout).

`team-agent-library` as `pragmatic-grouping` is correct. The agents within do not share a single ubiquitous language; they are a catalog organized by team type.

`documentation-and-examples` as `derivative-projection` is correct. It reads from everything, mutates nothing, and its content types (guide, example, how-to) are not domain concepts.

## 4. Anaemic-context risk mitigations

**Verdict: AGREE-WITH-CONCERNS**

The strengthened mitigations are materially better than the original draft's. Specifically:

- Risk 1 (release-plugin skill crossing module boundaries): the call for a cross-module-mutation validator is the right shape. This is no longer hand-waving; it is a concrete Phase E deliverable with a clear acceptance criterion ("code that writes to paths declared by another module must carry a cross-module `implements:` annotation").

- Risk 2 (framework-research dogfood loop): the procedural mitigation ("run kb-rebuild-indexes when kb-skills change") combined with the `known-violation` schema field is adequate. The coupling is architecturally intentional and cannot be eliminated. I agree.

- Risk 3 (team-agent-library coarseness): the `anaemic-context-detection: suppressed` declaration is honest and makes the consequence visible. The justification (agents are a catalog, not interacting components) is sound.

My concern is that Risk 1's mitigation defers entirely to Phase E. The spike could have included a concrete example of what a "cross-module-mutation validator" check looks like -- e.g., "when `release-plugin` skill writes to `plugins/sdlc-core/agents/`, it must carry `# cross-module: release-packaging.release-mapping`". Without even a sketch, Phase E implementers have to invent the annotation format from scratch. This is a minor concern; the direction is correct.

## 5. Granularity choices

**Verdict: AGREE**

Raising `kb-skills-and-orchestration` from `function` to `requirement` is correct. The orchestrator contains behavioural rules (synthesis detection, attribution post-check, dispatch formatting) that are themselves requirements, not mere helper functions. At `function` granularity, internal helpers could hide under a single entry-point annotation; at `requirement` granularity, each behavioural rule must be a named REQ, which the worked example in Section 6 demonstrates.

The other granularity choices are defensible:

- `constitution-and-rules` at `requirement` -- each article IS a requirement. Correct.
- `validators` at `function` -- each validator is a focused function. Correct.
- `team-*` at `module` -- per-agent annotation would be overkill for a catalog. Correct.
- `kb-templates` at `module` -- templates are not REQ/DES/TEST/CODE-shaped. Correct.
- `epic-and-feature-tracking` and `framework-research` at `requirement` -- each feature proposal and each curated finding IS a requirement-shaped record. Correct.

I see no granularity that is obviously wrong.

## 6. Worked example soundness

**Verdict: AGREE-WITH-CONCERNS**

The rewritten worked example is substantially better than what Section 9 described as the original. It now annotates all five participating functions (`run_synthesis_query`, `is_synthesis_query`, `format_synthesis_prompt`, `format_dispatch_prompt`, `check_synthesis_attribution`), and all five functions exist in the actual codebase at the declared paths (`plugins/sdlc-knowledge-base/scripts/orchestrator.py` and `plugins/sdlc-knowledge-base/scripts/attribution.py`).

The coverage gap finding is genuine: REQ-005 ("synthesis prompts MUST format dispatch sources via a single canonical template") has DES-004 and two code annotations (`format_synthesis_prompt`, `format_dispatch_prompt`) but no dedicated TEST-id. Tests for REQ-001 and REQ-002/003 exercise these functions indirectly, but no test specifically validates prompt formatting in isolation.

**ID format concern**: The IDs use `aisp.kb.kbsk.<TYPE>-NNN`, where `aisp` abbreviates the program name `ai-first-sdlc-practices`, `kb` abbreviates the sub-program `knowledge-base-system`, and `kbsk` abbreviates the module `kb-skills-and-orchestration`. METHODS.md Section 4 specifies the canonical format as `<program>.<sub-program>.<module>.<type>-<num>` with the example `P1.SP2.M3.REQ-007`. The spike's abbreviation scheme (`aisp`, `kb`, `kbsk`) is reasonable but is NOT the same format as METHODS.md's example, which uses positional identifiers (`P1`, `SP2`, `M3`). The spike declares this is "per METHODS.md Section 4 canonical schema" but the format is actually a creative interpretation of it. Phase E must decide: are module identifiers positional (`P1.SP2.M3`) or named (`aisp.kb.kbsk`)? The spike implicitly chose named, which is arguably better for human readability, but METHODS.md's example suggests positional. This is a schema gap that Section 9 did not fully resolve -- the review noted the format was fixed, but did not note the positional-vs-named divergence from METHODS.md.

## 7. Source-vs-distribution doubling

**Verdict: AGREE-WITH-CONCERNS**

Deferring the `source-paths` / `derived-paths` schema split to Phase E is reasonable. The spike correctly identifies the problem, and the `kb-skills-and-orchestration` module already prototypes the split in Section 2's YAML (it is the only module that uses `source-paths:` and `derived-paths:` instead of `paths:`). So the spike has partially prototyped the schema inline, even while deferring full design.

My concern is that only ONE module uses the split format, while the problem affects many modules. The `framework-core / core-skills` module lists both `skills/validate/` (source) and `plugins/sdlc-core/skills/` (derived) under a single `paths:` key. Same for `core-agents`, `librarians`, and `workflow-engine-integration`. Phase E will need to retrofit the split across all affected modules, not just `kb-skills-and-orchestration`. The spike should have been explicit that the `kb-skills-and-orchestration` module's format is the prototype and that all modules with plugin-dir mirrors need the same treatment.

## 8. Verdict pressure-test

**Verdict: AGREE-WITH-CONCERNS**

The revised verdict ("plausible-with-revision-required-before-Phase-E") is accurate. The spike has NOT resolved enough issues to ship as unconditional Phase E input. The four schema gaps (source-paths/derived-paths split, known-violation field, cross-module-mutation validator, anaemic-context-detection opt-out) are real and must be closed. Phase D plan-writing can use the spike as-is because plan-writing does not need validator-ready schemas; it needs module boundaries and granularity targets, which the spike provides.

However, I would not say the spike is entirely clean for Phase D either. The coverage gap I found (see below) means the `programs` block YAML itself has missing paths, which could mislead Phase D plan-writing about what is actually in scope for each module.

---

## Summary

The spike is good enough to feed Phase D plan-writing, with one caveat. The four Phase E schema gaps identified in Section 9 are correctly identified and reasonably bounded -- they are genuine schema-design decisions, not fundamental decomposition flaws, and deferring them to Phase E is appropriate.

**What this independent review found that Section 9 missed:**

1. **Material `paths:` coverage gap in the `programs` block YAML.** Multiple agent source directories that exist on disk and are actively mapped by `release-mapping.yaml` to plugins are not covered by any module. Specifically: `agents/testing/` (contains `code-review-specialist.md`, `ai-test-engineer.md`, `integration-orchestrator.md`, `performance-engineer.md` -- mapped to `sdlc-core`, `sdlc-team-ai`, `sdlc-team-common`), `agents/ai-builders/` (5 agents mapped to `sdlc-team-ai`), `agents/ai-development/` (10 agents mapped to `sdlc-team-ai`), `agents/delegation/` (1 agent mapped to `sdlc-workflows`), `agents/documentation/` (2 agents mapped to `sdlc-team-docs`), and `agents/project-management/` (4 agents mapped to `sdlc-team-pm`). These directories are neither listed in any module's `paths:` nor in the "out-of-scope filesystem locations" section. This means a `module-bound-check` validator running against this `programs` block would flag these directories as orphan code -- or worse, silently miss them. The fix is straightforward (add `agents/testing/` to `core-agents` or `team-agent-library`; add `agents/ai-builders/`, `agents/ai-development/` to a team-ai module; add `agents/delegation/` to `workflows-system`; add `agents/documentation/` and `agents/project-management/` to their respective team modules), but it should be done before Phase D uses the `programs` block for scope decisions.

2. **Positional-vs-named ID format divergence.** The worked example uses named identifiers (`aisp.kb.kbsk`) while METHODS.md's canonical example uses positional (`P1.SP2.M3`). This should be flagged as a fifth schema gap for Phase E to resolve.

3. **`release-packaging` cross-cutting-producer creates a subtle validator challenge** around derived-path ownership that Section 9's deferral to Phase E underestimates. The `module-bound-check` validator must understand that derived paths are owned by release-packaging for production purposes but attributed to other modules for traceability purposes.

Section 9's previous dispatch did strong work on structural and schema-level issues. This independent dispatch confirms all 8 of its verdicts directionally (no DISAGREE on any point where Section 9 agreed or agreed-with-concerns) while surfacing the filesystem coverage gap and ID format divergence as genuinely new findings.
