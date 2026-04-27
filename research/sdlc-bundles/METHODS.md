# Method 1 and Method 2 — Reference Context for Research

> **For the research operator (Steve):** the contents of this file should be pasted into the Claude Desktop conversation BEFORE the prompt content from `prompts/<line>.md`. Each research prompt assumes the researcher has read this file and understands the framework being designed, the two methods, and what's already built. Without this context, the research outputs will be too generic to be useful.

> **For the researcher (Claude Desktop):** this is the design context for the framework whose research you are conducting. Read it carefully before answering the research prompt that follows. When the research prompt refers to "the framework", "Method 1", "Method 2", "Programme bundle", or "Assured bundle", this document is the source of truth for what those terms mean.

---

## 1. The framework being designed (background)

The **AI-First SDLC Practices framework** (`SteveGJones/ai-first-sdlc-practices`) is an open-source software-development-lifecycle framework for AI-agent-led development teams. The current production version is 1.8.0. Its philosophy is that AI agents are the primary engineers, with humans acting as commissioners, reviewers, and decision-makers.

### Existing characteristics

- **Markdown-driven**: every artefact (feature proposals, retrospectives, specifications, knowledge-base entries) is a markdown file in a defined location.
- **Filesystem-first**: no relational database, no SaaS backend. Everything lives in a Git repository under defined paths.
- **Agent-orchestrated**: skills (markdown files describing procedures) and agents (markdown files with frontmatter describing capabilities and tools) drive the workflow. Skills can dispatch agents via Claude Code's Agent tool. The framework itself is a collection of skills, agents, and validators distributed via a plugin family.
- **Open-source**: MIT-licensed, with 12 plugins in the family (sdlc-core, sdlc-team-* for cross-cutting roles, sdlc-lang-* for languages, sdlc-knowledge-base for filesystem knowledge bases, sdlc-workflows for containerised execution).
- **Constitution-based rule enforcement**: a top-level `CONSTITUTION.md` defines 11 articles of mandatory rules (zero-tolerance technical debt, mandatory feature proposals, mandatory architecture documents at production tier, etc.). Local validators enforce the rules at commit / push / CI time.

### Existing substrate the new bundles build on

- **`superpowers` skills**: a curated set of meta-skills for software development. Relevant ones include:
  - `brainstorming` — converts ideas to designs through structured Q&A, output is a spec doc
  - `writing-plans` — converts spec docs to detailed implementation plans (file-by-file, task-by-task)
  - `subagent-driven-development` — executes plans by dispatching fresh subagents per task, with two-stage review (spec compliance + code quality)
  - `test-driven-development` — TDD discipline (red/green/refactor)
  - `requesting-code-review` — structured code review template
  - `dispatching-parallel-agents` — fanning out independent work
