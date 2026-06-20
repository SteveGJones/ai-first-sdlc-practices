"""Query output publication policy (#211, M1c-1, addendum decision 7).
supported -> published; partial -> published WITH a caveat; unsupported -> excluded and
reported in rejected_claims."""
from __future__ import annotations

from .contracts import Answer, EntailmentStatus


def published_line(claim, *, suffix: str = "") -> tuple[str | None, dict | None]:
    """Apply the publication policy to ONE claim. Returns (body_line, rejected_entry) with
    exactly one non-None: supported -> (text+suffix, None); partial -> (text+' (partially
    supported)'+suffix, None); unsupported/other -> (None, {text, reason, high_impact})."""
    if claim.entailment_status == EntailmentStatus.supported:
        return (f"{claim.text}{suffix}", None)
    if claim.entailment_status == EntailmentStatus.partial:
        return (f"{claim.text} (partially supported){suffix}", None)
    return (None, {"text": claim.text, "reason": "unsupported", "high_impact": claim.high_impact})


def finalize_answer(answer, rendered: str, *, abstain_reason: str) -> None:
    """Set rendered_text and reconcile abstention BOTH ways. Renderer-agnostic: the caller
    renders (publish OR render_federated) and passes the body."""
    answer.rendered_text = rendered
    if not rendered.strip():
        answer.abstained = True
        answer.abstention_reason = abstain_reason
    else:
        answer.abstained = False
        answer.abstention_reason = None


def publish(answer: Answer) -> tuple[str, list[dict]]:
    """Return (rendered_text, rejected_claims). supported claims are published as-is;
    partial claims are published with a '(partially supported)' caveat; unsupported claims
    are excluded from the body and listed in rejected_claims."""
    lines: list[str] = []
    rejected: list[dict] = []
    for c in answer.claims:
        line, rej = published_line(c)
        if line is not None:
            lines.append(line)
        if rej is not None:
            rejected.append(rej)
    return "\n".join(lines), rejected
