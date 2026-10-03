# Overall Scope Update: Programme & Assured Bundles
## Cross-Line Research Synthesis & Design Decisions

---

## Section 1 — Cross-Line Agreements (Triangulated Findings)

### 1. Bidirectional Traceability Is the Regulatory Consensus

**Cross-cutting finding**: Five independent regulated-industry standards (DO-178C, IEC 62304, ISO 26262, IEC 61508, FDA 21 CFR Part 820) mandate or strongly converge on bidirectional traceability. The framework's design of forward-declaration (REQ→DES→TEST→CODE) with backward-regeneration (indices supporting queries like "what tests cover REQ-auth-003?") satisfies the strictest standard (ISO 26262) and does not exceed any standard's requirement.

**Lines agreeing**: Lines 1 (Regulated-Industry Traceability Standards) and 3 (ALM/Requirements-Tools Landscape). Line 1 provides the standards basis: DO-178C, IEC 62304, ISO 26262, IEC 61508, and FDA all mandate or converge on bidirectional traceability. Line 3 confirms that sphinx-needs (field-proven in regulated aerospace and automotive contexts) implements backward-regenerated indices, demonstrating the pattern is operationally viable.

**Combined confidence**: VERY HIGH. Three standards on Line 1 mandate bidirectionality; two permit unidirectionality but practitioners implement bidirectionality anyway for audit assurance. Line 3 provides proof of concept showing this pattern works in practice.

**Design decision**: The Assured bundle's bidirectional-traceability validators must enforce both directions: forward-link integrity (every cited ID exists in the registry; non-existent references block commit) and backward coverage (every REQ has at least one DES; every DES has at least one TEST; every TEST has at least one CODE annotation; every CODE annotation references a valid REQ/DES/TEST). This is the non-negotiable baseline.

**Affected scope sections**: METHODS.md Section 4, "Bidirectional traceability" subsection (lines 156–164).

---

### 2. Static Build-Time Link Validation Is Sufficient and Preferred

**Cross-cutting finding**: Line 1 shows that standards require traceability integrity but do not mandate real-time database constraints. Line 3 documents that sphinx-needs and Doorstop both use static link validation at build-time (no relational database), yet are field-proven in regulated contexts. Line 2 recommends annotation-driven code linking (static parsing of code comments), which naturally pairs with build-time validation.

**Lines agreeing**: Lines 1 (standards do not mandate runtime database enforcement), 2 (annotation-driven approach is inherently static), and 3 (sphinx-needs and Doorstop proof of concept using static validation).

**Combined confidence**: VERY HIGH. The convergence is complete: standards don't require real-time databases, the annotation-driven approach is static by nature, and proven open-source tools use static validation successfully.

**Design decision**: The `kb-rebuild-indexes` validator performs all link validation at build-time (pre-push validation). No relational database is introduced; the framework remains filesystem-first and Git-native. This satisfies all regulatory standards while avoiding DOORS-style lock-in and operational complexity.

**Affected scope sections**: METHODS.md Section 4, "ID registry" subsection (lines 139–146).

---

### 3. File-Based, Git-Native Storage Avoids Vendor Lock-In and Scales Better Than Database-Centric Approaches

**Cross-cutting finding**: Line 3 documents in detail how DOORS' relational model (.rmd binary format, DXL customization, organizational hierarchy baked into schema) created vendor lock-in, made migration impossible, and inflated operational cost. Line 3 confirms that open-source tools (sphinx-needs, Doorstop, strictdoc) all use file-based storage in Git, providing portability and auditability. Line 1 confirms that standards require evidence-regenerability (ISO 26262-8, IEC 61508), which is easier with file-based systems where the primary artefacts (requirements documents, code, test reports) are the source of truth.

**Lines agreeing**: Lines 1 (regenerability principle means files are primary), 3 (DOORS lock-in analysis; sphinx-needs file-based approach), and 2 (decomposition validators work on filesystem paths, not database schemas).

**Combined confidence**: VERY HIGH. The research documents both the negative example (DOORS lock-in) and positive examples (sphinx-needs, Doorstop) showing file-based works at scale in regulated contexts.

**Design decision**: Affirm the filesystem-first, markdown + YAML approach as a core architectural decision. Store each spec record as a markdown file with YAML frontmatter for metadata. Make this an explicit design statement to fend off future pressure to "add a database for faster queries."

**Affected scope sections**: METHODS.md Section 4, "Spec-as-KB-finding" subsection (lines 148–154).

