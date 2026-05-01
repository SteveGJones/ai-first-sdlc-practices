# Research Plan — Programme + Assured SDLC Bundles

**EPIC context:** EPIC #97 (Multi-Option Commissioned SDLC), sub-features Programme (#103) and Assured (#104), shipping together.
**Branch:** `feature/sdlc-programme-assured-bundles`
**Date opened:** 2026-04-26
**Author:** Steve Jones (commissioning), Claude (drafting)

---

## Why this research exists

The drafted scope for Method 1 (waterfall phase gates) and Method 2 (agent-first specs with traceability + KB-for-code) carries three open design questions that we cannot answer from inside our heads. Getting these wrong locks in scope mistakes that compound through implementation.

The questions:

1. **What does "assurance-grade" actually require?** Major safety-critical standards (DO-178C, IEC 62304, ISO 26262, IEC 61508, FDA 21 CFR Part 820) all impose traceability, but at different granularity, with different evidence requirements. We need to know what the standards demand before we promise the Assured bundle "helps reach assurance".
2. **How do mature ecosystems decompose large systems?** Bazel, Erlang/OTP, DDD, microservices, MBSE/SysML, ARINC 653, and AUTOSAR all model module boundaries differently. We need to pick which model to borrow from for our markdown-driven framework — and know the failure mode of the one we don't pick.
3. **What does the existing requirements-management tool landscape teach us?** sphinx-needs is the closest existing thing to what we're building; DOORS is the canonical "do not become this" warning. We need a clear-eyed view of what to learn and what to avoid.

This research is **scope-shaping**, not background reading. Each line answers a specific design question with an actionable recommendation.

---

## Three-stage process

### Stage 1 — Plan (this document, plus the prompt files in `prompts/`)

Defines the research lines, the prompts to run, the reference discipline, and the synthesis pattern. **Complete when this commit lands.**

### Stage 2 — Research (run on Claude Desktop, NOT in Claude Code)

For each of the three prompt files in `prompts/`, the operator (Steve) opens Claude Desktop's extended research mode, pastes the prompt content, captures the output, and saves it to the corresponding `outputs/<line-id>/` directory. The output filename convention is `output-<run-N>.md` so multiple runs are preserved (a follow-up run with sharper questions, for instance, lives alongside the first).

Each Claude Desktop run should:
- Carry the **full prompt** including the reference discipline section
- Be allowed to do extended research (web access, multi-step reasoning)
- Produce a single comprehensive output document

If a Desktop run produces an output that's clearly thin or off-target, capture it anyway (in `outputs/<line-id>/output-1-thin.md` or similar) and re-run with a sharpened prompt. We'd rather have the failed-attempt artefact in the repo than discard it silently.

### Stage 3 — Synthesise (run in Claude Code)

For each research line, run the per-line synthesis prompt (see `prompts/synthesis-template.md`) against the corresponding output file. This produces a synthesis document in `synthesis/` that distils the research output into:

- Key empirical findings (with citations preserved from the source)
- Claims to incorporate into Method 1 / Method 2 scope
- Claims to reject (and why)
- Specific scope changes (additions, removals, clarifications)

Then run the **overall synthesis prompt** against all three per-line syntheses to produce the final scope-update document. The output of stage 3 is what we use to update the design specs and write the implementation plan.

The synthesis stage is intentionally a separate activity. Doing it inside the same Desktop run as the research conflates "what the literature says" with "what we should do" — two different judgements that benefit from being made separately.

---

## Folder structure

```
research/sdlc-bundles/
├── PLAN.md                                     # This file
├── METHODS.md                                  # Reference context: Method 1 + Method 2 definitions
│                                               # (REQUIRED context for every prompt below)
├── prompts/
│   ├── 01-traceability-standards.md            # Stage 2 prompt for line 1
│   ├── 02-decomposition-patterns.md            # Stage 2 prompt for line 2
│   ├── 03-alm-tools-landscape.md               # Stage 2 prompt for line 3
│   ├── synthesis-per-line-template.md          # Stage 3 prompt template (one synthesis per research line)
│   └── synthesis-overall.md                    # Stage 3 prompt for cross-line synthesis
├── outputs/                                    # Claude Desktop research outputs land here
│   ├── 01-traceability-standards/
│   ├── 02-decomposition-patterns/
│   └── 03-alm-tools-landscape/
└── synthesis/                                  # Stage 3 outputs land here
    ├── 01-traceability-synthesis.md
    ├── 02-decomposition-synthesis.md
    ├── 03-alm-synthesis.md
    └── overall-scope-update.md
```

