#!/usr/bin/env bash
# Lint suite for scripts/adapters/*/{adapter.json,adapter.sh} (issue #232,
# migration step 4 — see docs/superpowers/specs/
# 2026-07-24-sdlc-simple-orchestration-design.md §2, §4). Two things are
# checked per adapter directory:
#   1. adapter.json satisfies the §2.1 descriptor schema (schema_version,
#      id grammar, kind, all three postures with mechanism+fidelity+
#      native, and the required capability keys).
#   2. adapter.sh, once sourced, defines every REQUIRED §2.2 ABI function
#      (adapter_check_identity_drift is optional and not checked here).
#
# No mock CLI is invoked and no extdel.sh subcommand is run — this is a
# static lint over the adapter directories themselves, so it never spends
# API quota and needs no PATH/HOME fixtures.
#
# Run: bash plugins/sdlc-simple-orchestration/tests/test-adapter-descriptors.sh

set -u

THIS_DIR="$(cd "$(dirname "$0")" && pwd -P)"
PLUGIN_ROOT="$(cd "$THIS_DIR/.." && pwd -P)"
ADAPTERS_DIR="$PLUGIN_ROOT/scripts/adapters"

PASS=0
FAIL=0

pass() { PASS=$((PASS + 1)); printf 'PASS: %s\n' "$1"; }
fail() { FAIL=$((FAIL + 1)); printf 'FAIL: %s\n' "$1"; }

REQUIRED_CAPABILITY_KEYS="one_shot session_resume held_process per_action_approval fanout_safe model_select effort_select answer_file_native"
REQUIRED_POSTURES="read-only workspace dangerous"
REQUIRED_ABI_FUNCTIONS="adapter_detect adapter_preflight adapter_posture_args adapter_submit_turn adapter_capture_session_id adapter_files_changed_summary adapter_permission_hint_pattern"

echo "=== adapter descriptor + ABI lint suite ==="
echo "ADAPTERS_DIR=$ADAPTERS_DIR"
echo

if [ ! -d "$ADAPTERS_DIR" ]; then
  fail "adapters directory does not exist: $ADAPTERS_DIR"
  echo
  echo "=== Results: $PASS passed, $FAIL failed ==="
  [ "$FAIL" -eq 0 ]
  exit $?
fi

found_any=0

