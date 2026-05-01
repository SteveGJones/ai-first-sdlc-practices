# Research Line 1: Regulated-Industry Traceability Standards
## Synthesis — Design Decisions for Method 1 & Method 2

---

## Section 1: Source Attestation

**Source file:** `/Users/stevejones/Documents/Development/ai-first-sdlc-practices/research/sdlc-bundles/outputs/01-traceability-standards/output-1.md` (8,231 words)

**Citation discipline:** The source maintains strict citation discipline. All substantive claims carry `[N]` tags referencing a 22-entry bibliography (entries [1]–[22]). The bibliography is comprehensive, spanning authoritative standards (DO-178C, IEC 62304, ISO 26262, IEC 61508, FDA 21 CFR Part 820), regulator guidance (FAA AC 20-115D, FDA General Principles), vendor whitepapers, practitioner blogs, and peer-reviewed research. No claims lack attribution.

**Source quality:** The research is strong across two distinct dimensions. First, on standards compliance: the output directly cites all five primary standards (source data grounded in authoritative documents [1][5][9][12][14]) and regulator guidance ([3][15][16]), giving the source very high authority on what each standard mandates. Second, on practical limitations: the output incorporates peer-reviewed academic research ([17][18][21][22]) and practitioner experience reports ([19][20]) documenting known problems (traceability decay, bidirectional-traceability aspirational gaps, scalability challenges). This creates a balanced view: standards-as-written versus standards-as-practiced.

**Caveats:** The source is authoritative on standards and their stated requirements, but makes limited claim to implementation patterns for markdown-driven systems specifically. Section 6 of the source (Implications for Open-Source Markdown-Driven Framework) is the synthesis author's interpretation, not external evidence; I have marked such inferences clearly in Section 3 below.

---

## Section 2: Empirical Findings

### Bidirectional Traceability Requirements

**DO-178C mandate.** DO-178C requires bidirectional traceability: requirements↔code, with backward confirmation ensuring all code has justification and all tests connect to requirements. The depth scales by Level (Level A requires traceability to object code; Level D permits minimal documentation). [1][2][3][4]

**IEC 62304 permissiveness.** IEC 62304 permits unidirectional (forward: req→design→code) traceability at all class levels and does not mandate backward links, though practitioners typically implement bidirectionality for audit compliance. [6][7]

**ISO 26262 strictness.** ISO 26262:2018 mandates bidirectional traceability (both forward and backward) across all ASIL levels, particularly ASIL D, with no permit for unidirectionality. [9][10]

**IEC 61508 requirement.** IEC 61508-3 specifies bidirectional traceability as an explicit development objective in Annex A.1, ensuring all outline requirements are traced down and all detailed requirements trace back up with no spurious code. [12]

**FDA position.** FDA 21 CFR Part 820 emphasizes forward traceability (requirements→design→code→tests) with backward confirmation via design-history-file documentation; the regulation does not use the term "bidirectional" but practitioners implement bidirectional matrices to satisfy auditor expectations. [14][15][16]

**Cross-standard convergence.** Across all five standards, bidirectional or backward-confirmable traceability is the common demand, with the exception that IEC 62304 explicitly permits unidirectionality. The strictest standards (ISO 26262, IEC 61508) demand true bidirectionality; the most permissive (IEC 62304) allows forward-only with backward confirmation. [1][5][9][12][14]

### Granularity of Traceability

**DO-178C scaling.** DO-178C scales the *granularity* of required documentation by level: Level A requires traceability to individual object-code instructions; Level B and C require source-code statement or function level; Level D permits file-level or higher. [1]

**IEC 62304 decomposition.** IEC 62304 does not prescribe a minimum granularity; granularity follows software decomposition (if modular, function-level; if monolithic, natural-function separation). Class C software typically mandates finer granularity (function-level) than Class A. [7]

**ISO 26262 requirement-level mandate.** ISO 26262 Part 6 mandates requirement-level granularity for functional and technical safety requirements across all ASIL levels; implementation granularity is function or module depending on ASIL, with ASIL D demanding proof of no surplus code. [9][10]

**IEC 61508 SIL scaling.** IEC 61508 does not prescribe minimum granularity; SIL level and system decomposition guide the choice, with SIL 4 systems typically requiring finer granularity (requirement-level, function-level) than SIL 1. [12]

