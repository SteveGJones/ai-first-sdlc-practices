#!/usr/bin/env python3
"""
Technology registry validator.

Validates the curated technology registry at data/technology-registry/ against
the schema defined in docs/architecture/technology-registry-schema.md.

Enforces 11 rules:
  1. Required fields present (top-level, Section A/B/C, our_agents, trusted_sources)
  2. Type enum valid (Section A)
  3. Ecosystem enum valid (Section B)
  4. Trusted source type valid
  5. Dates parseable (YYYY-MM-DD)
  6. Slug format valid (Section C — lowercase, hyphenated, no spaces/specials)
  7. Index-file consistency (manifest vs disk)
  8. Alias targets valid (alias values map to manifest keys)
  9. Detection targets valid (detection values map to manifest keys)
  10. No duplicate detection keys (no package twice in same ecosystem)
  11. Staleness check (verified_date older than staleness_threshold_days)

Usage:
    python tools/validation/check-technology-registry.py                    # Rules 1-10
    python tools/validation/check-technology-registry.py --staleness-only   # Only rule 11
    python tools/validation/check-technology-registry.py --include-staleness # Rules 1-11

Exit codes:
    0 — validation passed
    1 — validation failed (at least one error)
    2 — configuration error (registry missing, YAML malformed)
"""

import argparse
import re
import sys
from datetime import date, datetime
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML not installed. Run: pip install pyyaml", file=sys.stderr)
    sys.exit(2)


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
REGISTRY_DIR = REPO_ROOT / "data" / "technology-registry"
INDEX_FILE = REGISTRY_DIR / "_index.yaml"

# --- Enum definitions from the schema ---

SECTION_A_TYPES = {
    "claude-plugin",
    "mcp-server-npm",
    "mcp-server-pip",
    "mcp-server-binary",
    "github-action",
    "standalone-cli",
}

SECTION_B_ECOSYSTEMS = {
    "pip",
    "npm",
    "cargo",
    "go",
    "gem",
}

TRUSTED_SOURCE_TYPES = {
    "github-org",
    "npm-scope",
    "pypi-publisher",
    "vendor-docs",
    "other",
}

# --- Required fields per entry type ---

TOP_LEVEL_REQUIRED = {"display_name", "category", "description", "trusted_sources"}

SECTION_A_REQUIRED = {"name", "type", "package", "source", "description", "verified_date"}

SECTION_B_REQUIRED = {
    "name",
    "package",
    "ecosystem",
    "source",
    "description",
    "verified_date",
}

SECTION_C_REQUIRED = {
    "topic",
    "slug",
    "why",
    "agent_would_know",
    "research_scope",
    "create_command",
    "verified_date",
}

OUR_AGENTS_REQUIRED = {"agent", "plugin", "relevance"}

TRUSTED_SOURCES_REQUIRED = {"url", "type"}

# Slug pattern: lowercase letters, digits, and hyphens only
SLUG_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def load_yaml(filepath: Path) -> dict | list | None:
    """Load a YAML file and return its contents."""
    try:
        with filepath.open() as handle:
            return yaml.safe_load(handle)
    except yaml.YAMLError as exc:
        print(f"ERROR: {filepath} is not valid YAML: {exc}", file=sys.stderr)
        sys.exit(2)
    except OSError as exc:
        print(f"ERROR: Cannot read {filepath}: {exc}", file=sys.stderr)
        sys.exit(2)


def parse_date(date_str: str) -> date | None:
    """Parse a YYYY-MM-DD date string. Returns None if invalid."""
    try:
        # Handle both string and non-string (e.g., datetime.date from YAML)
        if isinstance(date_str, date):
            return date_str
        return datetime.strptime(str(date_str), "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def check_required_fields(
    entry: dict,
    required: set[str],
    context: str,
) -> list[str]:
    """Check that all required fields are present in an entry."""
    errors = []
    for field in sorted(required):
        if field not in entry or entry[field] is None:
            errors.append(f"[Rule 1] {context}: missing required field '{field}'")
    return errors


