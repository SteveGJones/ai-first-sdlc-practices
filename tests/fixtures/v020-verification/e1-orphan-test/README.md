## Defect: E1 — Orphan TEST record

TEST-fxe1-001 is declared in the test-spec but no source file has
`# implements: TEST-fxe1-001`. The `orphan_ids` validator (E1 widened in v0.2.0)
should emit a warning that TEST-fxe1-001 is never cited.
