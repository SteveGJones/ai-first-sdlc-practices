# Research Line 2 — Decomposition Patterns in Practice

## Why this matters

The drafted Method 2 scope hinges on a decomposition primitive: program → sub-program → module → code/test elements, with each level having a clear boundary and a bounded set of requirements. This decomposition is the load-bearing structure that lets agents work with small, scoped contexts instead of carrying tens of thousands of requirements in working memory.

The hardest unsolved design call in Method 2 is *which decomposition pattern to borrow from*. Mature ecosystems — Bazel, Erlang/OTP, Domain-Driven Design, microservices, MBSE/SysML, ARINC 653, AUTOSAR — all model module boundaries differently, and each pattern has a distinctive failure mode when boundaries are wrong. We need to pick deliberately.

This research line surveys those patterns, characterises each, and identifies which model best suits a markdown-driven, agent-orchestrated framework where decomposition is *declared* in a registry rather than enforced by a build system or a runtime.

## How to use this prompt

1. Open Claude Desktop with extended research mode enabled.
2. Copy the entire content of the **`## Prompt`** section below into a new conversation.
3. Allow the research to complete. Expect ~45-90 minutes for a thorough output.
4. Save the output to `research/sdlc-bundles/outputs/02-decomposition-patterns/output-1.md`.
5. If the output is thin or off-target, save it as `output-1-thin.md` and run a sharpened follow-up.

---

## Prompt

You are conducting deep research to inform the design of an open-source software-development-lifecycle framework. The framework will support architectural decomposition: a project is broken into a small number of programs, each containing sub-programs, each containing modules, each containing code/test elements. Requirements, design elements, tests, and code are all assigned to a level in this hierarchy and tagged with a stable identifier.

Decomposition in this framework is **declarative** (a registry file says which programs exist, which sub-programs each contains, which modules each sub-program contains, and which directory paths belong to which module). It is enforced by validators that run during the development lifecycle rather than by a build system or a runtime. The framework is markdown-driven and filesystem-first; it does not own the build system or the deployment topology.

The decision your research informs is: which existing decomposition pattern (or combination) should this framework borrow its concepts and validators from? Which pattern's failure modes should it design against?

### Scope of research

Cover the following decomposition patterns. For each, answer the listed questions.

- **Bazel build graphs** — `BUILD` files, packages, targets, visibility rules, the dependency graph as a build artefact
- **Erlang/OTP supervision trees** — applications, supervisors, workers, restart strategies, the "let it crash" boundary model
- **Domain-Driven Design (DDD) bounded contexts** — context maps, ubiquitous language, anti-corruption layers, aggregates as the consistency boundary
- **Microservice boundaries** — Newman's *Building Microservices* and Richardson's *Microservices Patterns* on service decomposition; also the bounded-context-as-microservice mapping debate
- **MBSE / SysML** — blocks, ports, item flows, hierarchical block definition diagrams, allocation tables (the SysML approach to system-level decomposition)
- **ARINC 653 partitions** — time and space partitioning in avionics IMA (integrated modular avionics), partition-level isolation, partition scheduling
- **AUTOSAR software components** — SWCs, runtime environment (RTE), the virtual function bus, ports and interfaces
- **Hexagonal architecture / Ports-and-Adapters (Cockburn)** — included as a contrast point because it's a within-module decomposition rather than across-module

For each pattern, answer:

