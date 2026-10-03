# Cross-Library KB Query — Phase B Priming Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Activate the priming bundle scaffolded in Phase A so the local project's CLAUDE.md `[Knowledge Base]` section and shelf-index terms actively bias external librarian queries. Per spec §3.3 (priming as a key architectural property) and §6.1 step 2 (data flow).

**Architecture:** Phase A built the `PrimingBundle` dataclass, the builder, and the orchestrator's `priming` parameter. Phase B adds (a) a `format_dispatch_prompt` helper in the orchestrator that renders the priming bundle into the exact `SCOPE: / SOURCE_HANDLE: / PRIMING_CONTEXT:` structure the librarian expects, (b) librarian-prompt instructions for actively using the priming context to bias term-matching, (c) an integration test proving priming flows end-to-end through the dispatcher contract.

**Tech Stack:** Python 3.10+, pytest. No new external dependencies.

**Spec:** `docs/superpowers/specs/2026-04-24-cross-library-kb-query-design.md`
**Issue:** #168 (phase B of EPIC #164)
**Branch:** `feature/164-cross-library-kb-query` (continues from Phase A)

---

## Critical lesson from Phase A regression (apply to every task in this plan)

**Edit root sources, then sync to plugin-dir via release-plugin.** Phase A's Tasks 9, 10, 12, 13 edited `plugins/sdlc-knowledge-base/...` files directly. Task 14 ran release-plugin (which copies root→plugin-dir per `release-mapping.yaml`), and the sync silently wiped those edits because root sources hadn't been updated. Commit `557d521` restored both layers.

**For every task in this plan that touches a file packaged via release-mapping.yaml:**

1. Identify whether the file has a root source (look at `release-mapping.yaml` for the source path)
2. Edit the **root source** (e.g., `skills/kb-query/SKILL.md`, NOT `plugins/sdlc-knowledge-base/skills/kb-query/SKILL.md`)
3. Mirror the change to the plugin-dir copy via `cp` (or run `/sdlc-core:release-plugin` if a slash command is available — but `cp` is reliable inside a subagent)
4. Verify with `python3 tools/validation/check-plugin-packaging.py` — must report 12 plugins verified

For files that live ONLY in the plugin-dir (Python scripts under `plugins/sdlc-knowledge-base/scripts/`, the `kb-register-library` skill, etc.), edit them in place. The release-mapping has them as `source: plugins/sdlc-knowledge-base/scripts/...` (no separate root source).

This is captured in `memory/feedback_release_plugin_sync.md`.

---

## File structure

**Files to modify:**

| File | Change | Root source? |
|---|---|---|
| `plugins/sdlc-knowledge-base/scripts/orchestrator.py` | Add `format_dispatch_prompt(source, question, priming)` helper | No (in-plugin) |
| `tests/test_kb_orchestrator.py` | Add tests for `format_dispatch_prompt` and end-to-end priming flow | N/A (test file) |
| `agents/knowledge-base/research-librarian.md` + `plugins/sdlc-knowledge-base/agents/research-librarian.md` | Replace "phase A: optional, phase B will activate" caveat with active-use instructions | YES — root source first |
| `skills/kb-query/SKILL.md` + `plugins/sdlc-knowledge-base/skills/kb-query/SKILL.md` | Update Step 3 to use `format_dispatch_prompt` helper instead of inline templating; remove phase B deferral note | YES — root source first |
| `plugins/sdlc-knowledge-base/scripts/priming.py` | Update module docstring to note phase B activation | No (in-plugin) |

**No new files** — Phase B is activation, not new abstractions.

---

## Task 1: Add `format_dispatch_prompt` helper in orchestrator

**Files:**
- Modify: `plugins/sdlc-knowledge-base/scripts/orchestrator.py`
- Modify: `tests/test_kb_orchestrator.py`

The helper renders a `LibrarySource` + question + optional `PrimingBundle` into the exact text the librarian expects. Pure function, easy to test.

- [ ] **Step 1: Write failing tests**

Append to `tests/test_kb_orchestrator.py`:

