# Local models for agentic coding: is OpenCode viable, and is 32GB the problem?

**Date:** 2026-07-31
**Context:** follow-up to issue #237 (`research/poker-capstone/`), after both
auditioned local MLX models failed P1 and OpenCode (Path A) was rejected for
code-reproduction work.
**Question asked:** has *anyone* got on-laptop models working well in OpenCode,
and what were their tricks? If the answer is "you need a 64GB or 128GB
machine", that is a finding in itself.

---

## Method and provenance

Four parallel research agents (Sonnet) were dispatched, each on a distinct
angle so they would not duplicate work: OpenCode's local-model support, the
specific code-corruption failure mode, RAM requirements, and alternative
harnesses. Each was instructed to label evidence strength, to report negative
results plainly rather than pad, and never to fabricate a source.

**Verification discipline used here.** Agent-supplied citations were *not*
taken at face value — the same rule this project applies to judge verdicts.
Every load-bearing source below was re-checked directly (GitHub API for issue
state/date/title, direct fetch for the benchmark). Sources that were **not**
independently re-checked are marked *(agent-reported)* and should be treated
as leads, not established fact.

That re-check found three discrepancies worth recording, all in the direction
of agents overstating currency:

- `llama.cpp#20359` is **CLOSED** (2026-03-10). Presented by an agent as live
  evidence; it is a fixed issue. Still valid as evidence the failure mode is
  real, but not an open defect.
- `opencode#5591` is **CLOSED** and dates from **2025-12-15**, older than the
  "last 12 months" framing implied.
- `qwen-code#707` and `Qwen3-Coder#531` are both from **September 2025**, also
  older than implied.

---

## Direct answers

**1. Has anyone got local models working well in OpenCode? No — not cleanly.**
Across all four agents, no source demonstrates an unmodified, working OpenCode
+ local-model agentic session. The strongest positive case (96GB Mac,
Qwen3-Coder-30B-A3B at **8-bit**) still required hand-patching
`tokenizer_config.json` to get tool calls working. Others report "awkward"
tool-call output or confine themselves to single-file/SQL tasks. No source ran
a long, unattended, multi-step agentic session on a 14B–30B local model
through OpenCode and reported a clean pass. *(agent-reported)*

**2. Do we need 64GB or 128GB? Yes for comfort — but RAM would not have fixed
our failures.** See "Hardware" below. This is the nuance that matters: the two
problems we actually hit are not memory-bound.

**3. The unexpected answer: the harness may matter more than the model.** In
the one controlled cross-harness benchmark available, OpenCode places last
once corrected for a scoring artefact, while two lighter harnesses run the
same class of local model substantially better.

---

## Finding 1 — Our 11K-token prompt is a known, open OpenCode defect

We measured a 2 KB task inflating to an ~11,000-token request. That is not our
misconfiguration.

