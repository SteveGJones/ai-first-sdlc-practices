# Stage 3 Synthesis: ALM / Requirements-Tools Landscape
## Converting Research to Assured Bundle Design Decisions

---

## Section 1 — Source Attestation

**Research output file:** `/Users/stevejones/Documents/Development/ai-first-sdlc-practices/research/sdlc-bundles/outputs/03-alm-tools-landscape/output-1.md` (8,801 words)

**Citation discipline:** The source includes 32 bibliography entries with full source tags ([1] through [32]) covering open-source tools (sphinx-needs, Doorstop, strictdoc), commercial tools (IBM DOORS, DOORS Next, Siemens Polarion, Jama Connect, Reqtify, Helix ALM, codebeamer), the ReqIF standard, and category-level criticism (requirements rot, compliance theatre, Conway's Law). Source types are diverse: official project documentation, vendor docs, practitioner blogs, consultant reports, review sites, and peer-reviewed papers. Every empirical claim in the output is tagged with a citation; the bibliography is complete.

**Source quality assessment:** The output is strong on tool architecture and known failure modes (Sections 2-5 provide authoritative deep dives on sphinx-needs and DOORS based on official documentation and multiple independent practitioner sources). The output is authoritative on regulated-industry usage (sources [6], [7], [9], [10] from aerospace/safety-critical domains). The category-level critique (Section 7: requirements rot, compliance theatre, Conway's Law) relies on practitioner blogs and papers; these are credible but not universally held — they represent observed failure modes, not laws of nature. One caveat: DOORS criticism, while sourced (primarily from competing vendors and migration consultants), should be weighted with awareness that some sources are from competing vendors [11], [14]. However, the criticisms are consistent across independent sources ([12], [13], [15], [16], [17], [18]).

**Caveats:**
- ReqIF round-trip data loss is documented but based primarily on vendor practitioner blogs ([12], [13], [19]); no formal specification of what gets lost exists in the OMG standard.
- Category-level criticisms (requirements rot, compliance theatre) are drawn from practitioner literature, not empirical studies; they represent observed patterns, not metrics.
- The output does not deeply cover recent SaaS ALM entrants (Slack + AI-native tools); it focuses on established tools.

---

## Section 2 — Empirical Findings

### Sphinx-Needs: Architecture and Regulated Use

- Sphinx-needs is a Sphinx documentation extension storing needs as inline directives in RST files, indexed at build time, with the filesystem as source-of-truth [1]. Identifier scheme: prefix + auto-increment (REQ_001, TEST_042) [1]. Link model: declared links with static build-time validation [1].
- Sphinx-needs is actively used in regulated aerospace (DO-178B compliance) and automotive (ISO 26262) contexts, demonstrating that open-source, file-based requirements tools can meet assurance-level rigour [6][7].
- Known scaling limits: sphinx-needs' multiprocessing architecture struggles above 500 pages in a single Sphinx project; build time exceeds 30 minutes for 25K pages with memory exceeding 32 GB [1].
- Customisation is via declarative configuration (needs_types for requirement schemas; needs_links for link rules) plus Python plugins [1].
- Dynamic functions (computed fields referencing other needs) are powerful but have a steep learning curve; the syntax is terse and debugging is difficult [1].
- Sphinx-needs assumes Git and RST/markdown as the editing interface; no native web UI for collaborative editing [1].

### DOORS: Lock-In Anatomy

- DOORS Classic pioneered the module-and-attribute relational model: requirements grouped into hierarchical modules, each requirement a row, columns are attributes (Status, Priority, custom fields) [14]. All data lives in proprietary .rmd binary format [14].
- DOORS dominance (1990s-2000s) created organisational inertia: large programmes invested heavily in DXL (DOORS eXtension Language) customisation, with some deployments accumulating 1M+ lines of DXL code [15].
- DOORS Next (web-based, Jazz architecture) intended to modernise DOORS but created migration disaster: DXL scripts cannot be migrated (Jazz uses Java); views are incompatible; baselines and historical data are lost [15][16].
- DOORS lock-in operates at multiple levels: binary data format (.rmd files inaccessible without DOORS), DXL investment (rewriting 1M lines of code is economically prohibitive), proprietary licensing (enterprise sales model, per-seat cost steep), and organisational inertia [15].
- Rich-text legacy creates export pain: DOORS' rich-text fields do not round-trip cleanly through ReqIF, resulting in data loss [19].

### ReqIF and Data Loss in Tool Exchange

- ReqIF (Requirements Interchange Format, OMG standard since 2011) is intended as a tool-agnostic exchange schema [11]. Real-world round-trip workflows suffer from data loss: attributes not supported in the receiving tool are silently dropped; parent-child relationships cannot be re-assigned on round-trip; complex link types degrade to binary links [12][13].
- Lesson: use ReqIF as one-way export (from proprietary tool to ReqIF), not for bidirectional sync [12][13].

### File-Based vs. Database-First Trade-Off

- Open-source tools (sphinx-needs, Doorstop, strictdoc) store requirements as files in Git. Commercial tools (DOORS, Polarion, Jama) store in centralised database (on-premise or SaaS) [1][8][10][20][22].
- File-based tools sacrifice some query flexibility but gain portability, auditability (Git history is the audit trail), and integration with development workflows (requirements live alongside code) [1][8][10].
- Database-first tools provide powerful search and querying but create lock-in and centralised operational cost (database administration, licensing, user provisioning) [14][15][20].

### Code-to-Spec Linking Approaches

- sphinx-needs: plugin-based annotation parsing; teams write custom code to extract annotations from source [1].
- Doorstop: external scripting; YAML metadata stores code references [8].
- strictdoc: source-code parser (language-agnostic, no AST parsing) [10].
- DOORS: expensive DXL customisation [14][15].
- Commercial tools: IDE plugins + annotation parsing [20][22].
- Annotation-driven approach (plaintext comments in code) is simpler than DXL and more portable than IDE-plugin model [source: comparative inference from 1, 8, 10, 14].

### Category-Level Failure Modes

- **Requirements rot:** Specifications become outdated as the system evolves. 71% of software projects fail at least partially due to poor requirements [28]. Tool cannot prevent rot; it's a process and culture problem [27][28].
- **Traceability matrix as the work:** Maintenance overhead of updating links and attributes can exceed engineering value. Teams maintain two parallel systems: real design (in code) and shadow requirements document (in DOORS/Excel) for audit compliance [29].
- **Compliance theatre:** Requirements tools in regulated industries are deployed primarily to satisfy certification authorities, not to improve engineering [30]. Teams optimise for audit visibility rather than engineering effectiveness [30].
- **Conway's Law applied to requirements:** Requirement document structure often mirrors the org chart (team-level organisation) rather than user feature-level decomposition [31]. Database-centric tools bake org structure into schema, making feature-level reorganisation difficult without data migration [31].

---

## Section 3 — Claims to Incorporate

**Claim 1:** Sphinx-needs' declarative need-type schema (specifying for each type: allowed fields, field types, link rules, rendering hints) is the right pattern for requirement structuring.

**Source citation:** [1]

**Design decision:** Formalise the Assured bundle's spec-type decomposition (REQ / DES / TEST / CODE) as a configuration schema. Include link validation in kb-rebuild-indexes validator.

**Affected scope section:** METHODS.md Section 4, "Method 2 in detail" → "Identifier system" and "ID registry" subsections.

**Confidence:** HIGH.

---

**Claim 2:** File-based, Git-native storage (markdown + YAML frontmatter) is the right foundational choice. It provides portability, auditability, and integration with development workflows while avoiding DOORS' lock-in.

**Source citation:** [1][8][10] (architecture comparison); [14][15] (DOORS lock-in warning)

**Design decision:** Store each spec record as a markdown file with YAML frontmatter for metadata (ID, type, links). Explicitly state this as core architectural decision.

**Affected scope section:** METHODS.md Section 4, "Method 2 in detail" → "Spec-as-KB-finding" subsection.

**Confidence:** HIGH.

---

**Claim 3:** Static link validation at build-time (like sphinx-needs and Doorstop) is sufficient and preferred over real-time database constraints. It reduces operational complexity and requires no database infrastructure.

**Source citation:** [1][8] (static validation architecture)

**Design decision:** kb-rebuild-indexes validator performs static link validation. Do not introduce a relational database to enforce referential integrity at run-time.

**Affected scope section:** METHODS.md Section 4, "Method 2 in detail" → "ID registry" subsection.

**Confidence:** HIGH.

---

**Claim 4:** Identifiers must be stable (not renaming-vulnerable) and namespaced with prefixes that encode both type and context (e.g., program.sub-program.module.type-num). This allows type/context visibility at a glance and facilitates sorting, filtering, and querying.

**Source citation:** [1][8][10] (identifier stability is foundational across all serious tools)

**Design decision:** Adopt the identifier scheme designed in METHODS.md Section 4: program.sub-program.module.type-num with default decomposition P1.SP1.M1.* for un-decomposed projects.

**Affected scope section:** METHODS.md Section 4, "Method 2 in detail" → "Identifier system" subsection. No change needed; the design is sound.

**Confidence:** HIGH.

---

**Claim 5:** Annotation-driven code-to-spec linking (code comments like "# implements: DES-005") is simpler and more portable than DOORS' DXL burden, strictdoc's source parser, or commercial tools' IDE plugins.

**Source citation:** [1][8][10][14][15] (comparative analysis); [inferred]

**Design decision:** The kb-codeindex skill is the right pattern. Do not introduce AST parsing or IDE plugins as core. Keep code as plaintext-with-annotations.

**Affected scope section:** METHODS.md Section 4, "Method 2 in detail" → "KB extension to code (annotation-driven)" subsection.

**Confidence:** HIGH.

---

**Claim 6:** Modular decomposition (program → sub-program → module) should be a first-class concept from the start. This allows large projects to scale by bounding scope. A declarative decomposition registry is the right middle ground between sphinx-needs' flat structure and DOORS' rigid hierarchy.

**Source citation:** [1] (sphinx-needs scaling limits above 500 pages); [14][15] (DOORS' deep hierarchy unwieldy); [inferred]

**Design decision:** Ensure decomposition is declarative (teams declare it; the framework enforces it). Validators ensure every spec record and code annotation has a module assignment.

**Affected scope section:** METHODS.md Section 4, "Method 2 in detail" → "Decomposition" subsection.

**Confidence:** HIGH.

---

**Claim 7:** The framework should explicitly avoid ReqIF import/export as a core feature. ReqIF is useful as one-way export (for teams migrating away), but round-trip workflows are lossy and better handled as a plugin.

**Source citation:** [11][12][13][19]

**Design decision:** Do not bake ReqIF support into the core framework. If teams need ReqIF export, build it as a plugin. Document that this is one-way and that some metadata may be lost.

**Affected scope section:** METHODS.md Section 6, "What is explicitly out of scope for these bundles" — add note about ReqIF.

**Confidence:** MEDIUM.

---

## Section 4 — Claims to Reject

**Claim A:** The Assured bundle should adopt DOORS-style relational database storage (modules + attributes) with powerful query capabilities.

**Source citation:** [14][15][16] (detailed DOORS architecture)

**Why we reject it:** DOORS' relational model created lock-in, made migration impossible (binary .rmd format), baked organisational structure into the schema, and created brittleness. The framework's philosophy is filesystem-first, no relational database. Adopting a relational database would reintroduce the lock-in problems we are studying to avoid.

**What we do instead:** Keep the filesystem-first, Git-native approach. Static link validation provides sufficient integrity checking. Accept the trade-off that ad-hoc queries are less flexible than a relational database.

---

**Claim B:** The Assured bundle should support proprietary extension languages (like DOORS' DXL) or domain-specific query languages (like Polarion's PQL) for customisation.

**Source citation:** [14][15] (DXL burden: 1M+ lines of code, brittle, lock-in); [20] (Polarion PQL complexity)

**Why we reject it:** Proprietary extension languages create lock-in, brittleness, and adoption barriers. Extensibility via Python (a general-purpose language) or REST APIs (standard) is more accessible and avoids lock-in.

**What we do instead:** Expose extensibility via Python plugins (like sphinx-needs does) or REST API queries on the spec index. Do not create a proprietary scripting language.

---

**Claim C:** The Assured bundle should embed organisational structure (team ownership, approval chains, project hierarchies) into the core data model, like DOORS does.

**Source citation:** [31] (Conway's Law: org structure baked into schema makes feature-level reorganisation difficult)

**Why we reject it:** When organisational structure is baked into the data model, team reorganisation requires data migration. Org charts change faster than spec structures should change; decoupling them is better.

**What we do instead:** Allow organisational metadata (owner, reviewer, approver) as optional fields in YAML frontmatter, but do not require them. Process enforcement happens via validators and workflow tools, not the core spec schema.

---

**Claim D:** The Assured bundle should include a real-time collaborative editing interface (like Polarion's LiveDocs) as part of the core framework.

**Source citation:** [20] (Polarion's LiveDocs praised); [inferred]

**Why we reject it:** The framework is designed for agent-driven workflows (METHODS.md Section 1), where agents manage the text and humans review. A real-time collaborative editing interface is valuable but represents process complexity beyond the core spec-management scope.

**What we do instead:** The core framework produces markdown files and JSON indices. A separate web server (optional, not required) can serve a UI for reading specs, leaving comments, and triggering workflows. This keeps the core simple and allows teams to choose.

---

## Section 5 — Scope Changes

**Section affected:** METHODS.md Section 4, "Method 2 in detail" → "Identifier system" subsection.

**Current text (paraphrased):** "IDs are auto-increment within namespaces with default decomposition P1.SP1.M1.* for un-decomposed projects."

**Proposed change:** Clarify that identifier stability is foundational and that the scheme encodes type + context.

**Replacement text:** "Identifiers are stable, globally unique, and namespaced with type and context visible at a glance (e.g., REQ-feature-001 or P1.SP2.M3.DES-007). Once assigned, an ID never changes, even if the requirement is renamed or moved. This stability is foundational for traceability; breaking it breaks all downstream links."

**Driving claim(s):** Claims 1 and 4 from Section 3; source citations [1][8][10].

---

**Section affected:** METHODS.md Section 4, "Method 2 in detail" → "ID registry" subsection.

**Current text (paraphrased):** "Validators check ID uniqueness, referenced IDs exist, and no orphan IDs."

**Proposed change:** Clarify that link validation is static and occurs at build-time.

**Replacement text:** "Link validation is static, occurring at build-time when kb-rebuild-indexes runs (as part of pre-push validation). The validator checks ID uniqueness (no two artefacts claim the same ID), forward-link existence (every cited ID exists in the registry), and coverage (no orphan IDs: every REQ has at least one DES; every DES has at least one TEST). This static validation requires no database and allows local validation in CI/CD pipelines."

**Driving claim(s):** Claim 3 from Section 3; source citations [1][8].

---

**Section affected:** METHODS.md Section 4, "Method 2 in detail" → "KB extension to code (annotation-driven)" subsection.

**Current text (paraphrased):** "This deliberately does NOT do AST parsing, semantic search, call graphs, or sourcegraph-class intelligence."

**Proposed change:** Strengthen the rationale for this design choice.

**Replacement text:** "This deliberately does NOT do AST parsing, semantic search, call graphs, or sourcegraph-class intelligence. Code is treated as text-with-annotations. This is deliberately simpler than DOORS' DXL extensibility (which creates lock-in and brittleness) and aligns with sphinx-needs' plugin-based annotation parsing. The cost is annotation maintenance; the benefit is a lightweight, language-agnostic, vendor-independent KB substrate."

**Driving claim(s):** Claim 5 from Section 3; source citations [1][14][15].

---

**Section affected:** METHODS.md Section 4, "Method 2 in detail" → "Decomposition" subsection.

**Current text (paraphrased):** "Decomposition is declarative. Validators ensure every REQ has a module assignment."

**Proposed change:** Add explicit statement that decomposition avoids sphinx-needs' scaling friction and DOORS' rigid hierarchy.

**Replacement text:** "Decomposition is declarative, not inferred. Each team declares its program → sub-program → module structure; the framework does not suggest it. This design supports scaling (agents working on one module don't need context for the whole system), avoiding sphinx-needs' scaling friction above 500 pages and DOORS' inflexibility with deep hierarchies. Validators check that every REQ has a module assignment and every code annotation maps to a declared module path."

**Driving claim(s):** Claim 6 from Section 3; source citations [1][14][15].

---

**Section affected:** METHODS.md Section 6, "What is explicitly out of scope for these bundles" — add new item.

**Current text (paraphrased):** Current list of out-of-scope items (AST-level code intelligence, IDE integration, etc.).

**Proposed change:** Add explicit note about ReqIF and tool interoperability.

**Replacement text:** Add bullet: "ReqIF import/export. The Assured bundle's authoritative format is markdown + YAML (Git-native). One-way export to ReqIF (for teams migrating to other tools) can be built as a plugin. Round-trip workflows with other tools are not supported; ReqIF round-trip is lossy by design (parent-child relationships cannot be re-assigned, non-standard attributes are dropped). The framework assumes Git as the source of truth, not tool interoperability."

**Driving claim(s):** Claim 7 from Section 3; source citations [11][12][13][19].

---

**Section affected:** METHODS.md Section 4, "Method 2 in detail" → add new subsection "Organisational Metadata and Process Concerns".

**Current text (paraphrased):** No existing text.

**Proposed change:** Add clarification that org structure is not baked into the spec schema.

**Replacement text:** "Organisational metadata (owner, reviewer, approver) may be included as optional YAML fields in any spec record. However, the framework does not enforce organisational hierarchy at the schema level. When teams reorganise, requirements do not need to migrate. Process enforcement (approvals, sign-offs, workflow steps) is the responsibility of validators and workflow tools, not the core spec schema."

**Driving claim(s):** Rejection C from Section 4; source citations [31].

---

## Section 6 — Open Questions Remaining

**Question 1:** What is the right granularity for "module" in the decomposition primitive? Should the framework suggest a decomposition (program ≈ product; sub-program ≈ feature; module ≈ component) or remain agnostic?

**Why it matters:** METHODS.md Section 4 states "The framework does not try to suggest decomposition." But teams commissioning the Assured bundle need guidance on how to define their own. The research does not address this; it only documents that DOORS' rigid hierarchy and sphinx-needs' flat structure both create friction.

**How to resolve:** Ship templates with suggested decomposition examples, documented in commissioning guidance. For now, accept the uncertainty and document that teams should define their own.

---

**Question 2:** Should the Assured bundle support change-impact analysis (e.g., "if REQ-auth-001 changes, what tests and code are affected")? The research documents that Polarion claims to provide impact analysis, but does not evaluate how well it works.

**Why it matters:** Category-level critique [29] mentions "requirement cascade problem": when a high-level requirement changes, the entire cascade of sub-requirements may need revision, but tools often do not provide impact analysis. If the Assured bundle is to support "assurance-level rigour", impact analysis might be a requirement.

**How to resolve:** Prototype a simple impact-analysis query: given a REQ ID, find all DEsigns and TESTs that reference it. If teams find it valuable, add it as a traceability-query skill. For now, accept that the core framework supports the data structure; impact analysis is a query on top.

---

**Question 3:** How should the Assured bundle handle version/baseline management? Requirements change over time; teams in regulated industries need to snapshot spec state. DOORS' baseline mechanism is mentioned but not evaluated in the research.

**Why it matters:** METHODS.md does not discuss versioning or baselines. Git tags/commits alone may not be sufficient if teams need to snapshot traceability matrices, test results, or approval status at a given moment.

**How to resolve:** Treat this as a scope decision for the commission-assured skill. On commission, set up a naming convention for baselines (e.g., tags named baseline-v1.0). A separate skill can generate a snapshot of the traceability matrix at a tag. For now, document that baselines are Git tags, not a first-class ALM concept.

---

## Section 7 — Confidence Assessment

The synthesis is well-grounded. The source research is authoritative on sphinx-needs (official documentation, regulated-industry case studies) and DOORS (combination of vendor documentation, migration consultant reports, and independent user reviews). The comparative analysis systematically covers 11 tools across data model, identifier scheme, code linking, scaling, and failure modes.

**Strong areas:** The research provides definitive answers to "what patterns to adopt" (sphinx-needs' need-type schema, file-based storage, static link validation, annotation-driven code linking) and "what patterns to avoid" (DOORS' relational model, proprietary binary formats, DXL extensibility). The deep dives on sphinx-needs and DOORS are authoritative and well-cited.

**Weaker areas:** The research is thinner on "what patterns to leave as plugins." The category-level critiques (requirements rot, compliance theatre, Conway's Law) represent practitioner experience, not empirical measurement. ReqIF data-loss is documented but relies on practitioner blogs, not formal specifications.

**Overall confidence:** HIGH (85%). The core claims (adopt sphinx-needs patterns, avoid DOORS patterns, maintain filesystem-first architecture) are backed by strong evidence. The scope changes to METHODS.md are grounded in the research and do not require leaps. The open questions are genuine gaps in the research, not failures of the synthesis.