```python
from sdlc_knowledge_base_scripts.orchestrator import format_dispatch_prompt
from sdlc_knowledge_base_scripts.priming import PrimingBundle


def test_format_dispatch_prompt_with_full_priming() -> None:
    source = LibrarySource(name="corp-semi", type="filesystem", path="/lib/corp-semi")
    priming = PrimingBundle(
        question="what about EUV cleanroom",
        local_kb_config_excerpt="This project uses the knowledge base for semiconductor research.",
        local_shelf_index_terms=["semiconductor", "brazilian-fab", "alpha"],
    )
    prompt = format_dispatch_prompt(source=source, question="what about EUV cleanroom", priming=priming)

    # Check exact structural elements per librarian agent spec
    assert "SCOPE: /lib/corp-semi" in prompt
    assert "SOURCE_HANDLE: corp-semi" in prompt
    assert "PRIMING_CONTEXT:" in prompt
    # Priming JSON should contain the bundle's fields
    assert "semiconductor" in prompt
    assert "brazilian-fab" in prompt
    assert "This project uses the knowledge base" in prompt
    # Question is present
    assert "what about EUV cleanroom" in prompt
    # The do-not-emit-separators instruction is present (Task 6/8 contract)
    assert "---" in prompt and "horizontal rules inside a finding" in prompt


def test_format_dispatch_prompt_without_priming() -> None:
    source = LibrarySource(name="local", type="filesystem", path="/proj/library")
    prompt = format_dispatch_prompt(source=source, question="hello", priming=None)

    assert "SCOPE: /proj/library" in prompt
    assert "SOURCE_HANDLE: local" in prompt
    # Without priming, PRIMING_CONTEXT line should be absent OR explicitly null
    # We assert absent — minimal noise when no priming is configured
    assert "PRIMING_CONTEXT:" not in prompt
    assert "hello" in prompt


def test_format_dispatch_prompt_with_empty_priming_bundle() -> None:
    """A priming bundle with no excerpt and no terms should still emit a header,
    so the librarian knows the bundle was attempted (vs absent entirely)."""
    source = LibrarySource(name="local", type="filesystem", path="/proj/library")
    priming = PrimingBundle(
        question="hello",
        local_kb_config_excerpt="",
        local_shelf_index_terms=[],
    )
    prompt = format_dispatch_prompt(source=source, question="hello", priming=priming)

    assert "SCOPE: /proj/library" in prompt
    assert "SOURCE_HANDLE: local" in prompt
    # PRIMING_CONTEXT is present but with empty fields — still informational to librarian
    assert "PRIMING_CONTEXT:" in prompt
    # JSON should serialise empty values
    assert '"local_kb_config_excerpt": ""' in prompt
    assert '"local_shelf_index_terms": []' in prompt


def test_format_dispatch_prompt_json_is_valid() -> None:
    """The PRIMING_CONTEXT block must contain valid JSON the librarian can parse."""
    import json
    import re
    source = LibrarySource(name="x", type="filesystem", path="/x")
    priming = PrimingBundle(
        question="q",
        local_kb_config_excerpt="line1\nline2",  # multi-line content
        local_shelf_index_terms=["term-with-hyphen", "term with space"],
    )
    prompt = format_dispatch_prompt(source=source, question="q", priming=priming)
    # Extract the JSON block — must round-trip via json.loads
    match = re.search(r"PRIMING_CONTEXT:\s*\n(\{.*?\n\})", prompt, re.DOTALL)
    assert match is not None, f"PRIMING_CONTEXT JSON block not found in:\n{prompt}"
    parsed = json.loads(match.group(1))
    assert parsed["local_kb_config_excerpt"] == "line1\nline2"
    assert parsed["local_shelf_index_terms"] == ["term-with-hyphen", "term with space"]
```

- [ ] **Step 2: Run tests — verify they fail**

Run from repo root: `python3 -m pytest tests/test_kb_orchestrator.py::test_format_dispatch_prompt_with_full_priming -v`
Expected: FAIL with `ImportError: cannot import name 'format_dispatch_prompt'`

- [ ] **Step 3: Implement `format_dispatch_prompt`**

Append to `plugins/sdlc-knowledge-base/scripts/orchestrator.py` (above the existing helpers, near the top after the dataclass declarations):

