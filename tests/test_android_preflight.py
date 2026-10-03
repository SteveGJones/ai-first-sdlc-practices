"""Tests for the sdlc-team-android pre-flight checks.

Covers the pure check functions (manifest hygiene, SDK policy, release config)
and the CLI's manifest/Gradle parsing heuristics. Encodes the real Play blockers
the checks exist to catch (background location, target-API mandate, debug-signed
release, committed secrets).
"""

import xml.etree.ElementTree as ET
from pathlib import Path

from sdlc_team_android_scripts.android_preflight.checks import (
    Component,
    Finding,
    Severity,
    check_manifest,
    check_release_config,
    check_sdk_policy,
)
from sdlc_team_android_scripts.android_preflight.cli import (
    build_parser,
    parse_gradle,
    parse_manifest,
    run,
)


def _codes(findings: list[Finding]) -> set[str]:
    return {f.code for f in findings}


# --- check_manifest -----------------------------------------------------------


def test_background_location_is_error() -> None:
    findings = check_manifest(["android.permission.ACCESS_BACKGROUND_LOCATION"])
    assert any(
        f.severity is Severity.ERROR and f.code == "sensitive-permission"
        for f in findings
    )


def test_background_location_justified_passes() -> None:
    findings = check_manifest(
        ["android.permission.ACCESS_BACKGROUND_LOCATION"],
        justified_permissions=["android.permission.ACCESS_BACKGROUND_LOCATION"],
    )
    assert findings == []


def test_other_sensitive_permission_is_warning() -> None:
    findings = check_manifest(["android.permission.CAMERA"])
    assert _codes(findings) == {"sensitive-permission"}
    assert findings[0].severity is Severity.WARNING


def test_normal_permission_ignored() -> None:
    findings = check_manifest(["android.permission.INTERNET"])
    assert findings == []


def test_exported_component_without_guard_is_error() -> None:
    findings = check_manifest(
        [],
        components=[Component(name=".Deep", exported=True)],
    )
    assert _codes(findings) == {"exported-component-unguarded"}


def test_exported_component_with_intent_filter_ok() -> None:
    findings = check_manifest(
        [],
        components=[Component(name=".Main", exported=True, has_intent_filter=True)],
    )
    assert findings == []


def test_non_exported_component_ok() -> None:
    findings = check_manifest(
        [], components=[Component(name=".Internal", exported=False)]
    )
    assert findings == []


def test_debuggable_release_is_error() -> None:
    findings = check_manifest([], debuggable=True)
    assert _codes(findings) == {"debuggable-release"}


def test_cleartext_traffic_is_warning() -> None:
    findings = check_manifest([], uses_cleartext_traffic=True)
    assert _codes(findings) == {"cleartext-traffic"}


# --- check_sdk_policy ---------------------------------------------------------


def test_target_below_play_minimum_is_error() -> None:
    findings = check_sdk_policy(target_sdk=33, play_min_target=35)
    assert _codes(findings) == {"target-sdk-too-low"}
    assert findings[0].severity is Severity.ERROR


def test_target_meets_minimum_passes() -> None:
    findings = check_sdk_policy(
        target_sdk=35, min_sdk=24, compile_sdk=35, play_min_target=35
    )
    assert findings == []


def test_compile_below_target_is_error() -> None:
    findings = check_sdk_policy(target_sdk=35, compile_sdk=34, play_min_target=35)
    assert _codes(findings) == {"compile-sdk-below-target"}


def test_min_above_target_is_error() -> None:
    findings = check_sdk_policy(target_sdk=30, min_sdk=31, play_min_target=30)
    assert _codes(findings) == {"min-sdk-above-target"}


def test_missing_target_sdk_warns() -> None:
    findings = check_sdk_policy(target_sdk=None, play_min_target=35)
    assert _codes(findings) == {"missing-target-sdk"}


# --- check_release_config -----------------------------------------------------


def test_release_not_minified_warns() -> None:
    findings = check_release_config({"minifyEnabled": False})
    assert _codes(findings) == {"release-not-minified"}


def test_release_debug_signing_is_error() -> None:
    findings = check_release_config(
        {"minifyEnabled": True, "shrinkResources": True, "usesDebugSigning": True}
    )
    assert _codes(findings) == {"release-debug-signing"}


def test_release_minified_no_shrink_is_info() -> None:
    findings = check_release_config({"minifyEnabled": True, "shrinkResources": False})
    assert _codes(findings) == {"release-resources-not-shrunk"}


