"""Query output publication policy (#211, M1c-1, addendum decision 7).
supported -> published; partial -> published WITH a caveat; unsupported -> excluded and
reported in rejected_claims."""
from __future__ import annotations

from .contracts import Answer, EntailmentStatus


def publish(answer: Answer) -> tuple[str, list[dict]]:
    """Return (rendered_text, rejected_claims). supported claims are published as-is;
    partial claims are published with a '(partially supported)' caveat; unsupported claims
    are excluded from the body and listed in rejected_claims."""
    lines: list[str] = []
    rejected: list[dict] = []
    for c in answer.claims:
        if c.entailment_status == EntailmentStatus.supported:
            lines.append(c.text)
        elif c.entailment_status == EntailmentStatus.partial:
            lines.append(f"{c.text} (partially supported)")
        else:
            rejected.append({"text": c.text, "reason": "unsupported",
                             "high_impact": c.high_impact})
    return "\n".join(lines), rejected