```python
import json as _json


def format_dispatch_prompt(
    source: LibrarySource,
    question: str,
    priming: Optional[PrimingBundle],
) -> str:
    """Render the dispatch message a research-librarian invocation should receive.

    Output structure per librarian agent prompt spec:
        SCOPE: <source.path>
        SOURCE_HANDLE: <source.name>
        PRIMING_CONTEXT: <json>     (only when priming is provided)

        Question: <question>

        <closing instruction lines>

    The librarian's prompt extension (see agents/knowledge-base/research-librarian.md)
    documents the expected structure and the active-biasing semantics that consume
    PRIMING_CONTEXT.
    """
    lines: list[str] = []
    lines.append(f"SCOPE: {source.path}")
    lines.append(f"SOURCE_HANDLE: {source.name}")
    if priming is not None:
        priming_json = _json.dumps(
            {
                "local_kb_config_excerpt": priming.local_kb_config_excerpt,
                "local_shelf_index_terms": priming.local_shelf_index_terms,
            },
            indent=2,
        )
        lines.append("PRIMING_CONTEXT:")
        lines.append(priming_json)
    lines.append("")
    lines.append(f"Question: {question}")
    lines.append("")
    lines.append(
        f"Read the shelf-index at {source.path}/_shelf-index.md, identify the 2-4 "
        "most relevant library files for the question, deep-read only those, and "
        "return findings in the retrieval format. Every finding block must include "
        f"a **Source library**: {source.name} line (see your agent prompt)."
    )
    lines.append("")
    lines.append(
        f"Do not read any files outside {source.path}. Do not emit --- horizontal "
        "rules inside a finding block (they are treated as structural separators "
        "by the post-check tokenizer)."
    )
    return "\n".join(lines)
```

- [ ] **Step 4: Run tests — verify all pass**

Run: `python3 -m pytest tests/test_kb_orchestrator.py -v`
Expected: 9 tests pass (5 existing + 4 new).

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/orchestrator.py tests/test_kb_orchestrator.py
git commit -m "feat(kb): add format_dispatch_prompt helper (phase B, #168)

Pure function that renders a LibrarySource + question + optional
PrimingBundle into the exact dispatch message the research-librarian
expects (SCOPE / SOURCE_HANDLE / PRIMING_CONTEXT structure).

JSON-serialises priming bundle so multi-line excerpts and special
characters round-trip safely. Empty bundles still emit a header so
the librarian sees the attempt; absent priming omits the field
entirely.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 2: Update research-librarian prompt for active priming use

**Files:**
- Modify root: `agents/knowledge-base/research-librarian.md`
- Mirror to plugin: `plugins/sdlc-knowledge-base/agents/research-librarian.md`

Replace the phase A "optional, phase B will activate" caveat with concrete active-use instructions. The librarian should now actively use priming context to bias term-matching.

- [ ] **Step 1: Read the current prompt's PRIMING_CONTEXT description**

Run: `grep -n -B 1 -A 10 "PRIMING_CONTEXT" agents/knowledge-base/research-librarian.md`

Look for the bullet that currently reads:

> `PRIMING_CONTEXT:` — a JSON object passed in the dispatch message that may contain `local_kb_config_excerpt` (the project's CLAUDE.md [Knowledge Base] section) and `local_shelf_index_terms` (a list of domain vocabulary terms from the local project's shelf-index). Use these to bias your term-matching against your scoped shelf-index — if the local project's vocabulary includes terms you also have in your shelf-index, lean toward those matches. In phase A of EPIC #164, this parameter is passed but its use is optional; phase B will enable active biasing.

- [ ] **Step 2: Replace the bullet with the active-use form**

