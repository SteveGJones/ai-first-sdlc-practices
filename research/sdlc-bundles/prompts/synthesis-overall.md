# Stage 3 Prompt — Overall Synthesis (Cross-Line)

## How to use this prompt

Run this AFTER all three per-line syntheses are complete and saved at:

- `research/sdlc-bundles/synthesis/01-traceability-synthesis.md`
- `research/sdlc-bundles/synthesis/02-decomposition-synthesis.md`
- `research/sdlc-bundles/synthesis/03-alm-synthesis.md`

The output of this prompt lands at `research/sdlc-bundles/synthesis/overall-scope-update.md` and is the **single document** we use to update the design spec for Programme + Assured bundles before writing the implementation plan.

Run this in Claude Code or Claude Desktop. If in Desktop, paste all three per-line synthesis files alongside this prompt. If in Claude Code, the controller can read all three files directly and pass their content into the synthesis.

---

## Prompt

> **Required context**: this prompt assumes the contents of `research/sdlc-bundles/METHODS.md` are present in the conversation. METHODS.md describes the framework, Method 1 (Programme bundle), Method 2 (Assured bundle), the existing substrate, and out-of-scope boundaries. If METHODS.md is not in the conversation, paste it before this prompt.

You are producing the **scope-update document** that consolidates findings from three independent research lines into a single set of design decisions for the Programme and Assured bundles defined in METHODS.md Sections 3 and 4.

Each research line was synthesised separately into a per-line synthesis document. Your task is **cross-line consolidation**: identify where findings agree, where they conflict, and what the integrated set of design decisions should be.

### Inputs

- **Per-line synthesis 1**: `research/sdlc-bundles/synthesis/01-traceability-synthesis.md` — informs Assured bundle's traceability rigour
- **Per-line synthesis 2**: `research/sdlc-bundles/synthesis/02-decomposition-synthesis.md` — informs Method 2's decomposition primitive choice
- **Per-line synthesis 3**: `research/sdlc-bundles/synthesis/03-alm-synthesis.md` — informs which patterns from existing tools to adopt and avoid

[paste the content of all three per-line synthesis documents here, with clear section markers like `--- SYNTHESIS 1 START ---` ... `--- SYNTHESIS 1 END ---`]

### Existing scope draft for context

The Method 1 + Method 2 scope draft is `research/sdlc-bundles/METHODS.md` (paste its full content alongside the three per-line synthesis files when running this prompt). All scope-change pointers in the output must reference specific sections / subsections of METHODS.md — e.g. "METHODS.md Section 3 'Method 1 in detail' → 'Phase gates' subsection".

### Your output

Produce a single document with these sections.

**Section 1 — Cross-line agreement.**

Findings that appear consistently across two or more research lines. These are the highest-confidence design decisions because they're triangulated from independent sources. Each entry:

```
**Cross-cutting finding**: [the finding, restated as a design implication]
**Lines agreeing**: [which synthesis docs surface this — e.g., "Lines 1 and 3 both emphasise audit-grade evidence forms"]
**Combined confidence**: [HIGH if two lines agree, VERY HIGH if three]
**Design decision**: [what we should now build / change / clarify, integrating both perspectives]
**Affected scope sections**: [pointers]
```

Aim for 4-8 such entries.

**Section 2 — Cross-line conflicts.**

Findings that disagree across research lines. These need explicit resolution. Each entry:

```
**Conflict**: [the disagreement, framed precisely]
**Position from Line A**: [...]
**Position from Line B**: [...]
**Resolution**: [which position wins, or how the framework accommodates both]
**Reasoning for resolution**: [why this is the right call]
**Affected scope sections**: [pointers]
```

If there are zero conflicts, say so explicitly — it's a finding in itself (the research lines may be too disjoint to interact, which is its own scope concern).

**Section 3 — Integrated scope changes for Method 1 (Programme bundle).**

The full set of changes to the Method 1 scope, drawn from all three syntheses. Format:

```
**Scope section**: [exact reference]
**Change**: [add | remove | clarify | replace]
**Driving findings**: [Line N synthesis Section X entry Y, plus any cross-line agreement from Section 1 above]
**Replacement text or new content**: [...]
```

Aim for 4-10 changes for Method 1.

