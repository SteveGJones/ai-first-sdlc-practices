"""Pure pre-flight check functions for iOS TestFlight / App Store submission.

Each check takes already-parsed data (plist dicts, detected framework names)
and returns a list of :class:`Finding`. No file or network I/O here so the rules
are deterministic and unit-testable; loading/CLI lives in ``cli.py``.

The rules encode real upload/review blockers:
- Missing purpose strings for sensitive frameworks (ITMS-90683 class).
- Placeholder purpose strings (Apple rejects non-human text).
- Missing ``ITSAppUsesNonExemptEncryption`` (stalls every upload on the
  export-compliance questionnaire).
- Missing privacy manifest when required-reason APIs / SDKs are present.
- ``get-task-allow`` in a release build; sandbox APNs in a push build.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import Enum


class Severity(str, Enum):
    """Severity of a pre-flight finding."""

    ERROR = "error"  # will block upload or review
    WARNING = "warning"  # likely to cause friction / a stalled upload
    INFO = "info"  # advisory / good-practice


@dataclass(frozen=True)
class Finding:
    """A single pre-flight check result."""

    severity: Severity
    code: str
    message: str

    def __str__(self) -> str:
        return f"[{self.severity.value.upper()}] {self.code}: {self.message}"


# Sensitive frameworks / API symbols → the Info.plist purpose-string key that
# must be present when they are used. Keyed by a lowercase framework/module name
# that a source scan can detect (import CoreMotion, <CoreMotion/...>, etc.).
# Sourced from Apple's "protected resources" list; the CoreMotion entry is the
# one this project was bitten by (ITMS-90683).
FRAMEWORK_USAGE_KEYS: dict[str, str] = {
    "coremotion": "NSMotionUsageDescription",
    "corelocation": "NSLocationWhenInUseUsageDescription",
    "avfoundation": "NSCameraUsageDescription",
    "photos": "NSPhotoLibraryUsageDescription",
    "photosui": "NSPhotoLibraryUsageDescription",
    "contacts": "NSContactsUsageDescription",
    "contactsui": "NSContactsUsageDescription",
    "eventkit": "NSCalendarsUsageDescription",
    "speech": "NSSpeechRecognitionUsageDescription",
    "healthkit": "NSHealthShareUsageDescription",
    "homekit": "NSHomeKitUsageDescription",
    "corebluetooth": "NSBluetoothAlwaysUsageDescription",
    "usernotifications": "NSUserNotificationsUsageDescription",
    "localauthentication": "NSFaceIDUsageDescription",
    "apptrackingtransparency": "NSUserTrackingUsageDescription",
    "mediaplayer": "NSAppleMusicUsageDescription",
}

# Substrings that mark a purpose string as placeholder / non-human. Apple rejects
# these. Compared case-insensitively against a stripped, collapsed string.
_PLACEHOLDER_MARKERS: tuple[str, ...] = (
    "todo",
    "tbd",
    "fixme",
    "xxx",
    "placeholder",
    "your usage description",
    "usage description here",
    "description here",
    "lorem ipsum",
    "asdf",
    "test",
)

# A real purpose string should be at least this many characters and contain a
# space (i.e. more than one word). Apple wants a human sentence explaining why.
_MIN_PURPOSE_LEN = 12


def _is_placeholder_purpose(value: object) -> bool:
    """True if ``value`` is missing, too short, or looks like placeholder text."""
    if not isinstance(value, str):
        return True
    collapsed = " ".join(value.split())
    if len(collapsed) < _MIN_PURPOSE_LEN or " " not in collapsed:
        return True
    lowered = collapsed.lower()
    return any(marker in lowered for marker in _PLACEHOLDER_MARKERS)


def check_usage_descriptions(
    info_plist: Mapping[str, object],
    used_frameworks: Iterable[str],
) -> list[Finding]:
    """Check purpose strings for the sensitive frameworks the app uses.

    ``used_frameworks`` is a collection of detected framework/module names
    (case-insensitive; e.g. ``{"CoreMotion", "AVFoundation"}``). For each one
    that maps to a required Info.plist key, a missing key is an ERROR (the
    ITMS-90683 class of processing rejection) and a placeholder string is a
    WARNING. Any usage-description key already present in the plist is also
    checked for placeholder text.
    """
    findings: list[Finding] = []
    seen_keys: set[str] = set()

    for framework in used_frameworks:
        key = FRAMEWORK_USAGE_KEYS.get(framework.strip().lower())
        if key is None:
            continue
        seen_keys.add(key)
        if key not in info_plist:
            findings.append(
                Finding(
                    Severity.ERROR,
                    "missing-usage-description",
                    f"{framework} is used but Info.plist has no {key}. "
                    f"App Store Connect will reject the build in processing "
                    f"(ITMS-90683 class). Add a human-readable {key}.",
                )
            )
        elif _is_placeholder_purpose(info_plist[key]):
            findings.append(
                Finding(
                    Severity.WARNING,
                    "placeholder-usage-description",
                    f"{key} looks like placeholder text; Apple rejects "
                    f"non-descriptive purpose strings. Write a real sentence "
                    f"explaining why {framework} is used.",
                )
            )

    # Also flag placeholder text in any usage-description key already present,
    # even if we did not detect the corresponding framework.
    for key, value in info_plist.items():
        if not (isinstance(key, str) and key.endswith("UsageDescription")):
            continue
        if key in seen_keys:
            continue
        if _is_placeholder_purpose(value):
            findings.append(
                Finding(
                    Severity.WARNING,
                    "placeholder-usage-description",
                    f"{key} looks like placeholder text; replace it with a "
                    f"human-readable sentence before submitting.",
                )
            )

    return findings


def check_export_compliance(info_plist: Mapping[str, object]) -> list[Finding]:
    """Check the export-compliance key that gates every upload.

    Setting ``ITSAppUsesNonExemptEncryption = false`` (for apps using only
    standard/exempt encryption such as HTTPS) makes each upload skip the
    export-compliance questionnaire in App Store Connect. Its absence is a
    WARNING because every single build otherwise stalls waiting for an answer.
    """
    key = "ITSAppUsesNonExemptEncryption"
    if key not in info_plist:
        return [
            Finding(
                Severity.WARNING,
                "missing-export-compliance",
                f"Info.plist has no {key}. Every TestFlight/App Store upload "
                f"will stall on the export-compliance questionnaire. If the app "
                f"uses only exempt encryption (e.g. standard HTTPS), set "
                f"{key} = false to skip it on every upload.",
            )
        ]
    value = info_plist[key]
    if not isinstance(value, bool):
        return [
            Finding(
                Severity.WARNING,
                "invalid-export-compliance",
                f"{key} should be a Boolean (true/false), got {type(value).__name__}.",
            )
        ]
    return []


def check_privacy_manifest(
    manifest_present: bool,
    *,
    uses_required_reason_apis: bool,
    bundles_third_party_sdks: bool,
) -> list[Finding]:
    """Check that a privacy manifest exists when Apple now requires one.

    A ``PrivacyInfo.xcprivacy`` manifest is required when the app uses
    required-reason APIs (UserDefaults, file/disk timestamps, system boot time,
    active keyboard, disk space) or bundles third-party SDKs. Its absence in
    those cases is an ERROR (Apple flags such builds at upload).
    """
    if manifest_present:
        return []
    if uses_required_reason_apis or bundles_third_party_sdks:
        reason = []
        if uses_required_reason_apis:
            reason.append("required-reason APIs are used")
        if bundles_third_party_sdks:
            reason.append("third-party SDKs are bundled")
        return [
            Finding(
                Severity.ERROR,
                "missing-privacy-manifest",
                "No PrivacyInfo.xcprivacy manifest, but "
                + " and ".join(reason)
                + ". Add a privacy manifest declaring tracking, tracking "
                "domains, collected data types, and required-reason API usage.",
            )
        ]
    return [
        Finding(
            Severity.INFO,
            "no-privacy-manifest",
            "No PrivacyInfo.xcprivacy manifest found. Not required if you use "
            "no required-reason APIs and bundle no third-party SDKs, but "
            "double-check — this requirement is easy to miss.",
        )
    ]


def check_entitlements(
    entitlements: Mapping[str, object],
    *,
    is_release: bool,
    uses_push: bool = False,
) -> list[Finding]:
    """Check distribution-build entitlement invariants.

    - ``get-task-allow`` must be absent/false in a release (distribution) build;
      its presence is the classic "Invalid Provisioning Profile" upload
      rejection.
    - When push is used, ``aps-environment`` must be ``production`` for
      App Store / TestFlight builds (a ``development`` value is why "push works
      in debug but not TestFlight").
    """
    findings: list[Finding] = []

    if is_release and entitlements.get("get-task-allow") is True:
        findings.append(
            Finding(
                Severity.ERROR,
                "get-task-allow-in-release",
                "get-task-allow is true in a release build. App Store upload "
                "validation rejects this — archive with the Release "
                "configuration and an App Store distribution profile, not a "
                "development profile.",
            )
        )

    if uses_push:
        aps = entitlements.get("aps-environment")
        if aps is None:
            findings.append(
                Finding(
                    Severity.ERROR,
                    "missing-aps-environment",
                    "Push is used but aps-environment is not set in the "
                    "entitlements. Enable the Push Notifications capability.",
                )
            )
        elif is_release and aps != "production":
            findings.append(
                Finding(
                    Severity.WARNING,
                    "aps-environment-not-production",
                    f"aps-environment is '{aps}' in a release build. "
                    f"App Store/TestFlight use production APNs — a development "
                    f"value is why push 'works in debug but not TestFlight'.",
                )
            )

    return findings
