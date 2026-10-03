## Defect: E2 — Unannotated public function

`src/feature.py` defines `calculate_something()` with no `# implements:` annotation.
`forward_annotation_completeness` should report this function as missing an annotation.
The declared module path is `src/` — tests must pass file paths starting with `src/`
(or absolute paths where the prefix matches).
