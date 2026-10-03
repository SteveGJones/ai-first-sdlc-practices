#!/usr/bin/env python3
"""score/command-diff.py — execute-and-diff scorer for the command-exec
dimension (issue #235; design
docs/superpowers/specs/2026-07-26-council-tool-use-assessment-design.md §4a).

Invocation: command-diff.py <item-dir> <answer-file> <workdir>
Writes <workdir>/score.json {"score":float,"status":str,"details":{...}}.
Always exit 0 (scorer ABI). Stdlib only.

WHY THIS EXISTS. `command-check` scores a proposed command with a regex rubric,
which cannot separate a CORRECT alternative implementation from a
plausible-looking BROKEN one. Measured in the #235 audition on
ce-hard-grep-context: three local models answered with `awk` instead of
`grep -A 3`; Qwen3-Coder-30B-A3B's awk produced byte-identical output to the
golden (a rubric FALSE NEGATIVE) while Qwen2.5-Coder-7B's and Devstral-24B's awk
were genuinely wrong — yet all three scored the same 0.6667. Widening the regex
to admit awk would have turned the two false negatives into false POSITIVES.
Only running the command settles it, so this scorer runs the proposed command in
a throwaway sandbox and compares its stdout against a golden file: score is 1.0
on an exact match, else 0.0. It asserts what the command ACHIEVES, never which
binary achieves it.

SCOPE. Only suitable for items whose inputs are self-contained files (the
sandbox is a copy of the item's inputs/). Items whose correct answer inspects
live machine state (`/var/log`, a listening port) are NOT executable this way
and stay on `command-check`.

SAFETY. Executing model-proposed shell text is the risk this scorer takes on, so
it is gated three ways and is OFF by default:
  1. Opt-in — refuses unless COUNCIL_ALLOW_EXEC=1 is set in the environment
     (status `exec-disabled`). No env var, no execution, ever.
  2. Allowlist — every pipeline segment's leading binary must appear in the
     item's `allow_binaries`. Read-only text tools only; no curl/wget/nc/ssh,
     so there is no egress path. Anything else -> `unsafe-command`, refused
     BEFORE execution.
  3. Shell-metacharacter deny-list — output redirects, command substitution,
     command chaining/backgrounding, and destructive `find` actions are refused
     (`unsafe-command`). A plain `|` pipeline is allowed.
It then runs with cwd set to a per-invocation sandbox holding COPIES of the
item's inputs (so a write can only touch throwaway files), a stripped
environment, and a hard timeout. The item's own inputs are never the cwd.

expected/exec.json:
    {"field": "commands",              # answer field holding the command(s)
     "golden_stdout": "stdout.txt",    # golden file, relative to expected/
     "allow_binaries": ["grep", ...],  # permitted leading binaries
     "timeout_s": 10}                  # per-command wall-clock cap

Statuses: scored | exec-disabled | unsafe-command | timeout | exec-error |
contract-fail | error.
"""

import json
import os
import re
import shutil
import subprocess
import sys

# Shell constructs refused outright. A plain pipe is deliberately NOT here:
# pipelines are idiomatic for these items and every segment is allowlisted.
#
# These are matched against the QUOTE-MASKED command (see mask_quoted), so they
# only ever fire on real shell syntax. That distinction is essential: an awk
# program legitimately contains `;`, `&&` and `>` inside its quoted script
# (`awk '/E/{print; for(i=0;i<3;i++){getline; print}}'`), and matching those as
# shell operators is exactly the over-strictness this scorer exists to remove.
# A redirect INSIDE a quoted awk/sed program can still write, which the
# copies-only sandbox contains.
_DENY_PATTERNS = (
    (r">", "output redirect"),
    (r"<\(", "process substitution"),
    (r"\$\(", "command substitution"),
    (r"`", "backtick command substitution"),
    (r";", "command chaining"),
    (r"&", "backgrounding or chaining"),
    (r"\n", "multi-line command"),
    (r"\bfind\b[^|]*-delete\b", "find -delete"),
    (r"\bfind\b[^|]*-(exec|execdir|ok)\b", "find -exec"),
)


