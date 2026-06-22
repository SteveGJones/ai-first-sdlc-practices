"""Frozen cited-page normalizer (#211, Slice 2). Opaque, case-sensitive, fail-closed."""
import difflib

import pytest

from sdlc_knowledge_base_scripts.cited_page_normalize import (
    Resolution,
    normalize_cited_page,
    resolve_cited_page,
)


def test_exact_match_bypasses_fuzzy_with_score_one():
    # exact candidate resolves immediately at 1.0 even with another near candidate present
    res = resolve_cited_page("a.md", ["a.md", "a-x.md"])
    assert res == Resolution(page="a.md", score=1.0, runner_up=None)


def test_q035_recovers_above_floor():
    assert normalize_cited_page("sdlc-single-formm.md", ["sdlc-single-team.md"]) == "sdlc-single-team.md"


def test_q052_drops_below_floor_but_retains_score():
    res = resolve_cited_page("pair-summary.md", ["pair-programming.md"])
    assert res.page is None
    expected = difflib.SequenceMatcher(None, "pair-summary.md", "pair-programming.md").ratio()
    assert res.score == pytest.approx(expected)
    assert res.runner_up is None  # single candidate


def test_empty_candidates_score_none():
    assert resolve_cited_page("x.md", []) == Resolution(page=None, score=None, runner_up=None)
    assert normalize_cited_page("x.md", []) is None


def test_ambiguous_two_close_candidates_drop():
    # two candidates within margin of each other -> ambiguous -> None, scores retained
    res = resolve_cited_page("sdlc-single-tt.md", ["sdlc-single-team.md", "sdlc-single-tesm.md"])
    assert res.page is None
    assert res.score is not None and res.runner_up is not None
    assert (res.score - res.runner_up) < 0.10


def test_single_candidate_above_floor_recovers_margin_bypassed():
    # one distinct candidate: margin check skipped, recover iff >= floor, even with floor<margin
    assert normalize_cited_page("sdlc-single-formm.md", ["sdlc-single-team.md"],
                                floor=0.75, margin=0.99) == "sdlc-single-team.md"


def test_single_candidate_below_floor_drops():
    assert normalize_cited_page("pair-summary.md", ["pair-programming.md"]) is None


def test_boundary_score_exactly_at_floor_accepted():
    # choose a candidate whose ratio == floor exactly is brittle; instead assert >= semantics
    # by setting floor to the measured best score and expecting acceptance.
    best = resolve_cited_page("sdlc-single-formm.md", ["sdlc-single-team.md"]).score
    assert normalize_cited_page("sdlc-single-formm.md", ["sdlc-single-team.md"],
                                floor=best) == "sdlc-single-team.md"


def test_boundary_margin_exactly_at_margin_accepted():
    cands = ["sdlc-single-team.md", "pair-programming.md"]
    res = resolve_cited_page("sdlc-single-formm.md", cands)
    lead = res.score - res.runner_up
    assert normalize_cited_page("sdlc-single-formm.md", cands, margin=lead) == "sdlc-single-team.md"


def test_duplicate_candidates_deduped_no_false_ambiguity():
    # duplicates of the single good candidate must not register as a second candidate
    assert normalize_cited_page("sdlc-single-formm.md",
                                ["sdlc-single-team.md", "sdlc-single-team.md"]) == "sdlc-single-team.md"


def test_case_sensitive_not_exact():
    # different case is NOT an exact match; score < 1.0 and also below floor -> no recovery
    res = resolve_cited_page("SDLC-Single-Team.md", ["sdlc-single-team.md"])
    assert res.score is not None and res.score < 1.0
    assert res.page is None  # below floor -> documents fail-closed on wrong-case


def test_deterministic_order_independent_of_input_order():
    a = normalize_cited_page("sdlc-single-formm.md", ["tech-debt.md", "sdlc-single-team.md"])
    b = normalize_cited_page("sdlc-single-formm.md", ["sdlc-single-team.md", "tech-debt.md"])
    assert a == b == "sdlc-single-team.md"


def test_equal_score_tie_broken_alphabetically():
    # When two candidates share the best score, the alphabetically-earlier string wins,
    # because the sort key is (-score, string). floor/margin relaxed to force a resolution.
    res = resolve_cited_page("sdlc-single-tt.md",
                             ["sdlc-single-tesm.md", "sdlc-single-team.md"],
                             floor=0.0, margin=0.0)
    assert res.page == "sdlc-single-team.md"  # 'team' < 'tesm' alphabetically
