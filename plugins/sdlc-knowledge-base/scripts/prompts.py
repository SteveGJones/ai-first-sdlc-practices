"""Canonical operation prompt fragments (issue #211). Single source of truth shared by
the CLI pipeline and mirrored into the agent .md managed blocks; CI's
check-prompt-parity.py asserts they do not drift."""
from __future__ import annotations

EXTRACT_FRAGMENT = (
    "Read the source and the shelf-index (read-only). Emit ONLY a JSON object with "
    "fields: source, findings[], statistics[], citations[], confidence "
    "(high|medium|low), and targets[] mapping findings to existing files or proposed "
    "new topics. Summarise findings; never transcribe."
)

SELECT_FRAGMENT = (
    "Read the shelf-index and identify the 2-4 most relevant library pages for the "
    "question. Return only their page ids."
)

SYNTHESIZE_FRAGMENT = (
    "Answer using only the supplied pages. Return claims, each with the pages it cites "
    "and the exact supporting spans. Do not assign entailment status; the verifier does."
)

REDUCE_FRAGMENT = (
    "Synthesise all routed extracts into exactly one file. Propose a mutation (target, "
    "frontmatter, body, citations, cross-refs); do not write files yourself. Apply "
    "extend-vs-create, contradiction flagging, citation discipline, confidence frontmatter."
)