In `agents/knowledge-base/research-librarian.md`, find the `PRIMING_CONTEXT:` bullet (it's inside the "## Dispatch message parameters" section) and replace its body so it reads:

```markdown
- `PRIMING_CONTEXT:` — a JSON object passed in the dispatch message containing
  `local_kb_config_excerpt` (the project's CLAUDE.md [Knowledge Base] section,
  if present) and `local_shelf_index_terms` (a list of domain vocabulary terms
  from the local project's shelf-index). Use these as active framing for your
  retrieval against the scoped shelf-index:

    1. **Term overlap biases match selection.** When ranking candidate library
       files in your scoped shelf-index, prefer files whose `Terms:` entries
       overlap with `local_shelf_index_terms`. Two files with similar topical
       relevance to the question are not equally relevant — the one whose
       vocabulary aligns with the local project's vocabulary is more useful
       *for this caller*.

    2. **The KB config excerpt names the project's lens.** If the excerpt
       references domain-specific vocabulary or constraints (e.g., "Brazilian
       semiconductor packaging operations"), treat that as the framing under
       which findings are interpreted. Findings from your scoped library that
       match the local vocabulary should be preferred over findings that don't.

    3. **Caveat when priming finds no overlap.** If your scoped shelf-index
       has no Terms overlapping with `local_shelf_index_terms`, this is not a
       failure — your library may genuinely cover a different domain. Note in
       your findings' Caveats that "this library does not share vocabulary
       with the local project; the findings below may be applicable through
       analogy rather than direct overlap."

  When `PRIMING_CONTEXT` is absent, behave as a single-library query without
  framing — fall back to question-only matching against your shelf-index.
```

- [ ] **Step 3: Mirror the change to the plugin-dir copy**

```bash
cp agents/knowledge-base/research-librarian.md plugins/sdlc-knowledge-base/agents/research-librarian.md
```

- [ ] **Step 4: Verify packaging check still passes**

Run: `python3 tools/validation/check-plugin-packaging.py`
Expected: `Plugin packaging check PASSED — 12 plugin(s) verified.`

- [ ] **Step 5: Commit**

```bash
git add agents/knowledge-base/research-librarian.md plugins/sdlc-knowledge-base/agents/research-librarian.md
git commit -m "feat(kb): activate priming context in librarian prompt (phase B, #168)

Replaces the phase-A 'optional, will activate later' caveat with concrete
active-use instructions:

1. Term overlap biases match selection — files whose shelf-index Terms
   overlap with the local project's vocabulary rank higher.
2. The KB config excerpt names the project's lens — findings should be
   interpreted under that framing.
3. Absent overlap is not a failure but should surface as a Caveat —
   the library may cover a different domain.

When PRIMING_CONTEXT is absent the librarian falls back to question-only
matching, preserving backwards compatibility for non-cross-library use.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 3: kb-query skill uses `format_dispatch_prompt` instead of inline templating

**Files:**
- Modify root: `skills/kb-query/SKILL.md`
- Mirror to plugin: `plugins/sdlc-knowledge-base/skills/kb-query/SKILL.md`

Replace Step 3's inline prompt construction with a call to `format_dispatch_prompt`. This DRYs the format and ensures the skill stays consistent with what the orchestrator's tests verify.

- [ ] **Step 1: Read current Step 3**

Run: `grep -n -B 1 -A 30 "### 3. Dispatch \`research-librarian\`" skills/kb-query/SKILL.md`

The current step shows an inline template. We're replacing the prompt construction (not the dispatch mechanism — Claude still uses the Agent tool in parallel).

- [ ] **Step 2: Replace Step 3 with the helper-based form**

In `skills/kb-query/SKILL.md`, replace the entire `### 3. Dispatch research-librarian for every source — in parallel` section with:

```markdown
### 3. Format and dispatch one librarian per source — in parallel

For each source in the dispatch list, render the librarian prompt via the orchestrator's
helper (it produces the exact `SCOPE: / SOURCE_HANDLE: / PRIMING_CONTEXT:` shape the
librarian expects):

```bash
python3 -c "
from pathlib import Path
from sdlc_knowledge_base_scripts.orchestrator import format_dispatch_prompt
from sdlc_knowledge_base_scripts.priming import PrimingBundle
from sdlc_knowledge_base_scripts.registry import LibrarySource
import json

# Reconstruct the priming bundle from the JSON produced in Step 2
priming_data = json.loads('<priming_bundle_json_from_step_2>')
priming = PrimingBundle(
    question=priming_data['question'],
    local_kb_config_excerpt=priming_data['local_kb_config_excerpt'],
    local_shelf_index_terms=priming_data['local_shelf_index_terms'],
)

source = LibrarySource(name='<source.name>', type='filesystem', path='<source.path>')
prompt = format_dispatch_prompt(
    source=source,
    question='<the user question>',
    priming=priming,
)
print(prompt)
"
```

Then use the **Agent tool** to invoke the `research-librarian` agent *once per source* in
the dispatch list. Issue ALL invocations in a SINGLE message so they run in parallel
(Claude's parallel tool-call capability). Pass each source's rendered prompt as the
agent's input.

The rendered prompt structure looks like:

```
SCOPE: <source.path>
SOURCE_HANDLE: <source.name>
PRIMING_CONTEXT:
{
  "local_kb_config_excerpt": "...",
  "local_shelf_index_terms": [...]
}

Question: <the user question>

Read the shelf-index at <source.path>/_shelf-index.md, identify the 2-4
most relevant library files for the question, deep-read only those, and
return findings in the retrieval format. Every finding block must include
a **Source library**: <source.name> line (see your agent prompt).

Do not read any files outside <source.path>. Do not emit --- horizontal
rules inside a finding block (they are treated as structural separators
by the post-check tokenizer).
```

The librarian agent's prompt spec defines how it consumes `PRIMING_CONTEXT` — the orchestrator
helper, the librarian prompt, and this skill stay in lockstep on the format.
```

- [ ] **Step 3: Remove the phase B deferral note in Step 2**

Step 2 currently ends with:

> In phase A, the bundle is built but the librarian's use of it is not yet active (phase B, #168 enables that). Passing it through now means phase B is a librarian-prompt change only, not a skill rewrite.

Replace it with:

> The bundle's contents flow into each librarian dispatch via `format_dispatch_prompt`
> in Step 3. The librarian uses `local_shelf_index_terms` to bias term-matching against
> its scoped shelf-index, and `local_kb_config_excerpt` to frame findings in the local
> project's lens (see the librarian agent's `PRIMING_CONTEXT` documentation).

