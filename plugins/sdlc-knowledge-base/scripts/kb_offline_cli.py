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
from .contracts import MutationAction
from .mutation import CommitConflict, FenceError, commit_mutation, recover, validate_proposal
from .pipeline import extract, reduce_to_proposal
from .resume import LibraryLock, RunRegistry, config_hash, step_id


def _make_backend(name: str, override):
    if override is not None:
        return override
    if name == "anthropic":
        from .backends.anthropic_backend import AnthropicBackend

        return AnthropicBackend()
    raise SystemExit(f"backend '{name}' is not available in M0 (use anthropic or fake)")


def _cmd_init(args: argparse.Namespace) -> int:
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


def _cmd_ingest(args: argparse.Namespace, backend_override, allowed_layers: list[str]) -> int:
    lib = Path(args.library)
    shelf = lib / "_shelf-index.md"
    backend = _make_backend(args.backend, backend_override)
    reg = RunRegistry(lib)
    fingerprint = {"operation": "ingest", "config": config_hash({"backend": args.backend})}

    if args.resume == "latest":
        run_id = reg.select_resumable(fingerprint) or reg.start_run(args.timestamp, fingerprint)
    elif args.resume:
        if not reg.exists(args.resume):
            raise SystemExit(f"--resume: unknown run id {args.resume!r}")
        run_id = args.resume
    else:
        run_id = reg.start_run(args.timestamp, fingerprint)

    extracts_dir = lib / ".kb-offline" / "extracts"
    lock = LibraryLock(lib)
    # M0 ingest is single-source and sub-second « the 120s lock TTL, so no heartbeat is
    # needed here; the fencing token makes any reclaim safe regardless. M1's long-running
    # ingest-bulk loop wires lock.heartbeat() per round.
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
        rejected = 0
        conflicts = 0
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
                rejected += 1
                continue
            try:
                commit_mutation(
                    proposal,
                    library_path=lib,
                    fencing_token=token,
                    lock=lock,
                    run_step=step_id(run_id, "reduce", tfile),
                )
                committed += 1
            except CommitConflict as exc:
                # An idempotent re-create of a page already on disk (e.g. resuming a run
                # that committed it on a prior attempt) is benign completion, not a
                # partial failure — skip it without counting it against the run.
                if proposal.action == MutationAction.create and (lib / tfile).exists():
                    print(f"SKIPPED {tfile}: already committed", file=sys.stderr)
                    continue
                print(f"CONFLICT {tfile}: {exc}", file=sys.stderr)
                conflicts += 1
            except FenceError as exc:
                print(f"CONFLICT {tfile}: {exc}", file=sys.stderr)
                conflicts += 1

        report = recover(lib)
        had_errors = rejected > 0 or conflicts > 0
        reg.set_state(run_id, "completed_with_errors" if had_errors else "completed")
        print(
            f"ingest: run={run_id} committed={committed} rejected={rejected} "
            f"conflicts={conflicts} reindexed={report['reindexed']}"
        )
        if committed == 0 and had_errors:
            return 1
        return 0
    except Exception:
        reg.set_state(run_id, "failed")
        raise
    finally:
        lock.release()


def main(argv: list[str] | None = None, *, backend_override=None, allowed_layers: list[str] | None = None) -> int:
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