- **`sdlc-knowledge-base` plugin** (just shipped at v0.2.0): a filesystem-based knowledge base.
  - Each project's `library/` directory holds curated markdown findings.
  - `_shelf-index.md` is a hash-tracked index summarising every entry's terms, facts, and links.
  - `research-librarian` agent handles stateless retrieval (reads shelf-index, deep-reads 2-4 most relevant files, returns structured findings with citations).
  - `synthesis-librarian` agent (with `tools: []` declaration plus `check_synthesis_attribution` post-check) produces cross-source syntheses with bidirectional `[handle]`-tagged attribution. Untagged or fake-tagged claims are rejected by the post-check.
  - Cross-library queries against multiple corporate asset libraries shipped in v0.2.0 (just merged on PR #177).
  - The KB is already what we use for project knowledge findings; the new bundles will extend it to handle structured specifications and code annotations.
- **EPIC #97 commissioning**: a separate ongoing EPIC introduces "commissioning" — a project picks one of four SDLC options (Solo / Single-team / Programme / Assured) and the framework installs a fixed bundle of constitution + agents + skills + templates + validators for that option. The Programme and Assured bundles being designed here are sub-features of EPIC #97 (sub-features #103 and #104), shipping together on this branch (`feature/sdlc-programme-assured-bundles`).

### Existing artefact discipline

- Every feature requires a feature proposal (markdown file at `docs/feature-proposals/<n>-<slug>.md`) before any code is written.
- Every feature requires a retrospective (markdown file at `retrospectives/<n>-<slug>.md`) at completion.
- Production-tier projects require six architecture documents (requirements-traceability-matrix, what-if-analysis, architecture-decision-record, system-invariants, integration-design, failure-mode-analysis) reviewed before implementation.
- Feature branches are mandatory; commits to main are forbidden.
- Pre-push validation runs 10 checks (syntax, lint, technical-debt scan, architecture validation, type safety, security, logging compliance, static analysis, tests, smoke test).

---

## 2. The two methods at a glance

The framework already supports a "good enough for most product teams" SDLC. It does not yet support two distinct shapes that mature engineering organisations need:

- **Method 1 — formal waterfall phase gates**, where the SDLC has explicit phase boundaries (requirements → design → test → code), each phase produces a reviewable specification artefact, and gates between phases enforce that the prior phase's specification is complete and cited before the next phase begins. This pattern is normal at programme-of-work scale and in regulated industries.
- **Method 2 — agent-first specifications with end-to-end traceability**, where requirements, design elements, tests, and code are all individually identified (REQ-XXX, DES-XXX, TEST-XXX, CODE-XXX), bidirectionally linked, and queryable through the same knowledge-base substrate the framework already uses for findings. Decomposition is declared up-front: the project is partitioned into programs, sub-programs, and modules with bounded contexts, so any agent works with a small, scoped slice rather than the whole system in context.

Method 1 ships as the **Programme bundle**. Method 2 ships as the **Assured bundle** and is a strict superset of Method 1 (Assured = Programme + traceability + decomposition + KB-for-code). The two bundles ship together on a single branch and share their phase-gate substrate.

---

## 3. Method 1 in detail

### What Method 1 produces

Per feature, Method 1 mandates four artefacts in `docs/specs/<feature>/`:

- `requirements-spec.md` — what the feature must do, drawn from user need / business motivation / regulatory constraint
- `design-spec.md` — how the feature will be built, citing the requirements-spec
- `test-spec.md` — what the feature's tests will verify, citing both requirements-spec and design-spec
- (Code, written under TDD discipline driven by the test-spec)

Each artefact has a defined header schema (mandatory sections, optional sections) and a stable feature-id assigned at the requirements-spec phase.

### Phase gates

Validators that block progression unless the gate condition is met:

- `requirements-gate`: requirements-spec exists, has all mandatory sections, has a feature-id
- `design-gate`: design-spec exists, has all mandatory sections, references the requirements-spec by feature-id; **all cited requirements-spec section IDs must exist** (no broken cross-phase references)
- `test-gate`: test-spec exists, has all mandatory sections, references both requirements-spec and design-spec; **all cited IDs must exist in the prior phase artefacts**
- `code-gate`: code is written under TDD; pre-push validation includes "every code change cites a test-spec section" and the cited section ID must exist

The gates run as part of pre-push validation and CI. Programme bundle defaults: **block on missing artefact AND on broken cross-phase references; warn on weak (vague but non-broken) cross-phase reference**. The blocking-on-broken-refs rule strengthens earlier weaker phrasing — broken references are a defect, not a style issue. *[Line 1: §3 Claims 1, 5; Line 3: §3 Claims 1-3 — file-based static link validation is sufficient and matches the regulatory baseline]*

### Templates

The bundle ships markdown templates for each phase artefact, copied into the project on commission. Templates have:

- Mandatory sections (the validator checks they exist and are non-empty)
- Optional sections (skipped freely)
- Inline guidance prompts (commented-out paragraphs explaining what each section should contain)

### Cross-phase review skill

A new `phase-review` skill that runs structured review of the current artefact against its cited prior artefacts. Same shape as the existing `requesting-code-review` skill but for design documents. Output is a structured review record committed alongside the artefact under review.

### Skills shipped (Programme bundle)

- `commission-programme` — installs the Programme bundle into a project, configures the validators, copies the templates
- `phase-init <phase>` — creates a phase artefact from the template
- `phase-gate <phase>` — runs the gate validator
- `phase-review <phase>` — **mandatory** for design-spec and test-spec phases; recommended for requirements-spec. Dispatches a structured review of the artefact against its cited prior artefacts. Mandatory because human-in-the-loop review is the control that ensures not just *existence* but *meaningfulness* of cross-phase links — `phase-gate` validates syntactic integrity; `phase-review` validates semantic soundness. *[Cross-line agreement 1: bidirectional traceability requires link integrity; humans verify link meaningfulness]*
- `traceability-export <format>` — produces audit-friendly traceability matrices in basic formats (CSV table, markdown matrix). Programme bundle ships simple formats; Assured bundle extends with standard-specific formats (DO-178C RTM, IEC 62304, ISO 26262 ASIL, FDA DHF). *[Line 1: §3 Claim 6 — traceability evidence export should be template-driven, not tool-specific]*

### Model selection hints

Each skill ships with a "Model selection" section giving purpose-shaped guidance (no model names). The pattern follows the existing `superpowers:subagent-driven-development` skill's "Model Selection" section, with explicit per-skill characterisation:

- `phase-review` is a **structured comparison and reasoning task** — comparing artefacts against prior phases, surfacing semantic gaps, identifying where links are syntactically correct but semantically thin. Prefer a model with strong reasoning over one optimised for throughput. *[Cross-line agreement 1: bidirectional traceability complexity is distributed across artefacts; review is the integrative judgement step]*
- `phase-gate` is **mechanical syntax-checking** — does the artefact exist, does it have required sections, do cited IDs resolve. Smaller / faster models are fine and probably cheaper.
- `phase-init` is **template instantiation** — copying a template, filling placeholders. Smaller models are sufficient.
- `commission-programme` is **a one-shot configuration task** — small per-project run, model choice has minimal cost impact; default model is fine.

The discipline: each skill states *what kind of work it is* (deep reasoning vs mechanical execution vs template instantiation), and the operator chooses model accordingly.

### Integration with existing superpowers

- `brainstorming` → produces the requirements-spec (the spec doc output by brainstorming becomes the requirements-spec)
- `writing-plans` → produces the design-spec (planning becomes design)
- TDD → drives test-spec and code together

The integration is composition, not replacement. Programme bundle adds gates and templates around the existing skills; it doesn't fork them.

### Method 1 design questions the research informs

- What rigour level of phase gates is appropriate? (Line 3 ALM tools landscape — what does sphinx-needs vs DOORS imply about gate strictness?)
- Should phase gates support partial progress (e.g., draft design-spec while requirements-spec is in revision)? (Line 1 traceability standards — change-impact obligations)

---

## 4. Method 2 in detail (builds on Method 1)

### Identifier system

Stable IDs across all spec types:

- `REQ-<feature>-<num>` — a requirement (e.g., `REQ-cross-library-001`)
- `DES-<feature>-<num>` — a design element
- `TEST-<feature>-<num>` — a test specification
- `CODE-<feature>-<num>` — a code unit (a function, class, or named module element)

For decomposed systems (program → sub-program → module), IDs are namespaced:

- `<program>.<sub-program>.<module>.<type>-<num>` (e.g., `P1.SP2.M3.REQ-007`)

The default decomposition is `P1.SP1.M1.*` for any project that hasn't declared a structure. Once decomposition is declared, IDs use the declared namespace.

### ID registry

A `library/_ids.md` file (parallel to the KB's existing `library/_shelf-index.md`) is auto-generated by `kb-rebuild-indexes` and tracks every ID, its source artefact, and its links to other IDs.

Validators:
- ID uniqueness (no two artefacts may claim the same ID)
- ID referenced in any spec must exist in the registry
- No orphan IDs (every REQ has at least one DES; every DES has at least one TEST)

### Spec-as-KB-finding

Each REQ / DES / TEST / CODE record is structurally a KB finding: title, terms (taxonomy keywords), facts (the actual content), links (to other IDs). It reuses the existing shelf-index entry shape.

The existing `research-librarian` queries against this just like it queries today's library: "what does our system say about authentication?" returns relevant REQ/DES/TEST records. The librarian doesn't know spec records are different from regular findings — they're the same data shape.

The existing `synthesis-librarian` extends to a new mode `SYNTHESISE-ACROSS-SPEC-TYPES`: takes findings from multiple spec types (REQ + DES + TEST + CODE) and produces a synthesis with `[REQ]`/`[DES]`/`[TEST]`/`[CODE]` inline tags. The existing attribution post-check (`check_synthesis_attribution` with `valid_handles` whitelist) extends naturally to this — the dispatch sources include the spec-type pseudo-handles.

### Bidirectional traceability

- **Forward**: REQ → DES → TEST → CODE. Each link declared in the linking artefact (DES references its REQs; TEST references its REQ + DES).
- **Backward**: regenerated index supports queries like "what tests cover REQ-auth-003?" or "what code implements DES-auth-005?".

Validators:
- **Forward link integrity**: every cited ID exists in the registry; references to non-existent IDs block commit. *[Cross-line agreement 1 — bidirectional traceability is the regulatory baseline]*
- **Backward coverage**: every REQ has at least one DES; every DES has at least one TEST; every TEST has at least one CODE annotation; every CODE carries at least one REQ/DES annotation. Orphans block commit. *[Line 1: §3 Claim 1]*
- **Index regenerability**: `kb-rebuild-indexes` regenerates backward indices from markdown source idempotently (byte-identical output on repeat runs). Auditors verify integrity by running the command and comparing to committed indices. Warn if index age exceeds threshold (default: 7 days) and code has been committed since. *[Line 1: §3 Claim 4; cross-line agreement 8 — tool-neutral evidence regenerability]*
- **Annotation format integrity**: every `implements: <ID>` reference must resolve to a real REQ/DES/TEST/CODE ID in the registry. Missing or malformed annotations block push (consistent with existing technical-debt checks). *[Line 2: §3 Claim 5]*

#### Optional validators (enabled by configuration for regulated contexts)

- `change-impact-gate` (default: **disabled**): blocks commits where code changes exist but no change-impact annotation is present. Recommended for IEC 62304, FDA 21 CFR Part 820, and ISO 26262 ASIL C/D contexts where change-impact assessment is a mandatory gating control. Commissioning script enables this gate by default when regulatory context is one of those three. *[Line 1: §3 Claim 5; cross-line agreement 6 — change-impact must be structured and upfront]*

### Decomposition

Decomposition is **declarative**, not inferred, and rooted in **Domain-Driven Design bounded contexts** as the primary primitive, layered with **Bazel's visibility-rule discipline** for cross-module dependencies. A "module" is a bounded context: a domain model with consistent ubiquitous language, owned by one team or part of one team. Modules group into sub-programs; sub-programs into programs. *[Cross-line agreement 5; Line 2: §3 Claims 1, 2, 4]*

The commissioning step adds a `programs` block to the project's configuration:

- Which programs exist
- Which sub-programs each contains
- Which modules each sub-program contains
- Which directory paths belong to which module
- **Granularity target per module**: `granularity: [requirement | function | module]`. Default is `requirement` (the finest, accepted by all five regulated standards). Modules may declare looser explicitly when justified by their risk class. *[Line 1: §3 Claim 3; cross-line agreement 7]*
- **Visibility rules**: which modules (contexts) may depend on which, declared in a context-map document. *[Line 2: §3 Claim 2 — Bazel visibility-rule discipline]*
- **Optional within-module structure**: modules may declare hexagonal architecture (`structure: hexagonal`); code within tagged `core` (domain logic) and `adapter` (infrastructure) directories. Optional, never required. *[Line 2: §3 Claim 3]*

Validators:
- Every REQ has a module assignment
- Every CODE annotation maps to a declared module path
- No module has un-cited code (warn) or un-tested REQs (block)
- **Visibility-rule enforcement**: code imports must respect declared visibility; circular dependencies between programs block, between sub-programs warn. *[Line 2: §3 Claim 2]*
- **Anaemic-context detection**: code implementing a REQ/DES not co-located in its declared module flagged as boundary violation. *[Line 2: §3 Claim 4 — anaemic contexts is the explicit failure mode designed against]*
- **Granularity match**: if module M1 declares `granularity: requirement`, all code in M1 must carry REQ-level annotations; warn (not block) if actual granularity is coarser than declared (might be progressive tightening). *[Line 1: §3 Claim 3]*

The framework does not try to suggest decomposition. The team declares it; the framework enforces what is declared.

#### Decomposition refactoring without ID loss

When teams refactor decomposition (merging programs, moving modules between sub-programs, splitting modules), `kb-rebuild-indexes` remaps old IDs to new paths, preserving historical traceability. This mitigates premature-decomposition risk: if initial decomposition is wrong, teams can refactor it without losing traceability history. *[Line 2: §3 Claim 6 — premature-decomposition mitigation]*

### Organisational metadata (optional)

Organisational metadata (owner, reviewer, approver) is **optional in spec YAML frontmatter**, never baked into the schema. Process enforcement (who approves what; the workflow tool's job) lives in Git hooks or CI workflows, not in the spec-record schema. This prevents the framework from breaking when organisations reorganise — Conway's law applied to requirements is a documented failure mode of database-centric ALM tools. *[Line 3: §4 Rejection C; library/doors-cautionary-tale.md]*

### KB extension to code (annotation-driven)

Source code carries inline comment annotations that link CODE → DES / REQ. Example in Python:

```python
def authenticate(token: str) -> AuthResult:
    # implements: DES-auth-005, REQ-auth-003
    ...
```

A new `kb-codeindex` skill walks the source tree, parses annotations, and emits `library/_code-index.md` — a shelf-index-shaped file where each entry is a code location, its function/class name, and the IDs it implements. The librarian queries the code-index the same way it queries the regular shelf-index. Output is a `[code]`-tagged finding with file:line locations.

This deliberately does NOT do AST parsing, semantic search, call graphs, or sourcegraph-class intelligence. Code is treated as text-with-annotations. The cost is annotation maintenance; the benefit is a single KB substrate handles spec retrieval and code retrieval.

### Render pipeline

A new `traceability-render <module-id>` skill produces a human-scoped document for one module: just its REQs, just its DESs, just its tests, just its implementing code locations, with all inter-ID links rendered as anchor links.

This is what humans review. The agent records (REQ-files, DES-files, etc.) remain authoritative; the rendered document is a derivative artefact.

### Skills shipped (Assured bundle, in addition to Method 1's skills)

- `commission-assured` — installs Assured bundle (which includes everything from `commission-programme`)
- `req-add`, `req-link` — mint and connect IDs (alternatives are hand-editing the markdown; the skills are conveniences, not gatekeepers)
- `code-annotate <artifact-id>` — auto-generates boilerplate `implements: <ID>` annotations for code referencing the given REQ/DES/TEST. Reduces manual burden so annotations stay current. *[Line 2: §3 Claim 5 — make annotation cheap so traceability stays alive]*
- `module-bound-check` — runs decomposition validators (visibility rules, anaemic-context detection, granularity match)
- `kb-codeindex` — parses annotations and emits the code-index
- `change-impact-annotate <artifact-id>` — when a requirement, design element, or code unit changes, guides the team through declaring impact scope (e.g., "REQ-005 changed; affected: DES-012, TEST-034, CODE-segment-B"). The annotation is recorded as a structured artefact alongside the changed item. Required for `change-impact-gate` to pass. *[Line 1: §3 Claim 2; cross-line agreement 6]*
- `traceability-render <module-id>` — produces human-scoped doc for one module: just its REQs, just its DESs, just its tests, just its code locations, with all inter-ID links rendered as anchor links. Highlights orphan code and anaemic-context violations.
- `traceability-export <format>` — produces audit-friendly traceability matrices in **standard-specific** formats: `do-178c-rtm`, `iec-62304-matrix`, `iso-26262-asil-matrix`, `fda-dhf-structure`. Programme bundle's `traceability-export` ships basic formats; Assured extends with these. *[Line 1: §3 Claim 6 — template-driven export, supports all major standards]*

### Commissioning guidance

The `commission-assured` skill includes explicit guidance for the team:

- **Defer decomposition.** Decomposition should reflect *current* organisational boundaries and business domains, not speculative future structure. Default to `P1.SP1.M1.*` (one program, one sub-program, one module covering everything) and refactor when operational pain or business-domain shifts motivate change. *[Line 2: §3 Claim 7 — Segment microservices reversal as the canonical premature-decomposition warning]*
- **Granularity per module.** Commissioning script asks regulatory context (none / DO-178C / IEC 62304 / ISO 26262 / IEC 61508 / FDA) and proposes per-module granularity. Conservative default is `requirement`. Object-code granularity is opt-in only.
- **Change-impact gating.** When regulatory context is IEC 62304 / FDA 21 CFR Part 820 / ISO 26262 ASIL C/D, the commissioning script enables `change-impact-gate` by default. Other contexts default disabled.
- **Module-size heuristic.** "A module should be the scope of responsibility for one team (or part of one team)." This is heuristic, not enforced — teams may declare smaller or larger modules with documented justification.
- **Sub-program / program scale.** A program is a coherent product or service. A sub-program is a major capability area within it. Modules within a sub-program share a domain language. Don't worry about cross-program coupling at commissioning time — refactor when the cost surfaces. *[Line 2: §3 Claims 1, 7]*

### Method 2 design questions the research informs

- What rigour of bidirectional traceability is required for "assurance"? (Line 1 traceability standards)
- Which decomposition primitive should the framework borrow concepts from? (Line 2 decomposition patterns)
- Which patterns from existing requirements tools should we adopt? (Line 3 ALM landscape)
- What's the canonical "do not become this" warning we should design against? (Line 3 ALM landscape — DOORS specifically)

---

## 5. Why both methods ship together

The architect's review (`reviews/architect-reviews/SDLC-types.txt`) framed Method 1 and Method 2 as alternatives. After scope analysis, they are better understood as **different points on a single richness axis**: Method 2 is Method 1 plus a richer underlying data model. Building Method 1 alone would be a half-step; building both together establishes the substrate (templates + gates + cross-phase reviews) that Assured then layers traceability + decomposition + KB-for-code on top of.

The framework author's call (Steve, 2026-04-26) is that Method 2 will be more immediately useful for moving the state of the art forwards, and so they ship together rather than Method 1 first.

Operationally:
- Single branch (`feature/sdlc-programme-assured-bundles`) until both bundles are PR-ready
- Method 1 substrate (templates, gate validators, `phase-review` skill) is built once and shared between bundles
- Both bundles dogfooded on this repo for at least one EPIC (candidates: EPIC #142 sub-features 3-8) before either is recommended externally

---

## 6. What is explicitly out of scope for these bundles

- **AST-level code intelligence.** No call graphs, no semantic search, no automated refactor support. Code KB is annotation-driven only.
- **IDE integration.** The bundles are filesystem-first. IDE plug-ins are downstream tooling that someone can build on top of the substrate.
- **Full ALM database.** No relational schema, no stored procedures. Every artefact is a markdown file in Git.
- **Industry certification itself.** The Assured bundle produces *substrate that helps reach assurance* (e.g., bidirectional traceability records, decomposition declarations, change-impact records, code annotations, phase gates, independent reviews), not *certification* (which requires an accredited certification authority and is outside any framework's reach). Organisations may use the Assured bundle to build a safety case or prepare for external certification audits, but the framework itself is a tool, not a certifier. *[Line 1: §3 Claim 7]*
- **Bidirectional ReqIF sync.** ReqIF (Requirements Interchange Format, OMG standard) round-trip workflows are documented as lossy in the practitioner literature: attributes silently dropped, parent-child relationships unreconstructible, complex link types degraded. The Assured bundle supports **one-way ReqIF export only** (as a plugin, not core). Round-trip sync is explicitly out of scope. *[Line 3: §3 Claim 7; library/doors-cautionary-tale.md]*
- **Migration of pre-Assured projects' un-annotated code.** Manual annotation pass is part of adoption cost; the framework ships a coverage checker (`module-bound-check`) that reports gaps, not an auto-annotator.
- **Decomposition suggestion.** The framework enforces declared decomposition; it doesn't suggest where module edges go.
- **Automatic semantic change-impact detection.** The framework records human-declared change-impact annotations; it does not infer impact via call graphs, data-flow analysis, or AI-driven reasoning. *[Line 1: §4 first rejection]*
- **Distributed multi-team ID coordination.** Each project has its own ID namespace. Centralised ID governance across teams requires a coordination service outside the scope of an open-source filesystem-first framework. Document conventions; don't bake distributed coordination into the framework.

---

## 7. Glossary (cross-prompt)

- **Bundle**: a plugin shipped with a fixed set of constitution, agents, skills, templates, and validators that together implement one SDLC option.
- **Commissioning**: the act of installing a bundle into a project, recorded in `.sdlc/team-config.json`.
- **Plugin**: a packaged set of Claude Code agents and skills installed via `/plugin install`.
- **Skill**: a markdown file at `<plugin>/skills/<name>/SKILL.md` that describes a procedure invokable by Claude.
- **Agent**: a markdown file at `<plugin>/agents/<name>.md` with YAML frontmatter declaring tools and behaviour, dispatchable via Claude Code's Agent tool.
- **Librarian**: an agent that queries the project's knowledge base (shelf-index + curated markdown findings) and returns structured retrieval or synthesis output.
- **Shelf-index**: a hash-tracked index of every entry in a `library/` directory, used by the librarian for fast retrieval without reading every file.
- **Attribution post-check**: a Python validator that runs on synthesis output and rejects any claim not tagged with a real source handle. The structural guarantee that no fabricated citations reach the user.
- **Phase gate** (Method 1): a validator that blocks SDLC progression unless the previous phase's artefact is present and properly cited.
- **Decomposition primitive** (Method 2): the unit of architectural decomposition (program / sub-program / module). Declared in a registry, enforced by validators against filesystem layout.
- **Annotation-driven indexing** (Method 2): parsing inline code comments (e.g., `# implements: DES-005`) to build a code-index queryable by the librarian.

---

## 8. What this research campaign is NOT trying to settle

These open questions are **out of scope for the research**:

- Whether to ship Method 1 first or both together (decided: both together).
- Whether Method 2 is worth building (decided: yes — architect recommendation, framework author concurs).
- Specific Claude model choices (skill-level model hints are purpose-shaped, not name-shaped).
- Plugin packaging mechanics (Programme + Assured will follow the existing 12-plugin family pattern).
- How `/sdlc-core:commission` from EPIC #97 sub-feature #98 routes to Programme vs Assured (will be settled in plan-writing, not research).

The research informs *content* decisions: what rigour, which patterns, which lessons to apply. Operational decisions are the framework author's call.