- [ ] **Step 4: Mirror to plugin-dir**

```bash
cp skills/kb-query/SKILL.md plugins/sdlc-knowledge-base/skills/kb-query/SKILL.md
```

- [ ] **Step 5: Verify packaging check passes**

Run: `python3 tools/validation/check-plugin-packaging.py`
Expected: 12 plugins verified.

- [ ] **Step 6: Commit**

```bash
git add skills/kb-query/SKILL.md plugins/sdlc-knowledge-base/skills/kb-query/SKILL.md
git commit -m "feat(kb): kb-query uses format_dispatch_prompt helper (phase B, #168)

Step 3 now calls the orchestrator's format_dispatch_prompt helper
instead of templating the librarian prompt inline. This DRYs the
prompt format across the skill, the orchestrator (which produces it),
and the librarian (which consumes it). Step 2's phase-B deferral note
removed — priming is now active.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 4: Update `priming.py` module docstring

**Files:**
- Modify: `plugins/sdlc-knowledge-base/scripts/priming.py`

The docstring currently says "Phase A scaffold... Phase B will activate". Update to reflect activation. Trivial change.

- [ ] **Step 1: Edit the module and dataclass docstrings**

In `plugins/sdlc-knowledge-base/scripts/priming.py`, replace the module docstring:

```python
"""Priming bundle construction for cross-library kb-query.

Phase B of EPIC #164 (sub-2, #168). The bundle is consumed by external
librarian invocations via orchestrator.format_dispatch_prompt — see the
research-librarian agent's PRIMING_CONTEXT documentation for how the
librarian uses these fields to bias term-matching and frame findings.
"""
```

And update the `PrimingBundle` class docstring:

```python
@dataclass
class PrimingBundle:
    """Context passed to external librarians to frame their query.

    Consumed by `orchestrator.format_dispatch_prompt` and rendered into
    the librarian's PRIMING_CONTEXT JSON block. The librarian uses:

    - `local_kb_config_excerpt` — to interpret findings under the project's
      lens (e.g., "Brazilian semiconductor packaging operations")
    - `local_shelf_index_terms` — to bias term-matching against its scoped
      shelf-index, preferring files whose Terms overlap with the local
      project's vocabulary
    """
    question: str
    local_kb_config_excerpt: str = ""
    local_shelf_index_terms: list[str] = field(default_factory=list)
