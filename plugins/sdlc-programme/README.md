# sdlc-programme — Programme SDLC bundle (v0.1.0)

Method 1 phase-gate substrate for programme-of-work delivery. Ship a project to **Programme** when:

- Team size 11-50 people across 2-5 teams
- Specification maturity is formal or contract-first
- Blast radius is moderate-to-high
- Audit-friendly traceability matters but full regulated-industry traceability does not

For regulated-industry projects (DO-178C, IEC 62304, ISO 26262, IEC 61508, FDA), use the **Assured** bundle instead (Phase E).
For 1-2 person projects, use **Solo**. For 3-10 person product teams, **Single-team** (the framework default).

## What this bundle ships

- **4 phase gates** — `requirements-gate`, `design-gate`, `test-gate`, `code-gate` enforced at pre-push and CI. Block on missing artefact or broken cross-phase reference; warn on weak references.
- **3 phase artefact templates** — `requirements-spec.md`, `design-spec.md`, `test-spec.md` copied into a project on commission. Each phase artefact has stable IDs that subsequent phases reference.
- **5 skills** — `commission-programme`, `phase-init <phase>`, `phase-gate <phase>`, `phase-review <phase>` (mandatory for design-spec and test-spec), `traceability-export <format>` (csv, markdown).
- **Programme constitution** — overlays Single-team's foundations with 3 Programme-specific articles enforcing phase-gate compliance, cross-phase reference integrity, and mandatory `phase-review`.

## What this bundle does NOT ship (yet)

- Multi-team SAFe-Lite features (contract registry, dependency tracking, programme-wide audit consolidation, multi-team agents). See issue #103 — those land in v1.0 when a real multi-team collaborator is available.
- Method 2 features (traceability registry, decomposition, KB-for-code). See the Assured bundle (Phase E).

## How to commission

```
/sdlc-core:commission --option programme --level production
```

(The bundle ships an equivalent wrapper, `/sdlc-programme:commission-programme`, which delegates to the core skill with the right flags.)

After commission, every feature follows: `phase-init requirements <feature-id>` → fill in template → `phase-gate requirements <feature-id>` → `phase-init design <feature-id>` → fill in → `phase-review design <feature-id>` (mandatory) → `phase-gate design <feature-id>` → repeat for test → write code under TDD against the test-spec → push.

## Getting Started

A complete walkthrough from install to first audit-ready export.

**1. Install and commission**

```bash
/plugin install sdlc-programme@ai-first-sdlc
/sdlc-core:commission --option programme --level production
# (or: /sdlc-programme:commission-programme)
```

This scaffolds `requirements-spec.md`, `design-spec.md`, and `test-spec.md` templates into your project's specifications directory and overlays the Programme constitution articles (12–14) on top of the universal articles (1–11).

**2. For each feature, walk the phases**

```bash
# REQUIREMENTS phase
/sdlc-programme:phase-init requirements FEAT-123
# Edit the generated requirements-spec.md (capture user-visible capability with stable IDs)
/sdlc-programme:phase-gate requirements FEAT-123
# Gate validates artefact presence, ID format, and reference integrity.

# DESIGN phase
/sdlc-programme:phase-init design FEAT-123
# Edit the generated design-spec.md (architecture, decisions, references back to REQs)
/sdlc-programme:phase-review design FEAT-123    # MANDATORY cross-team sign-off
/sdlc-programme:phase-gate design FEAT-123

# TEST phase
/sdlc-programme:phase-init test FEAT-123
# Edit the generated test-spec.md (cases reference design + requirements)
/sdlc-programme:phase-review test FEAT-123      # MANDATORY
/sdlc-programme:phase-gate test FEAT-123

# CODE phase — uses the standard sdlc-core flow
/sdlc-core:new-feature 123 feature-name "Description"
# Implement under TDD against test-spec
/sdlc-core:validate --pre-push
/sdlc-core:pr
```

**3. Export traceability for audit**

```bash
/sdlc-programme:traceability-export csv      # Machine-readable matrix
/sdlc-programme:traceability-export markdown # Human-readable doc
```

**4. Throughout the lifecycle**

- The four phase gates run at pre-push and CI; they block on missing artefacts or broken cross-phase references and warn on weak references.
- `phase-review` records a sign-off per phase artefact in the project's review log; downstream phase-gate enforcement reads this log.
- All phase artefacts use stable IDs that the next phase references — break a reference and the gate blocks until you fix it.

## When to use this bundle vs. alternatives

| Project shape | Recommended option |
|---------------|--------------------|
| 1–2 contributors, fast iteration | `/sdlc-core:commission --option solo` (no extra bundle) |
| 3–10 contributors, organic delivery | Single-team default (no commission needed) |
| **11–50 contributors across 2–5 teams, formal phase gates** | **This bundle (Programme, Method 1)** |
| Regulated industry — DO-178C / IEC 62304 / ISO 26262 / FDA 21 CFR Part 820 | [`sdlc-assured`](../sdlc-assured/README.md) (Method 2 — superset of Programme with traceability and decomposition) |

For the full decision tree, comparison table, and migration notes, see [`docs/METHODS-GUIDE.md`](../../docs/METHODS-GUIDE.md).

## See also

- Bundle contract: `docs/architecture/option-bundle-contract.md`
- Phase D substrate spec: `docs/feature-proposals/186-phase-d-programme-bundle-substrate.md`
- Method 1 design: `research/sdlc-bundles/METHODS.md` §3
- Future v1.0 scope: #103
