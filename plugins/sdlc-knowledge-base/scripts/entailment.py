"""Entailment verifier (#211, M1c-1). Deterministic grounding cap + per-claim LLM-judge.
final entailment_status = min(grounding cap, judge grade). high_impact is verifier-assigned.
The model never sets these — see pipeline.synthesize which strips them."""

from __future__ import annotations

import json
import re

from .backends.base import Backend
from .contracts import Answer, Claim, EntailmentStatus

_RANK = {EntailmentStatus.unsupported: 0, EntailmentStatus.partial: 1, EntailmentStatus.supported: 2}
_WORD = re.compile(r"\w+")


def _norm(text: str) -> str:
    return " ".join(text.lower().split())


def _tokens(text: str) -> list[str]:
    return _WORD.findall(text.lower())


def _min_status(a: EntailmentStatus, b: EntailmentStatus) -> EntailmentStatus:
    # min over the supported>partial>unsupported rank; used by verify_entailment
    return a if _RANK[a] <= _RANK[b] else b


def ground_claim(claim: Claim, pages: dict[str, str], *, fuzzy_threshold: float = 0.6) -> EntailmentStatus:
    """Deterministic grounding cap for one claim:
    - any cited_page not in the read `pages` -> unsupported (hard reject)
    - a verbatim normalized-substring span on its cited page -> supported cap
    - else a fuzzy span (>= fuzzy_threshold of its tokens present on the page) -> partial cap
      (fuzzy_threshold is a provisional default (0.6) — calibrate empirically in M1c-2)
    - else unsupported
    A span may only ground a claim against a page the claim actually cited.
    """
    for ref in claim.cited_pages:
        if ref.page not in pages:
            return EntailmentStatus.unsupported

    cited = {ref.page for ref in claim.cited_pages}
    best = EntailmentStatus.unsupported
    for span in claim.evidence_spans:
        if span.page not in cited:
            continue  # a span may only ground against a page the claim actually cited
        page_text = pages.get(span.page)
        if page_text is None:
            continue  # cited-page presence already verified above; defensive
        if _norm(span.text) in _norm(page_text):
            return EntailmentStatus.supported
        page_tokens = set(_tokens(page_text))
        span_tokens = _tokens(span.text)
        if span_tokens:
            overlap = sum(1 for t in span_tokens if t in page_tokens) / len(span_tokens)
            if overlap >= fuzzy_threshold:
                best = EntailmentStatus.partial
    return best


_HIGH_IMPACT_RE = re.compile(
    r"\d|%|\bshould\b|\bmust\b|\brecommend|\brequire|\bsafety\b|\bcomplian|\bregulat|"
    r"\bISO\s?\d|\bIEC\b|\bFDA\b|\bDO-178|\b62304\b|\b26262\b",
    re.IGNORECASE,
)


def classify_high_impact(claim_text: str) -> bool:
    """Verifier-owned (never model-supplied): a claim is high-impact if it carries a
    number/statistic/unit, a recommendation/modal directive, or safety/compliance/regulatory
    language. Conservative: when these markers appear, treat as high-impact."""
    return bool(_HIGH_IMPACT_RE.search(claim_text))


def judge_claim(claim: Claim, pages: dict[str, str], *, backend: Backend) -> EntailmentStatus:
    """LLM-judge: does the cited page text SUPPORT the claim? Returns supported/partial/
    unsupported. Any non-conforming output defaults to unsupported (conservative)."""
    cited = "\n".join(f"<page id={r.page}>\n{pages.get(r.page, '')}\n</page>" for r in claim.cited_pages)
    prompt = (
        "Judge whether the cited page text SUPPORTS the claim. Reply ONLY a JSON object "
        '{"status": "supported"|"partial"|"unsupported"}.\n\n'
        f"Claim: {claim.text}\n\nCited pages:\n{cited}"
    )
    raw = backend.generate(
        prompt, schema={"type": "object", "properties": {"status": {"type": "string"}}, "required": ["status"]}
    )
    try:
        status = json.loads(raw).get("status", "")
    except (json.JSONDecodeError, ValueError, TypeError, AttributeError):
        return EntailmentStatus.unsupported
    try:
        return EntailmentStatus(status)
    except ValueError:
        return EntailmentStatus.unsupported


def verify_entailment(answer: Answer, pages: dict[str, str], *, backend: Backend) -> Answer:
    """Assign each claim's entailment_status = min(grounding cap, LLM-judge grade), and set
    high_impact deterministically. Skips the judge call when grounding already caps at
    unsupported. Mutates and returns the same Answer (it belongs to the pipeline)."""
    for claim in answer.claims:
        claim.high_impact = classify_high_impact(claim.text)
        cap = ground_claim(claim, pages)
        if cap == EntailmentStatus.unsupported:
            claim.entailment_status = EntailmentStatus.unsupported
            continue
        grade = judge_claim(claim, pages, backend=backend)
        claim.entailment_status = _min_status(cap, grade)
    return answer