**Distinctive DO-178C approach.** DO-178C is unique in scaling *required artefact depth* by level, whereas the other four standards scale *rigour of verification and review* by level/class/ASIL but require similar artefact depth at all levels. [1]

### Change-Impact Obligations

**IEC 62304 detail and gating.** IEC 62304 Clause 8.2.4 (Software changes) mandates that every change request be evaluated for impact on hazards, risk-control measures, and architecture *before implementation*. This is a blocking gate. The standard also mandates re-classification if a change affects hazard analysis or risk assessment. [8]

**FDA explicit gate.** FDA 21 CFR §820.30(i) requires design-change re-validation before implementation if the change could affect safety or effectiveness; impact assessment is a mandatory gating control, not a post-hoc review. [16]

**DO-178C implicit requirement.** DO-178C covers change-impact analysis in the Software Configuration Management Plan objective (Section 6.7.3), implying that when a requirement or code is modified, the plan must specify how impact is assessed (which artefacts must be reviewed, retested, or re-verified). Implementation is team-specific. [1]

**ISO 26262 design-change procedure.** ISO 26262 Part 6 Clause 9.6.1 requires a design-change procedure: when a requirement, design element, or code is modified, impact on other requirements, hazard analysis, and V&V must be assessed. For ASIL B, C, and D, re-verification is mandatory. [9]

**Universal but variable formalisation.** All five standards require change-impact assessment, but formalisation and gating vary: IEC 62304 and FDA treat it as a mandatory blocking gate; DO-178C and ISO 26262 require it in configuration-management and design-change procedures but less explicitly as a blocker; IEC 61508 implies obligation through the requirement to maintain traceability integrity. [1][8][9][14][16]

### Tool Neutrality and Evidence Export

**Universal tool-agnosticism.** All five standards specify objectives (what must be evidenced) but not means. DO-178C, IEC 62304, ISO 26262, IEC 61508, and FDA guidance all accept evidence produced by any tool (spreadsheet, database, commercial ALM platform, markdown-driven system) provided the evidence is producible and auditable. [4][7][11][13][15]

**Regenerability principle.** ISO 26262 Part 8 Clause 11 and IEC 61508 both emphasize regenerability: traceability links must be reconstructible from primary artefacts (requirements documents, source code, test reports) without reliance on a specific tool or database. If the tool becomes unavailable, the traceability must still be reconstructible. [11][13]

**Tool qualification specificity.** ISO 26262-8 Clause 11 specifies tool qualification based on tool-confidence levels (TCL 1, 2, 3) and tool impact (TI1, TI2), not on tool choice. A tool requires qualification only if its malfunction could introduce or fail to detect errors in safety-critical work products. Traceability tools that only record and display links may not require qualification at all. [11]

**Acceptable evidence forms.** Common evidence forms across standards include requirements-traceability matrices (spreadsheets, tables, database exports), design documents with embedded requirement IDs, test-case matrices, source-code comments or annotations, and configuration-management baselines. None of the standards prescribes a single format. [1][3][4][6][15]

### Practical Limitations and Known Problems

**Traceability decay.** Academic research (Tian et al. 2021; mapping study of 63 papers) shows traceability links decay rapidly if not actively maintained. While all standards demand traceability, none mandate ongoing audits of link currency or decay-detection mechanisms. [17]

**Compliance theatre.** Practitioner experience (Ketryx 2021; Perforce 2022) documents cases where organisations satisfy traceability audits by creating spreadsheet matrices where every requirement links to a test case, but the test cases themselves are thin, untested, or never executed. The standards define what must be linked but rarely define what a "complete" or "meaningful" link is. [19][20]

**Post-hoc impact analysis.** While all standards require change-impact assessment, enforcement varies. In practice, many organisations perform impact analysis *after* code changes are committed, using it as justification for re-testing scope rather than as a blocking gate. [20]

**Granularity scaling inefficiency.** Research (Cleland-Huang et al. 2003) shows the cost of maintaining fine-grained traceability increases exponentially with system size. ISO 26262 and IEC 61508 do not relax granularity requirements at system scale, placing smaller systems in disadvantaged compliance positions. [21]

**Bidirectional traceability aspirational gap.** Research (Lucia et al. 2012) shows that while forward traceability is common, backward traceability is rarely complete in large codebases. Even standards requiring bidirectionality often see practitioners implement only forward links, with backward links assumed regenerable at audit time. [22]

