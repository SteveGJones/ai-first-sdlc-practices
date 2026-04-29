"""Positional namespace ID parsing for the Assured bundle."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional


class IdParseError(ValueError):
    """Raised when a string cannot be parsed as an Assured ID."""


@dataclass(frozen=True)
class ParsedId:
    """Decomposed view of an Assured ID."""

    program: Optional[str]
    sub_program: Optional[str]
    module: Optional[str]
    kind: str
    feature: Optional[str]
    number: int


_FLAT_RE = re.compile(
    r"^(?P<kind>REQ|DES|TEST|CODE)-(?P<feature>[a-z0-9][a-z0-9-]*)-(?P<num>\d+)$"
)
_POSITIONAL_RE = re.compile(
    r"^(?P<prog>P\d+)\.(?P<sub>SP\d+)\.(?P<mod>M\d+)\."
    r"(?P<kind>REQ|DES|TEST|CODE)-(?P<num>\d+)$"
)


def parse_id(text: str) -> ParsedId:
    flat = _FLAT_RE.match(text)
    if flat:
        return ParsedId(
            program=None,
            sub_program=None,
            module=None,
            kind=flat["kind"],
            feature=flat["feature"],
            number=int(flat["num"]),
        )
    positional = _POSITIONAL_RE.match(text)
    if positional:
        return ParsedId(
            program=positional["prog"],
            sub_program=positional["sub"],
            module=positional["mod"],
            kind=positional["kind"],
            feature=None,
            number=int(positional["num"]),
        )
    raise IdParseError(f"not a valid Assured ID: {text!r}")


def format_id(parsed: ParsedId) -> str:
    if is_positional(parsed):
        return f"{parsed.program}.{parsed.sub_program}.{parsed.module}.{parsed.kind}-{parsed.number:03d}"
    return f"{parsed.kind}-{parsed.feature}-{parsed.number:03d}"


def is_positional(parsed: ParsedId) -> bool:
    return parsed.program is not None
