"""iOS TestFlight / App Store pre-flight checks (sdlc-team-ios).

Static checks that catch the configuration mistakes that most often block a
TestFlight upload or App Store / Beta App Review — encoded from real rejection
incidents (e.g. ITMS-90683: a CoreMotion build rejected for a missing
``NSMotionUsageDescription``). Pure functions operate on already-parsed plist
dictionaries so they are trivially testable; thin loaders and a CLI wrap them.

Public API:
- ``Finding`` / ``Severity`` — a single check result.
- ``check_usage_descriptions`` — sensitive frameworks in use must have their
  ``NS…UsageDescription`` purpose string, and it must read like a real sentence.
- ``check_export_compliance`` — ``ITSAppUsesNonExemptEncryption`` should be set
  so every upload skips the export-compliance questionnaire.
- ``check_privacy_manifest`` — a ``PrivacyInfo.xcprivacy`` manifest must exist
  when required-reason APIs or third-party SDKs are present.
- ``check_entitlements`` — release builds must not carry ``get-task-allow`` and
  push builds must use the production APNs environment.
- ``FRAMEWORK_USAGE_KEYS`` — the framework/symbol → Info.plist key mapping.
"""

from .checks import (
    FRAMEWORK_USAGE_KEYS,
    Finding,
    Severity,
    check_entitlements,
    check_export_compliance,
    check_privacy_manifest,
    check_usage_descriptions,
)

__all__ = [
    "FRAMEWORK_USAGE_KEYS",
    "Finding",
    "Severity",
    "check_entitlements",
    "check_export_compliance",
    "check_privacy_manifest",
    "check_usage_descriptions",
]