---

## Section 3: Claims to Incorporate

**Claim 1: Bidirectional traceability is the regulatory baseline.**
- **Source citation:** [1][9][12] (DO-178C, ISO 26262, IEC 61508 all mandate bidirectionality explicitly)
- **Design decision:** The Assured bundle must natively support bidirectional link integrity. Forward links (REQ→DES→TEST→CODE) are declared in the linking artefact; backward indices (CODE→TEST→DES→REQ) are regenerated by `kb-rebuild-indexes`. Validators must flag broken or orphaned links (a CODE with no REQ annotation, a REQ with no DES, etc.). This satisfies DO-178C, ISO 26262, and IEC 61508 simultaneously; IEC 62304 and FDA guidance accept unidirectional but organisations typically implement bidirectionality for audit assurance, so full bidirectionality does not exceed any standard's requirement.
- **Affected scope section:** METHODS.md Section 4, "Bidirectional traceability" subsection (lines 156–164). Current language states "regenerated index supports queries," which is correct; the change is to add explicit validator coverage: "Validators: Forward link integrity — every cited ID exists in the registry; Backward coverage — every REQ has tests, every DES has implementing code, every CODE has annotations linking back."
- **Confidence:** HIGH. Five independent standards converge on bidirectionality (with one permitting unidirectionality but practitioners implementing bidirectionality anyway). The framework's approach of forward-declaration + backward-regeneration satisfies all five standards' requirements.

**Claim 2: Change-impact obligations require structured annotation, not automatic detection.**
- **Source citation:** [8][14][16] (IEC 62304, FDA, ISO 26262 all mandate change-impact assessment; [20] shows this is often post-hoc in practice)
- **Design decision:** The Assured bundle should not attempt automatic semantic change-impact detection (per METHODS.md Section 6 out-of-scope). Instead, support structured annotation: when a requirement, design element, or code unit changes, the team annotates the change with impact scope (e.g., "REQ-005 changed; affected: DES-012, TEST-034, CODE-segment-B"). A `change-impact-report` skill could then query the annotations to surface the declared impact scope and warn if an impact annotation is missing on a change. This makes change-impact analysis upfront and auditable, satisfying IEC 62304 and FDA gating requirements; it remains human-decided (not automatic) and does not require AST analysis.
- **Affected scope section:** METHODS.md Section 4, "Bidirectional traceability" and "Skills shipped" subsections. New entry: a `change-impact-annotate` skill (minor; exists in the render pipeline concept but should be explicit as a standalone skill).
- **Confidence:** HIGH. All standards require change-impact assessment; the research shows this is weak in practice ([20]). Structured annotation is a pragmatic middle ground: supports the obligation without overreach into semantic analysis.

**Claim 3: Granularity declaration should be declarative, not inferred.**
- **Source citation:** [1][7][9] (DO-178C scales by Level; IEC 62304 scales by Class; ISO 26262 scales by ASIL; all permit team choice within constraints)
- **Design decision:** The Assured bundle's decomposition model already declares program/sub-program/module structure (METHODS.md Section 4). Extend this: for each module, the team should declare a granularity target (e.g., "M1: requirement-level traceability; M2: function-level for safety-critical, module-level for non-critical"). Validators then flag when actual traceability falls short (e.g., "M1 declaration requires requirement-level; found module-level links in code-index"). This makes granularity choice explicit and auditable, satisfying DO-178C's level-based scaling and ISO 26262's ASIL-based scaling.
- **Affected scope section:** METHODS.md Section 4, "Decomposition" subsection (lines 166–180). Current language: "Decomposition is **declarative**, not inferred." Add: "Each module declaration includes a `granularity: [requirement | function | module]` field, stored in `programs` block. Validators enforce that actual traceability links match declared granularity."
- **Confidence:** MEDIUM-HIGH. The research shows granularity varies by standard and system; the framework should enforce declared granularity, not try to infer it. The addition is small and mechanical.

