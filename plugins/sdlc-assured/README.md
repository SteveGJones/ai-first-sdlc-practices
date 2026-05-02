# sdlc-assured (v0.2.0 — audit-ready at the tooling layer)

Regulated-industry SDLC bundle (Method 2) for projects targeting DO-178C, IEC 62304, ISO 26262, IEC 61508, or FDA 21 CFR Part 820. Layers on top of `sdlc-programme` (Method 1) with positional namespace IDs, bidirectional traceability, DDD-style decomposition with visibility rules, KB extension to code, typed evidence statuses, and standard-specific traceability exports.

**v0.2.0 status**: audit-ready at the tooling layer. The validators, traceability machinery, evidence model, and exports are auditor-grade and deterministically regenerable. Corpus-policy formalisation and CI integration of the REQ-quality linter are deferred to v0.3.0 — see [Audit-Ready at the Tooling Layer (v0.2.0)](#audit-ready-at-the-tooling-layer-v020) below for what is and is not in scope.

## What this bundle adds over Programme

- **Identifier system**: positional namespace IDs (`P1.SP2.M3.REQ-007`) for decomposed projects; flat IDs preserved for non-decomposed projects.
- **ID registry**: `library/_ids.md` auto-generated, tracking every ID, source, and links. Validators enforce uniqueness and reference resolution.
- **Bidirectional traceability**: 4 mandatory validators (forward link integrity, backward coverage, index regenerability, annotation format) + 1 optional (change-impact-gate). v0.2.0 adds **indirect DES-mediated coverage** — transitive call paths (A → B → C) count as A covering C.
- **Decomposition**: declarative `programmes.yaml` with DDD bounded contexts, visibility rules, hexagonal-architecture opt-in. 5 module-bound validators check visibility, scatter, and anaemic contexts.
- **KB extension to code**: inline `# implements: <ID>` annotations parsed into `library/_code-index.md` (shelf-index-shaped). v0.2.0 adds a **platform-neutral dependency extractor** so non-Python projects participate in coverage analysis.
- **Typed evidence statuses (v0.2.0)**: requirements declare an `Evidence-Status` field — `LINKED`, `MANUAL_EVIDENCE_REQUIRED`, or `CONFIGURATION_ARTIFACT` — replacing untyped boolean traceability with auditable categories.
- **Multi-format evidence model (v0.2.0)**: a single requirement can be satisfied by Python `# implements:` annotations, markdown evidence tables, YAML satisfies-blocks, or satisfies-by-existence (file presence as evidence). All consumed via a unified `EvidenceIndexEntry` API.
- **Render and export**: module-scoped traceability render, module-dependency-graph (markdown edge-list), 4 standard-specific export formats (DO-178C / IEC 62304 / ISO 26262 / FDA DHF).
- **REQ-quality linter (v0.2.0)**: `tools/validation/check-req-quality.py` detects DRIFTER requirements (REQs that open with implementation detail rather than user-visible capability). Advisory by default; `--strict` opt-in for CI.

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

## Getting Started

A complete walkthrough from install to first audit-ready export.

**1. Install and commission**

```bash
/plugin install sdlc-assured@ai-first-sdlc
/sdlc-core:commission --option assured --level production
/sdlc-assured:commission-assured
```

The commission step scaffolds `programmes.yaml` (DDD bounded contexts), `visibility-rules.md` (cross-module reference rules), and base specification templates. It also overlays the Assured constitution articles (15–17) on top of Programme (12–14) and the universal articles (1–11).

**2. Declare your decomposition in `programmes.yaml`**

For each bounded context (DDD module), declare the module path, parent, and visibility rules (public / internal / test-only). For non-decomposed projects, use a single root module — flat IDs (e.g., `REQ-001`) will be minted.

**3. Mint requirements with positional IDs**

```bash
/sdlc-assured:req-add <module> <feature> "System SHALL authenticate users via OAuth 2.0"
# → mints e.g. P1.REQ-001 (positional) or REQ-001 (flat)
```

**4. Link artefacts (bidirectional traceability)**

```bash
/sdlc-assured:req-link P1.REQ-001 design-spec.md "Section 3.2 OAuth flow"
/sdlc-assured:req-link P1.REQ-001 test-spec.md "Test 4.1.3 valid token exchange"
```

**5. Annotate functions as you implement**

```bash
/sdlc-assured:code-annotate src/auth/login.py::authenticate_user
# → auto-generates "# implements: P1.REQ-001"
/sdlc-assured:kb-codeindex
# → parses all annotations into library/_code-index.md
```

**6. Validate decomposition before commit**

```bash
/sdlc-assured:module-bound-check
# Runs the 5 module-bound validators: visibility, scatter, anaemic contexts, etc.
```

**7. For IEC 62304 / FDA change-impact tracking**

```bash
/sdlc-assured:change-impact-annotate
# Guides the change-impact declaration: which requirements does this change affect?
```

**8. Generate audit-ready artefacts**

```bash
/sdlc-assured:traceability-render
# Human-readable module-scoped doc with all evidence links and anchor navigation.
# Standard-specific exports (DO-178C / IEC 62304 / ISO 26262 / FDA DHF) are
# generated from the same underlying registry.
```

**Pre-push integration**: the bundle's validators run inside `/sdlc-core:validate --pre-push` once commissioned, so the standard validation pipeline gates Assured-style projects on traceability integrity along with the universal 10 checks.

For the full decision tree and method comparison, see [`docs/METHODS-GUIDE.md`](../../docs/METHODS-GUIDE.md).

## Audit-Ready at the Tooling Layer (v0.2.0)

**What this means.** v0.2.0 ships the *tooling substrate* required for auditor-grade traceability: the ID system, validators, evidence model, and exports are deterministic, regenerable, and produce auditor-readable artefacts. A complete audit dossier still requires both this tooling **and** manual evidence (test reports, design reviews, code walkthroughs) that the team supplies. This section is explicit about what is and is not automated, so consumers and auditors share the same expectations.

This claim is backed by EPIC #188 Phase G hard gates (all PASS) and an independent containerised architect review (verdict: AGREE-WITH-CONCERNS — no blockers; 4 carry-forward items deferred to v0.3.0).

### What the tooling automates

- **ID integrity** — positional namespace IDs (e.g., `P1.SP2.M3.REQ-007`) with uniqueness enforcement, parent registry, and round-trip parsing.
- **Bidirectional traceability** — forward links (REQ → design / code / test) and backward coverage (every code annotation indexed and verified against the ID registry).
- **Decomposition visibility** — 5 module-bound validators catch cross-boundary calls, anaemic-context patterns, and scatter violations against the rules declared in `programmes.yaml`.
- **Typed evidence statuses** — `Evidence-Status` field replaces untyped boolean traceability with `LINKED`, `MANUAL_EVIDENCE_REQUIRED`, or `CONFIGURATION_ARTIFACT`. Gap-typing is 30/30 (13 LINKED + 15 MANUAL_EVIDENCE_REQUIRED + 2 CONFIGURATION_ARTIFACT) on the bundle's own 44-REQ corpus.
- **Multi-format evidence** — a single requirement can be satisfied by Python `# implements:` annotations, markdown evidence tables, YAML satisfies-blocks, or satisfies-by-existence (file presence). All consumed via a unified `EvidenceIndexEntry` API; teams pick the format that matches their existing artefacts.
- **Platform-neutral dependency extraction** — language-agnostic import-graph extraction (Python via AST; JavaScript / Go / Java fall back to a regex extractor sharing a common interface). Non-Python projects participate in coverage analysis without needing Python AST.
- **Indirect DES-mediated coverage** — transitive call paths are now part of RTM. If A explicitly calls B (via the code index) and B is documented to call C (via DES), the path A → C is counted as covered. RTM source-code gap improved from 68.18% (v0.1.0 baseline) to 4.55% on the bundle's own corpus.
- **Module-scoped render** — human-readable traceability document with anchor links per module; the same render seeds the standard-specific exports.
- **Standard-specific exports** — DO-178C / IEC 62304 / ISO 26262 / FDA DHF compliance-mapping templates ready to populate with the team's evidence and submit.
- **REQ-quality linter** — `tools/validation/check-req-quality.py` detects DRIFTER requirements (REQs that open with implementation detail instead of user-visible capability). Advisory by default; `--strict` opt-in for use in CI.

### What still requires manual evidence (compliance responsibility)

- **Evidence collection.** The tooling structures and indexes evidence; teams supply the actual proof (test execution reports, design-review minutes, code-walkthrough records) and link them via `req-link` or annotation.
- **Confidence and rationale.** Teams annotate each evidence entry with confidence and rationale where required by the target standard. The tooling validates structural integrity, not domain correctness.
- **Manual-evidence policy.** Teams declare per-corpus what `MANUAL_EVIDENCE_REQUIRED` actually means in their context (e.g., "ELC of test report required" vs. "design-review minutes required"). The bundle records the typed status; the team writes the policy. (CI enforcement of corpus policy is deferred to v0.3.0 — see below.)
- **Change-impact declaration.** Teams populate `change-impact.md` for each commit that affects regulated requirements; the tooling validates structure but does not infer impact.

### What an auditor can regenerate (verification)

All of the following are deterministic and regenerable from the source tree alone — an auditor can re-run the validators on a submitted codebase and verify that the traceability has not been tampered with post-audit.

- **ID registry** (`library/_ids.md`) — regenerable from `requirements-spec.md` artefacts via `kb-codeindex`.
- **Code index** (`library/_code-index.md`) — regenerable from source via `kb-codeindex` (parses `# implements:` annotations).
- **Module dependency graph** — regenerable from source via the platform-neutral dependency extractor.
- **RTM (Requirements Traceability Matrix)** — backward coverage for every requirement, regenerable via the `backward_coverage_validator`.
- **Granularity match** — REQ IDs in code match declared requirements; regenerable via `granularity_match_validator`.
- **Traceability render** — human-readable module-scoped doc; regenerable via `traceability-render`.
- **Standard-specific exports** — regenerable from the registry into DO-178C / IEC 62304 / ISO 26262 / FDA DHF templates.

### What is deferred to v0.3.0 (not in scope of v0.2.0)

From the EPIC #188 architect review (AGREE-WITH-CONCERNS — these are the concerns):

1. **Formalise the MANUAL_EVIDENCE_REQUIRED corpus policy.** v0.2.0 records the typed status; v0.3.0 will define and enforce per-corpus policies (e.g., "all CRITICAL requirements must have observational evidence at high confidence") in CI.
2. **Wire `check-req-quality.py --strict` into the pre-push pipeline.** The linter is shipped as advisory in v0.2.0; v0.3.0 will gate on it.
3. **Refactor `GenericRegexExtractor` / `PythonAstExtractor` coupling.** The two extractors share an interface but couple too tightly for clean third-extractor addition; v0.3.0 will decouple.
4. **Address 6 deferred F-010 DRIFTER requirements.** 10 of 16 DRIFTER REQs were rewritten during EPIC #188 close; 6 were deferred as a coherent batch for v0.3.0 (they share a common cross-cutting rewrite pattern).

### Test coverage and metrics (v0.2.0)

| Metric | Result | Hard-gate threshold |
|--------|--------|--------------------|
| Total tests passing | 594 / 594 | All pass |
| Granularity-match noise | 0% | ≤ 5% |
| RTM source-code gap (own corpus) | 4.55% (was 68.18% in v0.1.0) | < 30% for audit pass |
| Gap-typing completeness | 30 / 30 | 100% |
| FAC false-positive rate | 0% | ≤ 5% |
| Visibility-rule enforcement | Clean (no false positives) | Clean |
| Validator determinism | All deterministic; auditor-regenerable | Required |

See `retrospectives/188-v020-assured-improvements.md` for the full Phase G test session and `research/v020-acceptance-metrics.md` for the metric definitions.

## Out of scope (v0.2.0 and beyond)

- AST-level code intelligence
- IDE integration (validators run at pre-push only)
- ALM database (no built-in DOORS / Polarion / ReqIF sync)
- Industry certification itself (this bundle is substrate; certification is performed by the team and the regulator)
- Bidirectional ReqIF sync
- Decomposition suggestion (the bundle validates declared decomposition; it does not suggest one)
- Distributed multi-team ID coordination