> **[anomalyco/opencode#11995](https://github.com/anomalyco/opencode/issues/11995)**
> — "Tool descriptions consume excessive tokens in system prompt".
> **VERIFIED: open**, created 2026-02-03.

The issue reports tool-description files alone costing ~3,000–4,000 tokens per
message and proposes a ~69% reduction. It remains unfixed.

Note also that the repository moved: `sst/opencode` → **`anomalyco/opencode`**.
Old links redirect or go stale. *(agent-reported, but consistent with the API
responding on the new path.)*

## Finding 2 — The corruption is Qwen-family × payload size

Our symptom: emitted Python containing literal `\"\"\"` instead of `"""`, so it
would not compile — while the *same* models, called directly with a plain
prompt, produced clean code. Reproduced on both a 7B and a 14B Qwen coder.

This is a documented bug class, concentrated in the Qwen family:

| Source | State | Relevance |
|---|---|---|
| [qwen-code#707](https://github.com/QwenLM/qwen-code/issues/707) "Incorrect escaping of quotes in generated code" | **VERIFIED: closed**, 2025-09-24 | Near-exact symptom — docstrings as `\"\"\"` |
| [Qwen3-Coder#531](https://github.com/QwenLM/Qwen3-Coder/issues/531) "annoying newline issue" | **VERIFIED: closed**, 2025-09-27 | `"text"` → `\"text\"` during `write_file`; scoped to the tool-use path |
| [llama.cpp#20359](https://github.com/ggml-org/llama.cpp/issues/20359) | **VERIFIED: closed**, 2026-03-10 | Title states the trigger explicitly: *"…invalid JSON (mixed single/double quotes) **with large payloads**"*, on Qwen3-14B and Qwen3-30B-A3B |

`llama.cpp#20359` is the key one: corruption appears **only above a payload-size
threshold**, with small payloads clean on the identical model and schema. Chain
that to Finding 1 and the mechanism is coherent — **OpenCode's known prompt
bloat pushes Qwen models past the size at which they begin corrupting emitted
code.**

**Caveat on scope.** `#20359` concerns tool-call *arguments* being invalid JSON.
Our symptom is code inside a fenced block being over-escaped. Related and
plausibly the same underlying behaviour, but not identical — do not treat this
as a proven root cause.

**Reported fix, untried by us:** community-patched Jinja chat templates that
replace the official Qwen ones, explicitly targeting quote-corruption and
JSON-string truncation, and naming agent harnesses as the use case.
*(agent-reported; not verified.)*

**Model-family scope.** Evidence is concentrated entirely in Qwen. No reports
found for Devstral, Codestral, DeepSeek-Coder or GLM — which is **absence of
evidence, not evidence of absence**.

## Finding 3 — Hardware: 64GB is the honest floor, 128GB the maintainers' bar

*(RAM-tier table is agent-reported from secondary sources; treat as directional.)*

| Tier | Verdict |
|---|---|
| 16GB | 7–8B only; not recommended for real agentic work |
| 32GB | 14B dense workable **in isolation**; "thrashes with browser and IDE alongside" |
| 48GB | 32B dense / 30B-A3B MoE comfortably |
| **64GB** | Where accounts stop describing workarounds — *"good enough for serious development"* |
| **128GB** | Where mlx-lm maintainers stop warning about crash risk |

**But RAM is not what broke our runs.** A **96GB Mac Studio M3 Ultra** hit a
full kernel panic from the same unbounded-cache bug (Finding 4). The corruption
is model/harness-driven. Buying RAM would have delayed one failure and left the
other untouched.

Two supporting details *(agent-reported, computed from HF configs — not
independently re-derived)*:

- **MoE helps less than its headline implies.** All 128 experts must be
  resident — 17.2GB at 4-bit — so the win is compute, not memory. Sources place
  Qwen3-Coder-30B-A3B as a good fit for 48–64GB, not 32GB.
- **KV-cache cost is driven by GQA head count, not parameter count.**
  Qwen2.5-14B has 8 KV heads (~188 MiB/1000 tokens fp16 → ~2.06 GiB at our 11K
  request); Qwen3-Coder-30B-A3B has only 4 KV heads, so roughly *half* the
  per-token KV cost despite being 30B total.
- Apple Silicon defaults the GPU working set to roughly 75% of unified memory;
  `sudo sysctl iogpu.wired_limit_mb=<MB>` raises it. Leave 8–16GB for the OS.

## Finding 4 — Our July kernel panics were probably this bug

`RESTART-PROMPT.md` records four kernel panics on this machine (2026-07-26/27)
in `IOGPUGroupMemory.cpp:528` and `IOGPUMemory.cpp:550`, attributed at the time
to "large dense models under memory pressure" and considered resolved by an OS
update.

> **[ml-explore/mlx-lm#883](https://github.com/ml-explore/mlx-lm/issues/883)**
> — "mlx_lm.server causes macOS kernel panic (**IOGPUMemory** crash) due to
> **unbounded memory growth**". **VERIFIED: closed**, created 2026-02-12.
>
> Body (verified): Qwen3-Coder-30B-A3B-Instruct-8bit on a Mac Studio M3 Ultra,
> **96GB**, macOS 26.3, mlx-lm 0.30.6 — *"caused a full macOS kernel panic
> after the KV cache grew unboundedly during an agentic coding session (~58k+
> tokens context). The system crashed and rebooted — not a process termination,
> but a kernel-level panic in `IOGPUMemory.cpp`."*

Same kernel subsystem, same cause class, same model family, an adjacent mlx-lm
version. **This is a strong candidate re-interpretation of our July panics: not
"large models under memory pressure", but unbounded KV/prompt-cache growth.**

Two consequences:

1. Our `--prompt-cache-size 2` fix — applied for an unrelated OOM — likely
   addresses the panic class too.
2. **Bounding the cache is necessary at every RAM tier**, not a 32GB
   workaround. 96GB only delays it.

Stated as a hypothesis, not a conclusion: our panic reports carry no model
strings, so attribution remains circumstantial (as already recorded in
`RESTART-PROMPT.md`).

## Finding 5 — OpenCode is measurably the weakest mainstream harness here

**[harness-bench](https://neuralnoise.com/2026/harness-bench-wip/)**, published
**28 Apr 2026** — 17 model-quantisations × 5 harnesses × 16 tasks across seven
languages = **1,360 runs**, on a single M3 Max / 128GB laptop.
**VERIFIED by direct fetch.**

| Harness | Pass rate | Avg time/task |
|---|---|---|
| pi | **76.9%** | 163 s |
| qwen | 75.0% | 191 s |
| claude | 66.2% | 306 s |
| **opencode** | 63.8% | 271 s |
| aider | 62.5% | 384 s |

Verified quote: *"Across 14 distinct (model, task) cells, `opencode` either ran
`bash <repo>/tasks/<id>/test.sh <workspace>` directly…or read the contents of
the hidden `test.sh` file."* — of those, **13 passed**. Correcting for that
would move OpenCode to last.

**Author's caveat, quoted verbatim:** *"These are very preliminary findings –
some of the questions below probably deserve a careful re-run before I'd trust
the rankings to two decimal places."* Single author, WIP, sandbox not hardened
against peeking for any harness. **Treat the ordering as directional.**

Architectural factor most repeatedly implicated *(agent-reported)*: system
prompt / tool-schema size. Pi's authors credit its lead to a deliberately
minimal system prompt and a 4-tool core. Roo Code has its own issue about
building ~200KB prompts; OpenHands documents needing ≥22k context just to fit
its system prompt. Notably **no harness surveyed uses grammar-constrained
decoding** for tool calls — an unexploited mitigation.

**Aider is not a safe fallback** despite its no-tool-calling design: it placed
last on raw pass rate and was slowest.

---

## Unresolved conflict between agents

Two agents read **[opencode#5591](https://github.com/anomalyco/opencode/issues/5591)**
("Quotes in code getting stripped in model output", **VERIFIED: closed**,
2025-12-15) in opposite ways:

- One reported the thread showed *mitmproxy evidence that quotes were present
  on the wire and missing only in OpenCode's rendering* — i.e. a display bug,
  on a **cloud** Claude/OpenRouter model, not our symptom.
- The other cited it as the strongest evidence that the compile-breaking
  corruption is OpenCode's fault.

**I did not resolve this from the thread itself.** The title favours the second
reading; the mitmproxy detail favours the first. Either way its applicability
is doubtful: it is a cloud-model report, whereas our corruption was verified by
*decoding the JSON payload* — the escaping was in the data, not the display.

**Recorded as unresolved.** It should not be cited as settled evidence in
either direction without someone reading the thread.

---

## What this means for #237

The rejection of Path A (OpenCode) **stands, and is better supported than when
we made it** — but the stated reason needs refining. It is not "OpenCode is
broken". It is the compound of:

1. OpenCode's known, open prompt-bloat defect (#11995), pushing requests past
2. a Qwen-family escaping weakness that is payload-size-triggered (#20359), on
3. `mlx_lm.server`, whose tool-calling the MLX author himself describes as
   "basically broken" *(agent-reported)*.

Two of those three have known mitigations we never tried. That matters, because
our merged write-up implies a more final verdict than the evidence supports.

**Our 14B was also below the informal community floor** for reliable agentic
tool use, put at **30–32B @ Q4** *(agent-reported, informal consensus)*, with
7–14B repeatedly flagged as unreliable at tool-calling. This is consistent with
it failing P1 — though P1 is a judged-document phase requiring no tool use at
all, so the floor does not explain that particular failure.

Also relevant to our own benchmark design: harness-bench caught OpenCode
**reading the hidden grading script**. Worth confirming that a submission run
through our capstone harness cannot reach
`research/poker-capstone/harness/oracle.py`, the scenario definitions, or
`research/poker-capstone/docs/P1-GROUND-TRUTH-FACTS.md`.

## Open experiments, cheapest first

1. **Swap the model, hold the harness.** Run the same balanced-brackets item
   through OpenCode with `Devstral-Small-2-24B` (already cached). Separates
   "Qwen family" from "OpenCode". ~1 minute.
2. **Set `limit.context` / `limit.output`.** Never configured; local models are
   absent from OpenCode's registry so context defaults to **0** and compaction
   never fires ([#31433](https://github.com/anomalyco/opencode/issues/31433),
   **VERIFIED: open**, 2026-06-08).
3. **Try a patched Jinja chat template** for the Qwen models.
4. **Swap the harness, hold the model.** Pi or Qwen Code CLI.
5. **Confirm mlx-lm 0.31.3 includes the tool-call fix** (PR #711) — not checked.

## Confidence and gaps

- **High confidence:** every GitHub issue cited above (state, date, title
  verified via API); the harness-bench figures, caveats and publication date
  (verified by direct fetch); the mlx-lm#883 body.
- **Medium confidence:** the harness ranking itself — one author, WIP, self-
  declared provisional, sandbox not hardened; Cline, Roo Code, Goose, Zed,
  Continue and Crush were not in it at all.
- **Low confidence / unverified:** the RAM-tier table and KV arithmetic
  (agent-computed, secondary sources); the "30–32B floor" consensus (informal);
  the Awni Hannun MLX gist and all blog-based success reports.
- **Material gap:** no source tested any of these harnesses against
  **`mlx_lm.server`** specifically — community guides assume Ollama/LM Studio/
  GGUF. MLX-server API-shape edge cases therefore remain an unisolated
  confounder in our own results.
- **Material gap:** no official OpenCode-maintainer statement on local-model
  support quality or a recommended minimum model size was found.
- Our own characterisation — reproduced on both 7B and 14B, isolated to
  code-block content, clean under plain chat — was judged **more granular than
  anything published**, and may be worth filing upstream.