**Claim 4: Tool-neutral traceability requires regenerability from markdown source.**
- **Source citation:** [11][13] (ISO 26262-8 and IEC 61508 both emphasize that traceability must be reconstructible from primary artefacts without tool dependence)
- **Design decision:** The Assured bundle's shelf-index and code-index are already derivative artefacts, regenerable via `kb-rebuild-indexes`. This satisfies the regenerability principle. Extend: validators should confirm that the index is not stale (e.g., warn if the code-index was generated >7 days ago and code has been committed since). Document explicitly: "The framework's traceability indices (shelf-index, code-index) are derivative. Auditors may regenerate them from markdown source to verify link integrity; tool choice is immaterial to traceability validity."
- **Affected scope section:** METHODS.md Section 4, "KB extension to code" subsection (lines 182–194) and Section 6 "What is explicitly out of scope" (lines 232–240). No deletion needed; clarify in documentation of skills that indices are regenerable and tool-neutral.
- **Confidence:** HIGH. Regenerability from source is explicit in two standards; the framework already implements this design; documentation is the gap.

**Claim 5: IEC 62304's change-impact gating obligation implies mandatory blocking validation.**
- **Source citation:** [8] (IEC 62304 Clause 8.2.4 requires impact assessment *before* implementation; this is a blocking gate)
- **Design decision:** The Programme bundle's phase gates (METHODS.md Section 3, lines 73–82) already block progression unless prior-phase artefacts are complete and cited. Extend this to the Assured bundle: if a project is commissioned under IEC 62304 (or FDA regulations), add a `change-impact-gate` validator that blocks commits where code changes exist but no change-impact annotation is present. This is optional at commission time (teams can opt in per regulation or class level), but when enabled, it enforces the gating requirement. Default Assured bundle does not mandate this gate (preserves flexibility for Agile contexts), but the gate is available and documented.
- **Affected scope section:** METHODS.md Section 4, "Validators" under "Bidirectional traceability" subsection, and Section 3 "Phase gates" subsection. Add: "Optional validator: `change-impact-gate` (enabled by configuration) blocks commits where code changes lack change-impact annotation. Recommended for IEC 62304 and FDA 21 CFR Part 820 contexts."
- **Confidence:** MEDIUM. The research is clear that IEC 62304 and FDA require gating. Making it optional (rather than mandatory) hedges against the unknown: not all Assured bundle projects will be in regulated contexts. But the gate should be available and documented.

**Claim 6: Traceability evidence export should be template-driven, not tool-specific.**
- **Source citation:** [1][4][5][15] (All standards accept any evidence format; DO-178C AC 20-115D, IEC 62304, ISO 26262, FDA all state "any format that permits reconstruction")
- **Design decision:** Ship a `traceability-export <format>` skill that templates output in common audit formats: DO-178C traceability matrix (spreadsheet with Software Level per requirement), IEC 62304 risk-to-control matrix, ISO 26262 ASIL-scaled matrix, FDA Design History File (DHF) directory structure. The framework remains markdown-driven; export is a derivative artefact. This allows teams to satisfy auditor format preferences without abandoning the markdown substrate.
- **Affected scope section:** METHODS.md Section 4, "Skills shipped (Assured bundle)" subsection (lines 202–208). Add: "`traceability-export <format>` — produces human-auditor-friendly matrices in standard-specific formats (DO-178C RTM, ISO 26262 ASIL matrix, FDA DHF structure) from the shelf-index and code-index. Supports DO-178C, IEC 62304, ISO 26262, FDA 21 CFR Part 820; extensible for additional standards."
- **Confidence:** HIGH. All standards are tool-neutral; export templates are a convenience, not a compliance gate. Low risk, high utility.

**Claim 7: Certified compliance is out of scope; the framework produces assurance substrate, not assurance itself.**
- **Source citation:** [source: inferred from [2][5][9][14]] (Standards define what must be evidenced; no standard claims that an open-source framework certifies compliance)
- **Design decision:** The Assured bundle documentation must explicitly disclaim: "The Assured bundle produces substrate that helps organisations reach assurance (traceability records, decomposition declarations, change-impact records, phase gates, code annotations). It is not itself assurance and does not certify compliance. Certification requires an accredited certification authority. The framework is a tool; certification is an external governance activity."
- **Affected scope section:** METHODS.md Section 6 "What is explicitly out of scope" (lines 232–240), subsection "Industry certification itself" (lines 237–238). Current language: "The Assured bundle produces *substrate that helps reach assurance* (e.g., bidirectional traceability records), not *certification* (which requires an accredited certification authority and is out of any framework's reach)." This is correct; ensure it is repeated in the Assured bundle's commissioning documentation and in the framework's README.
- **Confidence:** HIGH. This is a clear out-of-scope boundary that protects the framework and sets user expectations correctly.

