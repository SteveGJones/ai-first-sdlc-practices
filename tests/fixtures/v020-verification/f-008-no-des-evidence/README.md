## Defect: F-008 — No DES evidence annotation

REQ-fix8-001 is covered by DES-fix8-001 via `satisfies`, but `src/fix8_mod/core.py`
has no `# implements:` annotation. `granularity_match` should warn that REQ-fix8-001
is under-specified (no direct or indirect coverage).