```

- [ ] **Step 2: Verify tests still pass**

Run: `python3 -m pytest tests/test_kb_priming.py tests/test_kb_orchestrator.py -v`
Expected: all tests pass (no behaviour changed).

- [ ] **Step 3: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/priming.py
git commit -m "docs(kb): priming.py docstrings reflect phase B activation (#168)

Module and PrimingBundle docstrings now describe how priming is
consumed (format_dispatch_prompt → librarian PRIMING_CONTEXT) rather
than 'phase A scaffold, phase B activates'.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 5: Integration test — orchestrator dispatcher receives populated priming

**Files:**
- Modify: `tests/test_kb_orchestrator.py`

Verify that when `kb-query` builds a real priming bundle and passes it through the orchestrator, the dispatcher receives a `DispatchRequest` with that bundle present and intact. This test exercises the priming → orchestrator → dispatcher contract end-to-end (with a mock dispatcher).

- [ ] **Step 1: Write the failing test**

Append to `tests/test_kb_orchestrator.py`:

```python
def test_orchestrator_passes_priming_bundle_to_dispatcher(tmp_path: Path) -> None:
    """Priming bundle built from a real project's local state must flow intact
    to each dispatcher invocation, with all fields preserved."""
    # Build a fake project directory with CLAUDE.md and a local library/_shelf-index.md
    proj_dir = tmp_path / "proj"
    proj_dir.mkdir()
    (proj_dir / "CLAUDE.md").write_text(
        "# CLAUDE.md\n\n"
        "## Knowledge Base\n\n"
        "This project uses the knowledge base for semiconductor research.\n"
    )
    local_lib = proj_dir / "library"
    local_lib.mkdir()
    (local_lib / "_shelf-index.md").write_text(
        "# Shelf Index\n\n"
        "## 1. local-topic.md\n"
        "**Terms:** semiconductor, brazilian-fab, alpha\n"
    )

    # Use the real priming builder, not a mock
    from sdlc_knowledge_base_scripts.priming import build_priming_bundle
    priming = build_priming_bundle(question="what about EUV", project_dir=proj_dir)

    # Verify the builder did its job
    assert "semiconductor research" in priming.local_kb_config_excerpt
    assert set(priming.local_shelf_index_terms) >= {"semiconductor", "brazilian-fab", "alpha"}

    # Capture every DispatchRequest the orchestrator passes to the dispatcher
    captured: list[DispatchRequest] = []

    def capturing_dispatcher(req: DispatchRequest) -> str:
        captured.append(req)
        return (
            f"### {req.source.name} finding\n"
            f"**Finding**: ok.\n"
            f"**Source library**: {req.source.name}\n"
        )

    sources = [
        LibrarySource(name="local", type="filesystem", path=str(local_lib)),
        LibrarySource(name="corp", type="filesystem", path=str(tmp_path / "corp" / "library")),
    ]
    # Make corp a real dir so the source preflight passes
    (tmp_path / "corp" / "library").mkdir(parents=True)

    result = run_retrieval_query(
        question="what about EUV",
        sources=sources,
        priming=priming,
        dispatcher=capturing_dispatcher,
    )

    # Both sources should have been dispatched with the SAME priming bundle
    assert len(captured) == 2
    for req in captured:
        assert req.priming is priming, (
            f"Dispatcher received a different priming bundle for source {req.source.name}"
        )
        assert req.priming.local_kb_config_excerpt == priming.local_kb_config_excerpt
        assert req.priming.local_shelf_index_terms == priming.local_shelf_index_terms

    # And the result should still be well-formed
    assert "local finding" in result.combined_output
    assert "corp finding" in result.combined_output
```

- [ ] **Step 2: Run test — verify it fails or passes correctly**

Run: `python3 -m pytest tests/test_kb_orchestrator.py::test_orchestrator_passes_priming_bundle_to_dispatcher -v`

Expected: PASS. The orchestrator's existing `priming` parameter already passes the bundle through. This test is a regression guard — if a future change accidentally breaks priming pass-through, this test fires immediately.

If the test FAILS, it means there's a real bug in the orchestrator's priming handling. Investigate the assertion that fired and report.

- [ ] **Step 3: Run the full kb test suite**

Run: `python3 -m pytest tests/test_kb_registry.py tests/test_kb_priming.py tests/test_kb_attribution.py tests/test_kb_format_version.py tests/test_kb_orchestrator.py -v`
Expected: all pass.

- [ ] **Step 4: Commit**

```bash
git add tests/test_kb_orchestrator.py
git commit -m "test(kb): regression guard for priming-through-dispatcher (#168)

End-to-end test from build_priming_bundle through run_retrieval_query
to a capturing dispatcher confirms the priming bundle reaches every
source's DispatchRequest unchanged. Catches future regressions where
priming might be silently dropped or mutated.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 6: Feature proposal + retrospective scaffold for #168

**Files:**
- Create: `docs/feature-proposals/168-kb-cross-library-phase-b.md`
- Create: `retrospectives/168-kb-cross-library-phase-b.md`

Mirrors the Phase A pattern. Per CONSTITUTION Article 2.

- [ ] **Step 1: Create the feature proposal**

Create `docs/feature-proposals/168-kb-cross-library-phase-b.md`:

