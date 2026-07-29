"""Sanity checks for the P1 doc-fidelity checklist and judge-prompt
builder. The judge itself can't be unit tested here (it's an Agent
dispatch, not a pure function) — this only covers the deterministic
half."""

from harness.doc_fidelity import build_judge_prompt, score_doc_checklist


def test_empty_text_is_zero_score():
    result = score_doc_checklist("")
    assert result.score == 0.0


def test_thorough_description_scores_high():
    text = """
    The server enforces turn order via current_actor. A betting round is
    complete once every active seat has acted_this_round. A short all-in
    raise does not reopen the round for players who already called.
    Side pots are computed in layers based on total_committed. Best hand
    evaluation checks all combinations of 5 cards; the wheel (A-2-3-4-5)
    straight counts the ace low. Blinds rotate around the button; in
    heads-up the button posts the small blind. The REST API exposes
    endpoints for creating tables and submitting actions. Hole card
    privacy means only your own cards are shown, redacted for everyone
    else until showdown.
    """
    result = score_doc_checklist(text)
    assert result.score == 1.0, result.missing


def test_partial_description_scores_between():
    text = "The server uses current_actor to enforce whose turn it is."
    result = score_doc_checklist(text)
    assert 0.0 < result.score < 1.0
    assert "turn_enforcement_described" in result.satisfied
    assert "side_pot_algorithm_described" in result.missing


def test_build_judge_prompt_includes_facts_and_doc():
    prompt = build_judge_prompt("F1: some fact", "candidate documentation text")
    assert "F1: some fact" in prompt
    assert "candidate documentation text" in prompt
    assert "CORRECT" in prompt and "INCORRECT" in prompt and "OMITTED" in prompt
