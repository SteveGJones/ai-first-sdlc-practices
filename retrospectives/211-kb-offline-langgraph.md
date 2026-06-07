# Retrospective: kb-offline M0 — Foundation (#211)

## What we set out to do
Build and prove the four foundational contracts of the kb-offline backend before any
Ollama/LangGraph work: (1) claim-structured `Answer`/`Claim` with verifier-assigned entailment,
(2) journaled durable mutation with WAL ordering + monotonic fencing + create/extend CAS + recovery,
(3) resume-selection (`--resume`/latest-compatible, lifecycle states, stale-lock TTL+PID+fencing),
(4) the backend ownership boundary (backend = `generate`/`embed` only; pipeline owns
validation + mutation) — plus a minimal Anthropic/Fake `kb-offline` CLI proving it end-to-end.

## What went well
- **Two external review rounds before any code** turned a plausible-but-shaky spec into a sound one:
  the parity claim was made honest (shared core+prompts+one CLI pipeline; in-agent skills stay
  native for Max-token economics), "resume for free" was replaced with an explicit
  manifest+journal+fencing model, and `reduce`/`promote` were forced to return typed
  `MutationProposal`s validated by deterministic code rather than emitting raw files.
- **Subagent-driven TDD with proportionate review** worked: mechanical tasks got fast controller
  verification; the load-bearing tasks (validator, journaled commit, recovery, CLI) each got full
  two-stage spec+quality review, which caught real defects (below).
- **The foundation composes on the first integration run** — `test_m0_end_to_end` (extract → route →
  reduce → validate → commit → recover/reindex) passed without a single foundation unit needing rework.
- **Determinism held**: run IDs derive from a caller-supplied `--timestamp`; `time.time()` appears
  only inside lock methods — no wall-clock/random in pure logic.

## What was hard / what review caught
- **Critical YAML-frontmatter corruption** (`_render_page` used `f"{k}: {v}"`): a value with a colon
  (`title: "Cost: a study"`) produced invalid YAML in the durable output. Fixed to `yaml.safe_dump`
  (red→green regression test added).
- **Recovery gap (I1)**: a crash after the durable page write but before the `committed` journal
  record would leave a durable page the shelf-index never learned about. `recover()` now reindexes
  `staged`-with-existing-page targets (hash-guarded, idempotent), distinct from `staged`-without-page
  (incomplete).
- **Latent #208 bug surfaced by real contracts**: `route_extracts._target_key` used `"file" in target`
  (key-presence), but the `ExtractTarget` contract always serialises `"file": null` for new topics,
  so real extract output routed new topics to a `None` filename. Fixed to truthiness `target.get("file")`.
- **CLI masking foundation failures**: an unknown `--resume <id>` did side-effecting work then crashed
  with a masked traceback; all-rejected/all-conflict runs reported `completed` + exit 0. Fixed:
  validate the id up front; track rejected/conflict counts; set `completed_with_errors` + non-zero
  exit when nothing succeeded but work was attempted (spec's "non-zero only if nothing succeeded").
- **Environment hygiene**: pip/pytest had been running against Homebrew system Python (no venv). The
  user caught it; we created a project `.venv` and now thread `.venv/bin/python` through all runs.

## Lessons
- For LLM-writing pipelines: typed mutation *proposals* + a deterministic validator/committer; never
  let the model emit final files. (See [[feedback_llm_writing_pipeline_safety]].)
- "Resume for free" via a graph checkpointer is unsafe for side-effecting graphs — the manifest +
  journal is the source of run truth; fencing tokens make stale-lock reclaim *safe*.
- Real contract types flush out latent bugs in older deterministic code that hand-built test dicts hide.
- Always confirm the interpreter/venv early — system-Python installs are easy to do by accident.

## Test evidence
- M0 suite (10 files): **57 passed**. Broader kb suite (`-k kb`): **358 passed**. Full repo suite at
  final review: **844 passed**. All under the project `.venv`.
- Safety-critical coverage: fencing (`test_stale_fencing_token_fenced_out`), create/extend CAS
  conflicts, recovery of staged-with-page vs incomplete, validator adversarial rejections,
  YAML-escaping regression, resume-skip + unknown-resume fail-fast + partial-failure exit code.
- Validation gate green: flake8 clean on all kb-offline modules; feature-proposal check pass;
  prompt-parity check "OK"; no kb-offline files in technical-debt output.

## Deferred to M1+ (by design)
OllamaBackend, LangGraph graphs, `ingest-bulk`, full query path (`select`/`synthesize` + the
entailment verifier that assigns `entailment_status`), federation, embeddings accelerator, promotion
graph, the `[offline]` extra (langgraph/ollama). Also: wire `LibraryLock.heartbeat()` into the
long-running `ingest-bulk` loop (unused at M0; sub-second runs « 120s TTL, and fencing makes any
reclaim safe), and add reduce-phase resume tracking (M0 re-reduces all targets on resume; the MAP
skip is the expensive part).
