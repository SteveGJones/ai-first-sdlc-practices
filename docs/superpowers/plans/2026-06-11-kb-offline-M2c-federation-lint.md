# kb-offline M2c — federation-aware lint Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A read-only `kb-offline lint` reporting library hygiene across the local + federated libraries — per-library frontmatter completeness plus cross-library staleness — gateable by CI/cron.

**Architecture:** Model-free, no graph. A new `lint.py` provides `check_frontmatter` (read-only scanner reusing the within-library fixer's required-field set), `check_staleness` (shelf-index `last_rebuilt` vs `staleness_threshold_for`, injected `now`), `lint_libraries` (aggregate), `render_lint_report` (markdown + `has_issues`). A CLI `lint` subcommand resolves its own `DispatchList` (full `LibrarySource` for staleness thresholds) and exits 1 on any issue.

**Tech Stack:** Python 3.9+, the project `.venv`, pytest. No backend/model. Spec: `docs/superpowers/specs/2026-06-11-kb-offline-M2c-federation-lint-design.md`.

---

## Environment & scope

- **`.venv` for everything**: `cd /Users/stevejones/Documents/Development/ai-first-sdlc-practices && .venv/bin/python -m pytest …`. Lint gate: `.venv/bin/python -m flake8 --max-line-length=127`.
- Commit trailer: `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`.
- **In scope:** `lint.py` (frontmatter + staleness + aggregate + render), CLI `lint`, the shared required-field constant in `kb_lint_fix.py`.
- **Out of scope:** semantic cross-library conflict detection (M3); auto-fixing (the separate `kb_lint_fix` fixer); within-library checks beyond frontmatter completeness; embeddings (M3).

## Reused APIs (verified against source)

- `kb_lint_fix.py`: `_is_library_file(path, library_path) -> bool` (excludes `_EXCLUDED_NAMES={_shelf-index.md,_index.md,log.md}`, `_EXCLUDED_DIRS={raw}`, non-`.md`); `_FRONTMATTER_RE` (frontmatter block regex). `_fix_existing_frontmatter` treats **`layer`, `confidence`, `cross_references`** as required-on-existing-frontmatter; pages with NO frontmatter block are fully stubbed. `FixResult` exposes only COUNTS (files_fixed/fields_added/files_skipped/errors) — NOT per-page detail, so `check_frontmatter` is a thin scanner, NOT a `fix_missing_fields(dry_run=True)` caller.
- `shelf_index_header.parse_shelf_index_header(shelf_index_path: Path) -> ShelfIndexHeader` with `.last_rebuilt: Optional[str]` (ISO 8601 or None).
- `registry.staleness_threshold_for(source: LibrarySource) -> int` (days; local 14 / `corp-` 90 / else 60, or `source.staleness_threshold_days` if set). `registry.LibrarySource(name, type, path: Optional[str], staleness_threshold_days: Optional[int], ...)`. `registry.load_global_registry(path)`, `ProjectActivation(activated_sources=[...])`, `resolve_dispatch_list(registry, activation, local_lib) -> DispatchList(sources: [LibrarySource], warnings, is_empty_error)`. Global registry path = `Path(os.path.expanduser("~/.sdlc/global-libraries.json"))`.
- `yaml` (PyYAML) for frontmatter parsing — already a dependency.
- CLI conventions: `kb_offline_cli.py` `main(argv=None, *, backend_override=None, allowed_layers=None, library_specs_override=None)`; `import sys`/`Path` present; subparsers under `sub`.

## File structure (M2c)

| File | Responsibility |
|---|---|
| `scripts/kb_lint_fix.py` (modify) | extract `REQUIRED_EXISTING_FIELDS = ("layer", "confidence", "cross_references")` constant; `_fix_existing_frontmatter` uses it (behavior-preserving) |
| `scripts/lint.py` (new) | `FrontmatterIssue`, `StalenessResult`, `LibraryLintResult`, `LintReport`, `check_frontmatter`, `check_staleness`, `lint_libraries`, `render_lint_report` |
| `scripts/kb_offline_cli.py` (modify) | `lint` subcommand (own DispatchList resolution + `sources_override` seam + exit code) |
| Tests | `tests/test_kb_offline_lint.py`, append CLI test to `tests/test_kb_offline_cli.py` |

---

## Task 1: shared required-field constant + `check_frontmatter`

**Files:** Modify `scripts/kb_lint_fix.py`; Create `scripts/lint.py`; Test `tests/test_kb_offline_lint.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_kb_offline_lint.py`:
```python
"""Federation-aware lint tests (model-free). kb-offline M2c (#211)."""
from __future__ import annotations

from sdlc_knowledge_base_scripts.lint import FrontmatterIssue, check_frontmatter


def _page(lib, name, body):
    (lib / name).write_text(body, encoding="utf-8")


def test_check_frontmatter_flags_missing_fields(tmp_path):
    lib = tmp_path / "library"
    lib.mkdir()
    # complete page — no issue
    _page(lib, "good.md", "---\nlayer: evidence\nconfidence: high\ncross_references: []\n---\n# Good\nok\n")
    # missing confidence + cross_references
    _page(lib, "partial.md", "---\nlayer: evidence\n---\n# Partial\nbody\n")
    # no frontmatter block at all
    _page(lib, "bare.md", "# Bare\njust text\n")
    # excluded meta files must be ignored
    _page(lib, "_shelf-index.md", "<!-- format_version: 1 -->\n# Shelf\n")
    issues = check_frontmatter(lib)
    by_page = {i.page: i for i in issues}
    assert "good.md" not in by_page                    # complete -> no issue
    assert "_shelf-index.md" not in by_page            # meta excluded
    assert "confidence" in by_page["partial.md"].detail and "cross_references" in by_page["partial.md"].detail
    assert "layer" not in by_page["partial.md"].detail  # present, not flagged
    assert "frontmatter" in by_page["bare.md"].detail.lower()   # no block -> flagged


def test_check_frontmatter_clean_library_returns_empty(tmp_path):
    lib = tmp_path / "library"
    lib.mkdir()
    _page(lib, "a.md", "---\nlayer: evidence\nconfidence: high\ncross_references: []\n---\n# A\n")
    assert check_frontmatter(lib) == []
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_lint.py -k frontmatter -v`
Expected: FAIL (ModuleNotFoundError: lint).

- [ ] **Step 3: Extract the shared constant in `kb_lint_fix.py`**

In `scripts/kb_lint_fix.py`, near the top (after `_EXCLUDED_DIRS`), add:
```python
# Required frontmatter fields on a page that ALREADY has a frontmatter block. Shared with
# lint.check_frontmatter so the read-only lint and the fixer never disagree on completeness.
REQUIRED_EXISTING_FIELDS = ("layer", "confidence", "cross_references")
```
Refactor `_fix_existing_frontmatter` to use it (behavior-preserving — same three fields, same defaults). Replace the three hard-coded `if "x" not in fm` blocks with a loop that preserves the exact default values + insertion order:
```python
    _DEFAULTS = {"layer": "uncategorized", "confidence": "medium", "cross_references": "[]"}
    for fieldname in REQUIRED_EXISTING_FIELDS:
        if fieldname not in fm:
            new_field_lines.append(f"{fieldname}: {_DEFAULTS[fieldname]}")
            additions.append(fieldname)
```
(Keep `_DEFAULTS` local to the function or module-level — match the file's style. Verify the existing `_fix_existing_frontmatter` tests still pass: the output must be byte-identical — same fields, same `layer: uncategorized`/`confidence: medium`/`cross_references: []` defaults, same order.)

- [ ] **Step 4: Implement `check_frontmatter` in new `scripts/lint.py`**

Create `scripts/lint.py`:
```python
"""Federation-aware hygiene lint (read-only). kb-offline M2c (#211). Model-free: per-library
frontmatter completeness + cross-library staleness. Semantic conflict detection is deferred
to M3 (needs embeddings for reliable same-claim matching)."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import yaml

from .kb_lint_fix import _FRONTMATTER_RE, _is_library_file, REQUIRED_EXISTING_FIELDS


@dataclass
class FrontmatterIssue:
    page: str
    detail: str


def check_frontmatter(library_path) -> list:
    """Read-only frontmatter completeness scan. Reports pages missing a frontmatter block, or
    missing any REQUIRED_EXISTING_FIELDS. Reuses the fixer's file-exclusion + required-field
    definitions so lint and fix agree. Writes nothing."""
    lib = Path(library_path)
    issues = []
    for md in sorted(lib.rglob("*.md")):
        if not _is_library_file(md, lib):
            continue
        text = md.read_text(encoding="utf-8")
        m = _FRONTMATTER_RE.match(text)
        if not m:
            issues.append(FrontmatterIssue(page=md.name, detail="missing frontmatter block"))
            continue
        try:
            fm = yaml.safe_load(m.group(2))
            if not isinstance(fm, dict):
                fm = {}
        except yaml.YAMLError:
            issues.append(FrontmatterIssue(page=md.name, detail="malformed frontmatter YAML"))
            continue
        missing = [f for f in REQUIRED_EXISTING_FIELDS if f not in fm]
        if missing:
            issues.append(FrontmatterIssue(page=md.name, detail=f"missing fields: {', '.join(missing)}"))
    return issues
```
(`md.name` matches the test's `by_page` keys; rglob + `_is_library_file` mirrors the fixer's traversal incl. the `raw/` + meta exclusions.)

- [ ] **Step 5: Run to verify pass**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_lint.py -k frontmatter -v` → 2 passed.
Then `.venv/bin/python -m pytest tests/ -k "lint or kb and not live" -q` (the existing kb_lint_fix tests must still pass — proves the constant refactor is behavior-preserving) + flake8 clean on `scripts/kb_lint_fix.py scripts/lint.py tests/test_kb_offline_lint.py`.

- [ ] **Step 6: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/kb_lint_fix.py plugins/sdlc-knowledge-base/scripts/lint.py tests/test_kb_offline_lint.py
git commit -m "$(cat <<'EOF'
feat(kb-offline): lint.check_frontmatter (read-only) + shared REQUIRED_EXISTING_FIELDS (#211)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: `check_staleness`

**Files:** Modify `scripts/lint.py`; Test append to `tests/test_kb_offline_lint.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_kb_offline_lint.py`:
```python
from datetime import datetime, timedelta, timezone

from sdlc_knowledge_base_scripts.lint import StalenessResult, check_staleness
from sdlc_knowledge_base_scripts.registry import LibrarySource


def _lib_with_rebuilt(tmp_path, name, rebuilt_iso):
    lib = tmp_path / name
    lib.mkdir()
    header = "" if rebuilt_iso is None else f"<!-- last_rebuilt: {rebuilt_iso} -->\n"
    (lib / "_shelf-index.md").write_text(f"<!-- format_version: 1 -->\n{header}# Shelf\n")
    return lib


_NOW = datetime(2026, 6, 11, tzinfo=timezone.utc)


def test_staleness_fresh(tmp_path):
    lib = _lib_with_rebuilt(tmp_path, "local", (_NOW - timedelta(days=5)).isoformat())
    src = LibrarySource(name="local", type="filesystem", path=str(lib))  # local threshold = 14
    res = check_staleness(src, now=_NOW)
    assert res.state == "fresh" and res.age_days == 5 and res.threshold_days == 14


def test_staleness_stale(tmp_path):
    lib = _lib_with_rebuilt(tmp_path, "local", (_NOW - timedelta(days=30)).isoformat())
    src = LibrarySource(name="local", type="filesystem", path=str(lib))  # 14
    res = check_staleness(src, now=_NOW)
    assert res.state == "stale" and res.age_days == 30


def test_staleness_unknown_when_no_last_rebuilt(tmp_path):
    lib = _lib_with_rebuilt(tmp_path, "local", None)
    src = LibrarySource(name="local", type="filesystem", path=str(lib))
    res = check_staleness(src, now=_NOW)
    assert res.state == "unknown" and res.age_days is None


def test_staleness_corp_threshold(tmp_path):
    lib = _lib_with_rebuilt(tmp_path, "corp-x", (_NOW - timedelta(days=30)).isoformat())
    src = LibrarySource(name="corp-x", type="filesystem", path=str(lib))  # corp- threshold = 90
    res = check_staleness(src, now=_NOW)
    assert res.state == "fresh" and res.threshold_days == 90   # 30 < 90
```
(Confirm `LibrarySource` is constructable with `name`/`type`/`path`; if it requires more fields, add their defaults to the test construction. Confirm the shelf-index header comment form `<!-- last_rebuilt: ... -->` is what `parse_shelf_index_header` reads — read shelf_index_header.py; adapt the fixture header to the real format.)

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_lint.py -k staleness -v`
Expected: FAIL (ImportError: check_staleness/StalenessResult).

- [ ] **Step 3: Implement `check_staleness`**

Append to `scripts/lint.py`:
```python
from .registry import staleness_threshold_for          # add to imports
from .shelf_index_header import parse_shelf_index_header  # add to imports


@dataclass
class StalenessResult:
    handle: str
    state: str          # "fresh" | "stale" | "unknown"
    age_days: int | None
    threshold_days: int
    last_rebuilt: str | None


def _parse_iso_utc(value: str):
    """Parse an ISO 8601 string to a tz-aware UTC datetime; naive inputs assumed UTC."""
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def check_staleness(source, *, now=None) -> StalenessResult:
    """Compare the library's shelf-index last_rebuilt against staleness_threshold_for(source).
    last_rebuilt absent/malformed -> state 'unknown' (reported, non-failing)."""
    now = now or datetime.now(timezone.utc)
    threshold = staleness_threshold_for(source)
    shelf = Path(source.path) / "_shelf-index.md"
    last = parse_shelf_index_header(shelf).last_rebuilt if shelf.is_file() else None
    if not last:
        return StalenessResult(handle=source.name, state="unknown", age_days=None,
                               threshold_days=threshold, last_rebuilt=None)
    try:
        age_days = (now - _parse_iso_utc(last)).days
    except (ValueError, TypeError):
        return StalenessResult(handle=source.name, state="unknown", age_days=None,
                               threshold_days=threshold, last_rebuilt=last)
    state = "stale" if age_days > threshold else "fresh"
    return StalenessResult(handle=source.name, state=state, age_days=age_days,
                           threshold_days=threshold, last_rebuilt=last)
```

- [ ] **Step 4: Run to verify pass**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_lint.py -k staleness -v` → 4 passed. flake8 clean on `scripts/lint.py tests/test_kb_offline_lint.py`.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/lint.py tests/test_kb_offline_lint.py
git commit -m "$(cat <<'EOF'
feat(kb-offline): lint.check_staleness (shelf last_rebuilt vs source threshold) (#211)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: `lint_libraries` + `render_lint_report`

**Files:** Modify `scripts/lint.py`; Test append to `tests/test_kb_offline_lint.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_kb_offline_lint.py`:
```python
from sdlc_knowledge_base_scripts.lint import lint_libraries, render_lint_report


def test_lint_libraries_aggregates_and_flags(tmp_path):
    # local: fresh + a frontmatter issue; corp: stale + clean
    local = _lib_with_rebuilt(tmp_path, "local", (_NOW - timedelta(days=2)).isoformat())
    _page(local, "partial.md", "---\nlayer: evidence\n---\n# P\nbody\n")
    corp = _lib_with_rebuilt(tmp_path, "corp-x", (_NOW - timedelta(days=200)).isoformat())
    _page(corp, "ok.md", "---\nlayer: evidence\nconfidence: high\ncross_references: []\n---\n# OK\n")
    sources = [LibrarySource(name="local", type="filesystem", path=str(local)),
               LibrarySource(name="corp-x", type="filesystem", path=str(corp))]
    report = lint_libraries(sources, now=_NOW)
    assert report.has_issues is True                       # frontmatter issue + stale corp
    by_handle = {r.handle: r for r in report.libraries}
    assert by_handle["local"].frontmatter_issues           # has the partial.md issue
    assert by_handle["local"].staleness.state == "fresh"
    assert by_handle["corp-x"].staleness.state == "stale"
    assert by_handle["corp-x"].frontmatter_issues == []


def test_render_lint_report_clean_has_no_issues(tmp_path):
    lib = _lib_with_rebuilt(tmp_path, "local", (_NOW - timedelta(days=1)).isoformat())
    _page(lib, "a.md", "---\nlayer: evidence\nconfidence: high\ncross_references: []\n---\n# A\n")
    report = lint_libraries([LibrarySource(name="local", type="filesystem", path=str(lib))], now=_NOW)
    text, has_issues = render_lint_report(report)
    assert has_issues is False
    assert "local" in text and "fresh" in text.lower()


def test_unknown_staleness_does_not_fail_gate(tmp_path):
    lib = _lib_with_rebuilt(tmp_path, "local", None)   # no last_rebuilt -> unknown
    _page(lib, "a.md", "---\nlayer: evidence\nconfidence: high\ncross_references: []\n---\n# A\n")
    report = lint_libraries([LibrarySource(name="local", type="filesystem", path=str(lib))], now=_NOW)
    assert report.has_issues is False                  # unknown staleness is reported, not a failure
    text, has_issues = render_lint_report(report)
    assert "unknown" in text.lower() and has_issues is False
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_lint.py -k "aggregates or render or unknown" -v`
Expected: FAIL (ImportError).

- [ ] **Step 3: Implement aggregate + render**

Append to `scripts/lint.py`:
```python
@dataclass
class LibraryLintResult:
    handle: str
    path: str
    frontmatter_issues: list = field(default_factory=list)
    staleness: StalenessResult = None


@dataclass
class LintReport:
    libraries: list = field(default_factory=list)

    @property
    def has_issues(self) -> bool:
        return any(r.frontmatter_issues or r.staleness.state == "stale" for r in self.libraries)


def lint_libraries(sources, *, now=None) -> LintReport:
    """Per source: frontmatter issues + staleness. now injected for determinism."""
    now = now or datetime.now(timezone.utc)
    results = []
    for src in sources:
        results.append(LibraryLintResult(
            handle=src.name, path=src.path,
            frontmatter_issues=check_frontmatter(src.path),
            staleness=check_staleness(src, now=now)))
    return LintReport(libraries=results)


def render_lint_report(report) -> tuple:
    """Markdown report + has_issues. supported by a summary line."""
    lines = ["# kb-offline lint report", ""]
    n_fm = n_stale = 0
    for r in report.libraries:
        s = r.staleness
        if r.frontmatter_issues:
            n_fm += 1
        if s.state == "stale":
            n_stale += 1
        stale_desc = {
            "fresh": f"fresh ({s.age_days}d / {s.threshold_days}d)",
            "stale": f"STALE ({s.age_days}d > {s.threshold_days}d threshold)",
            "unknown": "unknown (no last_rebuilt header)",
        }[s.state]
        lines.append(f"## {r.handle}  ({r.path})")
        lines.append(f"- staleness: {stale_desc}")
        if r.frontmatter_issues:
            lines.append(f"- frontmatter: {len(r.frontmatter_issues)} issue(s)")
            for iss in r.frontmatter_issues:
                lines.append(f"    - {iss.page}: {iss.detail}")
        else:
            lines.append("- frontmatter: clean")
        lines.append("")
    lines.append(f"## Summary: {len(report.libraries)} libraries, "
                 f"{n_fm} with frontmatter issues, {n_stale} stale")
    return "\n".join(lines) + "\n", report.has_issues
```

- [ ] **Step 4: Run to verify pass**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_lint.py -v` → all pass. flake8 clean.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/lint.py tests/test_kb_offline_lint.py
git commit -m "$(cat <<'EOF'
feat(kb-offline): lint_libraries aggregate + render_lint_report (has_issues gate) (#211)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: CLI `lint` subcommand

**Files:** Modify `scripts/kb_offline_cli.py`; Test append to `tests/test_kb_offline_cli.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_kb_offline_cli.py`:
```python
def test_cli_lint_reports_and_exit_code(tmp_path, capsys):
    from datetime import datetime, timedelta, timezone
    from sdlc_knowledge_base_scripts import kb_offline_cli as cli
    from sdlc_knowledge_base_scripts.registry import LibrarySource

    def _lib(name, rebuilt_days_ago, page_body):
        lib = tmp_path / name
        lib.mkdir()
        rebuilt = (datetime.now(timezone.utc) - timedelta(days=rebuilt_days_ago)).isoformat()
        (lib / "_shelf-index.md").write_text(f"<!-- format_version: 1 -->\n<!-- last_rebuilt: {rebuilt} -->\n# Shelf\n")
        (lib / "a.md").write_text(page_body)
        return lib
    # local fresh + clean; corp stale
    local = _lib("local", 1, "---\nlayer: evidence\nconfidence: high\ncross_references: []\n---\n# A\n")
    corp = _lib("corp-x", 200, "---\nlayer: evidence\nconfidence: high\ncross_references: []\n---\n# A\n")
    sources = [LibrarySource(name="local", type="filesystem", path=str(local)),
               LibrarySource(name="corp-x", type="filesystem", path=str(corp))]
    rc = cli.main(["lint", "--library", str(local), "--libraries", "corp-x"],
                  sources_override=sources)
    out = capsys.readouterr().out
    assert "corp-x" in out and "STALE" in out
    assert rc == 1                          # corp-x is stale -> non-zero gate


def test_cli_lint_clean_exits_zero(tmp_path, capsys):
    from datetime import datetime, timedelta, timezone
    from sdlc_knowledge_base_scripts import kb_offline_cli as cli
    from sdlc_knowledge_base_scripts.registry import LibrarySource
    lib = tmp_path / "local"
    lib.mkdir()
    rebuilt = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    (lib / "_shelf-index.md").write_text(f"<!-- format_version: 1 -->\n<!-- last_rebuilt: {rebuilt} -->\n# Shelf\n")
    (lib / "a.md").write_text("---\nlayer: evidence\nconfidence: high\ncross_references: []\n---\n# A\n")
    rc = cli.main(["lint", "--library", str(lib)],
                  sources_override=[LibrarySource(name="local", type="filesystem", path=str(lib))])
    assert rc == 0
    assert "clean" in capsys.readouterr().out.lower()
```
The `sources_override` kwarg is a TEST SEAM (the real `~/.sdlc/global-libraries.json` won't exist in CI) — implement analogous to `library_specs_override`: when given, skip registry resolution and lint those `LibrarySource`s directly.

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_cli.py -k lint -v`
Expected: FAIL (`invalid choice: 'lint'` / unknown `sources_override`).

- [ ] **Step 3: Implement the CLI `lint` subcommand**

In `scripts/kb_offline_cli.py`:

Add `_cmd_lint`:
```python
def _cmd_lint(args: argparse.Namespace, sources_override=None) -> int:
    from datetime import datetime, timezone
    from .lint import lint_libraries, render_lint_report
    local_lib = Path(args.library)
    if sources_override is not None:
        sources, warnings = sources_override, []
    else:
        import os
        from .registry import (ProjectActivation, load_global_registry, resolve_dispatch_list)
        handles = [h.strip() for h in (args.libraries or "").split(",") if h.strip()]
        registry = load_global_registry(Path(os.path.expanduser("~/.sdlc/global-libraries.json")))
        dispatch = resolve_dispatch_list(registry, ProjectActivation(activated_sources=handles), local_lib)
        sources, warnings = dispatch.sources, dispatch.warnings
    for w in warnings:
        print(f"warning: {w}", file=sys.stderr)
    if not sources:
        print("no libraries resolved — run kb-init / check ~/.sdlc/global-libraries.json", file=sys.stderr)
        return 1
    report = lint_libraries(sources, now=datetime.now(timezone.utc))
    text, has_issues = render_lint_report(report)
    print(text)
    return 1 if has_issues else 0
```
Add the subparser (under `sub`):
```python
    p_lint = sub.add_parser("lint")
    p_lint.add_argument("--library", default="library")
    p_lint.add_argument("--libraries", default=None, help="comma-separated external library handles")
```
Thread `sources_override` through `main(...)`: extend its signature to `def main(argv=None, *, backend_override=None, allowed_layers=None, library_specs_override=None, sources_override=None)` and dispatch:
```python
    if args.cmd == "lint":
        return _cmd_lint(args, sources_override)
```
(Confirm the exact `sub` subparser variable + the dispatch chain; match them. `Path`/`sys` already imported.)

- [ ] **Step 4: Run to verify pass**

Run: `.venv/bin/python -m pytest tests/test_kb_offline_cli.py -k lint -v` → 2 passed. Then the full gate:
```bash
.venv/bin/python -m pytest tests/ -k "kb and not live" -q
.venv/bin/python -m flake8 --max-line-length=127 plugins/sdlc-knowledge-base/scripts/ tests/test_kb_offline_lint.py tests/test_kb_offline_cli.py
.venv/bin/python tools/validation/check-prompt-parity.py
```
All green / clean / parity OK.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/kb_offline_cli.py tests/test_kb_offline_cli.py
git commit -m "$(cat <<'EOF'
feat(kb-offline): CLI lint subcommand (read-only federation hygiene report, gateable) (#211)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Self-review notes

- **Spec coverage:** §1 staleness → Task 2 (`check_staleness`); §2 frontmatter → Task 1 (`check_frontmatter` thin scanner — confirmed necessary since `FixResult` is counts-only — + shared `REQUIRED_EXISTING_FIELDS`); §3 aggregate+render → Task 3 (`lint_libraries`/`render_lint_report`/`has_issues`); §4 CLI → Task 4 (`lint` subcommand, own DispatchList resolution, `sources_override` seam, exit 1 on issues). Decisions log 1-6 covered.
- **Type/name consistency:** `FrontmatterIssue(page, detail)`; `StalenessResult(handle, state, age_days, threshold_days, last_rebuilt)`; `LibraryLintResult(handle, path, frontmatter_issues, staleness)`; `LintReport.has_issues`; `check_frontmatter(library_path)`, `check_staleness(source, *, now=None)`, `lint_libraries(sources, *, now=None)`, `render_lint_report(report) -> (text, bool)`; `sources_override` seam — consistent across tasks.
- **Model-free, read-only:** no backend, no graph, no library writes — `check_frontmatter` only reads; `check_staleness` only reads the shelf header. The fixer refactor (Task 1) is behavior-preserving (existing kb_lint_fix tests must stay green).
- **has_issues semantics:** frontmatter issue OR `stale` → fail; `unknown` staleness reported but NOT a gate failure (decision 5; test `test_unknown_staleness_does_not_fail_gate`).
- **Known verification points:** the exact shelf-index `last_rebuilt` header format `parse_shelf_index_header` reads (Task 2 test fixture must match it — confirm against shelf_index_header.py); `LibrarySource` constructor required fields (Task 2/4 tests construct it — add defaults if more are required); the `sub` subparser var + dispatch chain in main(); confirm the existing `_fix_existing_frontmatter` tests stay byte-identical after the constant refactor.
- **No silent caps:** dispatch warnings printed; `unknown` staleness surfaced in the report; summary line counts everything.
