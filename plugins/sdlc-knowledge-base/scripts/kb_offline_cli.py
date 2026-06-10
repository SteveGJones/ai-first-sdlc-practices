"""Minimal `kb-offline` CLI (issue #211, M0). Proves the foundation end-to-end on the
Anthropic/Fake path: ingest = discover -> extract -> route -> reduce -> validate ->
commit (fencing+CAS) -> recover/reindex, under a per-library lock with run lifecycle.
Ollama/graphs/bulk/query-synthesis arrive in M1+."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .resume import RunRegistry, config_hash


def _make_backend(name: str, override):
    if override is not None:
        return override
    if name == "anthropic":
        from .backends.anthropic_backend import AnthropicBackend

        return AnthropicBackend()
    if name == "ollama":
        from .backends.ollama_backend import OllamaBackend

        return OllamaBackend()
    raise SystemExit(f"backend '{name}' is not available (use anthropic, ollama, or fake)")


def _resolve_run_id(reg, args, fingerprint: dict) -> str:
    """Resume-id resolution shared by ingest + ingest-bulk."""
    if args.resume == "latest":
        return reg.select_resumable(fingerprint) or reg.start_run(args.timestamp, fingerprint)
    if args.resume:
        if not reg.exists(args.resume):
            raise SystemExit(f"--resume: unknown run id {args.resume!r}")
        return args.resume
    return reg.start_run(args.timestamp, fingerprint)


def _run_through_graph(reg, run_id: str, graph, state: dict, config: dict, *, label: str, extra: str = "") -> int:
    """Invoke a compiled ingest graph and apply the shared run-lifecycle + return-code
    policy. On any graph error: release the lock (graph's finalize is skipped) and mark
    the run failed, then re-raise. Otherwise set completed[_with_errors] and return the
    exit code (1 only if nothing committed but work was attempted)."""
    from .graphs.ingest_graph import release_lock

    try:
        out = graph.invoke(state, config=config)
    except Exception:
        release_lock(run_id)
        reg.set_state(run_id, "failed")
        raise
    committed = out.get("committed", 0)
    rejected = out.get("rejected", 0)
    conflicts = out.get("conflicts", 0)
    had_errors = rejected > 0 or conflicts > 0
    reg.set_state(run_id, "completed_with_errors" if had_errors else "completed")
    print(
        f"{label}: run={run_id} {extra}committed={committed} "
        f"rejected={rejected} conflicts={conflicts} reindexed={out.get('reindexed')}"
    )
    return 1 if (committed == 0 and had_errors) else 0


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
    backend = _make_backend(args.backend, backend_override)
    reg = RunRegistry(lib)
    fingerprint = {"operation": "ingest", "config": config_hash({"backend": args.backend})}
    run_id = _resolve_run_id(reg, args, fingerprint)

    from .graphs.ingest_graph import build_ingest_graph

    checkpoint = lib / ".kb-offline" / "graph-checkpoint.sqlite"
    graph = build_ingest_graph(backend, allowed_layers=allowed_layers, checkpoint_path=checkpoint)
    return _run_through_graph(
        reg,
        run_id,
        graph,
        {"library_path": str(lib), "source_spec": args.source, "run_id": run_id},
        {"configurable": {"thread_id": run_id}},
        label="ingest",
    )


def _cmd_ingest_bulk(args: argparse.Namespace, backend_override, allowed_layers: list[str]) -> int:
    from . import kb_ingest_bulk as kbb
    from .graphs.bulk_ingest_graph import build_bulk_ingest_graph

    lib = Path(args.library)
    backend = _make_backend(args.backend, backend_override)
    reg = RunRegistry(lib)
    parallel = max(1, min(64, args.parallel))
    # parallel in fingerprint: changing --parallel intentionally starts a fresh run
    fingerprint = {
        "operation": "ingest-bulk",
        "config": config_hash({"backend": args.backend, "parallel": parallel}),
    }
    run_id = _resolve_run_id(reg, args, fingerprint)

    source_specs = [str(p) for p in kbb.discover_sources(args.source)]
    checkpoint = lib / ".kb-offline" / "bulk-graph-checkpoint.sqlite"
    graph = build_bulk_ingest_graph(backend, allowed_layers=allowed_layers, checkpoint_path=checkpoint)
    return _run_through_graph(
        reg,
        run_id,
        graph,
        {"library_path": str(lib), "source_specs": source_specs, "run_id": run_id},
        {"configurable": {"thread_id": run_id}, "max_concurrency": parallel},
        label="ingest-bulk",
        extra=f"sources={len(source_specs)} ",
    )


def _cmd_query(args: argparse.Namespace, backend_override) -> int:
    from .graphs.query_graph import build_query_graph

    backend = _make_backend(args.backend, backend_override)
    graph = build_query_graph(backend)
    out = graph.invoke(
        {
            "library_path": args.library,
            "question": args.question,
            "layer": args.layer,
            "min_confidence": args.min_confidence,
        },
        config={"configurable": {"thread_id": "query"}},
    )
    print(out.get("rendered_text", ""))
    rejected = out.get("rejected_claims", [])
    if rejected:
        print(f"\n[{len(rejected)} claim(s) excluded as unsupported]", file=sys.stderr)
    return 0


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

    p_bulk = sub.add_parser("ingest-bulk")
    p_bulk.add_argument("source")
    p_bulk.add_argument("--library", default="library")
    p_bulk.add_argument("--backend", default="anthropic")
    p_bulk.add_argument("--parallel", type=int, default=16)
    p_bulk.add_argument("--resume", default=None)
    p_bulk.add_argument("--timestamp", required=True)

    p_q = sub.add_parser("query")
    p_q.add_argument("question")
    p_q.add_argument("--library", default="library")
    p_q.add_argument("--backend", default="anthropic")
    p_q.add_argument("--layer", default=None)
    p_q.add_argument("--min-confidence", default=None)

    args = parser.parse_args(argv)
    if args.cmd == "init":
        return _cmd_init(args)
    if args.cmd == "ingest":
        return _cmd_ingest(args, backend_override, allowed_layers)
    if args.cmd == "ingest-bulk":
        return _cmd_ingest_bulk(args, backend_override, allowed_layers)
    if args.cmd == "query":
        return _cmd_query(args, backend_override)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
