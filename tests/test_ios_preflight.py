"""Tests for the sdlc-team-ios pre-flight checks.

Covers the pure check functions (usage descriptions, export compliance,
privacy manifest, entitlements) and the CLI's source-scanning heuristics.
Encodes the real incidents the checks exist to catch — notably the CoreMotion
/ NSMotionUsageDescription rejection (ITMS-90683).
"""

import plistlib
from pathlib import Path

from sdlc_team_ios_scripts.ios_preflight.checks import (
    Severity,
    check_entitlements,
    check_export_compliance,
    check_privacy_manifest,
    check_usage_descriptions,
)
from sdlc_team_ios_scripts.ios_preflight.cli import (
    build_parser,
    detect_required_reason_apis,
    detect_third_party_sdks,
    detect_used_frameworks,
    run,
)

REAL_MOTION_STRING = "We use motion data to count your steps during a workout."


def _codes(findings):
    return {f.code for f in findings}


# --- check_usage_descriptions -------------------------------------------------


def test_coremotion_without_motion_string_is_error():
    """The ITMS-90683 case: CoreMotion used, no NSMotionUsageDescription."""
    findings = check_usage_descriptions({}, ["CoreMotion"])
    assert any(
        f.severity is Severity.ERROR and f.code == "missing-usage-description"
        for f in findings
    )
    assert any("NSMotionUsageDescription" in f.message for f in findings)


def test_coremotion_with_real_string_passes():
    plist = {"NSMotionUsageDescription": REAL_MOTION_STRING}
    findings = check_usage_descriptions(plist, ["CoreMotion"])
    assert findings == []


def test_placeholder_usage_string_is_warning():
    plist = {"NSMotionUsageDescription": "TODO"}
    findings = check_usage_descriptions(plist, ["CoreMotion"])
    assert _codes(findings) == {"placeholder-usage-description"}
    assert findings[0].severity is Severity.WARNING


def test_short_single_word_string_is_placeholder():
    plist = {"NSCameraUsageDescription": "Camera"}
    findings = check_usage_descriptions(plist, ["AVFoundation"])
    assert _codes(findings) == {"placeholder-usage-description"}


def test_framework_not_in_map_is_ignored():
    findings = check_usage_descriptions({}, ["SwiftUI", "Combine"])
    assert findings == []


def test_case_insensitive_framework_match():
    findings = check_usage_descriptions({}, ["coremotion"])
    assert _codes(findings) == {"missing-usage-description"}


def test_present_but_placeholder_key_without_detected_framework():
    """A placeholder purpose string is flagged even if we didn't detect its framework."""
    plist = {"NSContactsUsageDescription": "your usage description here"}
    findings = check_usage_descriptions(plist, [])
    assert _codes(findings) == {"placeholder-usage-description"}


# --- check_export_compliance --------------------------------------------------


def test_missing_export_compliance_warns():
    findings = check_export_compliance({})
    assert _codes(findings) == {"missing-export-compliance"}
    assert findings[0].severity is Severity.WARNING


def test_export_compliance_false_passes():
    assert check_export_compliance({"ITSAppUsesNonExemptEncryption": False}) == []


def test_export_compliance_true_passes():
    assert check_export_compliance({"ITSAppUsesNonExemptEncryption": True}) == []


def test_export_compliance_wrong_type_warns():
    findings = check_export_compliance({"ITSAppUsesNonExemptEncryption": "false"})
    assert _codes(findings) == {"invalid-export-compliance"}


# --- check_privacy_manifest ---------------------------------------------------


def test_missing_manifest_with_required_reason_api_is_error():
    findings = check_privacy_manifest(
        False, uses_required_reason_apis=True, bundles_third_party_sdks=False
    )
    assert any(f.severity is Severity.ERROR for f in findings)
    assert _codes(findings) == {"missing-privacy-manifest"}


def test_missing_manifest_with_sdks_is_error():
    findings = check_privacy_manifest(
        False, uses_required_reason_apis=False, bundles_third_party_sdks=True
    )
    assert _codes(findings) == {"missing-privacy-manifest"}


