# Research Line 3: ALM / Requirements-Tools Landscape
## Deep Comparative Analysis for the Assured Bundle

---

## Section 1: Executive Summary

The requirements-management and application-lifecycle-management tool landscape is dominated by two camps: relational, server-based commercial tools (IBM DOORS, Siemens Polarion, Jama Connect) optimised for enterprise-scale regulated industries, and lightweight, file-based open-source tools (sphinx-needs, Doorstop, strictdoc) optimised for integration with development workflows [1][2][3][4][5]. Both camps handle the core problem — minting stable identifiers for requirements, maintaining bidirectional links, and producing traceability artefacts — but with fundamentally different architecture assumptions.

**sphinx-needs** [1] is a Sphinx documentation extension enabling declarative definition of "need" types (requirements, features, test cases) with configurable link validation. It stores needs in reStructuredText files with YAML-like syntax, maintains traceability links as first-class entities, and integrates directly into docs-as-code pipelines. Used in regulated contexts including aerospace (where it supports DO-178B compliance) and automotive (ISO 26262), sphinx-needs demonstrates that open-source, file-based requirements tools can meet assurance-level rigour [6][7]. Its known limits are scaling (Sphinx's multiprocessing architecture struggles above 10,000 pages) and configuration complexity for advanced users seeking dynamic query functions [1].

**Doorstop** [8] stores each requirement as a YAML file in a Git repository, with a document tree formed by directory hierarchy and explicit parent-child links. Validation is command-line-driven (no database needed); publishing is to HTML/PDF. The value proposition is minimal lock-in — requirements live as plain YAML in Git — and integration with development workflows. Known friction: the requirement for manual link maintenance and no built-in web UI for collaborative editing [8][9].

**strictdoc** [10] introduces a more expressive `.sdoc` format (TOML-like syntax with ReqIF compliance) and web-based UI for editing and viewing. It supports decomposition into sections/chapters, rich metadata fields, and traceability matrix generation. Less mature than sphinx-needs or Doorstop, but designed explicitly for regulated contexts and large-scale requirements documents [10].

**ReqIF** [11] (Requirements Interchange Format, OMG standard since 2011) is not a tool but an XML-based schema for exchanging requirements between tools. Virtually all commercial requirements tools support ReqIF import/export, but real-world round-trip workflows suffer from data loss: attributes not supported in the receiving tool are silently dropped; parent-child relationships cannot be altered on round-trip; complex link types degrade to binary links [12][13].

**IBM DOORS** (classic, version 9.x) [14] pioneered the module-and-attribute data model for enterprise requirements: requirements grouped into modules (themselves hierarchical), each with configurable attribute rows (status, priority, custom fields). All data lives in a relational database; searching, filtering, and reporting are database operations. **DOORS Next** (web-based replacement on IBM Jazz architecture) aims to modernise the UI but retains the core data model and introduces new pain points: migration from DOORS Classic requires wholesale rewriting of DXL customisations (which can exceed 1 million lines); views don't migrate; historical data and baselines are not preserved [15][16]. DOORS' canonical failure is vendor lock-in via proprietary `.rmd` format, steep licensing costs (enterprise sales model), and a UI widely described as "outdated" and "clunky" by users seeking to migrate away [17][18]. The richtext-import nightmare (legacy DOORS rich-text fields do not round-trip cleanly through ReqIF) is a documented pain point [19].

**Siemens Polarion ALM** [20] is a web-based, modular ALM platform (requirements + test + change management) supporting large-scale projects with deep configuration. Strengths include LiveDocs (collaborative spec editing with paragraph-level traceability) and native ReqIF support. Weaknesses include configuration complexity (Polarion Query Language, workflow customisation) that creates a steep learning curve for non-technical users, and no published pricing (enterprise sales process) [20][21].

**Jama Connect** [22] is the leading cloud-based ALM platform for regulated industries (aerospace, automotive, medical devices). User reviews (G2: 97 customer satisfaction score) highlight ease of use, strong versioning, unlimited read-only stakeholder access, and intuitive UI. Core architecture is proprietary SaaS with multi-tenant scaling claims (supports 10 million items). Known limitation: upload/import size constraints for bulk operations [22][23].

**Reqtify** (Dassault Systèmes) [24] is an end-to-end traceability tool with 100+ connectors to capture requirements from diverse sources (documents, code, test tools). Compliance with IEC-61508, ISO26262, DO178C/254. Less commonly deployed than DOORS or Polarion; positioned as a specialist tool for organisations with heterogeneous tool environments [24].

**Helix ALM** (Perforce, formerly TestTrack) [25] and **codebeamer** (PTC, formerly Intland Software) [26] are full-lifecycle ALM platforms with similar value propositions to Polarion: centralised requirements + test + change management with configurable workflows. codebeamer emphasises gapless traceability and integration with 10+ version control systems [26].

The closest existing tool to what we are building is **sphinx-needs**: markdown/reStructuredText-native, filesystem-first, link-validated, designed for docs-as-code teams. The canonical "do not become this" warning is **DOORS**: its module-and-attribute relational model, rich-text legacy, proprietary data format, vendor lock-in, and user-unfriendly migration path are anti-patterns to study and avoid [14][15][16][17][18].

---

## Section 2: Comparison Matrix

### Table A: Feature Comparison (Data Model, Identifier Scheme, Link Handling, Code Integration, VCS Support, Extensibility)

| Tool | Data Model | Identifier Scheme | Link Model | Code-to-Spec | VCS Support | Extensibility |
|---|---|---|---|---|---|---|
| **sphinx-needs** [1] | Flat RST + YAML directives; in-memory document tree | Declared prefix + auto-increment (e.g., REQ_001); stable across renames | Explicit link types (links, child_needs); validated post-build | External annotation parsing via plugins | ✓ Native Git (stored in repo) | Sphinx extension API; Python plugins for custom link types, filters |
| **Doorstop** [8] | YAML files per requirement; directory hierarchy as document tree | Document prefix + item number (e.g., SRD001); derived from filename | Parent-child links as explicit list in YAML; tree validation on command-line | Code annotation regex matching (stored as metadata); no native IDE plugin | ✓ Native Git (stored in repo) | Python API for scripting; custom validators; publishing templates |
| **strictdoc** [10] | .sdoc files with TOML-like syntax; structured sections/chapters | UID declared in requirement; MID (module id) namespace optional; ReqIF-compatible | Forward/backward links via [LINK: ...] syntax; live cross-reference index | Annotation in code + source-code parsing (Python-agnostic parser) | ✓ Native Git (stored in repo) | Python API; web UI for editing; export to multiple formats |
| **ReqIF** [11] | XML schema (meta-model); tool-agnostic representation | Defined by receiving tool; stable across round-trip IF source tool preserves IDs | Relationship objects (reqif:Relationship); type-safe link tables | Tool-specific; ReqIF itself agnostic | Via tool (e.g., Git if tool integrates) | Per-tool customisation of object types; no standard extension mechanism |
| **IBM DOORS** [14] | Relational: modules + attributes in database; hierarchical folders | Auto-assigned in module (e.g., MOD00001); stable within module; renaming via DXL | Link tables in database; referential integrity enforced by DB | DXL automation; limited direct code annotation; third-party IDE plugins | Indirect (VCS integration via CI/CD; no native VCS) | DXL scripting (1M+ LoC in legacy deployments); limited extensibility in DOORS Next |
| **DOORS Next** [16] | Jazz RDF-based; artifact types + relationships; reduced hierarchy | Assigned per artifact; stable via baseline/configuration concept | Artifact link relationships; OSLC standard | OSLC-based via REST; IDE plugin extensibility | Indirect (OSLC bridges) | Artifact type definition; no equivalents to DXL customisation |
| **Siemens Polarion** [20] | Relational: work items (requirements, tests, defects) + custom fields | Auto-assigned (e.g., REQ-001); stable via space/project hierarchy | Explicit links with configurable types; bidirectional | IDE plugins (e.g., Visual Studio); coverage via annotation | Indirect (SVN/Git integration for change tracking) | Polarion Query Language (PQL); workflow automation; add-ons via Siemens portal |
| **Jama Connect** [22] | Proprietary SaaS relational; items + relationships + versioning | Auto-assigned; unique per project; stable across versioning | Item relationships with configurable link types; live traceability matrix | Code annotation via plugin; IDE integration via Planview Hub | Git/SVN integration via connectors | REST API; item type customisation; limited scripting |
| **Reqtify** [24] | Meta-tool: aggregates requirements from 100+ external sources | Source-tool IDs preserved in mappings | Traceability links across source tools; impact analysis | Source-tool dependent (100+ connectors) | Via source tool | Connector-based (extensible via custom connectors) |
| **Helix ALM** [25] | Relational: requirements + test cases + defects in shared schema | Auto-assigned per workspace; stable via versioning | Explicit requirement-to-test-to-defect links | IDE integrations (Visual Studio, Eclipse) | SVN/Git integration | Customisation via scripting; web API |
| **codebeamer** [26] | Relational: requirements + tests + implementation items + custom types | Auto-assigned; stable per project | Native links with configurable types; gapless traceability | Git/SVN/Mercurial/Plastic integration; code annotation support | ✓ Native integration (tracks changes from VCS) | Custom item types; workflow automation; API |

### Table B: Known Failure Modes (Scaling, Configuration, Data Loss, Lock-in)

| Tool | Scaling Failure | Configuration Failure | Data Loss Failure | Lock-in Risk |
|---|---|---|---|---|
| **sphinx-needs** [1] | Build time > 30 min for 25K pages; memory > 32 GB; parallelisation issues above 500 pages | Complex dynamic function syntax; learning curve for need-type customisation | Sphinx build corruption can require rebuild | Low: stored in Git; standard RST format |
| **Doorstop** [8] | No documented scaling issues to date | Manual link management can become tedious; no UI for large projects | Broken YAML syntax can invalidate document tree | Very low: plain YAML + Git; portable |
| **strictdoc** [10] | Web UI performance not documented for 10K+ requirements | .sdoc format learning curve; initial setup overhead | Unclear; smaller user base means fewer documented cases | Low: .sdoc is open format; ReqIF export available |
| **ReqIF** [11] | Standard-level; no tool-specific scaling issues | Round-trip requires careful field mapping | Parent-child relationships cannot be changed on round-trip; attributes not in receiving tool are dropped [12] | Per-tool; ReqIF is interchange standard |
| **IBM DOORS** [14] | Search performance degrades > 25K items; modules within modules compound query complexity | Rich-text import nightmare; DXL customisations brittle; deep attribute schema | Upgrade/migration data loss; baselines not reliably exported; module history lost in DOORS Next migration | Very high: proprietary .rmd format; no clean export to other tools; vendor sales model locks in customers |
| **DOORS Next** [16] | Not documented; Jazz architecture aims for enterprise scale | Workflow customisation requires deep Jazz platform knowledge | DXL scripts cannot be migrated from DOORS; views incompatible; historical data lost [15] | Very high: Jazz/OSLC lock-in; no export to legacy DOORS |
| **Siemens Polarion** [20] | Handles 100M+ items claimed; no public failure reports | PQL complexity; workflow config depth; initial setup panic for non-technical users | Not documented; ReqIF export/import available | High: Siemens ecosystem; proprietary workspace model; no published pricing makes switching costly |
| **Jama Connect** [22] | 10M items claim; no documented scaling failures | Intuitive UI reduces config burden; limited deep customisation | Cloud SaaS model means data loss risk managed by vendor; backup/restore policies not fully public | High: proprietary cloud SaaS; data in Jama's jurisdiction; termination/data export process unclear |
| **Reqtify** [24] | Connector-based; scales with source-tool capacity | 100+ connectors = complex mapping landscape | Depends on source tool; bidirectional sync can lose data if source tool doesn't support round-trip | Medium: depends on source-tool ecosystems; Dassault lock-in for dedicated users |
| **Helix ALM** [25] | Supports large projects; no public scaling failures | Scripting and workflow customisation require development effort | Relational backup/restore standard; no documented data loss issues | Medium-High: proprietary Perforce hosting; workspace-level export available |
| **codebeamer** [26] | Proven for 10K+ requirements in practice | Web UI friendly; customisation via API + configuration | Relational backup/restore; VCS integration provides version history | Medium-High: PTC ecosystem; workspace-level export available |

---

## Section 3: Per-Tool Dossier (Brief Summary)

This section summarises each tool's core characteristics in narrative form. Detailed deep dives on sphinx-needs (Section 4) and DOORS (Section 5) follow.

**sphinx-needs** [1] is a Sphinx documentation extension storing needs as inline directives in RST files. Needs are indexed at build time; the filesystem is the source of truth. Identifier scheme: prefix + auto-increment (REQ_001, TEST_042). Link model: declared links with static validation at build time. Code linking: annotation-driven via plugins. Core value: zero database overhead, Git-native, suited for docs-as-code teams and regulated industries (DO-178B, ISO 26262) [6][7]. Known limits: scaling above 500 pages in a single Sphinx project; no web UI; dynamic function syntax has steep learning curve [1].

**Doorstop** [8] stores each requirement as a YAML file; directory hierarchy forms document tree. Identifier scheme: document prefix + sequential number (SRD001). Link model: parent-child links declared in YAML, validated via command-line. Code linking: custom attributes or external scripting. Core value: maximum portability (plain YAML + Git), zero administrative overhead. Known limits: no web UI; manual link maintenance; command-line tooling less polished than commercial tools; used in RTEMS and embedded systems [8][9][10].

**strictdoc** [10] uses custom `.sdoc` format (TOML-like syntax, one file per document). Identifier scheme: user-declared UIDs (e.g., REQ-001, SPEC.2.3.4). Link model: [LINK: ...] directives with bidirectional indexing. Code linking: source-code parser (language-agnostic, no AST). Core value: structured specification documents with web UI for editing; designed for regulated industries. Known limits: smaller community; less mature than sphinx-needs; scaling not documented [10].

**ReqIF** (Requirements Interchange Format) [11] is an XML-based exchange schema (OMG standard, 2011). Not a tool but a data format. Core value: tool-agnostic requirement exchange. Known limits: round-trip workflows suffer data loss; parent-child relationships cannot be re-assigned; non-standard extensions are dropped [12][13]. Lesson: use ReqIF as one-way export (markdown → ReqIF), not for bidirectional sync.

**IBM DOORS** (see Section 5 deep dive) [14] introduced module-and-attribute relational model: requirements grouped into modules, each requirement a row, each column an attribute. Database-centric. Core value: powerful query/search, designed for 100K+ requirements. Known limits: proprietary `.rmd` binary format, vendor lock-in, 1M+ lines of DXL customisation code in large deployments, search performance degrades above 25K items, expensive per-seat licensing, poor usability (described as "clunky" by users) [17][18][19]. Migration to DOORS Next is failure-prone: DXL scripts cannot be migrated, views incompatible, data loss [15][16].

**Siemens Polarion ALM** [20] is a web-based ALM platform with relational database backend. Identifier scheme: auto-assigned per space (REQ-001). Link model: explicit work-item relationships. Code linking: IDE plugins. Core value: LiveDocs (collaborative spec editing with paragraph-level traceability), full-lifecycle ALM (requirements + test + change), Siemens ecosystem integration. Known limits: Polarion Query Language (PQL) and customisation require deep expertise; no published pricing; steep learning curve for non-technical users; configuration complexity [20][21].

**Jama Connect** [22] is the leading cloud SaaS ALM for regulated industries (aerospace, automotive, medical). Identifier scheme: auto-assigned per project. Link model: explicit item relationships. Code linking: IDE plugins via Planview Hub. Core value: ease of use (G2 score: 97 satisfaction), strong versioning, unlimited read-only access, intuitive UI. Known limits: limited customisation compared to Polarion; cloud SaaS lock-in; import size constraints; per-seat pricing (not published) [22][23].

**Other commercial tools** (Reqtify, Helix ALM, codebeamer) provide full-lifecycle ALM with similar core models. Reqtify emphasises 100+ connectors for heterogeneous tool ecosystems [24]. codebeamer emphasises VCS integration (Git, Mercurial, SVN, Plastic) for gapless traceability [26]. Helix ALM is a midmarket alternative to Polarion [25].

---

## Section 4: sphinx-needs Deep Dive

sphinx-needs is the closest existing tool to the Assured bundle's design. Understanding its strengths, implementation choices, and limits is essential for calibrating our scope.

### Architecture and Implementation

sphinx-needs extends the Sphinx documentation builder (Python-based, widely used for software documentation) by adding a new Sphinx directive: `.. need::` [1]. When Sphinx processes an RST file containing a need directive, the sphinx-needs extension intercepts the directive, parses its arguments and options, and registers the need in an internal index [1]. The index is built incrementally as Sphinx processes each file; at the end of the build, sphinx-needs performs validation (checking that all link targets exist) and generates output artefacts (HTML, traceability matrices, dynamic queries).

The core data structure is a Python dictionary per need, with keys corresponding to the configured need type (e.g., `requirements`, `specifications`, `test_cases`). Each need type has a schema: permissible field names, field types (string, list, enum), rendering templates, and link rules [1]. This schema is declared in the `conf.py` configuration file as `needs_types`, allowing teams to customise need types for their domain.

### Customisation via Configuration and Plugins

A large part of sphinx-needs' power lies in its configurability. The `needs_types` parameter allows teams to define new need types (in addition to the default `requirement`). For example, a team building an autopilot system might define types: `REQUIREMENT`, `SPECIFICATION`, `DESIGN_ELEMENT`, `TEST_CASE`, `IMPLEMENTATION`, `SAFETY_CLAIM`, `ARCHITECTURE_DECISION`. Each type can have different rendering styles (colour, prefix, icon in HTML output).

The `needs_links` parameter defines permissible link relationships [1]. For example: a `TEST_CASE` can link to a `REQUIREMENT` (forward link), and a `REQUIREMENT` should have no links (except backward links from `TEST_CASE`). The sphinx-needs build process validates the link topology: if a `SPECIFICATION` tries to link to a `TEST_CASE` (which is not in the `needs_links` rules), the build will emit an error or warning.

Beyond configuration, sphinx-needs is extensible via Sphinx plugins (Python code). Users can write custom role directives (to embed need IDs in prose), custom filters (to compute dynamic need fields), and custom renderers (to generate custom output formats) [1].

### Dynamic Functions and Computed Fields

One of sphinx-needs' most powerful features is dynamic functions: fields within a need can reference other needs' fields and compute values [1]. For example:

```
.. need:: REQ-auth-001
   :id: req_auth_001
   :status: approved
   :tests: test_001, test_002, test_003
   :test_count: eval("len({links:tests})")
```

The `test_count` field is computed at build time by evaluating Python code that counts the linked test cases. This allows requirements to maintain derived fields (like traceability coverage) automatically.

Dynamic functions are powerful but have a documented steep learning curve. The syntax is terse (heavy use of bracket notation for link queries), and debugging is difficult [1]. Teams adopting dynamic functions often require training or external expertise.

### Scaling Characteristics and Known Limits

sphinx-needs inherits Sphinx's architecture, which is fundamentally incremental-build-oriented (designed for single-documentation-project repositories, not monorepos). When Sphinx runs, it:

1. Parses all input files into an AST
2. Processes each AST node (invoking directives, roles, extensions)
3. Writes output files
4. Generates search indices, TOCs, and cross-reference tables

For projects with 500+ pages, this process becomes slow and memory-intensive [1]. The multiprocessing architecture (enabled via `sphinx build -j`) is intended to parallelize steps 2 and 3 across multiple processes, but in practice, much of the work is single-threaded (e.g., generating the search index), so speedup is only ~40% with 8 cores [1].

For large monorepos (25K+ pages), Sphinx can require 32+ GB of RAM and take 30+ minutes to build. The standard workaround is modular projects: split the monorepo into smaller Sphinx projects, build them independently, and link between projects via cross-project references. This works but adds complexity (separate build pipelines, inter-project link maintenance) [1].

### Use in Regulated Contexts

sphinx-needs is actively used in regulated aerospace and automotive projects. Specifically:

- **DO-178B/C Compliance (Avionics)**: sphinx-needs is used to manage requirements, design specifications, and traceability matrices required for DO-178B certification (a mandatory standard for commercial aircraft software). The tool's ability to generate stable HTML output (for audit trails) and traceability matrices (for certification authorities) is valuable [6][7].

- **ISO 26262 Compliance (Automotive Functional Safety)**: ISO 26262 requires bidirectional traceability (requirements → design → code → tests) and change impact analysis. sphinx-needs' link validation and traceability matrix generation satisfy these requirements [7].

- **Open-source Example: OpenAPS**: The OpenAPS project (open-source insulin pump controller, safety-critical) uses sphinx-needs to manage safety-critical specifications and produce compliance documentation [7].

These deployments demonstrate that sphinx-needs is not a toy; it is trusted in contexts where bugs or specification gaps can cost lives.

### Community and Maintenance

sphinx-needs is maintained by useblocks, a German software company specialising in documentation tooling. The project is active (regular releases, responsive to issues), and the community is small but engaged. The project has been in active development since ~2014, making it one of the older open-source requirements tools. Unlike Doorstop (primarily used in embedded Linux) or strictdoc (younger, smaller community), sphinx-needs has a visible user base in aerospace and automotive.

### Integration with Development Workflows

sphinx-needs assumes the project uses Git (or another VCS) and has a Sphinx-based documentation build. This is common in software projects (Python, C/C++, Rust, Go) but not universal. Teams using entirely proprietary tools or legacy workflows may not have Sphinx integration in place.

The integration with source code is via plugins: a team can write a plugin that parses code annotations and generates needs dynamically. Example: a C function with annotation `// implements: DES-auth-005` can be extracted at build time and added to the needs index. This is powerful but requires writing custom Python code.

### Known Limits and Trade-offs

1. **No Collaborative Web UI**: sphinx-needs assumes contributors use Git and editors to maintain RST files. For non-technical stakeholders, this is a barrier to entry.

2. **Scaling Above 500 Pages**: As noted, performance degrades significantly above 500 pages in a single project. The workaround (modular projects) is viable but adds complexity.

3. **Learning Curve for Dynamic Functions**: Advanced configurations (using dynamic functions to compute derived fields) require Python and bracket-notation expertise. This is a barrier for teams without Python expertise.

4. **Validation is Static, Not Real-Time**: The sphinx-needs build process runs at document build time, not at edit time. Users don't get real-time feedback when editing RST files; they must rebuild to see errors.

5. **No Native Database Queries**: Unlike DOORS or Polarion, sphinx-needs does not support ad-hoc queries on the requirements index. All queries must be pre-configured as need directives or plugin code.

### Summary: Lessons for the Assured Bundle

sphinx-needs demonstrates that:
- A filesystem-first, Git-native requirements tool can scale to thousands of requirements in regulated contexts.
- A declarative schema (need-type definitions in configuration) is the right way to define requirement structure.
- Link validation via static analysis (rather than a relational database) is sufficient and has low operational cost.
- Extensibility via plugins (Python code) is more powerful than configuration alone, but requires skill.

The Assured bundle should aspire to sphinx-needs' simplicity and VCS-native philosophy while avoiding its scaling bottlenecks (by supporting modular decomposition from the start) and its learning curve (by keeping the configuration simple by default and leaving advanced customisation to plugins).

---

## Section 5: DOORS / DOORS Next Deep Dive

IBM DOORS is the canonical ALM warning. Understanding why DOORS became the "do not become this" cautionary tale is critical for the Assured bundle.

### Historical Context: Why DOORS Dominated

DOORS (Dynamic Object Oriented Requirements System) was released in the 1990s and became the de facto standard for enterprise ALM [14]. At the time, requirements management was ad-hoc: requirements lived in Word documents, change tracking was manual, and traceability was a spreadsheet. DOORS introduced a relational database model for requirements (modules, attributes, links) with search and query capabilities far ahead of competitors. For large, regulated programmes (aerospace, automotive, medical devices), DOORS was transformative: it made requirements queryable and traceable.

By 2000-2010, DOORS had achieved such market dominance that it became the de facto standard in regulated industries. Customers invested heavily: integrating DOORS into build systems via DXL scripts, training teams, accumulating decades of requirements in DOORS databases. The lock-in was complete.

### The Module-and-Attribute Data Model: The Foundational Design

DOORS Classic (versions 7.x through 9.x) is built on a two-level hierarchy: Project → Folder → Module. Within each module, requirements are rows, and each column is an attribute (Status, Priority, Owner, Type, custom fields) [14].

This model was revolutionary in the 1990s because it provided:
- **Structured Storage**: Requirements are not just prose; they are structured data with typed fields.
- **Querying**: The relational database enables powerful searches (e.g., "find all requirements with Status=Open and Priority=High in Module X").
- **Versioning**: Baselines capture snapshots of module state for release management.

However, the model has profound limitations:

1. **Two-level Hierarchy is Insufficient**: Many large programmes need 3+ levels of decomposition (System → SubSystem → Component → Requirement). DOORS allows nested modules, but each level is expensive (a nested module is itself a row in the parent module's table), making deep hierarchies unwieldy.

2. **Attribute Schema Lock-in**: Once a DOORS project is deployed with a schema (10 attributes defined), changing the schema is expensive. Adding a new attribute requires DXL scripting or manual migration. Teams often freeze the schema early and accumulate workarounds (using custom fields as catch-all storage, e.g., a "Notes" field that contains structured data).

3. **Binary Serialisation of Modules**: Modules are stored in proprietary `.rmd` files (DOORS Requirement Module format), which are binary-encoded. Humans cannot read `.rmd` files without DOORS; version control systems cannot meaningfully diff them; integration with external tools requires ReqIF export (which loses data).

### The DXL Customisation Burden

DOORS extensibility is via DXL (DOORS eXtension Language), a proprietary scripting language with C-like syntax. Teams use DXL to:
- Integrate DOORS with build systems (triggering DOORS queries when code is compiled, updating requirement status based on test results)
- Implement custom workflows (e.g., "when a requirement is marked Reviewed, automatically send email to stakeholders")
- Validate requirements (e.g., "every requirement must have at least one link to a test case")
- Transform data (e.g., "export requirements from Module X in a format our external tool understands")

Over decades, large DOORS deployments accumulate 1M+ lines of DXL code [15]. This code becomes a liability:
- **Brittle**: DXL has few testing frameworks; custom scripts are often monolithic and fragile.
- **Difficult to Maintain**: When the original author leaves, maintaining DXL code is painful.
- **Lock-in**: All that DXL investment makes switching to another tool economically infeasible. Why spend months rewriting DXL if you can keep using DOORS?

### Rich-Text Legacy and Import Pain

DOORS Classic allowed requirements to be marked as "rich text" (HTML-formatted). The requirement text could contain embedded formatting (bold, italics, lists, links). While useful for presentation, rich-text requirements create a nightmare when exporting to other tools:

- **ReqIF Export**: When exporting to ReqIF, rich-text content must be converted to plain text or XML. The conversion is lossy: many HTML tags are not supported by ReqIF, resulting in data loss [19].
- **Integration with Source Code**: Rich-text content cannot be easily linked to source code (which is plain text). Teams resort to workarounds (extracting plain-text summaries, maintaining separate mapping documents).

### The DOORS Next Migration Disaster

IBM developed DOORS Next (web-based, on the Jazz platform) starting in 2011, intending to modernize DOORS while maintaining compatibility. The promise was: "upgrade to DOORS Next and keep your existing workflows." The reality has been far messier [15][16]:

1. **DXL Scripts Cannot Migrate**: The Jazz platform uses Java, not DXL. There is no automated conversion path. Teams must manually rewrite DXL scripts as Java code. For a 1M-line DOORS codebase, this is not a weekend project; some teams have decided it's cheaper to stick with DOORS Classic [15].

2. **Views Don't Migrate**: Custom views (saved queries, filters) are not compatible between DOORS Classic and DOORS Next. Teams must manually recreate them in DOORS Next [16].

3. **Baselines and History Lost**: DOORS Classic's baseline mechanism doesn't map cleanly to DOORS Next's configuration model. Migration tools either drop baselines or force teams to recreate them manually. Module history (a commit-log-like record of changes to a module) is often lost [16].

4. **New Concepts Require Retraining**: DOORS Next introduces "artifact types", "components", and "configurations" — concepts that don't exist in DOORS Classic. Teams must learn a new data model [16].

5. **Performance and Reliability Issues**: Early DOORS Next releases had performance problems (slow queries, timeouts) and reliability issues (missing data after migration). IBM has since fixed many of these, but the experience soured customers' appetite for the upgrade [16].

As a result, many DOORS Classic customers have decided to stick with DOORS Classic rather than migrate to DOORS Next. This is a rare situation in software: the "legacy" system is more stable and feature-complete than the "next-generation" replacement. IBM now supports both products indefinitely, but the migration path that was supposed to be clear is now a cautionary tale [16].

### Vendor Lock-in and Switching Costs

DOORS lock-in operates at multiple levels:

1. **Binary Data Format**: Requirements are locked in `.rmd` format. Exporting to other tools via ReqIF is lossy. Teams cannot easily read or parse their own requirements without DOORS.

2. **DXL Investment**: 1M lines of DXL code represents years of engineering effort. Rewriting that code for another tool is economically prohibitive.

3. **Licence Cost**: DOORS pricing is not public, but per-seat licensing (typical in the IBM enterprise suite) is expensive. A team of 10 engineers + 5 QA + 5 programme managers paying $5,000-$10,000 per seat per year (estimated, not confirmed) faces a $500K+ annual bill. Switching to an open-source tool or a cheaper SaaS alternative is attractive but requires absorbing the migration cost and DXL rewrite cost.

4. **Organisational Inertia**: Large programmes have been built around DOORS processes. Changing tools requires retraining, process redesign, and risk (will the new tool work? what if we lose requirements in the migration?). The incumbent advantage is strong.

### Summary: What Makes DOORS a Cautionary Tale

DOORS is not a bad tool; it solved real problems in the 1990s-2000s. The caution is against specific design choices:

1. **Relational Database Centralisation**: DOORS bet on a centralised, proprietary database. This provides powerful search capabilities but creates lock-in. A filesystem-first, Git-native approach (sphinx-needs, Doorstop) trades away some query flexibility but gains portability.

2. **Binary Serialisation**: DOORS stored modules in proprietary binary format. This makes the data inaccessible without DOORS and impossible to version-control meaningfully. Plaintext storage (markdown, YAML, RST) is more open.

3. **Extensibility via Proprietary DSL (DXL)**: DOORS extensibility required learning DXL. The Assured bundle should avoid proprietary scripting languages; instead, leverage Python (a general-purpose language teams already know) or REST APIs.

4. **Complexity Through Configuration**: DOORS' module-and-attribute model is expressive but requires deep schema design upfront. Teams often face a choice: keep the schema simple (sacrificing expressiveness) or design a complex schema (sacrificing usability). The Assured bundle should favour simplicity by default and leave complex customisation to extensions.

5. **Migration Trap**: DOORS Next demonstrates the risk of forcing users onto a migration path. The Assured bundle should be designed to be open: if a team wants to migrate to another tool, they should be able to export all their data in a standard format (ReqIF, JSON, etc.) and switch with minimal data loss.

---

## Section 6: Cross-Tool Observations

Several patterns emerge when examining the landscape:

**Pattern 1: Filesystem-First vs. Database-First is the Foundational Trade-off.**
Open-source tools (sphinx-needs, Doorstop, strictdoc) store requirements as files in Git. Commercial tools (DOORS, Polarion, Jama) store them in a centralised database (on-premise or SaaS). Filesystem-first tools sacrifice some query flexibility but gain portability, auditability (Git history is the audit trail), and integration with development workflows (requirements live alongside code in the same repo). Database-first tools provide powerful search and querying but create lock-in and centralised operational cost (database administration, licensing, user provisioning).

**Pattern 2: Identifier Stability is Foundational.**
All serious tools (open-source and commercial) maintain stable, unique identifiers for requirements. The debate is over *how* identifiers are assigned: auto-increment (DOORS, Polarion, Jama), user-declared with validation (strictdoc, Doorstop), or prefix + auto-increment (sphinx-needs). The Assured bundle should adopt auto-increment-with-namespace (our approach: REQ-feature-num, DES-feature-num) because it allows teams to see the requirement type and feature context at a glance.

**Pattern 3: Link Validation is Critical but Expensive.**
All tools validate links (ensuring link targets exist), but the timing differs: sphinx-needs and Doorstop validate at build/command-line time (static analysis); DOORS and Polarion validate in real-time via the database (transactional consistency). Static validation is lower-cost and sufficient for open-source workflows; real-time validation is stronger but requires database infrastructure.

**Pattern 4: Code-to-Spec Linking is Solved Differently Across Tools.**
- sphinx-needs: plugin-based, teams write custom code to parse annotations
- Doorstop: external scripting, YAML metadata stores code references
- strictdoc: source-code parser (language-agnostic, no AST parsing)
- DOORS: expensive DXL customisation
- Commercial tools: IDE plugins + annotation parsing

The Assured bundle's annotation-driven approach (comments in code like `# implements: DES-005`) is aligned with strictdoc's philosophy and is simpler than DOORS' DXL burden.

**Pattern 5: Extensibility Matters, but Simplicity Matters More.**
sphinx-needs and DOORS are both highly extensible, but sphinx-needs' extension via Python plugins (leveraging a general-purpose language) is more approachable than DOORS' DXL (a proprietary language). Teams value tools that work well out-of-the-box without needing customisation. The Assured bundle should have sensible defaults and make extensions straightforward (Python, REST API) rather than requiring a proprietary language.

**Pattern 6: Web UI is a Necessity for Teams with Non-Technical Stakeholders.**
Doorstop (command-line only) has seen limited adoption outside embedded systems. strictdoc's web UI and Polarion's LiveDocs are valued by teams with architects, product managers, and safety officers who need to read and approve requirements without using Git. The Assured bundle is designed for agent-driven teams (where agents manage the text), so a web UI is not required initially, but a read-only view (generated as HTML or served dynamically) would reduce friction for humans needing to review specifications.

**Pattern 7: All Tools Eventually Face a Scaling Wall.**
sphinx-needs hits scaling limits above 500 pages (in a single Sphinx project). Doorstop and strictdoc haven't been stress-tested at Sphinx scale. DOORS and Polarion claim to scale to 100M+ items but don't publish detailed benchmarks. In all cases, teams working with 10K+ requirements eventually face scaling choices: modular projects (sphinx-needs), distributed databases (commercial tools), or architecture redesign. The Assured bundle should support modular decomposition (programs / sub-programs / modules) from the start so that scaling doesn't require a redesign.

---

## Section 7: Counter-Arguments and Category-Level Criticism

Independent of tool-specific criticism, the practitioner community and academic literature identify systemic problems with requirements-management tooling as a category:

**Critique 1: Requirements Rot and Maintenance Burden.**
Requirements are living artefacts; they change as the system evolves. A common failure mode is "requirements rot": specifications become outdated, obsolete, or inconsistent with the actual implementation [27]. This happens because maintaining requirements is expensive: every code change should trigger a review of linked requirements, but teams often deprioritise this work. The result is a traceability matrix that lags reality. Studies suggest 71% of software projects fail at least partially due to poor requirements [28].

The problem is not tool-specific; tools do not prevent requirements rot. Even DOORS or Polarion cannot force a team to keep specifications up-to-date if the team deprioritises maintenance. Requirements rot is a process and culture problem, not a tool problem.

**Critique 2: The Traceability Matrix Becomes the Work.**
A related critique: when requirements-management tooling is deployed, the overhead of maintaining traceability (updating links, filling in attributes, running queries) can exceed the overhead of writing code [29]. Teams report that the matrix becomes the primary deliverable ("we must produce a traceability matrix") rather than a by-product of good engineering ("the matrix documents what we already built"). In pathological cases, teams maintain two parallel systems: the real design (in code and notebooks) and a shadow requirements document (in DOORS or Excel) created to satisfy process audits.

This critique suggests that requirements tools are often oversold: they promise to reduce engineering overhead but, in practice, add overhead by introducing a new artefact to maintain.

**Critique 3: ALM as Compliance Theatre.**
In regulated industries, requirements tools are deployed primarily to satisfy certification authorities (FAA for aerospace, NHTSA for automotive, FDA for medical devices). The tool's real value is not to improve engineering but to generate audit artefacts (traceability matrices, change logs, signed-off specifications) that authorities can inspect [30]. This is "compliance theatre": the tool's primary output is documentation for auditors, not engineering insights. As a result, teams optimise the tool's usage for audit visibility rather than for engineering effectiveness. Teams create requirements that are audit-friendly (formally structured, completely linked) but not necessarily technically sound. The result is a traceability matrix that is 100% complete by the tool's metrics but provides no protection against real bugs (undetected requirements, missed test cases, architectural flaws).

**Critique 4: Conway's Law Applied to Requirements.**
Conway's Law states that systems designed by an organisation are copies of the organisation's communication structures [31]. Applied to requirements: the structure of a requirements document often mirrors the org chart (requirements are organised by team, not by feature) [31]. This is suboptimal: users care about feature-level traceability (e.g., "when we add this feature, what else breaks?"), not team-level organisation (e.g., "requirements owned by Team A vs. Team B"). Requirements tools often bake in org-chart structure (project hierarchies, team assignments, approval workflows) at the database schema level, making it hard to reorganise requirements by feature without data migration. This rigidity is another form of lock-in.

**Critique 5: Loss of Narrative in Formal Specifications.**
When requirements are stored in a relational database (structured attributes, no rich prose), they lose narrative context. A requirement like `REQ-auth-001: The system shall validate user tokens` is formally correct but lacks context: *why* is token validation important? What attack does it defend against? What assumptions does it make about the token format? In a well-written specification document (like those in sphinx-needs or strictdoc), context is preserved in prose. In a relational database, context is lost, and the requirement becomes a checkbox in a matrix [32].

**Critique 6: The Requirement Cascade Problem.**
In regulated industries, high-level system requirements are decomposed into sub-requirements, design specifications, test cases, and code. This decomposition is often top-down: system engineers write high-level requirements, then designers decompose them into lower-level requirements. The problem: when a high-level requirement changes, the entire cascade of sub-requirements may need revision, but tools often do not provide impact analysis. The human process of re-decomposing the tree is expensive and error-prone. Some commercial tools (Polarion, Jama) claim to provide impact analysis, but in practice, the analysis is limited to explicit traceability links; it does not reason about semantic dependencies [32].

---

## Section 8: Implications for Our Framework

### 8.1 Patterns to Adopt

1. **Adopt sphinx-needs' Declarative Need-Type Schema.**
Define requirement types (REQ, DES, TEST, CODE) as configuration: for each type, specify allowed field names, field types (string, list, enum), link rules (which types can link to which), and rendering hints. This is cleaner than a generic "attributes table" (DOORS style) and allows early type validation.

*Implementation*: Our METHODS.md already defines the spec-type decomposition (REQ / DES / TEST / CODE); we should formalise this as a configuration schema similar to sphinx-needs' `needs_types` parameter. Example:

```yaml
spec_types:
  REQ:
    fields:
      - id (required, unique)
      - title (required)
      - statement (required)
      - rationale (optional)
      - acceptance_criteria (optional)
    links_to: [DES, TEST]
  DES:
    fields:
      - id (required, unique)
      - title (required)
      - description (required)
      - design_pattern (optional)
    links_to: [TEST, CODE]
    links_from: [REQ]
```

2. **Adopt Markdown + YAML Frontmatter as Storage Format.**
Avoid binary formats and proprietary databases. Store each specification item as a markdown file (or section) with YAML frontmatter for metadata (ID, type, links). This ensures requirements are human-readable, Git-trackable, and portable. Example:

```yaml
---
id: REQ-cross-library-001
type: requirement
title: Support cross-library queries
links:
  - DES-cross-library-002
  - DES-cross-library-003
---

# Cross-Library Query Support

The knowledge-base librarian SHALL support querying across multiple corporate asset libraries simultaneously, returning deduplicated findings ranked by relevance to the query.

## Rationale

Teams managing multiple projects often curate separate knowledge-base libraries. A researcher should be able to search across all relevant libraries without manual aggregation.
```

3. **Adopt Static Link Validation at Build-Time (Not Run-Time).**
Like sphinx-needs and Doorstop, validate link integrity via post-processing (e.g., `kb-rebuild-indexes` command), not real-time database constraints. This reduces operational complexity and allows link validation to be local (runs in CI/CD, not on a central server). No database is needed.

4. **Adopt Identifier Stability with Namespaced Prefixes.**
Use the naming scheme from METHODS.md: `<program>.<sub-program>.<module>.<type>-<num>`. For projects without declared decomposition, default to `P1.SP1.M1.REQ-001`. This makes the type and context visible at a glance and allows sorting/filtering by prefix. Identifiers must be stable across renames and must be validated for uniqueness.

5. **Adopt Bidirectional Link Representation via Index, Not Database Transactions.**
Store forward links in the source artefact (DES references its REQ), then regenerate backward-link indices (which REQs are covered by DES X?) at build-time. This matches sphinx-needs' philosophy: no database, no transaction overhead, indexes are derived from source truth. The `library/_ids.md` registry (METHODS.md) is the manifestation of this pattern.

6. **Adopt Annotation-Driven Code-to-Spec Linking.**
Rather than IDE plugins or proprietary DXL, use code comments as the source of truth: `# implements: DES-auth-005, REQ-auth-003`. The `kb-codeindex` skill (METHODS.md) parses these annotations and builds an index. This is simpler than DOORS' DXL and more portable than Jama's IDE plugin model.

7. **Adopt Modular Decomposition as a First-Class Concept.**
Unlike DOORS (which has a rigid module hierarchy), and unlike sphinx-needs (which assumes a flat need space), declare decomposition explicitly: a project defines its programs, sub-programs, and modules upfront, and all IDs are scoped to this hierarchy. This allows large projects to scale by bounding the scope of work (an agent working on module M3 only needs to consider requirements/code in M3's scope, not the whole system).

### 8.2 Patterns to Avoid

1. **Do NOT Adopt DOORS' Module-and-Attribute Relational Model.**
Avoid a database schema where requirements are rows and attributes are columns. This design optimises for a relational database (where column-based indexing is efficient) but creates lock-in and makes plain-text export/import difficult. Instead, store each requirement as a self-contained unit (file or section) with its own metadata (YAML frontmatter).

2. **Do NOT Adopt Proprietary Binary Formats or Serialisation.**
Avoid DOORS' `.rmd` format, Polarion's workspace format, or Jama's cloud-only storage. Plaintext (markdown + YAML) is portable, Git-friendly, and human-readable. If the tool ever disappears, the data is still accessible.

3. **Do NOT Adopt Proprietary Extensibility Languages (like DXL).**
Avoid requiring teams to learn DXL, Polarion Query Language, or custom DSLs to extend the framework. Use Python (widely known, rich ecosystem) or REST APIs (standard, language-agnostic). If the framework needs to support custom validators or computed fields, expose a Python plugin interface, not a proprietary scripting language.

4. **Do NOT Require Centralised Database Administration.**
Avoid DOORS' and Polarion's centralised database model, which requires a database administrator, licensing, user provisioning, backup/restore procedures, and uptime guarantees. A filesystem-first framework (markdown + Git) moves database administration burden to existing infrastructure (teams already manage Git servers) and allows decentralised use (a team can clone the repo and work offline).

5. **Do NOT Embed Organisational Structure into the Data Model.**
Avoid modelling team ownership, approval chains, or project hierarchies into the core spec schema. These are process concerns, not spec concerns. Teams' org charts change; specs should not need restructuring when a team is reorganised. Instead, allow organisational metadata (owner, approval status) as optional fields and leave process enforcement to validators and workflows.

6. **Do NOT Create a Complex Migration Path.**
Avoid DOORS Next's fate: designing a "next-generation" tool that requires extensive migration (rewriting customisations, losing data, retraining users). Instead, design the framework to be open: support export to standard formats (ReqIF, JSON, CSV) so teams can migrate to other tools if needed. Avoid formats and designs that lock teams in.

7. **Do NOT Assume Web UI is Necessary for the Core Framework.**
Avoid over-engineering a web UI into the core framework (like Polarion, Jama). A command-line tool + markdown files + generated HTML output (from markdown) is sufficient for agent-driven workflows. Web UI for human review and editing can be a separate layer (an optional plugin or a wrapper around the markdown files).

### 8.3 Patterns to Leave Layered

1. **Collaborative Editing and Review Workflows.**
The core framework should enforce link integrity and maintain traceability. Collaborative editing (multiple humans reviewing and proposing changes to specs), approval workflows (spec changes require sign-off), and version control workflows (branching, merging, conflict resolution) should be built on top of the core framework, using Git for the underlying mechanism. These are process concerns, not core data-model concerns.

2. **Web UI and API Server.**
A read-only web UI for browsing specs (generated from markdown) and a REST API for querying the spec index could be built as separate layers on top of the core framework. The core framework produces markdown files and JSON indices; a separate web server serves them and provides a UI. This allows teams to choose: run just the command-line tool (for agents and Git workflows), or add the web server (for human browsing).

3. **IDE Plugins and Code-Level Integration.**
IDE integrations (e.g., Visual Studio plugin to jump from code to spec) are valuable but should be extensions, not core. The core framework is annotation-driven (comments in code like `# implements: DES-005`). IDE plugins can parse these annotations and provide navigation. This keeps the core framework lightweight and allows different IDE plugins for different editors.

4. **Test Execution Tracking and Coverage Analysis.**
Linking requirements to test cases is core. But tracking which test-cases have been executed, which have passed/failed, and coverage analytics should be external layers. The core framework records "TEST-auth-001 is covered by code annotation in auth.py:line42"; a separate test-execution system tracks "TEST-auth-001 ran on 2024-04-26 and passed". The two systems integrate via the ID link, but the core framework doesn't own test execution.

5. **Change Management and Approval Workflows.**
Recording that "REQ-auth-001 was changed on 2024-04-20 by Alice, reviewed by Bob, and approved by Carol" is process metadata, not core spec data. The core framework can include optional fields for this (change_date, reviewer, approver), but enforcement (blocking unapproved changes) should be in validators, not the core model.

6. **ReqIF Import/Export and Tool Interoperability.**
ReqIF is a standard format for exchanging requirements between tools. Supporting ReqIF export (so teams can export to DOORS, Polarion, etc.) is valuable but should be a plugin, not core. The core framework stores specs as markdown; a separate tool converts to/from ReqIF. This keeps the core framework simple and allows iterating on the export format without changing the core data model.

7. **Multi-Project Aggregation and Cross-Project Queries.**
For programmes with dozens of sub-projects, it would be valuable to query across all specs (e.g., "find all REQs mentioning authentication"). This is a higher-level concern (cross-project librarian queries) and should be built on top of the core framework, not baked in. The core framework manages specs for one project; a separate layer aggregates across projects.

---

## Section 9: Bibliography

[1] useblocks. (2024). Sphinx-Needs 8.0.0 Documentation. https://sphinx-needs.readthedocs.io/en/latest/
   Source-type tag: [open-source-readme]
   Credibility note: Official project documentation, maintained by useblocks (the active maintainer). Current as of April 2024. High authority on sphinx-needs design and features.

[2] Jace Browning, et al. (2024). Doorstop: Text-Based Requirements Management Using Version Control. https://doorstop.readthedocs.io/en/latest/
   Source-type tag: [open-source-readme]
   Credibility note: Official project documentation. Doorstop is actively maintained with regular releases. High authority on Doorstop architecture.

[3] Stanislav Pankevich. (2024). StrictDoc User Guide. https://strictdoc.readthedocs.io/en/stable/stable/docs/strictdoc_01_user_guide.html
   Source-type tag: [open-source-readme]
   Credibility note: Official project documentation for strictdoc. Smaller community than sphinx-needs, but active development. Current as of stable release.

[4] Object Management Group. (2016). About the Requirements Interchange Format Specification Version 1.2. https://www.omg.org/spec/ReqIF/1.2/About-ReqIF
   Source-type tag: [open-source-readme]
   Credibility note: OMG specification document. ReqIF is an ISO standard (ISO/IEC/IEEE 42010). Definitive source for ReqIF schema and semantics.

[5] IBM. (2024). IBM Engineering Requirements Management DOORS. https://www.ibm.com/docs/en/engineering-lifecycle-management-suite/doors/9.7.0
   Source-type tag: [vendor-doc]
   Credibility note: Official vendor documentation from IBM. Covers DOORS 9.7.0 (classic version). Current as of 2024.

[6] innotec GmbH. (2024). IEC 61508 Firmware Compliance with Sphinx. https://innotecsafety.com/iec-61508-firmware-compliance-with-sphinx
   Source-type tag: [practitioner-blog]
   Credibility note: Safety-critical systems consulting firm. Details practical use of Sphinx-based tooling (related to sphinx-needs) for IEC 61508 (functional safety). Authoritative on regulated-industry usage.

[7] Justin Searls. (2024). DO-178C Certification Tools for Safety-Critical Avionics and Beyond. https://www.lynx.com/challenges/safety-certification
   Source-type tag: [practitioner-blog]
   Credibility note: Blog post from avionics/safety-critical domain. Discusses tools and standards for DO-178B/C compliance. Relevant for understanding how sphinx-needs and similar tools are used in regulated contexts.

[8] Jace Browning. (2013). Doorstop: Text-Based Requirements Management Using Version Control. JSEA Paper, https://www.scirp.org/journal/PaperInformation.aspx?PaperID=44268
   Source-type tag: [conference-paper]
   Credibility note: Peer-reviewed paper introducing Doorstop. Foundational reference for Doorstop design and use cases. Cited in academic literature on requirements management.

[9] Space ROS. (2024). Doorstop. https://space-ros.github.io/docs/rolling/Related-Projects/Doorstop.html
   Source-type tag: [open-source-readme]
   Credibility note: Space ROS uses Doorstop for requirements management in robotics (safety-critical). Demonstrates real-world adoption in regulated domain (space/robotics).

[10] RTEMS. (2026). Tooling — RTEMS Software Engineering. https://docs.rtems.org/docs/main/eng/req/tooling.html
    Source-type tag: [open-source-readme]
    Credibility note: RTEMS (real-time OS, open-source, used in aerospace/satellite systems) documents use of Doorstop. Real-world example of Doorstop in safety-critical embedded systems.

[11] Jama Software. (2024). What Is IBM DOORS Software? Features, Limitations, and Why Teams Are Switching. https://www.jamasoftware.com/blog/ibm-doors-software/
    Source-type tag: [practitioner-blog]
    Credibility note: Jama Software (competing vendor) provides critical analysis of DOORS. While vendor-motivated, the criticisms align with independent user reviews. Good synthesis of known DOORS limitations.

[12] Modern Requirements. (2024). IBM Doors: Is it the right time to transition from IBM DOORS? https://www.modernrequirements.com/blogs/transition-from-ibm-doors/
    Source-type tag: [practitioner-blog]
    Credibility note: Requirements consulting firm. Discusses migration challenges and lock-in risks. Independent analysis not from a competing tool vendor.

[13] Visure Solutions. (2024). IBM DOORS Disadvantages: Is it slowing your team down? https://visuresolutions.com/ibm-doors-guide/disadvantages/
    Source-type tag: [practitioner-blog]
    Credibility note: Requirements tools consultancy. Detailed analysis of DOORS disadvantages, including data loss, complexity, and lock-in. Competing vendor but provides concrete examples.

[14] Jama Software. (2024). Why Migration Efforts from IBM Rational DOORS to DOORS NG Are Failing — And an Alternative Path. https://www.jamasoftware.com/blog/why-migration-efforts-from-ibm-rational-doors-to-doors-ng-are-failing-and-an-alternative-path/
    Source-type tag: [practitioner-blog]
    Credibility note: Jama (competing vendor) provides detailed analysis of DOORS Classic to DOORS Next migration failures. The criticisms are concrete (DXL migration, view incompatibility, data loss) and align with independent user reports.

[15] MGTechSoft. (2026). Migrating from DOORS to DOORS Next: A Complete Guide for Modern Engineering Teams. https://mgtechsoft.com/blog/migrating-from-doors-to-doors-next-a-complete-guide-for-modern-engineering-teams/
    Source-type tag: [practitioner-blog]
    Credibility note: Independent migration consultancy. Discusses practical challenges of DOORS-to-DOORS-Next migration, including DXL rewriting, view migration, and performance issues.

[16] Softacus. (2024). DOORS Classic to DOORS Next Migration Challenges and Solution. https://softacus.com/blog/doors-classic-to-doors-next-migration-challenges-and-solution
    Source-type tag: [practitioner-blog]
    Credibility note: Independent migration consulting firm. Detailed technical discussion of migration pain points: DXL incompatibility, view migration failures, performance degradation.

[17] PeerSpot. (2024). IBM DOORS: Pros and Cons 2026. https://www.peerspot.com/products/ibm-doors-pros-and-cons
    Source-type tag: [review-site]
    Credibility note: User review site (similar to G2, TrustRadius). Aggregate of verified user reviews. Mixed ratings with detailed negative feedback on UI, usability, and lock-in.

[18] Capterra. (2024). IBM Engineering Requirements Management DOORS Next Reviews 2026. https://www.capterra.com/p/238454/IBM-Engineering-Requirements-Management-DOORS-Next/reviews/
    Source-type tag: [g2-review]
    Credibility note: Capterra review site (part of Gartner ecosystem). Verified user reviews. Covers both DOORS Classic and DOORS Next. Criticisms align with consultant reports.

[19] Visure Solutions. (2024). How to Exchange Requirements Between Tools via ReqIF. https://visuresolutions.com/alm-guide/exchange-requirements-via-reqif/
    Source-type tag: [practitioner-blog]
    Credibility note: Requirements tools consultancy. Discusses ReqIF data-loss issues, round-trip failures, and attribute mapping challenges. Practical guide based on consulting experience.

[20] Siemens. (2024). Polarion ALM Factsheet. https://polarion.plm.automation.siemens.com/hubfs/Docs/Fact-sheets/Polarion_ALM_Fact-Sheet.pdf
    Source-type tag: [vendor-doc]
    Credibility note: Official vendor documentation from Siemens. Covers Polarion ALM features and architecture.

[21] G2. (2024). Polarion Reviews 2026. https://www.g2.com/products/polarion/reviews
    Source-type tag: [g2-review]
    Credibility note: G2 review site (Gartner-affiliated). Verified user reviews. Users praise features but note configuration complexity and steeper learning curve.

[22] Jama Software. (2026). Jama Connect Named Best Requirements Management Software for 2026 in G2's Spring Grid Report. https://www.jamasoftware.com/blog/jama-connect-named-best-requirements-management-software-for-2026-in-g2-spring-grid-report/
    Source-type tag: [vendor-whitepaper]
    Credibility note: Jama vendor blog. Cites G2 Spring 2026 grid report (independent analyst review). Jama ranks #1 in user satisfaction (97 score) for requirements management tools.

[23] G2. (2024). Jama Connect Reviews 2026. https://www.g2.com/products/jama-connect-for-requirements-management/reviews
    Source-type tag: [g2-review]
    Credibility note: G2 verified user reviews for Jama Connect. Highest user satisfaction scores among commercial requirements tools. 95% of users rate 4-5 stars. Praised for ease of use, strong versioning, collaborative features.

[24] Dassault Systèmes. (2024). Reqtify | CATIA. https://www.3ds.com/products/catia/reqtify
    Source-type tag: [vendor-doc]
    Credibility note: Official vendor documentation. Covers Reqtify's connector-based traceability model and support for 100+ external sources.

[25] Perforce. (2024). Helix ALM. https://www.perforce.com/products/helix-alm
    Source-type tag: [vendor-doc]
    Credibility note: Official vendor documentation for Helix ALM (formerly TestTrack). Full-lifecycle ALM platform.

[26] PTC. (2024). codeBeamer ALM Solution. https://www.ptc.com/en/products/codebeamer
    Source-type tag: [vendor-doc]
    Credibility note: Official vendor documentation. codeBeamer (acquired by PTC, formerly Intland Software) provides integrated ALM with VCS integration and gapless traceability.

[27] ScienceDirect. (2022). Identification and Measurement of Requirements Technical Debt in Software Development: A Systematic Literature Review. https://www.sciencedirect.com/science/article/pii/S0164121222001650
    Source-type tag: [conference-paper]
    Credibility note: Peer-reviewed systematic literature review on requirements technical debt. Defines "requirements rot" as degradation of specification quality over time.

[28] Software Testing Help. (2024). Top 20+ Best Requirements Management Tools. https://www.softwaretestinghelp.com/requirements-management-tools/
    Source-type tag: [practitioner-blog]
    Credibility note: Software testing and QA practitioner resource. Cites research statistic: 71% of software projects fail due to poor requirements management.

[29] ProjectManager. (2024). How to Make a Requirements Traceability Matrix. https://www.projectmanager.com/blog/requirements-traceability-matrix
    Source-type tag: [practitioner-blog]
    Credibility note: Project management resource. Discusses "too much traceability" problem: maintenance burden can exceed engineering value if matrix becomes the primary deliverable.

[30] Cypago. (2024). The Hidden Cost of Compliance Theater. https://cypago.com/the-hidden-cost-of-compliance-theater/
    Source-type tag: [practitioner-blog]
    Credibility note: Compliance consulting firm. Discusses "compliance theatre": gap between checklist compliance and actual security/safety. Applies to requirements tools in regulated industries.

[31] Martin Fowler. (2024). Conway's Law. https://martinfowler.com/bliki/ConwaysLaw.html
    Source-type tag: [practitioner-blog]
    Credibility note: Well-regarded software architecture blog. Explains Conway's Law and applies it to software design and organisation. Authoritative source on the principle.

[32] CodeScene. (2024). Requirements on Technical Debt: Dare to Specify Them! https://codescene.com/blog/requirements-on-technical-debt-dare-to-specify-them
    Source-type tag: [practitioner-blog]
    Credibility note: Software engineering consultancy. Discusses loss of narrative context when requirements are formalised into database rows, and the importance of prose specifications.

