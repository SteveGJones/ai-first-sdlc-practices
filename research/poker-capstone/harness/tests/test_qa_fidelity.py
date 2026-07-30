"""Sanity check for harness/qa_fidelity.py using a small synthetic test
file (standing in for what a model's own generated suite would look
like) BEFORE spending a real subagent call on it — same discipline as
proving the REST/client harnesses against the exemplar before trusting
them on model output."""

from pathlib import Path

import pytest

from harness.qa_fidelity import QAFidelityError, evaluate, run_pytest_against

REPO_ROOT = Path(__file__).resolve().parents[2]
EXEMPLAR_SERVER = REPO_ROOT / "exemplar" / "server"
BROKEN_SERVER = REPO_ROOT / "broken-variants" / "wrong-pot-split" / "server"

# A minimal scripted-hand test, deliberately written the way a model's
# own generated suite is asked to (import via `app.*`, no dependency on
# the exemplar's own test fixtures) — heads-up, pocket aces vs garbage,
# should win at showdown regardless of which codebase it runs against
# UNLESS that codebase's payout logic is broken.
_SYNTHETIC_TEST_SOURCE = """
from app.game_engine import start_new_hand, submit_action
from app.models import Card, Deck, Player, Table


class FixedDeck(Deck):
    def __init__(self, order):
        self._cards = list(order)
        self._rng = None

    def deal(self, n):
        dealt, self._cards = self._cards[:n], self._cards[n:]
        return dealt


def _card(rank, suit):
    return Card(rank, suit)


def test_pocket_aces_wins_heads_up_showdown():
    table = Table(table_id="t", small_blind=1, big_blind=2, deck=Deck())
    table.players[0] = Player(seat=0, name="p0", stack=100)
    table.players[1] = Player(seat=1, name="p1", stack=100)

    order = [
        _card(14, "s"), _card(14, "h"),   # seat0: pocket aces
        _card(2, "c"), _card(7, "d"),     # seat1: garbage
        _card(3, "d"), _card(9, "d"), _card(11, "d"),  # flop
        _card(4, "h"),                     # turn
        _card(5, "h"),                     # river
    ]
    start_new_hand(table, deck=FixedDeck(order))

    for _ in range(50):
        if not table.hand_in_progress:
            break
        actor = table.current_actor
        me = table.players[actor]
        to_call = table.current_bet - me.current_bet
        submit_action(table, actor, "call" if to_call > 0 else "check")

    assert table.players[0].stack > 100, (
        f"seat 0 held pocket aces and should have won the pot; "
        f"final stacks: {[(s, p.stack) for s, p in table.players.items()]}"
    )
"""


@pytest.fixture()
def synthetic_test_file(tmp_path):
    test_file = tmp_path / "test_synthetic.py"
    test_file.write_text(_SYNTHETIC_TEST_SOURCE)
    return test_file


def test_run_pytest_against_exemplar_passes(synthetic_test_file):
    result = run_pytest_against(synthetic_test_file, EXEMPLAR_SERVER, "exemplar")
    assert result.passed == 1, result.stdout_tail
    assert result.failed == 0


def test_run_pytest_against_broken_variant_fails(synthetic_test_file):
    result = run_pytest_against(synthetic_test_file, BROKEN_SERVER, "broken_variant")
    assert result.failed == 1, result.stdout_tail


def test_evaluate_end_to_end(synthetic_test_file):
    report = evaluate(synthetic_test_file, EXEMPLAR_SERVER, BROKEN_SERVER)
    assert report.all_pass_on_exemplar is True
    assert report.catches_planted_bug is True


def test_missing_test_file_raises():
    with pytest.raises(QAFidelityError):
        run_pytest_against(Path("/nonexistent/test.py"), EXEMPLAR_SERVER, "exemplar")