```markdown
# Feature Proposal: Cross-Library KB Query — Phase B Priming

**Proposal Number:** 168
**Status:** In Progress
**Author:** Claude (AI Agent) and Steve Jones
**Created:** 2026-04-24
**Target Branch:** `feature/164-cross-library-kb-query` (continues from Phase A)
**EPIC:** #164 (Cross-Library KB Query Support)
**Sub-feature:** #168 (sub-2 of 3 in v1)

## Summary

Activate the priming bundle scaffolded in Phase A. The local project's CLAUDE.md `[Knowledge Base]` section and shelf-index terms now actively bias external librarian queries — files whose vocabulary overlaps with the local project's terms rank higher; the KB config excerpt names the lens under which findings are interpreted.

## Motivation

See EPIC #164 body and design spec §3.3 (priming as a key architectural property), §6.1 step 2 (data flow). Phase A built the scaffold (PrimingBundle dataclass, builder, orchestrator pass-through). Phase B is the activation layer — without it, the EPIC's differentiator ("local context frames how global libraries are interrogated") is unrealised.

## Design

Full design in `docs/superpowers/specs/2026-04-24-cross-library-kb-query-design.md`.

Phase B implementation per spec §6.1 step 2 (priming bundle construction) and the librarian's PRIMING_CONTEXT consumption rules in spec §3.3. Adds one helper (`format_dispatch_prompt`), updates the librarian prompt's PRIMING_CONTEXT bullet to active-use semantics, and DRYs the kb-query skill's Step 3 to call the helper instead of inline templating.

## Success Criteria

Per issue #168 acceptance criteria:

- [ ] `format_dispatch_prompt` helper renders SCOPE / SOURCE_HANDLE / PRIMING_CONTEXT in the exact shape the librarian agent expects
- [ ] Librarian agent prompt has active-use PRIMING_CONTEXT instructions (no more "optional, phase B will activate" caveat)
- [ ] kb-query skill Step 3 uses `format_dispatch_prompt` instead of inline templating
- [ ] Integration test proves priming bundle flows from `build_priming_bundle` through `run_retrieval_query` to every dispatcher invocation
- [ ] All Phase A tests still pass; `check-plugin-packaging.py` reports 12 plugins verified
- [ ] `python tools/validation/local-validation.py --pre-push` passes

## Out of scope (phase B)

- Cross-library synthesis (phase C, #169)
- RemoteAgentSource (deferred EPIC)
- E2E tests with real librarian dispatch (deferred — they exist in spec §8.3 but require live agent runs)
- Tuning the librarian's biasing heuristics based on real usage data (a future hardening pass)

## Dependencies

- Blocked by: #167 (Phase A) — **complete** as of 2026-04-24

## Implementation plan

`docs/superpowers/plans/2026-04-24-cross-library-kb-query-phase-b.md`
```

- [ ] **Step 2: Create the retrospective scaffold**

Create `retrospectives/168-kb-cross-library-phase-b.md`:

```markdown
# Retrospective: Cross-Library KB Query — Phase B Priming

**Issue:** #168 (sub-2 of EPIC #164)
**Branch:** `feature/164-cross-library-kb-query`
**Status:** In progress

## What went well

_(Fill in at end of implementation.)_

## What was harder than expected

_(Fill in at end of implementation.)_

## What surprised us

_(Fill in at end of implementation.)_

## What we'd do differently next time

_(Fill in at end of implementation.)_

## Metrics

- Implementation time: TBD
- Tests added: TBD
- Commits on branch for this sub-feature: TBD
- Validation pipeline pass status: TBD

## Decisions worth capturing in memory

_(Review at end; copy relevant patterns/feedback into MEMORY.md if not already captured.)_
```

- [ ] **Step 3: Commit**

