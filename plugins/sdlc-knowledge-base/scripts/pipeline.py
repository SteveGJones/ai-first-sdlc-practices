"""kb-offline pipeline operations (#211, M0). Each operation calls the backend for the
model step, then OWNS parsing + the validate->repair->fail ladder + (for writers) the
mutation proposal. Backends never validate or write."""
from __future__ import annotations

import json
import re
from pathlib import Path

from pydantic import ValidationError

from . import prompts
from .contracts import Answer, EntailmentStatus, ExtractJSON, MutationProposal, PageRef, SelectResult

# Chat-template sentinel tokens (e.g. <|tool_response>, <|tool_response|>, <|im_end|>) that
# some local models — gemma4:12b in particular — emit around grammar-constrained JSON, breaking
# the parse with "Extra data"/"trailing characters". Stripped before parsing (#211, M3 finding).
# Anchored at start/end only so legitimate JSON-string content is never touched.
_SENTINEL_TOKEN = r"\s*<\|[^>]*>\s*"
_LEADING_SENTINELS = re.compile(rf"^(?:{_SENTINEL_TOKEN})+")
_TRAILING_SENTINELS = re.compile(rf"(?:{_SENTINEL_TOKEN})+$")


def _sanitize_json(raw: str) -> str:
    """Strip leading/trailing chat-template sentinel tokens and surrounding whitespace so
    model-output contamination does not spuriously fail an otherwise-valid JSON parse."""
    return _TRAILING_SENTINELS.sub("", _LEADING_SENTINELS.sub("", raw)).strip()


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
        raw = _sanitize_json(backend.generate(prompt, schema=schema))
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
        raw = _sanitize_json(backend.generate(prompt, schema=schema))
        try:
            return MutationProposal.model_validate_json(raw)
        except (ValidationError, ValueError) as exc:
            last_error = str(exc)
            prompt = f"{base_prompt}\n\nPrevious output invalid: {last_error}\n" "Return valid JSON only."
    raise ValueError(f"reduce failed after {max_repairs} repair(s): {last_error}")


def _select_schema() -> dict:
    return SelectResult.model_json_schema()


def select(  # noqa: PLR0913
    question, shelf_index_path, *, backend, known_pages,
    max_repairs: int = 1, priming=None, shelf_text=None,
) -> SelectResult:
    """Pick the 2-4 most relevant library pages for the question by reasoning over the
    shelf-index. Drops any returned id that is not a known page (no fabricated targets).
    When `priming` (a PrimingBundle) is given, a PRIMING block biases selection toward the
    local project's vocabulary — used for NON-local libraries in federated query.
    When `shelf_text` is given, reason over it instead of reading shelf_index_path (the
    accelerated reduced-shelf path); None reads the file (default, byte-identical)."""
    shelf = shelf_text if shelf_text is not None else Path(shelf_index_path).read_text(encoding="utf-8")
    prime_block = ""
    if priming is not None:
        terms = ", ".join(priming.local_shelf_index_terms)
        prime_block = (
            "PRIMING (interpret findings under the local project's lens; prefer pages whose "
            f"terms overlap this vocabulary):\n{priming.local_kb_config_excerpt}\n"
            f"Local terms: {terms}\n\n"
        )
    base = f"{prime_block}{prompts.SELECT_FRAGMENT}\n\nQuestion: {question}\n\nShelf-index:\n{shelf}"
    schema = _select_schema()
    prompt = base
    last_error = ""
    for _ in range(max_repairs + 1):
        raw = _sanitize_json(backend.generate(prompt, schema=schema))
        try:
            result = SelectResult.model_validate_json(raw)
        except (ValidationError, ValueError) as exc:
            last_error = str(exc)
            prompt = f"{base}\n\nPrevious output invalid: {last_error}\n" "Return valid JSON only."
            continue
        return SelectResult(page_ids=[p for p in result.page_ids if p in set(known_pages)])
    raise ValueError(f"select failed after {max_repairs} repair(s): {last_error}")


