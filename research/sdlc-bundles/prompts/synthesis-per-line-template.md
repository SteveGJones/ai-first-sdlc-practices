# Stage 3 Prompt — Per-Line Synthesis Template

## How to use this template

Once a research output is captured at `research/sdlc-bundles/outputs/<line-id>/output-<N>.md`, run this synthesis prompt against it to produce `research/sdlc-bundles/synthesis/<line-id>-synthesis.md`.

Run this either in Claude Desktop (with the research output pasted in alongside the prompt) or in Claude Code (via direct file read and the same prompt content). The synthesis is deliberately separate from the research itself — it converts findings into design decisions, which is a different kind of judgement than "what does the literature say".

For each research line:

1. Replace `<LINE-NAME>` with the line title (e.g., "Regulated-Industry Traceability Standards").
2. Replace `<LINE-ID>` with the line number/slug (e.g., `01-traceability-standards`).
3. Replace `<RESEARCH-OUTPUT>` with the actual content of the research output file (paste it in).
4. Replace `<DRAFT-SCOPE-LINK>` with a pointer to the relevant scope draft section (initially this is the scope draft I already wrote in our planning conversation; once committed as a spec doc it'll be a path).

---

## Prompt

You are converting a deep-research output into actionable design decisions for an open-source SDLC framework. The research has already been done; your task is **synthesis**, not further research.

The framework being designed supports two methods that ship together as commissionable bundles:

- **Method 1 (Programme bundle)**: waterfall phase gates — requirements-spec, design-spec, test-spec, then TDD code — with cross-phase review enforcement and validators that block on missing artefacts.
- **Method 2 (Assured bundle)**: builds on Method 1 with stable identifiers (REQ-/DES-/TEST-/CODE-XXX), bidirectional link integrity, declarative decomposition (program → sub-program → module), KB-based retrieval over specs and code, and a render pipeline that produces human-readable scoped documentation per module.

The framework is markdown-driven, filesystem-first, agent-orchestrated, and open-source.

### Research line under synthesis

**Line:** <LINE-NAME>

**Decision the research informs:** [paste the "Decision it informs" line from PLAN.md for this research line]

**Research output to synthesise:**

<RESEARCH-OUTPUT>

### Existing scope draft for context

The Method 1 + Method 2 scope draft is located at <DRAFT-SCOPE-LINK>. The synthesis must reference specific paragraphs / table cells in that scope draft when proposing changes — not "the scope should change" but "section X.Y in the scope draft, which says Z, should change to W because of finding F in the research".

### Your synthesis output

Produce a single document with these sections.

**Section 1 — Source attestation.**

- Which research output file(s) this synthesis is based on (file path and word count).
- Total citations in the source; whether citation discipline was followed (every claim has `[N]` tag, bibliography present, source-tags assigned).
- Any source-quality concerns: thin citations on load-bearing claims, vendor-only sources for criticism, missing evidence for key questions.
- Any caveats to apply when reading the synthesis (e.g., "the source is authoritative on standards but thin on implementation patterns; weight Section 2 findings accordingly").

**Section 2 — Empirical findings.**

The substantive claims from the research, grouped by sub-question. Preserve the original citation indices as they appear in the source (don't renumber). Each finding is a single declarative sentence with the citation. Group findings under sub-headings that mirror the original questions. This section is *factual extraction* — no interpretation yet.

Maximum 1,500 words. The point is *capture* not *exhaustion*; cite the strongest 15-25 findings and skip the corroborating padding.

**Section 3 — Claims to incorporate.**

For each empirical finding that should drive a specific design decision in our framework, write one entry of the form:

```
**Claim**: [the finding, restated as a design implication]
**Source citation**: [N from source]
**Design decision**: [what we should now build / change / clarify]
**Affected scope section**: [pointer to the relevant section in the scope draft]
**Confidence**: [HIGH | MEDIUM | LOW] with one-sentence reason
```

Aim for 5-10 such entries per research line. Each must reference a specific empirical finding from Section 2 — no claims pulled from outside the research.

**Section 4 — Claims to reject.**

Findings from the research that we considered but should NOT incorporate. Each entry:

```
**Claim**: [the finding]
**Source citation**: [N from source]
**Why we reject it**: [reasoning — out of scope, contradicted by other findings, would push us into ALM-tool territory, etc.]
**What we do instead**: [our actual position, briefly]
```

This section forces explicit rejection rather than silent omission, which makes the decision auditable later.

**Section 5 — Scope changes.**

Concrete edits to the Method 1 + Method 2 scope draft. Each entry:

```
**Section affected**: [exact section/paragraph reference in the scope draft]
**Current text** (paraphrased if long): [...]
**Proposed change**: [add | remove | clarify | replace]
**Replacement text or new content**: [...]
**Driving claim(s)**: [reference back to Section 3 entry/entries]
```

If a scope section is unaffected by this research line, do not list it. Only entries that drive a change.

**Section 6 — Open questions remaining.**

What did the research NOT answer that we still need answered? Each entry:

```
**Question**: [...]
**Why it matters**: [what design decision is blocked]
**How to resolve**: [follow-up research line, expert consultation, prototype experiment, accept and document the uncertainty]
```

This section flags whether we need a stage-2 follow-up or whether we accept the uncertainty and move on.

**Section 7 — Confidence assessment for the line as a whole.**

A single paragraph (max 150 words) characterising:
- How well-grounded the synthesis is (citation density, source quality, internal consistency).
- Where the research was strong (which sub-questions got authoritative answers).
- Where the research was weak (which sub-questions got thin or vendor-marketing-driven answers).
- Whether the synthesis findings are HIGH / MEDIUM / LOW confidence overall.

### Reference discipline for the synthesis

- Every claim in your synthesis must trace back to a citation in the source research output. Use the form `[source: N]` to cite back to the source's bibliography.
- If you make an inference that goes *beyond* what the source explicitly says, mark it as `[inferred]` and explain the inference. Do not present inferences as if they were source findings.
- Do not introduce new external citations. The synthesis is bounded by the research output; if the research output didn't cite something, you don't either.
- If the source output has citation-discipline failures (claims without `[N]` tags, missing bibliography, etc.), call them out explicitly in Section 1 and downgrade affected findings' confidence in Section 3.

### What to avoid

- Do not produce a generic "key takeaways" summary. The deliverable is design-decision-shaped.
- Do not pull design recommendations from your training data that the research didn't cover. The synthesis is bounded by the research output.
- Do not over-claim confidence. A finding from a single vendor whitepaper is LOW confidence even if the whitepaper is well-written.
- Do not skip the rejection section (Section 4). Explicit rejection is a deliverable, not optional.
- Do not produce scope changes (Section 5) without referencing back to specific empirical findings (Section 2 → Section 3 → Section 5 chain must be traceable).

### Length

Target document length: 2,500-4,500 words. Sections 3, 4, and 5 together carry the deliverable weight; Sections 1, 2, 6, 7 are supporting context.
