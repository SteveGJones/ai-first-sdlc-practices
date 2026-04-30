---
feature_id: kb-bridge-mode
module: P1.SP1.M3
---

# Test Specification: KB-bridge SYNTHESISE-ACROSS-SPEC-TYPES mode (Assured)

**Feature-id:** kb-bridge-mode
**Module:** P1.SP1.M3
**Author:** Phase F dogfood
**Created:** 2026-04-30

---

## Test strategy

This is documentation, not Python code; the test approach is human review (architect review of the SKILL.md content) plus integration smoke tests of the dispatcher when the mode is invoked. Phase F does not implement integration smoke tests for the dispatcher (that's kb plugin scope, deferred to v0.2.0 if the architect review surfaces gaps).

## Test cases

### TEST-kb-bridge-mode-001

Verify the SYNTHESISE-ACROSS-SPEC-TYPES section is present in `synthesis-librarian.md` after Phase E task 23, with all required subsections (activation condition, behaviour, output format, valid_handles extension).

**satisfies:** REQ-kb-bridge-mode-001 via DES-kb-bridge-mode-001
**Module:** P1.SP1.M3

### TEST-kb-bridge-mode-002

Verify that `valid_handles` extension is documented in the same section.

**satisfies:** REQ-kb-bridge-mode-002 via DES-kb-bridge-mode-002
**Module:** P1.SP1.M3

## Coverage gaps (acknowledged)

- No automated test exists today for either REQ. Phase F surfaces this as a finding (likely F-NNN: "Method 2 has no story for documentation-only modules").