def mask_quoted(command):
    """Return `command` with every single/double-quoted region replaced by
    same-length runs of 'x'. Indices are preserved, so the mask can be searched
    for shell syntax and split into pipeline segments while the original string
    remains available for slicing. Backslash escapes are honoured outside
    quotes."""
    out = []
    quote = None
    escaped = False
    for ch in command:
        if escaped:
            out.append("x")
            escaped = False
            continue
        if quote is None and ch == "\\":
            out.append("x")
            escaped = True
            continue
        if quote is None and ch in ("'", '"'):
            quote = ch
            out.append(ch)
            continue
        if quote is not None and ch == quote:
            quote = None
            out.append(ch)
            continue
        out.append("x" if quote is not None else ch)
    return "".join(out)


def write_score(workdir, score, status, details):
    out_path = os.path.join(workdir, "score.json")
    os.makedirs(workdir, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"score": score, "status": status, "details": details}, f)
        f.write("\n")


def _load_extract_answer():
    """Import the sibling extract_answer module (its parent dir is not on
    sys.path when this scorer runs from the score/ subdirectory)."""
    council_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if council_dir not in sys.path:
        sys.path.insert(0, council_dir)
    import extract_answer

    return extract_answer


def _load_command_check():
    """Import the sibling command-check scorer for the static-rubric fallback.
    Its filename is hyphenated, so it cannot be a plain import."""
    import importlib.util

    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "command-check.py")
    spec = importlib.util.spec_from_file_location("command_check", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def commands_from(value):
    """Normalise the answer field into a list of command strings."""
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, list):
        return [str(v) for v in value if v is not None and str(v).strip()]
    return [str(value)]


def pipeline_segments(command):
    """Split on UNQUOTED `|` only, so a pipe character inside an awk/sed script
    or a grep pattern (`grep -E 'a|b'`) does not create a bogus segment."""
    masked = mask_quoted(command)
    segments = []
    start = 0
    for idx, ch in enumerate(masked):
        if ch == "|":
            segments.append(command[start:idx])
            start = idx + 1
    segments.append(command[start:])
    return segments


def leading_binaries(command):
    """The leading binary of each pipeline segment, with any leading VAR=value
    assignments and `env` skipped."""
    binaries = []
    for segment in pipeline_segments(command):
        tokens = segment.strip().split()
        idx = 0
        while idx < len(tokens) and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", tokens[idx]):
            idx += 1
        if idx < len(tokens) and tokens[idx] == "env":
            idx += 1
            while idx < len(tokens) and re.match(
                r"^[A-Za-z_][A-Za-z0-9_]*=", tokens[idx]
            ):
                idx += 1
        if idx < len(tokens):
            binaries.append(os.path.basename(tokens[idx]))
        else:
            binaries.append("")
    return binaries


def safety_refusal(command, allow_binaries):
    """Returns a refusal reason string, or None when the command is permitted."""
    masked = mask_quoted(command)
    if masked.count("'") % 2 or masked.count('"') % 2:
        return "refused unbalanced quoting: %s" % command
    for pattern, label in _DENY_PATTERNS:
        if re.search(pattern, masked):
            return "refused %s: %s" % (label, command)
    allowed = set(allow_binaries or [])
    for binary in leading_binaries(command):
        if not binary:
            return "refused empty pipeline segment: %s" % command
        if binary not in allowed:
            return "refused non-allowlisted binary '%s': %s" % (binary, command)
    return None


def build_sandbox(item_dir, workdir):
    """A throwaway cwd holding COPIES of the item's inputs, so a stray write can
    never touch the item itself."""
    sandbox = os.path.join(workdir, "sandbox")
    if os.path.isdir(sandbox):
        shutil.rmtree(sandbox)
    os.makedirs(sandbox)
    inputs = os.path.join(item_dir, "inputs")
    if os.path.isdir(inputs):
        for name in os.listdir(inputs):
            src = os.path.join(inputs, name)
            dst = os.path.join(sandbox, name)
            if os.path.isfile(src):
                shutil.copy2(src, dst)
            elif os.path.isdir(src):
                shutil.copytree(src, dst)
    return sandbox


def run_in_sandbox(command, sandbox, timeout_s):
    """Run one command. Returns (stdout, status, detail). Status is "ok",
    "timeout" or "exec-error"."""
    env = {
        "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
        "LC_ALL": "C",
        "LANG": "C",
        "HOME": sandbox,
        "TMPDIR": sandbox,
    }
    try:
        proc = subprocess.run(
            command,
            shell=True,
            cwd=sandbox,
            env=env,
            timeout=timeout_s,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except subprocess.TimeoutExpired:
        return "", "timeout", "exceeded %ss" % timeout_s
    except Exception as exc:
        return "", "exec-error", str(exc)
    stdout = proc.stdout.decode("utf-8", errors="replace")
    return stdout, "ok", "exit %d" % proc.returncode


def normalise(text):
    """Compare on content, not on trailing-newline trivia: drop trailing
    whitespace on each line and ignore trailing blank lines."""
    lines = [line.rstrip() for line in text.replace("\r\n", "\n").split("\n")]
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines)


