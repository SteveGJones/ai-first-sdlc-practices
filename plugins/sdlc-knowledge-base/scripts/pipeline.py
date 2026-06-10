"""kb-offline pipeline operations (#211, M0). Each operation calls the backend for the
model step, then OWNS parsing + the validate->repair->fail ladder + (for writers) the
mutation proposal. Backends never validate or write."""
from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from . import prompts
from .contracts import ExtractJSON, MutationProposal, SelectResult


def _extract_schema() -> dict:
    return ExtractJSON.model_json_schema()


def extract(source_path, shelf_index_path, *, backend, max_repairs: int = 1) -> ExtractJSON:
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


def _proposal_schema() -> dict:
    return MutationProposal.model_json_schema()


def reduce_to_proposal(*, target_file, is_new, extracts, existing_content, backend, max_repairs: int = 1) -> MutationProposal:
    """Reduce operation: synthesise routed extracts into a typed MutationProposal
    (NOT a final file). The caller validates + commits it deterministically."""
    action = "create" if is_new else "extend"
    base_prompt = (
        f"{prompts.REDUCE_FRAGMENT}\n\nTarget file: {target_file} ({action})\n"
        f"Existing content:\n{existing_content or '(none — new file)'}\n\n"
        f"Routed extracts (JSON):\n{json.dumps(extracts, indent=2)}"
    )
    schema = _proposal_schema()
    prompt = base_prompt
    last_error = ""
    for _ in range(max_repairs + 1):
        raw = backend.generate(prompt, schema=schema)
        try:
            return MutationProposal.model_validate_json(raw)
        except (ValidationError, ValueError) as exc:
            last_error = str(exc)
            prompt = f"{base_prompt}\n\nPrevious output invalid: {last_error}\n" "Return valid JSON only."
    raise ValueError(f"reduce failed after {max_repairs} repair(s): {last_error}")


def _select_schema() -> dict:
    return SelectResult.model_json_schema()


def select(question, shelf_index_path, *, backend, known_pages, max_repairs: int = 1) -> SelectResult:
    """Pick the 2-4 most relevant library pages for the question by reasoning over the
    shelf-index. Drops any returned id that is not a known page (no fabricated targets)."""
    shelf = Path(shelf_index_path).read_text(encoding="utf-8")
    base = f"{prompts.SELECT_FRAGMENT}\n\nQuestion: {question}\n\nShelf-index:\n{shelf}"
    schema = _select_schema()
    prompt = base
    last_error = ""
    for _ in range(max_repairs + 1):
        raw = backend.generate(prompt, schema=schema)
        try:
            result = SelectResult.model_validate_json(raw)
        except (ValidationError, ValueError) as exc:
            last_error = str(exc)
            prompt = f"{base}\n\nPrevious output invalid: {last_error}\n" "Return valid JSON only."
            continue
        return SelectResult(page_ids=[p for p in result.page_ids if p in set(known_pages)])
    raise ValueError(f"select failed after {max_repairs} repair(s): {last_error}")
