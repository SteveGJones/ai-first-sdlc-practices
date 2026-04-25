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


PERMISSIVE_HANDLES = {"local", "corp-semi", "corp", "corp-health", "corporate-semi", "TODO", "0", "citation-needed"}


def test_synthesis_all_claims_tagged() -> None:
    output = """### EUV cleanroom under regional constraints

**Claim**: Tropical sites need multi-stage dehumidification.

**Supporting evidence**:
1. RH must be ≤45% for EUV — [corporate-semi] EUV-operations.md
2. Brazilian ambient RH 75-85% — [local] site-environmental-baseline.md
3. Dutch fab managed with single-stage — [corporate-semi] nijmegen-fab.md

**Caveats**: This synthesis spans local and corporate-semi libraries.
"""
    result = check_synthesis_attribution(output, valid_handles={"local", "corporate-semi"})
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
    result = check_synthesis_attribution(output, valid_handles={"local", "corp"})
    assert result.passed is False
    assert len(result.untagged_claims) == 1
    assert "Untagged claim" in result.untagged_claims[0]


def test_synthesis_empty_evidence_list_is_ok() -> None:
    # No supporting evidence section at all — nothing to check
    output = "### Argument\n\n**Claim**: X.\n\n**Caveats**: None.\n"
    result = check_synthesis_attribution(output, valid_handles=set())
    assert result.passed is True


def test_retrieval_separator_does_not_leak_unattributed_content(tmp_path) -> None:
    """§7.1 confidentiality invariant: content after --- and before the next
    ### heading must NOT be swallowed into the preceding block's cleaned output."""
    output = """### Legit finding
**Source library**: corp

---

CONFIDENTIAL_BLEED_CONTENT_THIS_SHOULD_NOT_LEAK
this text has no attribution.

### Next legit
**Source library**: local
"""
    result = check_retrieval_attribution(output)
    # The critical check: bleed content must not appear in cleaned output
    assert "CONFIDENTIAL_BLEED_CONTENT" not in result.cleaned_output, (
        "Unattributed content between --- separators leaked into cleaned output — "
        "confidentiality invariant §7.1 violated"
    )
    # Both legitimate blocks should survive
    assert "### Legit finding" in result.cleaned_output
    assert "### Next legit" in result.cleaned_output


def test_retrieval_h4_subheading_inside_block_is_preserved() -> None:
    """A #### subheading inside a valid finding block must not split the block."""
    output = """### Finding A
**Source library**: corp

#### Subsection of Finding A

Detail text under the subsection.

### Finding B
**Source library**: local
"""
    result = check_retrieval_attribution(output)
    # No blocks should be dropped
    assert result.dropped_blocks == []
    # The subheading and its content must survive intact inside Finding A
    assert "#### Subsection of Finding A" in result.cleaned_output
    assert "Detail text under the subsection." in result.cleaned_output


def test_retrieval_fenced_code_with_hash_headings_is_preserved() -> None:
    """Lines starting with ### inside a fenced code block must not be
    read as block boundaries."""
    output = """### Real block
**Source library**: corp

Here is example output:

```
### This is inside a code fence
Not a real heading.
```

Trailing commentary.

### Another real block
**Source library**: local
"""
    result = check_retrieval_attribution(output)
    assert result.dropped_blocks == []
    assert "### This is inside a code fence" in result.cleaned_output
    assert "Trailing commentary." in result.cleaned_output


def test_retrieval_source_library_typo_variants_accepted() -> None:
    """Case and colon-position variants of Source library should still be accepted."""
    output = """### With colon inside asterisks
**Source library:** variant-accepted

### With capital L
**Source Library**: variant-accepted

### Lowercase
**source library**: variant-accepted
"""
    result = check_retrieval_attribution(output)
    # All three variants should survive
    assert result.dropped_blocks == []


def test_synthesis_valid_handles_rejects_bogus_brackets() -> None:
    """With a valid_handles whitelist, bogus bracketed tokens like [0] or [TODO]
    must not pass the synthesis attribution check."""
    output = """### Argument

**Claim**: Something.

**Supporting evidence**:
1. Claim with bogus tag — [TODO] not a real handle
2. Claim referring to `arr[0]` — no real attribution

**Caveats**: None.
"""
    result = check_synthesis_attribution(output, valid_handles={"local", "corp-semi"})
    assert result.passed is False
    assert len(result.untagged_claims) == 2


def test_synthesis_valid_handles_accepts_whitelisted() -> None:
    """With a valid_handles whitelist, only whitelisted bracketed tokens pass."""
    output = """### Argument

**Claim**: Something.

**Supporting evidence**:
1. Legit — [local] file.md
2. Also legit — [corp-semi] other.md

**Caveats**: None.
"""
    result = check_synthesis_attribution(output, valid_handles={"local", "corp-semi"})
    assert result.passed is True


def test_retrieval_preamble_is_dropped() -> None:
    """Preamble before the first block is not attributed and must be dropped."""
    output = """Here is some preamble commentary about the query.
This text has no attribution and must not survive.

### First finding
**Source library**: local
Body of the finding.
"""
    result = check_retrieval_attribution(output)
    assert "preamble commentary" not in result.cleaned_output
    assert "### First finding" in result.cleaned_output
    assert result.dropped_blocks == []  # no blocks were dropped, just preamble stripped


def test_synthesis_multiline_evidence_item_handles_handle_on_continuation() -> None:
    """An evidence item that wraps to the next line, with the [handle] on the
    continuation, must not be reported as untagged."""
    output = """### Argument

**Claim**: Something.

**Supporting evidence**:
1. This is a claim that wraps
   across multiple lines with attribution at the end — [local] file.md

**Caveats**: None.
"""
    result = check_synthesis_attribution(output, valid_handles={"local"})
    assert result.passed is True
