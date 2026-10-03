---
feature_id: kb-bridge-mode
module: P1.SP1.M3
granularity: requirement
---

# Requirements Specification: KB-bridge SYNTHESISE-ACROSS-SPEC-TYPES mode (Assured)

**Feature-id:** kb-bridge-mode
**Module:** P1.SP1.M3
**Granularity:** requirement
**Status:** Draft
**Author:** Phase F dogfood
**Created:** 2026-04-30

---

## Motivation

Method 2 (Assured) needs to query across spec types (REQ, DES, TEST, CODE) when answering "what implements X?" queries. This requires extending the existing synthesis-librarian agent with a new dispatch mode. The mode lives in the kb-bridge module — the bridge between the Assured bundle and the existing knowledge-base agent infrastructure.

## Requirements

### REQ-kb-bridge-mode-001

The synthesis-librarian agent MUST recognise a `mode: synthesise-across-spec-types` dispatch directive and treat it as a distinct synthesis mode, not a fallback to `SYNTHESISE-ACROSS-SOURCES`.

**Module:** P1.SP1.M3
**Evidence-Status:** MANUAL_EVIDENCE_REQUIRED
**Justification:** This requirement is satisfied by the `synthesis-librarian` agent YAML (in `plugins/sdlc-knowledge-base/agents/`); mode recognition is defined in the agent prompt, not an annotatable Python function.

### REQ-kb-bridge-mode-002

When the SYNTHESISE-ACROSS-SPEC-TYPES mode is active, the agent's `valid_handles` whitelist MUST accept the four pseudo-handles `req`, `des`, `test`, `code` in addition to any project library handles, so that spec-type-keyed dispatch sources resolve correctly during attribution post-checks.

**Module:** P1.SP1.M3
**Evidence-Status:** MANUAL_EVIDENCE_REQUIRED
**Justification:** This requirement is satisfied by the `synthesis-librarian` agent YAML; the `valid_handles` whitelist extension is defined in the agent prompt, not an annotatable Python function.

## Out of scope

- Multi-mode dispatch (one mode per dispatch is enforced by the existing dispatcher).
- New synthesis prompts for non-Assured bundles.

## Success criteria

- A dispatch with `mode: synthesise-across-spec-types` and pseudo-handles `req`, `des`, `test`, `code` produces an output with `## Synthesis` and `## Attribution` sections, citing IDs (not file paths).
- The same dispatch with one of the four pseudo-handles missing from `valid_handles` aborts via the post-check (per Article confidentiality).
