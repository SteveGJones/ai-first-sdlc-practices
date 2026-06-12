# kb-offline M2c — federation-aware lint design (read-only hygiene report)

**Issue:** #211 (EPIC kb-offline). **Branch:** `feature/211-kb-offline-langgraph`. **Builds on:** the existing within-library lint (`kb_lint_fix.fix_missing_fields`), the #164 registry (`resolve_dispatch_list`, `staleness_threshold_for`, `LibrarySource`), `shelf_index_header.parse_shelf_index_header`, and M2b's `_resolve_libraries` pattern. **Parent:** `docs/superpowers/specs/2026-06-06-kb-offline-langgraph-design.md` (wiki enhancement #5 "Federation-aware hygiene").

**Goal:** A read-only `kb-offline lint` that reports library hygiene across the local + federated libraries — per-library frontmatter completeness plus cross-library staleness — gateable by CI/cron.

**Decomposition note:** M2 = M2a (promote, DONE) / M2b (federation query, DONE) / **M2c (federation-aware lint, this spec)**. M2c is the last M2 piece. It is **model-free** (pure filesystem + header parsing — no LangGraph, no backend).

---

## Decisions (from brainstorm)

1. **Semantic conflict detection deferred to M3.** "Same claim with conflicting values across libraries" reliably needs semantic matching, which M3's embeddings provide. M2c ships only the deterministic, reliable halves; a crude term-overlap heuristic would be too noisy to be worth shipping.
2. **Cross-library staleness** = each library's shelf-index `last_rebuilt` vs its `staleness_threshold_for` (local 14d / `corp-` 90d / else 60d / explicit `staleness_threshold_days`).
3. **Within-library checks** = frontmatter completeness only (all the existing within-library lint covers), run **read-only** via `fix_missing_fields(..., dry_run=True)`.
4. **`now` is injected** for testability (default `datetime.now(timezone.utc)`); the CLI passes real wall-clock — a lint report legitimately uses it (not resume-sensitive).
5. **Exit 1 if any frontmatter issue or stale library, 0 if clean** (CI/cron-gateable); the full report prints regardless.
6. **Model-free, no graph** — `lint` is a sequential CLI command over the resolved library set.

---

## §1 `lint.py` — staleness check

```python
from dataclasses import dataclass

@dataclass
class StalenessResult:
    handle: str
    state: str          # "fresh" | "stale" | "unknown"
    age_days: int | None
    threshold_days: int
    last_rebuilt: str | None

def check_staleness(source, *, now) -> StalenessResult:
    """Parse <library>/_shelf-index.md header last_rebuilt; compare age vs
    registry.staleness_threshold_for(source). last_rebuilt absent/malformed -> 'unknown'."""
```
- `now` is a `datetime` (tz-aware UTC); injected for deterministic tests.
- `age_days = (now - parse(last_rebuilt)).days`; `state = "stale" if age_days > threshold else "fresh"`. Malformed/absent `last_rebuilt` (the `ShelfIndexHeader.last_rebuilt is None` case) → `state="unknown"`, `age_days=None`.

## §2 `lint.py` — frontmatter check (read-only, reuses existing)

```python
@dataclass
class FrontmatterIssue:
    page: str
    detail: str         # what's missing / malformed

def check_frontmatter(library_path) -> list[FrontmatterIssue]:
    """Read-only within-library frontmatter completeness check. Runs
    kb_lint_fix.fix_missing_fields(library_path, dry_run=True) and reports the would-fix
    items WITHOUT writing. Scope = frontmatter completeness only (no semantic checks)."""
```
- Implementation reads the `FixResult` returned by `fix_missing_fields(library_path, dry_run=True)`. **Planning note:** confirm `FixResult` exposes the per-page would-fix detail in dry-run; if it only exposes counts, add a thin read-only frontmatter scanner in `lint.py` (parse each page's frontmatter, report missing `layer`/`confidence`/`title`) rather than depending on the fixer's internal detail. Either way `check_frontmatter` writes nothing.
- **No conflict detection** — explicitly out of scope (M3).

## §3 Aggregate + render

```python
@dataclass
class LibraryLintResult:
    handle: str
    path: str
    frontmatter_issues: list   # FrontmatterIssue
    staleness: StalenessResult

@dataclass
class LintReport:
    libraries: list            # LibraryLintResult
    @property
    def has_issues(self) -> bool: ...   # True if any frontmatter issue OR any stale library

def lint_libraries(sources, *, now) -> LintReport:
    """For each LibrarySource: check_frontmatter(source.path) + check_staleness(source, now=now)."""

def render_lint_report(report) -> tuple[str, bool]:
    """Markdown report (per-library section: frontmatter issues + staleness state;
    summary line 'N libraries, Y with frontmatter issues, Z stale'). Returns (text, has_issues)."""
```
- `has_issues` counts a frontmatter issue OR a `stale` library. `unknown` staleness is reported but does **not** by itself set `has_issues` (it's a "couldn't determine" nudge, not a hard failure) — surfaced in the report so the operator sees it.

## §4 CLI `lint`

```
kb-offline lint [--library <local root>] [--libraries a,b,c]
```
- Resolves its **own** `DispatchList` (full `LibrarySource` objects — needed for per-source staleness thresholds; M2b's `_resolve_libraries` returns lossy `[[name, path]]` which drops the source type/threshold). Uses `resolve_dispatch_list(load_global_registry(~/.sdlc/global-libraries.json), ProjectActivation(activated_sources=handles), local_lib)`. With no `--libraries`, lints just the local library (implicit-local from the resolver).
- A `sources_override` test seam (analogous to M2b's `library_specs_override`) bypasses registry resolution for hermetic tests.
- Prints `render_lint_report(...)[0]`; surfaces dispatch warnings to stderr; **exits 1 if `report.has_issues` else 0**.

## Components & isolation

| File | Responsibility |
|---|---|
| `scripts/lint.py` (new) | `check_staleness`, `check_frontmatter`, `lint_libraries`, `render_lint_report` + the dataclasses |
| `scripts/kb_offline_cli.py` (modify) | `lint` subcommand (own DispatchList resolution + `sources_override` seam + exit code) |
| Tests | `tests/test_kb_offline_lint.py`, append CLI test to `tests/test_kb_offline_cli.py` |

(`kb_lint_fix.py` is reused read-only via `dry_run=True`; not modified unless the planning note's thin-scanner fallback is needed.)

## Out of scope (correctly deferred)

- **Semantic cross-library conflict detection** (same claim, divergent value) → M3 (embeddings make same-claim matching reliable).
- Auto-fixing lint issues — `lint` is read-only; `kb_lint_fix` remains the (separate) fixer.
- Within-library checks beyond frontmatter completeness (broken citations, etc.) — not part of the existing within-library lint; out of scope.
- Embedding accelerator (M3).

## Decisions log (M2c delta)

1. Semantic conflict detection deferred to M3; M2c ships staleness + read-only frontmatter report only.
2. Staleness = shelf-index `last_rebuilt` vs `staleness_threshold_for(source)`; absent/malformed → `unknown` (reported, non-failing).
3. Frontmatter check is read-only via `fix_missing_fields(dry_run=True)` (thin-scanner fallback if FixResult detail is insufficient).
4. `now` injected for determinism; CLI uses wall-clock.
5. Exit 1 on any frontmatter issue or stale library; 0 if clean; `unknown` staleness does not fail the gate.
6. `lint` resolves its own full `DispatchList` (LibrarySource) for staleness thresholds; `sources_override` test seam; model-free, no graph.
