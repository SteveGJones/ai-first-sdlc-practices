# Stage 3 Synthesis: Decomposition Patterns in Practice

---

## Section 1: Source Attestation

**Research output**: `/Users/stevejones/Documents/Development/ai-first-sdlc-practices/research/sdlc-bundles/outputs/02-decomposition-patterns/output-1.md`  
**Word count**: 10,252 words  
**Total citations**: 24 (all properly tagged with `[N]` references)  
**Bibliography entries**: 24 (complete, with source-type tags and credibility notes)

**Citation discipline**: Excellent. Every substantive claim in the source research carries a citation. The bibliography includes source-type tags (`[vendor-doc]`, `[peer-reviewed]`, `[book]`, `[standard]`, `[practitioner-blog]`, `[conference-paper]`, `[tech-report]`) and credibility notes contextualizing each source's authority. Section 6 (Implications for Our Framework), which carries the highest design weight, is densely cited: every pattern recommendation and failure-mode mitigation traces back to specific bibliography entries.

**Source quality**: HIGH confidence overall. The research surveyed eight decomposition patterns across diverse domains (build systems, runtime frameworks, domain modeling, distributed systems, formal methodologies, avionics, automotive). Pattern sources are authoritative (e.g., Evans' DDD book, Armstrong's Erlang thesis, official standards from OMG/ARINC/AUTOSAR) and/or peer-reviewed. Failure-mode and counter-argument citations span both academic (Brooks' "No Silver Bullet," Conway's Law) and practitioner evidence (Newman's microservices books, Segment's monolith reversal case study, MBSE/SysML adoption studies). No vendor-only sourcing for criticism; negative claims are grounded in published academic or standard-setting sources.

**Caveats**: 
- The research is strongest on the conceptual mapping between patterns and the framework's markdown-first constraints. It is less detailed on the specifics of validator implementation (e.g., the exact form of visibility-rule checkers or the mechanics of dependency-graph visualization). Implementation design deferred to coding stage.
- One boundary case: the research cites practitioner case studies (Segment, Netflix, Amazon microservices reversals) via blogs and conference talks rather than refereed journals. The lesson (premature decomposition is costlier than premature consolidation) is cited well and appears in multiple independent sources ([20]), so the claim is solid despite the source type.

---

## Section 2: Empirical Findings

### 2.1 Eight Decomposition Patterns Surveyed

**The research evaluated**:
1. **Bazel build graphs** [1]: Decomposition via BUILD targets and packages; explicit dependency declarations; compile-time boundary enforcement.
2. **Erlang/OTP supervision trees** [2]: Process-level decomposition; supervisor hierarchy; runtime-enforced failure isolation and restart semantics.
3. **Domain-Driven Design bounded contexts** [3][12]: Business-domain-driven boundaries; ubiquitous language per context; team discipline, not tool-enforced.
4. **Hexagonal (ports-and-adapters) architecture** [9]: Domain logic isolated from infrastructure adapters; testability via port interfaces; within-module isolation.
5. **Microservices architecture** [4][5]: Decomposition at deployment boundary; independent services; network isolation; organizational alignment per Conway's Law [21].
6. **MBSE/SysML** [6][15][16]: Formal hierarchical system modeling; tool-supported metamodel conformance; allocation tables; heavy tool overhead.
7. **ARINC 653** [7][17][18]: Space-time partitioning in avionics; hardware MMU enforcement; real-time OS isolation; criticality-level separation.
8. **AUTOSAR** [8][19]: Automotive software architecture; RTE (Run-Time Environment) abstraction; code generation overhead; component-level decomposition.

### 2.2 Translatability to Markdown-First Framework

**Key finding**: Not all patterns transfer equally to a markdown-declared, filesystem-first system without a build system or runtime. [1][3]

