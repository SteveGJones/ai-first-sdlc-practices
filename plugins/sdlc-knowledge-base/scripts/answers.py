"""Saved query answers — the promote entry point (#211, M2a). `query --save` persists a
verified Answer here; `promote <ref>` loads it. Read/write only under .kb-offline/answers/."""
from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

from .contracts import Answer
from .durability import atomic_write_text
from .resume import content_hash


class SavedAnswer(BaseModel):
    ref: str
    question: str
    libraries: list[str] = Field(default_factory=list)
    page_ids: list[str] = Field(default_factory=list)
    answer: Answer
    rendered_text: str = ""


def compute_ref(question: str, rendered_text: str) -> str:
    """Deterministic short id (no clock dependency) for a saved answer."""
    return content_hash(f"{question}\x00{rendered_text}")[:16]


def _answers_dir(library_path) -> Path:
    return Path(library_path) / ".kb-offline" / "answers"


def save_answer(library_path, question: str, answer: Answer, *, libraries, page_ids) -> str:
    """Persist a verified Answer + provenance; return its ref."""
    ref = compute_ref(question, answer.rendered_text)
    saved = SavedAnswer(ref=ref, question=question, libraries=list(libraries),
                        page_ids=list(page_ids), answer=answer, rendered_text=answer.rendered_text)
    d = _answers_dir(library_path)
    d.mkdir(parents=True, exist_ok=True)
    atomic_write_text(d / f"{ref}.json", saved.model_dump_json(indent=2))
    return ref


def load_answer(library_path, ref: str) -> SavedAnswer:
    path = _answers_dir(library_path) / f"{ref}.json"
    if not path.is_file():
        raise FileNotFoundError(f"no saved answer with ref {ref!r} under {_answers_dir(library_path)}")
    return SavedAnswer.model_validate_json(path.read_text(encoding="utf-8"))
