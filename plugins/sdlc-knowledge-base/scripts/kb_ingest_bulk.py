"""Parallel map-reduce bulk ingest for sdlc-knowledge-base (issue #208).

Pure-Python orchestration core. Agent dispatch (map extractors, reduce
updaters) happens in the SKILL.md via parallel Agent-tool calls; this module
provides discovery, manifest CRUD, extract persistence, routing, prompt
formatting, and finalize helpers. Dispatch is injected as a callable so tests
run without real Agent calls — mirrors orchestrator.py.
"""
from __future__ import annotations

import glob as _glob
import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

# Reuse the schema-agnostic atomic JSON helpers from the batch module.
# Re-exported via __all__ so the kb-ingest-bulk skill imports the whole
# orchestration surface from this one module.
from .kb_ingest_batch import load_manifest, save_manifest

__all__ = [
    "ExtractDispatchRequest",
    "ReduceDispatchRequest",
    "RouteResult",
    "discover_sources",
    "slug_for_source",
    "extract_path",
    "persist_extract",
    "build_bulk_manifest",
    "mark_source_extracted",
    "mark_source_failed",
    "mark_target_reduced",
    "mark_target_failed",
    "retry_failed",
    "normalize_slug",
    "estimate_tokens",
    "route_extracts",
    "format_extract_prompt",
    "format_reduce_prompt",
    "summarize_run",
    "write_log_entry",
    "load_manifest",
    "save_manifest",
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class ExtractDispatchRequest:
    source_path: str
    library_path: str
    shelf_index_path: str
    extractor_model: str


@dataclass(frozen=True)
class ReduceDispatchRequest:
    target_file: str
    is_new: bool
    library_path: str
    shelf_index_path: str
    extracts: list[dict]


@dataclass
class RouteResult:
    targets: dict[str, dict] = field(default_factory=dict)
    oversized: list[str] = field(default_factory=list)


def discover_sources(spec) -> list[Path]:
    """Resolve a glob string, a directory Path, or a list of paths to .md files.

    - dir  -> all *.md directly in the dir (non-recursive), sorted by name
    - glob -> files matching the pattern, sorted
    - list -> each entry resolved; missing paths skipped; deduped, order-stable
    Only files that exist are returned.
    """
    out: list[Path] = []
    seen: set[Path] = set()

    def _add(p: Path) -> None:
        rp = p.resolve()
        if rp in seen:
            return
        if p.is_file():
            seen.add(rp)
            out.append(p)

    if isinstance(spec, (list, tuple)):
        for entry in spec:
            _add(Path(entry))
        return out

    if isinstance(spec, Path) and spec.is_dir():
        for p in sorted(spec.glob("*.md")):
            _add(p)
        return out

    # Treat as glob string (also handles a dir given as str via trailing match)
    pattern = str(spec)
    if Path(pattern).is_dir():
        for p in sorted(Path(pattern).glob("*.md")):
            _add(p)
        return out
    for match in sorted(_glob.glob(pattern)):
        _add(Path(match))
    return out


_SLUG_RE = re.compile(r"[^a-z0-9]+")


def slug_for_source(path: Path) -> str:
    """Stable, filesystem-safe, collision-free slug from a source path.

    Combines the readable filename stem with a short hash of the full path so
    that two sources sharing a filename stem in different directories produce
    distinct slugs. Deterministic per path (resume-safe): the same path always
    yields the same slug regardless of which other sources are in the run.
    """
    p = Path(path)
    stem = p.stem.lower()
    base = _SLUG_RE.sub("-", stem).strip("-")
    digest = hashlib.sha1(str(p).encode("utf-8")).hexdigest()[:8]
    return f"{base}-{digest}" if base else digest


def extract_path(extracts_dir: Path, slug: str) -> Path:
    return Path(extracts_dir) / f"{slug}.json"


def persist_extract(extracts_dir: Path, slug: str, extract: dict) -> Path:
    """Write one extract as JSON to extracts_dir/<slug>.json (atomic)."""
    from .durability import atomic_write_text
    extracts_dir = Path(extracts_dir)
    extracts_dir.mkdir(parents=True, exist_ok=True)
    path = extract_path(extracts_dir, slug)
    atomic_write_text(path, json.dumps(extract, indent=2))
    return path


def build_bulk_manifest(sources, existing=None, run_meta=None) -> dict:
    """Build or update a two-phase bulk manifest.

    Preserves prior source/target status from *existing*; appends new sources
    as pending. run_meta is set only on first build.
    """
    if existing is not None:
        manifest = {
            "started_at": existing.get("started_at", _now()),
            "run_meta": existing.get("run_meta", run_meta or {}),
            "sources": dict(existing.get("sources", {})),
            "targets": dict(existing.get("targets", {})),
        }
    else:
        manifest = {
            "started_at": _now(),
            "run_meta": run_meta or {},
            "sources": {},
            "targets": {},
        }
    for p in sources:
        key = str(p)
        if key not in manifest["sources"]:
            manifest["sources"][key] = {
                "slug": slug_for_source(Path(p)),
                "status": "pending",
                "error": None,
            }
    return manifest


def mark_source_extracted(manifest: dict, path: str) -> dict:
    """Mark a source as successfully extracted."""
    manifest["sources"][path]["status"] = "extracted"
    manifest["sources"][path]["error"] = None
    return manifest


def mark_source_failed(manifest: dict, path: str, error: str) -> dict:
    """Mark a source as failed with an error message."""
    manifest["sources"][path]["status"] = "failed"
    manifest["sources"][path]["error"] = error
    return manifest


def mark_target_reduced(manifest: dict, target_file: str) -> dict:
    """Mark a target as successfully reduced."""
    manifest["targets"][target_file]["status"] = "reduced"
    manifest["targets"][target_file]["error"] = None
    return manifest


def mark_target_failed(manifest: dict, target_file: str, error: str) -> dict:
    """Mark a target as failed with an error message."""
    manifest["targets"][target_file]["status"] = "failed"
    manifest["targets"][target_file]["error"] = error
    return manifest


def retry_failed(manifest: dict) -> dict:
    """Reset all failed sources and targets back to pending."""
    for v in manifest["sources"].values():
        if v["status"] == "failed":
            v["status"] = "pending"
            v["error"] = None
    for v in manifest["targets"].values():
        if v["status"] == "failed":
            v["status"] = "pending"
            v["error"] = None
    return manifest


def normalize_slug(text: str) -> str:
    """Normalise a topic name/slug for new-topic dedup: lowercase, strip .md,
    collapse non-alphanumerics to single hyphens."""
    s = str(text).lower()
    if s.endswith(".md"):
        s = s[:-3]
    return _SLUG_RE.sub("-", s).strip("-")


def estimate_tokens(text: str) -> int:
    """Cheap token estimate: ~4 chars per token."""
    return len(text) // 4


def _target_key(target: dict, existing_files: set) -> tuple[str, bool] | None:
    """Resolve a single target entry to (target_file, is_new), or None if the
    target carries no usable identity (no 'file'/'new_topic_slug'/'title').

    Existing-file targets keep their filename. New-topic proposals are
    slug-normalised; if the normalised slug matches an existing file it routes
    there (is_new=False), else it becomes "<slug>.md" (is_new=True).
    """
    if "file" in target:
        return target["file"], False
    raw = target.get("new_topic_slug") or target.get("title") or ""
    norm = normalize_slug(raw)
    if not norm:
        return None
    candidate = f"{norm}.md"
    if candidate in existing_files:
        return candidate, False
    return candidate, True


def route_extracts(extracts, existing_files, size_threshold) -> RouteResult:
    """Group extracts by target library file.

    - existing-file targets group by filename
    - new-topic proposals are slug-normalised and fuzzy-merged (variants of the
      same slug collapse to one pre-allocated "<slug>.md")
    - a source touching multiple targets is added to each group
    - per-file: estimate combined token size; files exceeding size_threshold are
      moved to .oversized and excluded from .targets
    """
    existing_files = set(existing_files)
    targets: dict[str, dict] = {}

    for extract in extracts:
        for target in extract.get("targets", []):
            resolved = _target_key(target, existing_files)
            if resolved is None:
                continue
            tfile, is_new = resolved
            slot = targets.setdefault(
                tfile, {"extracts": [], "is_new": is_new, "est_tokens": 0}
            )
            # an existing-file resolution wins over a new-topic guess
            if not is_new:
                slot["is_new"] = False
            slot["extracts"].append(dict(extract))

    # size estimate per target (sum of its extracts' serialized size)
    oversized: list[str] = []
    for tfile, slot in list(targets.items()):
        est = sum(estimate_tokens(json.dumps(e)) for e in slot["extracts"])
        slot["est_tokens"] = est
        if est > size_threshold:
            oversized.append(tfile)
            del targets[tfile]

    return RouteResult(targets=targets, oversized=sorted(oversized))


def format_extract_prompt(req: ExtractDispatchRequest) -> str:
    """Prompt for one knowledge-extractor (map phase). Read-only; returns JSON."""
    return "\n".join([
        "MAP_EXTRACT — read-only extraction, no library writes.",
        "",
        f"Source: {req.source_path}",
        f"Library: {req.library_path}",
        f"Shelf-index: {req.shelf_index_path}",
        "",
        ("Read the source and the shelf-index (read-only — do NOT write any "
         + "library file). Emit ONLY a JSON object with this shape:"),
        "{",
        '  "source": "<source path>",',
        '  "findings": ["<concise finding>", ...],',
        '  "statistics": ["<stat with number + context>", ...],',
        '  "citations": ["<citation string>", ...],',
        '  "confidence": "high|medium|low",',
        '  "targets": [',
        '    {"file": "<existing-shelf-index-file>.md", "finding_idx": [<int>, ...]},',
        '    {"new_topic_slug": "<slug>", "title": "<Title>", "finding_idx": [<int>, ...]}',
        "  ]",
        "}",
        "",
        ("Rules: keep findings SUMMARISED (no verbatim transcription); match "
         + "existing files by name from the shelf-index; propose a new_topic "
         + "only when no existing file fits; finding_idx index into findings[]."),
    ])


def format_reduce_prompt(req: ReduceDispatchRequest) -> str:
    """Prompt for one agent-knowledge-updater (reduce phase) for a single file."""
    action = "CREATE this new file" if req.is_new else "UPDATE this existing file"
    return "\n".join([
        "BULK_REDUCE — synthesise all routed extracts into exactly one file.",
        ("Constraints: (1) write ONLY the target file; (2) Do NOT run "
         + "kb-rebuild-indexes; (3) Do NOT append to log.md."),
        "",
        f"Target file: {req.target_file} ({action})",
        f"Library: {req.library_path}",
        f"Shelf-index: {req.shelf_index_path}",
        "",
        ("Apply the standard agent-knowledge-updater rules: extend-vs-create, "
         + "contradiction flagging, citation discipline, confidence frontmatter. "
         + "You see ALL findings for this topic at once — dedupe and reconcile "
         + "contradictions across them."),
        "",
        "Extracts routed to this file (JSON):",
        json.dumps(req.extracts, indent=2),
    ])


def summarize_run(manifest: dict, oversized: list) -> str:
    """Produce a human-readable run summary (also embeddable in log.md)."""
    sources = manifest["sources"]
    targets = manifest["targets"]
    total = len(sources)
    extracted = sum(1 for v in sources.values() if v["status"] == "extracted")
    failed_sources = [k for k, v in sources.items() if v["status"] == "failed"]
    reduced = sum(1 for v in targets.values() if v["status"] == "reduced")
    failed_targets = [k for k, v in targets.items() if v["status"] == "failed"]
    new_files = sum(1 for v in targets.values() if v.get("is_new"))

    lines = [
        f"Sources: {total} total, {extracted} extracted, {len(failed_sources)} failed",
        f"Files: {reduced} reduced ({new_files} new), {len(failed_targets)} failed",
    ]
    if failed_sources:
        lines.append("Failed sources: " + ", ".join(sorted(failed_sources)))
    if failed_targets:
        lines.append("Failed files: " + ", ".join(sorted(failed_targets)))
    if oversized:
        lines.append("Oversized (skipped, run manually): " + ", ".join(sorted(oversized)))
    return "\n".join(lines)


def write_log_entry(log_path: Path, summary_line: str) -> None:
    """Append a single consolidated entry to log.md (creates if absent)."""
    log_path = Path(log_path)
    existing = log_path.read_text(encoding="utf-8") if log_path.exists() else ""
    sep = "" if existing.endswith("\n") or not existing else "\n"
    log_path.write_text(existing + sep + summary_line + "\n", encoding="utf-8")