---

### 4. Annotation-Driven Code-to-Spec Linking Is Simpler and More Portable Than Alternatives

**Cross-cutting finding**: Line 3 documents that DOORS' DXL extensibility (proprietary scripting language accumulating 1M+ lines of code in large deployments) created lock-in and brittleness. Line 3 compares DOORS to sphinx-needs (which uses plugin-based annotation parsing) and strictdoc (which uses a language-agnostic source-code parser without AST analysis). Line 2 recommends annotation-driven code indexing (code comments like `# implements: DES-005`) as the right pattern for avoiding AST-parsing complexity and IDE-plugin dependency. Line 1 supports this: standards require evidence but do not prescribe how code is tagged.

**Lines agreeing**: Lines 1 (standards-agnostic on tagging method), 2 (annotation-driven is simpler than AST), 3 (annotation-driven is simpler than DOORS DXL or IDE plugins).

**Combined confidence**: VERY HIGH. All three lines converge from different angles: standards don't prescribe the method, decomposition research recommends simplicity, and ALM landscape research shows proprietary approaches create lock-in.

**Design decision**: The `kb-codeindex` skill parses code comments with `implements:` tags. No AST parsing, no semantic search, no call graphs. This is deliberately simpler than DOORS' customization burden and simpler than strictdoc's source-parser. Document the trade-off explicitly: the cost is annotation maintenance; the benefit is vendor-independence and language-agnosticism.

**Affected scope sections**: METHODS.md Section 4, "KB extension to code (annotation-driven)" subsection (lines 182–194) and Section 6, "What is explicitly out of scope" (lines 232–240).

---

### 5. Domain-Driven Design Bounded Contexts Is the Decomposition Primitive

**Cross-cutting finding**: Line 2 conducts a survey of eight decomposition patterns (Bazel, Erlang/OTP, DDD, hexagonal, microservices, MBSE/SysML, ARINC 653, AUTOSAR) and recommends DDD bounded contexts as the highest-translatability pattern for a markdown-first framework. Line 2 also recommends layering Bazel's visibility-rule discipline on top. Line 3 documents that sphinx-needs has no decomposition primitive (flat structure, scaling limits above 500 pages) and DOORS' rigid hierarchy is unwieldy. Line 1 emphasizes that standards require granularity declaration (DO-178C scales by Level; ISO 26262 scales by ASIL) and that decomposition should be declarative. All three lines converge: DDD + Bazel visibility is the pattern.

**Lines agreeing**: Lines 1 (granularity declaration required; tool-neutral), 2 (DDD + Bazel recommendation explicit in synthesis), 3 (sphinx-needs flat-structure problem identified; DOORS hierarchy problem identified).

**Combined confidence**: VERY HIGH. Triangulation is complete: standards require decomposition/granularity, decomposition research explicitly recommends DDD, ALM research identifies gaps in existing tools.

**Design decision**: Use Domain-Driven Design's bounded-context concept as the primary decomposition abstraction. Layers Bazel's visibility-rule philosophy for cross-module dependencies. A "module" is a bounded context: a domain model with consistent ubiquitous language. Modules are grouped into sub-programs; sub-programs into programs. Teams declare context maps (markdown documents showing relationships). Validators enforce visibility rules (cross-module imports must respect declared dependencies) and detect anaemic contexts (code not co-located in its declared module).

**Affected scope sections**: METHODS.md Section 4, "Decomposition" subsection (lines 166–180).

---

### 6. Change-Impact Assessment Must Be Structured and Upfront, Not Automatic or Post-Hoc

**Cross-cutting finding**: Line 1 documents that IEC 62304 and FDA mandate change-impact assessment *before* implementation (blocking gate), while DO-178C and ISO 26262 require it as a procedure but less explicitly as a blocker. Line 1 cites practitioner research showing change-impact is often post-hoc in practice, which is a compliance-theatre red flag. Line 3 documents that commercial tools attempt to automate impact analysis (Polarion claims to do this), but the research does not evaluate success. Line 2 mentions traceability breakdown as a failure mode but does not prescribe change-impact methodology. Integrating Lines 1 and 3: the framework should support structured *annotation* of change impact (teams declare "REQ-005 changed; affected: DES-012, TEST-034, CODE-segment-B"), not automatic detection.

**Lines agreeing**: Lines 1 (structured annotation is the right level; gating is required for IEC 62304/FDA) and 3 (static validation is preferred over runtime intelligence).

