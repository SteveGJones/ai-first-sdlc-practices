# kb-offline eval release report — claude-code-baseline

**Pinned config:** `{'backend': 'claude-code (in-session subagents)', 'model': 'claude (Max plan)', 'runs': 1}`

| metric | min | mean | stddev | runs | pass |
|---|---|---|---|---|---|
| fact_recall | 0.85 | 0.9067 | 0.0000 | 0.907 | PASS |
| routing_recall | 0.9 | 1.0000 | 0.0000 | 1.000 | PASS |
| routing_precision | 0.8 | 0.9868 | 0.0000 | 0.987 | PASS |
| abstention_precision | 0.95 | 1.0000 | 0.0000 | 1.000 | PASS |
| abstention_recall | 0.9 | 1.0000 | 0.0000 | 1.000 | PASS |
| verifier_precision | 0.98 | 1.0000 | 0.0000 | 1.000 | PASS |
| verifier_recall | 0.95 | 1.0000 | 0.0000 | 1.000 | PASS |
| first_pass_json_validity | 0.95 | 1.0000 | 0.0000 | 1.000 | PASS |
| clean_published_support_rate | 1.0 | 1.0000 | 0.0000 | 1.000 | PASS |

**Safety floors (must = 1.0 every run):**
- invalid_mutation_rejection_floor: [1.0]
- citation_validity_floor: [1.0]
- post_repair_json_validity_floor: [1.0]

## Verdict: PASS

**Ollama-default recommendation:** claude-code-baseline clears both bars — recommend making Ollama the default backend.
