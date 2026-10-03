# Cross-Library KB Query — Phase D Operational Maturity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn EPIC #164 v1 from "matches the spec" into "consulting team can rely on this for client engagements." Address the operational maturity gaps surfaced by the five-reviewer assessment after Phases A+B+C: validate the priming differentiator actually works; add audit observability for confidentiality events; make the librarian's reasoning transparent; enable knowledge to compound back into corporate libraries; surface library staleness; reduce onboarding from a hand-walk to a single skill.

**Architecture:** Adds one new agent (`synthesis-librarian` with `tools: []`), one new module (`audit.py`), one new helper module (richer shelf-index header parser), three new skills (`kb-audit-query`, `kb-setup-consulting`, `kb-verify`), and structural extensions to `kb-promote-answer-to-library` (cross-library targets) and the librarian prompts (selection rationale, priming-influence transparency). Reuses Phases A-C's orchestrator/registry/attribution scaffolding without architectural rework.

**Tech Stack:** Python 3.10+, pytest. No new external dependencies.

**Spec:** `docs/superpowers/specs/2026-04-24-cross-library-kb-query-design.md`
**Issues:** #170 (sub-4) through #176 (sub-10)
**Branch:** `feature/164-cross-library-kb-query` (continues from Phases A+B+C, 41 commits)

---

## Critical lesson from Phase A regression (apply to every plugin-file edit)

Edit root sources first, then mirror to plugin-dir, then run `python3 tools/validation/check-plugin-packaging.py`. See `memory/feedback_phase_a_plugin_dir_regression.md`. The files in this plan that have root sources:

- `agents/knowledge-base/research-librarian.md`
- `agents/knowledge-base/synthesis-librarian.md` (new — Task 5 — also has root source per release-mapping convention)
- `skills/kb-query/SKILL.md`
- `skills/kb-rebuild-indexes/SKILL.md`
- `skills/kb-promote-answer-to-library/SKILL.md`
- `skills/kb-init/templates/claude-md-section.md`

Files only in the plugin-dir (no root source — edit in place):

- `plugins/sdlc-knowledge-base/scripts/*.py`
- `plugins/sdlc-knowledge-base/skills/kb-register-library/SKILL.md`
- `plugins/sdlc-knowledge-base/skills/kb-audit-query/SKILL.md` (new — Task 13)
- `plugins/sdlc-knowledge-base/skills/kb-setup-consulting/SKILL.md` (new — Task 26)

---

## File structure

**New files:**

| File | Responsibility |
|---|---|
| `agents/knowledge-base/synthesis-librarian.md` + plugin mirror | Synthesis-only agent with `tools: []` — structural "no file reads" guarantee |
| `plugins/sdlc-knowledge-base/scripts/audit.py` | AuditEvent dataclass, log_event/read_log functions |
| `plugins/sdlc-knowledge-base/skills/kb-audit-query/SKILL.md` | Skill that filters/summarises the audit log |
| `plugins/sdlc-knowledge-base/skills/kb-setup-consulting/SKILL.md` | Onboarding skill |
| `tests/test_kb_audit.py` | Unit + integration tests for audit module |
| `tests/test_kb_shelf_index_header.py` | Unit tests for the richer header parser |
| `tests/fixtures/kb_libraries/corp-substantial-fixture/` | Multi-topic corporate fixture for sub-5 priming validation |
| `docs/superpowers/specs/2026-04-24-priming-validation.md` | Validation methodology + captured evidence |
| `docs/feature-proposals/170-kb-cross-library-phase-d.md` | Phase D feature proposal (covers all 7 sub-features) |
| `retrospectives/170-kb-cross-library-phase-d.md` | Phase D retrospective scaffold |

**Modified files:**

| File | Change |
|---|---|
| `plugins/sdlc-knowledge-base/scripts/registry.py` | Library `name` charset validation; library `path` validation helper; `staleness_threshold_days` field on LibrarySource |
| `plugins/sdlc-knowledge-base/scripts/orchestrator.py` | `valid_handles` required; synthesis dispatch to new agent; `_render_priming_block` helper extraction; staleness caveat in retrieval output; audit-log instrumentation |
| `plugins/sdlc-knowledge-base/scripts/attribution.py` | `valid_handles` parameter required (invert default) |
| `plugins/sdlc-knowledge-base/scripts/format_version.py` | Rename or extend to `shelf_index_header.py` with full header parser |
| `agents/knowledge-base/research-librarian.md` + plugin mirror | Retrieval Selection rationale instruction |
| `skills/kb-query/SKILL.md` + plugin mirror | sys.path resolution / install check; synthesis dispatched to new agent; staleness output |
| `skills/kb-rebuild-indexes/SKILL.md` + plugin mirror | Emit full multi-line shelf-index header with timestamps |
| `skills/kb-promote-answer-to-library/SKILL.md` + plugin mirror | `--target <handle>` for cross-library promotion |
| `skills/kb-init/templates/claude-md-section.md` + plugin mirror | Reference onboarding skill |
| `release-mapping.yaml` | Wire new files into the sdlc-knowledge-base plugin |

---

## Sub-feature 1: Code quality + security cleanup (#170)

### Task 1: Run black + fix flake8

**Files:** `plugins/sdlc-knowledge-base/scripts/*.py`, `tests/test_kb_*.py`

- [ ] **Step 1: Run black formatter**

```bash
cd /Users/stevejones/Documents/Development/ai-first-sdlc-practices
black plugins/sdlc-knowledge-base/scripts/ tests/test_kb_*.py
```

- [ ] **Step 2: Run flake8 and capture remaining issues**

```bash
flake8 plugins/sdlc-knowledge-base/scripts/ tests/test_kb_*.py
```

Expected output before fixes: 9 violations (1 F401 unused import, 4 E402 late imports, 3 E306 missing blank lines, 2 E501 too-long lines).

- [ ] **Step 3: Fix flake8 violations manually**

For each test file with E402 violations: move all `from sdlc_knowledge_base_scripts.X import ...` lines to the top of the file with the other imports.

For E306 violations: add a blank line before the nested `def mock_dispatch(...)` etc. inside test functions.

For F401 (`tests/test_kb_orchestrator.py:5` unused `import json`): remove if unused, or if used in a function body but missed by static analysis, leave with `# noqa: F401` comment.

For E501 violations in `registry.py`: break the long warning strings:

```python
# Before:
warnings.append(f"Activated source '{name}' is type 'remote-agent' (planned for future release). Skipping.")

# After:
warnings.append(
    f"Activated source '{name}' is type 'remote-agent' "
    "(planned for future release). Skipping."
)
```

- [ ] **Step 4: Verify clean**

```bash
black --check plugins/sdlc-knowledge-base/scripts/ tests/test_kb_*.py
flake8 plugins/sdlc-knowledge-base/scripts/ tests/test_kb_*.py
python3 -m pytest tests/test_kb_*.py -v
```