**Combined confidence**: HIGH. Line 1 is clear on the regulatory need; Line 3 confirms that static annotation is the right pattern compared to automatic detection.

**Design decision**: Add a `change-impact-annotate` skill that guides teams through declaring impact scope when artifacts change. Optionally support a `change-impact-gate` validator (enabled by configuration for IEC 62304/FDA contexts) that blocks commits where code changes exist but no change-impact annotation is present. This makes impact analysis upfront and auditable, satisfying regulatory obligations while remaining human-decided and lightweight.

**Affected scope sections**: METHODS.md Section 4, "Bidirectional traceability" and "Skills shipped" subsections; new optional validator section.

---

### 7. Granularity Declaration (Requirement-Level vs. Function-Level vs. Module-Level) Must Be Declarative, Not Inferred

**Cross-cutting finding**: Line 1 documents that DO-178C scales traceability granularity by Level (Level A requires object-code level; Level D permits file-level). IEC 62304 scales by Class; ISO 26262 scales by ASIL. Line 1 explicitly recommends: "Granularity declaration should be declarative, not inferred." Line 2 recommends per-module granularity declaration in the decomposition registry. Line 3 documents that sphinx-needs has no per-module granularity concept (all needs are at the same granularity). All three converge: add granularity as a declarative field in the decomposition model.

**Lines agreeing**: Lines 1 (standards support per-system granularity; framework should make it explicit), 2 (per-module declaration recommended), 3 (sphinx-needs omits this; the framework should add it as innovation).

**Combined confidence**: HIGH. The need is clear from standards; the solution is clearly articulated in Line 2; the gap is identified in Line 3.

**Design decision**: Each module in the decomposition registry declares a granularity target (`granularity: [requirement | function | module]`). Validators enforce that actual traceability links match declared granularity. This makes the choice explicit and auditable, satisfying DO-178C's level-based scaling and ISO 26262's ASIL-based scaling.

**Affected scope sections**: METHODS.md Section 4, "Decomposition" subsection (lines 166–180).

---

### 8. Tool-Neutral Evidence Regenerability Is the Non-Negotiable Requirement

**Cross-cutting finding**: Line 1 documents that ISO 26262-8 and IEC 61508 both explicitly require that traceability be reconstructible from primary artefacts (requirements documents, source code, test reports) without tool dependence. If the tool becomes unavailable, the traceability must still be reconstructible. Line 3 confirms that file-based tools (sphinx-needs, Doorstop, strictdoc) satisfy this naturally because the primary artefacts are markdown in Git. Line 2 supports this with the regeneration-from-source design of the backward-indices. All three converge: evidence regenerability is non-negotiable.

**Lines agreeing**: Lines 1 (standards require regenerability explicitly), 2 (annotation-driven approach allows regeneration from source), 3 (sphinx-needs achieves this via file-based storage).

**Combined confidence**: VERY HIGH. Standards mandate it; research confirms it's achievable; proof of concept exists.

**Design decision**: Ensure that `kb-rebuild-indexes` is idempotent and regenerates all backward-indices (shelf-index, code-index) from markdown source without tool dependence. Document this explicitly: auditors can regenerate indices from markdown source to verify link integrity; tool choice is immaterial to traceability validity. This satisfies the regenerability principle and protects against tool lock-in.

**Affected scope sections**: METHODS.md Section 4, "KB extension to code" subsection (lines 182–194) and documentation of skills.

---

## Section 2 — Cross-Line Conflicts

**Finding**: No material conflicts exist between the three research lines. All three research lines are addressing different facets of the same design space (traceability standards, decomposition patterns, ALM tool patterns) and their recommendations integrate without contradiction.

**Potential tensions resolved**: Line 2 recommends DDD bounded contexts; Line 3 documents that sphinx-needs has no decomposition concept. This is not a conflict but a gap: the Assured bundle should add what sphinx-needs omits (explicit decomposition primitive). Line 1 emphasizes bidirectionality; Line 2 emphasizes annotation-driven code linking; Line 3 confirms both patterns exist in sphinx-needs. No contradiction; all reinforce each other.

**Conclusion**: The three research lines show strong lateral coherence. This is a sign of research quality: independent lines converging on the same design directions (DDD + Bazel + annotation-driven + file-based + bidirectional + static validation) suggests high confidence in the recommendations. If the lines had conflicted, we would have needed to arbitrate. The absence of conflict is itself a strong signal.

---