**Important — METHODS.md is required context for every prompt.** Each prompt now starts with a "Required context" line instructing the operator to paste the contents of METHODS.md into Claude Desktop *before* the prompt itself. Without that context the research outputs will be too generic to drive specific design decisions.

---

## Reference discipline (applies to every prompt)

Every research output and every synthesis document MUST follow these rules. The prompts include this discipline inline so the rules are enforced at generation time, not by post-hoc cleanup.

### Per-claim citation

Every factual claim — every statement that asserts something is true about how a standard works, what a tool does, how a pattern is implemented — must carry an inline citation in the form `[N]` where `N` indexes into a bibliography at the end of the document.

Acceptable claim shape:

> DO-178C Objective A-3.4 requires bidirectional traceability between high-level requirements and low-level requirements [12].

Unacceptable claim shape (no citation):

> DO-178C requires bidirectional traceability.

### Bibliography format

Each cited source listed at the document end as:

```
[N] <Author/Organisation>. (<Year>). <Title>. <Source type>. <URL>. Accessed <YYYY-MM-DD>.
   Source-type tag: [standard | peer-reviewed | vendor-whitepaper | vendor-doc | practitioner-blog | wiki | book | conference-talk]
   Credibility note: <one-line note on authority and any conflict of interest>
```

Example:

```
[12] RTCA. (2011). DO-178C: Software Considerations in Airborne Systems and Equipment Certification.
     Source-type tag: [standard]
     URL: https://my.rtca.org/productdetails?id=2403
     Accessed 2026-04-27.
     Credibility note: Authoritative — the controlling standard itself. Behind paywall; secondary citations from regulator-published summaries acceptable when the standard text is not directly accessible.
```

### Source-quality assessment (CRAAP-style)

Sources should be evaluated on:

- **Currency** — when was it published / last updated? Is it current relative to the topic?
- **Relevance** — does it directly answer the question, or is it adjacent?
- **Authority** — who wrote it? Standards body, peer-reviewed, vendor with skin in the game, anonymous blog?
- **Accuracy** — corroborated by other sources? Any obvious errors?
- **Purpose** — informational, advocacy, marketing, opinion?

Vendor whitepapers and practitioner blogs are acceptable but must be tagged as such. **Do not cite a vendor's own marketing about their product without also citing an independent source if the claim is load-bearing.** Cite each source's tag in the bibliography.

### Counter-argument requirement

Each research line includes an explicit "Counter-arguments and known criticism" section. The prompt forces the researcher to surface opposing views, known failure modes, and credible criticism — not just the positive case. We do not want one-sided research outputs.

### No invented sources

If a fact cannot be cited from a credible source, the output must say so explicitly: "I could not find an authoritative source for this claim within the research scope." Inventing or paraphrasing-without-citation is the failure mode that makes research outputs worse than no research.

---

## Three research lines

### Line 1 — Regulated-industry traceability standards

**Decision it informs:** What rigour the Assured bundle must support to be defensibly "assurance-grade".

**Open questions to answer:**

- Across DO-178C, IEC 62304, ISO 26262, IEC 61508, FDA 21 CFR Part 820: which standards mandate bidirectional req↔code traceability vs unidirectional?
- What's the required granularity (high-level requirements only, or also low-level / derived requirements)?
- What evidence forms are acceptable for an audit (database export, traceability matrix, link records inside requirement text)?
- How is responsibility assigned for link maintenance (process discipline vs tooling)?
- What does each standard say about *change-impact analysis* — when a requirement changes, what re-verification is required?

**Output deliverable:** comparison matrix across standards + per-standard deep dive + "what an Assured bundle would need to support each".

**Time-box:** ~2 hours of Desktop research time.

**Prompt file:** `prompts/01-traceability-standards.md`.

### Line 2 — Decomposition patterns in practice

**Decision it informs:** Which decomposition primitive Method 2 should borrow from, and what failure mode to design against.

**Open questions to answer:**

