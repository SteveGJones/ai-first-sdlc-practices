"""Entailment verifier (#211, M1c-1). Deterministic grounding cap + per-claim LLM-judge.
final entailment_status = min(grounding cap, judge grade). high_impact is verifier-assigned.
The model never sets these — see pipeline.synthesize which strips them."""

from __future__ import annotations

import re

from .contracts import Claim, EntailmentStatus

_RANK = {EntailmentStatus.unsupported: 0, EntailmentStatus.partial: 1, EntailmentStatus.supported: 2}
_WORD = re.compile(r"\w+")


def _norm(text: str) -> str:
    return " ".join(text.lower().split())


def _tokens(text: str) -> list[str]:
    return _WORD.findall(text.lower())


def _min_status(a: EntailmentStatus, b: EntailmentStatus) -> EntailmentStatus:
    return a if _RANK[a] <= _RANK[b] else b


def ground_claim(claim: Claim, pages: dict, *, fuzzy_threshold: float = 0.6) -> EntailmentStatus:
    """Deterministic grounding cap for one claim:
    - any cited_page not in the read `pages` -> unsupported (hard reject)
    - a verbatim normalized-substring span on its cited page -> supported cap
    - else a fuzzy span (>= fuzzy_threshold of its tokens present on the page) -> partial cap
    - else unsupported
    """
    for ref in claim.cited_pages:
        if ref.page not in pages:
            return EntailmentStatus.unsupported

    best = EntailmentStatus.unsupported
    for span in claim.evidence_spans:
        page_text = pages.get(span.page)
        if page_text is None:
            return EntailmentStatus.unsupported
        if _norm(span.text) in _norm(page_text):
            return EntailmentStatus.supported
        page_tokens = set(_tokens(page_text))
        span_tokens = _tokens(span.text)
        if span_tokens:
            overlap = sum(1 for t in span_tokens if t in page_tokens) / len(span_tokens)
            if overlap >= fuzzy_threshold:
                best = EntailmentStatus.partial
    return best
