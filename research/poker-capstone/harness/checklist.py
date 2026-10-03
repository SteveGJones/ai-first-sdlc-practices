"""Deterministic checklist scorer for the two open-ended design stages
(architecture, detailed design). Used two ways: (1) as a directional
design-quality score, recorded as-produced and never retroactively
improved; (2) as the sufficiency gate for the explicit, logged backfill
described in the retrospective's "First verification" decision — if a
model's own stage output doesn't clear the threshold, the corresponding
exemplar section is spliced in so the pipeline can still reach stage 3/4,
but the model's own checklist score stands regardless.

Each checklist item is an (name, [patterns]) pair — satisfied if ANY
pattern matches the text (case-insensitive), since a design doc can
express the same required element in many different words. This is
deliberately generous (keyword presence, not exact structure) — the
point is "did they address this concept at all," not "did they use our
exact section headers."
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

ARCHITECTURE_CHECKLIST: list[tuple[str, list[str]]] = [
    (
        "identifies_server_and_client_as_separate",
        [r"\bserver\b.{0,80}\bclient\b", r"\bclient\b.{0,80}\bserver\b"],
    ),
    (
        "server_is_authority_for_game_state",
        [r"server.{0,60}(authorit|source of truth|owns|enforc)"],
    ),
    (
        "names_a_communication_protocol",
        [r"\bREST\b", r"\bWebSocket\b", r"\bHTTP\b", r"\bAPI\b"],
    ),
    (
        "addresses_turn_order_or_enforcement",
        [r"turn(s)? (order|enforc)", r"whose turn", r"current[_ ]?actor"],
    ),
    (
        "states_a_tech_stack",
        [
            r"\b(Python|Node|FastAPI|Flask|Express|Go|Rust|Java)\b",
            r"tech(nology)? stack",
        ],
    ),
]

SERVER_DESIGN_CHECKLIST: list[tuple[str, list[str]]] = [
    (
        "turn_state_machine_named",
        [r"state machine", r"current[_ ]?actor", r"turn enforc"],
    ),
    (
        "betting_rounds_addressed",
        [
            r"\b(preflop|pre-flop)\b",
            r"\bflop\b.{0,40}\bturn\b.{0,40}\briver\b",
            r"betting round",
        ],
    ),
    ("blinds_and_button_addressed", [r"\bblind", r"\bbutton\b"]),
    ("side_pot_or_all_in_handling", [r"side[- ]?pot", r"all[- ]?in"]),
    (
        "hand_ranking_or_evaluation_specified",
        [r"hand (rank|evaluat)", r"straight flush", r"full house"],
    ),
    (
        "api_or_endpoint_contract_specified",
        [r"\bAPI\b", r"endpoint", r"\bREST\b", r"POST /", r"GET /"],
    ),
    ("showdown_addressed", [r"showdown"]),
]

CLIENT_DESIGN_CHECKLIST: list[tuple[str, list[str]]] = [
    (
        "state_sync_mechanism_specified",
        [r"\bWebSocket\b", r"poll(ing)?", r"state sync"],
    ),
    (
        "action_submission_mechanism_specified",
        [r"\bREST\b", r"\bAPI\b", r"fetch\(", r"POST /"],
    ),
    (
        "player_actions_named",
        [r"\bfold\b", r"\bcheck\b", r"\bcall\b", r"\b(bet|raise)\b"],
    ),
    ("hole_cards_visibility_addressed", [r"hole card", r"own cards?", r"private card"]),
    ("pot_display_addressed", [r"\bpot\b"]),
]


@dataclass
class ChecklistResult:
    score: float  # satisfied / total, in [0, 1]
    satisfied: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)

    def sufficient(self, threshold: float = 0.6) -> bool:
        return self.score >= threshold


def score_checklist(
    text: str, checklist: list[tuple[str, list[str]]]
) -> ChecklistResult:
    satisfied, missing = [], []
    for name, patterns in checklist:
        if any(re.search(p, text, re.IGNORECASE) for p in patterns):
            satisfied.append(name)
        else:
            missing.append(name)
    total = len(checklist)
    return ChecklistResult(
        score=(len(satisfied) / total if total else 1.0),
        satisfied=satisfied,
        missing=missing,
    )
