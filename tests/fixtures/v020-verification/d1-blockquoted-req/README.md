## Defect: D1 — Blockquoted fake REQ-ID

`requirements-spec.md` contains a real `### REQ-fxd1-001` heading AND a blockquote
line `> REQ-fake-001 example: ...`. `build_id_registry` (spec_parser) should extract
only REQ-fxd1-001 — the blockquoted line does not start with `###` so it is not
picked up by `_HEADING_RE`. The test asserts exactly 1 ID is extracted.
