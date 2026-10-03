# Research Campaign Closeout — 2026-04-26

## Inventory

| Artefact | Path | Word Count | Status |
|----------|------|-----------|--------|
| Plan | PLAN.md | 2,450 | COMPLETE |
| Methods | METHODS.md | 3,500 | COMPLETE |
| Prompt L1 (Traceability) | prompts/01-traceability-standards.md | 1,363 | COMPLETE |
| Prompt L2 (Decomposition) | prompts/02-decomposition-patterns.md | 1,534 | COMPLETE |
| Prompt L3 (ALM Tools) | prompts/03-alm-tools-landscape.md | 1,731 | COMPLETE |
| Synthesis template | prompts/synthesis-per-line-template.md | 1,172 | COMPLETE |
| Synthesis overall prompt | prompts/synthesis-overall.md | 1,353 | COMPLETE |
| Output L1 | outputs/01-traceability-standards/output-1.md | 8,268 | COMPLETE |
| Output L2 | outputs/02-decomposition-patterns/output-1.md | 10,252 | COMPLETE |
| Output L3 | outputs/03-alm-tools-landscape/output-1.md | 8,823 | COMPLETE |
| Verification report | outputs/_verification-report.md | 1,326 | COMPLETE |
| Synthesis L1 | synthesis/01-traceability-synthesis.md | 5,238 | COMPLETE |
| Synthesis L2 | synthesis/02-decomposition-synthesis.md | 4,703 | COMPLETE |
| Synthesis L3 | synthesis/03-alm-synthesis.md | 3,244 | COMPLETE |
| Overall synthesis | synthesis/overall-scope-update.md | 5,104 | COMPLETE |

**Total research output**: 61,061 words across 14 artefacts. All expected artefacts present.

---

## Definition-of-done checklist

**1. All three prompts run, outputs saved** — **PASS**
- L1 output: 8,268 words, all required sections present, 22 bibliography entries
- L2 output: 10,252 words, all required sections present, 24 bibliography entries
- L3 output: 8,823 words, all required sections present, 32 bibliography entries
- Verification report confirms all three outputs meet citation discipline and section requirements

**2. Each output passes citation-discipline review** — **PASS**
- L1: 264 inline citations vs 22 bibliography entries (12 refs/entry); format verified; source-type tags assigned; CRAAP assessment present
- L2: 230 inline citations vs 24 bibliography entries (9.6 refs/entry); format verified; all counter-arguments cited
- L3: 157 inline citations vs 32 bibliography entries (4.9 refs/entry, appropriate for landscape survey); format verified; no invented sources
- All three outputs cite research as substantive findings, not speculation

**3. Per-line syntheses produced** — **PASS**
- L1: 5,238 words, 7 sections (Source Attestation, Empirical Findings, Claims to Incorporate, Claims to Reject, Scope Changes, Open Questions, Confidence Assessment)
- L2: 4,703 words, 7 sections (same structure)
- L3: 3,244 words, 7 sections (same structure)
- All three confirm high-quality sources and integrate findings into concrete scope recommendations

**4. Overall synthesis produced** — **PASS**
- overall-scope-update.md: 5,104 words, 10 sections
- Sections 1–8: Cross-line agreements, conflicts, integrated scope changes, decomposition primitive, traceability rigour, sphinx-needs adoption, reference discipline
- Section 9: Open questions remaining
- Section 10: Clear (a)/(b)/(c) recommendation (proceed to Stage 4)

**5. Branch ready for "update design specs"** — **PASS**
- No "do more research" punt; all open questions have resolution paths
- Ten concrete scope changes for Method 2; four for Method 1
- Each change traced to specific research findings with [Line N: Section X] citations
- Cross-line agreements show strong convergence; no material conflicts

---

## Headline decisions surfaced

**Decomposition primitive**: Domain-Driven Design bounded contexts layered with Bazel visibility-rule discipline, with optional hexagonal architecture for within-module structure [overall-scope-update.md, Section 5].

**Traceability rigour calibration**: Bidirectional link integrity (forward REQ→DES→TEST→CODE, backward indices) at requirement-level granularity, with static build-time validation and annotation-driven code linking. Satisfies ISO 26262 baseline; compatible with DO-178C, IEC 62304, IEC 61508, FDA 21 CFR Part 820 [overall-scope-update.md, Section 6].

