# Architect Review — Decomposition Spike

## Your Role

You are a senior solution architect reviewing an architectural decomposition spike for the `ai-first-sdlc-practices` repository (an open-source SDLC framework). The spike proposes a candidate `programs / sub-programs / modules` decomposition under DDD bounded-context discipline + Bazel visibility-rule philosophy.

You operate in a fresh container with SDLC plugins installed. Use the `sdlc-team-common:solution-architect` agent (via the Agent tool with `subagent_type="sdlc-team-common:solution-architect"`) for the actual architectural reasoning — this command file briefs the agent and captures their output as your structured review.

Your task is **review and critique, not redesign**. Do not propose alternative decompositions. Surface concrete issues with the one proposed.

## What you're reviewing

Primary input: `research/sdlc-bundles/decomposition-spike.md` (in the worktree).

Read the WHOLE document before reviewing. It has 9 sections:

- 0: executive verdict
- 1: repo character analysis
- 2: candidate `programs` block (YAML)
- 3: per-module DDD analysis
- 4: visibility rules / DAG
- 5: granularity targets
- 6: worked example using `kb-query` cross-library synthesis (PR #177 code)
- 7: failure-mode honest assessment
- 8: verdict and what it means for Phase D-E
- 9: critical review by `sdlc-team-common:solution-architect` and response

**Important**: Section 9 is a previous review by the same agent type that you are now invoking. Your dispatch must:

1. Independently produce findings — read the spike Sections 0-8 first, form your own judgement, then read Section 9 to compare
2. Confirm whether the previous review's verdicts hold under independent dispatch (would you have surfaced the same 8 issues? would you have surfaced different ones?)
3. Surface any issues NOT covered by the previous review

Do not rubber-stamp the previous review. Do not just re-paraphrase it.

## Required context

Before reviewing, also read:

- `research/sdlc-bundles/METHODS.md` — design document defining Method 1 (Programme bundle) and Method 2 (Assured bundle); Method 2 is what the decomposition feeds into
- `library/decomposition-ddd-bazel.md` — curated finding on DDD + Bazel as the chosen primitive
- `library/decomposition-failure-modes.md` — failure modes Method 2 designs against (anaemic contexts, premature decomposition)

You may also walk the repo (using Bash `ls` / `find`) to understand the structure being decomposed.

## What to do

Dispatch the `sdlc-team-common:solution-architect` agent with the prompt below. The agent should answer the 8 questions in this exact order, with verdict labels (AGREE / AGREE-WITH-CONCERNS / DISAGREE / NEEDS-REWORK) per question.

### Prompt to dispatch

```
You are conducting an INDEPENDENT critical review of a decomposition spike at:
research/sdlc-bundles/decomposition-spike.md

A previous review by the same agent type (you, in a different invocation) is in
Section 9 of the spike. Read Sections 0-8 FIRST, form independent findings, then
read Section 9 to determine if your findings agree, differ, or surface new issues.

Required reading: METHODS.md, library/decomposition-ddd-bazel.md,
library/decomposition-failure-modes.md.

Answer these 8 questions, in order, each with a verdict (AGREE /
AGREE-WITH-CONCERNS / DISAGREE / NEEDS-REWORK):

1. DDD bounded-context soundness — are proposed modules actually bounded
   contexts, or directory groupings dressed in DDD language? Where does
   ubiquitous language overlap between modules? Where is it thin or hand-wavy?

2. Acyclicity check — does the source-code DAG hold? Are there hidden circular
   data-flow dependencies the spike author missed? Does Section 9's previous
   review fully cover the runtime data-flow cycle, or are there others?

3. Cross-cutting concerns classification — `release-packaging` is now classified
   as `cross-cutting-producer` and `team-agent-library` as `pragmatic-grouping`.
   Are these classifications correct? Is `documentation-and-examples` correctly
   classified as `derivative-projection`?

4. Anaemic-context risk mitigations — Section 7 lists three risks with
   mitigations. Section 9's response strengthened them. Are the strengthened
   mitigations adequate, or do they still hand-wave?

5. Granularity choices — Section 9 raised `kb-skills-and-orchestration` from
   `function` to `requirement`. Is that the right level? Are other modules'
   granularities defensible?

6. Worked example soundness — Section 6 was rewritten in response to Section 9's
   first-pass review (now annotates 5 functions, surfaces a real coverage gap,
   uses namespaced IDs). Does the rewritten example hold up? Are the IDs
   correctly formatted per METHODS.md schema? Is the coverage-gap finding
   genuine?

7. Source-vs-distribution doubling — Section 9 deferred this to Phase E as a
   schema-design decision (source-paths / derived-paths split). Is that
   deferral reasonable, or should the spike prototype the schema split inline?

8. Verdict pressure-test — is Section 0's revised verdict ("plausible-with-
   revision-required-before-Phase-E") accurate? Or has the spike now resolved
   enough issues that it could ship as unconditional Phase E input?

End with a one-paragraph summary stating whether the spike is good enough to
feed Phase D plan-writing as-is, whether the Phase E schema gaps are correctly
identified and bounded, and whether you (this independent dispatch) found
anything Section 9's previous dispatch missed.

Do NOT propose an alternative decomposition. Do NOT modify files. Return text
only.
```

### Capture output

The agent's response IS your structured review. Save it verbatim to a file the
controller can read after the workflow completes:

```bash
# Write the agent's response (returned via the Agent tool result) to:
research/sdlc-bundles/dogfood-workflows/architect-review-spike-output.md
```

(Note: in the containerised run, you have repo write access to capture the
output. The controller will pick this up after the workflow returns.)

## What NOT to do

- Don't read or echo this command file's content as the review — invoke the agent
- Don't propose an alternative decomposition
- Don't modify the decomposition spike or any other source file
- Don't dispatch other agents besides `sdlc-team-common:solution-architect`
- Don't run validation, tests, or lint — this is a design review

## Done criteria

The workflow node is done when:
- The agent has been dispatched
- The agent's verbatim response is written to `research/sdlc-bundles/dogfood-workflows/architect-review-spike-output.md`
- The agent returned at least 8 verdict labels (one per question)
- The agent stated explicit agreement / disagreement with Section 9's previous review