def _answer_schema() -> dict:
    return Answer.model_json_schema()


def synthesize(question, pages, *, backend, max_repairs: int = 1) -> Answer:
    """Answer using only the supplied pages. Returns claims with cited_pages + verbatim
    evidence_spans. The model NEVER sets entailment_status/high_impact — both are stripped
    here so only the verifier assigns them."""
    pages_block = "\n\n".join(f"<page id={p['page']}>\n{p['content']}\n</page>" for p in pages)
    base = f"{prompts.SYNTHESIZE_FRAGMENT}\n\nQuestion: {question}\n\nPages:\n{pages_block}"
    schema = _answer_schema()
    prompt = base
    last_error = ""
    for _ in range(max_repairs + 1):
        raw = _sanitize_json(backend.generate(prompt, schema=schema))
        try:
            ans = Answer.model_validate_json(raw)
        except (ValidationError, ValueError) as exc:
            last_error = str(exc)
            prompt = f"{base}\n\nPrevious output invalid: {last_error}\nReturn valid JSON only."
            continue
        for c in ans.claims:
            c.entailment_status = None
            c.high_impact = False
            # Contract normalization (#211): some models (e.g. gemma4:12b) attribute the page
            # via evidence_spans and leave cited_pages empty. ground_claim requires a span's
            # page to be in cited_pages, so an empty list orphans every span -> unsupported ->
            # empty answer. Back-fill cited_pages from the spans' declared pages when (and only
            # when) the model left it empty, so deterministic grounding can attribute the
            # evidence. Preserves the anti-mis-attribution rule when cited_pages IS populated.
            if not c.cited_pages and c.evidence_spans:
                seen: list[PageRef] = []
                keys = set()
                for s in c.evidence_spans:
                    key = (s.library or "local", s.page)
                    if key not in keys:
                        keys.add(key)
                        seen.append(PageRef(library=s.library or "local", page=s.page))
                c.cited_pages = seen
        return ans
    raise ValueError(f"synthesize failed after {max_repairs} repair(s): {last_error}")


def _promote_body_schema() -> dict:
    return {"type": "object", "properties": {"body": {"type": "string"}}, "required": ["body"]}


def promote(saved, *, target_file, action, existing_content, backend, max_repairs: int = 1) -> str:
    """Draft page BODY prose from the saved answer's `supported` claims ONLY. Returns the body
    string (the graph assembles the typed MutationProposal + deterministic frontmatter). Raises
    ValueError if there are zero supported claims, or if the model output stays invalid after
    repairs."""
    supported = [c for c in saved.answer.claims if c.entailment_status == EntailmentStatus.supported]
    if not supported:
        raise ValueError("promote: no supported claims to promote")
    claims_block = "\n".join(
        f"- {c.text}  [sources: {', '.join(r.page for r in c.cited_pages)}]" for c in supported
    )
    base = (f"{prompts.PROMOTE_FRAGMENT}\n\nQuestion: {saved.question}\n\n"
            f"Verified claims:\n{claims_block}")
    if action == "extend":
        base += f"\n\nExisting page content to extend (preserve it, append coherently):\n{existing_content or ''}"
    schema = _promote_body_schema()
    prompt = base
    last_error = ""
    for _ in range(max_repairs + 1):
        raw = _sanitize_json(backend.generate(prompt, schema=schema))
        try:
            data = json.loads(raw)
            body = data["body"]
            if not isinstance(body, str) or not body.strip():
                raise ValueError("empty body")
            return body
        except (json.JSONDecodeError, ValueError, TypeError, KeyError) as exc:
            last_error = str(exc)
            prompt = f"{base}\n\nPrevious output invalid: {last_error}\nReturn valid JSON only."
    raise ValueError(f"promote failed after {max_repairs} repair(s): {last_error}")