## Section 3 — Integrated Scope Changes for Method 1 (Programme Bundle)

### Change 1: Clarify Phase Gates' Blocking Scope
**Scope section**: METHODS.md Section 3, "Phase gates" subsection (lines 73–82).
**Change type**: Clarify.
**Driving findings**: [Line 1: Section 3, Claims 1 & 5] (bidirectional traceability and change-impact obligations). [Line 3: Section 3, Claims 1-3] (file-based validation is sufficient).
**Summary**: Strengthen phase-gate enforcement to explicitly require "no broken links" in cross-phase references.

### Change 2: Add Traceability-Export Skill to Programme Bundle
**Scope section**: METHODS.md Section 3, "Skills shipped (Programme bundle)" subsection (lines 96–101).
**Change type**: Add.
**Driving findings**: [Line 1: Section 3, Claim 6] (traceability evidence export should be template-driven, not tool-specific).
**Summary**: New skill `traceability-export <format>` produces audit-friendly matrices in standard-specific formats. Programme bundle exports simple formats; Assured bundle supports DO-178C, IEC 62304, ISO 26262, FDA formats.

### Change 3: Strengthen Model Selection Guidance
**Scope section**: METHODS.md Section 3, "Model selection hints" subsection (lines 103–105).
**Change type**: Clarify.
**Driving findings**: [Cross-line agreement 1] (bidirectional traceability is standard baseline; complexity is distributed, not concentrated in one skill).
**Summary**: Make explicit that phase-review is a structured comparison task requiring models with strong reasoning; phase-gate is mechanical syntax-checking suitable for smaller models.

### Change 4: Make Phase-Review Skill Mandatory
**Scope section**: METHODS.md Section 3, "Skills shipped (Programme bundle)" subsection (lines 96–101).
**Change type**: Clarify.
**Driving findings**: [Cross-line agreement 1] (bidirectional traceability requires link integrity; human review is the control that ensures not just existence but *meaningfulness* of links).
**Summary**: `phase-review <phase>` is mandatory for design-phase artefacts (design-spec, test-spec); recommended for requirements-spec. Human-in-the-loop review ensures links are not just syntactically correct but semantically sound.

---

## Section 4 — Integrated Scope Changes for Method 2 (Assured Bundle)

### Change 1: Enrich Decomposition with DDD and Bazel Visibility Concepts
**Scope section**: METHODS.md Section 4, "Decomposition" subsection (lines 166–180).
**Driving findings**: [Cross-line agreements 1, 5] (DDD + Bazel visibility converged recommendation). [Line 2: Section 3, Claims 1, 2, 4, 7] (DDD bounded contexts; Bazel visibility discipline; anaemic-context detection; deferral guidance).
**Summary**: Replace generic decomposition language with explicit DDD terminology. Add visibility rules (program-level visibility, circular-dependency detection). Add granularity targets per module. Add validators to detect anaemic contexts and enforce visibility.

### Change 2: Support Decomposition Refactoring Without ID Invalidation
**Scope section**: METHODS.md Section 4, "ID registry" subsection (lines 139–146).
**Driving findings**: [Line 2: Section 3, Claim 6] (support decomposition refactoring without ID invalidation to mitigate premature-decomposition risk).
**Summary**: `kb-rebuild-indexes` supports decomposition refactoring: when the programs block is reconfigured, remaps old IDs to new paths, preserving historical traceability. Enables teams to learn and adjust initial decomposition without losing history.

### Change 3: Strengthen Code-Annotation Validation and Add Code-Annotate Skill
**Scope section**: METHODS.md Section 4, "Bidirectional traceability" and "Skills shipped" subsections.
**Driving findings**: [Cross-line agreement 4] (annotation-driven is the right pattern). [Line 2: Section 3, Claim 5] (validators must enforce annotation format; report coverage gaps). [Line 1: Section 3, Claim 2] (change-impact annotation must be supported).
**Summary**: Add annotation-format-integrity validator. Add `code-annotate <artifact-id>` skill to auto-generate boilerplate annotations, reducing manual burden.

### Change 4: Add KB-Extension Support for Hexagonal Architecture (Optional)
**Scope section**: METHODS.md Section 4, "KB extension to code (annotation-driven)" subsection (lines 182–194).
**Driving findings**: [Line 2: Section 3, Claim 3] (optional hexagonal-architecture support for teams wanting within-module isolation).
**Summary**: Code may be annotated with role tags (`core` for domain logic, `adapter` for infrastructure). `traceability-render` visualizes domain-logic density per module, detecting boundary violations.