- **HIGH translatability**: Bazel's concepts (packages, visibility rules, explicit dependency graphs) transfer readily to markdown registries and validators. DDD's bounded contexts require no build system or runtime—they are pure code organization and team discipline. [1][3][12]
- **MODERATE translatability**: Erlang/OTP concepts (hierarchy, restart semantics, failure isolation) are conceptually clear but validators cannot recreate runtime isolation or automatic recovery. [2]
- **LOW translatability**: MBSE/SysML, ARINC 653, AUTOSAR all depend on specialized tooling (formal modeling tools, real-time OS, code generators) that a markdown framework does not own. [6][7][8][15][16][19]

### 2.3 Boundary Declaration and Enforcement Mechanisms

**Three categories of enforcement**:

1. **Build-time**: Bazel's compile-time violation detection via BUILD-file dependency analysis. Strength: precision. Weakness: maintenance burden at scale. [1][10]

2. **Runtime**: Erlang/OTP supervisors actively monitor and respond to process crashes. ARINC 653 and AUTOSAR rely on hardware/OS enforcement. Strength: guaranteed isolation. Weakness: requires runtime ownership. [2][7][8][18]

3. **Team discipline + linting**: DDD, hexagonal architecture, microservices rely on code structure, documentation, and team consensus, with optional code review and static analysis support. Strength: tool-agnostic, low infrastructure cost. Weakness: human-dependent, harder to audit at scale. [3][4][5][9][21]

### 2.4 Failure Modes from the Literature

**Critical failure modes identified**:

1. **Anaemic contexts** [13]: Business logic is scattered across modules rather than concentrated in domain models, rendering context boundaries meaningless.

2. **Premature or over-decomposition** [20]: Teams decompose before business boundaries stabilize or operational pain is acute, paying high coordination cost without benefit. Segment's reversal from 200+ microservices to a modular monolith is canonical.

3. **Cross-module dependency proliferation** [1][10]: If every module can depend on every other, visibility rules become meaningless. At large scale, build-file maintenance becomes error-prone.

4. **Traceability breakdown** [24]: As systems grow, maintaining forward and backward traceability (REQ → DES → TEST → CODE) becomes tedious. Developers skip annotations; format drifts; orphan code appears.

5. **Distributed monolith anti-pattern** [14]: Teams decompose at deployment boundary without clear business value, inheriting all the operational complexity of distributed systems while losing monolith's simplicity.

6. **Tool lock-in and abandonment** [15][16]: MBSE/SysML adoption is hindered by steep learning curves and tool complexity. If framework depends on specialized tool, adoption is gated on tool licensing and training.

### 2.5 DDD Bounded Contexts as Primary Recommendation

**Direct statement from research**: "The strongest recommendation is to borrow Domain-Driven Design's bounded-context concepts and combine them with Bazel's visibility-rule discipline, with a fallback to hexagonal architecture's port-and-adapter pattern for within-module structure." [3][12][1][9]

**Rationale cited**:
- Translatability paramount: DDD is pure team discipline, no build system or runtime required. [3][12]
- Bounded contexts map directly to modules: a context is bounded by ubiquitous language and domain model. [3][12]
- Enforcement achievable via validators: module assignment checks, cross-module dependency documentation, vocabulary consistency linting. [3][12][1]
- Bazel visibility discipline complements DDD: translates Bazel's visibility rules to markdown-declared module dependencies. [1]
- Failure modes manageable: anaemic contexts and scattered logic are detectable via code review and linting. [13]

### 2.6 Aspects NOT to Borrow

**Explicitly rejected approaches**:

1. **MBSE/SysML's tooling requirement** [15][16]: Formal analysis is lost if tool is removed. Framework should remain tool-agnostic (text editors + Git); borrow SysML's conceptual hierarchy but implement as markdown registries.

2. **ARINC 653's runtime-isolation assumption** [7][18]: Partition isolation requires real-time OS and hardware MMU. Markdown declarations are aspirational, not binding. If runtime isolation is needed, that is a deployment-level concern orthogonal to SDLC.

3. **Erlang/OTP's process-boundary assumption** [2]: Supervision trees work because Erlang runtime isolates processes and supervisors actively monitor/restart. Markdown declarations without runtime isolation are misleading.

4. **Microservices' independent-deployment assumption** [4][5]: Method 2 is whole-system (not service-level); modules are not independently deployed. If future independent deployment is desired, that is a deployment refactor, not SDLC-level.

