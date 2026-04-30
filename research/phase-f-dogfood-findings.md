# Phase F — Dogfood Findings

## F-001 — `# implements:` annotation parser does not handle markdown files

**Severity:** IMPORTANT
**Surfaced during:** Task 4 (Stage 1 proof-of-flow)
**Reproduction:** The `_IMPLEMENTS_RE` regex in `plugins/sdlc-assured/scripts/assured/code_index.py` matches `^\s*#\s*implements:\s*(?P<ids>.+)$`. In a markdown file, the line `# implements: REQ-x-001` parses as an H1 heading by markdown renderers AND matches the regex — producing a fake annotation that displays as a giant title. The HTML-comment workaround `<!-- implements: REQ-x-001 -->` displays correctly in markdown but does NOT match the regex.
**Impact on regulated-industry users:** high — most user-facing artefacts (SKILLs, agents, design docs) are markdown, not Python. Regulated-industry users will hit this within the first feature.
**Suggested resolution:** v0.2.0 — extend `_IMPLEMENTS_RE` to recognise both forms, or add a second regex `_HTML_IMPLEMENTS_RE = re.compile(r"<!--\s*implements:\s*(?P<ids>.+)\s*-->")`. Alternative: define a project-wide rule that markdown annotations live in YAML frontmatter (`implements: [DES-x-001, ...]`).
**Related code:** plugins/sdlc-assured/scripts/assured/code_index.py:9-13, plugins/sdlc-assured/scripts/assured/traceability_validators.py:_IMPLEMENTS_RE

## F-002 — programs.yaml `paths` cannot scope to a section of a file

**Severity:** MINOR
**Surfaced during:** Task 2 (Stage 1)
**Reproduction:** Module M3 (kb-bridge) implements only the SYNTHESISE-ACROSS-SPEC-TYPES section of synthesis-librarian.md, not the whole file. programs.yaml `paths` is whole-directory only.
**Impact on regulated-industry users:** medium — fine-grained ownership of file sections is common in regulated codebases (e.g., MISRA-C compliant subset of a header file)
**Suggested resolution:** consider line-range or section-anchor support in v0.2.0; or document the limitation
**Related:** plugins/sdlc-assured/scripts/assured/decomposition.py:Module.paths
