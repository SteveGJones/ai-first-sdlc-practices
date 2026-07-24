"""Android Play Store / release pre-flight checks (sdlc-team-android).

Static checks that catch the configuration mistakes that most often block a
Play submission or cause a release-quality incident — encoded from Google's
Play policy and release guidance. Pure functions operate on already-parsed
inputs (manifest permission/attribute data, SDK-level values, release-config
flags) so they are trivially testable; thin loaders and a CLI wrap them.

Public API:
- ``Finding`` / ``Severity`` — a single check result.
- ``check_manifest`` — dangerous permissions need justification; exported
  components need a permission or intent-filter; no cleartext/debuggable in
  release.
- ``check_sdk_policy`` — targetSdk meets the Play minimum and is consistent
  with compileSdk/minSdk.
- ``check_release_config`` — release builds shrink code (R8), don't use a debug
  signing config, and don't commit secrets.
"""

from .checks import (
    DANGEROUS_PERMISSIONS,
    Finding,
    Severity,
    check_manifest,
    check_release_config,
    check_sdk_policy,
)

__all__ = [
    "DANGEROUS_PERMISSIONS",
    "Finding",
    "Severity",
    "check_manifest",
    "check_release_config",
    "check_sdk_policy",
]
