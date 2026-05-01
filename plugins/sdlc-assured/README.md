# sdlc-assured

Regulated-industry SDLC bundle (Method 2) for projects targeting DO-178C, IEC 62304, ISO 26262, IEC 61508, or FDA 21 CFR Part 820. Layers on top of `sdlc-programme` (Phase D) with positional namespace IDs, bidirectional traceability, DDD-style decomposition with visibility rules, KB extension to code, and standard-specific traceability exports.

## What this bundle adds over Programme

- **Identifier system**: positional namespace IDs (`P1.SP2.M3.REQ-007`) for decomposed projects; flat IDs preserved for non-decomposed projects.
- **ID registry**: `library/_ids.md` auto-generated, tracking every ID, source, and links. Validators enforce uniqueness and reference resolution.
- **Bidirectional traceability**: 4 mandatory validators (forward link integrity, backward coverage, index regenerability, annotation format) + 1 optional (change-impact-gate).
- **Decomposition**: declarative `programs.yaml` with DDD bounded contexts, visibility rules, hexagonal-architecture opt-in.
- **KB extension to code**: inline `# implements: <ID>` annotations parsed into `library/_code-index.md` (shelf-index-shaped).
- **Render and export**: module-scoped traceability render, module-dependency-graph (markdown edge-list), 4 standard-specific export formats.

## Constitution

Articles 15-17 overlay the universal articles 1-11 and Programme articles 12-14:

- Article 15: Identifier and traceability integrity
- Article 16: Decomposition discipline
- Article 17: KB-for-code annotation completeness

See `CONSTITUTION.md`.

## Skills

| Skill | Purpose |
|-------|---------|
| `commission-assured` | Install Assured bundle into a project; prompt for programs block, granularity, regulatory context |
| `req-add` | Mint a new REQ ID with module assignment |
| `req-link` | Add a satisfies link between artefacts |
| `code-annotate` | Auto-generate `# implements:` boilerplate for a function |
| `module-bound-check` | Run all 5 decomposition validators |
| `kb-codeindex` | Parse annotations into `library/_code-index.md` |
| `change-impact-annotate` | Guide change-impact declaration for IEC 62304 / FDA / ISO 26262 |
| `traceability-render` | Module-scoped human-readable doc with anchor links |

## Out of scope (v0.1.0)

- AST-level code intelligence
- IDE integration
- ALM database
- Industry certification itself (this is substrate, not certification)
- Bidirectional ReqIF sync
- Decomposition suggestion (we declare; we don't suggest)
- Distributed multi-team ID coordination
