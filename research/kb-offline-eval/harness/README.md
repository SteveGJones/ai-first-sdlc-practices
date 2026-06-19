# Eval audit harness (#211)

Auditable evidence for `../2026-06-18-gemma-ratification-findings.md`.

- `diagnose_gemma.py` — runs the REAL LangGraph query pipeline (`OllamaBackend gemma4:12b`)
  over N evidence questions and dumps a per-stage trace. Used to find the `fact_recall=0.000`
  root cause. (The release runner now writes equivalent traces by default — see
  `../trace-*.jsonl`.)
- `baseline_score.py` — scores the **Claude Code agentic reference** outputs on the SAME
  harness (`ground_claim`/`publish`/`harness`) as gemma. NOT the `AnthropicBackend` path.
- `claude-baseline-outputs/` — the structured outputs from the 9 Claude Code subagents
  (8 question slices + 1 verifier), model = Claude Code subagents pinned to `sonnet`.

**Reference identity & timing caveats:** the reference is Claude Code subagents (model
`sonnet`), run in parallel, writing final structured JSON — it does NOT exercise the
`AnthropicBackend` prompts/schema/repair-ladder/orchestration, and its per-question
latency (parallel) is NOT comparable to the sequential pipeline. Treat its score as an
agentic-reference upper bound, not a measurement of `claude-sonnet-4-6` via the cloud backend.
