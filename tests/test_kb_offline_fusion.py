"""RRF fusion + index-compat primitive tests (pure). kb-offline M3c-1 (#211)."""
from __future__ import annotations

from sdlc_knowledge_base_scripts.embeddings import Provenance
from sdlc_knowledge_base_scripts.fusion import compatible, rrf_fuse


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
