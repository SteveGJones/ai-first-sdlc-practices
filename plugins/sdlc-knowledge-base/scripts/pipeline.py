"""kb-offline pipeline operations (#211, M0). Each operation calls the backend for the
model step, then OWNS parsing + the validate->repair->fail ladder + (for writers) the
mutation proposal. Backends never validate or write."""
from __future__ import annotations

from pathlib import Path

from pydantic import ValidationError

from . import prompts
from .contracts import ExtractJSON


def _extract_schema() -> dict:
    return ExtractJSON.model_json_schema()


def extract(
    source_path, shelf_index_path, *, backend, max_repairs: int = 1
) -> ExtractJSON:
    """Map operation: read one source, return a validated ExtractJSON. Grammar-constrained
    when the backend supports it; otherwise parse + bounded repair + fail."""
    source_text = Path(source_path).read_text(encoding="utf-8")
    base_prompt = (
        f"{prompts.EXTRACT_FRAGMENT}\n\nSource: {source_path}\n"
        f"Shelf-index: {shelf_index_path}\n\n<source>\n{source_text}\n</source>"
    )
    schema = _extract_schema()
    prompt = base_prompt
    last_error = ""
    for _ in range(max_repairs + 1):
        raw = backend.generate(prompt, schema=schema)
        try:
            return ExtractJSON.model_validate_json(raw)
        except (ValidationError, ValueError) as exc:
            last_error = str(exc)
            prompt = (
                f"{base_prompt}\n\nYour previous output was invalid: {last_error}\n"
                "Return ONLY a valid JSON object conforming to the schema."
            )
    raise ValueError(f"extract failed after {max_repairs} repair(s): {last_error}")