5. **Bazel's full dependency-graph management** [1][10]: Bazel's BUILD files are verbose for small teams and designed for multi-language, multi-platform complexity. Framework should borrow visibility philosophy, not full BUILD-graph burden.

---

## Section 3: Claims to Incorporate

**Claim 1: DDD Bounded Contexts as the Decomposition Primitive**

**Source citation**: [3][12]

**Design decision**: Method 2's decomposition model should use Domain-Driven Design's bounded-context concept as the primary abstraction. A "module" in the Assured bundle's decomposition registry is a bounded context: a domain model with consistent ubiquitous language. The commissioning step (METHODS.md Section 4, Decomposition subsection) should document that teams declare programs, sub-programs, and modules using DDD terminology, and that the `module-bound-check` validator verifies all REQ/DES/TEST/CODE IDs are assigned to declared contexts. Teams should use DDD's "context maps" (markdown documents showing how contexts relate) as the cross-module dependency documentation.

**Affected scope section**: METHODS.md Section 4, subsection "Decomposition" (lines 166-180). Currently states: "Decomposition is **declarative**, not inferred... The team declares it; the framework enforces what is declared." Should be enriched to specify DDD bounded-context terminology and context-map documentation.

**Confidence**: HIGH. The research was explicitly commissioned to answer "which decomposition primitive should the framework borrow concepts from?" Section 6.1 directly recommends DDD bounded contexts with detailed rationale (translatability, module-mapping, validator achievability, failure-mode manageability). The source is authoritative (Evans' DDD book [3] is canonical; Vernon's implementation guide [12] is the practical companion). No conflicting sources.

---

**Claim 2: Bazel Visibility-Rule Discipline for Cross-Module Dependencies**

**Source citation**: [1]

**Design decision**: Layer Bazel's visibility-rule philosophy on top of DDD bounded contexts. Declare which modules (contexts) may depend on which, enforced via validators that check filesystem imports. Programs should be loosely coupled: sub-programs within a program can depend on each other, programs can depend on a shared/core program, but circular dependencies between programs should be flagged as violations. The `traceability-render` skill should visualize the module dependency graph. Add guidance to templates and commissioning docs that programs are loosely coupled and circular program dependencies require architectural approval.

**Affected scope section**: METHODS.md Section 4, subsection "Decomposition" (lines 166-180). New sub-point: "Module visibility rules" — cross-module dependencies are declared in a context-map document; validators check that code imports respect declared visibility; circular dependencies between programs are flagged as violations.

**Confidence**: HIGH. The research recommends Bazel's visibility discipline as a complement to DDD [1] and explicitly states: "declare which modules can depend on which, and validate via filesystem checks (import statements in code should respect declared visibility), not via a build system" (Section 6.1). This is implementable via validators and fits the markdown-first paradigm.

---

**Claim 3: Hexagonal Architecture for Within-Module Structure (Optional)**

**Source citation**: [9]

**Design decision**: For teams wanting further within-module isolation, recommend hexagonal architecture (ports-and-adapters) to separate domain core from infrastructure adapters. This is optional; the framework should support annotation of modules as "hexagonal-structured" but not require it. The KB-codeindex skill can be extended to tag code locations as "core" vs "adapter" based on package/directory structure, supporting visualization of domain-logic density per context.

**Affected scope section**: METHODS.md Section 4, subsection "KB extension to code (annotation-driven)" (lines 182-194). Add note: "Modules may optionally declare internal structure via hexagonal architecture; code-index tags can distinguish domain core from infrastructure adapters."

**Confidence**: MEDIUM-HIGH. The research recommends hexagonal architecture as a "fallback for within-module structure" [9] but notes it is optional ("optionally adopt hexagonal architecture... to further reduce coupling and improve testability" — Section 6.1). The recommendation is sound and implementable as optional annotation, but lower priority than DDD contexts + Bazel visibility.

---

**Claim 4: Design Validators to Detect Anaemic Contexts**

**Source citation**: [13]

