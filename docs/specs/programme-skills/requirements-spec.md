---
feature_id: programme-skills
module: P1.SP1.M1
granularity: requirement
---

# Requirements Specification: Programme-skills (Assured)

**Feature-id:** programme-skills
**Module:** P1.SP1.M1
**Granularity:** requirement
**Status:** Draft
**Author:** Phase F dogfood
**Created:** 2026-04-28

---

## Motivation

The Programme SDLC option exposes five user-facing skills: `commission-programme`,
`phase-init`, `phase-gate`, `phase-review`, and `traceability-export`. These skills
are the primary interface through which a user drives the formal waterfall phase-gate
workflow. Each skill must have a clearly specified user-visible contract so that its
behaviour can be designed, tested, and audited independently of the substrate and
validator layers it delegates to.

## Requirements

### REQ-programme-skills-001

The `commission-programme` skill SHALL scaffold a feature directory containing a REQ
spec, populate it with stub entries derived from `programs.yaml` module decomposition,
and record the commissioning event in an audit log.

**Module:** P1.SP1.M1
**Evidence-Status:** MANUAL_EVIDENCE_REQUIRED
**Justification:** This requirement is satisfied by the `commission-programme` skill workflow (a Claude Code skill YAML); the scaffolding behaviour is defined in the skill prompt, not a single annotatable Python function.

### REQ-programme-skills-002

The `phase-init` skill SHALL create the phase-appropriate spec file (requirements-spec,
design-spec, or test-spec) in the feature directory by copying the correct template from
the plugin, and SHALL refuse to proceed if the target spec file already exists.

**Module:** P1.SP1.M1
**Evidence-Status:** MANUAL_EVIDENCE_REQUIRED
**Justification:** This requirement is satisfied by the `phase-init` skill workflow; the template-copy and conflict-check behaviour is defined in the skill YAML, not a single annotatable Python function.

### REQ-programme-skills-003

The `phase-gate` skill SHALL invoke the corresponding gate function (requirements,
design, test, or code), surface pass/fail with per-failure rationale, and block
progression when the gate fails.

**Module:** P1.SP1.M1
**Evidence-Status:** MANUAL_EVIDENCE_REQUIRED
**Justification:** This requirement is satisfied by the `phase-gate` skill workflow; the gate-invocation and pass/fail reporting contract is defined in the skill YAML, not a single annotatable Python function.

### REQ-programme-skills-004

The `phase-review` skill SHALL record a dated review entry in the feature directory,
update the phase status, and make no structural mutations beyond the review record.

**Module:** P1.SP1.M1
**Evidence-Status:** MANUAL_EVIDENCE_REQUIRED
**Justification:** This requirement is satisfied by the `phase-review` skill workflow; the review-record writing and status-update contract is defined in the skill YAML, not a single annotatable Python function.

### REQ-programme-skills-005

The `traceability-export` skill SHALL produce a REQ→DES→TEST→CODE traceability matrix
in both CSV and Markdown formats from the artefacts in the feature directory, with no
rows silently omitted.

**Module:** P1.SP1.M1
**Evidence-Status:** MANUAL_EVIDENCE_REQUIRED
**Justification:** This requirement is satisfied by the `traceability-export` skill workflow; the matrix-production and no-omission contract is defined in the skill YAML, not a single annotatable Python function.

## Out of scope

- Code-phase annotation injection — the `commission-programme` skill installs bundle
  files and writes a commissioning record; it does not annotate source files.
- Phase artefact editing — `phase-init` copies a template; it does not pre-populate
  spec entries with project-specific content beyond the feature-id substitution.
- Automated remediation — `phase-gate` surfaces failures; it does not modify artefacts
  to fix them.
- Review content generation — `phase-review` dispatches a reviewer agent; the review
  content is produced by that agent, not by the skill itself.
- Standard-specific export formats (DO-178C, IEC 62304, ISO 26262, FDA DHF) —
  deferred to the Assured bundle.

## Success criteria

- `commission-programme` on a fresh project directory produces a
  `docs/specs/<feature-id>/requirements-spec.md` stub and a commissioning record in
  `.sdlc/team-config.json`.
- `phase-init requirements <feature-id>` on a project where no requirements-spec.md
  exists creates `docs/specs/<feature-id>/requirements-spec.md`; the same invocation
  a second time exits non-zero without overwriting the file.
- `phase-gate requirements <feature-id>` on a feature directory with a passing
  requirements-spec.md exits zero; on a feature directory with no spec file exits
  non-zero and emits at least one error line.
- `phase-review design <feature-id>` on a feature directory with a valid design-spec.md
  produces a review file at `docs/specs/<feature-id>/reviews/design-review-*.md` and
  exits zero; on a feature directory with no design-spec.md exits non-zero.
- `traceability-export csv <feature-id>` on a feature with all three spec artefacts
  produces a CSV file containing a `REQ,DES,TEST` header and one data row per declared
  REQ-ID with no rows omitted.
