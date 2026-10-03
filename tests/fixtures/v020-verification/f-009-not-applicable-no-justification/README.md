## Defect: F-009 — not_applicable without justification

REQ-fix9-001 has `**Evidence-status:** not_applicable` but no `**Justification:**`
field. `RequirementMetadata` parsing should flag this REQ as missing justification
when its evidence_status is `not_applicable` or `manual_evidence_required`.