Expected: black clean, flake8 zero output, all tests pass.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/ tests/test_kb_*.py
git commit -m "$(cat <<'EOF'
style(kb): apply black + fix flake8 violations (phase D, #170)

The phase A-C work shipped with 7 black-formatting violations and
9 flake8 violations the rest of the repo does not have. Applied
black formatter; resolved E402 (late imports) by hoisting test
imports, E306 (missing blank lines) by adding blank lines before
nested defs, F401 (unused import) by removal, E501 (long lines)
by string concatenation.

No behaviour changes.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 2: Library `name` charset validation

**Files:**
- Modify: `plugins/sdlc-knowledge-base/scripts/registry.py`
- Modify: `tests/test_kb_registry.py`
- Modify: `plugins/sdlc-knowledge-base/skills/kb-register-library/SKILL.md` (in-plugin only)

- [ ] **Step 1: Write failing tests**

Append to `tests/test_kb_registry.py`:

```python
def test_load_global_registry_invalid_name_charset_skipped(tmp_path: Path) -> None:
    registry_file = tmp_path / "global-libraries.json"
    registry_file.write_text(json.dumps({
        "version": 1,
        "libraries": [
            {"name": "Valid-Name", "type": "filesystem", "path": "/x"},
            {"name": "with spaces", "type": "filesystem", "path": "/y"},
            {"name": "with;semi", "type": "filesystem", "path": "/z"},
            {"name": "good-name", "type": "filesystem", "path": "/ok"},
        ],
    }))
    result = load_global_registry(registry_file)
    assert [lib.name for lib in result.libraries] == ["good-name"]
    invalid_warnings = [w for w in result.warnings if "name" in w.lower() and "invalid" in w.lower()]
    assert len(invalid_warnings) == 3
```

- [ ] **Step 2: Run test, confirm failure**

```bash
python3 -m pytest tests/test_kb_registry.py::test_load_global_registry_invalid_name_charset_skipped -v
```

Expected: FAIL (current code accepts any name).

- [ ] **Step 3: Add validator and wire into loader**

In `plugins/sdlc-knowledge-base/scripts/registry.py`, add at module level after `KNOWN_LIBRARY_TYPES`:

```python
import re as _re

_VALID_NAME_RE = _re.compile(r"^[a-z][a-z0-9-]*$")


def _is_valid_library_name(name: str) -> bool:
    """Library handles must match `^[a-z][a-z0-9-]*$`.

    Aligns with the synthesis attribution check's _HANDLE_TAG_RE = `[\\w-]+`,
    rejected cases: starts with digit, contains uppercase, contains spaces,
    contains shell-quoting / markdown directives.
    """
    return bool(_VALID_NAME_RE.match(name))
```

Modify `load_global_registry` (within the entry-iteration loop, before the `seen_names` check):

```python
for entry in raw_libraries:
    if not isinstance(entry, dict):
        warnings.append("Library entry is not an object; skipping.")
        continue
    name = entry.get("name")
    if not name:
        warnings.append("Library entry missing 'name' field; skipping.")
        continue
    if not _is_valid_library_name(name):
        warnings.append(
            f"Library name '{name}' invalid (must match ^[a-z][a-z0-9-]*$); skipping."
        )
        continue
    # ... rest unchanged
```

- [ ] **Step 4: Update kb-register-library skill**

Modify `plugins/sdlc-knowledge-base/skills/kb-register-library/SKILL.md`. Find the "Preflight" section. Add a step:

```markdown
- Validate `<name>` matches `^[a-z][a-z0-9-]*$` (lowercase letters, digits, hyphens; must start with a letter). If not, error with: "Library handle must match ^[a-z][a-z0-9-]*$ — found '<name>'. Choose a different name."
```

- [ ] **Step 5: Run tests + verify packaging**

```bash
python3 -m pytest tests/test_kb_registry.py -v
python3 tools/validation/check-plugin-packaging.py
```

Expected: all tests pass, 12 plugins verified.

- [ ] **Step 6: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/registry.py tests/test_kb_registry.py plugins/sdlc-knowledge-base/skills/kb-register-library/SKILL.md
git commit -m "$(cat <<'EOF'
feat(kb): library name charset validation (phase D, #170)

Library handles must match ^[a-z][a-z0-9-]*$ at registry load and at
kb-register-library invocation. Closes the markdown-injection /
shell-quoting class of attacks (a registry entry with name 'foo;bar'
or 'foo with spaces' previously survived to the dispatch prompt and
the synthesis attribution whitelist; now rejected with a clear warning).

Aligns the registry-side validation with the synthesis attribution
regex `_HANDLE_TAG_RE = [\\w-]+` so handles that pass registry will
also pass attribution checks (no silent post-attribution drops from
charset mismatches).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 3: Library `path` validation + denylist

**Files:**
- Modify: `plugins/sdlc-knowledge-base/scripts/registry.py`
- Modify: `tests/test_kb_registry.py`

- [ ] **Step 1: Write failing tests**

Append to `tests/test_kb_registry.py`:

```python
from sdlc_knowledge_base_scripts.registry import validate_library_path


def test_validate_library_path_happy(tmp_path: Path) -> None:
    lib = tmp_path / "library"
    lib.mkdir()
    (lib / "_shelf-index.md").write_text("<!-- format_version: 1 -->\n# Shelf\n")
    ok, reason = validate_library_path(lib)
    assert ok is True
    assert reason == ""


def test_validate_library_path_not_absolute(tmp_path: Path) -> None:
    ok, reason = validate_library_path(Path("library"))  # relative
    assert ok is False
    assert "absolute" in reason.lower()


def test_validate_library_path_does_not_exist(tmp_path: Path) -> None:
    ok, reason = validate_library_path(tmp_path / "nonexistent")
    assert ok is False
    assert "does not exist" in reason.lower()


def test_validate_library_path_no_shelf_index(tmp_path: Path) -> None:
    lib = tmp_path / "library"
    lib.mkdir()
    ok, reason = validate_library_path(lib)
    assert ok is False
    assert "shelf-index" in reason.lower()


def test_validate_library_path_denylist_ssh(tmp_path: Path) -> None:
    # We don't actually create ~/.ssh; we test the denylist check on the path string
    fake_ssh = Path("/Users/test/.ssh")
    ok, reason = validate_library_path(fake_ssh)
    assert ok is False
    assert ".ssh" in reason or "denylist" in reason.lower()
```

- [ ] **Step 2: Run tests, confirm failure**

```bash
python3 -m pytest tests/test_kb_registry.py::test_validate_library_path_happy -v
```

Expected: FAIL with ImportError.

- [ ] **Step 3: Implement `validate_library_path`**

Append to `plugins/sdlc-knowledge-base/scripts/registry.py`:

```python
_PATH_DENYLIST_FRAGMENTS = (
    "/.ssh",
    "/.gnupg",
    "/.aws",
    "/etc/",
    "/.git",
    "/.git/",
)


def validate_library_path(path: Path) -> tuple[bool, str]:
    """Validate a library path is safe to dispatch a librarian against.

    Returns (True, "") if valid, (False, "reason") if not. Checks:
    - Path is absolute (or resolves to absolute)
    - Path exists and is a directory
    - Path contains a `_shelf-index.md` file
    - Resolved path does not contain any denylisted fragment

    The denylist is conservative — fragments that should never be a
    valid library directory. Symlinks are resolved before the check.
    """
    if not path.is_absolute():
        return False, f"path '{path}' must be absolute"

    if not path.exists():
        return False, f"path '{path}' does not exist"

    if not path.is_dir():
        return False, f"path '{path}' is not a directory"

    try:
        resolved = path.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        return False, f"path '{path}' could not be resolved: {exc}"

    resolved_str = str(resolved)
    for fragment in _PATH_DENYLIST_FRAGMENTS:
        if fragment in resolved_str:
            return False, (
                f"path '{path}' resolves to '{resolved}' which contains "
                f"denylisted fragment '{fragment}'"
            )

    if not (resolved / "_shelf-index.md").exists():
        return False, f"path '{path}' has no _shelf-index.md"

    return True, ""
```

- [ ] **Step 4: Run tests, all pass**

```bash
python3 -m pytest tests/test_kb_registry.py -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/registry.py tests/test_kb_registry.py
git commit -m "$(cat <<'EOF'
feat(kb): library path validation + denylist (phase D, #170)

Adds validate_library_path(path) -> (ok, reason). Verifies path is
absolute, exists, is a directory, contains _shelf-index.md, and does
not resolve under a denylist (~/.ssh, ~/.gnupg, ~/.aws, /etc, .git).
Symlinks are resolved before the denylist check so symlink tricks
cannot bypass.

Used in the next commit to prevent the librarian from being dispatched
against a typo'd or maliciously-registered path. Standalone helper now
so kb-register-library and resolve_dispatch_list can both call it.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 4: Wire path validation into resolve_dispatch_list and kb-register-library

**Files:**
- Modify: `plugins/sdlc-knowledge-base/scripts/registry.py` (extend `resolve_dispatch_list`)
- Modify: `tests/test_kb_registry.py`
- Modify: `plugins/sdlc-knowledge-base/skills/kb-register-library/SKILL.md`

- [ ] **Step 1: Write failing test for resolver-side validation**

Append to `tests/test_kb_registry.py`:

```python
def test_resolve_dispatch_skips_invalid_path_with_warning(tmp_path: Path) -> None:
    local_lib = tmp_path / "library"
    local_lib.mkdir()
    (local_lib / "_shelf-index.md").write_text("# Shelf\n")

    gr = _make_global([
        LibrarySource(name="bad-corp", type="filesystem", path="/totally/nonexistent/path"),
    ])
    pa = _make_activation(["bad-corp"])
    result = resolve_dispatch_list(gr, pa, project_library_path=local_lib)
    # Local should still be in the dispatch list
    assert any(s.name == "local" for s in result.sources)
    # bad-corp should be SKIPPED (not in dispatch list)
    assert not any(s.name == "bad-corp" for s in result.sources)
    # And there should be a warning explaining why
    assert any("bad-corp" in w and ("does not exist" in w or "invalid" in w.lower()) for w in result.warnings)
```

- [ ] **Step 2: Run test, confirm failure**

```bash
python3 -m pytest tests/test_kb_registry.py::test_resolve_dispatch_skips_invalid_path_with_warning -v
```

Expected: FAIL — current code does not validate paths at resolve time.

- [ ] **Step 3: Wire validation into resolve_dispatch_list**

In `plugins/sdlc-knowledge-base/scripts/registry.py`, modify `resolve_dispatch_list`. After the `entry.type != "filesystem"` check, add a path validation step:

```python
        if entry.type != "filesystem":
            warnings.append(
                f"Source '{name}' has unknown type '{entry.type}'. Skipping."
            )
            continue
        # NEW: validate the path
        if entry.path is None:
            warnings.append(f"Source '{name}' has no path; skipping.")
            continue
        ok, reason = validate_library_path(Path(entry.path))
        if not ok:
            warnings.append(f"Source '{name}': {reason}; skipping.")
            continue
        sources.append(entry)
```

- [ ] **Step 4: Update kb-register-library skill**

Modify `plugins/sdlc-knowledge-base/skills/kb-register-library/SKILL.md`. Find the "1. Validate the target library path" step. Replace its bullets with a single instruction to call `validate_library_path`:

```markdown
### 1. Validate the target library path

Run the path validator:

\`\`\`bash
python3 -c "
from pathlib import Path
from sdlc_knowledge_base_scripts.registry import validate_library_path
ok, reason = validate_library_path(Path('<path>'))
if not ok:
    print(f'ERROR: {reason}')
    exit(1)
print('OK')
"
\`\`\`

If the validator returns an error, surface the exact `reason` string to the user and stop. Common reasons:

- "path 'X' must be absolute" — user gave a relative path; correct it
- "path 'X' does not exist" — directory doesn't exist; create it or correct path
- "path 'X' has no _shelf-index.md" — run `/sdlc-knowledge-base:kb-rebuild-indexes` in that library first
- "path 'X' resolves to '...' which contains denylisted fragment '...'" — refuse to register; user should pick a different path
```

- [ ] **Step 5: Run tests + packaging check**

```bash
python3 -m pytest tests/test_kb_registry.py -v
python3 tools/validation/check-plugin-packaging.py
```

Expected: all tests pass, 12 plugins verified.

- [ ] **Step 6: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/registry.py tests/test_kb_registry.py plugins/sdlc-knowledge-base/skills/kb-register-library/SKILL.md
git commit -m "$(cat <<'EOF'
feat(kb): wire path validation into resolver + register skill (phase D, #170)

resolve_dispatch_list now validates each filesystem source's path
before adding it to the dispatch list. Invalid paths (nonexistent,
denylisted, no shelf-index) are skipped with a clear warning rather
than dispatched against, so a typo or compromised registry entry
cannot send the librarian off-piste with full Read/Glob/Grep/Bash.

kb-register-library skill updated to use the same validator with
clear error reporting per failure reason.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 5: `valid_handles` parameter required + extract priming-block helper

**Files:**
- Modify: `plugins/sdlc-knowledge-base/scripts/attribution.py`
- Modify: `plugins/sdlc-knowledge-base/scripts/orchestrator.py`
- Modify: `tests/test_kb_attribution.py`
- Modify: `tests/test_kb_orchestrator.py`

- [ ] **Step 1: Update existing tests for new signature**

In `tests/test_kb_attribution.py`, find the synthesis tests. Each test that calls `check_synthesis_attribution(output)` without `valid_handles` will need to pass an explicit value. For tests that previously used the permissive default, pass a permissive set:

```python
# OLD:
result = check_synthesis_attribution(output)
# NEW for tests where any handle should pass (the default-permissive cases):
PERMISSIVE_HANDLES = {"local", "corp-semi", "corp", "TODO", "0", "citation-needed"}  # tests expecting the old "anything bracketed passes"
result = check_synthesis_attribution(output, valid_handles=PERMISSIVE_HANDLES)
```

For tests that explicitly verified rejection (e.g., `test_synthesis_valid_handles_rejects_bogus_brackets`), keep the strict whitelist they already pass.

- [ ] **Step 2: Update attribution.py to require valid_handles**

In `plugins/sdlc-knowledge-base/scripts/attribution.py`, change the signature of `check_synthesis_attribution`:

```python
def check_synthesis_attribution(
    output: str,
    valid_handles: set[str],
) -> SynthesisCheckResult:
    """Verify every supporting-evidence item has a [handle] in valid_handles.

    valid_handles is required — there is no permissive default. This prevents
    callers from accidentally accepting any bracketed token (e.g., [TODO] or
    [0]) as a valid attribution.
    """
    untagged: list[str] = []
    # ... rest unchanged but inline the _has_valid_handle check (no None-permissive branch)
```

Update or remove `_has_valid_handle` to no longer accept None.

- [ ] **Step 3: Run all tests, fix call sites**

```bash
python3 -m pytest tests/test_kb_*.py -v
```

Expected: any test that called `check_synthesis_attribution(output)` without `valid_handles` will fail with TypeError. Fix each call site to pass an explicit value.

- [ ] **Step 4: Extract `_render_priming_block` helper in orchestrator**

In `plugins/sdlc-knowledge-base/scripts/orchestrator.py`, add a helper near the top after the dataclass declarations:

```python
def _render_priming_block(priming: Optional[PrimingBundle]) -> list[str]:
    """Return prompt lines for the PRIMING_CONTEXT block, empty if priming is None."""
    if priming is None:
        return []
    priming_json = _json.dumps(
        {
            "local_kb_config_excerpt": priming.local_kb_config_excerpt,
            "local_shelf_index_terms": priming.local_shelf_index_terms,
        },
        indent=2,
    )
    return ["PRIMING_CONTEXT:", priming_json]
```

In `format_dispatch_prompt`, replace the existing inline block (lines that build the priming JSON when `priming is not None`) with `lines.extend(_render_priming_block(priming))`.

In `format_synthesis_prompt`, do the same replacement.

- [ ] **Step 5: Run all tests**

```bash
python3 -m pytest tests/test_kb_*.py -v
```

Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/attribution.py plugins/sdlc-knowledge-base/scripts/orchestrator.py tests/test_kb_attribution.py tests/test_kb_orchestrator.py
git commit -m "$(cat <<'EOF'
refactor(kb): valid_handles required + extract priming block helper (phase D, #170)

check_synthesis_attribution(valid_handles=...) is now required. Removes
the permissive default that would silently accept [TODO] / [0] tokens
if a future caller forgot to pass it. All current call sites in
run_synthesis_query already pass valid_handles drawn from the dispatch
sources; this change locks that down so a future caller cannot regress.

Extracts _render_priming_block helper to deduplicate the 8-line
PRIMING_CONTEXT JSON serialisation that was duplicated between
format_dispatch_prompt and format_synthesis_prompt. format_synthesis_prompt
will gain more shape in later sub-features (Selection rationale, library
evolution caveats), so deduplication now reduces drift risk.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 6: Synthesis-librarian as separate agent with `tools: []`

**Files:**
- Create root: `agents/knowledge-base/synthesis-librarian.md`
- Create plugin mirror: `plugins/sdlc-knowledge-base/agents/synthesis-librarian.md`
- Modify: `plugins/sdlc-knowledge-base/scripts/orchestrator.py` (dispatcher must target the new agent)
- Modify: `release-mapping.yaml`

- [ ] **Step 1: Create the new agent at root source**

Create `agents/knowledge-base/synthesis-librarian.md`:

```markdown
---
name: synthesis-librarian
description: "Stateless cross-library synthesis agent. Receives pre-retrieved findings from multiple sources and produces a single attributed argument. Has NO file-reading tools — its only ground truth is the supplied findings, which makes inline source-handle attribution structurally guaranteed."
model: sonnet
tools: []
color: cyan
---

# Synthesis Librarian

You are the Synthesis Librarian. You produce cross-library syntheses from pre-retrieved findings supplied in your dispatch message. You have no file-reading tools — the findings you receive are your only source of ground truth.

## Critical behaviour: never hallucinate

The trust users place in you depends on three rules:

1. **Never invent a citation, statistic, or claim.** Every claim in your output must be traceable to one of the per-source findings supplied to you.
2. **Never reference a library or file you have not been given findings from.** The dispatch sources are your bounded universe.
3. **Say "the supplied findings do not support a synthesis for this question" when the available findings genuinely cannot answer.** Do not pad with speculation.

## Dispatch message format

You will always receive a dispatch starting with:

```
MODE: SYNTHESISE-ACROSS-SOURCES
PRIMING_CONTEXT:
{
  "local_kb_config_excerpt": "...",
  "local_shelf_index_terms": [...]
}

Question: <the user question>

Per-source findings (your only source of facts — do not read any files):

--- [<handle>] ---
<findings text>
--- [<other-handle>] ---
<findings text>
...
```

The PRIMING_CONTEXT block may be omitted (when no priming is supplied). The per-source findings sections are your bounded universe.

## Output format

Use the synthesis output format:

```markdown
### [Argument Title]

**Claim**: [The synthesised conclusion]

**Supporting evidence**:
1. [Specific claim from a source] — [<handle>] <library file>
2. [Another claim] — [<other-handle>] <library file>
3. ...

**Caveats**: [Cross-library spans, contradictions, limitations]

**Programme application**: [How this applies to the local project, drawn from PRIMING_CONTEXT — only if PRIMING_CONTEXT was supplied and the local KB config excerpt makes the connection]
```

### MANDATORY attribution

Every Supporting evidence item MUST carry an inline `[<handle>]` tag identifying which source library the claim came from. The format is:

```
1. <claim text> — [<handle>] <library file>
```

The structural attribution post-check whitelists handles against the dispatch sources. Bracketed tokens that are not real source handles (e.g., `[TODO]`, `[citation-needed]`, `[0]`) will fail the post-check and the synthesis will be aborted. Untagged claims will also fail. There are no warnings — the synthesis either ships with full attribution or it doesn't ship at all.

### MANDATORY cross-library caveats

When your supporting evidence draws on more than one source library, the Caveats section MUST explicitly name the libraries and any boundary conditions. For example:

> **Caveats**: This synthesis draws on local and corp-semi libraries; the corp-semi findings are from a different regional context (Dutch fab) and may need adaptation before applying to the local project (Brazilian fab).

This is a transparency requirement — the reader needs to know which boundaries the synthesis crosses to judge whether the inference is sound for their decision.

### Priming-influence transparency

When PRIMING_CONTEXT is supplied, mention in the Caveats how priming influenced your synthesis. For example:

> **Caveats**: ... I prioritised findings tagged with `dutch-fab` (over similar findings tagged `austin-fab`) because the local project's vocabulary includes `brazilian-fab` which is more analogous to dutch-fab in operating environment.

This makes the influence of the local project's framing visible to the reader.

## When the question cannot be synthesised

If the supplied findings genuinely do not support a synthesis answering the question:

```markdown
### [Question topic]

**Status**: The supplied findings do not support a synthesis for this question.

**What is missing**: [Specific gaps — e.g., "the corp-semi findings cover EUV reticle humidity tolerance but not chamber pressure dynamics, which the question requires"]

**What was supplied**: [Brief catalogue of the per-source findings you did receive]

**Recommendation**: [Either commission additional research via kb-ingest, or rephrase the question to match what the findings cover]
```

Do not pad. Do not speculate. The user wants to know whether your library has the evidence, not your guesses.

## What you do not have

You do not have Read, Glob, Grep, Bash, or any other file-reading tools. This is by design — your guarantee that you cannot invent citations rests on your inability to read files outside the supplied dispatch.

If you find yourself wanting to look up something not in the dispatch, that is a signal that the synthesis is not safe and you should return the "cannot be synthesised" response.

## Configuration

This agent is dispatched by the `kb-query` skill in cross-library synthesis mode. Its prompt structure is produced by `orchestrator.format_synthesis_prompt`. Its output is validated by `attribution.check_synthesis_attribution` with the dispatch sources as the valid_handles whitelist.
```

- [ ] **Step 2: Mirror to plugin-dir**

```bash
cp agents/knowledge-base/synthesis-librarian.md plugins/sdlc-knowledge-base/agents/synthesis-librarian.md
```

- [ ] **Step 3: Update release-mapping.yaml**

In `release-mapping.yaml`, find the `sdlc-knowledge-base:` block, `agents:` subsection. Add:

```yaml
    - source: agents/knowledge-base/synthesis-librarian.md
```

(Place after the existing `research-librarian.md` entry.)

- [ ] **Step 4: Update orchestrator + skill to dispatch synthesis to the new agent**

In `plugins/sdlc-knowledge-base/scripts/orchestrator.py`, update the `SynthesisDispatcher` type alias documentation comment to reference the new agent:

```python
# SynthesisDispatcher: callable that takes a synthesis prompt and returns the
# librarian's output. In the kb-query skill, this is wired to dispatch the
# `synthesis-librarian` agent (NOT research-librarian) so the structural
# "no file reads" guarantee is enforced at the agent level (tools: [])
# rather than purely by prompt instruction.
SynthesisDispatcher = Callable[[str], str]
```

In `skills/kb-query/SKILL.md` Step 6 (the synthesis branch), update the Agent tool dispatch instruction to use `synthesis-librarian` agent rather than `research-librarian`:

```markdown
... use the **Agent tool** to invoke the `synthesis-librarian` agent (NOT research-librarian — synthesis-librarian has tools: [] which makes 'no file reads' structural). Pass the rendered prompt as the agent's input.
```

Also update the rendered prompt explanation in Step 6 to note the agent change.

Mirror to `plugins/sdlc-knowledge-base/skills/kb-query/SKILL.md`:

```bash
cp skills/kb-query/SKILL.md plugins/sdlc-knowledge-base/skills/kb-query/SKILL.md
```

- [ ] **Step 5: Run packaging check + tests**

```bash
python3 tools/validation/check-plugin-packaging.py
python3 -m pytest tests/test_kb_*.py -v
```

Expected: 13 plugins verified (the new agent file is now packaged), all tests pass.

- [ ] **Step 6: Commit**

```bash
git add agents/knowledge-base/synthesis-librarian.md plugins/sdlc-knowledge-base/agents/synthesis-librarian.md plugins/sdlc-knowledge-base/scripts/orchestrator.py skills/kb-query/SKILL.md plugins/sdlc-knowledge-base/skills/kb-query/SKILL.md release-mapping.yaml
git commit -m "$(cat <<'EOF'
feat(kb): synthesis-librarian as separate agent with tools: [] (phase D, #170)

Splits synthesis from retrieval at the agent level. The new
synthesis-librarian agent has tools: [] in its frontmatter, which
makes the 'no file reads' guarantee structural — the agent literally
cannot read files because no file-reading tools are bound to it.
Previously the guarantee was prompt-only ('You have no file-reading
tools in this mode') which a non-compliant or jailbroken model could
ignore.

The retrieval librarian (research-librarian) keeps its Read/Glob/Grep/Bash
tools because retrieval requires reading library files within scope.
Synthesis works only from pre-retrieved findings supplied in the dispatch
message; that's now structurally enforced.

kb-query Step 6 updated to dispatch the new agent. release-mapping
packages the new agent file.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 7: Skill bash sys.path resolution

**Files:**
- Modify root: `skills/kb-query/SKILL.md`
- Modify plugin: `plugins/sdlc-knowledge-base/skills/kb-query/SKILL.md`
- Modify: `plugins/sdlc-knowledge-base/skills/kb-register-library/SKILL.md` (in-plugin only)

The skill's bash snippets call `from sdlc_knowledge_base_scripts.registry import ...` which only works if the package was pip-install -e'd. In a fresh user environment it fails with ModuleNotFoundError.

- [ ] **Step 1: Add a step-0 importability check to kb-query SKILL.md**

In `skills/kb-query/SKILL.md`, before Step 1 (Preflight), add:

```markdown
## Preflight: verify scripts package importable

Before running any subsequent step, verify the kb scripts package can be imported. The scripts are bundled with the plugin but require either an editable install or a sys.path resolution.

```bash
python3 -c "
import sys
import os
PLUGIN_SCRIPTS = os.path.join(os.environ.get('CLAUDE_PLUGIN_ROOT', ''), 'scripts')
if os.path.isdir(PLUGIN_SCRIPTS):
    sys.path.insert(0, os.path.dirname(PLUGIN_SCRIPTS))  # parent so 'scripts' is importable as a package
try:
    import sdlc_knowledge_base_scripts.registry  # noqa
    print('OK')
except ImportError:
    print('MISSING')
"
```

If the output is `MISSING`, prepend this preamble to every subsequent bash snippet in this skill:

```python
import sys, os
sys.path.insert(0, os.path.join(os.environ.get('CLAUDE_PLUGIN_ROOT', ''), 'scripts'))
```

The `CLAUDE_PLUGIN_ROOT` environment variable is set by Claude Code when it loads the plugin; it points to the plugin's directory. The scripts subdirectory is always packaged as `<plugin>/scripts/`.

If `CLAUDE_PLUGIN_ROOT` is not set (e.g., running outside Claude Code), the user can either:
- Set it manually: `export CLAUDE_PLUGIN_ROOT=plugins/sdlc-knowledge-base`
- Editable-install the plugin: `pip install -e plugins/sdlc-knowledge-base`
```

- [ ] **Step 2: Apply the same fix to kb-register-library**

In `plugins/sdlc-knowledge-base/skills/kb-register-library/SKILL.md`, find the bash snippet in Step 1. Prepend:

```python
import sys, os
sys.path.insert(0, os.path.join(os.environ.get('CLAUDE_PLUGIN_ROOT', ''), 'scripts'))
```

(Inside the existing python3 -c "..." block, before the `from pathlib import Path` line.)

- [ ] **Step 3: Mirror kb-query to plugin-dir**

```bash
cp skills/kb-query/SKILL.md plugins/sdlc-knowledge-base/skills/kb-query/SKILL.md
```

- [ ] **Step 4: Verify packaging**

```bash
python3 tools/validation/check-plugin-packaging.py
```

Expected: 13 plugins verified.

- [ ] **Step 5: Commit**

```bash
git add skills/kb-query/SKILL.md plugins/sdlc-knowledge-base/skills/kb-query/SKILL.md plugins/sdlc-knowledge-base/skills/kb-register-library/SKILL.md
git commit -m "$(cat <<'EOF'
fix(kb): skill bash snippets use CLAUDE_PLUGIN_ROOT for imports (phase D, #170)

The skill's python3 -c bash snippets called 'from
sdlc_knowledge_base_scripts.registry import ...' which only works if
the package was pip-install -e'd in the user's environment. Fresh
user environments hit ModuleNotFoundError.

Adds a step-0 preflight check and a sys.path resolution preamble
that uses CLAUDE_PLUGIN_ROOT (set by Claude Code when loading the
plugin) to point at <plugin>/scripts/. Falls back to manual env-var
setting or pip install -e for non-Claude-Code execution contexts.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 8: Documentation drift fixes

**Files:**
- Modify: `retrospectives/167-kb-cross-library-phase-a.md`
- Modify: `plugins/sdlc-knowledge-base/scripts/orchestrator.py` (module docstring)
- Modify: `plugins/sdlc-knowledge-base/scripts/attribution.py` (function docstring)
- Modify root + mirror: `skills/kb-query/SKILL.md` (Multi-source example header format)
- Modify: `docs/superpowers/specs/2026-04-24-cross-library-kb-query-design.md` (§5.1)
- Modify: `plugins/sdlc-knowledge-base/scripts/registry.py` (LibrarySource.description)
- Delete or repurpose: `tests/fixtures/kb_libraries/` (dead fixtures)

- [ ] **Step 1: Phase A retrospective filename + 557d521 reference**

In `retrospectives/167-kb-cross-library-phase-a.md`, find the `.sdlc-kb-libraries.json` reference (line ~45) and replace with `.sdlc/libraries.json`.

Find the "Tasks 9-13 drift" item (around line 18-29). Reframe it to reference the actual root cause and the fix commit:

```markdown
- **Plugin-dir vs root-source layer confusion**: Tasks 9, 10, 12, and 13 edited plugin-directory copies of files that have separate root sources packaged via `release-mapping.yaml` (research-librarian.md, kb-query/SKILL.md, kb-rebuild-indexes/SKILL.md, claude-md-section.md, two shelf-index files). Task 14's release-plugin sync correctly synced root → plugin-dir per the release-mapping convention, which silently wiped the Phase A edits because the root sources hadn't been updated. The regression was caught at the start of Phase B by spot-checking the post-Phase-A state and fixed in commit `557d521` ("fix(kb): restore phase A edits to root sources + plugin dir"). Lesson: when editing files listed in `release-mapping.yaml` with a separate root source, edit the root first, then mirror, then verify with `check-plugin-packaging.py` before committing. Captured permanently in `memory/feedback_phase_a_plugin_dir_regression.md`.
```

- [ ] **Step 2: orchestrator.py module docstring update**

In `plugins/sdlc-knowledge-base/scripts/orchestrator.py`, replace the module docstring header:

```python
"""kb-query orchestrator: dispatch, collect, attribution post-check, render.

The orchestrator is pure Python; the `dispatcher` callable abstracts the
Agent tool call so tests can inject mocks. The kb-query skill wires in a
real dispatcher backed by parallel Agent invocations against the
research-librarian (retrieval) and synthesis-librarian (synthesis) agents.

Phases A+B+C+D of EPIC #164 — see spec §3.2, §6.1, §6.2, §7.1, and the
Phase D operational maturity additions (audit logging, staleness caveats,
priming transparency).
"""
```

- [ ] **Step 3: attribution.py docstring update**

In `plugins/sdlc-knowledge-base/scripts/attribution.py`, find the `check_synthesis_attribution` docstring. Update to reflect that valid_handles is now required:

```python
def check_synthesis_attribution(
    output: str,
    valid_handles: set[str],
) -> SynthesisCheckResult:
    """Verify every supporting-evidence item has an inline [handle] tag in valid_handles.

    valid_handles is required and is typically the set of source names from
    run_synthesis_query's dispatch sources. Bracketed tokens not in the set
    (e.g., [TODO], [0], [citation-needed]) fail the check.

    Any untagged or out-of-whitelist item causes passed=False; the caller is
    expected to abort the synthesis and return retrieval-only output with an
    error block.
    """
```

- [ ] **Step 4: kb-query Multi-source example header format fix**

In `skills/kb-query/SKILL.md`, find the Multi-source query Examples section. Replace the old single-line header `**Sources queried: 2 | Sources with findings: 2**` with the multi-line format that `_render_header()` actually produces:

```markdown
**Sources queried:** local, corporate-platform
**Sources with findings:** local, corporate-platform
```

Mirror to plugin-dir:

```bash
cp skills/kb-query/SKILL.md plugins/sdlc-knowledge-base/skills/kb-query/SKILL.md
```

- [ ] **Step 5: Spec §5.1 row 4 update**

In `docs/superpowers/specs/2026-04-24-cross-library-kb-query-design.md`, find the §5.1 validation table. Update the row about path-existence checks to reflect actual implementation:

The row currently says path-existence emits a warning at load time. The implementation only validates at dispatch time (Task 4 above wires this in). Update the row to:

> Non-existent path | Validated at dispatch time by `validate_library_path` (Task 4 of Phase D). Source is skipped from the dispatch list with a warning. The registry loader does not validate paths at load time so a temporarily-unmounted drive does not cause registry-wide failure.

- [ ] **Step 6: LibrarySource.description — keep but document**

In `plugins/sdlc-knowledge-base/scripts/registry.py`, update the `LibrarySource` dataclass docstring or the `description` field comment:

```python
@dataclass(frozen=True)
class LibrarySource:
    """A library the skill can dispatch a librarian against.

    The `description` field is human-readable metadata for the operator's
    own reference (shown by kb-setup-consulting and kb-audit-query). It is
    not used by any dispatch-path code; the librarian never sees it.
    """
    name: str
    type: str  # "filesystem" or "remote-agent"
    path: Optional[str] = None
    description: Optional[str] = None
    staleness_threshold_days: Optional[int] = None  # NEW field — populated in Task 24
```

(Note: `staleness_threshold_days` is added preparatorily here; Task 24 fills in the staleness-check logic that uses it.)

- [ ] **Step 7: Resolve dead fixtures**

The fixtures at `tests/fixtures/kb_libraries/` are not consumed by any current test. Two options:

1. **Delete** if not needed (sub-5's priming validation will create its own fixture).
2. **Keep** if the priming validation in sub-5 will use them.

Decision: KEEP `corp-future-version`, `corp-legacy-no-header`, and `empty-dir` (these document edge cases for future tests); DELETE `local-sample`, `corp-semi-sample`, `corp-health-sample` as they are too small to be useful for sub-5 validation.

```bash
rm -rf tests/fixtures/kb_libraries/local-sample
rm -rf tests/fixtures/kb_libraries/corp-semi-sample
rm -rf tests/fixtures/kb_libraries/corp-health-sample 2>/dev/null  # may not exist
```

- [ ] **Step 8: Run all tests + packaging check**

```bash
python3 -m pytest tests/test_kb_*.py -v
python3 tools/validation/check-plugin-packaging.py
```

Expected: all tests pass, 13 plugins verified.

- [ ] **Step 9: Commit**

```bash
git add retrospectives/167-kb-cross-library-phase-a.md plugins/sdlc-knowledge-base/scripts/orchestrator.py plugins/sdlc-knowledge-base/scripts/attribution.py plugins/sdlc-knowledge-base/scripts/registry.py skills/kb-query/SKILL.md plugins/sdlc-knowledge-base/skills/kb-query/SKILL.md docs/superpowers/specs/2026-04-24-cross-library-kb-query-design.md
git rm -r --ignore-unmatch tests/fixtures/kb_libraries/local-sample tests/fixtures/kb_libraries/corp-semi-sample
git commit -m "$(cat <<'EOF'
docs(kb): fix documentation drift across phases A-C (phase D, #170)

Cleanup pass surfaced by the multi-reviewer documentation review:

- Phase A retrospective: `.sdlc-kb-libraries.json` typo fixed; Tasks
  9-13 'drift' reframed as plugin-dir-vs-root-source layer confusion;
  fix commit 557d521 referenced.
- orchestrator.py module docstring updated from 'Phase A' to span A-D.
- attribution.py docstring on check_synthesis_attribution updated to
  reflect required valid_handles parameter.
- kb-query SKILL.md Multi-source Example header format corrected to
  match _render_header() multi-line output.
- Spec §5.1 path-existence row updated to document dispatch-time
  validation (was: load-time warning, never implemented).
- LibrarySource docstring documents description field as operator-only
  metadata.
- LibrarySource gains staleness_threshold_days field (used by Task 24).

Dead fixtures (local-sample, corp-semi-sample) deleted; edge-case
fixtures kept for future tests.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Sub-feature 2: Validate priming actually works (#171)

### Task 9: Build a substantial validation fixture library

**Files:**
- Create: `tests/fixtures/kb_libraries/corp-substantial-fixture/library/_shelf-index.md`
- Create: `tests/fixtures/kb_libraries/corp-substantial-fixture/library/<5-8 topic files>.md`

This fixture must be substantial enough that priming has a real opportunity to discriminate — at least 5-8 library files covering related-but-distinct topics, each with real-looking shelf-index entries.

- [ ] **Step 1: Design the fixture's topic distribution**

The fixture represents a hypothetical corporate semiconductor library. Topics must cluster around two distinct domains where priming-induced selection should differ:

- **Cluster A (Dutch fab operations)**: nijmegen-fab-operations.md, eindhoven-fab-cleanroom.md, dutch-supply-chain.md
- **Cluster B (Austin / TSMC operations)**: austin-fab-operations.md, tsmc-cleanroom-protocols.md
- **Cluster C (general)**: euv-spec-asml-2024.md, semiconductor-yield-analysis.md, cleanroom-iso-14644.md

Each file gets shelf-index entry with:
- Distinct `Terms:` lists (some terms shared across clusters, most distinct)
- Real-looking facts with citations
- Cross-references between cluster members

A primed query about "fab operations" with local terms `[brazilian-fab, semiconductor]` should plausibly prefer cluster B (austin-fab) or cluster A (nijmegen-fab) depending on which terms the local primer surfaces.

- [ ] **Step 2: Create the shelf-index**

Create `tests/fixtures/kb_libraries/corp-substantial-fixture/library/_shelf-index.md`:

```markdown
<!-- format_version: 1 -->
<!-- last_rebuilt: 2026-04-24T10:00:00Z -->
<!-- library_handle: corp-substantial-fixture -->
<!-- library_description: Multi-topic fixture for priming validation. Covers Dutch + Austin fab operations + general cleanroom standards. -->

# Knowledge Base Shelf-Index

## 1. nijmegen-fab-operations.md

**Hash:** placeholder
**Terms:** dutch-fab, nijmegen, ASML, EUV, cleanroom, lithography, single-stage-dehumidification, NXE:3600D, semiconductor
**Facts:**
- Nijmegen fab achieved <45% RH with single-stage dehumidification (internal 2024)
- ASML NXE:3600D commissioned 2023; first wafers Q1 2024
**Links:** eindhoven-fab-cleanroom.md, dutch-supply-chain.md, euv-spec-asml-2024.md

## 2. eindhoven-fab-cleanroom.md

**Hash:** placeholder
**Terms:** dutch-fab, eindhoven, cleanroom, ISO-14644-1, class-1, particulate, monitoring, semiconductor
**Facts:**
- Eindhoven Class 1 cleanroom particulate target <10 particles/m³ at 0.1µm (ISO 14644-1, internal commissioning 2023)
**Links:** nijmegen-fab-operations.md, cleanroom-iso-14644.md

## 3. dutch-supply-chain.md

**Hash:** placeholder
**Terms:** dutch-fab, supply-chain, ASML, holland-high-tech, ecosystem, chip-shortage, semiconductor, EUV
**Facts:**
- ASML 80% of EUV market share; concentrated supply risk for non-Dutch fabs (industry analysis 2024)
**Links:** nijmegen-fab-operations.md, euv-spec-asml-2024.md

## 4. austin-fab-operations.md

**Hash:** placeholder
**Terms:** austin-fab, texas, samsung, tsmc, GAAFET, cleanroom, semiconductor, fab-construction
**Facts:**
- Austin Samsung fab Phase 2 commissioned 2024; GAAFET 3nm production line
- TSMC Arizona second fab pulled forward to 2026 due to CHIPS Act incentives
**Links:** tsmc-cleanroom-protocols.md, semiconductor-yield-analysis.md

## 5. tsmc-cleanroom-protocols.md

**Hash:** placeholder
**Terms:** tsmc, austin-fab, cleanroom, gowning, ESD, particulate, taiwan-protocols, semiconductor
**Facts:**
- TSMC standard cleanroom gowning protocol revised 2024 to require fluoroelastomer gloves
**Links:** austin-fab-operations.md, cleanroom-iso-14644.md

## 6. euv-spec-asml-2024.md

**Hash:** placeholder
**Terms:** ASML, EUV, NXE:3600D, NXE:3800E, lithography, reticle, mirror-degradation, semiconductor
**Facts:**
- NXE:3800E announced 2024; >220 wafers/hour throughput vs NXE:3600D's 160
- EUV reticle requires <45% RH for stability (ASML spec sheet 2024)
**Links:** nijmegen-fab-operations.md, dutch-supply-chain.md

## 7. semiconductor-yield-analysis.md

**Hash:** placeholder
**Terms:** yield, semiconductor, defect-density, statistical-process-control, six-sigma, fab-comparison, austin-fab, dutch-fab
**Facts:**
- Industry yield benchmarks: 90%+ for mature 28nm; 70-85% for leading-edge 3-5nm (industry data 2024)
**Links:** austin-fab-operations.md, nijmegen-fab-operations.md

## 8. cleanroom-iso-14644.md

**Hash:** placeholder
**Terms:** cleanroom, ISO-14644-1, particulate-classification, semiconductor, class-1, class-100, monitoring
**Facts:**
- ISO 14644-1:2015 defines particulate classification; class 1 = <10 particles/m³ at 0.1µm
**Links:** eindhoven-fab-cleanroom.md, tsmc-cleanroom-protocols.md
```

- [ ] **Step 3: Create the 8 topic files**

For each filename in the shelf-index, create a corresponding library file with the standard knowledge-base file structure (Key Question, Core Findings, Frameworks Reviewed, Actionable Thresholds, Design Principles, Key References, Programme Relevance). Use realistic-looking content sufficient for the librarian to draw findings from.

Don't write ALL 8 files in this plan task — write enough to demonstrate the pattern, then have the implementer subagent expand. At minimum write 3 files (one from each cluster A, B, C) as templates.

Example for `nijmegen-fab-operations.md`:

```markdown
---
title: "Nijmegen fab operations"
domain: dutch-fab, semiconductor, fab-operations
status: active
source: internal engagement notes 2024
cross_references:
  - eindhoven-fab-cleanroom.md
  - dutch-supply-chain.md
  - euv-spec-asml-2024.md
---

## Key Question

How does the Nijmegen fab operate its EUV lithography line under tight humidity tolerances?

## Core Findings

1. Single-stage dehumidification holds cleanroom RH below 45%, sufficient for ASML NXE:3600D EUV reticle stability (internal 2024 commissioning report)
2. Reticle pod transitions are buffered through an N+1 redundant load-port system to absorb humidity transients during pod swap (internal 2024)
3. ASML NXE:3600D throughput averaged 152 wafers/hour over Q1 2024, slightly below the 160 wph design target due to early-life mirror conditioning (internal Q1 2024 production report)

## Actionable Thresholds

| Metric | Threshold | Source | Signal |
|---|---|---|---|
| Cleanroom RH | <45% | ASML spec | EUV reticle warpage above |
| EUV throughput | 152-160 wph | NXE:3600D internal | Below 140 indicates conditioning issue |

## Design Principles

- Dehumidification load-balancing: N+1 redundancy at load-port absorbs transients
- Early-life mirror conditioning: 4-week ramp before nominal throughput

## Key References

1. ASML NXE:3600D operations manual, version 4.2 (2023)
2. Internal Nijmegen fab Q1 2024 production report

## Programme Relevance

Local project (Brazilian fab) is in commissioning phase; the dehumidification redundancy pattern from Nijmegen may apply directly given Brazil's higher ambient RH (75-85% vs Netherlands 60-70%).
```

(Implementer creates this and 7 more in similar shape.)

- [ ] **Step 4: Validate fixture is parseable**

```bash
cd /Users/stevejones/Documents/Development/ai-first-sdlc-practices
python3 -c "
from pathlib import Path
from sdlc_knowledge_base_scripts.format_version import parse_format_version
fixture_dir = Path('tests/fixtures/kb_libraries/corp-substantial-fixture/library')
print(f'Files: {sorted(p.name for p in fixture_dir.glob(\"*.md\"))}')
print(f'format_version: {parse_format_version(fixture_dir / \"_shelf-index.md\")}')
"
```

Expected: 9 files (8 topic + 1 shelf-index), format_version: 1.

- [ ] **Step 5: Commit**

```bash
git add tests/fixtures/kb_libraries/corp-substantial-fixture/
git commit -m "$(cat <<'EOF'
test(kb): substantial fixture for priming validation (phase D, #171)

8 topic files + shelf-index covering Dutch fab operations, Austin/TSMC
operations, and general cleanroom standards. Designed so a primed
query against the fixture has real opportunity to discriminate based
on local term overlap (e.g., a local project tagged 'brazilian-fab'
should plausibly prefer austin-fab or nijmegen-fab cluster files
depending on which local terms the librarian latches onto).

This fixture replaces the too-small local-sample / corp-semi-sample
fixtures from phase A. It will be used in the priming validation
manual run (Task 10).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 10: Execute paired priming validation queries

**Files:**
- Create: `docs/superpowers/specs/2026-04-24-priming-validation.md`

This is a **manual validation task**, not an automated test. The implementer (or Steve) executes the paired queries, observes outputs, and captures evidence.

- [ ] **Step 1: Set up the paired query environment**

Create a temporary project directory at `/tmp/kb-priming-validation/` with:
- `CLAUDE.md` containing a `## Knowledge Base` section that names a Brazilian semiconductor packaging operations project, mentions ambient RH 75-85%, and lists local domain terms `brazilian-fab, semiconductor, packaging`
- `library/_shelf-index.md` containing a small shelf-index with 2-3 entries about local site context

In `~/.sdlc/global-libraries.json`, register the corp-substantial-fixture:

```json
{
  "version": 1,
  "libraries": [
    {
      "name": "corp-substantial",
      "type": "filesystem",
      "path": "/Users/stevejones/Documents/Development/ai-first-sdlc-practices/tests/fixtures/kb_libraries/corp-substantial-fixture/library",
      "description": "Validation fixture for priming"
    }
  ]
}
```

In `/tmp/kb-priming-validation/.sdlc/libraries.json`, activate it.

- [ ] **Step 2: Run paired queries**

For each of these 3 questions, run:
1. The query with priming on (the kb-query skill standard flow, which builds and dispatches priming)
2. The query with priming forcibly off (run a special invocation that passes `priming=None` to the orchestrator)

Questions:
- Q1: "What does our research say about cleanroom humidity control under high-humidity ambient conditions?"
- Q2: "What does our research say about fab supply chain and ecosystem dependencies?"
- Q3: "What does our research say about cleanroom particulate classification?"

Capture for each query:
- Which library files the librarian selected (visible in librarian's output)
- The Selection rationale section (added in sub-7) — but for this validation task, sub-7 may not be implemented yet, so observe the file selection differences directly

- [ ] **Step 3: Compare and document**

Create `docs/superpowers/specs/2026-04-24-priming-validation.md`:

```markdown
# Priming Validation Evidence

**Date:** 2026-04-24
**Issue:** #171 (Phase D sub-5 of EPIC #164)
**Status:** [PENDING / PASSED / NEEDS_ITERATION based on outcome]

## Methodology

Paired queries against the same corporate fixture library, with priming context on vs off. Local project is a Brazilian semiconductor packaging operations project with ambient RH 75-85%; local terms `brazilian-fab, semiconductor, packaging`.

## Fixture

`tests/fixtures/kb_libraries/corp-substantial-fixture/library` — 8 topic files covering Dutch fab, Austin/TSMC fab, and general cleanroom standards.

## Results

### Q1: "What does our research say about cleanroom humidity control under high-humidity ambient conditions?"

**Priming OFF:**
- Files selected: [list]
- Findings summary: [brief]

**Priming ON:**
- Files selected: [list]
- Findings summary: [brief]
- Selection rationale (if sub-7 implemented): [quote from librarian]

**Difference observed:** [yes/no, what differed, was the difference in the right direction?]

### Q2: ... [same structure]

### Q3: ... [same structure]

## Verdict

[PASS = priming demonstrably affected file selection in the right direction on at least 2 of 3 queries. NEEDS_ITERATION = priming did not affect selection meaningfully; iterate librarian prompt and retest. FAIL = priming made selection worse — investigate prompt issues.]

## Iterations needed

[If verdict is NEEDS_ITERATION, document what was changed in the librarian prompt and which subsequent test runs showed improvement.]
```

- [ ] **Step 4: If verdict is PASS, commit and proceed**

```bash
git add docs/superpowers/specs/2026-04-24-priming-validation.md
git commit -m "$(cat <<'EOF'
docs(kb): priming validation evidence (phase D, #171)

Paired query validation against corp-substantial-fixture. Priming
demonstrably affected file selection in the [N of 3] test queries.
Verdict: PASS. The Phase B priming mechanism works as designed.

This is the HARD GATE for the rest of Phase D. With validation
passed, Tasks 11+ can proceed knowing the underlying differentiator
is real.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 4 (alternate): If verdict is NEEDS_ITERATION, iterate the librarian prompt**

Update `agents/knowledge-base/research-librarian.md` PRIMING_CONTEXT instructions to be more directive. Re-run Step 2-3. If priming still doesn't differentiate after 2-3 iterations, escalate to Steve — this may indicate a deeper design issue with the priming approach.

Each iteration is its own commit:

```bash
git add agents/knowledge-base/research-librarian.md plugins/sdlc-knowledge-base/agents/research-librarian.md docs/superpowers/specs/2026-04-24-priming-validation.md
git commit -m "fix(kb): iterate librarian PRIMING_CONTEXT instructions for priming validation (#171)

Iteration N: changed [X] in the priming-use rules. Re-validation: [outcome].

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Sub-feature 3: Audit log of confidentiality events (#172)

### Task 11: Audit module — AuditEvent + log_event + read_log

**Files:**
- Create: `plugins/sdlc-knowledge-base/scripts/audit.py`
- Create: `tests/test_kb_audit.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_kb_audit.py`:

```python
"""Unit tests for sdlc_knowledge_base_scripts.audit."""
import json
from datetime import datetime, timezone
from pathlib import Path
from sdlc_knowledge_base_scripts.audit import (
    AuditEvent,
    log_event,
    read_log,
)


def test_log_event_appends_jsonline(tmp_path: Path) -> None:
    log_path = tmp_path / "audit.log"
    event = AuditEvent(
        timestamp="2026-04-24T15:30:00Z",
        event_type="attribution_drop_retrieval",
        query="what about EUV",
        source_handle="corp-semi",
        reason="finding lacked Source library tag",
        detail={"dropped_block_titles": ["Bogus finding"]},
    )
    log_event(log_path, event)
    contents = log_path.read_text()
    line = contents.strip()
    parsed = json.loads(line)
    assert parsed["timestamp"] == "2026-04-24T15:30:00Z"
    assert parsed["event_type"] == "attribution_drop_retrieval"
    assert parsed["source_handle"] == "corp-semi"


def test_log_event_appends_multiple(tmp_path: Path) -> None:
    log_path = tmp_path / "audit.log"
    for i in range(3):
        log_event(log_path, AuditEvent(
            timestamp=f"2026-04-24T15:30:0{i}Z",
            event_type="attribution_drop_retrieval",
            query=f"q{i}",
            source_handle="local",
            reason="r",
            detail={},
        ))
    lines = log_path.read_text().strip().split("\n")
    assert len(lines) == 3


def test_read_log_filter_by_event_type(tmp_path: Path) -> None:
    log_path = tmp_path / "audit.log"
    log_event(log_path, AuditEvent("2026-04-24T15:30:00Z", "attribution_drop_retrieval", "q", "local", "r", {}))
    log_event(log_path, AuditEvent("2026-04-24T15:30:01Z", "synthesis_aborted_attribution", "q", None, "r", {}))
    log_event(log_path, AuditEvent("2026-04-24T15:30:02Z", "attribution_drop_retrieval", "q", "corp", "r", {}))
    drops = read_log(log_path, event_type="attribution_drop_retrieval")
    assert len(drops) == 2
    aborts = read_log(log_path, event_type="synthesis_aborted_attribution")
    assert len(aborts) == 1


def test_read_log_filter_by_source_handle(tmp_path: Path) -> None:
    log_path = tmp_path / "audit.log"
    log_event(log_path, AuditEvent("2026-04-24T15:30:00Z", "attribution_drop_retrieval", "q", "local", "r", {}))
    log_event(log_path, AuditEvent("2026-04-24T15:30:01Z", "attribution_drop_retrieval", "q", "corp", "r", {}))
    locals = read_log(log_path, source_handle="local")
    assert len(locals) == 1
    corps = read_log(log_path, source_handle="corp")
    assert len(corps) == 1


def test_read_log_filter_by_date_range(tmp_path: Path) -> None:
    log_path = tmp_path / "audit.log"
    log_event(log_path, AuditEvent("2026-01-01T00:00:00Z", "attribution_drop_retrieval", "old", "local", "r", {}))
    log_event(log_path, AuditEvent("2026-04-24T00:00:00Z", "attribution_drop_retrieval", "new", "local", "r", {}))
    recent = read_log(log_path, since="2026-04-01T00:00:00Z")
    assert len(recent) == 1
    assert recent[0].query == "new"


def test_read_log_missing_file_returns_empty(tmp_path: Path) -> None:
    log_path = tmp_path / "missing.log"
    assert read_log(log_path) == []


def test_read_log_malformed_lines_skipped(tmp_path: Path) -> None:
    log_path = tmp_path / "audit.log"
    log_event(log_path, AuditEvent("2026-04-24T15:30:00Z", "attribution_drop_retrieval", "q", "local", "r", {}))
    # Append a malformed line
    with log_path.open("a") as f:
        f.write("this is not json\n")
    log_event(log_path, AuditEvent("2026-04-24T15:30:01Z", "attribution_drop_retrieval", "q", "local", "r", {}))
    events = read_log(log_path)
    assert len(events) == 2  # malformed line skipped
```

- [ ] **Step 2: Run tests, confirm failure**

```bash
python3 -m pytest tests/test_kb_audit.py -v
```

Expected: FAIL with ImportError.

- [ ] **Step 3: Implement audit.py**

Create `plugins/sdlc-knowledge-base/scripts/audit.py`:

```python
"""Audit log for confidentiality-relevant events in cross-library kb-query.

Events written here are durable trails of: attribution drops, synthesis
aborts, dispatcher failures, no-evidence markers, and cross-library
promotions. The trail enables a consulting practice to answer questions
like "show me all attribution drops in the last 90 days" — questions
that today require re-running every query.

Phase D of EPIC #164 (sub-6, #172) — see spec §7.1 and the operational
maturity additions.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional


VALID_EVENT_TYPES = frozenset({
    "attribution_drop_retrieval",
    "synthesis_aborted_attribution",
    "synthesis_aborted_dispatcher_error",
    "source_dispatch_failed",
    "no_evidence_marker",
    "cross_library_promotion",
})


@dataclass
class AuditEvent:
    """One audit log entry. Append-only; never mutated after write."""
    timestamp: str  # ISO 8601 UTC
    event_type: str  # one of VALID_EVENT_TYPES
    query: str  # truncated to 500 chars at write
    source_handle: Optional[str]  # the relevant library, or None for orchestrator-level events
    reason: str  # human-readable cause
    detail: dict  # event-type-specific extras


_QUERY_TRUNCATION = 500


def log_event(log_path: Path, event: AuditEvent) -> None:
    """Append an audit event to the log as a JSON line.

    Truncates the query to 500 chars to bound log size on
    pathological inputs. Creates the log file if missing.
    Does NOT lock — callers serialise writes themselves
    (kb-query is not concurrent within a single project).
    """
    record = asdict(event)
    if record["query"] and len(record["query"]) > _QUERY_TRUNCATION:
        record["query"] = record["query"][:_QUERY_TRUNCATION] + "...[truncated]"
    line = json.dumps(record, ensure_ascii=False, separators=(",", ":"))
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def read_log(
    log_path: Path,
    event_type: Optional[str] = None,
    source_handle: Optional[str] = None,
    since: Optional[str] = None,  # ISO 8601 timestamp
    until: Optional[str] = None,  # ISO 8601 timestamp
) -> list[AuditEvent]:
    """Read and filter the audit log.

    Returns matching events in append order (oldest first).
    Missing file returns []. Malformed lines are skipped.
    """
    if not log_path.exists():
        return []
    results: list[AuditEvent] = []
    with log_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue  # skip malformed
            try:
                event = AuditEvent(**record)
            except TypeError:
                continue  # skip if shape doesn't match
            if event_type is not None and event.event_type != event_type:
                continue
            if source_handle is not None and event.source_handle != source_handle:
                continue
            if since is not None and event.timestamp < since:
                continue
            if until is not None and event.timestamp > until:
                continue
            results.append(event)
    return results
```

- [ ] **Step 4: Run tests, all pass**

```bash
python3 -m pytest tests/test_kb_audit.py -v
```

Expected: 7 tests pass.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/audit.py tests/test_kb_audit.py
git commit -m "$(cat <<'EOF'
feat(kb): audit module for confidentiality events (phase D, #172)

AuditEvent dataclass + log_event/read_log functions. Append-only
JSON-line log. Filters by event_type, source_handle, date range.
Truncates query to 500 chars to bound log size. Skips malformed
lines on read.

Six event types reserved: attribution_drop_retrieval,
synthesis_aborted_attribution, synthesis_aborted_dispatcher_error,
source_dispatch_failed, no_evidence_marker, cross_library_promotion.
The orchestrator and kb-promote-answer-to-library will be wired to
this module in Tasks 12, 13, and 20.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 12: Instrument orchestrator with audit logging

**Files:**
- Modify: `plugins/sdlc-knowledge-base/scripts/orchestrator.py`
- Modify: `tests/test_kb_orchestrator.py`

- [ ] **Step 1: Decide where the log path comes from**

Add a new parameter to `run_retrieval_query` and `run_synthesis_query`: `audit_log_path: Optional[Path] = None`. When None, audit logging is skipped (back-compat for tests that don't care). When set, every confidentiality-relevant event triggers `log_event` calls.

- [ ] **Step 2: Write integration test for audit logging**

Append to `tests/test_kb_orchestrator.py`:

```python
from sdlc_knowledge_base_scripts.audit import read_log


def test_orchestrator_writes_audit_event_on_attribution_drop(tmp_path: Path) -> None:
    """When a finding is dropped for missing Source library tag, an audit event is written."""
    audit_log = tmp_path / "audit.log"
    local_lib = _make_fixture_library(tmp_path, "proj", "<!-- format_version: 1 -->\n# Shelf\n")

    def mock_dispatch(req: DispatchRequest) -> str:
        return (
            "### Tagged finding\n"
            "**Finding**: ok.\n"
            "**Source library**: local\n\n"
            "### Untagged finding\n"
            "**Finding**: bad, no attribution.\n"
        )

    sources = [LibrarySource(name="local", type="filesystem", path=str(local_lib))]
    result = run_retrieval_query(
        question="q",
        sources=sources,
        priming=None,
        dispatcher=mock_dispatch,
        audit_log_path=audit_log,
    )
    events = read_log(audit_log, event_type="attribution_drop_retrieval")
    assert len(events) == 1
    assert events[0].source_handle == "local"
    assert "Untagged finding" in events[0].detail.get("dropped_block_titles", [])[0]


def test_orchestrator_writes_audit_event_on_dispatcher_failure(tmp_path: Path) -> None:
    audit_log = tmp_path / "audit.log"
    local_lib = _make_fixture_library(tmp_path, "proj", "<!-- format_version: 1 -->\n# Shelf\n")

    def mock_dispatch(req: DispatchRequest) -> str:
        raise RuntimeError("agent timeout")

    sources = [LibrarySource(name="corp", type="filesystem", path="/tmp/x")]
    # Skip path validation by using a mock that errors
    result = run_retrieval_query(
        question="q",
        sources=sources,
        priming=None,
        dispatcher=mock_dispatch,
        audit_log_path=audit_log,
    )
    events = read_log(audit_log, event_type="source_dispatch_failed")
    assert len(events) == 1
    assert events[0].source_handle == "corp"
    assert "agent timeout" in events[0].reason


def test_orchestrator_writes_audit_event_on_synthesis_abort(tmp_path: Path) -> None:
    audit_log = tmp_path / "audit.log"
    retrieval = RetrievalQueryResult(
        combined_output="output",
        sources_with_findings=["local", "corp"],
    )
    sources = [
        LibrarySource(name="local", type="filesystem", path="/x"),
        LibrarySource(name="corp", type="filesystem", path="/y"),
    ]
    bad_synth = "### Argument\n**Claim**: X.\n**Supporting evidence**:\n1. Untagged.\n**Caveats**: None.\n"
    def synth_dispatch(p): return bad_synth
    result = run_synthesis_query(
        question="how should we think",
        retrieval=retrieval,
        priming=None,
        sources=sources,
        synthesis_dispatcher=synth_dispatch,
        per_source_findings={"local": "x", "corp": "y"},
        audit_log_path=audit_log,
    )
    events = read_log(audit_log, event_type="synthesis_aborted_attribution")
    assert len(events) == 1
```

- [ ] **Step 3: Run tests, confirm failure**

```bash
python3 -m pytest tests/test_kb_orchestrator.py::test_orchestrator_writes_audit_event_on_attribution_drop -v
```

Expected: FAIL — `audit_log_path` parameter doesn't exist yet.

- [ ] **Step 4: Wire audit logging into orchestrator**

In `plugins/sdlc-knowledge-base/scripts/orchestrator.py`:

Import audit at the top:

```python
from datetime import datetime, timezone
from .audit import AuditEvent, log_event
```

Add `audit_log_path: Optional[Path] = None` parameter to `run_retrieval_query` and `run_synthesis_query`.

In `run_retrieval_query`, around the dispatcher exception handling:

```python
        try:
            raw = dispatcher(request)
        except Exception as exc:
            failed.append(source.name)
            per_source_sections[source.name] = (
                f"## [{source.name}] — failed\n\n"
                f"[{source.name}] dispatch failed: {exc}\n"
            )
            if audit_log_path is not None:
                log_event(audit_log_path, AuditEvent(
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    event_type="source_dispatch_failed",
                    query=question,
                    source_handle=source.name,
                    reason=str(exc),
                    detail={"exception_type": type(exc).__name__},
                ))
            continue
```

In `run_retrieval_query`, around the attribution post-check:

```python
        check = check_retrieval_attribution(raw)
        if check.dropped_blocks and audit_log_path is not None:
            log_event(audit_log_path, AuditEvent(
                timestamp=datetime.now(timezone.utc).isoformat(),
                event_type="attribution_drop_retrieval",
                query=question,
                source_handle=source.name,
                reason=f"{len(check.dropped_blocks)} finding(s) lacked Source library tag",
                detail={"dropped_block_titles": check.dropped_blocks},
            ))
```

In `run_synthesis_query`, in the attribution-failure branch:

```python
    if not check.passed:
        # ... existing error block construction
        if audit_log_path is not None:
            log_event(audit_log_path, AuditEvent(
                timestamp=datetime.now(timezone.utc).isoformat(),
                event_type="synthesis_aborted_attribution",
                query=question,
                source_handle=None,
                reason=f"{len(check.untagged_claims)} untagged supporting-evidence claim(s)",
                detail={"untagged_claims": check.untagged_claims},
            ))
        return SynthesisQueryResult(
            # ... existing return
        )
```

In `run_synthesis_query`, in the dispatcher-exception branch:

```python
    try:
        synthesis_output = synthesis_dispatcher(prompt)
    except Exception as exc:
        # ... existing error block
        if audit_log_path is not None:
            log_event(audit_log_path, AuditEvent(
                timestamp=datetime.now(timezone.utc).isoformat(),
                event_type="synthesis_aborted_dispatcher_error",
                query=question,
                source_handle=None,
                reason=str(exc),
                detail={"exception_type": type(exc).__name__},
            ))
        return SynthesisQueryResult(
            # ... existing return
        )
```

- [ ] **Step 5: Run tests, all pass**

```bash
python3 -m pytest tests/test_kb_*.py -v
```

Expected: all tests pass (existing tests still pass because audit_log_path defaults to None; new tests pass because the wiring works).

- [ ] **Step 6: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/orchestrator.py tests/test_kb_orchestrator.py
git commit -m "$(cat <<'EOF'
feat(kb): orchestrator writes audit events for confidentiality events (phase D, #172)

run_retrieval_query and run_synthesis_query gain an optional
audit_log_path parameter. When set, every confidentiality-relevant
event (attribution drop, synthesis abort, dispatcher failure)
appends to the audit log. When None (default), no logging — preserves
existing test behaviour.

Three event types instrumented in this commit: attribution_drop_retrieval,
source_dispatch_failed, synthesis_aborted_attribution,
synthesis_aborted_dispatcher_error. The remaining types
(no_evidence_marker, cross_library_promotion) wire in at later sub-features.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 13: kb-audit-query skill

**Files:**
- Create: `plugins/sdlc-knowledge-base/skills/kb-audit-query/SKILL.md`
- Modify: `release-mapping.yaml`

- [ ] **Step 1: Create the skill**

Create `plugins/sdlc-knowledge-base/skills/kb-audit-query/SKILL.md`:

```markdown
---
name: kb-audit-query
description: Filter and summarise the cross-library KB audit log. Reports confidentiality events (attribution drops, synthesis aborts, dispatcher failures, no-evidence markers, cross-library promotions) over a date range, by event type, and by source handle.
disable-model-invocation: false
argument-hint: "[--since <ISO-date>] [--until <ISO-date>] [--event-type <type>] [--source <handle>] [--summary]"
---

# Audit Log Query

Filter and summarise events from `library/audit.log` for the current project. The audit log is project-scope (lives in the project's library directory) and append-only; this skill is read-only.

## Arguments

All optional:

- `--since <ISO-date>` — events at or after this timestamp (e.g., `2026-01-01T00:00:00Z`)
- `--until <ISO-date>` — events at or before this timestamp
- `--event-type <type>` — one of: `attribution_drop_retrieval`, `synthesis_aborted_attribution`, `synthesis_aborted_dispatcher_error`, `source_dispatch_failed`, `no_evidence_marker`, `cross_library_promotion`
- `--source <handle>` — events for this library handle only
- `--summary` — emit count-by-type summary instead of detailed event list

## Steps

### Preflight: verify scripts importable

(Same step-0 preamble pattern as kb-query — sets sys.path from CLAUDE_PLUGIN_ROOT)

### 1. Read and filter

```bash
python3 -c "
import sys, os
sys.path.insert(0, os.path.join(os.environ.get('CLAUDE_PLUGIN_ROOT', ''), 'scripts'))
from pathlib import Path
from sdlc_knowledge_base_scripts.audit import read_log
import json

events = read_log(
    Path('library/audit.log'),
    event_type='<--event-type or None>',
    source_handle='<--source or None>',
    since='<--since or None>',
    until='<--until or None>',
)
print(json.dumps([e.__dict__ for e in events], indent=2))
"
```

### 2. Summarise (if --summary)

If `--summary` was specified, group results by event_type and count:

```python
from collections import Counter
counts = Counter(e.event_type for e in events)
for event_type, count in counts.most_common():
    print(f"{event_type}: {count}")
```

### 3. Render results

Render either:

- **Detailed view** (default): one block per event with timestamp, event_type, source_handle, reason, detail summary
- **Summary view** (`--summary`): count by type, then "see kb-audit-query --event-type X for details"

## Examples

Show all events in the last 90 days:

```
/sdlc-knowledge-base:kb-audit-query --since 2026-01-24T00:00:00Z
```

Count events by type for the last quarter:

```
/sdlc-knowledge-base:kb-audit-query --since 2026-01-01T00:00:00Z --summary
```

Investigate attribution drops on a specific source:

```
/sdlc-knowledge-base:kb-audit-query --event-type attribution_drop_retrieval --source corp-semi
```

## What this skill does NOT do

- It does not modify the audit log (read-only)
- It does not query other projects' audit logs (project-scope)
- It does not export audit data to external systems (the JSON output can be redirected if needed)

## Errors

- **Audit log file missing** — emit "No audit log at library/audit.log. Either no events have been logged yet, or this project has no library/ directory."
- **Malformed log file** — read_log skips malformed lines; the output may be smaller than expected
```

- [ ] **Step 2: Update release-mapping.yaml**

In `release-mapping.yaml`, add to the `sdlc-knowledge-base:` skills block:

```yaml
    - source: plugins/sdlc-knowledge-base/skills/kb-audit-query/SKILL.md
```

- [ ] **Step 3: Verify packaging**

```bash
python3 tools/validation/check-plugin-packaging.py
```

Expected: 13 plugins verified.

- [ ] **Step 4: Commit**

```bash
git add plugins/sdlc-knowledge-base/skills/kb-audit-query/SKILL.md release-mapping.yaml
git commit -m "$(cat <<'EOF'
feat(kb): kb-audit-query skill for filtering audit log (phase D, #172)

New skill that reads library/audit.log and filters by event type,
source handle, and date range. Supports --summary for count-by-type
output.

Lets the consulting team answer questions like:
- 'Show me all attribution drops in the last 90 days'
- 'How many synthesis aborts has corp-semi caused this quarter?'
- 'What dispatcher failures happened around the Brazil engagement go-live?'

These were previously unanswerable without re-running every query.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Sub-feature 4: Librarian transparency (#173)

### Task 14: Retrieval Selection rationale in research-librarian prompt

**Files:**
- Modify root: `agents/knowledge-base/research-librarian.md`
- Mirror: `plugins/sdlc-knowledge-base/agents/research-librarian.md`

- [ ] **Step 1: Locate insertion point**

Find the existing "### Retrieval format with source attribution" section in the agent prompt (added in Phase A). The new instructions go INSIDE this section.

- [ ] **Step 2: Add Selection rationale instructions**

In `agents/knowledge-base/research-librarian.md`, find the retrieval format example. After the format block, insert:

```markdown
### Selection rationale (when priming is supplied)

When `PRIMING_CONTEXT` is supplied, your output MUST include a `Selection rationale` section after the findings. The format:

```markdown
## Selection rationale

I considered N files in the shelf-index that matched the question terms.
I chose:
- **<filename>**: [reason — typically term overlap with local_shelf_index_terms or KB config alignment]
- **<filename>**: [reason]

I did not choose:
- **<filename>**: [reason — typically no overlap with local terms, or covered a different cluster]
```

This makes your priming-influenced reasoning visible to the user, so they can evaluate whether the priming worked correctly. If priming did not influence selection (e.g., your shelf-index has no overlap with local_shelf_index_terms), state that explicitly: "Selection was based on question-only matching; the local project's terms had no overlap with my shelf-index."

When `PRIMING_CONTEXT` is absent, omit the Selection rationale section — it adds noise to single-library queries.
```

- [ ] **Step 3: Mirror to plugin**

```bash
cp agents/knowledge-base/research-librarian.md plugins/sdlc-knowledge-base/agents/research-librarian.md
```

- [ ] **Step 4: Verify packaging**

```bash
python3 tools/validation/check-plugin-packaging.py
```

- [ ] **Step 5: Commit**

```bash
git add agents/knowledge-base/research-librarian.md plugins/sdlc-knowledge-base/agents/research-librarian.md
git commit -m "$(cat <<'EOF'
feat(kb): retrieval Selection rationale in librarian prompt (phase D, #173)

When PRIMING_CONTEXT is supplied, the librarian's retrieval output
includes a Selection rationale section explaining which files were
considered, which were chosen and why, and which were rejected and
why. Makes priming-influenced reasoning visible — the user can see
whether priming biased selection in the right direction.

Suppressed when no priming is supplied (avoid noise on single-library
queries).

Manual verification will run during Task 17.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 15: Synthesis priming-influence in synthesis-librarian prompt

**Files:**
- Modify root: `agents/knowledge-base/synthesis-librarian.md`
- Mirror: `plugins/sdlc-knowledge-base/agents/synthesis-librarian.md`

The synthesis-librarian agent (created in Task 6) already mentions "priming-influence transparency" in its instruction; this task makes the format explicit.

- [ ] **Step 1: Update synthesis-librarian prompt**

In `agents/knowledge-base/synthesis-librarian.md`, find the "Priming-influence transparency" subsection. Replace it with:

```markdown
### Priming-influence transparency (when PRIMING_CONTEXT is supplied)

When PRIMING_CONTEXT is supplied, your Caveats section MUST mention how priming influenced your synthesis. The required additions:

1. **Which findings were prioritised, and why.** Example: "I prioritised findings from the corp-semi library tagged with `dutch-fab` over similar findings tagged `austin-fab`, because the local project's vocabulary includes `brazilian-fab` which is more analogous to dutch-fab in operating environment."

2. **Which findings were de-emphasised or omitted, and why.** Example: "Findings about TSMC's Taiwan-specific protocols were de-emphasised because the local project context indicates greenfield operations rather than retrofit."

3. **Whether priming changed the synthesis outcome.** Example: "Without priming, the synthesis would have averaged across all libraries; with priming, the conclusion specifically tracks the dutch-fab analog."

This makes your priming-influenced reasoning visible to the reader so they can evaluate whether the framing was correct for their decision.

When PRIMING_CONTEXT is absent, the Caveats section omits priming-influence statements — fall back to standard cross-library span / contradiction caveats only.
```

- [ ] **Step 2: Mirror to plugin**

```bash
cp agents/knowledge-base/synthesis-librarian.md plugins/sdlc-knowledge-base/agents/synthesis-librarian.md
```

- [ ] **Step 3: Verify packaging + commit**

```bash
python3 tools/validation/check-plugin-packaging.py
git add agents/knowledge-base/synthesis-librarian.md plugins/sdlc-knowledge-base/agents/synthesis-librarian.md
git commit -m "$(cat <<'EOF'
feat(kb): synthesis priming-influence transparency (phase D, #173)

The synthesis-librarian's Caveats section MUST now name (when priming
is supplied):
- Which findings were prioritised because of priming, and why
- Which findings were de-emphasised, and why
- Whether priming changed the synthesis outcome

Makes the team-quality differentiator (priming) accountable in output
form, not just in mechanism. Manual verification in Task 17.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 16: Manual verification of transparency on multiple queries

**Files:**
- Modify: `docs/superpowers/specs/2026-04-24-priming-validation.md` (extend with transparency results)

- [ ] **Step 1: Run 3-5 verification queries**

Using the corp-substantial-fixture from Task 9 and the same project setup from Task 10, run queries that should:

1. Show distinct file selection from priming
2. Show convergent file selection (priming aligned with question-only choice)
3. Show divergent file selection (priming preferred different files)
4. A synthesis query that spans both clusters
5. A query against an empty shelf-index (transparency should say "no overlap")

Capture the librarian's Selection rationale (retrieval) and Caveats priming-influence (synthesis) sections.

- [ ] **Step 2: Document outcomes**

Append to `docs/superpowers/specs/2026-04-24-priming-validation.md`:

```markdown
## Transparency verification (Phase D Task 16)

### Query 1: ... (distinct selection expected)
- Selection rationale: [quote]
- Verdict: [meaningful / not meaningful]

### Query 2-5: [same structure]

## Verdict on transparency

[PASS = at least 4 of 5 queries produce meaningful Selection rationale or Caveats. NEEDS_ITERATION = librarian transparency was missing or vague; iterate prompt.]
```

- [ ] **Step 3: If verdict PASS, commit**

```bash
git add docs/superpowers/specs/2026-04-24-priming-validation.md
git commit -m "docs(kb): manual verification of librarian transparency (phase D, #173)

5 test queries against corp-substantial-fixture confirmed Selection
rationale (retrieval) and Caveats priming-influence (synthesis) are
present and meaningful. Verdict: PASS.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Sub-feature 5: Local→corporate finding promotion (#174)

### Task 17: Extend kb-promote-answer-to-library with --target argument

**Files:**
- Modify root: `skills/kb-promote-answer-to-library/SKILL.md`
- Mirror: `plugins/sdlc-knowledge-base/skills/kb-promote-answer-to-library/SKILL.md`

- [ ] **Step 1: Read current skill**

Run: `cat skills/kb-promote-answer-to-library/SKILL.md`

Note the current arguments and steps.

- [ ] **Step 2: Add --target argument**

Update the frontmatter `argument-hint` field:

```yaml
argument-hint: "<answer-source-or-text> [--target <handle>]"
```

Add a new "Arguments" section (or extend existing):

```markdown
## Arguments

- `<answer-source-or-text>` — the answer to promote (existing argument; unchanged behaviour)
- `--target <handle>` — optional. The registered library handle to promote into. When omitted, promotes to the local library (default behaviour, backwards compatible). When set to a registered external library handle:
  - The handle must resolve in `~/.sdlc/global-libraries.json`
  - The library must be filesystem type (remote-agent rejected)
  - The library's directory must be writeable
  - The promotion writes a new file there + updates that library's shelf-index
```

- [ ] **Step 3: Add target resolution + validation step**

In the Steps section, before the existing "write the file" step, add:

```markdown
### Resolve and validate target

If `--target <handle>` was specified:

```bash
python3 -c "
import sys, os
sys.path.insert(0, os.path.join(os.environ.get('CLAUDE_PLUGIN_ROOT', ''), 'scripts'))
from pathlib import Path
from sdlc_knowledge_base_scripts.registry import (
    load_global_registry, validate_library_path
)

handle = '<--target argument>'
gr = load_global_registry(Path(os.path.expanduser('~/.sdlc/global-libraries.json')))
matches = [lib for lib in gr.libraries if lib.name == handle]
if not matches:
    print(f'ERROR: target handle {handle!r} not registered')
    exit(1)
entry = matches[0]
if entry.type != 'filesystem':
    print(f'ERROR: target {handle!r} is type {entry.type!r}; remote-agent promotion is not supported in v1')
    exit(1)
ok, reason = validate_library_path(Path(entry.path))
if not ok:
    print(f'ERROR: target path invalid: {reason}')
    exit(1)
# Check writeability
target_dir = Path(entry.path)
test_file = target_dir / '.kb-promote-write-test'
try:
    test_file.write_text('')
    test_file.unlink()
except OSError as exc:
    print(f'ERROR: target directory not writeable: {exc}')
    exit(1)
print(f'OK: target {handle!r} -> {entry.path}')
"
```

If the validator emits ERROR, surface it to the user and stop. The default behaviour (no --target, write to local) is unchanged.
```

- [ ] **Step 4: Update the file-write step**

The existing step "write the answer as a new file in `library/`" becomes "write the answer as a new file in `<target>/`" where `<target>` is either `library/` (default) or the resolved external library path from --target.

- [ ] **Step 5: Update the shelf-index rebuild step**

The existing step that runs `kb-rebuild-indexes` against the local library now runs it against the target library. If --target is set, run rebuild on the target's directory.

- [ ] **Step 6: Add user reminder about commit responsibility**

After the file-write + shelf-index update, add an output step:

```markdown
### Final report

```
Answer promoted to: <target>/<filename>.md
Target shelf-index updated: <target>/_shelf-index.md
Audit event written: cross_library_promotion (target=<handle>)

NOTE: the target library is a separate filesystem location, possibly
in its own git repo. This skill does NOT auto-commit or push the
target library. To complete promotion:
  cd <target-repo-root>
  git add library/<filename>.md library/_shelf-index.md
  git commit -m "..."
  git push
```

This reminds the user that the corporate library has its own version control discipline.
```

- [ ] **Step 7: Mirror to plugin**

```bash
cp skills/kb-promote-answer-to-library/SKILL.md plugins/sdlc-knowledge-base/skills/kb-promote-answer-to-library/SKILL.md
```

- [ ] **Step 8: Verify packaging + commit**

```bash
python3 tools/validation/check-plugin-packaging.py
git add skills/kb-promote-answer-to-library/SKILL.md plugins/sdlc-knowledge-base/skills/kb-promote-answer-to-library/SKILL.md
git commit -m "$(cat <<'EOF'
feat(kb): kb-promote-answer-to-library --target for cross-library promotion (phase D, #174)

New optional --target <handle> argument. Default behaviour unchanged:
omitting --target promotes to the local library.

With --target corporate-semi, the skill:
- Validates target handle is registered, is filesystem type, path is
  valid, and directory is writeable
- Writes the new library file into the target directory
- Updates the target library's shelf-index
- Writes a cross_library_promotion audit event
- Reminds the user that the target library has its own git discipline

This is the path by which engagement-discovered findings compound back
into corporate libraries — the team's knowledge actually accumulates
across engagements rather than calcifying in dead corporate state.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 18: Audit logging for cross-library promotion

**Files:**
- Modify: `plugins/sdlc-knowledge-base/skills/kb-promote-answer-to-library/SKILL.md`

The skill now writes a `cross_library_promotion` audit event when --target is used. The Step 7 from Task 17 referenced this without implementing it — implement now.

- [ ] **Step 1: Add audit-write step to the skill**

After the file-write + shelf-index update, before the final report:

```bash
python3 -c "
import sys, os
sys.path.insert(0, os.path.join(os.environ.get('CLAUDE_PLUGIN_ROOT', ''), 'scripts'))
from pathlib import Path
from datetime import datetime, timezone
from sdlc_knowledge_base_scripts.audit import log_event, AuditEvent

log_event(Path('library/audit.log'), AuditEvent(
    timestamp=datetime.now(timezone.utc).isoformat(),
    event_type='cross_library_promotion',
    query='<the question that produced the answer>',
    source_handle='<--target handle>',
    reason='answer promoted to external library',
    detail={
        'source_file': '<local file or answer source>',
        'target_path': '<absolute path to target library file>',
    },
))
"
```

- [ ] **Step 2: Mirror + verify + commit**

```bash
cp skills/kb-promote-answer-to-library/SKILL.md plugins/sdlc-knowledge-base/skills/kb-promote-answer-to-library/SKILL.md
python3 tools/validation/check-plugin-packaging.py
git add skills/kb-promote-answer-to-library/SKILL.md plugins/sdlc-knowledge-base/skills/kb-promote-answer-to-library/SKILL.md
git commit -m "$(cat <<'EOF'
feat(kb): cross-library promotion writes audit event (phase D, #174)

Every cross-library promotion (--target was specified) writes a
cross_library_promotion event to the project's audit log. The event
includes source file, target path, and target handle. Enables queries
like 'show me every cross-library promotion in the last quarter' via
kb-audit-query.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Sub-feature 6: Library evolution mechanism (#175)

### Task 19: Shelf-index header parser (rename and extend format_version.py)

**Files:**
- Rename: `plugins/sdlc-knowledge-base/scripts/format_version.py` → `plugins/sdlc-knowledge-base/scripts/shelf_index_header.py`
- Modify: `tests/test_kb_format_version.py` → `tests/test_kb_shelf_index_header.py` (rename + extend)
- Modify: `release-mapping.yaml`

- [ ] **Step 1: Rename module**

```bash
git mv plugins/sdlc-knowledge-base/scripts/format_version.py plugins/sdlc-knowledge-base/scripts/shelf_index_header.py
git mv tests/test_kb_format_version.py tests/test_kb_shelf_index_header.py
```

Update imports anywhere that referenced `format_version`:

```bash
grep -rln "format_version\b" plugins/sdlc-knowledge-base/ tests/ skills/ agents/ --include="*.py" --include="*.md" 2>/dev/null
```

For each match, decide whether the import name needs updating (Python imports do; documentation references to the YAML field don't).

- [ ] **Step 2: Write failing tests for richer header**

In `tests/test_kb_shelf_index_header.py`, replace the existing tests with:

```python
"""Unit tests for sdlc_knowledge_base_scripts.shelf_index_header."""
from datetime import datetime, timezone
from pathlib import Path
from sdlc_knowledge_base_scripts.shelf_index_header import (
    parse_shelf_index_header,
    ShelfIndexHeader,
    CURRENT_FORMAT_VERSION,
)


def test_parse_full_header(tmp_path: Path) -> None:
    shelf = tmp_path / "_shelf-index.md"
    shelf.write_text(
        "<!-- format_version: 1 -->\n"
        "<!-- last_rebuilt: 2026-04-24T15:30:00Z -->\n"
        "<!-- library_handle: corp-semi -->\n"
        "<!-- library_description: Corporate semiconductor findings 2024-2026 -->\n"
        "# Knowledge Base Shelf-Index\n"
    )
    header = parse_shelf_index_header(shelf)
    assert header.format_version == 1
    assert header.last_rebuilt == "2026-04-24T15:30:00Z"
    assert header.library_handle == "corp-semi"
    assert header.library_description == "Corporate semiconductor findings 2024-2026"


def test_parse_only_format_version_legacy(tmp_path: Path) -> None:
    shelf = tmp_path / "_shelf-index.md"
    shelf.write_text("<!-- format_version: 1 -->\n# Shelf\n")
    header = parse_shelf_index_header(shelf)
    assert header.format_version == 1
    assert header.last_rebuilt is None
    assert header.library_handle is None
    assert header.library_description is None


def test_parse_no_header_legacy(tmp_path: Path) -> None:
    shelf = tmp_path / "_shelf-index.md"
    shelf.write_text("# Shelf\n## Entry\n")
    header = parse_shelf_index_header(shelf)
    assert header.format_version == CURRENT_FORMAT_VERSION  # treated as v1
    assert header.last_rebuilt is None
    assert header.library_handle is None


def test_parse_unknown_future_version(tmp_path: Path) -> None:
    shelf = tmp_path / "_shelf-index.md"
    shelf.write_text(
        "<!-- format_version: 99 -->\n"
        "<!-- last_rebuilt: 2027-01-01T00:00:00Z -->\n"
        "# Shelf\n"
    )
    header = parse_shelf_index_header(shelf)
    assert header.format_version == 99
    assert header.last_rebuilt == "2027-01-01T00:00:00Z"


def test_parse_malformed_date_field(tmp_path: Path) -> None:
    shelf = tmp_path / "_shelf-index.md"
    shelf.write_text(
        "<!-- format_version: 1 -->\n"
        "<!-- last_rebuilt: not-a-date -->\n"
        "# Shelf\n"
    )
    header = parse_shelf_index_header(shelf)
    # Malformed date is parsed as the literal string; downstream consumers handle
    assert header.last_rebuilt == "not-a-date"


def test_parse_missing_file(tmp_path: Path) -> None:
    header = parse_shelf_index_header(tmp_path / "missing.md")
    assert header.format_version == CURRENT_FORMAT_VERSION
    assert header.last_rebuilt is None
```

- [ ] **Step 3: Run tests, confirm failure**

```bash
python3 -m pytest tests/test_kb_shelf_index_header.py -v
```

Expected: FAIL — current module only parses format_version.

- [ ] **Step 4: Implement extended parser**

Replace `plugins/sdlc-knowledge-base/scripts/shelf_index_header.py` with:

```python
"""Parse the shelf-index HTML-comment header block.

The header is the source of library-evolution metadata: format version,
last rebuild timestamp, library handle, and human-readable description.
All four fields are optional for backwards compatibility with libraries
predating the rich header.

Phase D of EPIC #164 (sub-9, #175) — see spec §5.3 (originally narrower
format_version-only mechanism, now expanded for library evolution).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


CURRENT_FORMAT_VERSION = 1

_HEADER_FIELD_RE = re.compile(r"^<!--\s*(\w+):\s*(.+?)\s*-->\s*$")


@dataclass
class ShelfIndexHeader:
    format_version: int = CURRENT_FORMAT_VERSION
    last_rebuilt: Optional[str] = None  # ISO 8601 string; None if absent or malformed
    library_handle: Optional[str] = None
    library_description: Optional[str] = None


def parse_shelf_index_header(shelf_index_path: Path) -> ShelfIndexHeader:
    """Parse the HTML-comment header block at the top of a shelf-index file.

    Reads consecutive lines starting with `<!-- ` until a non-comment line
    is encountered. Supports four field names: format_version, last_rebuilt,
    library_handle, library_description. Other field names are ignored.

    Missing or malformed fields default to CURRENT_FORMAT_VERSION (for
    format_version) or None (for the others).
    """
    header = ShelfIndexHeader()
    if not shelf_index_path.exists():
        return header

    with shelf_index_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            stripped = line.rstrip("\n").rstrip("\r")
            if not stripped.startswith("<!--"):
                break  # header block ends at first non-comment line
            match = _HEADER_FIELD_RE.match(stripped)
            if not match:
                continue  # malformed comment; skip
            field_name, value = match.group(1), match.group(2).strip()
            if field_name == "format_version":
                try:
                    header.format_version = int(value)
                except ValueError:
                    header.format_version = CURRENT_FORMAT_VERSION
            elif field_name == "last_rebuilt":
                header.last_rebuilt = value
            elif field_name == "library_handle":
                header.library_handle = value
            elif field_name == "library_description":
                header.library_description = value
    return header
```

- [ ] **Step 5: Update release-mapping.yaml**

Find the entry:
```yaml
    - source: plugins/sdlc-knowledge-base/scripts/format_version.py
```

Replace with:
```yaml
    - source: plugins/sdlc-knowledge-base/scripts/shelf_index_header.py
```

- [ ] **Step 6: Run tests + packaging + commit**

```bash
python3 -m pytest tests/test_kb_shelf_index_header.py -v
python3 tools/validation/check-plugin-packaging.py
git add plugins/sdlc-knowledge-base/scripts/shelf_index_header.py tests/test_kb_shelf_index_header.py release-mapping.yaml
git rm plugins/sdlc-knowledge-base/scripts/format_version.py 2>/dev/null  # already moved by git mv
git commit -m "$(cat <<'EOF'
feat(kb): rename format_version → shelf_index_header with richer schema (phase D, #175)

The shelf-index header is now a 4-field block (format_version,
last_rebuilt, library_handle, library_description) parsed by
ShelfIndexHeader / parse_shelf_index_header. All fields are
optional for backwards compatibility.

Replaces the bare format_version mechanism with a fuller
library-evolution surface. last_rebuilt enables staleness
detection (Task 22). library_handle / library_description
are useful for kb-setup-consulting onboarding (Task 26).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 20: kb-rebuild-indexes emits full header

**Files:**
- Modify root: `skills/kb-rebuild-indexes/SKILL.md`
- Mirror: `plugins/sdlc-knowledge-base/skills/kb-rebuild-indexes/SKILL.md`
- Modify root + plugin templates: `skills/kb-rebuild-indexes/templates/shelf-index-example.md`, `skills/kb-init/templates/starter-pack/library/_shelf-index.md`

- [ ] **Step 1: Update kb-rebuild-indexes SKILL.md to emit full header**

In `skills/kb-rebuild-indexes/SKILL.md`, find the "Mandatory format_version header" section (added in Phase A Task 9). Replace it with:

```markdown
### Mandatory shelf-index header

Every generated shelf-index MUST begin with these four HTML-comment header lines, in this order:

\`\`\`
<!-- format_version: 1 -->
<!-- last_rebuilt: <ISO-8601 UTC timestamp at rebuild time> -->
<!-- library_handle: <handle from registry, or empty if unregistered> -->
<!-- library_description: <one-line description, or empty> -->
\`\`\`

These four breadcrumbs are the library's evolution metadata:

- `format_version` — schema version of the shelf-index
- `last_rebuilt` — when this skill last regenerated the index; used by kb-query to surface staleness caveats
- `library_handle` — the handle this library is registered under (if any); used by kb-setup-consulting and kb-audit-query
- `library_description` — human-readable note for operator reference

If this library is registered (its path appears in `~/.sdlc/global-libraries.json`), preserve the existing `library_handle` and `library_description` from the previous header on rebuild. If they differ from the registry entry, refuse to rebuild and emit a clear error: "shelf-index handle does not match registry; refusing to overwrite. Either correct the registry or rebuild with explicit `--handle <name>`."

If `library_handle` and `library_description` are not yet set (new library), leave them as empty strings or omit those two header lines.
```

- [ ] **Step 2: Update templates**

`skills/kb-rebuild-indexes/templates/shelf-index-example.md` — prepend the full 4-line header.

`skills/kb-init/templates/starter-pack/library/_shelf-index.md` — same.

- [ ] **Step 3: Mirror to plugin-dir**

```bash
cp skills/kb-rebuild-indexes/SKILL.md plugins/sdlc-knowledge-base/skills/kb-rebuild-indexes/SKILL.md
cp skills/kb-rebuild-indexes/templates/shelf-index-example.md plugins/sdlc-knowledge-base/skills/kb-rebuild-indexes/templates/shelf-index-example.md
cp skills/kb-init/templates/starter-pack/library/_shelf-index.md plugins/sdlc-knowledge-base/skills/kb-init/templates/starter-pack/library/_shelf-index.md
```

- [ ] **Step 4: Verify + commit**

```bash
python3 tools/validation/check-plugin-packaging.py
git add skills/kb-rebuild-indexes/ plugins/sdlc-knowledge-base/skills/kb-rebuild-indexes/ skills/kb-init/templates/starter-pack/library/_shelf-index.md plugins/sdlc-knowledge-base/skills/kb-init/templates/starter-pack/library/_shelf-index.md
git commit -m "$(cat <<'EOF'
feat(kb): kb-rebuild-indexes emits full 4-field shelf-index header (phase D, #175)

Headers now include format_version, last_rebuilt, library_handle,
library_description. Library handle preserved on rebuild and
refuses to overwrite if registry says otherwise.

Templates and starter pack updated.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 21: Staleness threshold config + query-time caveat

**Files:**
- Modify: `plugins/sdlc-knowledge-base/scripts/registry.py` (read staleness_threshold_days)
- Modify: `plugins/sdlc-knowledge-base/scripts/orchestrator.py` (surface staleness in output)
- Modify: `tests/test_kb_orchestrator.py`

- [ ] **Step 1: Update LibrarySource + registry loader**

`LibrarySource` already gained `staleness_threshold_days: Optional[int] = None` in Task 8 Step 6. Now make `load_global_registry` populate it from registry entries:

```python
libraries.append(
    LibrarySource(
        name=name,
        type=raw_type,
        path=entry.get("path"),
        description=entry.get("description"),
        staleness_threshold_days=entry.get("staleness_threshold_days"),
    )
)
```

Add a default heuristic helper:

```python
def staleness_threshold_for(source: LibrarySource) -> int:
    """Default threshold heuristic when not explicitly configured.

    Local source: 14 days (project libraries should be kept fresh).
    'corp-' prefixed: 90 days (corporate libraries evolve slower).
    Otherwise: 60 days.
    """
    if source.staleness_threshold_days is not None:
        return source.staleness_threshold_days
    if source.name == "local":
        return 14
    if source.name.startswith("corp-"):
        return 90
    return 60
```

- [ ] **Step 2: Wire staleness check into run_retrieval_query**

In `orchestrator.py`, before dispatching each source, parse its shelf-index header and check staleness. If stale, append a Caveats line to that source's output:

```python
from .shelf_index_header import parse_shelf_index_header
from .registry import staleness_threshold_for
from datetime import datetime, timezone, timedelta

# Inside the per-source loop in run_retrieval_query, after the try-dispatch block:
# (approximate location — check the existing code structure)

if source.path is not None:
    header = parse_shelf_index_header(Path(source.path) / "_shelf-index.md")
    if header.last_rebuilt is not None:
        try:
            last_rebuilt_dt = datetime.fromisoformat(header.last_rebuilt.replace("Z", "+00:00"))
            age_days = (datetime.now(timezone.utc) - last_rebuilt_dt).days
            threshold = staleness_threshold_for(source)
            if age_days > threshold:
                staleness_caveat = (
                    f"\n\n**Staleness note:** {source.name} was last rebuilt "
                    f"{age_days} days ago (threshold: {threshold}). Findings may "
                    f"not reflect domain changes since {header.last_rebuilt}."
                )
                # Append to per_source_sections[source.name]
                per_source_sections[source.name] += staleness_caveat
        except (ValueError, TypeError):
            pass  # malformed timestamp; skip staleness check
```

- [ ] **Step 3: Write integration test**

Append to `tests/test_kb_orchestrator.py`:

```python
def test_orchestrator_appends_staleness_caveat_when_stale(tmp_path: Path) -> None:
    """A library whose last_rebuilt is older than threshold emits a staleness caveat."""
    lib = tmp_path / "library"
    lib.mkdir()
    # 200 days old
    old_date = (datetime.now(timezone.utc) - timedelta(days=200)).isoformat()
    (lib / "_shelf-index.md").write_text(
        f"<!-- format_version: 1 -->\n"
        f"<!-- last_rebuilt: {old_date} -->\n"
        "# Shelf\n"
    )

    def mock_dispatch(req): return f"### finding\n**Source library**: {req.source.name}\n"
    sources = [LibrarySource(name="corp-old", type="filesystem", path=str(lib), staleness_threshold_days=90)]
    result = run_retrieval_query(question="q", sources=sources, priming=None, dispatcher=mock_dispatch)
    assert "Staleness note" in result.combined_output
    assert "200 days" in result.combined_output
```

(Add `from datetime import datetime, timezone, timedelta` to the test file imports.)

- [ ] **Step 4: Run tests, all pass**

```bash
python3 -m pytest tests/test_kb_*.py -v
```

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/registry.py plugins/sdlc-knowledge-base/scripts/orchestrator.py tests/test_kb_orchestrator.py
git commit -m "$(cat <<'EOF'
feat(kb): query-time staleness caveat for outdated libraries (phase D, #175)

LibrarySource.staleness_threshold_days is loaded from registry entries.
Default heuristic: 14 days for local, 90 for corp-* prefix, 60 otherwise.

run_retrieval_query parses each source's shelf-index header, computes
last_rebuilt age, and appends a Staleness note to the source's output
when older than threshold. The note names age, threshold, and
last-rebuilt date so the user can judge how seriously to weight the
findings.

A two-year-old corporate library with confidently stated 2024 specs
no longer ships its findings without a freshness signal.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Sub-feature 7: Onboarding skill — kb-setup-consulting (#176)

### Task 22: Create kb-setup-consulting skill scaffold

**Files:**
- Create: `plugins/sdlc-knowledge-base/skills/kb-setup-consulting/SKILL.md`
- Modify: `release-mapping.yaml`

- [ ] **Step 1: Create skill**

Create `plugins/sdlc-knowledge-base/skills/kb-setup-consulting/SKILL.md`:

```markdown
---
name: kb-setup-consulting
description: Onboarding workflow for cross-library KB query in a consulting practice. Discovers existing user-scope library registrations, prompts for additions, validates each library, helps activate the relevant ones for the current project, runs a smoke test, and reports a clear "ready" or "issues to fix" verdict.
disable-model-invocation: false
argument-hint: "[--dry-run] [--verify-only]"
---

# Cross-Library KB Onboarding

Walk a new consultant or a fresh project through KB cross-library setup. Replaces the hand-walked sequence of "discover ~/.sdlc/global-libraries.json, get paths from someone, run kb-register-library or hand-edit, test it manually" with a single skill.

## Steps

### Preflight: ensure scripts importable

(Standard CLAUDE_PLUGIN_ROOT sys.path preamble.)

### 1. Discover existing user-scope registrations

Read `~/.sdlc/global-libraries.json` if it exists. List every registered library with handle, path, type, last-validated status:

```bash
python3 -c "
import sys, os
sys.path.insert(0, os.path.join(os.environ.get('CLAUDE_PLUGIN_ROOT', ''), 'scripts'))
from pathlib import Path
from sdlc_knowledge_base_scripts.registry import load_global_registry, validate_library_path
from sdlc_knowledge_base_scripts.shelf_index_header import parse_shelf_index_header

gr = load_global_registry(Path(os.path.expanduser('~/.sdlc/global-libraries.json')))
print(f'Registered libraries: {len(gr.libraries)}')
for lib in gr.libraries:
    print(f'  {lib.name}  ({lib.type})  -> {lib.path}')
    if lib.type == 'filesystem':
        ok, reason = validate_library_path(Path(lib.path))
        if ok:
            header = parse_shelf_index_header(Path(lib.path) / '_shelf-index.md')
            print(f'    last_rebuilt: {header.last_rebuilt}')
        else:
            print(f'    INVALID: {reason}')
for w in gr.warnings:
    print(f'  Warning: {w}')
"
```

### 2. Prompt for additions

If the user wants to register additional libraries that aren't already there, walk through `kb-register-library` for each one. Collect the handle, path, and description. Validate each via the same path validator before adding to the registry.

### 3. Validate all registrations

For every library in the registry (existing + new):

- Path validation: `validate_library_path` returns OK
- Header parse: shelf-index has at least format_version
- Handle consistency: if shelf-index has `library_handle`, it must match the registry name

Report per-library status. If any library has issues, list them but continue (don't block onboarding on a single broken corporate library).

### 4. Per-project activation

Read `.sdlc/libraries.json` if it exists (or initialise empty). Show the user the list of registered library handles and ask which apply to this engagement. Write the activated handles to `.sdlc/libraries.json`.

### 5. Smoke test

For each activated library, dispatch a trivial query ("test connection — do you have a shelf-index?") via the **research-librarian** agent (Agent tool). Capture which sources respond successfully.

```bash
# Pseudo-code for the smoke test loop — actual dispatch via Agent tool in skill flow
for source in activated_sources:
    prompt = format_dispatch_prompt(source, "test connection — do you have a shelf-index?", priming=None)
    # ... dispatch via Agent tool
    # ... record result
```

### 6. Final report

Output one of:

**Ready:**
```
✓ KB environment ready
  Registered libraries: 3 (corp-semi, corp-health, internal-research)
  Activated for this project: 2 (corp-semi, internal-research)
  Smoke test: 2 of 2 passed
```

**Issues to fix:**
```
✗ KB environment NOT ready — fix these issues:
  • corp-semi: path /Users/.../semi-library has no _shelf-index.md
    Suggestion: cd /Users/.../semi-library && /sdlc-knowledge-base:kb-rebuild-indexes
  • corp-health: handle in registry conflicts with shelf-index handle
    Suggestion: rebuild shelf-index with --handle corp-health, or rename registry entry
  • Smoke test failed for internal-research: dispatcher timeout

Re-run /sdlc-knowledge-base:kb-setup-consulting --verify-only after fixing.
```

## Arguments

- `--dry-run` — go through discovery + validation but don't write to `.sdlc/libraries.json` or modify any files
- `--verify-only` — skip prompting; just validate existing registry + activation and report status

## Examples

First-time setup for a new consultant:
```
/sdlc-knowledge-base:kb-setup-consulting
```

Verify environment after fixing reported issues:
```
/sdlc-knowledge-base:kb-setup-consulting --verify-only
```

Preview without writing:
```
/sdlc-knowledge-base:kb-setup-consulting --dry-run
```

## What this skill does NOT do

- It does not create corporate libraries — those exist independently and must be cloned/mounted by the user before registration
- It does not modify corporate libraries — only registers pointers
- It does not run kb-rebuild-indexes against external libraries (their owners control that)
```

- [ ] **Step 2: Wire into release-mapping**

In `release-mapping.yaml`, add to the `sdlc-knowledge-base:` skills block:

```yaml
    - source: plugins/sdlc-knowledge-base/skills/kb-setup-consulting/SKILL.md
```

- [ ] **Step 3: Verify + commit**

```bash
python3 tools/validation/check-plugin-packaging.py
git add plugins/sdlc-knowledge-base/skills/kb-setup-consulting/SKILL.md release-mapping.yaml
git commit -m "$(cat <<'EOF'
feat(kb): kb-setup-consulting onboarding skill (phase D, #176)

Replaces hand-walked onboarding (discover ~/.sdlc/global-libraries.json,
get paths from someone, register/edit, test) with one skill that:

1. Discovers existing user-scope registrations + their validation status
2. Prompts for additional library registrations
3. Validates every registry entry (path, header, handle consistency)
4. Helps activate the relevant ones in .sdlc/libraries.json
5. Runs a smoke test against each activated library
6. Reports clear "ready" or "issues to fix" with actionable suggestions

A new consultant joining a practice can run this once and either be
ready or have a concrete punch-list. --dry-run and --verify-only modes
support troubleshooting without writes.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 23: kb-verify standalone helper

**Files:**
- The `--verify-only` mode of `kb-setup-consulting` covers this. No separate skill needed.

- [ ] **Verify the --verify-only path is documented in the kb-setup-consulting skill from Task 22.** It is. No new commit.

---

## Sub-feature 8: Phase D feature proposal + retrospective + EPIC closure

### Task 24: Phase D feature proposal + retrospective scaffold

**Files:**
- Create: `docs/feature-proposals/170-kb-cross-library-phase-d.md`
- Create: `retrospectives/170-kb-cross-library-phase-d.md`

- [ ] **Step 1: Create feature proposal**

Create `docs/feature-proposals/170-kb-cross-library-phase-d.md` covering the 7 sub-features (#170-#176). Standard format. Include the success criteria from each sub-feature issue.

- [ ] **Step 2: Create retrospective scaffold**

Create `retrospectives/170-kb-cross-library-phase-d.md` with the standard placeholder sections.

- [ ] **Step 3: Commit**

```bash
git add docs/feature-proposals/170-kb-cross-library-phase-d.md retrospectives/170-kb-cross-library-phase-d.md
git commit -m "docs: feature proposal + retrospective scaffold for phase D (#170-#176)

Required by CONSTITUTION Article 2.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

### Task 25: Final validation + EPIC #164 v1 closure

**Files:**
- Modify: `retrospectives/170-kb-cross-library-phase-d.md` (fill in)
- Modify: MEMORY.md

- [ ] **Step 1: Run full kb test suite**

```bash
python3 -m pytest tests/test_kb_*.py -v
```

Expected: ~90+ tests pass (72 from A-C + ~20 from Phase D).

- [ ] **Step 2: Plugin packaging + pre-push validation**

```bash
python3 tools/validation/check-plugin-packaging.py
python3 tools/validation/local-validation.py --pre-push
black --check plugins/sdlc-knowledge-base/scripts/ tests/test_kb_*.py
flake8 plugins/sdlc-knowledge-base/scripts/ tests/test_kb_*.py
```

Expected: All clean (modulo pre-existing pre-commit binary missing).

- [ ] **Step 3: Fill in retrospective**

Fill in `retrospectives/170-kb-cross-library-phase-d.md` with substantive content — the team-quality reframing, the validation outcomes, the operational trust gained, and what the next EPIC (RemoteAgentSource as Phase E) should consider.

- [ ] **Step 4: Update MEMORY.md**

Phase A+B+C+D complete on `feature/164-cross-library-kb-query`. EPIC #164 v1 feature-complete and ready for PR. Phase E (RemoteAgentSource) is a separate future EPIC.

- [ ] **Step 5: Commit**

```bash
git add retrospectives/170-kb-cross-library-phase-d.md
git commit -m "docs: complete phase D retrospective; EPIC #164 v1 ready for PR

Phase D closes the operational maturity gap surfaced by the multi-
reviewer assessment. EPIC #164 v1 (Phases A+B+C+D) feature-complete
on this branch.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

- [ ] **Step 6: Report**

```bash
git log main..HEAD --oneline | wc -l
git status
```

Phase D complete. EPIC #164 v1 feature-complete, ready for PR.

---

## Self-review

**Spec coverage:**

| Sub-feature (issue) | Tasks | Coverage |
|---|---|---|
| #170 sub-4 (cleanup + security) | 1-8 | black/flake8, name validation, path validation, valid_handles required, synthesis-librarian agent, sys.path, doc drift |
| #171 sub-5 (validate priming — HARD GATE) | 9-10 | Substantial fixture + paired query validation |
| #172 sub-6 (audit log) | 11-13 | audit module, orchestrator instrumentation, kb-audit-query skill |
| #173 sub-7 (transparency) | 14-16 | Retrieval Selection rationale, synthesis priming-influence, manual verification |
| #174 sub-8 (promotion) | 17-18 | --target argument, validation, audit event |
| #175 sub-9 (evolution) | 19-21 | Richer header parser, kb-rebuild-indexes update, staleness caveat |
| #176 sub-10 (onboarding) | 22-23 | kb-setup-consulting skill (covers --verify-only) |
| Final | 24-25 | Proposal + retrospective + EPIC closure |

All sub-features covered. ~25 tasks total.

**Placeholder scan:** no TBDs in implementation tasks. The retrospective has explicit "Fill in at end" markers. Task 9 step 3 acknowledges that the implementer creates 8 fixture files — not all 8 are spelled out verbatim, but the structure and one full template example is given.

**Type consistency:** new types `AuditEvent`, `ShelfIndexHeader` consistent across tasks. Function names `validate_library_path`, `staleness_threshold_for`, `parse_shelf_index_header`, `log_event`, `read_log` consistent.

**Plugin-dir lesson coverage:** Tasks 6, 7, 8, 14, 15, 17, 18, 20 explicitly call out the root-first / mirror / verify pattern. Tasks 11-13 (audit module + skill) and 22 (onboarding skill) are in-plugin only and don't need mirroring.

---

## Execution handoff

Plan complete and saved to `docs/superpowers/plans/2026-04-24-cross-library-kb-query-phase-d-operational-maturity.md`. Two execution options:

**1. Subagent-Driven (recommended)** — fresh subagent per task with two-stage review, same as Phases A/B/C.

**2. Inline Execution** — `superpowers:executing-plans` with checkpoints.

Phase D is bigger than B and C (~25 tasks vs 7 each). Subagent-driven scaling matches Phases A's pace (~2-4 minutes per task plus reviews). Estimated total time: 6-10 working days of execution.

The Task 10 priming validation is a HARD GATE — if priming doesn't actually demonstrate behavioural change, the rest of Phase D pauses until the librarian prompt is iterated to make priming work. This is intentional: the operational layer is only worth building on top of a feature that demonstrably exists.