**Section 4 — Integrated scope changes for Method 2 (Assured bundle).**

Same format as Section 3, for the Method 2 scope. Method 2 typically has more changes because it's more research-shaped.

Aim for 6-15 changes for Method 2.

**Section 5 — Decomposition primitive — final call.**

Specifically address the Method 2 decomposition design question. Based on Line 2's synthesis, name the chosen decomposition primitive (e.g., "borrow Bazel's package + visibility rule discipline; ignore the build-system enforcement; enforce via filesystem-path-and-registry validators instead"). Justify it. State the explicit failure mode the framework will design against (which failure mode from Line 2's research is the highest risk for our shape).

500-1,000 words. This is the single highest-stakes design call in Method 2; treat it as such.

**Section 6 — Traceability rigour calibration — final call.**

Based on Line 1's synthesis, state the calibration of Assured's traceability obligations: which standards' baseline obligations the framework will natively support, which it will support via documented extension points, and which it will explicitly disclaim. Include a one-paragraph "what we will NOT promise" so the bundle's scope is honest about its limits.

400-800 words.

**Section 7 — sphinx-needs adoption boundary.**

Based on Line 3's synthesis, state precisely what the framework will adopt from sphinx-needs and what it will deliberately do differently. Include a "shapes-the-framework-takes-from-sphinx-needs" list and a "shapes-we-decline" list. The objective is to not accidentally re-implement sphinx-needs while also not ignoring what sphinx-needs has learned.

400-700 words.

**Section 8 — Reference discipline for the framework's own artefacts.**

Based on the citation discipline used in this research campaign, propose how the framework's own artefacts (specs, requirements, design records) should reference their sources. Should requirements cite their origin (research, business decision, regulatory clause)? Should design records cite their requirements? What about the synthesis layer — should the framework's own decisions cite back to the research that informed them?

This is a **meta-decision** the research campaign itself raises: if we're shipping a framework that values reference discipline, the framework's own internal documentation should model the discipline.

300-500 words.

**Section 9 — Open questions remaining for stage-4 (post-research).**

What design decisions still cannot be made from the available research and synthesis? For each:

```
**Question**: [...]
**Why it can't be answered now**: [no usable evidence, conflicting expert opinion, depends on prototype experiment]
**Resolution path**: [follow-up research, prototype, accept and document the uncertainty as a v1 limitation]
**Blocks**: [yes if it blocks plan-writing; no if it can be left for plan-writing or implementation]
```

Be honest. If the research has resolved most decisions, this section is short. If significant uncertainty remains, this section is the call to do another research round.

**Section 10 — Recommended next action.**

A single paragraph stating what should happen next:

- (a) Update the design spec with these scope changes and proceed to writing-plans.
- (b) Run a stage-2 follow-up on specific open questions before updating the spec.
- (c) Pause and re-scope at the EPIC level because the research surfaced fundamental issues with the proposed bundles.

Justify the recommendation in 100-200 words.

### Reference discipline for the overall synthesis

- Every claim in this overall synthesis must trace back through a per-line synthesis to the original research output. Use the form `[Line N: Section X entry Y]` to cite back through the synthesis chain.
- Cross-line agreements must explicitly cite both contributing lines.
- Do not introduce findings not present in any per-line synthesis. The chain is research → per-line synthesis → overall synthesis; nothing else gets in.
- If the per-line syntheses themselves had quality issues (low-confidence findings, source-quality concerns), propagate that uncertainty here. Do not launder LOW-confidence findings into HIGH-confidence ones by combining them.

### What to avoid

- Do not produce a "summary of summaries". The deliverable is integrated decisions, not aggregated bullets.
- Do not duck the conflicts. Section 2 is mandatory; if you find no conflicts, that's a positive finding to note, but you must look for them.
- Do not punt the decomposition primitive call (Section 5). It's the highest-stakes design decision and the research was specifically commissioned to inform it.
- Do not write Sections 3 and 4 as a list of "we should consider...". Each scope change is a *decision*, not a possibility.
- Do not produce a final "Recommended next action" of "do more research" without specific resolution paths in Section 9. Don't punt; either we have enough or we list what specifically we need.

### Length

Target document length: 4,000-7,000 words. Sections 3, 4, 5, 6, 7 carry the deliverable weight.