```bash
git add docs/feature-proposals/168-kb-cross-library-phase-b.md retrospectives/168-kb-cross-library-phase-b.md
git commit -m "docs: feature proposal + retrospective scaffold for phase B (#168)

Required by CONSTITUTION Article 2.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 7: Final validation + retrospective completion

**Files:**
- Modify: `retrospectives/168-kb-cross-library-phase-b.md` (fill in)

- [ ] **Step 1: Run full kb test suite**

Run: `python3 -m pytest tests/test_kb_registry.py tests/test_kb_priming.py tests/test_kb_attribution.py tests/test_kb_format_version.py tests/test_kb_orchestrator.py -v`
Expected: all tests PASS (53 — 52 from Phase A + ~5 new from Task 1 + 1 new from Task 5 = ~58 total).

Note the actual final count.

- [ ] **Step 2: Run plugin packaging check**

Run: `python3 tools/validation/check-plugin-packaging.py`
Expected: 12 plugins verified.

- [ ] **Step 3: Run pre-push validation**

Run: `python3 tools/validation/local-validation.py --pre-push`
Expected: PASS (or, like Phase A, 9/10 with pre-commit binary missing as the only env issue).

If a real failure surfaces, investigate. Report BLOCKED if it's beyond Phase B's scope.

- [ ] **Step 4: Fill in the retrospective**

Edit `retrospectives/168-kb-cross-library-phase-b.md`. Sample content:

- **What went well**: Smaller scope than Phase A — 7 tasks vs 17. Helper extraction (`format_dispatch_prompt`) cleanly DRYed the prompt format across orchestrator/skill/librarian. Phase A regression caught and fixed before Phase B started.
- **What was harder than expected**: Phase A's plugin-dir vs root-source confusion (the regression). Discovered at the start of Phase B by spot-checking the post-Phase-A state.
- **What surprised us**: The `feedback_release_plugin_sync.md` memory entry already captured the lesson — but I didn't apply it during Phase A. The memory exists for a reason; reading it before starting work is on the worker.
- **What we'd do differently**: Add a pre-task checklist for any plugin-file edit: "Is this file in release-mapping.yaml? If yes, edit root source first, then mirror to plugin-dir, then run check-plugin-packaging.py before commit." Add this as a feedback memory.
- **Metrics**: implementation time, test count, commit count, validation result
- **Decisions worth capturing**: format_dispatch_prompt is the single source of truth for librarian prompt structure — orchestrator tests, kb-query skill, and the librarian agent prompt must all stay aligned with it.

- [ ] **Step 5: Update MEMORY.md**

Add a line under "Recent Work" noting Phase B (#168) is implementation-complete on branch `feature/164-cross-library-kb-query`. Update the EPIC #164 entry under "Active EPICs" — Phase A complete, Phase B complete, Phase C (#169) pending.

Also: add a new feedback memory file `memory/feedback_phase_a_plugin_dir_regression.md` capturing the pattern: "When editing files packaged in release-mapping.yaml, edit the root source first; then mirror to plugin-dir; then run check-plugin-packaging.py BEFORE committing. The plugin-dir is downstream of root, never edited directly." Reference commit `557d521` as the regression fix.

- [ ] **Step 6: Final commit**

```bash
git add retrospectives/168-kb-cross-library-phase-b.md
git commit -m "docs: complete phase B retrospective (#168)

Phase B of EPIC #164 implementation-complete. Activates the priming
bundle scaffolded in Phase A — local project context now actively
biases external librarian queries.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

- [ ] **Step 7: Report branch state**

Run: `git log main..HEAD --oneline | wc -l`
Run: `git status` — should be clean.

Phase B complete. Branch stays open for Phase C (#169 — cross-library synthesis).

---

## Self-review

**Spec coverage:**

| Spec section | Covered by task |
|---|---|
| §3.2 Orchestration with priming | Task 1 (format_dispatch_prompt), Task 3 (skill uses it) |
| §3.3 Local-context priming as architectural property | Task 2 (librarian active-use rules) |
| §6.1 step 2 (priming bundle construction) | Already in Phase A; Task 4 updates docstrings |
| §6.1 step 3 (priming flows to dispatcher) | Task 5 regression guard test |
| Spec §8.3 e2e test scenario 4 (priming affects matching) | **Deferred** — requires real librarian. Documented in proposal §"Out of scope" |

**Placeholder scan:** no TBDs. The retrospective scaffold has explicit "Fill in at end" markers — intentional.

**Type consistency:** `LibrarySource`, `PrimingBundle`, `DispatchRequest`, `RetrievalQueryResult` consistent across tasks. New function `format_dispatch_prompt(source, question, priming)` parameter names consistent across Tasks 1, 3, 5.

**Coverage of the Phase A regression lesson:** Task 2, 3 explicitly call out "edit root source first, then mirror". Task 7 step 5 captures the lesson as a feedback memory. The plan's preamble has a top-of-document warning.

---

## Execution handoff

Plan complete and saved to `docs/superpowers/plans/2026-04-24-cross-library-kb-query-phase-b.md`. Two execution options:

**1. Subagent-Driven (recommended)** — fresh subagent per task with two-stage review.

**2. Inline Execution** — `superpowers:executing-plans` with checkpoints.

Phase B is smaller than Phase A (7 tasks vs 17) so the cost ratio is more favourable. Recommend Subagent-Driven again for consistency with Phase A's quality ratchet.
