## Defect: F-007 — Undeclared Swift cross-module import

`src/mod_a/UsesB.swift` has `import ModB`, but `programs.yaml` declares no
visibility from P1.SP1.M1 → P1.SP1.M2. `GenericRegexExtractor` (Swift adapter)
should detect the edge and `visibility_rule_enforcement` should fire.
