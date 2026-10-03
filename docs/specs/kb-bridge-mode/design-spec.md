---
feature_id: kb-bridge-mode
module: P1.SP1.M3
---

# Design Specification: KB-bridge SYNTHESISE-ACROSS-SPEC-TYPES mode (Assured)

**Feature-id:** kb-bridge-mode
**Module:** P1.SP1.M3
**Author:** Phase F dogfood
**Created:** 2026-04-30

---

## Architecture

The mode is a documentation-only addition to `synthesis-librarian.md`. The agent runtime reads SKILL/agent body content; mode-routing is text-based via the `mode:` field in the dispatch prompt. No code change in the kb plugin's Python is required.

## Design elements

### DES-kb-bridge-mode-001

A new `### MODE: SYNTHESISE-ACROSS-SPEC-TYPES` section added to `synthesis-librarian.md` after the existing ACROSS-SOURCES section. Section documents activation condition, behaviour, output format, and `valid_handles` extension.

**satisfies:** REQ-kb-bridge-mode-001
**Module:** P1.SP1.M3

### DES-kb-bridge-mode-002

The `valid_handles` extension is documented as a behaviour the dispatcher must apply when the mode is active. Enforcement remains the dispatcher's responsibility (the agent body is documentation; the post-check is in the kb dispatcher code).

**satisfies:** REQ-kb-bridge-mode-002
**Module:** P1.SP1.M3

## Visibility rules used

- P1.SP1.M3 → none. KB-bridge is a leaf in the dogfood decomposition.

## Out of scope

- Implementing the dispatcher behaviour (lives in kb plugin code, outside Phase F's annotation surface).
