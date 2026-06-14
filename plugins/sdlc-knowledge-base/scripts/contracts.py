"""Typed I/O contracts for the kb-offline pipeline (issue #211, M0).

Pydantic v2 models shared by the pipeline, backends, mutation validator, and eval
harness. `entailment_status` is assigned by the deterministic verifier — never trusted
from synthesis-model output.
"""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class Confidence(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"


class ExtractTarget(BaseModel):
    file: str | None = None
    new_topic_slug: str | None = None
    title: str | None = None
    finding_idx: list[int] = Field(default_factory=list)


class ExtractJSON(BaseModel):
    source: str
    findings: list[str] = Field(default_factory=list)
    statistics: list[str] = Field(default_factory=list)
    citations: list[str] = Field(default_factory=list)
    confidence: Confidence = Confidence.medium
    targets: list[ExtractTarget] = Field(default_factory=list)


class PageRef(BaseModel):
    library: str
    page: str


class Span(BaseModel):
    library: str | None = None
    page: str
    text: str


class EntailmentStatus(str, Enum):
    supported = "supported"
    partial = "partial"
    unsupported = "unsupported"


class Claim(BaseModel):
    text: str
    cited_pages: list[PageRef] = Field(default_factory=list)
    evidence_spans: list[Span] = Field(default_factory=list)
    # Verifier-assigned only; any model-supplied value is discarded by the pipeline.
    entailment_status: EntailmentStatus | None = None
    high_impact: bool = False


class Answer(BaseModel):
    claims: list[Claim] = Field(default_factory=list)
    rendered_text: str = ""


class SelectResult(BaseModel):
    page_ids: list[str] = Field(default_factory=list)


class MutationAction(str, Enum):
    create = "create"
    extend = "extend"


class MutationProposal(BaseModel):
    target_file: str
    action: MutationAction
    frontmatter: dict = Field(default_factory=dict)
    body: str = ""
    citations: list[str] = Field(default_factory=list)
    cross_refs: list[str] = Field(default_factory=list)
    # extend: hash of the target page as read during validation (CAS). create: must be None.
    expected_hash: str | None = None