---

## Section 4: Claims to Reject

**Claim: The framework should include automatic semantic change-impact analysis (detecting that a code change to function `authenticate()` impacts tests for login, permission checking, and session management).**
- **Source citation:** [21] (Cleland-Huang et al. notes the cost of maintaining traceability scales exponentially with system size; automation would require AST analysis)
- **Why we reject it:** METHODS.md Section 6 explicitly declares "AST-level code intelligence" out of scope. The research confirms this is correct: semantic change-impact detection requires call graphs, data-flow analysis, or AI-driven reasoning, which are not markdown-compatible and would push the framework into IDE/ALM territory. The framework should support annotation-driven and manual change-impact recording, not automatic detection.
- **What we do instead:** The `change-impact-annotate` skill (Claim 2) surfaces change scope based on manual annotations; the `change-impact <artifact-id>` skill (Section 6.2 below) can query indices to propose impacted scope, but humans approve the scope.

**Claim: Bidirectional traceability should be optional (projects can choose unidirectional-only).**
- **Source citation:** [6][7] (IEC 62304 permits unidirectionality; [22] shows practitioners often implement only forward links)
- **Why we reject it:** While IEC 62304 permits unidirectionality, DO-178C, ISO 26262, and IEC 61508 mandate bidirectionality (three of five standards; the two medical-device standards diverge). Practitioners implementing IEC 62304 typically add bidirectionality for audit assurance anyway ([6]). Making bidirectionality mandatory in the Assured bundle defaults does not exceed any standard's requirement and aligns with the strictest standard (ISO 26262), which is defensible as "assurance-grade." Projects that need only IEC 62304 can use weaker validators via configuration, but the framework's default should be the strictest common requirement.
- **What we do instead:** Bidirectional traceability is mandatory in the Assured bundle defaults (Claim 1). Projects can relax validators via commissioning configuration if their regulatory context permits (e.g., IEC 62304 Class A).

**Claim: The framework should enforce artefact-quality gates (e.g., test cases must be non-empty, must be executed).**
- **Source citation:** [19][20] (Ketryx and Perforce document "compliance theatre": matrices exist but tests are thin or never executed)
- **Why we reject it:** The framework validates syntactic traceability integrity (links exist, are non-circular, map to declared IDs), not semantic quality. Enforcing test execution or non-emptiness would require integration with CI/CD systems and test frameworks, pushing the framework beyond "filesystem-first" design. The standards require evidence that testing was performed; the framework validates that links are declared. Semantic rigour is a team responsibility and auditor's concern, not the framework's.
- **What we do instead:** The `phase-review` skill (METHODS.md Section 3) supports structured review records that can include human assessment of test quality. The framework is a process enabler, not a quality gate.

**Claim: The framework should manage ID namespacing across multiple teams/projects (e.g., allow teams to share a central ID registry).**
- **Source citation:** [source: inferred from [9]] (ISO 26262 does not address multi-team governance)
- **Why we reject it:** Centralised ID governance requires a coordination service outside the scope of an open-source filesystem-first framework. Multiple teams cannot safely share a single ID namespace via Git without a centralised ID server. Teams can share ID-generation conventions (e.g., "TA-* for team A, TB-* for team B"), but governance is organisational, not technical. The framework should not attempt distributed ID coordination.
- **What we do instead:** Document ID-naming conventions in the commissioning guidance; each project has its own ID namespace. If organisations need central ID governance, they can build a coordination layer on top (outside the framework).

**Claim: IEC 61508 and ISO 26262 should require object-code or assembly-level traceability (mirroring DO-178C Level A).**
- **Source citation:** [1] (Only DO-178C requires object-code traceability; ISO 26262 and IEC 61508 require requirement-level and implementation-level but not object-code level)
- **Why we reject it:** The research is clear: DO-178C's object-code requirement is unique to aviation's extreme criticality. ISO 26262 and IEC 61508 require fine granularity (requirement-level, function-level) but not object-code level. Imposing object-code traceability on the Assured bundle would exceed the strictest standard's requirement and would be unmaintainable for most systems. ASIL D (ISO 26262) and SIL 4 (IEC 61508) can declare object-code traceability as a granularity target (Claim 3), but it should not be mandatory for the framework.
- **What we do instead:** The Assured bundle defaults to requirement-level and function-level granularity (satisfying ISO 26262 and IEC 61508). Projects can declare finer granularity (object-code level) per module if their ASIL/SIL and domain require it (Claim 3).

