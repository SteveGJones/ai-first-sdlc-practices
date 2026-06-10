"""Typed loaders for the frozen eval suite. kb-offline M1c-2 (#211).
questions.jsonl  -> EvalQuestion  ; verifier_labels.jsonl -> VerifierLabel.
Both are JSONL (one JSON object per line; blank lines skipped)."""
from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

from ..contracts import PageRef, Span


class EvalQuestion(BaseModel):
    id: str
    question: str
    kind: str                                   # fact | routing | abstention
    expected_facts: list[str] = Field(default_factory=list)
    expected_routing_targets: list[str] = Field(default_factory=list)
    no_evidence: bool = False
    expected_layer: str | None = None


class VerifierLabel(BaseModel):
    id: str
    claim_text: str
    cited_pages: list[PageRef] = Field(default_factory=list)
    evidence_spans: list[Span] = Field(default_factory=list)
    gold_status: str                            # supported | partial | unsupported


def _load_jsonl(path, model):
    out = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            out.append(model.model_validate_json(line))
    return out


def load_questions(path) -> list[EvalQuestion]:
    return _load_jsonl(path, EvalQuestion)


def load_verifier_labels(path) -> list[VerifierLabel]:
    return _load_jsonl(path, VerifierLabel)
