# Research Line 3 — ALM / Requirements-Tools Landscape

## Why this matters

We are designing a framework that will mint stable IDs for requirements/design/tests/code, maintain bidirectional links, and produce traceability artefacts on demand. This puts us adjacent to the existing application-lifecycle-management (ALM) and requirements-management (RM) tool landscape: IBM DOORS, Siemens Polarion, Jama Connect, sphinx-needs, and others.

We've named the trap (\"don't become DOORS\") but haven't characterised it concretely. This research line surveys the existing tools so we can:

- Steal proven patterns (especially from sphinx-needs, the closest open-source markdown-native predecessor)
- Avoid known failure modes (DOORS bloat, Polarion lock-in, ReqIF round-trip pain)
- Calibrate scope (what's table-stakes for a requirements tool vs what's enterprise-only)

This research is *calibration*, not direction-setting. The Method 1 + Method 2 scope is already drafted; this line tells us which scope decisions to tighten or relax based on what existing tools have learned.

## How to use this prompt

1. Open Claude Desktop with extended research mode enabled.
2. **Paste the contents of `research/sdlc-bundles/METHODS.md` first**, as a system-context message at the start of the conversation. This tells the researcher what the framework is, what Method 1 and Method 2 are, and what's already built. Without this context the research output will be too generic to be useful.
3. Then copy the entire content of the **`## Prompt`** section below as the next message.
4. Allow the research to complete. Expect ~30-60 minutes for a thorough output.
5. Save the output to `research/sdlc-bundles/outputs/03-alm-tools-landscape/output-1.md`.
6. If the output is thin or off-target, save it as `output-1-thin.md` and run a sharpened follow-up.

---

## Prompt

> **Required context**: this prompt assumes you have just read `research/sdlc-bundles/METHODS.md` describing the framework, Method 1 (Programme bundle), and Method 2 (Assured bundle). If that document was not pasted into this conversation, request it before continuing.

You are conducting deep research on the application-lifecycle-management and requirements-management tool landscape, with a specific objective: extract concrete design lessons (both positive and negative) for the **Assured bundle** described in METHODS.md Section 4. The Assured bundle supports requirements-to-code traceability via stable identifiers, KB-style retrieval, and validator-enforced link integrity, on top of the markdown-driven, filesystem-first, agent-orchestrated framework described in METHODS.md.

It is intentionally NOT a relational ALM database; it stores specifications as markdown files with YAML headers, indexed by a content-hashed registry, and retrieved by a research librarian agent (see METHODS.md Section 1 for the existing knowledge-base substrate). Bidirectional links are validated by post-check tooling (similar to a static type-checker), not maintained by a database transaction.

The decision your research informs is: which existing tools' design patterns should the Assured bundle adopt, and which should it explicitly avoid?

### Scope of research

Cover the following tools and standards. For each, answer the listed questions.

**Open-source / community:**
- **sphinx-needs** (Sphinx extension for need objects with status/links/options)
- **Doorstop** (file-based requirements management in Python, plain-text storage)
- **strictdoc** (open-source technical writing tool with traceability)
- **OpenAPS / sphinx-needs-derived patterns** in safety-critical open-source projects
- **ReqIF** (Requirements Interchange Format — the OMG/ISO standard, not a tool)

**Commercial:**
- **IBM DOORS** (classic) and **DOORS Next** (web-based replacement)
- **Siemens Polarion** (ALM platform, requirements + test + change management)
- **Jama Connect** (cloud ALM with focus on regulated industries)
- **Reqtify** (Dassault Systèmes — requirements traceability with strong code-link support)
- **Helix ALM** (Perforce — formerly TestTrack, now full ALM)
- **codebeamer** (Intland Software, now PTC — ALM with cybersecurity focus)

For each tool/standard, answer:

