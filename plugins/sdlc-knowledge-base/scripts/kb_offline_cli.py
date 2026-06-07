"""Minimal `kb-offline` CLI (issue #211, M0). Proves the foundation end-to-end on the
Anthropic/Fake path: ingest = discover -> extract -> route -> reduce -> validate ->
commit (fencing+CAS) -> recover/reindex, under a per-library lock with run lifecycle.
Ollama/graphs/bulk/query-synthesis arrive in M1+."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import kb_ingest_bulk as kbb
from .mutation import CommitConflict, FenceError, commit_mutation, recover, validate_proposal
from .pipeline import extract, reduce_to_proposal
from .resume import LibraryLock, RunRegistry, config_hash


def _make_backend(name, override):
    if override is not None:
        return override
    if name == "anthropic":
        from .backends.anthropic_backend import AnthropicBackend

        return AnthropicBackend()
    raise SystemExit(f"backend '{name}' is not available in M0 (use anthropic or fake)")


def _cmd_init(args) -> int:
    lib = Path(args.library)
    (lib / ".kb-offline").mkdir(parents=True, exist_ok=True)
    (lib / "raw").mkdir(parents=True, exist_ok=True)
    shelf = lib / "_shelf-index.md"
    if not shelf.exists():
        shelf.write_text("<!-- format_version: 1 -->\n# Shelf Index\n", encoding="utf-8")
    log = lib / "log.md"
    if not log.exists():
        log.write_text("# Knowledge Base Log\n", encoding="utf-8")
    print(f"initialised library at {lib}")
    return 0


def _cmd_ingest(args, backend_override, allowed_layers) -> int:
    lib = Path(args.library)
    shelf = lib / "_shelf-index.md"
    backend = _make_backend(args.backend, backend_override)
    reg = RunRegistry(lib)
    fingerprint = {"operation": "ingest", "config": config_hash({"backend": args.backend})}

    if args.resume == "latest":
        run_id = reg.select_resumable(fingerprint) or reg.start_run(args.timestamp, fingerprint)
    elif args.resume:
        run_id = args.resume
    else:
        run_id = reg.start_run(args.timestamp, fingerprint)

    extracts_dir = lib / ".kb-offline" / "extracts"
    lock = LibraryLock(lib)
    token = lock.acquire()
    try:
        sources = kbb.discover_sources([args.source])
        for src in sources:
            slug = kbb.slug_for_source(src)
            ep = kbb.extract_path(extracts_dir, slug)
            if ep.exists():
                continue
            result = extract(str(src), shelf, backend=backend)
            kbb.persist_extract(extracts_dir, slug, json.loads(result.model_dump_json()))

        loaded = [json.loads(p.read_text()) for p in sorted(extracts_dir.glob("*.json"))]
        existing = {p.name for p in lib.glob("*.md") if p.name not in {"_shelf-index.md", "log.md", "_index.md"}}
        route = kbb.route_extracts(loaded, existing_files=existing, size_threshold=200_000)

        known_citations = set()
        for ex in loaded:
            known_citations.update(ex.get("citations", []))

        committed = 0
        for tfile, slot in route.targets.items():
            existing_content = (lib / tfile).read_text() if (lib / tfile).exists() else None
            proposal = reduce_to_proposal(
                target_file=tfile,
                is_new=slot["is_new"],
                extracts=slot["extracts"],
                existing_content=existing_content,
                backend=backend,
            )
            errors = validate_proposal(
                proposal,
                library_path=lib,
                allowed_layers=allowed_layers,
                known_citations=known_citations,
            )
            if errors:
                print(f"REJECTED {tfile}: {errors}", file=sys.stderr)
                continue
            try:
                commit_mutation(
                    proposal,
                    library_path=lib,
                    fencing_token=token,
                    lock=lock,
                    run_step=f"{run_id}-{tfile}",
                )
                committed += 1
            except (CommitConflict, FenceError) as exc:
                print(f"CONFLICT {tfile}: {exc}", file=sys.stderr)

        report = recover(lib)
        reg.set_state(run_id, "completed")
        print(f"ingest complete: run={run_id} committed={committed} reindexed={report['reindexed']}")
        return 0
    except Exception:
        reg.set_state(run_id, "failed")
        raise
    finally:
        lock.release()


def main(argv=None, *, backend_override=None, allowed_layers=None) -> int:
    allowed_layers = allowed_layers or ["methodology", "evidence", "domain", "development"]
    parser = argparse.ArgumentParser(prog="kb-offline")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init")
    p_init.add_argument("--library", default="library")

    p_ing = sub.add_parser("ingest")
    p_ing.add_argument("source")
    p_ing.add_argument("--library", default="library")
    p_ing.add_argument("--backend", default="anthropic")
    p_ing.add_argument("--resume", default=None)
    p_ing.add_argument("--timestamp", required=True)

    args = parser.parse_args(argv)
    if args.cmd == "init":
        return _cmd_init(args)
    if args.cmd == "ingest":
        return _cmd_ingest(args, backend_override, allowed_layers)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