**Design decision**: The `module-bound-check` and `kb-codeindex` validators should explicitly detect anaemic contexts: code that implements a REQ/DES is not co-located in the declared module. Validators should flag orphan code (code that does not reference any REQ/DES/TEST). The `traceability-render` skill should highlight code locations, making orphan code and context violation visible to developers. A code-annotation guide (similar to existing templates) should emphasize that all application code should reference the REQ/DES it implements.

**Affected scope section**: METHODS.md Section 4, subsection "KB extension to code (annotation-driven)" (lines 182-194) and "Validators" (implicit in the context-binding validators). New requirement: validators should report code-to-module assignment violations and orphan code.

**Confidence**: HIGH. The research identifies anaemic contexts as a primary failure mode [13] and explicitly recommends this mitigation in Section 6.2: "Validators should check that code implementing a REQ/DES is co-located in the declared module... `kb-codeindex` skill will flag orphan code (code that does not reference any REQ/DES/TEST)." This is implementable and directly addresses a major risk in large systems.

---

**Claim 5: Validators Must Enforce Annotation Format and Report Coverage Gaps**

**Source citation**: [24]

**Design decision**: The pre-push validators must strictly enforce code-annotation format. Every `implements: X` reference must correspond to a valid REQ/DES/TEST/CODE ID in the registry. Missing annotations must block the push (like existing technical-debt checks). The `kb-codeindex` skill should be run pre-push. A `req-add` or `code-annotate` skill should be provided to auto-generate boilerplate annotations, making annotation cheap. Coverage gaps (REQ without DES, DES without CODE) must be reported pre-push.

**Affected scope section**: METHODS.md Section 4, subsection "Validators" (implicit, as part of code-gate enforcement). Also Section 4, "Bidirectional traceability" (lines 156-164): "Validators: ... Block on broken links; warn on coverage gaps for non-commissioned modules." Should be strengthened to: "Block on missing or malformed annotations; warn on coverage gaps."

**Confidence**: HIGH. The research cites DO-178C (the industry standard for safety-critical software) [24] requiring bidirectional traceability and identifies annotation-format breakdown as a critical failure mode in Section 6.2: "Validators should... report coverage gaps (missing annotations, orphan code). The framework should make annotation cheap by providing a `req-add` skill that auto-generates boilerplate annotations." This is both a best-practice recommendation and directly implementable.

---

**Claim 6: Support Decomposition Refactoring Without Invalidating Historical IDs**

**Source citation**: [20]

**Design decision**: The framework should support reconfiguring the programs/sub-programs/modules structure without invalidating all historical IDs. When teams refactor decomposition (e.g., merging two programs or moving modules between sub-programs), the `kb-rebuild-indexes` skill should support remapping old IDs to new paths. This mitigates the risk of premature decomposition: if initial decomposition is wrong, teams can refactor it without losing traceability history.

**Affected scope section**: METHODS.md Section 4, subsection "ID registry" (lines 139-146). Add requirement: "The `kb-rebuild-indexes` skill supports decomposition refactoring: when the programs block is reconfigured, old IDs are remapped to new paths, preserving historical traceability."

**Confidence**: HIGH. The research identifies premature decomposition as a major risk [20] and explicitly recommends this mitigation in Section 6.2: "Additionally, refactoring decomposition should be supported: the framework should allow reconfiguring the programs block (reassigning modules to sub-programs) without invalidating all historical IDs... The `kb-rebuild-indexes` skill should support remapping old IDs to new paths during refactoring."

---

**Claim 7: Commissioning Guidance Must Emphasize Deferring Decomposition**

**Source citation**: [20]

**Design decision**: The `commission-assured` skill and commissioning documentation should include explicit guidance that decomposition should reflect *current* organizational boundaries and business domains, not speculative future structure. Teams should defer decomposition until business boundaries stabilize. This is a procedural safeguard against premature decomposition, complementing the technical ability to refactor decomposition (Claim 6).