1. **Data model.** What's the core data structure — relational (rows in a database), document (markdown/XML files), graph (linked nodes), proprietary binary? Where does the source of truth live (filesystem, server database, cloud SaaS)?
2. **Identifier scheme.** How are requirements (and other artefacts) identified? Auto-incremented integers, namespaced strings, GUIDs, user-chosen? Are IDs stable across renames/moves?
3. **Link model.** How are bidirectional links represented and maintained — explicit relationship rows, link tables, stored procedures, file-based references with hash check? What happens when a target is deleted or renamed?
4. **Code-to-spec linking.** How does the tool link from a requirement to the code that implements it? Annotation in code (regex-detected), external link table, plug-in to IDE, manual entry?
5. **Versioning and history.** How are version control and change history modelled? Native VCS-friendly (works with Git), proprietary baseline/branch model, snapshot-based?
6. **Extensibility.** Can users add new artefact types, new link types, new validators? Is extension via plug-ins, scripts, or only configuration?
7. **Core value proposition.** When does a team genuinely need this tool — what does it actually buy you that markdown plus Git wouldn't?
8. **Known criticism.** What do practitioners and review sites say goes wrong with this tool? Specific failure modes: DOORS rich-text-import nightmare, Polarion configuration depth, Jama upload limits, sphinx-needs scaling on large projects, ReqIF round-trip data loss.
9. **Pricing tier.** Per-seat, per-server, freemium, free? (Not for our pricing decision — for understanding which tools are within reach for a small open-source project's audience vs which are enterprise-only).

### Output structure

Produce a single document with the following sections.

**Section 1 — Executive summary.** One paragraph per tool/standard summarising its data model, core value prop, and biggest known criticism. Plus a closing paragraph identifying which tool is closest in shape to what we're building, and which tool is the canonical "do not become this" warning. Maximum 800 words.

**Section 2 — Comparison matrix.** Two tables.
- Table A: feature comparison (rows = tools, columns = data model / ID scheme / link model / code-link / VCS support / extensibility).
- Table B: failure-mode comparison (rows = tools, columns = scaling failure / configuration failure / data-loss failure / lock-in failure).

Each cell short and factual with citation indices.

**Section 3 — Per-tool dossier.** One subsection per tool/standard. Each subsection covers questions 1-9 in narrative form with citations. Each subsection ends with a "Lessons for our framework" mini-section listing 2-4 specific design lessons (both positive — patterns to adopt — and negative — patterns to avoid). Each subsection should be 350-650 words.

**Section 4 — sphinx-needs deep dive.** sphinx-needs is the closest existing thing to what we're building (markdown-native, filesystem-first, open-source, with link validation). This subsection goes deeper than the others: how sphinx-needs declares need types, how its dynamic functions work, how it scales, what its known limits are, what its community uses it for. 600-1,000 words.

**Section 5 — DOORS / DOORS Next deep dive.** DOORS is the canonical ALM warning. This subsection characterises *exactly* what makes DOORS a cautionary tale: the data-import friction, the rich-text legacy, the modules-and-attributes data model, the pricing barrier, the lock-in via .rmd file format, the slow web migration. 500-800 words.

**Section 6 — Cross-tool observations.** What patterns are present in *every* serious ALM tool that we'd be missing without conscious effort? What patterns are present in *some* tools and absent in others — and which side of that line should we be on? Are there patterns the open-source tools share that the commercial tools lack (or vice versa)?

**Section 7 — Counter-arguments and known criticism (of the category).** Independent of tool-specific criticism, what does the practitioner community say about *requirements-management tooling as a category*? Common critiques: requirements rot, the matrix becomes the work, ALM as compliance theatre, "the tool that nobody actually opens", Conway's law applied to RM tools (the org chart shapes the requirements). Surface 4-6 such criticisms with citations.

**Section 8 — Implications for our framework.** Three subsections:

- *Patterns to adopt* — specific design patterns from sphinx-needs / Doorstop / strictdoc / DOORS that map cleanly onto a markdown-driven framework. Be concrete: "adopt sphinx-needs' need-type declarative schema (similar to YAML frontmatter)".
- *Patterns to avoid* — specific design patterns from any tool that we should explicitly NOT replicate. Be concrete: "do not adopt DOORS' module-and-attribute model; flat markdown files with stable IDs are our model".
- *Patterns to leave layered* — capabilities that are valuable but should be left to extension/integration rather than baked in (e.g., test-execution tracking, change-management approval flows, IDE-plug-in integration).

This is the deliverable that informs framework design. Maximum 1,000 words.

**Section 9 — Bibliography.** Every cited source per the reference-discipline section.

### Reference discipline

Every factual claim must carry an inline citation in the form `[N]` indexing into a bibliography at the end.

Bibliography entries:

```
[N] <Author/Organisation>. (<Year>). <Title>. <URL>. Accessed <YYYY-MM-DD>.
   Source-type tag: [vendor-doc | vendor-whitepaper | review-site | practitioner-blog | conference-paper | open-source-readme | book | wiki | g2-review | gartner-report]
   Credibility note: <one-line note on authority and any conflict of interest>
```

Source quality requirements specific to this research line:

- For each commercial tool, the **vendor's own documentation** is required as a primary citation but cannot be the only citation for criticism (vendors don't criticise themselves).
- **Independent review sites** (G2, Gartner Peer Insights, TrustRadius, Capterra) are acceptable for user perception but should be cross-checked with practitioner blogs for substance.
- **sphinx-needs** has a public GitHub repo and ReadTheDocs documentation; cite both.
- **Doorstop** and **strictdoc** are open-source; cite their READMEs, documentation, and any peer-reviewed papers about them.
- **ReqIF**: cite the OMG specification document directly; secondary citations from tool vendors describing their ReqIF support are acceptable.
- For the criticism sections, weight peer-reviewed papers and well-regarded practitioner blogs over anonymous review-site comments.
- **Pricing tier**: vendor websites are sufficient. If a vendor doesn't publish prices (DOORS, Polarion typically don't), say "pricing not publicly published; enterprise sales process required" rather than guessing.

CRAAP-style quality assessment in each bibliography credibility note.

### What to avoid

- Do not produce a tutorial on each tool; the deliverable is a *comparative analysis with lessons*, not "how to use sphinx-needs".
- Do not give the commercial tools the benefit of vendor marketing claims. Independent corroboration is required for any positive claim about vendor capability.
- Do not understate the open-source tools just because they have less marketing. sphinx-needs and strictdoc are credible serious tools used in regulated contexts.
- Do not extrapolate where literature is silent. If a tool's failure mode isn't documented, say "no documented failure-mode analysis located" rather than guessing.
- Do not produce a recommendation that says "build your own". Of course we're building our own; the deliverable is *which patterns* to adopt and avoid.

### Length and depth

Target document length: 5,000-9,000 words. Section 4 (sphinx-needs deep dive), Section 5 (DOORS deep dive), and Section 8 (implications) carry the most weight for our purposes; allocate analytical depth there.
