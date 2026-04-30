# Phase F — Dogfood Findings

## F-002 — programs.yaml `paths` cannot scope to a section of a file

**Severity:** MINOR
**Surfaced during:** Task 2 (Stage 1)
**Reproduction:** Module M3 (kb-bridge) implements only the SYNTHESISE-ACROSS-SPEC-TYPES section of synthesis-librarian.md, not the whole file. programs.yaml `paths` is whole-directory only.
**Impact on regulated-industry users:** medium — fine-grained ownership of file sections is common in regulated codebases (e.g., MISRA-C compliant subset of a header file)
**Suggested resolution:** consider line-range or section-anchor support in v0.2.0; or document the limitation
**Related:** plugins/sdlc-assured/scripts/assured/decomposition.py:Module.paths