- For each of: Bazel build graphs, Erlang/OTP supervision trees, DDD bounded contexts, microservice boundaries (Newman / Richardson), MBSE/SysML blocks, ARINC 653 partitions, AUTOSAR software components — what is the unit of decomposition and how is it declared?
- Which patterns make boundary leakage *visible* (build break, type error, runtime fault) vs. only *discoverable in review*?
- What does each pattern's literature say about the failure mode when boundaries are wrong (god-modules, tangled coupling, unclear ownership)?
- Which pattern best suits a markdown-driven, agent-orchestrated framework where the decomposition is *declared* in a registry rather than enforced by a build system or runtime?

**Output deliverable:** comparison table + per-pattern section + final synthesis "for our shape, the closest model is X because Y, with the explicit known failure mode of Z to design against".

**Time-box:** ~3 hours of Desktop research time.

**Prompt file:** `prompts/02-decomposition-patterns.md`.

### Line 3 — ALM / requirements-tools landscape

**Decision it informs:** Concrete "what to borrow" and "what to avoid" calibration for our framework.

**Open questions to answer:**

- For each of: sphinx-needs, IBM DOORS / DOORS Next, Siemens Polarion, Jama Connect, Reqtify, ReqIF (the standard), CodeBeamer, Helix ALM — what's the data model, the core value prop, the known criticism?
- How does each handle code-to-spec linking (annotations in code, external link tables, bidirectional database)?
- Which are open / closed / extensible? Pricing tier?
- What does practitioner literature say about each tool's failure mode (DOORS bloat, Polarion lock-in, sphinx-needs scaling limits)?

**Output deliverable:** comparison matrix + per-tool dossier with "lessons for us" + a final "what we should NOT do" section + a final "what we should learn" section.

**Time-box:** ~1.5 hours of Desktop research time.

**Prompt file:** `prompts/03-alm-tools-landscape.md`.

---

## What we will explicitly NOT research

- "Plan-then-act" patterns — superpowers covers this; re-reading agent-orchestration patterns adds nothing.
- General SDLC theory — covered by EPIC #97's existing research (`research/sdlc/Agentic_SDLC_Options.md`, `research/sdlc/Phase5_Final_Report.md`).
- Code-intelligence tools at scale (Sourcegraph, Cody, GitHub indexing) — Method 2 deliberately caps code KB at annotation-driven indexing. Researching deeper indexing would invite scope creep, not constrain it.
- Specific commercial pricing or licensing — irrelevant to design decisions.

If the research outputs surface a strong reason to revisit any of these caps, we revisit them — but we don't commission research with the cap-revisit as the goal.

---

## Stage-3 synthesis pattern

Each per-line synthesis follows the template at `prompts/synthesis-per-line-template.md`. The output is structured as:

1. **Source attestation** — which output file(s) this synthesis is based on; total claims processed; any source-quality concerns.
2. **Empirical findings** — the substantive claims from the research, grouped by sub-question, each preserving the original citation.
3. **Claims to incorporate** — specific findings that we should adopt as design decisions, with the design decision spelled out.
4. **Claims to reject** — findings we considered but rejected, with reasoning.
5. **Scope changes** — concrete edits to the Method 1 + Method 2 scope (additions, removals, clarifications), each tagged to a specific paragraph or table cell in the existing scope draft.
6. **Open questions remaining** — what the research did not answer, and whether we need a follow-up research line.

The overall synthesis takes all three per-line syntheses and produces `synthesis/overall-scope-update.md`, which is the document we'll use to update the design spec before writing-plans.

---

## Definition of done for the research stage

The research stage is complete when:

- [ ] All three prompts have been run in Claude Desktop and outputs saved to `outputs/<line-id>/`
- [ ] Each output passes a quick review for citation discipline (every claim has a `[N]` tag, bibliography present, source-tags assigned)
- [ ] Per-line syntheses produced in `synthesis/01-...md`, `synthesis/02-...md`, `synthesis/03-...md`
- [ ] Overall synthesis produced in `synthesis/overall-scope-update.md`
- [ ] Branch is in a state where the next step is "update design specs based on synthesis", not "do more research"

If a research output comes back thin or off-target and a re-run is needed, that re-run is part of stage 2, not a slip in stage 1.

---

## What this research does NOT do

- It does not produce the design spec for Programme + Assured bundles. That comes after synthesis.
- It does not produce the implementation plan. That comes after the design spec.
- It does not commit us to any specific design decision. The decisions are made in synthesis, with the research as input.

The research is informational — it sharpens the decisions we make, but the framework author (Steve) makes the calls.