### Change 5: Add Change-Impact Annotation Skill and Optional Gate
**Scope section**: METHODS.md Section 4, "Skills shipped" subsection and new optional validators subsection.
**Driving findings**: [Cross-line agreement 6] (change-impact must be structured and upfront). [Line 1: Section 3, Claims 2, 5] (structured annotation supports regulatory obligations).
**Summary**: New skill `change-impact-annotate` guides teams through declaring impact scope. Optional `change-impact-gate` validator (default: disabled) blocks commits lacking change-impact annotation; recommended for IEC 62304/FDA/ISO 26262 contexts.

### Change 6: Add Traceability-Export Skill with Standard-Specific Formats
**Scope section**: METHODS.md Section 4, "Skills shipped (Assured bundle)" subsection (lines 202–208).
**Driving findings**: [Line 1: Section 3, Claim 6] (traceability evidence export should be template-driven, supporting all major standards).
**Summary**: New skill `traceability-export <format>` produces audit-friendly matrices in standard-specific formats: DO-178C RTM, IEC 62304 risk-control matrix, ISO 26262 ASIL matrix, FDA DHF structure.

### Change 7: Add Granularity Validation to Validators
**Scope section**: METHODS.md Section 4, "Decomposition" subsection.
**Driving findings**: [Cross-line agreement 7] (granularity declaration must be declarative). [Line 1: Section 3, Claim 3] (granularity declaration should be explicit and validated).
**Summary**: Add validator: if module M1 declares `granularity: requirement`, all code must carry REQ-level annotations; if M2 declares `function`, function-level annotations suffice. Warn if actual granularity is underspecified.

### Change 8: Add Commissioning Guidance Subsection
**Scope section**: METHODS.md Section 4, new subsection "Commissioning guidance" (add after "Skills shipped").
**Driving findings**: [Line 2: Section 3, Claim 7] (commissioning guidance must emphasize deferring decomposition). [Line 1: Section 3, Claims 1, 5] (granularity declaration and change-impact gating are optional at commission time).
**Summary**: Commissioning guidance for decomposition strategy, change-impact gating defaults, and granularity targets. Emphasis on starting simple, deferring until pain appears.

### Change 9: Strengthen Out-of-Scope Statement on Certification and Add ReqIF Disclaimer
**Scope section**: METHODS.md Section 6, "What is explicitly out of scope" (lines 232–240).
**Driving findings**: [Line 1: Section 3, Claim 7] (certified compliance is out of scope; the framework produces substrate). [Line 3: Section 3, Claim 7] (ReqIF should not be a core feature; one-way export only, as plugin).
**Summary**: Expand "Industry certification itself" to clarify the framework produces assurance substrate, not certification. Add new bullet on ReqIF: one-way export supported; round-trip is lossy by design.

### Change 10: Add Organisational Metadata and Process Concerns Subsection
**Scope section**: METHODS.md Section 4, new subsection "Organisational Metadata and Process Concerns" (add after "Decomposition").
**Driving findings**: [Line 3: Section 4, Rejection C] (org structure should not be baked into spec schema; prevents team reorganization from requiring data migration).
**Summary**: Organisational metadata (owner, reviewer, approver) is optional in YAML. Process enforcement is workflow-tool concern, not spec-schema concern.

---

## Section 5 — Decomposition Primitive — Final Call

The framework should adopt **Domain-Driven Design bounded contexts as the primary decomposition unit, layered with Bazel's visibility-rule discipline, with optional hexagonal architecture for within-module structure**.

### Rationale

DDD bounded contexts are the highest-translatability pattern for a markdown-first framework [Line 2: Section 2.2]. They require no build system or runtime—they are pure code organization and team discipline. Contexts map directly to modules in the declarative decomposition registry. Validation is achievable via filesystem checks (imports respect declared visibility) and code-location co-location rules (code implementing a REQ/DES is found in the declared module). This satisfies the framework's constraints: no runtime, no specialized tooling, no lock-in.

Bazel's visibility-rule philosophy complements DDD: teams declare which modules (contexts) may depend on which, enforced via validators that check code imports. This prevents the most dangerous failure mode in decomposed systems: dependency proliferation leading to circular dependencies and anaemic contexts (business logic scattered across modules rather than concentrated in domain models) [Line 2: Section 2.4].