**Affected scope section**: METHODS.md Section 4, subsection "Decomposition" (lines 166-180). Add requirement: "Commissioning guidance should emphasize that decomposition reflects current business domains and organizational structure, not speculative future architecture. Teams should start with minimal decomposition (default P1.SP1.M1.*) and refactor when operational pain or business domain shifts motivate change."

**Confidence**: HIGH. The research cites Segment's microservices reversal and general practitioner consensus [20] that premature decomposition is costlier than premature consolidation. Section 6.2 explicitly recommends: "The framework should provide guidance (in the commissioning documentation) that decomposition should reflect current organizational boundaries and business domains, not speculative future structure."

---

## Section 4: Claims to Reject

**Claim: Borrow Erlang/OTP's Supervision-Tree Restart Semantics**

**Source citation**: [2]

**Why we reject it**: OTP supervision trees work because the Erlang runtime isolates processes and supervisors actively monitor and restart them. In a markdown-declared framework, we have no runtime isolation and no automatic recovery. Declaring a module as an "OTP-style supervisor" without actual process-level isolation is misleading. Validators cannot enforce restart strategies; developers would have to implement them in code, orthogonal to SDLC decomposition.

**What we do instead**: If error-recovery strategies are important to a system (e.g., "if this module fails, restart with exponential backoff"), those strategies are explicit in the code and deployment configuration, not in the SDLC framework. The framework can support optional annotation of modules as "error-recovery: supervisor-pattern" or similar, but it does not enforce or implement the pattern. This is a runtime/deployment concern, not SDLC-level.

---

**Claim: Borrow MBSE/SysML's Hierarchical Modeling and Tool Infrastructure**

**Source citation**: [15][16]

**Why we reject it**: MBSE's value comes from formal analysis: a tool checks inconsistencies, generates reports, validates metamodel conformance. If we adopt SysML concepts (hierarchical blocks, allocation tables) but remove the tool, we lose the formal analysis. Additionally, empirical studies [15][16] show that MBSE/SysML adoption is hindered by steep learning curves and tool complexity. A framework dependent on specialized modeling tools gates adoption on tool licensing and training.

**What we do instead**: Borrow SysML's conceptual hierarchy (the idea that a block can contain sub-blocks) but implement it as markdown registries and validators, not as formal tool models. The decomposition registry (programs → sub-programs → modules) is inspired by hierarchical thinking, but implementation is markdown + validators, not formalized modeling.

---

**Claim: Adopt ARINC 653's Partition-Level Runtime Isolation**

**Source citation**: [7][18]

**Why we reject it**: ARINC 653's strength comes from hardware MMU and real-time OS enforcing partition isolation. Declarations in markdown are aspirational; teams cannot rely on partition boundaries to prevent cross-partition faults. For safety-critical systems, runtime isolation is essential but is a deployment and testing responsibility, not SDLC framework responsibility.

**What we do instead**: The framework can support annotation of modules as "safety-critical" or "high-consequence," and validators can enforce stricter traceability and code-annotation discipline for such modules. But the actual isolation (hardware, OS, testing) is out of scope. Method 2 produces substrate that *helps* reach assurance (bidirectional traceability, decomposition records) but does not itself certify.

---

**Claim: Adopt Microservices' Independent-Deployment Model**

**Source citation**: [4][5][14]

**Why we reject it**: Method 2 is a whole-system framework supporting modules, sub-programs, and programs. Modules are not independently deployed; they are compiled and tested as a whole system. If an organization later wants to split a program into independently deployed services, that is a deployment-level refactor (after SDLC design), not an SDLC-level change.

**What we do instead**: The framework should not encourage teams to think of modules as independently deployable unless the organization is actually deploying them independently. Decomposition is about code organization and team structure, following Conway's Law [21], not about deployment topology. The framework explicitly stays out of deployment decisions.

---

**Claim: Borrow Bazel's Full BUILD-Graph Management and Multi-Language Support**

**Source citation**: [1][10]

**Why we reject it**: Bazel's BUILD files are verbose and designed for multi-language, multi-platform complexity. At small to medium scale, the burden of maintaining explicit dependencies in BUILD files exceeds the benefit. Practitioners report maintenance challenges [10], especially in refactoring-heavy codebases.

