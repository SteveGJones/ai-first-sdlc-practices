"""Minimal `kb-offline` CLI (issue #211, M0). Proves the foundation end-to-end on the
Anthropic/Fake path: ingest = discover -> extract -> route -> reduce -> validate ->
commit (fencing+CAS) -> recover/reindex, under a per-library lock with run lifecycle.
Ollama/graphs/bulk/query-synthesis arrive in M1+."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .resume import RunRegistry, config_hash


def _slugify(text: str) -> str:
    import re
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s or "promoted-answer"


def _positive_int(s: str) -> int:
    v = int(s)
    if v < 1:
        raise argparse.ArgumentTypeError("--accelerate-k must be >= 1")
    return v


def _make_backend(name: str, override, *, options=None, model=None):
    if override is not None:
        return override
    if name == "anthropic":
        from .backends.anthropic_backend import AnthropicBackend

        return AnthropicBackend()
    if name == "ollama":
        from .backends.ollama_backend import OllamaBackend

        kwargs = {"options": options}
        if model:
            kwargs["model"] = model
        return OllamaBackend(**kwargs)
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


def _resolve_libraries(local_lib: Path, handles: list[str]):
    import os
    from .registry import ProjectActivation, load_global_registry, resolve_dispatch_list
    registry = load_global_registry(Path(os.path.expanduser("~/.sdlc/global-libraries.json")))
    activation = ProjectActivation(activated_sources=handles)
    dispatch = resolve_dispatch_list(registry, activation, local_lib)
    return [[s.name, s.path] for s in dispatch.sources], dispatch.warnings


def _query_single(args: argparse.Namespace, backend) -> int:
    from .graphs.query_graph import build_query_graph

    graph = build_query_graph(backend)
    out = graph.invoke(
        {
            "library_path": args.library,
            "question": args.question,
            "layer": args.layer,
            "min_confidence": args.min_confidence,
            "accelerate": getattr(args, "accelerate", False),
            "accelerate_k": getattr(args, "accelerate_k", 20),
        },
        config={"configurable": {"thread_id": "query"}},
    )
    print(out.get("rendered_text", ""))
    rejected = out.get("rejected_claims", [])
    if rejected:
        print(f"\n[{len(rejected)} claim(s) excluded as unsupported]", file=sys.stderr)
    if args.save:
        from .answers import save_answer
        from .contracts import Answer

        verified = Answer.model_validate(out["_answer"])
        ref = save_answer(args.library, args.question, verified,
                          libraries=["local"], page_ids=list(out.get("page_ids", [])))
        print(f"saved: {ref}")
    return 0


def _emit_federation_result(args, out, specs) -> int:
    print(out.get("rendered_text", ""))
    rejected = out.get("rejected_claims", [])
    if rejected:
        print(f"\n[{len(rejected)} claim(s) excluded as unsupported]", file=sys.stderr)
    claims_n = len(out.get("_answer", {}).get("claims", []))
    print(f"\nqueried {out.get('queried', 0)} libraries ({claims_n} claims, "
          f"{out.get('deduped', 0)} deduped)")
    if args.save:
        from .answers import save_answer
        from .contracts import Answer

        verified = Answer.model_validate(out["_answer"])
        ref = save_answer(args.library, args.question, verified,
                          libraries=[h for h, _ in specs], page_ids=[])
        print(f"saved: {ref}")
    return 0


def _cmd_query(args: argparse.Namespace, backend_override, library_specs_override=None) -> int:
    backend = _make_backend(args.backend, backend_override)
    if not getattr(args, "libraries", None) and library_specs_override is None:
        return _query_single(args, backend)

    local_lib = Path(args.library)
    if library_specs_override is not None:
        specs, warnings = library_specs_override, []
    else:
        handles = [h.strip() for h in args.libraries.split(",") if h.strip()]
        specs, warnings = _resolve_libraries(local_lib, handles)
    for w in warnings:
        print(f"warning: {w}", file=sys.stderr)
    if not specs:
        print("no libraries resolved — run kb-init / check ~/.sdlc/global-libraries.json", file=sys.stderr)
        return 1

    specs = [tuple(s) for s in specs]
    if getattr(args, "accelerate", False):
        from .federation_accel import accelerated_federation_query
        result = accelerated_federation_query(
            local_lib, specs, args.question, backend=backend,
            search_k=getattr(args, "accelerate_k", 20),
            layer=args.layer, min_confidence=args.min_confidence)
        if result is not None:
            return _emit_federation_result(args, result, specs)
        print("accelerate: falling back to full federation", file=sys.stderr)

    from .graphs.federation_query_graph import build_federation_query_graph

    graph = build_federation_query_graph(backend)
    # Priming reads <project>/CLAUDE.md and <project>/library/_shelf-index.md, so
    # local_project_dir must be the PROJECT ROOT, not the library dir. The library is
    # conventionally <project>/library, so the project root is its parent.
    project_dir = local_lib.parent
    out = graph.invoke(
        {"library_specs": [list(s) for s in specs], "local_project_dir": str(project_dir),
         "question": args.question, "layer": args.layer, "min_confidence": args.min_confidence},
        config={"configurable": {"thread_id": "federated-query"}, "max_concurrency": 8})
    return _emit_federation_result(args, out, specs)


def _cmd_eval(args: argparse.Namespace, backend_override) -> int:
    from .eval import report as report_mod
    from .eval.runner import score_run
    from .eval.suite import load_questions, load_verifier_labels

    suite_root = Path(args.suite)
    base = suite_root / "smoke" if args.eval_cmd == "smoke" else suite_root
    library = base / "library"
    questions = load_questions(base / "questions.jsonl")
    labels = load_verifier_labels(base / "verifier_labels.jsonl")

    if args.eval_cmd == "smoke":
        backend = _make_backend(args.backend, backend_override)
        metrics = score_run(str(library), questions, labels, backend=backend)
        print(f"eval smoke — suite={base} ({len(questions)} questions, {len(labels)} verifier labels)")
        for k in sorted(metrics):
            print(f"  {k}: {metrics[k]:.4f}")
        return 0

    # num_ctx pinned to a right-sized window: eval prompts (shelf-index select, 2-4 page
    # synthesize, single-page judge) fit well under 8k tokens. The model's default 131072
    # context reserves a huge KV-cache that drives the host into swap; pinning it keeps the
    # run memory-bounded and reproducible.
    pin = {"temperature": 0, "seed": 7, "top_p": 1, "num_ctx": 8192}
    backend = _make_backend(args.backend, backend_override, options=pin, model=args.model)
    runs = [score_run(str(library), questions, labels, backend=backend) for _ in range(args.runs)]
    agg = report_mod.aggregate(runs)
    verdict = report_mod.gate(agg)
    drift = None
    if args.compare == "anthropic":
        a_backend = _make_backend("anthropic", None)
        a_runs = [score_run(str(library), questions, labels, backend=a_backend)]
        drift = report_mod.aggregate(a_runs)
    text = report_mod.render_report(agg, verdict, model=args.model, drift=drift, pin=pin)
    report_dir = Path(args.report_dir)
    report_dir.mkdir(parents=True, exist_ok=True)
    stem = report_dir / f"release-{args.model.replace(':', '_')}-{args.stamp}"
    stem.with_suffix(".md").write_text(text, encoding="utf-8")
    import json as _json
    stem.with_suffix(".json").write_text(
        _json.dumps({"model": args.model, "stamp": args.stamp, "pin": pin,
                     "verdict": verdict, "metrics": agg}, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(text)
    print(f"\n[report written to {stem.with_suffix('.md')} (+ .json)]")
    return 0 if verdict["passed"] else 1


def _cmd_promote(args: argparse.Namespace, backend_override) -> int:
    from .graphs.promote_graph import build_promote_graph, release_lock
    lib = Path(args.library)
    backend = _make_backend(args.backend, backend_override)
    if args.new and args.into:
        raise SystemExit("promote: pass only one of --new / --into")
    if args.into:
        target_file, action = args.into, "extend"
        if not (lib / target_file).is_file():
            raise SystemExit(f"promote --into: page {target_file!r} does not exist")
    else:
        slug = args.new or _slugify(args.ref)
        target_file = slug if slug.endswith(".md") else f"{slug}.md"
        action = "create"
    reg = RunRegistry(lib)
    fingerprint = {"operation": "promote", "config": config_hash({"ref": args.ref, "target": target_file})}
    run_id = reg.start_run(args.timestamp, fingerprint)
    checkpoint = lib / ".kb-offline" / "promote-graph-checkpoint.sqlite"
    graph = build_promote_graph(backend, checkpoint_path=checkpoint)
    try:
        out = graph.invoke(
            {"library_path": str(lib), "ref": args.ref, "target_file": target_file, "action": action,
             "layer": args.layer, "confidence": args.confidence, "run_id": run_id},
            config={"configurable": {"thread_id": run_id}})
    except Exception:
        release_lock(run_id)
        reg.set_state(run_id, "failed")
        raise
    committed = out.get("committed", 0)
    reg.set_state(run_id, "completed" if committed else "completed_with_errors")
    if out.get("failed"):
        print(f"promote: no supported claims in {args.ref} — nothing promoted")
        return 1
    print(f"promote: run={run_id} target={target_file} committed={committed} "
          f"rejected={out.get('rejected', 0)} promoted {out.get('promoted', 0)} claim(s), "
          f"dropped {out.get('dropped', 0)}")
    return 0 if committed else 1


def _cmd_index(args: argparse.Namespace, backend_override) -> int:
    import numpy as np
    from .embeddings import EmbeddingStore, IndexRow, Provenance, chunk_pages, corpus_hash
    # Capability gate before construction: embedding-capable backends expose
    # embedding_model_id(); AnthropicBackend does not. Gating on the class avoids
    # constructing a backend (e.g. importing the anthropic SDK) only to reject it.
    if backend_override is None:
        from .backends.anthropic_backend import AnthropicBackend
        backend_classes = {"anthropic": AnthropicBackend}
        cls = backend_classes.get(args.backend)
        if cls is not None and getattr(cls, "embedding_model_id", None) is None:
            raise SystemExit(f"backend '{args.backend}' does not support embeddings; use ollama or fake")
    backend = _make_backend(args.backend, backend_override)
    # Instance gate (in addition to the class pre-check above): catches the
    # backend_override path the class map can't see, and any future named
    # embedding-less backend.
    if getattr(backend, "embedding_model_id", None) is None:
        raise SystemExit(f"backend '{args.backend}' does not support embeddings; use ollama or fake")
    lib = Path(args.library)
    model = backend.embedding_model_id()
    pages = chunk_pages(lib)

    existing = EmbeddingStore.load(lib)
    compatible = existing is not None and existing.provenance.model == model
    prior = {}
    if compatible:
        prior = {r.page_id: (r.content_hash, i) for i, r in enumerate(existing.rows)}

    final_rows, vec_slots, to_embed, reembedded, unchanged = [], [], [], 0, 0
    for page_id, text, chash in pages:
        if page_id in prior and prior[page_id][0] == chash:
            final_rows.append(IndexRow(page_id=page_id, content_hash=chash))
            vec_slots.append(("reuse", prior[page_id][1]))
            unchanged += 1
        else:
            final_rows.append(IndexRow(page_id=page_id, content_hash=chash))
            vec_slots.append(("new", len(to_embed)))
            to_embed.append(text)
            reembedded += 1
    current_ids = {r.page_id for r in final_rows}
    removed = len(set(prior) - current_ids)   # prior is {} when not compatible -> 0

    new_vecs = np.array(backend.embed(to_embed), dtype=np.float32) if to_embed else None
    if new_vecs is not None and new_vecs.shape[0]:
        dims = new_vecs.shape[1]
    elif compatible:
        dims = existing.provenance.dims
    else:
        dims = 0
    if dims:
        matrix = np.zeros((len(final_rows), dims), dtype=np.float32)
        for row_i, (kind, idx) in enumerate(vec_slots):
            matrix[row_i] = existing.matrix[idx] if kind == "reuse" else new_vecs[idx]
    else:
        matrix = np.zeros((0, 0), dtype=np.float32)
    prov = Provenance(model=model, dims=dims, normalization="l2",
                      corpus_hash=corpus_hash([(r.page_id, r.content_hash) for r in final_rows]))
    # from_rows re-L2-normalizes the whole matrix, including reused (already unit-norm)
    # rows. This does NOT accumulate: re-normalizing a float32 unit vector is a fixed
    # point (the norm rounds to 1.0), so drift saturates at ~1 ULP (~1.5e-08) regardless
    # of incremental-cycle count — orders of magnitude below cosine ranking sensitivity.
    EmbeddingStore.from_rows(matrix, final_rows, prov).save(lib)
    print(f"indexed {len(final_rows)} pages ({reembedded} re-embedded, {unchanged} unchanged, "
          f"{removed} removed); index at {lib / '.kb-offline'}")
    return 0


def _cmd_fingerprint(args: argparse.Namespace) -> int:
    if args.fp_cmd != "export":
        return 2
    from .embeddings import EmbeddingStore, chunk_pages, corpus_hash
    from .fingerprint import Manifest, export_fingerprint, write_fingerprint

    if args.clusters < 1:
        raise SystemExit("fingerprint export: --clusters must be >= 1")
    lib = Path(args.library)
    store = EmbeddingStore.load(lib)
    if store is None:
        print("fingerprint export: no embedding index — run `kb-offline index` first", file=sys.stderr)
        return 1
    fresh = corpus_hash([(pid, h) for pid, _, h in chunk_pages(lib)])
    if store.provenance.corpus_hash != fresh and not args.allow_stale:
        print("fingerprint export: index is stale (corpus changed since last index) — "
              "re-run `kb-offline index`, or pass --allow-stale", file=sys.stderr)
        return 1
    handle = args.handle or lib.name
    manifest = Manifest(handle=handle, owner=args.owner, contact=args.contact)
    artifact = export_fingerprint(store, tier=args.tier, manifest=manifest,
                                  clusters=args.clusters, weights=not args.no_weights)
    out = Path(args.out) if args.out else Path(f"{handle}.kbfp.json")
    write_fingerprint(out, artifact)
    print(f"wrote {out} (tier={args.tier}, {len(artifact['vectors'])} vectors)")
    return 0


def _cmd_lint(args: argparse.Namespace, sources_override=None) -> int:
    from datetime import datetime, timezone
    from .lint import lint_libraries, render_lint_report
    local_lib = Path(args.library)
    if sources_override is not None:
        sources, warnings = sources_override, []
    else:
        import os
        from .registry import ProjectActivation, load_global_registry, resolve_dispatch_list
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


def main(argv: list[str] | None = None, *, backend_override=None, allowed_layers: list[str] | None = None,
         library_specs_override=None, sources_override=None) -> int:
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
    p_q.add_argument("--libraries", default=None, help="comma-separated external library handles to federate")
    p_q.add_argument("--save", action="store_true", help="persist the verified answer; print its ref")
    p_q.add_argument("--accelerate", action="store_true", help="use the embedding index to pre-filter candidates")
    p_q.add_argument("--accelerate-k", type=_positive_int, default=20)

    p_eval = sub.add_parser("eval")
    eval_sub = p_eval.add_subparsers(dest="eval_cmd", required=True)
    p_smoke = eval_sub.add_parser("smoke")
    p_smoke.add_argument("--suite", default="plugins/sdlc-knowledge-base/eval/suite")
    p_smoke.add_argument("--backend", default="fake")
    p_rel = eval_sub.add_parser("release")
    p_rel.add_argument("--suite", default="plugins/sdlc-knowledge-base/eval/suite")
    p_rel.add_argument("--backend", default="ollama")
    p_rel.add_argument("--model", default="gemma4:12b")
    p_rel.add_argument("--runs", type=int, default=3)
    p_rel.add_argument("--compare", default=None, choices=["anthropic"])
    p_rel.add_argument("--report-dir", default="research/kb-offline-eval")
    p_rel.add_argument("--stamp", required=True)

    p_promote = sub.add_parser("promote")
    p_promote.add_argument("ref")
    p_promote.add_argument("--new", default=None, help="create a new page with this slug")
    p_promote.add_argument("--into", default=None, help="extend an existing page")
    p_promote.add_argument("--library", default="library")
    p_promote.add_argument("--backend", default="anthropic")
    p_promote.add_argument("--layer", default=None)
    p_promote.add_argument("--confidence", default=None, choices=["low", "medium", "high"])
    p_promote.add_argument("--timestamp", required=True)

    p_index = sub.add_parser("index")
    p_index.add_argument("--library", default="library")
    p_index.add_argument("--backend", default="ollama")

    p_lint = sub.add_parser("lint")
    p_lint.add_argument("--library", default="library")
    p_lint.add_argument("--libraries", default=None, help="comma-separated external library handles")

    p_fp = sub.add_parser("fingerprint")
    fp_sub = p_fp.add_subparsers(dest="fp_cmd", required=True)
    p_fpx = fp_sub.add_parser("export")
    p_fpx.add_argument(
        "--library", default="library",
        help="library directory holding the built embedding index (default: library)")
    p_fpx.add_argument(
        "--tier", required=True, choices=["coarse", "page"],
        help="fingerprint granularity: 'coarse' k-means centroids, or 'page' per-page vectors")
    p_fpx.add_argument(
        "--out", default=None,
        help="output path for the .kbfp.json artifact (default: <handle>.kbfp.json)")
    p_fpx.add_argument(
        "--handle", default=None,
        help="short publisher handle for the fingerprint (default: library dir name)")
    p_fpx.add_argument(
        "--owner", default="",
        help="human-readable owner/org name recorded in the manifest")
    p_fpx.add_argument(
        "--contact", default=None,
        help="contact string (e.g. email) recorded in the manifest for 'who to ask'")
    p_fpx.add_argument(
        "--clusters", type=int, default=8,
        help="number of k-means centroids for the coarse tier (default: 8)")
    p_fpx.add_argument(
        "--no-weights", action="store_true",
        help="omit per-centroid page-count weights from the coarse artifact")
    p_fpx.add_argument(
        "--allow-stale", action="store_true",
        help="export even if the index is stale (corpus changed since last index)")

    args = parser.parse_args(argv)
    if args.cmd == "init":
        return _cmd_init(args)
    if args.cmd == "ingest":
        return _cmd_ingest(args, backend_override, allowed_layers)
    if args.cmd == "ingest-bulk":
        return _cmd_ingest_bulk(args, backend_override, allowed_layers)
    if args.cmd == "query":
        return _cmd_query(args, backend_override, library_specs_override)
    if args.cmd == "eval":
        return _cmd_eval(args, backend_override)
    if args.cmd == "promote":
        return _cmd_promote(args, backend_override)
    if args.cmd == "index":
        return _cmd_index(args, backend_override)
    if args.cmd == "lint":
        return _cmd_lint(args, sources_override)
    if args.cmd == "fingerprint":
        return _cmd_fingerprint(args)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