1. **Decomposition primitive.** What is the unit of decomposition (build target, supervisor, bounded context, microservice, block, partition, SWC)? What does an instance of that primitive *contain* (what's inside) and what does it *expose* (its boundary)?
2. **Boundary declaration.** How is the boundary declared (BUILD file syntax, supervisor module, context map document, OpenAPI spec, SysML block diagram, ARINC partition table, ARXML SWC description)? Is the declaration enforced (build break, type error, runtime fault) or only conventional (review catches violations)?
3. **Coupling visibility.** When code violates a boundary, how is the violation made visible? Compile-time, build-time, runtime, review-time, never?
4. **Hierarchy support.** Does the pattern support nested decomposition (programs containing sub-programs containing modules)? If yes, how is the nesting modelled? If no, what's the practical workaround?
5. **Identifier discipline.** Does the pattern require stable identifiers for its primitives? How are they assigned and maintained?
6. **Failure modes.** What goes wrong when a team gets the decomposition wrong with this pattern? Cite practitioner literature: god-modules, distributed monoliths, supervisor explosion, anaemic bounded contexts, AUTOSAR-induced glue-code, ARINC partition starvation, Bazel BUILD-file fragility.
7. **Translatability to markdown-declared framework.** Could the *concept* of this primitive be translated into a markdown-registry-and-validator pattern (rather than its native enforcement mechanism)? Specifically: if we declared the decomposition in a markdown registry and validated it with filesystem checks, would we capture the pattern's value or lose it?

### Output structure

Produce a single document with the following sections.

**Section 1 — Executive summary.** One paragraph per pattern characterising its decomposition primitive, its boundary-enforcement strength, and its translatability to a markdown-declared framework. Plus one closing paragraph identifying the *strongest* and *weakest* candidates for our framework. Maximum 700 words.

**Section 2 — Comparison matrix.** A table with one row per pattern and one column per question (1-7 above). Each cell short and factual with citation indices.

**Section 3 — Per-pattern deep dive.** One subsection per pattern. Each subsection answers questions 1-7 in narrative form with citations. Each subsection ends with a "Failure modes from the literature" mini-section listing 2-4 documented failure modes with citations. Each subsection should be 400-700 words.

**Section 4 — Cross-pattern observations.** What is shared across the strongest patterns? Which patterns rely on a build system or runtime for enforcement vs which can be enforced by validators alone? Are there patterns that explicitly model nested decomposition (program → sub-program → module) and which collapse the hierarchy?

**Section 5 — Counter-arguments and known criticism.** Independent of pattern-specific failure modes (covered in Section 3), what does the literature say about decomposition *as a whole*? Anti-patterns the practitioner community has identified: premature decomposition, over-decomposition, decomposition without ownership, "shapeless" software (Brooks). Surface 4-6 such criticisms with citations.

**Section 6 — Implications for our framework.** Three subsections:

- *Closest model* — which pattern's concepts best translate to a markdown-declared, validator-enforced framework? Make a specific recommendation with reasoning. The recommendation may be a hybrid (e.g., "borrow the boundary-declaration discipline from Bazel and the failure-mode observability from Erlang/OTP supervisors, ignore the runtime aspects of both").
- *Failure modes to design against* — which two or three failure modes from the surveyed patterns are most likely to recur in our framework? What validator or convention would mitigate each?
- *What we should NOT borrow* — patterns or aspects of patterns that look attractive but would be harmful (e.g., "do not borrow MBSE/SysML's tooling-heaviness; the value is in the conceptual primitives, not the modelling tools").

This is the most important section for our use. Maximum 1,000 words.

**Section 7 — Bibliography.** Every cited source listed per the reference-discipline section below.

### Reference discipline

Every factual claim must carry an inline citation in the form `[N]` indexing into a bibliography at the end.

Bibliography entries:

```
[N] <Author>. (<Year>). <Title>. <Source type>. <URL or DOI or publisher>. Accessed <YYYY-MM-DD>.
   Source-type tag: [book | peer-reviewed | conference-paper | standard | tech-report | practitioner-blog | vendor-doc | wiki | conference-talk]
   Credibility note: <one-line note on authority>
```

Source quality requirements specific to this research line:

- **Books**: cite specific page numbers or chapters where possible. *Building Microservices* (Newman), *Microservices Patterns* (Richardson), *Domain-Driven Design* (Evans), *Implementing Domain-Driven Design* (Vernon), *Designing Data-Intensive Applications* (Kleppmann) are highly valued primary sources.
- **Erlang/OTP**: official OTP documentation, Joe Armstrong's thesis "Making reliable distributed systems in the presence of software errors" (2003), Joe Armstrong's *Programming Erlang*.
- **Bazel**: official Bazel documentation, Google's "Software Engineering at Google" book chapters on build systems.
- **MBSE/SysML**: OMG SysML specification (current version), Friedenthal et al. *A Practical Guide to SysML*.
- **ARINC 653**: ARINC 653 specification (parts 1-7), DO-297, peer-reviewed papers on IMA.
- **AUTOSAR**: AUTOSAR official documentation (Classic Platform), conference papers from AUTOSAR-using OEMs.
- **Hexagonal**: Cockburn's original blog post and follow-up clarifications; Vlad Khononov's writing on contemporary interpretations.
- For criticism (Section 5): Fred Brooks' *Mythical Man-Month* and *No Silver Bullet*, Pete Hodgson on distributed monolith, Sam Newman on microservice anti-patterns.

CRAAP-style quality assessment in each bibliography credibility note.

### What to avoid

- Do not produce a tutorial on each pattern; the deliverable is a *comparison and translatability assessment*, not "what is Bazel".
- Do not cite vendor marketing as evidence of pattern strength. Cite books, papers, or independent practitioner writing.
- Do not extrapolate beyond what the literature actually says. If the literature is silent on a sub-question, say so.
- Do not recommend a pattern based on its popularity. Recommend based on translatability to our framework's shape.
- Do not produce more than light analysis of patterns we did not list. If something important is missing from the list (e.g., "C4 model decomposition"), surface it as a one-paragraph note in Section 4 rather than a full deep-dive.

### Length and depth

Target document length: 6,000-10,000 words. Section 6 (implications) is the deliverable that informs framework design — allocate the most analytical depth there.
