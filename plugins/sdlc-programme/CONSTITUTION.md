# Programme Constitution (sdlc-programme bundle v0.1.0)

This constitution applies to projects commissioned to the **Programme** SDLC option. It extends the universal AI-First SDLC Constitution (`CONSTITUTION.md` at the framework root) with three Programme-specific articles enforcing formal waterfall phase gates and mandatory cross-phase review.

The universal articles (1-11) apply unchanged. Programme adds articles 12-14.

---

## Article 12 — Phase-gate compliance (Programme)

**Every feature MUST have all three phase artefacts in `docs/specs/<feature-id>/` before code commits proceed:**

1. `requirements-spec.md` — what the feature must do
2. `design-spec.md` — how it will be built, citing the requirements-spec by feature-id
3. `test-spec.md` — what tests verify, citing both requirements-spec and design-spec

Code may not be committed for a feature whose phase artefacts are incomplete. The `code-gate` validator enforces this at pre-push.

**Each phase artefact has mandatory sections** declared by its template (see `plugins/sdlc-programme/templates/`). Missing mandatory sections block the corresponding phase-gate validator.

**Each artefact has a stable feature-id** assigned at the requirements-spec phase and inherited by design-spec and test-spec. The feature-id format is `<short-slug>` (e.g., `cross-library-query`, `oauth-flow`).

## Article 13 — Cross-phase reference integrity (Programme)

**Citations between phase artefacts MUST resolve to existing IDs.**

- `design-spec.md` references requirements-spec via `satisfies: REQ-<feature-id>-NNN` lines. Each cited REQ-ID MUST exist in the requirements-spec.
- `test-spec.md` references both requirements-spec via `satisfies: REQ-<feature-id>-NNN` and design-spec via `satisfies: DES-<feature-id>-NNN`. Each cited ID MUST exist in the corresponding artefact.
- Code MUST cite a test-spec section via `# implements: TEST-<feature-id>-NNN` annotation. The cited TEST-ID MUST exist in the test-spec.

The `design-gate`, `test-gate`, and `code-gate` validators enforce this at pre-push. Broken references are defects, not style issues — they block.

Weak references (vague but non-broken; e.g., a citation that refers to a real REQ-ID but where the design-spec content doesn't actually address that requirement) are caught by `phase-review` (Article 14), not by the gates. Gates check structure; reviews check meaning.

## Article 14 — Mandatory phase-review (Programme)

**Cross-phase review via `phase-review <phase> <feature-id>` is mandatory for:**

- `design-spec.md` — review against the cited requirements-spec
- `test-spec.md` — review against both cited requirements-spec and design-spec

**Recommended (not mandatory) for:**

- `requirements-spec.md` — self-review or peer-review of completeness

The review record MUST be committed alongside the artefact under review. Review records live at `docs/specs/<feature-id>/reviews/<phase>-review-<reviewer>.md`. The review records are checked into git as the auditable evidence that human-in-the-loop review occurred.

`phase-gate` validators check that a review record exists before they pass for design-spec and test-spec phases. Missing review records block the gate.

---

## What this bundle does NOT enforce

- Decomposition / programs / sub-programs / modules — that's the **Assured** bundle (Method 2)
- Bidirectional traceability beyond REQ → DES → TEST → CODE — that's Assured
- Industry certification compliance (DO-178C, IEC 62304, etc.) — Programme is not a certification path; it is an audit-friendly substrate. Use Assured for regulated industries.
- Multi-team SAFe-Lite features — see #103 future v1.0 scope

The Programme constitution is the floor — universal articles plus phase gates. Teams may layer additional process on top via their own retrospective decisions.