def test_missing_manifest_without_triggers_is_info():
    findings = check_privacy_manifest(
        False, uses_required_reason_apis=False, bundles_third_party_sdks=False
    )
    assert _codes(findings) == {"no-privacy-manifest"}
    assert findings[0].severity is Severity.INFO


def test_present_manifest_passes():
    findings = check_privacy_manifest(
        True, uses_required_reason_apis=True, bundles_third_party_sdks=True
    )
    assert findings == []


# --- check_entitlements -------------------------------------------------------


def test_get_task_allow_in_release_is_error():
    findings = check_entitlements({"get-task-allow": True}, is_release=True)
    assert _codes(findings) == {"get-task-allow-in-release"}
    assert findings[0].severity is Severity.ERROR


def test_get_task_allow_in_debug_is_fine():
    assert check_entitlements({"get-task-allow": True}, is_release=False) == []


def test_push_without_aps_environment_is_error():
    findings = check_entitlements({}, is_release=True, uses_push=True)
    assert _codes(findings) == {"missing-aps-environment"}


def test_push_development_aps_in_release_warns():
    findings = check_entitlements(
        {"aps-environment": "development"}, is_release=True, uses_push=True
    )
    assert _codes(findings) == {"aps-environment-not-production"}


def test_push_production_aps_passes():
    findings = check_entitlements(
        {"aps-environment": "production"}, is_release=True, uses_push=True
    )
    assert findings == []


# --- CLI source-scanning heuristics ------------------------------------------


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_detect_used_frameworks_swift_import(tmp_path):
    _write(
        tmp_path / "Sources" / "Pedometer.swift", "import CoreMotion\nimport SwiftUI\n"
    )
    found = {f.lower() for f in detect_used_frameworks(tmp_path)}
    assert "coremotion" in found
    assert "swiftui" not in found  # not a sensitive-framework key


def test_detect_used_frameworks_objc_import(tmp_path):
    _write(tmp_path / "Cam.m", "#import <AVFoundation/AVFoundation.h>\n")
    found = {f.lower() for f in detect_used_frameworks(tmp_path)}
    assert "avfoundation" in found


def test_detect_required_reason_apis(tmp_path):
    _write(tmp_path / "Store.swift", "let d = UserDefaults.standard\n")
    assert detect_required_reason_apis(tmp_path) is True


def test_detect_required_reason_apis_absent(tmp_path):
    _write(
        tmp_path / "View.swift",
        'import SwiftUI\nstruct V: View { var body: some View { Text("hi") } }\n',
    )
    assert detect_required_reason_apis(tmp_path) is False


def test_detect_third_party_sdks_via_podfile(tmp_path):
    _write(tmp_path / "Podfile", "pod 'Firebase'\n")
    assert detect_third_party_sdks(tmp_path) is True


def test_detect_third_party_sdks_absent(tmp_path):
    _write(tmp_path / "App.swift", "import SwiftUI\n")
    assert detect_third_party_sdks(tmp_path) is False


# --- CLI end-to-end run -------------------------------------------------------


def test_run_end_to_end_flags_missing_motion_string(tmp_path):
    """A project using CoreMotion with no motion string and no export key."""
    _write(tmp_path / "App" / "Steps.swift", "import CoreMotion\n")
    info = tmp_path / "App" / "Info.plist"
    with info.open("wb") as handle:
        plistlib.dump({"CFBundleIdentifier": "com.acme.app"}, handle)

    args = build_parser().parse_args([str(tmp_path)])
    findings = run(args)
    codes = _codes(findings)
    assert "missing-usage-description" in codes  # CoreMotion / motion string
    assert "missing-export-compliance" in codes  # no ITSAppUsesNonExemptEncryption


def test_run_clean_project_has_no_errors(tmp_path):
    """A well-configured project yields no ERROR findings."""
    _write(tmp_path / "App" / "View.swift", "import SwiftUI\n")
    info = tmp_path / "App" / "Info.plist"
    with info.open("wb") as handle:
        plistlib.dump({"ITSAppUsesNonExemptEncryption": False}, handle)
    args = build_parser().parse_args([str(tmp_path)])
    findings = run(args)
    assert [f for f in findings if f.severity is Severity.ERROR] == []