---

## Section 5: Scope Changes

**Section affected:** METHODS.md Section 4, "Bidirectional traceability" subsection (lines 156–164)

**Current text (paraphrased):** "Forward links declared in the linking artefact (DES references REQs; TEST references REQ + DES). Backward links regenerated by index. Validators flag broken links; warn on coverage gaps."

**Proposed change:** Clarify and strengthen validator coverage.

**Replacement text:**
```
### Bidirectional traceability

- **Forward**: REQ → DES → TEST → CODE. Each link declared in the linking artefact (DES references its REQs; TEST references its REQ + DES).
- **Backward**: regenerated index supports queries like "what tests cover REQ-auth-003?" or "what code implements DES-auth-005?".

Validators:
- **Forward link integrity**: every cited ID exists in the registry; references to non-existent IDs block commit.
- **Backward coverage**: every REQ has at least one DES; every DES has at least one TEST; every TEST has at least one CODE annotation; every CODE carries at least one REQ/DES annotation. Orphans (requirements with no design, design with no tests, code with no annotation) block commit.
- **Index regenerability**: `kb-rebuild-indexes` regenerates backward indices from markdown source; auditors can verify index integrity by running the command and comparing to committed index. Warn if index age exceeds threshold (default: 7 days) and code has been committed since last regeneration.
```

**Driving claim(s):** Claim 1 (bidirectional traceability is the regulatory baseline); Claim 4 (tool-neutral traceability requires regenerability).

---

**Section affected:** METHODS.md Section 4, "Decomposition" subsection (lines 166–180)

**Current text (paraphrased):** "Decomposition is declarative. The commissioning step adds a `programs` block to the project configuration with programs, sub-programs, and modules. Validators enforce that code maps to modules."

**Proposed change:** Add granularity declaration as part of decomposition.

**Replacement text:**
```
### Decomposition

Decomposition is **declarative**, not inferred. The commissioning step adds a `programs` block to the project's configuration:

- Which programs exist
- Which sub-programs each contains
- Which modules each sub-program contains
- Which directory paths belong to which module
- **Which modules have granularity targets** (optional): `granularity: [requirement | function | module]` per module. Default is `requirement` (finest). Modules may declare `function` or `module` if appropriate to their risk or complexity.

Validators:
- Every REQ has a module assignment
- Every CODE annotation maps to a declared module path
- No module has un-cited code (warn) or un-tested REQs (block)
- **Traceability granularity matches declared target**: if module M1 declares `granularity: requirement`, all code in M1 must carry REQ-level annotations; if M2 declares `granularity: function`, function-level annotations suffice. Warn if actual granularity exceeds declared target (underspecified links).
```

**Driving claim(s):** Claim 3 (granularity declaration should be declarative, not inferred).

---

**Section affected:** METHODS.md Section 4, "Skills shipped (Assured bundle)" subsection (lines 202–208)

**Current text:** Lists `commission-assured`, `req-add`, `req-link`, `module-bound-check`, `kb-codeindex`, `traceability-render`.

**Proposed change:** Add two skills: `change-impact-annotate` and `traceability-export`.

**Replacement text:**
```
### Skills shipped (Assured bundle, in addition to Method 1's skills)

- `commission-assured` — installs Assured bundle (which includes everything from `commission-programme`)
- `req-add`, `req-link` — mint and connect IDs (alternatives are hand-editing the markdown; the skills are conveniences, not gatekeepers)
- `module-bound-check` — runs decomposition validators
- `kb-codeindex` — parses annotations and emits the code-index
- `change-impact-annotate` — when a requirement, design element, or code unit changes, guide the team through annotating the change with impact scope (e.g., "REQ-005 changed; affected: DES-012, TEST-034, CODE-segment-B"). Supports change-impact gating when enabled. [NEW]
- `traceability-render <module-id>` — produces human-scoped doc for one module with all inter-ID links rendered as anchor links
- `traceability-export <format>` — produces human-auditor-friendly traceability matrices in standard-specific formats (options: do-178c-rtm, iec-62304-matrix, iso-26262-asil-matrix, fda-dhf-structure). Supports audit/certification preparation. [NEW]
```