Hexagonal (ports-and-adapters) architecture is optional for teams wanting further within-module isolation. This pattern is lightweight: code is organized into `core` (domain logic) and `adapter` (infrastructure) directories. Annotations tag code locations accordingly. `traceability-render` visualizes domain-logic density per module, helping teams detect when the separation is violated.

The commissioning guidance must emphasize deferral: decomposition should reflect current business domains and organizational structure, not speculative future architecture. This prevents premature decomposition (a major risk documented in Line 2) by explicitly steering teams toward starting simple (default `P1.SP1.M1.*`) and refactoring when operational pain appears.

### Failure Mode the Framework Designs Against

The explicit failure mode is **anaemic contexts** [Line 2: Section 2.4]: business logic scattered across modules rather than concentrated in domain models, rendering context boundaries meaningless. This manifests as code that implements a REQ/DES not co-located in its declared module, orphan code with no annotations, or contexts with only infrastructure code and no domain logic.

The framework detects and prevents this via validators that flag code-to-module assignment violations and orphan code. The `traceability-render` skill highlights code locations, making violations visible during code review. The commissioning guidance emphasizes that a module should be "the scope of responsibility for one team (or part of one team)", providing a human heuristic for avoiding over-fragmentation.

This is a deliberate choice to favor **cohesion over coupling prevention**: the framework assumes that if you define a bounded context, you will put the logic that belongs there into it. That is a team discipline problem, not a framework problem. The framework validates coherence (logic is co-located, not scattered) and provides visibility (traceability-render shows the structure). It does not attempt to *prevent* bad decomposition decisions (that is a commissioning-time choice) or to *suggest* correct decomposition (that requires domain knowledge the framework does not have).

---

## Section 6 — Traceability Rigour Calibration — Final Call

