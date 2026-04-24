"""Unit tests for sdlc_knowledge_base_scripts.attribution."""
from sdlc_knowledge_base_scripts.attribution import (
    check_retrieval_attribution,
    check_synthesis_attribution,
    RetrievalCheckResult,
    SynthesisCheckResult,
)


def test_retrieval_all_findings_tagged() -> None:
    output = """### EUV humidity
**Finding**: RH must be ≤45%.
**Source**: ASML 2024.
**Source library**: corporate-semi
**Library file**: EUV-operations.md

### Local site baseline
**Finding**: Ambient RH 75-85%.
**Source**: site survey 2026.
**Source library**: local
**Library file**: site-environmental-baseline.md
"""
    result = check_retrieval_attribution(output)
    assert isinstance(result, RetrievalCheckResult)
    assert result.passed is True
    assert result.dropped_blocks == []


def test_retrieval_finding_missing_source_library_dropped() -> None:
    output = """### Has attribution
**Finding**: good.
**Source library**: local

### Missing attribution
**Finding**: bad.
"""
    result = check_retrieval_attribution(output)
    assert result.passed is False  # at least one dropped
    assert len(result.dropped_blocks) == 1
    assert "Missing attribution" in result.dropped_blocks[0]
    # Cleaned output retains the good block
    assert "### Has attribution" in result.cleaned_output
    assert "### Missing attribution" not in result.cleaned_output


def test_retrieval_empty_output_is_ok() -> None:
    result = check_retrieval_attribution("")
    assert result.passed is True
    assert result.dropped_blocks == []


def test_synthesis_all_claims_tagged() -> None:
    output = """### EUV cleanroom under regional constraints

**Claim**: Tropical sites need multi-stage dehumidification.

**Supporting evidence**:
1. RH must be ≤45% for EUV — [corporate-semi] EUV-operations.md
2. Brazilian ambient RH 75-85% — [local] site-environmental-baseline.md
3. Dutch fab managed with single-stage — [corporate-semi] nijmegen-fab.md

**Caveats**: This synthesis spans local and corporate-semi libraries.
"""
    result = check_synthesis_attribution(output)
    assert isinstance(result, SynthesisCheckResult)
    assert result.passed is True
    assert result.untagged_claims == []


def test_synthesis_claim_missing_handle_aborts() -> None:
    output = """### Argument

**Claim**: Something.

**Supporting evidence**:
1. Good claim — [local] file-a.md
2. Untagged claim with no bracketed handle
3. Another good one — [corp] file-b.md

**Caveats**: None.
"""
    result = check_synthesis_attribution(output)
    assert result.passed is False
    assert len(result.untagged_claims) == 1
    assert "Untagged claim" in result.untagged_claims[0]


def test_synthesis_empty_evidence_list_is_ok() -> None:
    # No supporting evidence section at all — nothing to check
    output = "### Argument\n\n**Claim**: X.\n\n**Caveats**: None.\n"
    result = check_synthesis_attribution(output)
    assert result.passed is True