def validate_technology_file(
    tech_key: str,
    filepath: Path,
    staleness_threshold: int | None,
) -> tuple[list[str], list[str]]:
    """
    Validate a single technology YAML file.

    Returns (errors, staleness_warnings).
    """
    errors: list[str] = []
    warnings: list[str] = []
    rel = filepath.relative_to(REPO_ROOT)

    data = load_yaml(filepath)
    if not isinstance(data, dict):
        errors.append(f"[Rule 1] {rel}: file must be a YAML mapping")
        return errors, warnings

    # --- Rule 1: Top-level required fields ---
    for field in sorted(TOP_LEVEL_REQUIRED):
        if field not in data or data[field] is None:
            errors.append(f"[Rule 1] {rel}: missing required top-level field '{field}'")

    # --- Section A validation ---
    section_a = data.get("section_a") or []
    for i, entry in enumerate(section_a):
        ctx = f"{rel} section_a[{i}]"
        errors.extend(check_required_fields(entry, SECTION_A_REQUIRED, ctx))

        # Rule 2: Type enum
        entry_type = entry.get("type")
        if entry_type and entry_type not in SECTION_A_TYPES:
            errors.append(
                f"[Rule 2] {ctx}: invalid type '{entry_type}' — "
                f"must be one of {sorted(SECTION_A_TYPES)}"
            )

        # Rule 5: Date
        vd = entry.get("verified_date")
        if vd is not None:
            parsed = parse_date(vd)
            if parsed is None:
                errors.append(
                    f"[Rule 5] {ctx}: invalid verified_date '{vd}' — "
                    f"must be YYYY-MM-DD"
                )
            elif staleness_threshold is not None and parsed is not None:
                age = (date.today() - parsed).days
                if age > staleness_threshold:
                    warnings.append(
                        f"[Rule 11] {ctx}: verified_date '{parsed}' is "
                        f"{age} days old (threshold: {staleness_threshold})"
                    )

    # --- Section B validation ---
    section_b = data.get("section_b") or []
    for i, entry in enumerate(section_b):
        ctx = f"{rel} section_b[{i}]"
        errors.extend(check_required_fields(entry, SECTION_B_REQUIRED, ctx))

        # Rule 3: Ecosystem enum
        ecosystem = entry.get("ecosystem")
        if ecosystem and ecosystem not in SECTION_B_ECOSYSTEMS:
            errors.append(
                f"[Rule 3] {ctx}: invalid ecosystem '{ecosystem}' — "
                f"must be one of {sorted(SECTION_B_ECOSYSTEMS)}"
            )

        # Rule 5: Date
        vd = entry.get("verified_date")
        if vd is not None:
            parsed = parse_date(vd)
            if parsed is None:
                errors.append(
                    f"[Rule 5] {ctx}: invalid verified_date '{vd}' — "
                    f"must be YYYY-MM-DD"
                )
            elif staleness_threshold is not None and parsed is not None:
                age = (date.today() - parsed).days
                if age > staleness_threshold:
                    warnings.append(
                        f"[Rule 11] {ctx}: verified_date '{parsed}' is "
                        f"{age} days old (threshold: {staleness_threshold})"
                    )

    # --- Section C validation ---
    section_c = data.get("section_c") or []
    for i, entry in enumerate(section_c):
        ctx = f"{rel} section_c[{i}]"
        errors.extend(check_required_fields(entry, SECTION_C_REQUIRED, ctx))

        # Rule 6: Slug format
        slug = entry.get("slug")
        if slug is not None:
            if not SLUG_PATTERN.match(str(slug)):
                errors.append(
                    f"[Rule 6] {ctx}: invalid slug '{slug}' — "
                    f"must be lowercase, hyphenated, no spaces or special characters"
                )

        # Rule 5: Date
        vd = entry.get("verified_date")
        if vd is not None:
            parsed = parse_date(vd)
            if parsed is None:
                errors.append(
                    f"[Rule 5] {ctx}: invalid verified_date '{vd}' — "
                    f"must be YYYY-MM-DD"
                )
            elif staleness_threshold is not None and parsed is not None:
                age = (date.today() - parsed).days
                if age > staleness_threshold:
                    warnings.append(
                        f"[Rule 11] {ctx}: verified_date '{parsed}' is "
                        f"{age} days old (threshold: {staleness_threshold})"
                    )

    # --- our_agents validation ---
    our_agents = data.get("our_agents") or []
    for i, entry in enumerate(our_agents):
        ctx = f"{rel} our_agents[{i}]"
        errors.extend(check_required_fields(entry, OUR_AGENTS_REQUIRED, ctx))

    # --- trusted_sources validation ---
    trusted_sources = data.get("trusted_sources") or []
    for i, entry in enumerate(trusted_sources):
        ctx = f"{rel} trusted_sources[{i}]"
        errors.extend(check_required_fields(entry, TRUSTED_SOURCES_REQUIRED, ctx))

        # Rule 4: Trusted source type enum
        src_type = entry.get("type")
        if src_type and src_type not in TRUSTED_SOURCE_TYPES:
            errors.append(
                f"[Rule 4] {ctx}: invalid trusted source type '{src_type}' — "
                f"must be one of {sorted(TRUSTED_SOURCE_TYPES)}"
            )

    return errors, warnings


