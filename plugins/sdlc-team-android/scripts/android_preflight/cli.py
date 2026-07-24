"""CLI wrapper: run Android pre-flight checks against a project directory.

Parses AndroidManifest.xml (permissions, exported components, application flags)
and Gradle files (targetSdk/minSdk/compileSdk, release build type, secrets),
runs the pure checks in :mod:`checks`, prints findings, and exits non-zero when
any ERROR is found (so it can gate a release skill or CI step).

Usage:
    python -m android_preflight.cli <project-dir> [--play-min-target N]
        [--manifest PATH]

Heuristics are best-effort and never fatal: a file it cannot find or parse is
reported as INFO/skip, not a crash. Gradle parsing is regex-based (it does not
evaluate the build), so values set dynamically may not be detected — findings
are additive, not a guarantee.
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from .checks import (
    Component,
    Finding,
    Severity,
    check_manifest,
    check_release_config,
    check_sdk_policy,
)

# Play's current annual minimum target API. Version-sensitive — override with
# --play-min-target; re-verify against the live Play requirement.
DEFAULT_PLAY_MIN_TARGET = 35

_ANDROID_NS = "http://schemas.android.com/apk/res/android"
_GRADLE_GLOBS = ("build.gradle", "build.gradle.kts")
_SECRET_SCAN_GLOBS = ("build.gradle", "build.gradle.kts", "gradle.properties")


def _find_first(root: Path, name: str) -> Path | None:
    """Find the first file named ``name`` under ``root`` (shallowest wins)."""
    matches = sorted(root.rglob(name), key=lambda p: len(p.parts))
    return matches[0] if matches else None


def _attr(el: ET.Element, name: str) -> str | None:
    return el.get(f"{{{_ANDROID_NS}}}{name}")


def _as_bool(value: str | None) -> bool | None:
    if value is None:
        return None
    return value.strip().lower() == "true"


def parse_manifest(path: Path) -> dict:
    """Parse AndroidManifest.xml into the inputs check_manifest expects."""
    result: dict = {
        "permissions": [],
        "components": [],
        "uses_cleartext_traffic": None,
        "debuggable": None,
        "allow_backup": None,
    }
    try:
        tree = ET.parse(path)
    except (OSError, ET.ParseError):
        return result
    manifest = tree.getroot()

    for perm in manifest.findall("uses-permission"):
        name = _attr(perm, "name")
        if name:
            result["permissions"].append(name)

    app = manifest.find("application")
    if app is not None:
        result["uses_cleartext_traffic"] = _as_bool(_attr(app, "usesCleartextTraffic"))
        result["debuggable"] = _as_bool(_attr(app, "debuggable"))
        result["allow_backup"] = _as_bool(_attr(app, "allowBackup"))
        for tag in ("activity", "service", "receiver", "provider"):
            for comp in app.findall(tag):
                name = _attr(comp, "name") or f"<{tag}>"
                exported = _as_bool(_attr(comp, "exported"))
                result["components"].append(
                    Component(
                        name=name,
                        exported=bool(exported),
                        has_permission=_attr(comp, "permission") is not None,
                        has_intent_filter=comp.find("intent-filter") is not None,
                    )
                )
    return result


def _grep_int(texts: list[str], key: str) -> int | None:
    """Extract an integer DSL value like `targetSdk = 35` / `targetSdkVersion 35`."""
    pattern = re.compile(rf"{key}\s*(?:=|\s)\s*(\d+)")
    for text in texts:
        m = pattern.search(text)
        if m:
            return int(m.group(1))
    return None


def parse_gradle(root: Path) -> dict:
    """Parse Gradle files for SDK levels and release-build flags (regex-based)."""
    texts: list[str] = []
    for pattern in _GRADLE_GLOBS:
        for f in root.rglob(pattern):
            try:
                texts.append(f.read_text(encoding="utf-8", errors="ignore"))
            except OSError:
                continue

    sdk = {
        "target_sdk": _grep_int(texts, "targetSdk(?:Version)?"),
        "min_sdk": _grep_int(texts, "minSdk(?:Version)?"),
        "compile_sdk": _grep_int(texts, "compileSdk(?:Version)?"),
    }

    joined = "\n".join(texts)
    release = {
        "minifyEnabled": bool(
            re.search(r"(?:isMinifyEnabled|minifyEnabled)\s*=?\s*true", joined)
        ),
        "shrinkResources": bool(
            re.search(r"(?:isShrinkResources|shrinkResources)\s*=?\s*true", joined)
        ),
        "usesDebugSigning": bool(
            re.search(
                r"signingConfig\s*=?\s*signingConfigs\.(?:getByName\(\s*)?[\"']?debug",
                joined,
            )
        ),
    }
    return {"sdk": sdk, "release": release}


def _read_secret_texts(root: Path) -> list[str]:
    texts: list[str] = []
    for pattern in _SECRET_SCAN_GLOBS:
        for f in root.rglob(pattern):
            try:
                texts.append(f.read_text(encoding="utf-8", errors="ignore"))
            except OSError:
                continue
    return texts


def run(args: argparse.Namespace) -> list[Finding]:
    """Run all checks for the resolved project and return findings."""
    root = Path(args.project).resolve()
    findings: list[Finding] = []

    manifest_path = (
        Path(args.manifest)
        if args.manifest
        else _find_first(root, "AndroidManifest.xml")
    )
    if manifest_path is None:
        findings.append(
            Finding(
                Severity.INFO,
                "no-manifest",
                "No AndroidManifest.xml found to check (pass --manifest to point "
                "at yours).",
            )
        )
    else:
        m = parse_manifest(manifest_path)
        findings.extend(
            check_manifest(
                m["permissions"],
                components=m["components"],
                uses_cleartext_traffic=m["uses_cleartext_traffic"],
                debuggable=m["debuggable"],
                allow_backup=m["allow_backup"],
            )
        )

    gradle = parse_gradle(root)
    findings.extend(
        check_sdk_policy(
            target_sdk=gradle["sdk"]["target_sdk"],
            min_sdk=gradle["sdk"]["min_sdk"],
            compile_sdk=gradle["sdk"]["compile_sdk"],
            play_min_target=args.play_min_target,
        )
    )
    findings.extend(
        check_release_config(
            gradle["release"],
            gradle_texts=_read_secret_texts(root),
        )
    )
    return findings


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser."""
    parser = argparse.ArgumentParser(
        prog="android-preflight",
        description="Android Play Store / release submission pre-flight checks.",
    )
    parser.add_argument("project", help="Path to the Android project directory")
    parser.add_argument("--manifest", help="Explicit AndroidManifest.xml path")
    parser.add_argument(
        "--play-min-target",
        type=int,
        default=DEFAULT_PLAY_MIN_TARGET,
        help=f"Play's current minimum target API (default {DEFAULT_PLAY_MIN_TARGET}; version-sensitive)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point. Returns process exit code (non-zero if any ERROR)."""
    args = build_parser().parse_args(argv)
    findings = run(args)

    errors = [f for f in findings if f.severity is Severity.ERROR]
    warnings = [f for f in findings if f.severity is Severity.WARNING]

    if not findings:
        print("Android pre-flight: no issues found.")
        return 0

    for finding in findings:
        print(finding)

    print(
        f"\nAndroid pre-flight: {len(errors)} error(s), {len(warnings)} warning(s), "
        f"{len(findings) - len(errors) - len(warnings)} info."
    )
    return 1 if errors else 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