The Assured bundle natively supports the traceability baseline defined by the strictest regulated-industry standard (ISO 26262: bidirectional traceability at requirement-level granularity, with change-impact assessment, across all ASIL levels). This baseline is simultaneously compatible with the four other major standards (DO-178C, IEC 62304, IEC 61508, FDA 21 CFR Part 820), each of which either mandates bidirectionality or (in IEC 62304's case) permits unidirectionality while practitioners implement bidirectionality for audit assurance anyway [Line 1: Section 2, empirical findings].

### What We Will Natively Support

1. **Bidirectional link integrity**: Forward declaration (REQ→DES→TEST→CODE) with backward-regenerated indices supporting queries like "what tests cover REQ-auth-003?" or "what code implements DES-auth-005?". Validators block on broken links and orphan IDs.

2. **Granularity declaration and enforcement**: Each module declares a granularity target (`requirement`, `function`, or `module`). Validators ensure actual traceability links match the declaration. This satisfies DO-178C's level-based scaling and ISO 26262's ASIL-based scaling.

3. **Change-impact annotation**: Teams declare impact scope when artifacts change (e.g., "REQ-005 changed; affected: DES-012, TEST-034"). The framework records these annotations and can generate change-impact reports for audit trails. This satisfies IEC 62304 and FDA's gating requirements.

4. **Static, build-time link validation**: All validation occurs at pre-push validation and CI time, via the `kb-rebuild-indexes` skill. No runtime database constraints; Git is the source of truth. This satisfies the tool-neutrality principle.

5. **Annotation-driven code-to-spec linking**: Code comments carry `implements: REQ/DES/TEST` tags. The `kb-codeindex` skill parses these and builds a shelf-index-shaped code-index queryable by the librarian. This is language-agnostic.

6. **Structured review records**: The `phase-review` skill (Method 1) and traceability-review workflows (Method 2) produce human-signed review records committed alongside reviewed artefacts. These satisfy the "independent review" obligation in several standards.

### What We Support via Documented Extension Points

1. **Traceability export in external formats**: The `traceability-export` skill produces audit-friendly matrices in standard-specific formats. These are derivative; the authoritative source remains markdown in Git.

2. **Change-impact gating enforcement**: The optional `change-impact-gate` validator enforces that code commits lack change-impact annotation. Disabled by default; teams in IEC 62304/FDA/ISO 26262 contexts enable at commissioning.

3. **Decomposition refactoring without ID loss**: The `kb-rebuild-indexes` skill supports remapping old IDs to new module paths. Mitigates premature-decomposition risk.

4. **Hexagonal architecture tagging**: Code can be annotated with structural role (`core` vs `adapter`). Validators and `traceability-render` highlight domain-logic concentration and boundary violations.

### What We Will Explicitly Not Promise

The Assured bundle will not promise automatic change-impact detection. This requires semantic analysis (call graphs, data-flow analysis) or AI-driven reasoning, incompatible with markdown-first philosophy. Change-impact is human-annotated. Teams maintain change-impact records manually, which is a compliance discipline cost but avoids false positives.

The framework will not promise that traceability links are *meaningful*, only that they are *correct*. Whether a test actually exercises a requirement is a human responsibility (auditor's concern) and team discipline issue (reviewer's responsibility). The framework validates syntax; semantics are verified by human review.

The framework will not promise real-time database queries or complex requirements analytics. The markdown + static-validation approach trades query flexibility for portability. Teams can build analytics on top of generated indices, but the framework provides basic queries only.

The framework will not enforce identity-verification or approval-chain workflows at the schema level. Organisational metadata is optional in YAML. Process enforcement is a Git hook / workflow tool concern, not a spec-schema concern. This prevents the framework from breaking when organizations reorganize.

---

## Section 7 — Sphinx-Needs Adoption Boundary

The Assured bundle adopts sphinx-needs' foundational patterns: declarative need-type schema, static build-time link validation, file-based Git-native storage, and annotation-driven code-to-spec linking via plugins. These patterns are proven in regulated aerospace and automotive contexts [Line 3: Section 2].

### Patterns We Adopt from Sphinx-Needs

1. **Declarative need-type schema**: Each spec type (REQ, DES, TEST, CODE) is configured with allowed fields, field types, link validation rules, and rendering hints. This allows teams to customize spec structure while keeping core validation unchanged. Scales to multiple spec types better than sphinx-needs' flat identifier scheme.

2. **Static, build-time link validation**: All link checking occurs when `kb-rebuild-indexes` runs. No relational database; Git commits are atomic checkpoints of link integrity. This is how sphinx-needs achieves compliance-grade rigor without operational complexity.

3. **File-based, Git-native storage**: Each spec record is a markdown file with YAML frontmatter. Git history is the audit trail. Auditors can clone the repo and regenerate indices from markdown source without depending on a tool. Core of portability and auditability.

4. **Annotation-driven code parsing**: Code comments carry `implements: ID` tags. The `kb-codeindex` skill parses these; no AST analysis. Simpler than strictdoc's source-code parser and less burdensome than DOORS' DXL.

5. **Modular rendering (traceability-render)**: A skill produces human-scoped views of one module: just its REQs, just its DEsigns, just its tests, just its code locations, with all inter-ID links rendered as anchor links. Derivative artefact; authoritative source is markdown files. Supports large systems without requiring complex tool UI.

### Patterns We Deliberately Do Not Adopt from Sphinx-Needs

1. **Flat identifier scheme (REQ_001, TEST_042 with no context)**: Sphinx-needs uses simple auto-increment, which works for single-document projects but loses context at scale. The Assured bundle uses `P1.SP2.M3.REQ-007` to make program/module context visible at a glance and to facilitate decomposition [Line 2: Section 3.1; Line 3: Section 3, Claim 6].

2. **No built-in decomposition primitive**: Sphinx-needs has no concept of decomposition beyond document-level organization. The Assured bundle adds a declarative program/sub-program/module registry with visibility-rule enforcement [Line 2: Section 3, Claims 1-2]. This allows large systems to bound scope per module, reducing agent context and preventing anaemic contexts.

3. **Dynamic functions (computed fields referencing other needs)**: Sphinx-needs allows markdown directives like `.. needs_link_to_other_needs::` executed at build time. Powerful but steep learning curve; difficult to debug [Line 3: Section 2]. The Assured bundle supports simpler annotation-based linking with no computed functions. Less dynamic but more transparent.

4. **Multiprocessing for large projects**: Sphinx-needs uses multiprocessing for 25K+ pages, but build times exceed 30 minutes and memory exceeds 32 GB [Line 3: Section 2]. The Assured bundle assumes reasonable project size (up to ~5K specs per module) and targets single-process execution. If a project exceeds this, teams should refactor into multiple git repos, each with its own KB.

5. **Rich-text field support**: Sphinx-needs supports rich-text in RST; makes round-trip export (e.g., to ReqIF) lossy [Line 3: Section 3]. The Assured bundle uses markdown (plain text + links), which round-trips cleanly and resists feature creep.

6. **Sphinx-based rendering and documentation generation**: Sphinx-needs produces HTML via Sphinx. The Assured bundle produces markdown indices and optional HTML exports (via traceability-export skill), but does not require Sphinx. Keeps toolchain lightweight; teams choose their own documentation generator.

---

## Section 8 — Reference Discipline for the Framework's Own Artefacts

The Assured bundle should model the reference discipline it enforces, making the framework's own specifications cite their origins and design records cite requirements.

**Proposal**: Requirements should cite their origin (research finding citing the synthesis line, regulated-industry standard with citation, or design decision citing the design spec). Design records should cite which requirements each design decision satisfies, creating an internal traceability matrix. The synthesis layer should cite back to research using [Line N: Section X entry Y] form, creating a complete chain: research → per-line synthesis → overall synthesis → design spec → code annotations. Implementation rationale should be documented in code comments referencing design spec sections and research rationale.

**Benefit**: Transparency (teams and auditors see why each constraint exists); traceability of governance (if a standard changes, maintainers quickly identify affected components); inheritance of discipline (teams see by example how to cite their own requirements and design decisions); defensibility (certification auditors can see the research basis).

---

## Section 9 — Open Questions Remaining for Stage 4

**Q1: How to Visualize Module Dependency Graphs?** Line 2 recommends `traceability-render` should visualize the module dependency graph, but exact output format is not specified. **Resolution path**: Prototype during Stage 4. Options: ASCII DAG, HTML SVG graph, markdown table. Accept visualization will be lossy at large scale (50+ modules). **Blocks plan-writing**: No.

**Q2: Visibility Violations — Block, Warn, or Advisory?** Framework does not specify enforcement level. Violations might indicate design issues or stale decomposition registry. **Resolution path**: Recommend strict warning (visible in pre-push, must be acknowledged, does not block push) until commissioning team opts into strict mode. Strict mode recommended for regulated-industry projects. **Blocks plan-writing**: No.

**Q3: How Fine-Grained Should Module Boundaries Be?** Framework recommends DDD bounded contexts but does not specify size. **Resolution path**: Accept as team-driven design choice. Provide heuristic: "A module should be the scope of responsibility for one team." Defer specific metrics to post-dogfooding. **Blocks plan-writing**: No.

**Q4: Should the Framework Support "Soft" Decomposition?** Assured bundle defaults to enforced decomposition; some teams might want advisory (warnings, not errors). **Resolution path**: Support both modes (enforced for regulated/assured contexts; advisory for exploratory). Configurable at commissioning. **Blocks plan-writing**: No.

**Q5: What is the Right Cycle for Index Regeneration?** Line 1 proposes warning if indices stale (>7 days). No standard prescribes refresh frequency. **Resolution path**: Accept uncertainty. Default: 7 days. Teams adjust per context. Threshold is convenience flag, not compliance requirement. **Blocks plan-writing**: No.

**Q6: Should the Framework Support Integration with External Requirements Tools?** Research shows organizations use commercial ALM platforms alongside custom tooling. **Resolution path**: Out of scope. Propose Stage 2 follow-up on "Integration with external ALM tools (Jama, Polarion, Codebeamer)." Framework remains markdown-first; if integration needed, build as plugin. **Blocks plan-writing**: No.

---

## Section 10 — Recommended Next Action

**(a) Update the design spec with these scope changes and proceed to writing-plans.**

The three research lines show strong convergence on design decisions: bidirectional traceability (Lines 1 and 3), DDD + Bazel decomposition (Lines 1, 2, 3), static link validation (Lines 1 and 3), annotation-driven code linking (Lines 1, 2, 3), file-based storage (Lines 1 and 3), and change-impact annotation (Lines 1 and 3). No material conflicts exist; all eight cross-line agreements integrate without contradiction. Open questions (visualization format, soft vs. hard decomposition, tool integration) are implementation details resolvable during Stage 4 via prototype experiments.

Scope changes are focused and grounded: ten changes to Method 2 (Assured bundle) and four changes to Method 1 (Programme bundle), each traced to specific research findings. The framework is defensible against regulated-industry scrutiny (traceability standards, change-impact obligations, tool-neutrality), pragmatic in implementation (no semantic analysis, no database, no AST parsing), and risk-aware (flagging anaemic contexts, premature decomposition, lock-in).

**Proceed to Stage 4 (implementation planning and plan-writing) immediately.** Dogfood the Assured bundle on an internal EPIC (candidate: EPIC #142 sub-features 3–8) to validate that the design satisfies regulatory and assurance-quality expectations in practice.

---

**End of Overall Scope Update**
