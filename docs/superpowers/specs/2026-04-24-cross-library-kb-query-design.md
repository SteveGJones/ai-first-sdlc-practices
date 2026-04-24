# Cross-Library Knowledge Base Query — Design

**EPIC:** #164
**Branch:** `feature/164-cross-library-kb-query`
**Plugin:** `sdlc-knowledge-base`
**Scope:** v1 (phases A+B+C); phase D (RemoteAgentSource) deferred to a follow-up EPIC
**Status:** Design, awaiting implementation plan

---

## 1. Context

The `research-librarian` agent shipped in `sdlc-knowledge-base` (EPIC #105) can only query the current project's library. This design extends the plugin so a project can query **multiple external knowledge bases** — "corporate asset libraries" — alongside its own, with every finding attributed to its source library and with the local project's context used to frame how external libraries are interrogated.

The motivating scenario: a consultant working on a Brazilian semiconductor project needs to pull findings from a corporate semiconductor library accumulated across prior engagements (Dutch manufacturing, etc.). The findings are only useful through the lens of the current project's context — domain vocabulary, site constraints, the specific question being asked. This is not "dump external findings into the answer"; it is **"use local context to interrogate global libraries."**

Hard confidentiality isolation between concurrent NDA-bound engagements is **out of scope** and handled at the repo boundary: separate engagements live in separate repositories, each with its own activation list. The plugin does not attempt to enforce cross-client NDA boundaries.

## 2. Design decisions (settled)

Seven architectural questions were resolved during brainstorming:

| # | Decision | Rationale |
|---|---|---|
| 1 | Primary use case = corporate asset libraries + sequential reuse, framed by local project context | Amkor feedback + broader consulting workflow |
| 2 | Priming = question + local CLAUDE.md `[Knowledge Base]` section + local shelf-index terms | External libraries are queried *through* the lens of what the local project already knows |
| 3 | Configuration = user-scope registry (`~/.sdlc/global-libraries.json`) + per-project activation (`.sdlc/libraries.json`) | Keeps filesystem paths and (future) auth out of project-committed files; registers once, activates many |
| 4 | Default scope = local + all activated externals on every query; `--local-only` to suppress | Activation already signals intent; forcing a flag on every query is friction |
| 5 | Cross-library synthesis = allowed, with mandatory inline per-claim attribution | Synthesis is the differentiator; forbidding it loses the feature; attribution is structural |
| 6 | Format compatibility = `<!-- format_version: 1 -->` breadcrumb in shelf-index, LLM-flexible best-effort parsing | LLM handles mild format drift gracefully; header enables real versioning later without rework |
| 7 | v1 scope = phases A (foundation) + B (priming) + C (synthesis); phase D (RemoteAgentSource) deferred | A alone loses the differentiator; D needs a real remote endpoint to integrate with |

## 3. Architecture

### 3.1 LibrarySource abstraction

Every library (local or external) is modelled as a **LibrarySource** record with:

- `name` — string handle used for attribution output
- `type` — `filesystem` (v1) or `remote-agent` (schema-reserved, v2+)
- type-specific fields (for `filesystem`: absolute `path` to the library directory)

The local project's library is an **implicit source** with `name: "local"` and path pointing at the project's `library/` directory. This keeps the orchestrator uniform — no special-cased local branch.

### 3.2 Orchestration pattern

```
user query
    │
    ▼
┌─────────────────────────────────────────────────┐
│ kb-query preflight (in the skill)               │
│ - load global + project registries              │
│ - resolve activated sources → dispatch list     │
│ - add implicit local source                     │
└─────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────┐
│ Build priming bundle                            │
│ - user question                                 │
│ - local CLAUDE.md [KB] section excerpt          │
│ - local shelf-index terms (domain vocabulary)   │
└─────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────┐
│ Dispatch librarians in parallel                 │
│ (one Agent-tool message with N parallel calls)  │
│                                                 │
│ each librarian invocation:                      │
│   receives: framed question + priming + scope   │
│   reads: its scoped shelf-index only            │
│   deep-reads: 2-4 files within its scope        │
│   returns: findings tagged with source handle   │
└─────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────┐
│ Collect + render combined retrieval             │
│ (local first, externals alphabetical)           │
│ Apply attribution post-check (structural)       │
└─────────────────────────────────────────────────┘
    │
    ▼
  synthesis query? ──no──► return to user
    │
    yes
    ▼
┌─────────────────────────────────────────────────┐
│ Synthesis librarian call                        │
│ input: question + priming + all retrieval       │
│        findings (no file re-reads)              │
│ output: connected argument with inline          │
│         [handle] tags on every claim's          │
│         supporting evidence                     │
└─────────────────────────────────────────────────┘
    │
    ▼
return to user
```

### 3.3 Key architectural properties

- **Orchestration lives in the `kb-query` skill, not a new agent.** Dispatching N librarian calls via the Agent tool is a mechanical act; it doesn't need agent-level reasoning. No new agent files.
- **The `research-librarian` agent is unchanged in nature.** Its prompt gets a small extension to accept `scope` and `priming_context` parameters and to operate in "synthesise-across-sources" mode when requested. Its anti-hallucination discipline, its stateless design, and its two output formats stay identical.
- **Each librarian invocation has the same cognitive shape as today.** It reads one shelf-index, matches the query against it, deep-reads 2-4 files. Scaling to N libraries happens by invoking the librarian N times, not by asking one librarian to juggle N libraries.
- **Failure isolation is structural.** One source's failure produces a failure marker in the output; other sources still complete. The orchestrator collects what it can and is honest about what it couldn't.
- **Attribution integrity is a post-processing check, not a prompt rule.** The skill validates that every finding has a `Source library:` tag and every synthesis claim has an inline `[handle]`, before returning to the user.
- **Synthesis works only from retrieved findings, never from files.** The synthesis librarian call receives the collected retrieval output as input; it cannot re-read files or invent citations. Attribution is carried through automatically.

## 4. Components

### 4.1 New files

1. **`~/.sdlc/global-libraries.json`** — user-scope registry (see §5.1 for schema). Created by hand or by the new `kb-register-library` skill.

2. **`.sdlc/libraries.json`** — per-project activation (see §5.2 for schema). Human-editable. Lists which registered libraries this project taps into.

3. **`plugins/sdlc-knowledge-base/skills/kb-register-library/SKILL.md`** — optional skill for registering a library in the user-scope registry. Validates the path, checks for `_shelf-index.md`, reads its `format_version`, records the entry. Optional — hand-editing JSON is supported.

### 4.2 Modified files

4. **`plugins/sdlc-knowledge-base/skills/kb-query/SKILL.md`** — gains orchestration logic (§3.2). New preflight loads registries and resolves activated sources. New dispatch fans out parallel librarian calls. New attribution post-check runs before output. New synthesis branch for cross-library synthesis queries.

5. **`plugins/sdlc-knowledge-base/agents/research-librarian.md`** — prompt extension (additive, not a rewrite):
   - Accepts a `scope` parameter (absolute path); does not read outside it
   - Accepts a `priming_context` parameter (question + local `[KB]` excerpt + local shelf-index terms); uses it to bias matching against its own shelf-index
   - Accepts a `source_handle` parameter for attribution in its output
   - New "synthesise-across-sources" mode: receives pre-retrieved findings from multiple sources and produces an attributed synthesis, without re-reading files

6. **`plugins/sdlc-knowledge-base/skills/kb-rebuild-indexes/SKILL.md`** — always emits `<!-- format_version: 1 -->` as the first line of generated shelf-indexes.

7. **`plugins/sdlc-knowledge-base/skills/kb-rebuild-indexes/templates/shelf-index-example.md`** — template updated with the `format_version` header.

8. **`plugins/sdlc-knowledge-base/skills/kb-init/templates/claude-md-section.md`** — adds a short "External libraries" subsection documenting the registration + activation workflow and pointing at `kb-register-library`.

### 4.3 Files and behaviours intentionally unchanged

- `agents/agent-knowledge-updater.md` — ingest remains local-only. Corporate asset libraries are read-only from the local project's perspective.
- `skills/kb-ingest/SKILL.md`, `skills/kb-lint/SKILL.md`, `skills/kb-staleness-check/SKILL.md`, `skills/kb-validate-citations/SKILL.md`, `skills/kb-promote-answer-to-library/SKILL.md` — all remain local-only in v1. Cross-library equivalents, if ever needed, are follow-up work.
- The existing librarian's anti-hallucination rules, stateless design, two output formats, and clarifying-question behaviour.

## 5. Configuration schemas

### 5.1 `~/.sdlc/global-libraries.json`

```json
{
  "version": 1,
  "libraries": [
    {
      "name": "corporate-semiconductor",
      "type": "filesystem",
      "path": "/Users/steve/corporate/semi-library/library",
      "description": "Corporate semiconductor engagement findings, 2024-2026"
    }
  ]
}
```

**Validation rules:**

| Field | Rule |
|---|---|
| `version` | Integer. Currently `1`. Unknown versions → warning, best-effort load of `libraries`. |
| `libraries[].name` | String, unique within the file. Lowercase-kebab-case recommended, not enforced. Used as the source handle in attribution output. |
| `libraries[].type` | String, one of `filesystem` or `remote-agent`. v1 only dispatches `filesystem`; `remote-agent` entries load into the registry but are skipped at dispatch time with a clear warning. |
| `libraries[].path` | String, absolute path to the library *directory* (the one containing `_shelf-index.md`), not the repo root. Non-existent path at load time → warning, entry still loaded (drive may be unmounted); non-existent at dispatch time → failure marker. |
| `libraries[].description` | Optional human note. Ignored by the system. |

Absent file is normal. No registry means kb-query works as today (local only).

### 5.2 `.sdlc/libraries.json`

```json
{
  "version": 1,
  "activated_sources": [
    "corporate-semiconductor",
    "corporate-healthcare"
  ]
}
```

**Validation rules:**

| Field | Rule |
|---|---|
| `version` | Integer. Currently `1`. |
| `activated_sources` | Array of strings matching `libraries[].name` in the user-scope registry. Unresolved names → warning at query time, name skipped, query proceeds. |

Absent file is normal. No activation means kb-query runs local-only, exactly as today.

**Why this file is safe to commit to a client repo:** it contains only handle names, never filesystem paths. A client viewing `.sdlc/libraries.json` sees `corporate-semiconductor` as an opaque identifier; they do not see the operator's filesystem layout, and they do not learn that other corporate libraries exist.

### 5.3 Shelf-index `format_version` header

First line of every generated shelf-index:

```markdown
<!-- format_version: 1 -->
# Knowledge Base Shelf-Index

Generated by `/sdlc-knowledge-base:kb-rebuild-indexes`. ...
```

- HTML-comment form so the header is invisible when rendered but machine-readable.
- Librarian reads the first line and extracts the version.
- Missing header → treated as v1 silently (existing libraries predate the header).
- Unknown version → librarian proceeds with best-effort and notes the mismatch as a caveat in its findings.
- `kb-rebuild-indexes` always emits `<!-- format_version: 1 -->`. Users who rebuild once silently migrate to the header.

## 6. Data flow

### 6.1 Retrieval query

1. **Preflight.** Load `~/.sdlc/global-libraries.json` → `{name → source_record}` map. Load `.sdlc/libraries.json` → `activated_sources`. Resolve each activated name against the map; unknown names produce warnings and are skipped. Filter out `type: remote-agent` entries with a warning. Prepend implicit `local` source pointing at `<project>/library`. If the dispatch list is empty → error with `kb-init` recommendation.

2. **Build priming bundle.** Extract the local `[Knowledge Base]` section from the project's `CLAUDE.md` if present. Read `<project>/library/_shelf-index.md` and extract the union of `Terms:` fields across all entries (the local domain vocabulary). Assemble `{question, local_kb_config_excerpt, local_shelf_index_terms}`.

3. **Dispatch librarians in parallel.** For each source in the dispatch list, invoke `research-librarian` via the Agent tool. All invocations go out in a single orchestrator message (Claude's parallel tool-call mechanism). Each invocation's prompt includes the framed question, the priming bundle, the scope (absolute path + strict "do not read outside this path" constraint), and the source handle.

4. **Collect per-source findings.** Each librarian returns findings in the existing retrieval format, with each finding block augmented by a `**Source library**: <handle>` line inserted by the librarian itself (per prompt extension). A librarian returning "no evidence on this" for its scope produces a `[<handle>] library has no evidence on this topic` marker. A failed librarian call produces a `[<handle>] dispatch failed: <reason>` marker. Other sources are unaffected.

5. **Apply attribution post-check.** Structural validator ensures every finding block has a `Source library:` line. Findings failing the check are dropped with a warning (should never happen with a correctly-prompted librarian; this is a belt-and-braces guard).

6. **Render combined output.** Local source findings first, externals alphabetical by handle. Header summarises sources queried / with findings / skipped or failed. Return to user.

### 6.2 Synthesis query

Steps 1–5 as retrieval. Then:

7. **Synthesise across findings.** Detect synthesis via the existing librarian's heuristic (phrases like "build me the case for", "how should we think about"). Invoke `research-librarian` one more time in "synthesise-across-sources" mode. Prompt includes the original question, the priming bundle, and *all* collected per-source findings as input. The librarian produces a single connected argument. Every claim in the `Supporting evidence` list has an inline `[<handle>] <filename>` tag (plus original citation if the source finding had one). The `Caveats` section explicitly names cross-library spans and any library that had no evidence.

8. **Attribution post-check on synthesis.** Structural validator ensures every claim in `Supporting evidence` has an inline `[handle]` tag. A claim missing a tag causes the synthesis to be aborted and the retrieval output returned alone with an error block appended. Never silently published.

**Critical property of the synthesis step:** it works only from retrieval findings collected in step 4. The synthesis librarian has no file-reading capability in this mode — it receives findings as input and composes an argument. This means it cannot invent citations; it can only reuse provenance that already exists.

## 7. Error handling

Principle: **no single library failure kills a query.** Degrade gracefully with explicit markers.

| Layer | Condition | Behaviour |
|---|---|---|
| Registry load | Global registry absent | Empty external registry, no error |
| Registry load | Global registry malformed JSON | Warning, empty registry, query local-only |
| Registry load | Global registry unknown `version` | Warning, best-effort load |
| Registry load | Duplicate `libraries[].name` | Warning, first occurrence wins |
| Registry load | Project activation absent | Empty activation, query local-only |
| Registry load | Project activation malformed | Warning, empty activation, query local-only |
| Registry resolve | Activated name not in registry | Warning, skip, proceed |
| Registry resolve | Activated source has `type: remote-agent` | Warning ("RemoteAgentSource planned for future release, skipping"), skip, proceed |
| Source preflight | Source `path` does not exist | Failure marker `[<handle>] source path not accessible: <path>` |
| Source preflight | Source `path` exists but no `_shelf-index.md` | Failure marker with recommendation to run `kb-rebuild-indexes` in that library |
| Librarian invocation | Agent call fails (timeout, tool error) | Failure marker `[<handle>] librarian dispatch failed: <reason>` |
| Librarian output | Librarian says "no evidence on this topic" | Rendered as `[<handle>] library has no evidence on this topic` — normal behaviour, not a failure |
| Librarian output | Librarian notes `format_version` mismatch | Propagated to user output as caveat; findings still returned |
| Synthesis | Synthesis call fails | Retrieval output still returned; error block appended: "Synthesis step failed: <reason>" |
| Synthesis | Synthesis claim missing attribution | Synthesis aborted; retrieval output returned; error block appended |
| Local library | No local `library/` + no activated externals | Error: "No knowledge base available. Run kb-init or activate an external library." |
| Local library | No local `library/` but externals activated | Local omitted from dispatch list silently; externals proceed |

### 7.1 Attribution integrity — hard invariant

The one failure mode that must never silently happen: **a finding or claim published without a source handle.** This is a structural post-processing check run by the skill on the librarian's output before returning to the user:

- Every retrieval finding block has `**Source library**: <handle>` line, or it is dropped with a warning logged.
- Every synthesis supporting-evidence claim has inline `[<handle>]` tag, or the synthesis is aborted.

This closes the one gap where an LLM could produce confidentiality-sensitive output without provenance. It runs before *any* output reaches the user.

### 7.2 Explicitly not handled in v1

- Concurrent kb-query safety (reads are idempotent)
- Registry corruption auto-recovery (manual JSON repair is the v1 story)
- Stale external shelf-indexes (`kb-staleness-check` stays local-only)
- Network retry/timeout/backoff (N/A — filesystem only)

## 8. Testing approach

Heavy at the unit layer where deterministic mechanics live; integration tests mock the librarian Agent tool; a small end-to-end set runs the real librarian behind a gating env flag.

### 8.1 Unit tests (fast, deterministic)

- Registry loading: happy path, missing file, malformed JSON, unknown version, duplicate names.
- Activation resolution: happy path, unknown names, remote-agent type filtering, implicit-local inclusion, empty dispatch list error.
- Priming bundle construction: happy path, missing CLAUDE.md `[KB]` section, missing local shelf-index.
- Format-version parsing: header present (v1), header absent (legacy = v1), header unknown version.
- Attribution post-check: all findings tagged → pass; one finding untagged → dropped with warning; synthesis claim without inline handle → synthesis aborted.

### 8.2 Integration tests (fixture libraries, mocked librarian)

- Parallel dispatch: N activated sources → N parallel Agent calls in one orchestrator message (verify via mock).
- Dispatch order: local first, externals alphabetical.
- Retrieval failure degradation: one fixture path removed → failure marker, other sources return findings.
- No-shelf-index source: empty fixture directory → failure marker with recommendation.
- No-evidence source: mock returns "no evidence" → no-evidence marker, not a failure.
- Synthesis path: synthesis query → extra librarian call with all findings as input.
- Synthesis disabled: only one source returned findings → synthesis skipped, retrieval terminal.
- Synthesis failure fallback: mocked synthesis fails → retrieval output still returned with error block.
- Format-version mismatch caveat: fixture with `format_version: 99` → caveat propagated to user output.
- No sources error: no local + no activated externals → error with kb-init recommendation.

### 8.3 End-to-end tests (real librarian, gated behind env flag)

Five scenarios using tiny real fixture libraries:

1. Retrieval across two sources, both hit — combined attributed output.
2. Retrieval across two sources, one returns no evidence — one finding block, one no-evidence marker.
3. Synthesis across two sources — argument with inline `[handle]` tags on every supporting-evidence line, `Caveats` flags cross-library span.
4. Priming affects matching — same query with/without priming context; assert priming version returns more domain-relevant files.
5. Unmounted source — two activated, one path removed pre-test; failure marker for removed, findings from other.

### 8.4 Test fixtures

- `tests/fixtures/libraries/local-sample/` — typical project library (2 files + shelf-index)
- `tests/fixtures/libraries/corp-semi-sample/` — corporate asset library on EUV/cleanroom topics (2-3 files + shelf-index with `format_version: 1`)
- `tests/fixtures/libraries/corp-health-sample/` — corporate asset library on unrelated topics (for cross-library miss scenarios)
- `tests/fixtures/libraries/corp-legacy-no-header/` — shelf-index without `format_version` header
- `tests/fixtures/libraries/corp-future-version/` — shelf-index with `format_version: 99`
- `tests/fixtures/libraries/empty-dir/` — empty directory for the no-shelf-index failure case

## 9. Scope

### 9.1 In scope for v1 (this spec)

- Phase A — LibrarySource abstraction, global + project registries, FilesystemSource dispatcher, format_version breadcrumb, `kb-query` orchestration with parallel dispatch, mandatory source attribution on every finding
- Phase B — priming bundle (question + local CLAUDE.md `[KB]` + local shelf-index terms) passed to every external librarian invocation
- Phase C — cross-library synthesis via dedicated post-retrieval librarian call, mandatory inline per-claim attribution, structural post-check
- `kb-register-library` skill (optional registration helper)
- `kb-rebuild-indexes` emits `format_version: 1` header
- Updated CLAUDE.md template with External Libraries subsection
- Unit + integration + (gated) end-to-end test coverage per §8

### 9.2 Out of scope for v1 (deferred)

- **Phase D — RemoteAgentSource.** Separate EPIC. Needs wire contract, auth model, retry/timeout design, and a real endpoint to integrate with. Schema reserves `type: remote-agent` so v1 data is forward-compatible.
- Cross-library ingest (`kb-ingest` stays local-only)
- Cross-library lint (`kb-lint` stays local-only)
- Cross-library staleness checks (`kb-staleness-check` stays local-only)
- Cross-library citation validation (`kb-validate-citations` stays local-only)
- `kb-deregister-library` / `kb-list-libraries` helper skills (hand-editing JSON is fine)
- Registry corruption auto-recovery / backup rotation
- Performance tuning for N > 5 activated libraries (add load tests if it becomes a concern)
- Hard client-isolation enforcement inside the plugin (handled at repo boundary — documented, not enforced in code)

### 9.3 Mapping to #164 sub-features

The EPIC body listed six original sub-features (design document, `--library-path` parameter, external library validation, `.sdlc/libraries.json` registry, `--federated` flag, source attribution). The design above restructures these into three phases (A+B+C) for v1 and one deferred phase (D). Before implementation, #164 should be re-decomposed against this design — likely three new sub-feature issues for phases A, B, C and one follow-up EPIC placeholder for D.

## 10. Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Librarian's prompt extension grows too complex | Agent behaves inconsistently, hallucinations creep in | Keep the extension additive (new parameters, not rewritten behaviour). The stateless, shelf-index-first, deep-read-2-4 pattern stays exactly as today. New behaviour is "you now know about scope and priming" — not a new cognitive shape. |
| Parallel dispatch overwhelms orchestrator context window | Skill can't fit N librarian responses + original context | N in practice is 2-5 (local + a handful of corporate libraries). Each librarian response is bounded by the existing retrieval format (~few hundred tokens). If this becomes a problem, streaming or batched collection is a bounded follow-up. |
| Synthesis librarian invents connections not supported by the findings | Confidentiality-adjacent failure — cross-library synthesis could blend sources misleadingly | Synthesis works only from retrieval findings, not files. Structural attribution post-check catches any claim without a handle tag. Librarian's existing anti-hallucination rules extend naturally. Worst case: synthesis aborts, retrieval output returned alone. |
| Corporate library's filesystem path changes and breaks all dependent projects | Every project activation silently breaks | Registration is explicit; failure produces a clear warning (not a silent omission). `kb-register-library` could be re-run to update the path. Mitigation in the failure marker's recommendation text. |
| Format drift between corporate libraries and local library | Librarian outputs become inconsistent | `format_version` breadcrumb is primarily a signal to the LLM about what to expect. LLM-based parsing is flexible by design; structural mismatches surface as caveats. Hard incompatibility is documented as a future concern requiring real adapters. |
| User commits `.sdlc/libraries.json` to a client repo with sensitive handle names | Handle names leak engagement details | Handle names are chosen by the operator; the documentation should recommend generic names (`corporate-semi` not `acme-corp-2024-confidential`). Client repos should be reviewed before sharing. This is a policy concern, not enforceable in code. |
| Priming bundle pulls in project-sensitive CLAUDE.md content | Local project context sent to external librarians that run against corporate libraries | v1 dispatches only to local FilesystemSource (no network). The priming bundle is shared with in-process librarian invocations that read local filesystem. No external transmission. When RemoteAgentSource lands in v2, the priming bundle's contents become a live transmission concern requiring a separate design pass. |

## 11. Open questions for implementation plan

These are tactical and belong in the writing-plans output, not in this design:

- Python helper module structure — new `kb_query_orchestrator.py` or extend an existing module? Location under the skill directory vs under `tools/`?
- How to detect synthesis queries in the skill — reuse the librarian's heuristic, mirror it, or ask the user? (The existing librarian detects it internally; the skill needs its own detection to decide whether to run the synthesis step.)
- Exact format of the `scope` and `priming_context` parameters in the librarian's dispatch message (JSON block? sectioned markdown? both work).
- Whether `kb-register-library` needs its own tests or whether schema validation of the registry file is sufficient.
- Whether to add a `--local-only` flag now or defer until a user asks for it.

## 12. References

- EPIC #164 body (GitHub)
- `plugins/sdlc-knowledge-base/agents/research-librarian.md` — existing agent behaviour
- `plugins/sdlc-knowledge-base/skills/kb-query/SKILL.md` — existing skill
- `plugins/sdlc-knowledge-base/skills/kb-init/templates/claude-md-section.md` — KB configuration pattern
- `research/sdlc/` — Agentic SDLC research referenced by the starter pack library
- Amkor AI Strategy engagement feedback (2026-04-23), `tmp/sdlc-feedback.md` item F4