def validate_index(
    index: dict,
    tech_keys: set[str],
) -> list[str]:
    """
    Validate the index file against the registry directory.

    Rules 7-10.
    """
    errors: list[str] = []

    # --- Rule 7: Index-file consistency ---
    manifest = index.get("technologies") or {}

    # Every file in manifest exists on disk
    for key, tech_info in manifest.items():
        filename = tech_info.get("file")
        if not filename:
            errors.append(
                f"[Rule 7] _index.yaml technologies.{key}: missing 'file' field"
            )
            continue
        filepath = REGISTRY_DIR / filename
        if not filepath.exists():
            errors.append(
                f"[Rule 7] _index.yaml technologies.{key}: file '{filename}' "
                f"not found on disk"
            )

    # Every .yaml file (except _index.yaml) is in the manifest
    manifest_files = {
        tech_info.get("file") for tech_info in manifest.values() if tech_info.get("file")
    }
    for filepath in sorted(REGISTRY_DIR.glob("*.yaml")):
        if filepath.name == "_index.yaml":
            continue
        if filepath.name not in manifest_files:
            errors.append(
                f"[Rule 7] {filepath.name} exists on disk but is not in "
                f"_index.yaml technologies manifest"
            )

    # --- Rule 8: Alias targets valid ---
    aliases = index.get("aliases") or {}
    for alias_name, target in aliases.items():
        if target not in tech_keys:
            errors.append(
                f"[Rule 8] _index.yaml aliases.{alias_name}: target '{target}' "
                f"not found in technologies manifest"
            )

    # --- Rule 9: Detection targets valid ---
    detection = index.get("detection") or {}
    for ecosystem, packages in detection.items():
        if not isinstance(packages, dict):
            errors.append(
                f"[Rule 9] _index.yaml detection.{ecosystem}: expected a mapping"
            )
            continue
        for pkg, target in packages.items():
            if target not in tech_keys:
                errors.append(
                    f"[Rule 9] _index.yaml detection.{ecosystem}.{pkg}: "
                    f"target '{target}' not found in technologies manifest"
                )

    # --- Rule 10: No duplicate detection keys ---
    for ecosystem, packages in detection.items():
        if not isinstance(packages, dict):
            continue
        seen: dict[str, str] = {}
        for pkg in packages:
            pkg_lower = pkg.lower()
            if pkg_lower in seen:
                errors.append(
                    f"[Rule 10] _index.yaml detection.{ecosystem}: "
                    f"duplicate package '{pkg}' (also appears as '{seen[pkg_lower]}')"
                )
            else:
                seen[pkg_lower] = pkg

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate the curated technology registry"
    )
    parser.add_argument(
        "--staleness-only",
        action="store_true",
        help="Only run rule 11 (staleness check)",
    )
    parser.add_argument(
        "--include-staleness",
        action="store_true",
        help="Include rule 11 (staleness check) alongside rules 1-10",
    )
    args = parser.parse_args()

    # --- Preflight checks ---
    if not REGISTRY_DIR.exists():
        print(
            f"ERROR: Registry directory not found: {REGISTRY_DIR}",
            file=sys.stderr,
        )
        return 2

    if not INDEX_FILE.exists():
        print(f"ERROR: Index file not found: {INDEX_FILE}", file=sys.stderr)
        return 2

    index = load_yaml(INDEX_FILE)
    if not isinstance(index, dict):
        print("ERROR: _index.yaml must be a YAML mapping", file=sys.stderr)
        return 2

    staleness_threshold_days = index.get("staleness_threshold_days")
    manifest = index.get("technologies") or {}
    tech_keys = set(manifest.keys())

    # Determine whether to compute staleness
    compute_staleness = args.staleness_only or args.include_staleness
    threshold_for_files = staleness_threshold_days if compute_staleness else None

    all_errors: list[str] = []
    all_warnings: list[str] = []
    tech_count = 0

    if not args.staleness_only:
        # --- Rules 7-10: Index-level validation ---
        all_errors.extend(validate_index(index, tech_keys))

    # --- Per-technology-file validation (rules 1-6, optionally 11) ---
    for tech_key, tech_info in sorted(manifest.items()):
        filename = tech_info.get("file")
        if not filename:
            continue
        filepath = REGISTRY_DIR / filename
        if not filepath.exists():
            # Already reported by Rule 7
            continue

        if args.staleness_only:
            # Only compute staleness, skip structural rules
            _, warnings = validate_technology_file(
                tech_key, filepath, staleness_threshold_days
            )
            all_warnings.extend(warnings)
        else:
            errors, warnings = validate_technology_file(
                tech_key, filepath, threshold_for_files
            )
            all_errors.extend(errors)
            all_warnings.extend(warnings)

        tech_count += 1

    # --- Output ---
    if all_warnings:
        print(f"\nStaleness warnings ({len(all_warnings)}):\n")
        for warning in all_warnings:
            print(f"  - {warning}")
        print()

    if args.staleness_only:
        if all_warnings:
            print(
                f"Staleness check found {len(all_warnings)} stale "
                f"entr{'y' if len(all_warnings) == 1 else 'ies'} "
                f"across {tech_count} technologies."
            )
            return 1
        print(
            f"Technology registry staleness check PASSED — "
            f"{tech_count} technologies verified."
        )
        return 0

    if all_errors:
        print(f"\nTechnology registry validation FAILED — "
              f"{len(all_errors)} error(s):\n")
        for error in all_errors:
            print(f"  - {error}")
        print()
        return 1

    print(
        f"Technology registry validation PASSED — "
        f"{tech_count} technologies verified."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
