"""CLI wrapper: run iOS pre-flight checks against a project directory.

Loads Info.plist / entitlements / PrivacyInfo.xcprivacy, heuristically detects
which sensitive frameworks and required-reason APIs the source uses, runs the
pure checks in :mod:`checks`, prints findings, and exits non-zero when any
ERROR is found (so it can gate a release skill or CI step).

Usage:
    python -m ios_preflight.cli <project-dir> [--info-plist PATH]
        [--entitlements PATH] [--uses-push] [--debug-build]

Heuristics are best-effort and never fatal: a file it cannot find or parse is
reported as an INFO/skip, not a crash — the checks still run on what is found.
"""

from __future__ import annotations

import argparse
import plistlib
import re
import sys
from pathlib import Path

from .checks import (
    FRAMEWORK_USAGE_KEYS,
    Finding,
    Severity,
    check_entitlements,
    check_export_compliance,
    check_privacy_manifest,
    check_usage_descriptions,
)

# Source extensions worth scanning for framework imports and API usage.
_SOURCE_GLOBS = ("*.swift", "*.m", "*.mm", "*.h")

# Directories that indicate bundled third-party SDKs / dependency managers.
_SDK_MARKERS = ("Podfile", "Pods", "Cartfile", "Carthage")

# Heuristic patterns for required-reason API usage.
_REQUIRED_REASON_PATTERNS = (
    r"\bUserDefaults\b",
    r"\bNSUserDefaults\b",
    r"\.creationDate\b",
    r"\.modificationDate\b",
    r"\bsystemUptime\b",
    r"\bmach_absolute_time\b",
    r"\bstatvfs\b",
    r"\bvolumeAvailableCapacity",
)


def _load_plist(path: Path) -> dict:
    """Load a plist file, returning {} on missing/unreadable/invalid."""
    try:
        with path.open("rb") as handle:
            data = plistlib.load(handle)
        return data if isinstance(data, dict) else {}
    except (OSError, plistlib.InvalidFileException, ValueError):
        return {}


def _find_first(root: Path, name: str) -> Path | None:
    """Find the first file named ``name`` under ``root`` (shallowest wins)."""
    matches = sorted(root.rglob(name), key=lambda p: len(p.parts))
    return matches[0] if matches else None


def detect_used_frameworks(root: Path) -> set[str]:
    """Scan source files for imported frameworks that map to a usage key."""
    import_res = [
        re.compile(r"^\s*import\s+([A-Za-z_][A-Za-z0-9_]*)", re.MULTILINE),
        re.compile(r"@import\s+([A-Za-z_][A-Za-z0-9_]*)"),
        re.compile(r"#import\s+<([A-Za-z_][A-Za-z0-9_]*)/"),
    ]
    known = set(FRAMEWORK_USAGE_KEYS)
    found: set[str] = set()
    for pattern in _SOURCE_GLOBS:
        for src in root.rglob(pattern):
            try:
                text = src.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for regex in import_res:
                for name in regex.findall(text):
                    if name.lower() in known:
                        found.add(name)
    return found


def detect_required_reason_apis(root: Path) -> bool:
    """Heuristically detect required-reason API usage in source."""
    combined = re.compile("|".join(_REQUIRED_REASON_PATTERNS))
    for pattern in _SOURCE_GLOBS:
        for src in root.rglob(pattern):
            try:
                text = src.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if combined.search(text):
                return True
    return False


def detect_third_party_sdks(root: Path) -> bool:
    """Detect dependency-manager markers indicating bundled third-party SDKs."""
    for marker in _SDK_MARKERS:
        if (root / marker).exists() or _find_first(root, marker) is not None:
            return True
    resolved = _find_first(root, "Package.resolved")
    if resolved is not None:
        try:
            text = resolved.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            return False
        # A non-Apple package URL implies a third-party SDK.
        for match in re.findall(r'"(https?://[^"]+)"', text):
            if "apple.com" not in match and "github.com/apple" not in match:
                return True
    return False


def run(args: argparse.Namespace) -> list[Finding]:
    """Run all checks for the resolved project and return findings."""
    root = Path(args.project).resolve()
    findings: list[Finding] = []

    info_path = (
        Path(args.info_plist) if args.info_plist else _find_first(root, "Info.plist")
    )
    if info_path is None:
        findings.append(
            Finding(
                Severity.INFO,
                "no-info-plist",
                "No Info.plist found to check (modern targets may generate it "
                "from build settings — pass --info-plist to point at yours).",
            )
        )
        info_plist: dict = {}
    else:
        info_plist = _load_plist(info_path)

    used = detect_used_frameworks(root)
    findings.extend(check_usage_descriptions(info_plist, used))
    findings.extend(check_export_compliance(info_plist))

    manifest_present = _find_first(root, "PrivacyInfo.xcprivacy") is not None
    findings.extend(
        check_privacy_manifest(
            manifest_present,
            uses_required_reason_apis=detect_required_reason_apis(root),
            bundles_third_party_sdks=detect_third_party_sdks(root),
        )
    )

    ent_path = (
        Path(args.entitlements)
        if args.entitlements
        else _find_first(root, "*.entitlements")
    )
    if ent_path is not None:
        findings.extend(
            check_entitlements(
                _load_plist(ent_path),
                is_release=not args.debug_build,
                uses_push=args.uses_push,
            )
        )

    return findings


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser."""
    parser = argparse.ArgumentParser(
        prog="ios-preflight",
        description="iOS TestFlight / App Store submission pre-flight checks.",
    )
    parser.add_argument("project", help="Path to the iOS project directory")
    parser.add_argument("--info-plist", help="Explicit Info.plist path")
    parser.add_argument("--entitlements", help="Explicit .entitlements path")
    parser.add_argument(
        "--uses-push",
        action="store_true",
        help="App uses push notifications (checks aps-environment)",
    )
    parser.add_argument(
        "--debug-build",
        action="store_true",
        help="Treat as a debug build (skips release-only entitlement checks)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point. Returns process exit code (non-zero if any ERROR)."""
    args = build_parser().parse_args(argv)
    findings = run(args)

    errors = [f for f in findings if f.severity is Severity.ERROR]
    warnings = [f for f in findings if f.severity is Severity.WARNING]

    if not findings:
        print("iOS pre-flight: no issues found.")
        return 0

    for finding in findings:
        print(finding)

    print(
        f"\niOS pre-flight: {len(errors)} error(s), {len(warnings)} warning(s), "
        f"{len(findings) - len(errors) - len(warnings)} info."
    )
    return 1 if errors else 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
