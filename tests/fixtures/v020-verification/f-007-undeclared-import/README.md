## Defect: F-007 — Undeclared Python cross-module import

`src/mod_a/uses_b.py` imports from `mod_b`, but `programs.yaml` declares no
visibility from P1.SP1.M1 → P1.SP1.M2. `visibility_rule_enforcement` should
fire (warning in advisory mode, error in strict mode).
