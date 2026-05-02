<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [SDLC Methods Guide](#sdlc-methods-guide)
  - [Overview](#overview)
  - [Decision Tree](#decision-tree)
  - [Single-team](#single-team)
    - [When to use](#when-to-use)
    - [What you get](#what-you-get)
    - [Example workflow](#example-workflow)
    - [What you don't get (compared with Programme / Assured)](#what-you-dont-get-compared-with-programme--assured)
  - [Solo](#solo)
    - [When to use](#when-to-use-1)
    - [What Solo adds (or removes) compared with Single-team](#what-solo-adds-or-removes-compared-with-single-team)
    - [Example workflow](#example-workflow-1)
    - [When NOT to use Solo](#when-not-to-use-solo)
  - [Programme (Method 1)](#programme-method-1)
    - [When to use](#when-to-use-2)
    - [What Method 1 adds over Single-team](#what-method-1-adds-over-single-team)
    - [Example workflow per feature](#example-workflow-per-feature)
    - [Trade-offs](#trade-offs)
    - [What you don't get (compared with Assured)](#what-you-dont-get-compared-with-assured)
  - [Assured (Method 2)](#assured-method-2)
    - [When to use](#when-to-use-3)
    - [What Method 2 adds over Method 1](#what-method-2-adds-over-method-1)
    - [Example workflow per requirement](#example-workflow-per-requirement)
    - [v0.2.0 status: audit-ready at the tooling layer](#v020-status-audit-ready-at-the-tooling-layer)
    - [Trade-offs](#trade-offs-1)
  - [Comparison Table](#comparison-table)
  - [Trade-offs](#trade-offs-2)
    - [Solo](#solo-1)
    - [Single-team](#single-team-1)
    - [Programme](#programme)
    - [Assured](#assured)
  - [Migration](#migration)
    - [Single-team → Programme](#single-team-%E2%86%92-programme)
    - [Single-team → Assured](#single-team-%E2%86%92-assured)
    - [Programme → Assured](#programme-%E2%86%92-assured)
    - [Solo → Single-team](#solo-%E2%86%92-single-team)
    - [Downgrades](#downgrades)
  - [Commissioning Status and `setup-team`](#commissioning-status-and-setup-team)
  - [Further Reading](#further-reading)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# SDLC Methods Guide

The AI-First SDLC Framework supports four SDLC delivery structures. This guide helps you pick the right one and explains how to migrate between them as your project evolves.

If you only read one section, read [Decision Tree](#decision-tree) and [Comparison Table](#comparison-table).

---

## Overview

The framework's `/sdlc-core:commission` skill walks projects through commissioning to one of four options:

| Option | One-line summary |
|--------|------------------|
| **Solo** | 1–2 contributors, fast iteration, lightweight constitution overlay. |
| **Single-team** | 3–10 contributors, organic delivery — the framework default. |
| **Programme** (Method 1) | 11–50 across 2–5 teams, formal phase gates, mandatory cross-phase review. |
| **Assured** (Method 2) | Regulated industries **or** complex agentic systems at scale (10+ bounded contexts; scoped context per agent); audit-ready traceability + decomposition + typed evidence. |

The choice is **orthogonal to team plugin selection**. A regulated medical-device project might be `cloud-infrastructure` (project type C in `setup-team`) **and** `assured` (SDLC method D); an AI/ML prototype might be `ai-ml` (project type B) **and** `solo` (SDLC method B). Project type drives team plugin selection; SDLC method drives delivery discipline.

You don't have to pick at setup time — `setup-team` accepts "Decide later" and you can run `/sdlc-core:commission` at any point.

---

## Decision Tree

Answer the questions in order; the first match wins.

**1. Are you targeting a regulated industry** (DO-178C avionics, IEC 62304 medical devices, ISO 26262 automotive, IEC 61508 functional safety, FDA 21 CFR Part 820) **— or — building a complex agentic system with 10+ bounded contexts** where you need to give each agent a scoped context slice rather than the whole system (to prevent mis-implementation from "knowing too much")?

- **Yes to either** → use [**Assured (Method 2)**](#assured-method-2). Stop here.
- **No** → continue.

**2. Do you need formal cross-team sign-off on phase artefacts?** (typically: 11+ contributors, **or** 2 or more sub-teams that must explicitly approve each other's design / test artefacts)

- **Yes** → use [**Programme (Method 1)**](#programme-method-1). Stop here. The driver is the *cross-team review need*, not just the headcount — a single team of 14 that doesn't need formal sign-off can still pick Single-team; a single team of 8 that does need formal sign-off should pick Programme.
- **No** → continue.

**3. Is this a 1–2 person project with fast iteration and minimal review overhead?**

- **Yes** → use [**Solo**](#solo). Stop here.
- **No** → continue.

**4. Default**

- Use [**Single-team**](#single-team) — the framework default; no commissioning needed. Single-team scales comfortably to ~15 contributors; the upper bound is whenever you start needing formal cross-phase sign-off (see Q2).

If you're between two options, pick the lighter one — you can always migrate up later. See [Migration](#migration) for what each upgrade involves.

---

## Single-team

**The framework default.** No commissioning is required; you get this by installing `sdlc-core` and running `/sdlc-core:setup-team` without picking a method bundle.

### When to use

- Team size: 3–10 contributors
- Delivery: a single product, startup MVP, established team with informal process
- Audit requirement: none (or self-audit only)
- Specification maturity: informal or organic
- Project lifecycle: production work that doesn't need formal phase gates

### What you get

- `/sdlc-core:validate` — 10-check validation pipeline (syntax, lint, format, technical-debt, tests, imports, type-safety, security, static analysis, smoke test)
- `/sdlc-core:new-feature` — feature proposal + retrospective + branch in one step
- `/sdlc-core:commit`, `/sdlc-core:pr` — validated commits and PR creation
- Specialist agents from the team plugins picked in `setup-team` (solution architect, database architect, security architect, etc.)
- Constitution articles 1–11 enforced at pre-push and CI
- Optional: `sdlc-knowledge-base` for research-grounded decisions; `sdlc-workflows` for containerised parallel-agent execution

### Example workflow

```bash
/sdlc-core:setup-team
# (pick "Single-team" when asked the SDLC method question)

/sdlc-core:new-feature 1 auth-system "User authentication"
# Use specialist agents to architect; implement under TDD
/sdlc-core:validate --pre-push
/sdlc-core:pr
```

### What you don't get (compared with Programme / Assured)

- No formal phase gates between requirements / design / test / code
- No mandatory cross-phase review
- No bidirectional traceability (REQ ↔ design ↔ code ↔ test)
- No DDD decomposition with visibility-rule enforcement
- No standard-specific (DO-178C / IEC 62304 / etc.) export templates

If you need any of those, pick Programme or Assured.

---

## Solo

**Lightweight overlay for very small teams.** Solo is single-team minus most of the ceremony; commission with `/sdlc-core:commission --option solo`.

### When to use

- Team size: 1–2 contributors
- Delivery: research code, prototypes, side projects, time-boxed experiments
- Audit requirement: none
- Specification maturity: organic; you might not write a feature proposal at all for some changes
- Project lifecycle: throwaway, exploratory, or pre-decision work

### What Solo adds (or removes) compared with Single-team

- Lighter retrospective cadence (one per significant cluster of changes, not per feature)
- Reduced constitution enforcement on personal-style preferences (e.g., commit message format checks become advisory)
- Optional skip on the formal feature-proposal step for changes that don't materially alter design

The full delta is in the Solo constitution overlay (installed by `/sdlc-core:commission --option solo`).

### Example workflow

```bash
/sdlc-core:commission --option solo
# (after setup-team)

git checkout -b experiment/<idea>
# Code freely; validate before pushing
/sdlc-core:validate --pre-push
git push -u origin experiment/<idea>
```

### When NOT to use Solo

- More than 2 contributors → use Single-team
- Audit-relevant work → use Assured
- Even informal multi-team coordination → use Programme

---

## Programme (Method 1)

**For multi-team programmes-of-work.** Adds formal phase gates and mandatory cross-phase review on top of Single-team's foundations. Commission with `/sdlc-core:commission --option programme --level production`.

### When to use

- Team size: 11–50 across 2–5 teams
- Delivery: large feature, product release, cross-team programme of work
- Audit requirement: moderate (cross-phase traceability, recorded reviews)
- Specification maturity: formal or contract-first
- Regulatory context: **not** regulated industry (if yes, Method 2 is the right choice)

### What Method 1 adds over Single-team

- **4 phase gates**: `requirements-gate`, `design-gate`, `test-gate`, `code-gate` enforced at pre-push and CI. Block on missing artefacts or broken cross-phase references; warn on weak references.
- **3 phase artefact templates**: `requirements-spec.md`, `design-spec.md`, `test-spec.md` with stable IDs that subsequent phases reference.
- **Mandatory `phase-review`** for design and test phases — explicit cross-team sign-off recorded before the next phase can gate.
- **5 skills**: `commission-programme`, `phase-init`, `phase-gate`, `phase-review`, `traceability-export` (csv / markdown).
- **Programme constitution overlay**: Articles 12–14 enforce phase-gate compliance, cross-phase reference integrity, and mandatory `phase-review`.

### Example workflow per feature

```bash
# REQUIREMENTS
/sdlc-programme:phase-init requirements FEAT-123
# Edit requirements-spec.md; capture user-visible capability
/sdlc-programme:phase-gate requirements FEAT-123

# DESIGN
/sdlc-programme:phase-init design FEAT-123
# Edit design-spec.md; reference requirements
/sdlc-programme:phase-review design FEAT-123          # Mandatory
/sdlc-programme:phase-gate design FEAT-123

# TEST
/sdlc-programme:phase-init test FEAT-123
# Edit test-spec.md; reference design
/sdlc-programme:phase-review test FEAT-123             # Mandatory
/sdlc-programme:phase-gate test FEAT-123

# CODE
/sdlc-core:new-feature 123 feature-name "Description"
# Implement under TDD against test-spec
/sdlc-core:pr

# AUDIT
/sdlc-programme:traceability-export csv
/sdlc-programme:traceability-export markdown
```

### Trade-offs

- **Pro**: formal discipline; cross-team sign-off is explicit and recorded; auditors can reconstruct what was reviewed and when.
- **Con**: per-feature ceremony is significantly higher than Single-team; not suitable for small teams or rapid prototyping; not certified for regulated-industry use.

### What you don't get (compared with Assured)

- No bidirectional traceability validators (REQ → code) — Programme tracks REQ → design → test, but not REQ → code annotations.
- No positional namespace IDs.
- No DDD decomposition or module visibility rules.
- No typed evidence statuses (LINKED / MANUAL_EVIDENCE_REQUIRED / CONFIGURATION_ARTIFACT).
- No standard-specific export templates (DO-178C / IEC 62304 / etc.).

If you need any of those, pick Assured.

---

## Assured (Method 2)

**For regulated industries.** Method 2 is a superset of Method 1 — it keeps phase discipline and adds the substrate required for audit-ready traceability. Commission with `/sdlc-core:commission --option assured --level production` (and run `/sdlc-assured:commission-assured` to scaffold the decomposition files).

### When to use

**Regulated industries** — any of these apply:

- Target standards: **DO-178C** (avionics), **IEC 62304** (medical devices), **ISO 26262** (automotive), **IEC 61508** (functional safety), **FDA 21 CFR Part 820** (medical devices)
- Audit requirement: audit-ready bidirectional traceability, positional IDs, decomposition visibility, typed evidence
- Regulator context: FAA, EASA, FDA, notified body, certification agency

**Complex agentic systems at scale** — any of these apply:

- 10 or more bounded contexts / modules where routing each agent to a scoped slice reduces mis-implementation
- You need KB-for-code (`# implements:` annotations) to give agents a requirements-grounded context slice without loading the entire codebase
- Decomposition visibility enforcement across module boundaries is operationally valuable, regardless of any audit requirement

**Common to both**:

- Specification maturity: formal, requirement-driven
- Team size: any (the bundle scales from one engineer up to multi-team programmes)

### What Method 2 adds over Method 1

- **Positional namespace IDs**: `P1.SP2.M3.REQ-007` for decomposed projects; flat IDs (`REQ-001`) preserved for non-decomposed projects.
- **ID registry** (`library/_ids.md`): auto-generated; tracks every ID, source, and link; uniqueness and reference resolution enforced.
- **Bidirectional traceability**: forward (REQ → design / code / test) **and** backward (code → REQ); both validated.
- **DDD decomposition**: `programmes.yaml` declares bounded contexts with parent + visibility rules (public / internal / test-only). Hexagonal architecture is opt-in.
- **5 module-bound validators**: visibility, scatter, anaemic-context detection, etc.
- **KB-for-code**: inline `# implements: <ID>` annotations parsed into `library/_code-index.md` (shelf-index-shaped).
- **Typed evidence statuses (v0.2.0)**: `Evidence-Status` field — `LINKED`, `MANUAL_EVIDENCE_REQUIRED`, or `CONFIGURATION_ARTIFACT`.
- **Multi-format evidence model (v0.2.0)**: requirements satisfied by Python annotations, markdown tables, YAML satisfies-blocks, or satisfies-by-existence — all consumed via a unified API.
- **Platform-neutral dependency extractor (v0.2.0)**: language-agnostic import-graph extraction (Python AST + regex extractor for JS / Go / Java).
- **Indirect DES-mediated coverage (v0.2.0)**: transitive call paths count as covered (A → B → C ⇒ A covers C via DES).
- **Standard-specific exports**: DO-178C / IEC 62304 / ISO 26262 / FDA DHF templates ready to populate.
- **REQ-quality linter (v0.2.0)**: `tools/validation/check-req-quality.py` detects DRIFTER requirements (REQs that open with implementation rather than capability). Advisory by default; `--strict` opt-in.
- **Assured constitution overlay**: Articles 15–17 enforce ID integrity, decomposition discipline, and KB-for-code annotation completeness.

### Example workflow per requirement

```bash
# Mint a requirement with positional ID
/sdlc-assured:req-add authentication feature "System SHALL authenticate users via OAuth 2.0"
# → P1.REQ-001

# Link it bidirectionally
/sdlc-assured:req-link P1.REQ-001 design-spec.md "Section 3.2 OAuth flow"
/sdlc-assured:req-link P1.REQ-001 test-spec.md "Test 4.1.3 valid token"

# As you implement
/sdlc-assured:code-annotate src/auth/login.py::authenticate_user
# → auto-generates "# implements: P1.REQ-001"
/sdlc-assured:kb-codeindex
# → parses all annotations into library/_code-index.md

# Before commit
/sdlc-assured:module-bound-check       # 5 decomposition validators
/sdlc-assured:change-impact-annotate   # IEC 62304 / FDA change-impact tracking

# For audit
/sdlc-assured:traceability-render
# Standard-specific exports (DO-178C / IEC 62304 / ISO 26262 / FDA DHF) generated from same registry
```

### v0.2.0 status: audit-ready at the tooling layer

**The gap in one sentence:** the tooling automates ID integrity, traceability, and standard-specific exports; teams supply the actual evidence that backs each requirement; corpus-policy CI enforcement and REQ-quality lint gating are deferred to v0.3.0.

The validators, traceability machinery, evidence model, and exports are deterministic and auditor-regenerable. EPIC #188 Phase G hard-gate metrics: 594 / 594 tests pass; RTM source-code gap 4.55% (2 of 44 REQs in the bundle's own corpus, both correctly typed as `CONFIGURATION_ARTIFACT` — Constitution overlay contracts with no Python function to annotate); granularity-match noise 0%; gap-typing complete. Independent architect review verdict: AGREE-WITH-CONCERNS — no blockers; four carry-forward items deferred to v0.3.0 (corpus-policy CI enforcement, REQ-quality linter CI gate, extractor decoupling, six deferred F-010 DRIFTERs).

For a full breakdown of what's automated vs. what requires manual evidence vs. what an auditor can regenerate vs. what's deferred to v0.3.0 — including a glossary of the metric terms — see the [Audit-Ready at the Tooling Layer (v0.2.0)](../plugins/sdlc-assured/README.md#audit-ready-at-the-tooling-layer-v020) section in the bundle README.

### Trade-offs

- **Pro**: audit-ready at the tooling layer — validators are deterministic, an auditor can regenerate the ID registry, code index, RTM, and standard-specific exports from the source tree alone; evidence typing makes audit dossiers reproducible. Metrics and the four v0.3.0 carry-forward gaps are documented in the [bundle README](../plugins/sdlc-assured/README.md#audit-ready-at-the-tooling-layer-v020) with a glossary.
- **Con**: requires explicit decomposition discipline (`programmes.yaml` + visibility rules); evidence collection is still manual (teams provide proof, tooling provides structure); higher learning curve than Programme.

---

## Comparison Table

| Criterion | Solo | Single-team | Programme (Method 1) | Assured (Method 2) |
|-----------|------|-------------|----------------------|---------------------|
| Team size | 1–2 | 3–10 | 11–50 | Any |
| Delivery structure | Light overlay | Organic | Phase gates (REQ → DES → TEST → CODE) | Decomposed modules + evidence-typed REQs |
| Per-feature ceremony | Minimal | Standard | High (3 mandatory phase reviews) | High (decomposition + traceability links) |
| Traceability | Code → test only | Code → test only | Cross-phase (REQ → design → test → code) | Bidirectional (REQ ↔ design ↔ test ↔ code) + positional IDs + ID registry |
| Decomposition | Implicit | Implicit | Optional | Mandatory (DDD, visibility rules) |
| Evidence model | None (test coverage only) | None (test coverage only) | Phase-review records | Typed (LINKED / MANUAL_EVIDENCE_REQUIRED / CONFIGURATION_ARTIFACT) |
| Audit readiness | None | None | Cross-phase records | Auditor-regenerable, standard-specific exports |
| Skills shipped | 9 (sdlc-core only) | 9 (sdlc-core only) | 9 + 5 (sdlc-programme) = 14 | 9 + 8 (sdlc-assured) = 17 |
| Constitution articles | 1–11 (overlay relaxes some) | 1–11 | 1–11 + 12–14 | 1–11 + 12–14 + 15–17 |
| Regulatory support | None | None | None | DO-178C, IEC 62304, ISO 26262, IEC 61508, FDA 21 CFR Part 820 |
| Commission command | `/sdlc-core:commission --option solo` | (none — default) | `/sdlc-core:commission --option programme` | `/sdlc-core:commission --option assured` |
| When to pick | Solo / experimental | Most projects (default) | Multi-team, formal spec | Regulated industry OR complex agentic system (10+ bounded contexts) |

---

## Trade-offs

### Solo

- **Pro**: zero ceremony; fits research / prototype workflow; you can ship in an hour without writing a feature proposal first
- **Con**: no enforcement of cross-team practices (you have no team); not suitable once a second contributor joins

### Single-team

- **Pro**: minimal overhead with all the validators; specialist agents do the architectural lifting; well-suited for product teams shipping iteratively
- **Con**: no formal phase enforcement; team discipline is required to maintain quality; not suitable for multi-team or regulated contexts

### Programme

- **Pro**: phase discipline visible to auditors; cross-team sign-off explicit and recorded; scales to ~50 contributors across teams
- **Con**: significantly higher per-feature ceremony than Single-team; requires explicit cross-team sign-off; does not automate evidence collection; not certified for regulated-industry use

### Assured

- **Pro**: audit-ready at the tooling layer (validators are deterministic; an auditor can regenerate ID registry, code index, RTM, and standard-specific exports from the source tree); evidence typing makes audit dossiers reproducible. EPIC #188 metrics are documented in the [bundle README](../plugins/sdlc-assured/README.md#audit-ready-at-the-tooling-layer-v020).
- **Con**: requires explicit decomposition discipline (`programmes.yaml` + visibility rules); evidence collection is still manual (teams provide proof, tooling provides structure); higher learning curve. Four v0.3.0 carry-forward gaps (corpus-policy CI enforcement, REQ-quality linter CI gate, extractor decoupling, deferred F-010 DRIFTERs) — see the bundle README for what each gap means for what an auditor can rely on.

---

## Migration

Methods can be added or upgraded mid-project without rewriting existing artefacts. The framework is additive — new constitution overlays apply to **new** work, with explicit migration steps for legacy content.

### Single-team → Programme

You can add phase gates mid-project.

1. Run `/sdlc-core:commission --option programme --level production` to install the bundle and scaffold templates.
2. Existing `/sdlc-core:new-feature` work continues to validate as before; new features follow the phase workflow.
3. Optional: backfill `requirements-spec.md` artefacts for in-flight features so phase gates can be applied retrospectively.

### Single-team → Assured

Requires more upfront work because Assured needs decomposition declared.

1. Decide your decomposition strategy (DDD bounded contexts). For a non-decomposed project, declare a single root module — flat IDs (`REQ-001`) will be minted.
2. Run `/sdlc-core:commission --option assured --level production` to install the bundle.
3. Run `/sdlc-assured:commission-assured` to scaffold `programmes.yaml`, `visibility-rules.md`, and base specification templates.
4. Edit `programmes.yaml` to declare modules.
5. New requirements use `req-add` and get positional IDs; legacy IDs can be mapped (manual today; an import-mode is on the v0.3.0+ roadmap). For corpora over ~50 legacy requirements, plan this as a one-off migration project rather than per-feature work.
6. Annotate functions as you touch them (`code-annotate` + `kb-codeindex`); legacy code can be annotated incrementally.

### Programme → Assured

Method 2 is a superset of Method 1.

1. Run `/sdlc-core:commission --option assured --level production` (this overlays articles 15–17 on top of the existing 12–14).
2. Run `/sdlc-assured:commission-assured` to scaffold `programmes.yaml` and `visibility-rules.md`.
3. Existing phase artefacts (REQ / DES / TEST specs) are valid Assured artefacts — IDs are reused; you opt in to positional IDs by declaring decomposition.
4. Validators activate at next pre-push. Address any backward-coverage gaps incrementally.

### Solo → Single-team

1. Just stop using `--option solo`. The Solo overlay relaxes some defaults; ceasing to use it re-engages the standard Single-team behaviour.
2. If `/sdlc-core:commission --option solo` was recorded in `.sdlc/team-config.json`, run `/sdlc-core:commission --option single-team` to switch (or just delete the relevant fields).

### Downgrades

The framework allows downgrades, but they are rare in practice. If you commissioned Assured and want to drop back to Programme, run `/sdlc-core:commission --option programme` and any Assured-only validators stop running. Existing positional IDs remain valid (they're just longer than necessary for Method 1).

---

## Commissioning Status and `setup-team`

The `/sdlc-core:setup-team` skill asks the SDLC method question (step 3) and records the answer in `.sdlc/team-config.json` as `sdlc_method`. For Programme and Assured, it also adds the bundle plugin to the install recommendation list and surfaces a "Post-install action" reminder to run `/sdlc-core:commission` once the plugin is installed.

If you pick "Decide later" during `setup-team`, `sdlc_method` is recorded as `undecided` and the post-check (step 13) surfaces a one-line reminder. You can run `/sdlc-core:commission` at any time to pick.

If `sdlc_method` is already set in `.sdlc/team-config.json` and `sdlc_method_commissioned` is `false`, the post-check reminds you that the bundle is installed but not yet commissioned. Run the appropriate `/sdlc-core:commission` command to complete setup.

---

## Further Reading

- [README.md](../README.md) — project overview and quick-start
- [HOWTO.md](HOWTO.md) — step-by-step workflows for all methods
- [QUICK-REFERENCE.md](QUICK-REFERENCE.md) — command cheat sheet
- [PLUGIN-CONSUMER-GUIDE.md](PLUGIN-CONSUMER-GUIDE.md) — plugin ecosystem details
- [CONSTITUTION.md](../CONSTITUTION.md) — all rules (universal articles 1–11; Programme adds 12–14; Assured adds 15–17)
- `plugins/sdlc-programme/README.md` — Method 1 detail and Getting Started walkthrough
- `plugins/sdlc-assured/README.md` — Method 2 detail, Getting Started walkthrough, and the **Audit-Ready at the Tooling Layer (v0.2.0)** narrative explaining what's automated, what's manual evidence, what an auditor can regenerate, and what's deferred to v0.3.0
