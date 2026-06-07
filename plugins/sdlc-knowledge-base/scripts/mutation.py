"""Deterministic mutation validator, operation journal, durable committer, and
recovery for kb-offline (#211, M0). Models propose; this module validates and writes.
The validator is a safety floor — invalid proposals are rejected 100% of the time."""
from __future__ import annotations

from pathlib import Path

from .contracts import MutationAction, MutationProposal

_REQUIRED_FRONTMATTER = ("layer", "confidence")


def validate_proposal(
    proposal: MutationProposal,
    library_path: str | Path,
    allowed_layers: list[str],
    known_citations: set[str],
) -> list[str]:
    """Return a list of error strings; empty means valid."""
    errors: list[str] = []
    library_path = Path(library_path).resolve()

    # 1. Path containment + shape
    if (not proposal.target_file
            or proposal.target_file != Path(proposal.target_file).name
            or proposal.target_file.startswith(".")):
        errors.append(f"path: target_file must be a bare library page name, got {proposal.target_file!r}")
    else:
        resolved = (library_path / proposal.target_file).resolve()
        if library_path not in resolved.parents:
            errors.append(f"path: target escapes the library: {proposal.target_file!r}")

    # 2. Required frontmatter
    for key in _REQUIRED_FRONTMATTER:
        if key not in proposal.frontmatter:
            errors.append(f"frontmatter: required key '{key}' missing")

    # 3. Layer validity
    layer = proposal.frontmatter.get("layer")
    if layer is not None and layer not in allowed_layers:
        errors.append(f"layer: '{layer}' not in allowed set {allowed_layers}")

    # 4. Citation existence
    for c in proposal.citations:
        if c not in known_citations:
            errors.append(f"citation: '{c}' does not resolve to a known source")

    # 5. CAS shape: create must not carry expected_hash; extend must.
    if proposal.action == MutationAction.create and proposal.expected_hash is not None:
        errors.append("expected_hash: must be None for a create proposal")
    if proposal.action == MutationAction.extend and proposal.expected_hash is None:
        errors.append("expected_hash: required for an extend proposal (compare-and-swap)")

    return errors
