"""RRF fusion + index-compat primitive tests (pure). kb-offline M3c-1 (#211)."""
from __future__ import annotations

from sdlc_knowledge_base_scripts.embeddings import Provenance
from sdlc_knowledge_base_scripts.fusion import compatible, fuse_compatible, qualify, rrf_fuse, split_qualified


def test_rrf_item_in_two_lists_outranks_item_in_one():
    fused = rrf_fuse([["A", "B"], ["A", "C"]])
    items = [it for it, _ in fused]
    assert items[0] == "A"
    assert set(items) == {"A", "B", "C"}


def test_rrf_one_based_rank_math():
    fused = rrf_fuse([["X"]])
    assert fused == [("X", 1.0 / 61)]


def test_rrf_k_const_effect():
    [(_, a1), (_, a2)] = rrf_fuse([["A", "B"]], k_const=1)
    [(_, b1), (_, b2)] = rrf_fuse([["A", "B"]], k_const=1000)
    assert (a1 - a2) > (b1 - b2)


def test_rrf_tiebreak_by_first_appearance():
    fused = rrf_fuse([["P"], ["Q"]])
    assert [it for it, _ in fused] == ["P", "Q"]
    assert fused[0][1] == fused[1][1]


def test_rrf_empty():
    assert rrf_fuse([]) == []
    assert rrf_fuse([[], []]) == []


def test_compatible_matrix():
    base = Provenance(model="nomic", dims=768, normalization="l2", corpus_hash="c1")
    assert compatible(base, Provenance(model="nomic", dims=768, normalization="l2", corpus_hash="c2")) is True
    assert compatible(base, Provenance(model="other", dims=768, normalization="l2", corpus_hash="c1")) is False
    assert compatible(base, Provenance(model="nomic", dims=512, normalization="l2", corpus_hash="c1")) is False
    assert compatible(base, Provenance(model="nomic", dims=768, normalization="none", corpus_hash="c1")) is False


def _prov(model="nomic", dims=768, norm="l2"):
    return Provenance(model=model, dims=dims, normalization=norm, corpus_hash="c")


def test_fuse_compatible_rejects_incompatible_and_fuses_survivors():
    ref = _prov()
    entries = [
        ("local", _prov(), ["a.md", "b.md"]),
        ("acme-kb", _prov(), ["a.md", "c.md"]),
        ("legacy", _prov(model="old-embed"), ["z.md"]),
    ]
    fused, rejected = fuse_compatible(ref, entries)
    assert rejected == ["legacy"]
    assert all(handle != "legacy" for (handle, _), _ in fused)
    keys = {item for item, _ in fused}
    assert ("local", "a.md") in keys and ("acme-kb", "a.md") in keys


def test_fuse_compatible_all_rejected_yields_empty_fusion():
    ref = _prov()
    entries = [("x", _prov(dims=1), ["a.md"]), ("y", _prov(model="z"), ["b.md"])]
    fused, rejected = fuse_compatible(ref, entries)
    assert fused == [] and set(rejected) == {"x", "y"}


def test_fuse_compatible_ranks_cross_library():
    ref = _prov()
    entries = [("l1", _prov(), ["a.md", "b.md"]), ("l2", _prov(), ["a.md", "c.md"])]
    fused, rejected = fuse_compatible(ref, entries)
    assert rejected == []
    top2 = {item for item, _ in fused[:2]}
    assert top2 == {("l1", "a.md"), ("l2", "a.md")}


def test_qualify_round_trips_flat_and_nested_page_ids():
    assert qualify("acme-kb", "a.md") == "acme-kb/a.md"
    assert split_qualified("acme-kb/a.md") == ("acme-kb", "a.md")
    # nested page id: handle recovered by splitting on the FIRST '/'
    assert qualify("acme-kb", "sub/x.md") == "acme-kb/sub/x.md"
    assert split_qualified("acme-kb/sub/x.md") == ("acme-kb", "sub/x.md")