def test_committed_secret_is_error() -> None:
    # A committed private key (PEM header) is a classic leaked secret.
    findings = check_release_config(
        {"minifyEnabled": True, "shrinkResources": True},
        gradle_texts=["-----BEGIN OPENSSH PRIVATE KEY-----\nAAAA\n"],
    )
    assert _codes(findings) == {"committed-secret"}


def test_secret_from_env_ok() -> None:
    findings = check_release_config(
        {"minifyEnabled": True, "shrinkResources": True},
        gradle_texts=['storePassword = System.getenv("KSTOREPWD")'],
    )
    assert findings == []


def test_clean_release_config_passes() -> None:
    findings = check_release_config(
        {"minifyEnabled": True, "shrinkResources": True, "usesDebugSigning": False}
    )
    assert findings == []


# --- CLI parsing --------------------------------------------------------------


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


MANIFEST = """<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    <uses-permission android:name="android.permission.ACCESS_BACKGROUND_LOCATION"/>
    <uses-permission android:name="android.permission.INTERNET"/>
    <application android:debuggable="false" android:allowBackup="true">
        <activity android:name=".MainActivity" android:exported="true">
            <intent-filter><action android:name="android.intent.action.MAIN"/></intent-filter>
        </activity>
        <receiver android:name=".SecretReceiver" android:exported="true"/>
    </application>
</manifest>
"""


def test_parse_manifest(tmp_path: Path) -> None:
    p = tmp_path / "AndroidManifest.xml"
    _write(p, MANIFEST)
    parsed = parse_manifest(p)
    assert "android.permission.ACCESS_BACKGROUND_LOCATION" in parsed["permissions"]
    assert parsed["allow_backup"] is True
    names = {c.name: c for c in parsed["components"]}
    assert names[".MainActivity"].has_intent_filter is True
    assert names[".SecretReceiver"].exported is True
    assert names[".SecretReceiver"].has_intent_filter is False


def test_parse_gradle_kts(tmp_path: Path) -> None:
    _write(
        tmp_path / "app" / "build.gradle.kts",
        """android {
    compileSdk = 35
    defaultConfig { minSdk = 24; targetSdk = 33 }
    buildTypes { getByName("release") { isMinifyEnabled = true; isShrinkResources = true } }
}""",
    )
    g = parse_gradle(tmp_path)
    assert g["sdk"]["target_sdk"] == 33
    assert g["sdk"]["compile_sdk"] == 35
    assert g["release"]["minifyEnabled"] is True


def test_run_end_to_end_flags_blockers(tmp_path: Path) -> None:
    """A project with background location, low targetSdk, and an unguarded receiver."""
    _write(tmp_path / "app" / "src" / "main" / "AndroidManifest.xml", MANIFEST)
    _write(
        tmp_path / "app" / "build.gradle.kts",
        "android { compileSdk = 35\n defaultConfig { targetSdk = 33 } }",
    )
    args = build_parser().parse_args([str(tmp_path), "--play-min-target", "35"])
    codes = _codes(run(args))
    assert "sensitive-permission" in codes  # background location
    assert "target-sdk-too-low" in codes  # 33 < 35
    assert "exported-component-unguarded" in codes  # SecretReceiver


def test_run_clean_project_no_errors(tmp_path: Path) -> None:
    _write(
        tmp_path / "app" / "src" / "main" / "AndroidManifest.xml",
        '<?xml version="1.0"?><manifest xmlns:android="http://schemas.android.com/apk/res/android">'
        '<uses-permission android:name="android.permission.INTERNET"/>'
        "<application/></manifest>",
    )
    _write(
        tmp_path / "app" / "build.gradle.kts",
        "android { compileSdk = 35\n defaultConfig { minSdk = 24; targetSdk = 35 }\n"
        ' buildTypes { getByName("release") { isMinifyEnabled = true; isShrinkResources = true } } }',
    )
    args = build_parser().parse_args([str(tmp_path), "--play-min-target", "35"])
    errors = [f for f in run(args) if f.severity is Severity.ERROR]
    assert errors == []


def test_manifest_parse_survives_bad_xml(tmp_path: Path) -> None:
    p = tmp_path / "AndroidManifest.xml"
    _write(p, "<manifest not-valid")
    assert parse_manifest(p)["permissions"] == []


def test_xml_import_available() -> None:
    # Guard: the CLI relies on ElementTree; confirm the module is importable here.
    assert ET.Element is not None