**Driving claim(s):** Claim 2 (change-impact obligations require structured annotation); Claim 6 (traceability evidence export should be template-driven).

---

**Section affected:** METHODS.md Section 4, "Validators" (to be added as a new subsection under Bidirectional traceability or as extension of existing Validators text)

**Current text:** N/A (implicit in descriptions above)

**Proposed change:** Add optional gating validator for regulated contexts.

**Replacement text:**
```
### Optional validators (enabled by configuration for regulated contexts)

- `change-impact-gate` (default: disabled): blocks commits where code changes exist but no change-impact annotation is present. Recommended for IEC 62304, FDA 21 CFR Part 820, and ISO 26262 ASIL C/D contexts where change-impact assessment is a mandatory gating control.
```

**Driving claim(s):** Claim 5 (IEC 62304's change-impact gating obligation implies mandatory blocking validation).

---

**Section affected:** METHODS.md Section 6, "What is explicitly out of scope" (lines 232–240)

**Current text:** Already contains correct out-of-scope declarations.

**Proposed change:** Enhance subsection "Industry certification itself" to be explicit about what the framework does provide (assurance substrate).

**Replacement text:**
```
- **Industry certification itself.** The Assured bundle produces *substrate that helps reach assurance* (e.g., bidirectional traceability records, decomposition declarations, change-impact records, code annotations, phase gates, independent reviews), not *certification* (which requires an accredited certification authority and is outside any framework's reach). Organisations may use the Assured bundle to build a safety case or prepare for external certification audits, but the framework itself is a tool, not a certifier.
```

**Driving claim(s):** Claim 7 (certified compliance is out of scope; the framework produces assurance substrate, not assurance itself).

---

## Section 6: Open Questions Remaining

**Question 1: Should change-impact gates be default-enabled or default-disabled in the Assured bundle?**
- **Why it matters:** Claim 5 proposes an optional `change-impact-gate` validator. For regulated projects (IEC 62304, FDA), gating is mandatory; for Agile projects, blocking on change-impact annotation may feel bureaucratic. The research shows change-impact is often post-hoc in practice ([20]), suggesting teams need friction to enforce it upfront, but also suggesting that enforcing it by default may cause friction.
- **How to resolve:** Commissioning decision. When a project is commissioned as Assured, the team declares their regulatory context (none / IEC 62304 / FDA / ISO 26262 / DO-178C); the commissioning script enables the appropriate validators by default. This is an operational choice (Steve's call at commissioning time), not a research question. Propose: default-disable globally, but enable by policy at commissioning based on context. Document the impact: "Change-impact gating is a significant process change; teams should understand the gate's cost before enabling it."

**Question 2: What is the minimum acceptable cycle for index regeneration and freshness checks?**
- **Why it matters:** Claim 4 proposes warning if indices are stale (>7 days). The research documents traceability decay ([17][18]), suggesting frequent regeneration is prudent, but no standard prescribes a refresh frequency. Seven days is a guess.
- **How to resolve:** Accept the uncertainty. Document: "Default freshness threshold for backward-index staleness warnings: 7 days. Teams may adjust per their context (hourly for CI/CD integration, weekly for manual workflows). The threshold is a convenience flag, not a compliance requirement; the framework ensures regenerability, not freshness."

**Question 3: Should the framework support integration with external requirements tools (e.g., Jama)?**
- **Why it matters:** The research shows organisations often use commercial ALM platforms alongside custom tooling. The framework is markdown-driven, but teams might want to import requirements from Jama into the markdown source or export to Jama for auditor review.
- **How to resolve:** Out of scope for this synthesis. Propose a stage-2 follow-up: "Integration with external ALM tools (Jama, Polarion, Codebeamer)." The framework should remain markdown-first; if integration is needed, build it as a plugin/extension, not core.

**Question 4: How should the framework handle projects that mix granularities (some modules require requirement-level, others function-level)?**
- **Why it matters:** Claim 3 proposes per-module granularity declaration, but the research is not explicit on how mixed granularities within a single project scale.
- **How to resolve:** The framework already supports this via decomposition: each module declares its own granularity target. Validators are per-module. No additional research needed; the design supports mixing. Document: "Granularity is declared per module, not globally. A single project may have M1 at requirement-level and M2 at function-level; validators enforce each module's target independently."

**Question 5: What should happen when external traceability tools (e.g., Sphinx-needs, Codebeamer) are in use alongside the framework?**
- **Why it matters:** Some teams may use both the framework's markdown approach and a legacy ALM tool. The research emphasizes tool-neutrality but does not address co-existence.
- **How to resolve:** Accept the uncertainty. Document: "The framework is tool-agnostic; teams may use external tools in parallel (e.g., Jama for formal requirements, the framework for code annotation). Synchronisation between tools is a team responsibility, not the framework's. Manual export/import with validation is the safe boundary."

---

## Section 7: Confidence Assessment

**Overall confidence: HIGH (with nuance)**

The synthesis is grounded in five authoritative standards and regulator guidance ([1][5][9][12][14]) cited directly in the source research, plus peer-reviewed academic work documenting practical limitations ([17][18][21][22]). The source's citation discipline is strict (all claims tagged; 22-entry bibliography). Where the synthesis makes design recommendations (Claim 1 through Claim 7), each is traceable to empirical findings in Section 2 and backwards to the source.

**Strengths of the research:** The source is exceptionally strong on standards compliance and regulatory requirements. Five independent standards are covered, their traceability mandates are direct-cited, and their differences are clearly documented (DO-178C's unique object-code requirement, IEC 62304's permissiveness on bidirectionality, ISO 26262's strictness on granularity, etc.). The cross-standard comparison (Section 4 of the source) is a model of clarity. The source also incorporates academic and practitioner counter-arguments, making the research balanced.

**Where the research is thin:** The source does not provide deep guidance on implementation patterns for markdown-driven systems specifically. Section 6 of the source (the framework implications section) is the source author's synthesis, not external evidence. This is appropriate (it's where research meets design), but it means Claims 1–7 rest on the premise that "the framework's ID registry and phase gates can satisfy these standards," which is plausible but not externally validated. Recommend: prototype testing of the Assured bundle against a sample project to validate the claim that it satisfies, e.g., IEC 62304 or FDA requirements in practice.

**Confidence by claim:**
- Claim 1 (bidirectional traceability): HIGH. Three standards mandate it; two permit unidirectionality but practitioners implement bidirectionality. Consensus is clear.
- Claim 2 (change-impact annotation): HIGH. All standards require change-impact assessment; the annotation approach is pragmatic and supported by research showing post-hoc analysis is weak.
- Claim 3 (granularity declaration): MEDIUM-HIGH. Standards support declaration; adding it to the framework is straightforward but adds configuration complexity.
- Claim 4 (tool-neutral regenerability): HIGH. Two standards explicitly require regenerability; the framework already implements this.
- Claim 5 (change-impact gating): MEDIUM. IEC 62304 and FDA clearly require gating; making it optional hedges against unknown contexts. The balance is defensible.
- Claim 6 (export templates): HIGH. All standards are tool-neutral; export templates are a convenience with no downside.
- Claim 7 (disclaimer on certification): HIGH. Legally and technically sound; essential to set user expectations.

**Overall verdict: Proceed with implementation.** The synthesis provides clear, evidence-grounded guidance for finalising the Assured bundle's scope. The main risk is that the framework has not been tested against a real regulated project yet; recommend a proof-of-concept engagement (Stage 2 follow-up) before external launch.

---

## Summary for Framework Author

The research identifies a common floor of traceability obligations across five regulated-industry standards (DO-178C, IEC 62304, ISO 26262, IEC 61508, FDA 21 CFR Part 820): bidirectional or backward-confirmable traceability, granularity declaration, change-impact assessment, and tool-neutral evidence. The framework's proposed design (Method 1 phase gates + Method 2 ID registry, bidirectional indices, code annotations, decomposition model) satisfies this floor simultaneously. Key additions proposed:
1. Explicit backward-coverage validators (Claim 1)
2. Change-impact annotation skill and optional gating (Claims 2, 5)
3. Per-module granularity declaration (Claim 3)
4. Index-regenerability and freshness validation (Claim 4)
5. Audit-friendly export templates (Claim 6)
6. Clear out-of-scope boundaries (Claim 7)

None of these additions contradict any standard; most exceed the minimum requirement in at least one standard. The framework will be defensible as "assurance-grade substrate" for regulated projects while remaining lightweight and markdown-driven.
