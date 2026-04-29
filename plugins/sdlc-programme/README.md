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

After commission, every feature follows: `phase-init requirements <feature-id>` → fill in template → `phase-gate requirements <feature-id>` → `phase-init design <feature-id>` → fill in → `phase-review design <feature-id>` (mandatory) → `phase-gate design <feature-id>` → repeat for test → write code under TDD against the test-spec → push.

## See also

- Bundle contract: `docs/architecture/option-bundle-contract.md`
- Phase D substrate spec: `docs/feature-proposals/186-phase-d-programme-bundle-substrate.md`
- Method 1 design: `research/sdlc-bundles/METHODS.md` §3
- Future v1.0 scope: #103
