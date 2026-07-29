"""Sanity checks for the checklist scorer: the exemplar's own design docs
must score sufficient (proves the checklist isn't miscalibrated against
the very docs it's meant to check), and garbage text must not."""

from pathlib import Path

from harness.checklist import (
    ARCHITECTURE_CHECKLIST,
    CLIENT_DESIGN_CHECKLIST,
    SERVER_DESIGN_CHECKLIST,
    score_checklist,
)

EXEMPLAR_DOCS = Path(__file__).parent.parent.parent / "exemplar" / "docs"


def test_exemplar_architecture_doc_is_sufficient():
    text = (EXEMPLAR_DOCS / "architecture.md").read_text()
    result = score_checklist(text, ARCHITECTURE_CHECKLIST)
    assert result.sufficient(), result.missing


def test_exemplar_server_design_doc_is_sufficient():
    text = (EXEMPLAR_DOCS / "design-server.md").read_text()
    result = score_checklist(text, SERVER_DESIGN_CHECKLIST)
    assert result.sufficient(), result.missing


def test_exemplar_client_design_doc_is_sufficient():
    text = (EXEMPLAR_DOCS / "design-client.md").read_text()
    result = score_checklist(text, CLIENT_DESIGN_CHECKLIST)
    assert result.sufficient(), result.missing


def test_empty_text_is_insufficient():
    result = score_checklist("", SERVER_DESIGN_CHECKLIST)
    assert not result.sufficient()
    assert result.score == 0.0


def test_unrelated_text_is_insufficient():
    text = "This is a document about baking bread. Flour, water, yeast, salt."
    result = score_checklist(text, SERVER_DESIGN_CHECKLIST)
    assert not result.sufficient()


def test_partial_doc_scores_between():
    text = "The server uses a state machine to track whose turn it is. Blinds are posted each hand."
    result = score_checklist(text, SERVER_DESIGN_CHECKLIST)
    assert 0.0 < result.score < 1.0
    assert "turn_state_machine_named" in result.satisfied
    assert "blinds_and_button_addressed" in result.satisfied
    assert "side_pot_or_all_in_handling" in result.missing
