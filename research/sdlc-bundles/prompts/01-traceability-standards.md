# Research Line 1 — Regulated-Industry Traceability Standards

## Why this matters

We are designing an "Assured" SDLC bundle that promises to be defensible substrate for safety-critical and regulated software development. Our scope draft asserts the bundle "produces substrate that helps reach assurance" — without grounding that claim in what specific standards demand, we will either over-build (becoming a rigid ALM tool) or under-build (the bundle promises assurance but doesn't deliver auditable evidence).

This research line establishes what the major safety-critical software standards actually require for requirements traceability, so the Assured bundle's scope can be calibrated to real demands rather than imagined ones.

## How to use this prompt

1. Open Claude Desktop with extended research mode enabled.
2. **Paste the contents of `research/sdlc-bundles/METHODS.md` first**, as a system-context message at the start of the conversation. This tells the researcher what the framework is, what Method 1 and Method 2 are, and what's already built. Without this context the research output will be too generic to be useful.
3. Then copy the entire content of the **`## Prompt`** section below as the next message.
4. Allow the research to complete. Expect ~30-60 minutes of generation time for a thorough output.
5. Save the output to `research/sdlc-bundles/outputs/01-traceability-standards/output-1.md`.
6. If the output is thin or off-target, save it as `output-1-thin.md` and run a sharpened follow-up; the failed-attempt artefact stays in the repo as evidence.

---

## Prompt

> **Required context**: this prompt assumes you have just read `research/sdlc-bundles/METHODS.md` describing the framework, Method 1 (Programme bundle), and Method 2 (Assured bundle). If that document was not pasted into this conversation, request it before continuing.

You are conducting deep research to inform the design of the **Assured bundle** described in METHODS.md. You are NOT being asked to recommend a tool; you are being asked to characterise what authoritative standards demand, so the framework's scope can be calibrated.

The decision your research informs is: which traceability obligations should the framework's **Assured bundle** (Method 2) natively support, and which are out of scope for an open-source framework (left to projects to layer on)?

### Scope of research

Cover the following standards. For each, answer the listed questions. Where a standard has been superseded or revised, focus on the **current published version** (DO-178C not DO-178B; ISO 26262:2018 not the 2011 edition; etc.) and note when an older version differed materially.

- **DO-178C** (Software Considerations in Airborne Systems and Equipment Certification) — civil aviation
- **IEC 62304** (Medical device software — Software life cycle processes) — medical devices
- **ISO 26262** (Road vehicles — Functional safety) — automotive, specifically Part 6 (product development at the software level)
- **IEC 61508** (Functional safety of electrical/electronic/programmable electronic safety-related systems) — generic industrial / process control
- **FDA 21 CFR Part 820** (Quality System Regulation) — US medical device regulation, particularly the design controls subpart and the related guidance "General Principles of Software Validation"

For each of these five, answer:

1. **Traceability mandate.** Does the standard require traceability between requirements and code? Between requirements and tests? Between high-level requirements and low-level requirements? Quote or paraphrase the controlling clause/objective with citation.
2. **Bidirectional vs unidirectional.** Does the standard require links to be navigable in both directions (req↔code), or only one direction (req→test)? Cite the controlling text.
3. **Granularity.** What is the smallest unit at which traceability must be maintained? Function-level? Module-level? File-level? Requirement-level only? Cite the controlling text.
4. **Acceptable evidence forms.** What artefacts satisfy the auditor — traceability matrices, requirement-to-test maps inside test reports, database exports, embedded annotations? Quote any standard-published guidance on acceptable evidence.
5. **Change-impact obligation.** When a requirement changes, what re-verification or re-analysis does the standard require? How does this interact with the traceability obligation?
6. **Tooling neutrality.** Does the standard prescribe specific tools, or is tool choice unconstrained provided the evidence is producible? Cite where the standard speaks (or is silent) on tooling.
7. **Process vs artefact.** Does the standard care about the *process* by which traceability is maintained (who is accountable, when reviews happen) as well as the *artefacts* (the matrix, the links)? Cite both kinds of obligations where present.

### Output structure

Produce a single document with the following sections.

**Section 1 — Executive summary.** One paragraph per standard summarising what each demands, plus one closing paragraph identifying the *strictest* and *most permissive* of the five and what the strictness gradient looks like. Maximum 600 words.

**Section 2 — Comparison matrix.** A table with one row per standard and one column per question (1-7 above). Cells contain short factual claims (with citation indices), not prose. The matrix must be readable on its own.

**Section 3 — Per-standard deep dive.** One subsection per standard. Each subsection answers questions 1-7 in narrative form, quoting or paraphrasing controlling text with citations. Each subsection ends with "Notable specifics" — particular obligations or quirks that distinguish this standard from others. Each subsection should be 400-800 words.

**Section 4 — Cross-standard observations.** What's shared across all five (the common floor of obligations)? What's distinctive (where each standard goes its own way)? Are there patterns by industry — e.g., do medical and aviation diverge in a particular direction? Maximum 600 words.

**Section 5 — Counter-arguments and known criticism.** What do standards practitioners and academic critics say about these traceability obligations? Common criticisms include "traceability matrices become stale and lie", "the standard mandates the artefact but not its quality", "compliance theatre vs real assurance". Surface 4-6 such criticisms with citations from practitioner literature, conference papers, or peer-reviewed work.

**Section 6 — Implications for an open-source markdown-driven framework.** Three subsections:

- *Native obligations* — what the framework must support directly to be defensibly "assurance-grade substrate" (e.g., bidirectional link integrity, per-requirement change-impact recording).
- *Layered obligations* — what the framework can support through extension points but should not bake in (e.g., specific evidence-export formats per standard).
- *Out-of-scope obligations* — what the framework should explicitly disclaim (e.g., certification itself; only an accredited certification authority can certify).

This section is the deliverable that informs the framework's design. Be specific and actionable. Maximum 800 words.

**Section 7 — Bibliography.** Every cited source listed in the format specified in "Reference discipline" below.

### Reference discipline

Every factual claim — every statement that asserts something about what a standard requires, what an objective says, what evidence is acceptable — must carry an inline citation in the form `[N]` where `N` is a bibliography index.

The bibliography at the end of the document lists each cited source as:

```
[N] <Author/Organisation>. (<Year>). <Title>. <URL>. Accessed <YYYY-MM-DD>.
   Source-type tag: [standard | regulator-guidance | peer-reviewed | vendor-whitepaper | practitioner-blog | industry-report | book | conference-paper | wiki]
   Credibility note: <one-line note on authority and any conflict of interest>
```

Source quality requirements specific to this research line:

- For each standard, the **primary citation must be the standard itself** (or a regulator-published summary if the standard text is paywalled and inaccessible).
- Secondary citations from regulator guidance (FAA AC 20-115D for DO-178C, FDA software validation guidance for 21 CFR Part 820) are highly valued.
- Vendor whitepapers (LDRA, Parasoft, Rapita Systems) are acceptable if tagged as such, but may not be the *only* source for a load-bearing claim.
- Practitioner blogs are acceptable for the criticism section (Section 5) but must be tagged and the author's authority noted.
- If a claim cannot be cited from a credible source, write "Source not located" rather than asserting it.

CRAAP-style quality assessment is required in each bibliography entry's credibility note (Currency, Relevance, Authority, Accuracy, Purpose).

### What to avoid

- Do not paraphrase a standard without citing the specific clause/objective number.
- Do not cite a vendor's marketing claim about their product as evidence of what the standard requires.
- Do not produce a generic "what is traceability" essay — the deliverable is a comparison across these five specific standards.
- Do not extrapolate beyond the standards' actual text. If the standard is silent on something, say so explicitly.
- Do not rank or recommend tools. The deliverable is about standards, not products.

### Length and depth

Target document length: 4,000-7,000 words. Section 6 (implications) is the most important section for our use; allocate the most depth there.
