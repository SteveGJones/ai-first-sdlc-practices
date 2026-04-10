# Technology Registry Maintenance Strategy

**Sub-feature**: #150 (EPIC #142)
**Date**: 2026-04-10

## Overview

The technology registry at `data/technology-registry/` requires ongoing maintenance to stay accurate. This document defines the process for verifying entries, adding new technologies, updating stale data, and eventually automating freshness checks.

## Freshness Model

Each Section A, B, and C entry has a `verified_date` field (YYYY-MM-DD). The index file `_index.yaml` has a `staleness_threshold_days` field (default: 180 days).

**An entry is stale when:** `today - verified_date > staleness_threshold_days`

**What "verified" means:** Someone (human or agent) confirmed the entry is still accurate — the package exists, the URL works, the publisher is correct, and the description matches current capabilities.

## Maintenance Cadence

### Quarterly review (recommended)

Every 3 months, run a staleness check across all entries:

1. Identify entries where `verified_date` is older than the threshold
2. For each stale entry, verify the source URL still resolves
3. Check if the package version has changed significantly
4. Update `verified_date` to today if the entry is still accurate
5. Update fields if capabilities, package names, or URLs have changed
6. Remove entries for tools that no longer exist or are deprecated

### Event-driven updates

Update entries when:
- A vendor announces a new MCP server (add to registry)
- A package is deprecated or archived (mark or remove)
- A new version changes capabilities significantly (update description)
- A new technology becomes commonly used (add new file)
- Setup-team or pipeline-orchestrator falls back to web search for a technology that should be in the registry (add it)

## Adding a New Technology

1. **Create the technology file** at `data/technology-registry/{key}.yaml` using the schema in `docs/architecture/technology-registry-schema.md`
2. **Add detection patterns** to `_index.yaml` under the appropriate ecosystems
3. **Add aliases** if the technology has common informal names
4. **Add to the manifest** in `_index.yaml` with the file path and display name
5. **Run cross-validation** to ensure index-file consistency
6. **Commit and push** — the registry is version-controlled, changes go through normal PR review

## Removing a Technology

1. Remove the YAML file from `data/technology-registry/`
2. Remove the manifest entry from `_index.yaml`
3. Remove detection patterns that point to the removed key
4. Remove aliases that point to the removed key
5. Run cross-validation to ensure no dangling references

## Handling Deprecated Tools

When a Section A tool is deprecated:
- If a replacement exists, add the replacement as a new entry and add a `deprecated_by` note in the old entry's description
- If no replacement exists, remove the entry from Section A and consider adding a Section C gap
- Update `verified_date` to document when the deprecation was confirmed

## Validator Script

A future `tools/validation/check-technology-registry.py` script should enforce the 10 validation rules defined in the schema doc:

1. Required fields present (per Section A/B/C)
2. Type enum valid (Section A)
3. Ecosystem enum valid (Section B)
4. Trusted source type valid
5. Dates parseable (YYYY-MM-DD)
6. Slug format valid (Section C)
7. Index-file consistency (manifest ↔ files)
8. Alias targets valid
9. Detection targets valid
10. No duplicate detection keys

Additionally:
11. **Staleness check**: flag entries where `verified_date` is older than `staleness_threshold_days`
12. **URL reachability** (optional, slow): check that `source` URLs return 200

The validator should be runnable as:
```bash
python tools/validation/check-technology-registry.py                    # All rules
python tools/validation/check-technology-registry.py --staleness-only   # Only rule 11
python tools/validation/check-technology-registry.py --check-urls       # Include rule 12
```

## CI Integration

Add the registry validator to the existing CI pipeline (`.github/workflows/plugin-packaging-sync.yml` or a new workflow):

```yaml
- name: Validate technology registry
  run: python tools/validation/check-technology-registry.py
```

This ensures:
- PRs that modify registry files pass all validation rules
- No broken references between index and technology files
- All required fields are present

The staleness check should run on a schedule (e.g., monthly cron) rather than on every PR, since staleness is time-based:

```yaml
on:
  schedule:
    - cron: '0 0 1 * *'  # First of each month
```

## Schema Evolution

The `version` field in `_index.yaml` tracks the schema version:
- **Non-breaking changes** (new optional fields, new enum values): version stays the same
- **Breaking changes** (required field additions, structural changes): bump the version

When bumping the version, update:
1. `_index.yaml` version field
2. `docs/architecture/technology-registry-schema.md` schema doc
3. `tools/validation/check-technology-registry.py` validator (when it exists)
4. All affected technology files

## Ownership

The registry is maintained alongside the SDLC framework itself. Anyone contributing to the framework can update technology entries. The maintenance cadence is a team responsibility, not assigned to a single person.

For large-scale updates (verifying all 31+ technologies), the same parallel research agent approach used during initial population can be reused — dispatch agents per category to verify entries in parallel.