for adir in "$ADAPTERS_DIR"/*/; do
  [ -d "$adir" ] || continue
  adir="${adir%/}"
  id="$(basename "$adir")"
  found_any=1
  dj="$adir/adapter.json"
  ds="$adir/adapter.sh"

  echo "--- adapter: $id ---"

  if [ ! -f "$dj" ]; then
    fail "$id: adapter.json missing"
    continue
  fi
  if ! jq -e . "$dj" >/dev/null 2>&1; then
    fail "$id: adapter.json is not valid JSON"
    continue
  fi
  pass "$id: adapter.json parses as JSON"

  # 1. schema_version==1
  if [ "$(jq -r '.schema_version // empty' "$dj" 2>/dev/null)" = "1" ]; then
    pass "$id: schema_version == 1"
  else
    fail "$id: schema_version is not 1"
  fi

  # 2. id present, matches the file's own directory name, and matches the
  #    handle/adapter-dir grammar ^[a-z][a-z0-9]*$ (no hyphens —
  #    validate_handle in extdel.sh splits handles on '-').
  json_id=$(jq -r '.id // empty' "$dj" 2>/dev/null)
  if [ -z "$json_id" ]; then
    fail "$id: .id is missing"
  elif ! printf '%s' "$json_id" | grep -Eq '^[a-z][a-z0-9]*$'; then
    fail "$id: .id ('$json_id') does not match ^[a-z][a-z0-9]*\$"
  elif [ "$json_id" != "$id" ]; then
    fail "$id: .id ('$json_id') does not match its directory name"
  else
    pass "$id: .id present and matches grammar ^[a-z][a-z0-9]*\$"
  fi

  # 3. kind present
  kind=$(jq -r '.kind // empty' "$dj" 2>/dev/null)
  if [ -n "$kind" ]; then
    pass "$id: .kind present ('$kind')"
  else
    fail "$id: .kind is missing"
  fi

  # 4. all three postures present, each with mechanism+fidelity+native
  posture_ok=1
  for p in $REQUIRED_POSTURES; do
    if ! jq -e --arg p "$p" '.postures[$p]' "$dj" >/dev/null 2>&1; then
      fail "$id: postures.$p is missing"
      posture_ok=0
      continue
    fi
    for field in mechanism fidelity native; do
      if ! jq -e --arg p "$p" --arg f "$field" '.postures[$p][$f] // empty | length > 0' "$dj" >/dev/null 2>&1; then
        fail "$id: postures.$p.$field is missing or empty"
        posture_ok=0
      fi
    done
  done
  [ "$posture_ok" -eq 1 ] && pass "$id: all three postures present with mechanism+fidelity+native"

  # 5. required capability keys present (booleans; presence is what's
  #    checked, not a specific value — different backends legitimately
  #    differ, e.g. agy's answer_file_native:false vs codex's true).
  cap_ok=1
  for k in $REQUIRED_CAPABILITY_KEYS; do
    if ! jq -e --arg k "$k" '.capabilities | has($k)' "$dj" >/dev/null 2>&1; then
      fail "$id: capabilities.$k is missing"
      cap_ok=0
    fi
  done
  [ "$cap_ok" -eq 1 ] && pass "$id: all required capability keys present"

  # 6. sibling_plugins, if present, has a non-empty plugin_match and a
  #    valid relationship value (advisory-only field, but a malformed one
  #    would silently break list-backends' sibling column).
  if jq -e '.sibling_plugins // empty | length > 0' "$dj" >/dev/null 2>&1; then
    sm=$(jq -r '.sibling_plugins[0].plugin_match // empty' "$dj" 2>/dev/null)
    rel=$(jq -r '.sibling_plugins[0].relationship // empty' "$dj" 2>/dev/null)
    if [ -n "$sm" ]; then
      pass "$id: sibling_plugins[0].plugin_match present ('$sm')"
    else
      fail "$id: sibling_plugins[0].plugin_match is missing/empty"
    fi
    case "$rel" in
      prefer-for|coexist|superseded-by-us) pass "$id: sibling_plugins[0].relationship is valid ('$rel')" ;;
      *) fail "$id: sibling_plugins[0].relationship ('$rel') is not one of prefer-for|coexist|superseded-by-us" ;;
    esac
  fi

  # 7. adapter.sh exists, is syntactically valid, and (once sourced in a
  #    throwaway subshell) defines every required ABI function.
  if [ ! -f "$ds" ]; then
    fail "$id: adapter.sh missing"
    continue
  fi
  if bash -n "$ds" 2>/dev/null; then
    pass "$id: adapter.sh passes bash -n"
  else
    fail "$id: adapter.sh fails bash -n"
    continue
  fi

  # Source in a subshell that just reports which required functions are
  # (not) defined — avoids polluting THIS test script's own function
  # namespace across adapters, and needs no engine helpers since we only
  # check `type -t`, never call the functions.
  missing=$(
    # shellcheck disable=SC1090
    . "$ds"
    m=""
    for fn in $REQUIRED_ABI_FUNCTIONS; do
      [ "$(type -t "$fn" 2>/dev/null)" = "function" ] || m="$m $fn"
    done
    printf '%s' "$m"
  )
  if [ -z "$missing" ]; then
    pass "$id: adapter.sh defines all required ABI functions ($REQUIRED_ABI_FUNCTIONS)"
  else
    fail "$id: adapter.sh is missing ABI function(s):$missing"
  fi

  echo
done

if [ "$found_any" -eq 0 ]; then
  fail "no adapter directories found under $ADAPTERS_DIR"
fi

echo "=== Results: $PASS passed, $FAIL failed ==="
[ "$FAIL" -eq 0 ]