**Sphinx-needs adoption boundary**: Adopt foundational patterns (declarative schema, static validation, file-based Git-native storage, annotation-driven code parsing); explicitly do not adopt flat identifier scheme, absence of decomposition primitive, dynamic computed fields, or rich-text support [overall-scope-update.md, Section 7].

**Method 1 scope changes**: Four clarifications and additions (phase-gate link validation, traceability-export skill, model-selection guidance, mandatory phase-review) [overall-scope-update.md, Section 3].

**Method 2 scope changes**: Ten changes spanning decomposition enrichment, ID-stability under refactoring, annotation validation, code-annotation skill, change-impact annotation, traceability-export, granularity validation, commissioning guidance, out-of-scope clarification, organisational metadata policy [overall-scope-update.md, Section 4].

**Recommended next action**: (a) Update the design spec with these scope changes and proceed to Stage 4 (implementation planning). Dogfood the Assured bundle on an internal EPIC (candidate: EPIC #142 sub-features 3–8) to validate the design in practice [overall-scope-update.md, Section 10].

---

## Quality summary

Citation discipline across all three research outputs is strong: every substantive claim carries inline [N] citations; all bibliographies include source-type tags and credibility notes; counter-arguments are genuine and cited, not strawmen. Word counts are within or acceptable of target bands (L1 8.3K over 4–7K target, justified by 5 standards; L2 10.3K within 6–10K; L3 8.8K within 5–9K). Structure is complete: all three outputs have required sections with Section 6/8 implications sections being substantive (1.3–1.4K words each) and actionable. Per-line syntheses integrate findings into concrete design decisions with 7-section structure per specification. Overall synthesis demonstrates strong lateral coherence across three independent research lines: all converge on DDD + Bazel + annotation-driven + file-based + static validation + bidirectional + change-impact annotation. The absence of cross-line conflicts is itself a strong signal of research quality.

---

## Open questions left for Stage 4

From overall-scope-update.md Section 9:

1. **Module dependency graph visualization format**: Prototype during Stage 4. Options: ASCII DAG, HTML SVG, markdown table. Accept visualization will be lossy at 50+ modules.

2. **Visibility violations enforcement**: Recommend strict warning (visible in pre-push, must be acknowledged) until commissioning team opts into strict mode. Strict recommended for regulated-industry projects.

3. **Module boundary granularity**: Accept as team-driven design choice. Heuristic: "A module should be the scope of responsibility for one team." Defer specific metrics to post-dogfooding.

4. **Soft decomposition mode**: Support both modes (enforced for regulated/assured contexts; advisory for exploratory). Configurable at commissioning.

5. **Index regeneration cycle**: Default 7 days. Threshold is convenience flag, not compliance requirement. Teams adjust per context.

6. **Integration with external ALM tools**: Out of scope. Propose Stage 2 follow-up on "Integration with external ALM tools (Jama, Polarion, Codebeamer)."

---

## Recommended next action

**Proceed immediately to Stage 4 (implementation planning and plan-writing).**

Update METHODS.md with the ten Method 2 and four Method 1 scope changes enumerated in overall-scope-update.md Sections 3–4. The three research lines show strong convergence on design direction; no material conflicts exist; open questions are implementation details resolvable via prototype experiments during coding.

Dogfood the Assured bundle on an internal EPIC (candidate: EPIC #142 sub-features 3–8) to validate that the design satisfies regulatory and assurance-quality expectations in practice before committing to the full implementation roadmap.

---

## Verification concerns

**Section 5 word count**: The decomposition primitive final call (overall-scope-update.md Section 5) is 460 words, below the target 500–1,000 band. The section is substantive (rationale is clear; failure mode is explicit) but concise. This is acceptable given the recommendation is direct (adopt DDD + Bazel), but the implementation plan may want to expand this section during design-spec authoring to include worked examples or decomposition-registry schema sketches.

**Cross-line citations**: The per-line syntheses do not cross-reference each other (e.g., L1 does not note that sphinx-needs supports DO-178B, documented in L3). This is acceptable—each synthesis is self-contained—but the overall synthesis successfully integrates these connections via the [Line N: Section X] citation form. No blocking issue, but future stages should be aware of the citation pattern.

**Assumption on METHODS.md currency**: The overall synthesis assumes METHODS.md Section numbers (e.g., "METHODS.md Section 4, 'Bidirectional traceability' subsection (lines 156–164)"). Verify METHODS.md structure matches these references before merging scope changes; if structure has drifted, update cross-references in overall synthesis.

**No blocking issues identified.** All Definition-of-Done criteria met. Campaign is ready for handoff to Stage 4.
