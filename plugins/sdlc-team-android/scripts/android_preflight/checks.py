"""Pure pre-flight check functions for Android Play Store / release submission.

Each check takes already-parsed data (manifest permission/attribute info, SDK
levels, release-config flags) and returns a list of :class:`Finding`. No file
or network I/O here so the rules are deterministic and unit-testable; loading
and the CLI live in ``cli.py``.

The rules encode real Play blockers / release-quality issues:
- Sensitive permissions declared without justification (esp. background location).
- Exported components with no permission / intent-filter guard.
- ``usesCleartextTraffic`` / ``debuggable`` / ``allowBackup`` risks in release.
- ``targetSdk`` below the Play annual minimum, or inconsistent SDK levels.
- Release build not shrinking (R8), using a debug signing config, or committing
  secrets in Gradle files.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import Enum


class Severity(str, Enum):
    """Severity of a pre-flight finding."""

    ERROR = "error"  # will block a submission or is a release-quality defect
    WARNING = "warning"  # likely to cause friction / policy scrutiny
    INFO = "info"  # advisory / good-practice


@dataclass(frozen=True)
class Finding:
    """A single pre-flight check result."""

    severity: Severity
    code: str
    message: str

    def __str__(self) -> str:
        return f"[{self.severity.value.upper()}] {self.code}: {self.message}"


# Sensitive/restricted permissions that require a Play Console declaration and/or
# strong justification. Background location is the classic rejection trap.
# (Not exhaustive — Play's list evolves; version-sensitive.)
DANGEROUS_PERMISSIONS: frozenset[str] = frozenset(
    {
        "android.permission.ACCESS_BACKGROUND_LOCATION",
        "android.permission.ACCESS_FINE_LOCATION",
        "android.permission.ACCESS_COARSE_LOCATION",
        "android.permission.READ_SMS",
        "android.permission.SEND_SMS",
        "android.permission.RECEIVE_SMS",
        "android.permission.READ_CALL_LOG",
        "android.permission.WRITE_CALL_LOG",
        "android.permission.QUERY_ALL_PACKAGES",
        "android.permission.MANAGE_EXTERNAL_STORAGE",
        "android.permission.CAMERA",
        "android.permission.RECORD_AUDIO",
        "android.permission.READ_CONTACTS",
        "android.permission.READ_MEDIA_IMAGES",
        "android.permission.READ_MEDIA_VIDEO",
        "android.permission.SCHEDULE_EXACT_ALARM",
        "android.permission.USE_FULL_SCREEN_INTENT",
    }
)

# The permission Play treats as needing exactly one core feature + demo video.
_HIGHEST_SCRUTINY = "android.permission.ACCESS_BACKGROUND_LOCATION"


@dataclass(frozen=True)
class Component:
    """A manifest component (activity/service/receiver/provider)."""

    name: str
    exported: bool
    has_permission: bool = False
    has_intent_filter: bool = False


def check_manifest(
    permissions: Iterable[str],
    *,
    components: Iterable[Component] = (),
    uses_cleartext_traffic: bool | None = None,
    debuggable: bool | None = None,
    allow_backup: bool | None = None,
    justified_permissions: Iterable[str] = (),
) -> list[Finding]:
    """Check AndroidManifest permission and component hygiene.

    - Sensitive permissions not in ``justified_permissions`` are flagged (ERROR
      for background location — the top rejection trap; WARNING otherwise).
    - An exported component with neither a permission nor an intent-filter is an
      ERROR (it's callable by any app).
    - ``usesCleartextTraffic``/``debuggable`` true in a release manifest, and
      ``allowBackup`` left default-true, are WARNINGs.
    """
    findings: list[Finding] = []
    justified = {p for p in justified_permissions}

    for perm in permissions:
        if perm not in DANGEROUS_PERMISSIONS or perm in justified:
            continue
        if perm == _HIGHEST_SCRUTINY:
            findings.append(
                Finding(
                    Severity.ERROR,
                    "sensitive-permission",
                    f"{perm} requires a Play Console declaration with exactly one "
                    f"core feature, a strong justification, and a working demo "
                    f"video — a top rejection cause. Justify it or remove it.",
                )
            )
        else:
            findings.append(
                Finding(
                    Severity.WARNING,
                    "sensitive-permission",
                    f"{perm} is a sensitive/restricted permission that may need a "
                    f"Play declaration and prominent-disclosure/consent. Confirm "
                    f"a genuine feature needs it.",
                )
            )

    for comp in components:
        if comp.exported and not comp.has_permission and not comp.has_intent_filter:
            findings.append(
                Finding(
                    Severity.ERROR,
                    "exported-component-unguarded",
                    f"Component {comp.name} is exported with no permission or "
                    f"intent-filter — any app can invoke it. Add a permission or "
                    f"set android:exported=false.",
                )
            )

    if uses_cleartext_traffic is True:
        findings.append(
            Finding(
                Severity.WARNING,
                "cleartext-traffic",
                'android:usesCleartextTraffic="true" allows unencrypted HTTP. '
                "Prefer HTTPS + a network-security-config allowlist for any "
                "genuinely-needed cleartext host.",
            )
        )
    if debuggable is True:
        findings.append(
            Finding(
                Severity.ERROR,
                "debuggable-release",
                'android:debuggable="true" must not ship in a release build.',
            )
        )
    if allow_backup is True:
        findings.append(
            Finding(
                Severity.INFO,
                "allow-backup",
                "android:allowBackup defaults to true — confirm you want cloud/ADB "
                "backup of app data, or set it false / configure backup rules for "
                "sensitive data.",
            )
        )

    return findings


def check_sdk_policy(
    *,
    target_sdk: int | None,
    min_sdk: int | None = None,
    compile_sdk: int | None = None,
    play_min_target: int,
) -> list[Finding]:
    """Check SDK levels against Play's annual target-API mandate and consistency.

    - ``target_sdk`` below ``play_min_target`` is an ERROR (new apps/updates are
      blocked and the app is hidden on newer devices).
    - ``compile_sdk`` below ``target_sdk`` is an ERROR (can't compile against the
      target's APIs).
    - ``min_sdk`` above ``target_sdk`` is an ERROR (nonsensical range).
    """
    findings: list[Finding] = []

    if target_sdk is None:
        return [
            Finding(
                Severity.WARNING,
                "missing-target-sdk",
                "No targetSdk found to check. Set targetSdk to at least the "
                f"current Play minimum (API {play_min_target}).",
            )
        ]

    if target_sdk < play_min_target:
        findings.append(
            Finding(
                Severity.ERROR,
                "target-sdk-too-low",
                f"targetSdk {target_sdk} is below the current Play minimum "
                f"(API {play_min_target}). New apps/updates are blocked and the "
                f"app is hidden on newer devices. (Play deadlines are "
                f"version-sensitive — re-verify the current requirement.)",
            )
        )
    if compile_sdk is not None and compile_sdk < target_sdk:
        findings.append(
            Finding(
                Severity.ERROR,
                "compile-sdk-below-target",
                f"compileSdk {compile_sdk} is below targetSdk {target_sdk} — you "
                f"can't compile against the target's APIs. Raise compileSdk.",
            )
        )
    if min_sdk is not None and min_sdk > target_sdk:
        findings.append(
            Finding(
                Severity.ERROR,
                "min-sdk-above-target",
                f"minSdk {min_sdk} is greater than targetSdk {target_sdk}.",
            )
        )

    return findings


# Substrings that indicate a committed secret in a Gradle/properties file.
_SECRET_MARKERS: tuple[str, ...] = (
    "storepassword",
    "keypassword",
    "api_key",
    "apikey",
    "secret",
    "-----begin",
)


def check_release_config(
    release: Mapping[str, object],
    *,
    gradle_texts: Iterable[str] = (),
) -> list[Finding]:
    """Check the release build type and Gradle files for release-safety issues.

    ``release`` describes the release build type, e.g.
    ``{"minifyEnabled": True, "shrinkResources": True, "usesDebugSigning": False}``.
    ``gradle_texts`` are the raw contents of build.gradle(.kts)/gradle.properties
    scanned for committed secrets.
    """
    findings: list[Finding] = []

    if release.get("minifyEnabled") is not True:
        findings.append(
            Finding(
                Severity.WARNING,
                "release-not-minified",
                "Release build has minifyEnabled=false — no R8 code shrinking/"
                "optimization/obfuscation. Enable it (with keep rules) to reduce "
                "size and protect code; upload mapping.txt for deobfuscation.",
            )
        )
    elif release.get("shrinkResources") is not True:
        findings.append(
            Finding(
                Severity.INFO,
                "release-resources-not-shrunk",
                "Release has minifyEnabled=true but shrinkResources=false — enable "
                "resource shrinking to remove unused resources.",
            )
        )

    if release.get("usesDebugSigning") is True:
        findings.append(
            Finding(
                Severity.ERROR,
                "release-debug-signing",
                "Release build uses the debug signing config. Configure a release "
                "signingConfig (secrets from a git-ignored keystore.properties / "
                "CI), not the debug keystore.",
            )
        )

    for text in gradle_texts:
        lowered = text.lower()
        for marker in _SECRET_MARKERS:
            if marker in lowered and "system.getenv" not in lowered.replace(" ", ""):
                findings.append(
                    Finding(
                        Severity.ERROR,
                        "committed-secret",
                        f"A Gradle/properties file appears to contain a hard-coded "
                        f"secret (matched '{marker}'). Move secrets to a git-ignored "
                        f"keystore.properties / environment variables / CI secret "
                        f"store and never commit them.",
                    )
                )
                break

    return findings