def main(argv):
    if len(argv) != 4:
        sys.stderr.write("usage: command-diff.py <item-dir> <answer-file> <workdir>\n")
        sys.exit(2)

    item_dir, answer_file, workdir = argv[1], argv[2], argv[3]

    try:
        with open(
            os.path.join(item_dir, "expected", "exec.json"), "r", encoding="utf-8"
        ) as f:
            spec = json.load(f)

        extract_answer = _load_extract_answer()
        with open(answer_file, "r", encoding="utf-8") as f:
            raw = f.read()
        obj = extract_answer.extract_strict_json(raw)
        if obj is None:
            write_score(workdir, 0.0, "contract-fail", {"error": "not-a-json-object"})
            sys.exit(0)

        commands = commands_from(obj.get(spec.get("field", "commands")))
        if not commands:
            write_score(
                workdir, 0.0, "contract-fail", {"error": "no command in answer"}
            )
            sys.exit(0)

        # --- Gate 1: opt-in. Nothing is executed without it. -----------------
        # An item may ship expected/checks.json alongside exec.json. When the
        # gate is closed we fall back to that static rubric rather than scoring
        # 0.0, so a default (non-opted-in) council run stays meaningful and the
        # exec mode is a strict upgrade rather than a prerequisite.
        if os.environ.get("COUNCIL_ALLOW_EXEC") != "1":
            checks_path = os.path.join(item_dir, "expected", "checks.json")
            if os.path.isfile(checks_path):
                command_check = _load_command_check()
                with open(checks_path, "r", encoding="utf-8") as f:
                    checks = json.load(f)
                satisfied, total, failed = command_check.evaluate(obj, checks)
                score = round((satisfied / total), 4) if total > 0 else 1.0
                write_score(
                    workdir,
                    score,
                    "scored-static",
                    {
                        "satisfied": satisfied,
                        "total": total,
                        "failed_checks": failed,
                        "note": "exec gate closed; scored by static rubric",
                    },
                )
                sys.exit(0)
            write_score(
                workdir,
                0.0,
                "exec-disabled",
                {
                    "error": "execution not enabled",
                    "hint": "set COUNCIL_ALLOW_EXEC=1 to score this item",
                    "commands": commands,
                },
            )
            sys.exit(0)

        # --- Gates 2 and 3: allowlist + metacharacter deny-list. -------------
        allow = spec.get("allow_binaries", []) or []
        for command in commands:
            refusal = safety_refusal(command, allow)
            if refusal is not None:
                write_score(
                    workdir,
                    0.0,
                    "unsafe-command",
                    {"error": refusal, "commands": commands},
                )
                sys.exit(0)

        # --- Execute in a sandbox of input COPIES, diff stdout vs golden. ----
        sandbox = build_sandbox(item_dir, workdir)
        timeout_s = spec.get("timeout_s", 10)
        stdout = ""
        for command in commands:
            stdout, run_status, detail = run_in_sandbox(command, sandbox, timeout_s)
            if run_status != "ok":
                write_score(
                    workdir,
                    0.0,
                    run_status,
                    {"error": detail, "command": command},
                )
                sys.exit(0)

        golden_path = os.path.join(
            item_dir, "expected", spec.get("golden_stdout", "stdout.txt")
        )
        with open(golden_path, "r", encoding="utf-8") as f:
            golden = f.read()

        actual_norm = normalise(stdout)
        golden_norm = normalise(golden)
        matched = actual_norm == golden_norm

        details = {
            "matched": matched,
            "commands": commands,
            "golden_lines": len(golden_norm.split("\n")) if golden_norm else 0,
            "actual_lines": len(actual_norm.split("\n")) if actual_norm else 0,
        }
        if not matched:
            details["actual_stdout"] = actual_norm[:2000]
        write_score(workdir, 1.0 if matched else 0.0, "scored", details)
    except Exception as exc:  # scorer ABI: always exit 0
        write_score(workdir, 0.0, "error", {"error": str(exc)})

    sys.exit(0)


if __name__ == "__main__":
    main(sys.argv)