**What we do instead**: Borrow Bazel's visibility-rule philosophy (declare which packages/modules can depend on which, enforce at check time) but implement via filesystem checks (import statements in code should respect declared visibility), not via a build-system dependency graph. This achieves Bazel's boundary-clarity goal without the maintenance burden.

---

## Section 5: Scope Changes

**Scope Change 1: Enrich Decomposition Subsection with DDD and Bazel Visibility Concepts**

**Section affected**: METHODS.md Section 4, subsection "Decomposition" (lines 166-180)

**Current text** (paraphrased): "Decomposition is **declarative**, not inferred... The team declares [programs, sub-programs, modules] and paths; validators enforce layout. The framework does not suggest decomposition."

**Proposed change**: Replace with clearer terminology and add visibility-rule enforcement.

**Replacement text**:

Decomposition follows **Domain-Driven Design bounded-context concepts**. A module is a bounded context: a domain model with consistent ubiquitous language. Modules are grouped into sub-programs; sub-programs into programs.

Decomposition is **declarative**, not inferred. The commissioning step adds a `programs` block to the project's configuration:
- Which programs exist (e.g., `P1-auth`, `P2-payments`, `P3-reporting`)
- Which sub-programs each contains
- Which modules each sub-program contains
- Which directory paths belong to which module
- Which modules may depend on which (visibility rules, per Bazel's package-visibility model)

Teams should document cross-module dependencies in **context maps** (markdown files showing how contexts relate), reusing DDD terminology.

Validators enforce:
- Every REQ has a module assignment
- Every CODE annotation maps to a declared module path
- No module has un-cited code (warn) or un-tested REQs (block)
- **Cross-module imports respect declared visibility** (enforce via filesystem checks)
- **Circular dependencies between programs are flagged** as violations requiring architectural approval
- **Code implementing a REQ/DES is co-located in its declared module** (detect anaemic contexts)

The framework does not try to suggest decomposition. The team declares it; the framework enforces what is declared.

Commissioning guidance should emphasize that decomposition reflects **current** business domains and organizational structure, not speculative future architecture. Teams should defer decomposition until operational pain or business-domain shifts motivate change.

**Driving claim(s)**: Claims 1, 2, 4, 7 (DDD bounded contexts, Bazel visibility discipline, anaemic-context detection, deferral guidance)

---

**Scope Change 2: Add Decomposition-Refactoring Support to ID Registry Subsection**

**Section affected**: METHODS.md Section 4, subsection "ID registry" (lines 139-146)

**Current text** (paraphrased): "A `library/_ids.md` file is auto-generated by `kb-rebuild-indexes`... Validators: ID uniqueness, referenced IDs exist, no orphan IDs."

**Proposed change**: Add support for decomposition refactoring without ID invalidation.

**Replacement text** (insert after "Validators" paragraph):

The `kb-rebuild-indexes` skill supports **decomposition refactoring**: when the programs block is reconfigured (e.g., merging two programs, moving modules between sub-programs), the skill remaps old IDs to new paths, preserving historical traceability. This enables teams to refactor an initial (possibly incorrect) decomposition without losing the chain of REQ/DES/TEST/CODE linkages.

**Driving claim(s)**: Claim 6 (decomposition refactoring without ID invalidation)

---

**Scope Change 3: Strengthen Code-Annotation Validation**

**Section affected**: METHODS.md Section 4, subsection "Bidirectional traceability" (lines 156-164)

**Current text** (paraphrased): "Validators: Forward link integrity — every cited ID exists in the registry. Backward coverage — every REQ has tests, every DES has implementing code... Block on broken links; warn on coverage gaps for non-commissioned modules."

**Proposed change**: Strengthen to enforce annotation format and make annotation a blocker.

**Replacement text** (replace the final sentence):

Validators:
- Forward link integrity — every cited ID exists in the registry
- Backward coverage — every REQ has tests, every DES has implementing code, every CODE annotation references a valid REQ/DES/TEST
- **Annotation-format integrity** — every `implements: X` or `cites: X` reference in code is syntactically valid and resolves to a registry entry
- **Block on broken links and missing annotations** (as part of pre-push validation); warn on coverage gaps for non-commissioned modules

A `code-annotate` or `req-add` skill should be provided to auto-generate boilerplate annotations, making annotation cheap and reducing manual burden.

**Driving claim(s)**: Claim 5 (validator-enforced annotation format and coverage gaps)

---

**Scope Change 4: Add KB-Extension Support for Hexagonal Architecture (Optional)**

**Section affected**: METHODS.md Section 4, subsection "KB extension to code (annotation-driven)" (lines 182-194)

**Current text** (paraphrased): "Source code carries inline comment annotations... A new `kb-codeindex` skill walks the source tree, parses annotations, emits `library/_code-index.md`..."

**Proposed change**: Add optional hexagonal-architecture tagging.

**Replacement text** (insert before final paragraph):

For teams adopting **hexagonal architecture** (optional), code locations may be annotated as `core` (domain logic) or `adapter` (infrastructure boundary). The `kb-codeindex` skill can distinguish these, and `traceability-render` can visualize domain-logic density and boundary violations per module.

**Driving claim(s)**: Claim 3 (optional hexagonal-architecture support)

---

**Scope Change 5: Add Commissioning Guidance on Premature Decomposition**

**Section affected**: METHODS.md Section 4, subsection "Skills shipped (Assured bundle, in addition to Method 1's skills)" (lines 202-208), add a new subsection "Commissioning guidance"

**Current text**: No explicit section on commissioning guidance; `commission-assured` is listed as a skill but guidance details are not specified.

**Proposed change**: Add new subsection documenting commissioning guidance.

**New subsection**:

### Commissioning guidance

The `commission-assured` skill includes guidance documentation on decomposition strategy. Key principles:
- **Start simple**: The default decomposition is `P1.SP1.M1.*`. Do not create multiple programs until business domains are clearly separated or operational pain motivates it.
- **Decomposition reflects current state**: The decomposition should match current organizational structure and business domains, not speculative future architecture (per Conway's Law).
- **Refactor when pain appears**: Decomposition is not fixed. When operational pain, team structure changes, or business-domain shifts occur, teams should refactor the programs block using the `kb-rebuild-indexes` remapping support.
- **Cross-module dependencies are costly**: Each cross-module dependency increases coordination cost. Teams should prefer loosely coupled programs (programs may depend on a shared/core program, but circular dependencies are architectural violations).

**Driving claim(s)**: Claim 7 (deferral guidance); implicit in Claims 1-2.

---

## Section 6: Open Questions Remaining

**Question 1: How to Visualize Module Dependency Graphs in Human-Reviewable Form?**

**Why it matters**: The research recommends validators report cross-module dependencies and `traceability-render` should visualize the module dependency graph [1]. The scope change (Section 5) requires this visualization, but the exact output format (plaintext table, ASCII diagram, HTML graph) is not specified. For large systems with many modules, graph visualization is essential to catch cycles and density hotspots.

**How to resolve**: Prototype experiment during implementation phase. Options: (a) ASCII DAG layout similar to dependency-check tools; (b) HTML SVG graph using a GraphViz backend; (c) Markdown table showing pairwise dependencies with cycle detection. Recommend trying (a) and (b) in Stage 4 (implementation planning) with a sample medium-size decomposition (8-12 modules). Accept that visualization will be lossy at large scale (50+ modules) and document that teams with very large systems should use external dependency-analysis tools.

---

**Question 2: What Happens When a Module's Declared Visibility Rules Conflict with Actual Import Statements?**

**Why it matters**: The research recommends Bazel's visibility-rule discipline but does not specify whether violations block the commit, create warnings, or are advisory. In a whole-system framework, a visibility violation might indicate a real design issue or might be a necessary dependency that the decomposition registry hasn't been updated to reflect.

**How to resolve**: Design decision required before implementation. Recommend: visibility violations produce a *strict warning* (visible in pre-push output, must be acknowledged but do not block push) until the commissioning team opts into strict mode. Strict mode blocks violations and is recommended for regulated-industry projects (Method 2 in assured/certified contexts). This allows teams to discover and document violations before committing to strict enforcement.

---

**Question 3: How Fine-Grained Should Module Boundaries Be? Module-Per-Feature vs. Module-Per-Domain?**

**Why it matters**: The research recommends DDD bounded contexts as modules [3][12] but does not specify what size a context should be. In practice, teams might end up with 5-10 large contexts (one per major business domain) or 50-100 small contexts (one per feature). The size affects validator load, KB query performance, and team coordination overhead.

**How to resolve**: Accept as a team-driven design choice, documented in commissioning guidance. Provide a heuristic: "A module should be the scope of responsibility for one team (or part of one team). If a single developer spans multiple modules, decomposition is too fine-grained. If one module is maintained by multiple geographically distributed teams, it is too coarse-grained." Defer specific metrics (lines-of-code per module, number of files per module) to post-dogfooding lessons learned.

---

**Question 4: Should the Framework Support "Soft" Decomposition (Recommended but Not Enforced)?**

**Why it matters**: The scope draft (Section 4) describes validators that enforce decomposition. The research recommends validators block on violations [1]. However, some teams might want advisory decomposition (boundaries are recommended but code violations are warnings, not errors). This is the difference between "decomposition is mandatory" and "decomposition is aspirational guidance."

**How to resolve**: Design decision deferred to implementation. Recommend supporting both modes: (a) **enforced mode** for regulated/assured contexts (violations block commits), (b) **advisory mode** for exploratory projects (violations are warnings). Both modes should be configurable at commissioning time, with enforced as the default for Assured bundle.

---

## Section 7: Confidence Assessment for the Line as a Whole

The synthesis is **HIGH confidence overall**. The research output is densely cited (24 citations, all properly attributed) and spans authoritative sources: canonical texts (Evans' DDD [3], Armstrong's Erlang thesis [2]), industry standards (ARINC 653 [7], AUTOSAR [8], DO-178C [24]), peer-reviewed work (Brooks' "No Silver Bullet" [22], Conway's Law [21]), and practitioner consensus (Segment's microservices reversal [20], Newman's microservices books [4][5], Fowler's anemic-domain-model anti-pattern [13]). The critical recommendation — to borrow DDD bounded contexts plus Bazel visibility discipline — is grounded in Section 6.1 with explicit translatability analysis and failure-mode reasoning, not speculation. Section 6.2 (Failure Modes to Design Against) directly maps research findings to specific validator designs, meeting the high standard for actionable synthesis.

**Strengths**: The research is strongest on conceptual mapping (which patterns translate to a markdown-first framework and why). The pattern survey is comprehensive, covering build systems (Bazel), runtime frameworks (Erlang), domain modeling (DDD), deployment-level patterns (microservices), formal methodologies (SysML, MBSE), and avionics/automotive standards. The rejection section (Section 6.3, "What We Should NOT Borrow") is explicit and reasoning is clear, preventing false adoption of patterns that depend on runtime or tooling the framework does not own. Failure modes are grounded in independent sources (academic, standard-setting, practitioner case studies), not vendor marketing.

**Weaknesses**: The research is less detailed on implementation mechanics. For example, the visibility-rule validator is conceptually clear (check that imports respect declared module dependencies) but the exact parsing strategy (grep imports, use AST, use type-system hints) is deferred to implementation. Validator design patterns and performance at scale (large systems with 50+ modules) are not fully scoped. These gaps are appropriate for a synthesis stage (implementation detail is coding-phase work) but future Stage 4 (implementation planning) should prototype validator performance on test repositories.

**Verdict**: HIGH confidence that the synthesis accurately captures the research findings and proposes design changes that are directly grounded in cited evidence. The top-line recommendation (DDD bounded contexts + Bazel visibility rules, with hexagonal as optional within-module pattern) has explicit translatability justification and is implementable without custom build systems or runtimes. The failure-mode mitigations are specific and actionable. Overall scope changes are modest and focused, avoiding over-specification while establishing clear design direction.

---

**End of Synthesis**

