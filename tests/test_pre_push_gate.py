"""Tests for the non-mutating pre-push gate in tools/validation/local-validation.py.

The gate must run pre-commit hooks in a throwaway worktree so a mutating hook
can never rewrite the developer's checkout, and a tripwire must catch any
check that nevertheless changes the working tree.

Hook tests are hermetic: the temp repo's config uses only ``repo: local``
hooks with ``language: system`` so nothing is downloaded. They still need the
``pre-commit`` binary, so they skip when it is not installed.
"""

import importlib.util
import os
import re
import shutil
import signal
import subprocess
import sys
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List, Tuple

import pytest
import yaml

_REPO = Path(__file__).resolve().parents[1]
_SCRIPT = _REPO / "tools" / "validation" / "local-validation.py"
spec = importlib.util.spec_from_file_location("local_validation", _SCRIPT)
assert spec is not None and spec.loader is not None
local_validation = importlib.util.module_from_spec(spec)
sys.modules["local_validation"] = local_validation
spec.loader.exec_module(local_validation)

needs_pre_commit = pytest.mark.skipif(
    shutil.which("pre-commit") is None, reason="pre-commit binary not installed"
)

_MUTATING_CONFIG = """\
repos:
  - repo: local
    hooks:
      - id: append-line
        name: append a line to every file
        entry: sh -c 'for f in "$@"; do echo mutated >> "$f"; done' --
        language: system
        files: '\\.txt$'
"""

_PASSING_CONFIG = """\
repos:
  - repo: local
    hooks:
      - id: ok
        name: always passes
        entry: 'true'
        language: system
        pass_filenames: false
"""


#: Make every git call in these tests immune to the developer's own config
#: (commit signing, global hooks, templates, ...).
_GIT_ISOLATION = ["-c", "commit.gpgsign=false", "-c", "core.hooksPath=/dev/null"]


@pytest.fixture(autouse=True)
def _isolate_git_config(monkeypatch: pytest.MonkeyPatch) -> None:
    """Also isolate the gate's own git calls, which inherit this environment."""
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")


@pytest.fixture(autouse=True)
def _fresh_env_var_cache() -> "Iterator[None]":
    """The variable list is memoised per process; tests that patch it need a clean slate."""
    local_validation._repo_env_var_names.cache_clear()
    yield
    local_validation._repo_env_var_names.cache_clear()


def _unique_marker(base: int) -> str:
    """A sleep duration no other process on the host can share.

    Tests identify the processes they spawned by this token (never by a
    generic pattern), so concurrent test runs cannot see or kill each other's.
    """
    return f"{base}.{uuid.uuid4().int % 10**9:09d}"


def _pids_with(marker: str) -> List[int]:
    result = subprocess.run(
        ["pgrep", "-f", f"sleep {marker}"], capture_output=True, text=True
    )
    return [int(p) for p in result.stdout.split()]


def _carries(pid: int, marker: str) -> bool:
    """True only if ``pid`` is alive right now AND its command line has the token."""
    result = subprocess.run(
        ["ps", "-p", str(pid), "-o", "command="], capture_output=True, text=True
    )
    return f"sleep {marker}" in result.stdout


def _kill_pids(pids: List[int], marker: str) -> None:
    """SIGKILL only pids that STILL carry the unique marker.

    A pid recorded earlier may by now belong to an unrelated process on a busy
    host, so each one is re-verified immediately before it is signalled.
    """
    for pid in pids:
        if not _carries(pid, marker):
            continue
        try:
            os.kill(pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            # The marker process already exited (or is not ours): nothing to
            # kill, which is the outcome the cleanup wants.
            pass


def _wait_until(predicate: "Callable[[], bool]", seconds: float = 120.0) -> bool:
    """Poll ``predicate`` until true or the (generous) deadline passes."""
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.1)
    return predicate()


def _gone(marker: str, seconds: float = 30.0) -> bool:
    return _wait_until(lambda: not _pids_with(marker), seconds)


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *_GIT_ISOLATION, *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def _make_repo(root: Path, config: str) -> Path:
    repo = root / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "t@example.com")
    _git(repo, "config", "user.name", "T")
    (repo / ".gitignore").write_text("tmp/\n")
    (repo / "a.txt").write_text("hello\n")
    (repo / ".pre-commit-config.yaml").write_text(config)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "init")
    return repo


def _tracked_bytes(repo: Path) -> Dict[str, bytes]:
    return {
        name: (repo / name).read_bytes() for name in _git(repo, "ls-files").splitlines()
    }


def _runner(repo: Path) -> "local_validation.ValidationRunner":
    return local_validation.ValidationRunner(verbose=False, repo_root=repo)


@needs_pre_commit
def test_gate_fails_on_mutating_hook_without_touching_checkout(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path, _MUTATING_CONFIG)
    before_bytes = _tracked_bytes(repo)
    before_status = _git(repo, "status", "--porcelain")

    runner = _runner(repo)
    assert runner.check_pre_commit_hooks() is False

    assert _tracked_bytes(repo) == before_bytes
    assert _git(repo, "status", "--porcelain") == before_status
    assert not list((repo / "tmp").glob("prepush-gate-*"))
    assert "prepush-gate-" not in _git(repo, "worktree", "list")
    assert any("Pre-commit hooks failed" in e for e in runner.errors)


@needs_pre_commit
def test_gate_failure_report_includes_hook_output(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path, _MUTATING_CONFIG)
    runner = _runner(repo)
    runner.check_pre_commit_hooks()
    assert any("append a line to every file" in e for e in runner.errors)


@needs_pre_commit
def test_gate_passes_on_clean_hook_and_leaves_repo_unchanged(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path, _PASSING_CONFIG)
    before_bytes = _tracked_bytes(repo)
    before_status = _git(repo, "status", "--porcelain")

    runner = _runner(repo)
    assert runner.check_pre_commit_hooks() is True

    assert _tracked_bytes(repo) == before_bytes
    assert _git(repo, "status", "--porcelain") == before_status
    assert not list((repo / "tmp").glob("prepush-gate-*"))
    assert runner.errors == []


@needs_pre_commit
def test_gate_validates_head_not_uncommitted_edits(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path, _MUTATING_CONFIG)
    (repo / "a.txt").write_text("uncommitted edit\n")
    runner = _runner(repo)
    runner.check_pre_commit_hooks()
    assert (repo / "a.txt").read_text() == "uncommitted edit\n"


def _stub_all_checks(runner: "local_validation.ValidationRunner") -> None:
    for name in (
        "check_python_syntax",
        "check_pre_commit_hooks",
        "check_technical_debt",
        "check_architecture_compliance",
        "check_type_safety",
        "check_security",
        "check_logging_compliance",
        "check_static_analysis",
    ):
        setattr(runner, name, lambda: True)


def test_tripwire_fails_when_a_check_mutates_a_tracked_file(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path, _PASSING_CONFIG)
    runner = _runner(repo)
    _stub_all_checks(runner)

    def mutate() -> bool:
        (repo / "a.txt").write_text("rewritten by a check\n")
        return True

    setattr(runner, "check_technical_debt", mutate)
    assert runner.run_pre_push_validation() is False
    assert any("a.txt" in e and "tripwire" in e.lower() for e in runner.errors)


def test_tripwire_quiet_when_nothing_changes(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path, _PASSING_CONFIG)
    runner = _runner(repo)
    _stub_all_checks(runner)
    assert runner.run_pre_push_validation() is True
    assert runner.errors == []


def test_tripwire_ignores_gitignored_tmp(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path, _PASSING_CONFIG)
    runner = _runner(repo)
    _stub_all_checks(runner)

    def scratch() -> bool:
        (repo / "tmp").mkdir(exist_ok=True)
        (repo / "tmp" / "scratch.txt").write_text("x")
        return True

    setattr(runner, "check_security", scratch)
    assert runner.run_pre_push_validation() is True


_CORPUS_PATHS: List[str] = [
    "research/poker-capstone/runs/p1/model/solution.py",
    "research/poker-capstone/broken-variants/v1/solution.py",
    "plugins/sdlc-model-council/assessment/stack/v1/items/x/item.json",
    "research/sdlc-bundles/outputs/bundle/out.md",
]
_NORMAL_PATHS: List[str] = [
    "plugins/sdlc-core/skills/x/SKILL.md",
    "tests/test_x.py",
    "tools/validation/y.py",
    "research/poker-capstone/harness/run.py",
]


def _top_level_exclude() -> str:
    config = yaml.safe_load((_REPO / ".pre-commit-config.yaml").read_text())
    return str(config["exclude"])


@pytest.mark.parametrize("path", _CORPUS_PATHS)
def test_config_excludes_byte_identical_corpora(path: str) -> None:
    assert re.search(_top_level_exclude(), path)


@pytest.mark.parametrize("path", _NORMAL_PATHS)
def test_config_does_not_exclude_normal_paths(path: str) -> None:
    assert not re.search(_top_level_exclude(), path)


def test_config_hook_args_prevent_generator_ping_pong() -> None:
    config = yaml.safe_load((_REPO / ".pre-commit-config.yaml").read_text())
    hooks = {hook["id"]: hook for repo in config["repos"] for hook in repo["hooks"]}
    assert "--markdown-linebreak-ext=md" in hooks["trailing-whitespace"]["args"]
    json_args = hooks["pretty-format-json"]["args"]
    assert "--no-ensure-ascii" in json_args
    assert "--autofix" in json_args and "--no-sort-keys" in json_args


def test_setup_cfg_flake8_excludes_corpora() -> None:
    text = (_REPO / "setup.cfg").read_text()
    exclude_line = next(
        line for line in text.splitlines() if line.startswith("exclude =")
    )
    for fragment in (
        "research/poker-capstone/runs",
        "research/poker-capstone/broken-variants",
        "plugins/sdlc-model-council/assessment",
        "research/sdlc-bundles/outputs",
    ):
        assert fragment in exclude_line


# --- tripwire: reports the DIFFERENCE, sees new files in untracked dirs ------


def test_tripwire_reports_only_what_the_run_changed(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path, _PASSING_CONFIG)
    (repo / "b.txt").write_text("b\n")
    _git(repo, "add", "b.txt")
    _git(repo, "commit", "-q", "-m", "add b")
    (repo / "a.txt").write_text("already dirty before the run\n")

    runner = _runner(repo)
    _stub_all_checks(runner)

    def mutate() -> bool:
        (repo / "b.txt").write_text("changed by a check\n")
        return True

    setattr(runner, "check_technical_debt", mutate)
    assert runner.run_pre_push_validation() is False
    report = next(e for e in runner.errors if "TRIPWIRE" in e)
    assert "b.txt" in report
    assert "a.txt" not in report


def test_tripwire_sees_new_file_inside_existing_untracked_directory(
    tmp_path: Path,
) -> None:
    repo = _make_repo(tmp_path, _PASSING_CONFIG)
    (repo / "scratch").mkdir()
    (repo / "scratch" / "first.txt").write_text("1")

    runner = _runner(repo)
    _stub_all_checks(runner)

    def add_file() -> bool:
        (repo / "scratch" / "second.txt").write_text("2")
        return True

    setattr(runner, "check_security", add_file)
    assert runner.run_pre_push_validation() is False
    assert any("second.txt" in e for e in runner.errors)


def _make_repo_with_corpus(tmp_path: Path) -> Path:
    repo = _make_repo(tmp_path, _PASSING_CONFIG)
    corpus = repo / "research" / "poker-capstone" / "runs"
    corpus.mkdir(parents=True)
    (corpus / "x.txt").write_text("verbatim model output\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "corpus")
    return repo


def test_tripwire_reports_protected_corpus_bytes_changing(tmp_path: Path) -> None:
    repo = _make_repo_with_corpus(tmp_path)
    runner = _runner(repo)
    _stub_all_checks(runner)

    def rewrite() -> bool:
        (repo / "research/poker-capstone/runs/x.txt").write_text("rewritten\n")
        return True

    setattr(runner, "check_type_safety", rewrite)
    assert runner.run_pre_push_validation() is False
    assert any("research/poker-capstone/runs/x.txt" in e for e in runner.errors)


def test_tripwire_reports_protected_corpus_index_entry_changing(
    tmp_path: Path,
) -> None:
    repo = _make_repo_with_corpus(tmp_path)
    runner = _runner(repo)
    _stub_all_checks(runner)

    def stage_rewrite() -> bool:
        target = repo / "research/poker-capstone/runs/x.txt"
        target.write_text("rewritten and staged\n")
        _git(repo, "add", str(target))
        return True

    setattr(runner, "check_type_safety", stage_rewrite)
    assert runner.run_pre_push_validation() is False
    assert any(
        "research/poker-capstone" in e and "index entries changed" in e
        for e in runner.errors
    )


# --- worktree lifecycle failure paths ---------------------------------------


def _intercepting_run_command(
    runner: "local_validation.ValidationRunner", needle: List[str], result: Tuple
) -> None:
    """Make run_command return ``result`` for commands containing ``needle``."""
    real = runner.run_command

    def fake(cmd: List[str], *args: Any, **kwargs: Any) -> Tuple:
        if all(part in cmd for part in needle):
            return result
        return real(cmd, *args, **kwargs)

    setattr(runner, "run_command", fake)


@needs_pre_commit
def test_gate_reports_worktree_add_failure_and_leaves_no_worktree(
    tmp_path: Path,
) -> None:
    repo = _make_repo(tmp_path, _PASSING_CONFIG)
    runner = _runner(repo)
    _intercepting_run_command(runner, ["worktree", "add"], (128, "", "fatal: boom"))

    assert runner.check_pre_commit_hooks() is False
    assert any("cannot create worktree" in e and "boom" in e for e in runner.errors)
    assert "prepush-gate-" not in _git(repo, "worktree", "list")
    assert not list((repo / "tmp").glob("prepush-gate-*"))


@needs_pre_commit
def test_gate_reports_worktree_remove_failure_with_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _make_repo(tmp_path, _PASSING_CONFIG)
    runner = _runner(repo)
    _intercepting_run_command(runner, ["worktree", "remove"], (1, "", "locked"))
    # Removal must be impossible, including the directory-deletion fallback.
    monkeypatch.setattr(local_validation.shutil, "rmtree", lambda *a, **k: None)

    try:
        assert runner.check_pre_commit_hooks() is False
        removal = [e for e in runner.errors if "could not remove" in e]
        assert removal and "prepush-gate-" in removal[0] and "locked" in removal[0]
    finally:
        _git(repo, "worktree", "remove", "--force", *_leftover(repo))


def _leftover(repo: Path) -> List[str]:
    return [str(p) for p in (repo / "tmp").glob("prepush-gate-*")][:1]


@needs_pre_commit
def test_gate_survives_a_stale_registration_whose_directory_is_gone(
    tmp_path: Path,
) -> None:
    repo = _make_repo(tmp_path, _PASSING_CONFIG)
    stale = repo / "tmp" / f"prepush-gate-{os.getpid()}-deadbeef"
    _git(repo, "worktree", "add", "--detach", str(stale), "HEAD")
    shutil.rmtree(stale)  # a killed run: registered in .git, gone from disk
    assert "prepush-gate-" in _git(repo, "worktree", "list")

    runner = _runner(repo)
    assert runner.check_pre_commit_hooks() is True
    assert runner.errors == []
    assert "prepush-gate-" not in _git(repo, "worktree", "list")


# --- timeout kills the whole process group ----------------------------------

_SLEEP_CONFIG = """\
repos:
  - repo: local
    hooks:
      - id: sleeper
        name: sleeps far longer than the timeout
        entry: sleep {marker}
        language: system
        pass_filenames: false
        always_run: true
"""


def _watch_for(marker: str, seen: List[int], stop: "threading.Event") -> None:
    """Record every pid carrying ``marker`` until told to stop."""
    while not stop.is_set():
        for pid in _pids_with(marker):
            if pid not in seen:
                seen.append(pid)
        stop.wait(0.05)


@needs_pre_commit
@pytest.mark.skipif(os.name == "nt", reason="process groups are POSIX-only")
@pytest.mark.skipif(shutil.which("pgrep") is None, reason="pgrep not available")
def test_gate_timeout_fails_removes_worktree_and_kills_grandchildren(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    marker = _unique_marker(31337)
    repo = _make_repo(tmp_path, _SLEEP_CONFIG.format(marker=marker))
    monkeypatch.setattr(local_validation, "_PRE_COMMIT_TIMEOUT", 20)
    runner = _runner(repo)
    seen: List[int] = []
    stop = threading.Event()
    watcher = threading.Thread(target=_watch_for, args=(marker, seen, stop))
    watcher.start()
    try:
        assert runner.check_pre_commit_hooks() is False
        stop.set()
        watcher.join()
        assert seen, "the hook never started, so the timeout proved nothing"
        assert any("timed out" in e for e in runner.errors), runner.errors
        assert "prepush-gate-" not in _git(repo, "worktree", "list")
        assert not list((repo / "tmp").glob("prepush-gate-*"))
        assert _gone(marker), "hook grandchild outlived the gate"
    finally:
        stop.set()
        watcher.join()
        _kill_pids(seen + _pids_with(marker), marker)


# --- tripwire: untracked content is not hashed (the gate's own log may grow) --


def test_tripwire_ignores_a_preexisting_untracked_file_that_grows(
    tmp_path: Path,
) -> None:
    repo = _make_repo(tmp_path, _PASSING_CONFIG)
    (repo / "command-runs").mkdir()
    log = repo / "command-runs" / "cmd.log"
    log.write_text("start\n")

    runner = _runner(repo)
    _stub_all_checks(runner)

    def keep_logging() -> bool:
        with log.open("a") as handle:
            handle.write("the gate's own output, tee'd into the repo\n")
        return True

    setattr(runner, "check_security", keep_logging)
    assert runner.run_pre_push_validation() is True
    assert runner.errors == []


def test_tripwire_trips_on_a_new_untracked_file_in_an_untracked_directory(
    tmp_path: Path,
) -> None:
    repo = _make_repo(tmp_path, _PASSING_CONFIG)
    (repo / "command-runs").mkdir()
    (repo / "command-runs" / "old.log").write_text("old\n")

    runner = _runner(repo)
    _stub_all_checks(runner)

    def add_file() -> bool:
        (repo / "command-runs" / "new.log").write_text("new\n")
        return True

    setattr(runner, "check_security", add_file)
    assert runner.run_pre_push_validation() is False
    report = next(e for e in runner.errors if "TRIPWIRE" in e)
    assert "new.log" in report and "old.log" not in report


def test_tripwire_trips_when_an_untracked_file_disappears(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path, _PASSING_CONFIG)
    (repo / "scratch.txt").write_text("x")

    runner = _runner(repo)
    _stub_all_checks(runner)

    def remove() -> bool:
        (repo / "scratch.txt").unlink()
        return True

    setattr(runner, "check_security", remove)
    assert runner.run_pre_push_validation() is False
    assert any("scratch.txt" in e for e in runner.errors)


def test_tripwire_still_hashes_content_of_modified_tracked_files(
    tmp_path: Path,
) -> None:
    repo = _make_repo(tmp_path, _PASSING_CONFIG)
    (repo / "a.txt").write_text("dirty before\n")

    runner = _runner(repo)
    _stub_all_checks(runner)

    def mutate_again() -> bool:
        (repo / "a.txt").write_text("dirty after\n")
        return True

    setattr(runner, "check_security", mutate_again)
    assert runner.run_pre_push_validation() is False
    assert any("a.txt" in e and "TRIPWIRE" in e for e in runner.errors)


def test_status_parser_skips_rename_source_when_rename_is_in_second_column(
    tmp_path: Path,
) -> None:
    repo = _make_repo(tmp_path, _PASSING_CONFIG)
    runner = _runner(repo)
    (repo / "new.txt").write_text("n\n")

    def fake_git_output(args: List[str]) -> str:
        if args[0] == "status":
            return " R new.txt\0a-rather-long-rename-source.txt\0"
        return ""

    setattr(runner, "_git_output", fake_git_output)
    keys = [k for k in runner._tree_snapshot() if k.startswith("file:")]
    assert keys == ["file:new.txt"]


# --- run_command hardening ---------------------------------------------------


def test_run_command_survives_undecodable_output(tmp_path: Path) -> None:
    runner = _runner(tmp_path)
    code, out, _ = runner.run_command(
        [
            sys.executable,
            "-c",
            "import sys; sys.stdout.buffer.write(b'ok \\xff\\xfe end')",
        ]
    )
    assert code == 0
    assert out.startswith("ok ") and out.endswith(" end")


class _HungProc:
    """Popen stand-in whose pipes never close, even after the kill."""

    pid = 2**22 + 1
    returncode = None

    def __init__(self) -> None:
        self.timeouts: List[object] = []

    def communicate(self, timeout: object = None) -> Tuple[str, str]:
        self.timeouts.append(timeout)
        raise subprocess.TimeoutExpired("x", 0)


def test_run_command_gives_up_if_pipes_stay_open_after_kill(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    proc = _HungProc()
    # Discovery shells out through the same (patched) Popen; bypass it.
    monkeypatch.setattr(local_validation, "_discover_repo_env_vars", lambda: None)
    monkeypatch.setattr(local_validation.subprocess, "Popen", lambda *a, **k: proc)
    monkeypatch.setattr(
        local_validation.ValidationRunner,
        "_kill_process_group",
        staticmethod(lambda p: None),
    )
    runner = _runner(tmp_path)
    code, _, err = runner.run_command(["whatever"], timeout=1)
    assert code == 1
    assert "timed out" in err
    assert len(proc.timeouts) == 2 and proc.timeouts[1] is not None


# --- SIGTERM to the gate cleans up ------------------------------------------

_GATE_SCRIPT = """\
import importlib.util, sys
from pathlib import Path
spec = importlib.util.spec_from_file_location("lv", sys.argv[1])
lv = importlib.util.module_from_spec(spec)
sys.modules["lv"] = lv
spec.loader.exec_module(lv)
runner = lv.ValidationRunner(verbose=False, repo_root=Path(sys.argv[2]))
print("READY", flush=True)
try:
    runner.check_pre_commit_hooks()
except BaseException as exc:
    print("INTERRUPTED", type(exc).__name__, flush=True)
    raise SystemExit(143)
"""


def _start_gate(
    tmp_path: Path, source: str, repo: Path, *extra: str
) -> "subprocess.Popen[str]":
    script = tmp_path / "gate.py"
    script.write_text(source)
    env = dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1")
    return subprocess.Popen(
        [sys.executable, str(script), str(_SCRIPT), str(repo), *extra],
        stdout=subprocess.PIPE,
        text=True,
        env=env,
    )


def _read_until(proc: "subprocess.Popen[str]", wanted: str) -> List[str]:
    assert proc.stdout is not None
    lines: List[str] = []
    while True:
        line = proc.stdout.readline()
        if not line:
            raise AssertionError(f"gate exited before printing {wanted!r}: {lines}")
        lines.append(line.strip())
        if line.strip() == wanted:
            return lines


posix_only = pytest.mark.skipif(os.name == "nt", reason="signals/groups are POSIX")
needs_pgrep = pytest.mark.skipif(shutil.which("pgrep") is None, reason="no pgrep")


@needs_pre_commit
@posix_only
@needs_pgrep
def test_sigterm_to_the_gate_removes_worktree_and_kills_children(
    tmp_path: Path,
) -> None:
    marker = _unique_marker(31337)
    repo = _make_repo(tmp_path, _SLEEP_CONFIG.format(marker=marker))
    proc = _start_gate(tmp_path, _GATE_SCRIPT, repo)
    try:
        _read_until(proc, "READY")
        assert _wait_until(lambda: bool(_pids_with(marker))), "hook never started"
        proc.send_signal(signal.SIGTERM)
        proc.wait(timeout=120)
        assert "prepush-gate-" not in _git(repo, "worktree", "list")
        assert not list((repo / "tmp").glob("prepush-gate-*"))
        assert _gone(marker), "hook grandchild survived SIGTERM"
    finally:
        proc.kill()
        _kill_pids(_pids_with(marker), marker)


_SLOW_CLEANUP_SCRIPT = """\
import importlib.util, os, signal, sys, time
from pathlib import Path
spec = importlib.util.spec_from_file_location("lv", sys.argv[1])
lv = importlib.util.module_from_spec(spec)
sys.modules["lv"] = lv
spec.loader.exec_module(lv)
runner = lv.ValidationRunner(verbose=False, repo_root=Path(sys.argv[2]))
mode = sys.argv[3]
if mode == "original_handler":
    def original(signum, frame):
        print("ORIGINAL_HANDLER", flush=True)
        signal.signal(signal.SIGTERM, signal.SIG_DFL)
        os.kill(os.getpid(), signal.SIGTERM)
    signal.signal(signal.SIGTERM, original)
real = runner.run_command

def slow_removal(cmd, *args, **kwargs):
    if "worktree" in cmd and "remove" in cmd:
        print("CLEANUP", flush=True)
        time.sleep(2.0)  # a long window in which a SIGTERM can land
    return real(cmd, *args, **kwargs)

runner.run_command = slow_removal
print("READY", flush=True)
try:
    result = runner.check_pre_commit_hooks()
except BaseException as exc:
    print("INTERRUPTED", type(exc).__name__, flush=True)
    raise SystemExit(143)
print("STILL ALIVE", result, flush=True)
"""


def _assert_clean(repo: Path, marker: str) -> None:
    assert "prepush-gate-" not in _git(repo, "worktree", "list")
    assert not list((repo / "tmp").glob("prepush-gate-*"))
    assert _gone(marker)


@needs_pre_commit
@posix_only
@needs_pgrep
def test_sigterm_during_normal_cleanup_is_honoured_after_cleanup(
    tmp_path: Path,
) -> None:
    """F1: a SIGTERM with no earlier signal, landing in cleanup, must not be lost."""
    marker = _unique_marker(31340)
    repo = _make_repo(tmp_path, _PASSING_CONFIG)
    proc = _start_gate(tmp_path, _SLOW_CLEANUP_SCRIPT, repo, "default")
    try:
        _read_until(proc, "READY")
        _read_until(proc, "CLEANUP")
        proc.send_signal(signal.SIGTERM)
        assert proc.stdout is not None
        output = proc.stdout.read()
        assert proc.wait(timeout=120) == -signal.SIGTERM, output
        assert "STILL ALIVE" not in output
        _assert_clean(repo, marker)
    finally:
        proc.kill()


@needs_pre_commit
@posix_only
@needs_pgrep
def test_two_sigterms_with_a_confirmed_delay_still_clean_up_and_end_by_signal(
    tmp_path: Path,
) -> None:
    """The second SIGTERM arrives DURING the first one's cleanup.

    Cleanup must finish, the previous handler must be back in place, and the
    second signal must then reach that original disposition (it is not lost).
    """
    marker = _unique_marker(31341)
    repo = _make_repo(tmp_path, _SLEEP_CONFIG.format(marker=marker))
    proc = _start_gate(tmp_path, _SLOW_CLEANUP_SCRIPT, repo, "original_handler")
    try:
        _read_until(proc, "READY")
        assert _wait_until(lambda: bool(_pids_with(marker))), "hook never started"
        proc.send_signal(signal.SIGTERM)
        _read_until(proc, "CLEANUP")
        time.sleep(0.5)  # confirmed delay: cleanup is demonstrably in progress
        proc.send_signal(signal.SIGTERM)
        assert proc.stdout is not None
        output = proc.stdout.read()
        assert proc.wait(timeout=120) == -signal.SIGTERM, output
        assert "ORIGINAL_HANDLER" in output, "previous handler was not restored"
        assert "STILL ALIVE" not in output
        _assert_clean(repo, marker)
    finally:
        proc.kill()
        _kill_pids(_pids_with(marker), marker)


_THREAD_SCRIPT = """\
import importlib.util, sys, threading
from pathlib import Path
spec = importlib.util.spec_from_file_location("lv", sys.argv[1])
lv = importlib.util.module_from_spec(spec)
sys.modules["lv"] = lv
spec.loader.exec_module(lv)
lv._PRE_COMMIT_TIMEOUT = 10
repo = Path(sys.argv[2])
main_runner = lv.ValidationRunner(verbose=False, repo_root=repo)
worker_runner = lv.ValidationRunner(verbose=False, repo_root=repo)
worker_runner.run_command = lambda cmd, *a, **k: (0, "", "")  # instant gate call
worker = threading.Thread(target=worker_runner.check_pre_commit_hooks, daemon=True)
real = main_runner.run_command

def wrapped(cmd, *args, **kwargs):
    if cmd and cmd[0] == "pre-commit":
        worker.start()
        worker.join(timeout=2.0)  # old code: finishes; new code: queues on the lock
        print("HOOK", worker.is_alive(), flush=True)
    return real(cmd, *args, **kwargs)

main_runner.run_command = wrapped
print("READY", flush=True)
try:
    main_runner.check_pre_commit_hooks()
except BaseException as exc:
    print("INTERRUPTED", type(exc).__name__, flush=True)
    raise SystemExit(143)
print("STILL ALIVE", flush=True)
"""


@needs_pre_commit
@posix_only
@needs_pgrep
def test_a_worker_thread_gate_call_does_not_mute_the_main_thread_gate(
    tmp_path: Path,
) -> None:
    marker = _unique_marker(31342)
    repo = _make_repo(tmp_path, _SLEEP_CONFIG.format(marker=marker))
    proc = _start_gate(tmp_path, _THREAD_SCRIPT, repo)
    try:
        _read_until(proc, "READY")
        _read_until(proc, "HOOK True")
        assert _wait_until(lambda: bool(_pids_with(marker))), "hook never started"
        proc.send_signal(signal.SIGTERM)
        assert proc.stdout is not None
        output = proc.stdout.read()
        assert proc.wait(timeout=60) == 143, output
        assert "INTERRUPTED GateTerminated" in output
        assert "STILL ALIVE" not in output
        _assert_clean(repo, marker)
    finally:
        proc.kill()
        _kill_pids(_pids_with(marker), marker)


# --- repository-selection variables must not leak into the gate's children ---


@needs_pre_commit
def test_gate_ignores_inherited_git_dir_and_work_tree(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A git hook runs the gate with GIT_DIR/GIT_WORK_TREE exported.

    Those override ``cwd``, so without sanitising, ``git worktree`` and
    ``pre-commit`` would operate on the checkout named by the variables (the
    developer's MAIN checkout) instead of the repository being gated.
    """
    main = tmp_path / "main"
    main.mkdir()
    checkout = _make_repo(main, _MUTATING_CONFIG)
    target_root = tmp_path / "target"
    target_root.mkdir()
    target = _make_repo(target_root, _PASSING_CONFIG)
    main_bytes = _tracked_bytes(checkout)
    main_status = _git(checkout, "status", "--porcelain")

    monkeypatch.setenv("GIT_DIR", str(checkout / ".git"))
    monkeypatch.setenv("GIT_WORK_TREE", str(checkout))
    runner = _runner(target)
    result = runner.check_pre_commit_hooks()
    monkeypatch.delenv("GIT_DIR")
    monkeypatch.delenv("GIT_WORK_TREE")

    assert _tracked_bytes(checkout) == main_bytes, "the main checkout was rewritten"
    assert _git(checkout, "status", "--porcelain") == main_status
    assert result is True, runner.errors  # the gate saw target's passing config
    assert runner.errors == []
    for repo in (checkout, target):
        assert "prepush-gate-" not in _git(repo, "worktree", "list")
        assert not list((repo / "tmp").glob("prepush-gate-*"))


@needs_pre_commit
def test_gate_reports_the_gated_repos_hook_not_the_inherited_ones(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    main = tmp_path / "main"
    main.mkdir()
    checkout = _make_repo(main, _PASSING_CONFIG)
    target_root = tmp_path / "target"
    target_root.mkdir()
    target = _make_repo(target_root, _MUTATING_CONFIG)

    monkeypatch.setenv("GIT_DIR", str(checkout / ".git"))
    monkeypatch.setenv("GIT_WORK_TREE", str(checkout))
    runner = _runner(target)
    result = runner.check_pre_commit_hooks()

    assert result is False
    assert any("append a line to every file" in e for e in runner.errors)


def test_tripwire_snapshot_uses_the_gated_repo_not_inherited_git_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    main = tmp_path / "main"
    main.mkdir()
    checkout = _make_repo(main, _PASSING_CONFIG)
    target_root = tmp_path / "target"
    target_root.mkdir()
    target = _make_repo(target_root, _PASSING_CONFIG)
    (target / "only-in-target.txt").write_text("x\n")

    monkeypatch.setenv("GIT_DIR", str(checkout / ".git"))
    monkeypatch.setenv("GIT_WORK_TREE", str(checkout))
    snapshot = _runner(target)._tree_snapshot()

    assert snapshot.get("untracked:only-in-target.txt") == "present"


def test_git_environment_drops_repository_selection_but_keeps_config_isolation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for name in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_COMMON_DIR"):
        monkeypatch.setenv(name, "/somewhere")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.setenv("UNRELATED_VARIABLE", "kept")

    env = local_validation.sanitized_git_env()

    for name in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_COMMON_DIR"):
        assert name not in env
    assert env["GIT_CONFIG_GLOBAL"] == os.devnull
    assert env["GIT_CONFIG_NOSYSTEM"] == "1"
    assert env["UNRELATED_VARIABLE"] == "kept"


def test_git_environment_falls_back_to_the_builtin_list(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(local_validation, "_discover_repo_env_vars", lambda: None)
    monkeypatch.setenv("GIT_DIR", "/somewhere")
    monkeypatch.setenv("GIT_OBJECT_DIRECTORY", "/objects")
    env = local_validation.sanitized_git_env()
    assert "GIT_DIR" not in env and "GIT_OBJECT_DIRECTORY" not in env


# --- worktree creation is inside the cleanup scope ---------------------------


def _create_then(
    runner: "local_validation.ValidationRunner", action: Callable[[], None]
) -> None:
    """After the real `git worktree add` succeeds, run ``action`` (e.g. raise)."""
    real = runner.run_command

    def fake(cmd: List[str], *args: Any, **kwargs: Any) -> Tuple:
        result = real(cmd, *args, **kwargs)
        if "worktree" in cmd and "add" in cmd:
            action()
        return result

    setattr(runner, "run_command", fake)


@needs_pre_commit
def test_failure_during_creation_still_removes_what_was_created(
    tmp_path: Path,
) -> None:
    repo = _make_repo(tmp_path, _PASSING_CONFIG)
    runner = _runner(repo)

    def boom() -> None:
        raise RuntimeError("interrupted right after creation")

    _create_then(runner, boom)
    with pytest.raises(RuntimeError, match="interrupted right after creation"):
        runner.check_pre_commit_hooks()

    assert "prepush-gate-" not in _git(repo, "worktree", "list")
    assert not list((repo / "tmp").glob("prepush-gate-*"))


@needs_pre_commit
def test_cleanup_failure_does_not_mask_the_original_error(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path, _PASSING_CONFIG)
    runner = _runner(repo)
    real = runner.run_command

    def fake(cmd: List[str], *args: Any, **kwargs: Any) -> Tuple:
        if "worktree" in cmd and "remove" in cmd:
            raise OSError("cleanup exploded")
        return real(cmd, *args, **kwargs)

    def boom() -> None:
        raise RuntimeError("original error")

    setattr(runner, "run_command", fake)
    _create_then(runner, boom)
    try:
        with pytest.raises(RuntimeError, match="original error"):
            runner.check_pre_commit_hooks()
    finally:
        subprocess.run(
            ["git", "worktree", "remove", "--force", *_leftover(repo)],
            cwd=repo,
            check=False,
            capture_output=True,
        )


@needs_pre_commit
def test_sigterm_handler_is_restored_after_the_gate(tmp_path: Path) -> None:
    import signal

    if os.name == "nt":
        pytest.skip("SIGTERM handlers are POSIX")
    repo = _make_repo(tmp_path, _PASSING_CONFIG)
    before = signal.getsignal(signal.SIGTERM)
    _runner(repo).check_pre_commit_hooks()
    assert signal.getsignal(signal.SIGTERM) is before


_SLOW_ADD_SCRIPT = """\
import importlib.util, sys
from pathlib import Path
spec = importlib.util.spec_from_file_location("lv", sys.argv[1])
lv = importlib.util.module_from_spec(spec)
sys.modules["lv"] = lv
spec.loader.exec_module(lv)
runner = lv.ValidationRunner(verbose=False, repo_root=Path(sys.argv[2]))
real = runner.run_command
marker = sys.argv[3]

def slow(cmd, *args, **kwargs):
    if "worktree" in cmd and "add" in cmd:
        # A slow git: registers the worktree, then lingers before returning.
        script = 'git worktree add --detach "$0" HEAD; sleep ' + marker
        wrapped = ["sh", "-c", script, cmd[-2]]
        print("ADDING", flush=True)
        return real(wrapped, *args, **kwargs)
    return real(cmd, *args, **kwargs)

runner.run_command = slow
print("READY", flush=True)
try:
    runner.check_pre_commit_hooks()
except BaseException as exc:
    print("INTERRUPTED", type(exc).__name__, flush=True)
    raise SystemExit(143)
"""


@needs_pre_commit
@posix_only
@needs_pgrep
def test_sigterm_during_worktree_creation_leaves_no_worktree_or_orphan(
    tmp_path: Path,
) -> None:
    marker = _unique_marker(31338)
    repo = _make_repo(tmp_path, _PASSING_CONFIG)
    proc = _start_gate(tmp_path, _SLOW_ADD_SCRIPT, repo, marker)
    try:
        _read_until(proc, "ADDING")
        assert _wait_until(lambda: bool(_pids_with(marker))), "slow add never started"
        assert _wait_until(
            lambda: "prepush-gate-" in _git(repo, "worktree", "list"), 60
        )
        proc.send_signal(signal.SIGTERM)
        proc.wait(timeout=120)
        assert "prepush-gate-" not in _git(repo, "worktree", "list")
        assert not list((repo / "tmp").glob("prepush-gate-*"))
        assert _gone(marker), "slow git child survived SIGTERM"
    finally:
        proc.kill()
        _kill_pids(_pids_with(marker), marker)


# --- F1: a creation killed mid-checkout leaves a LOCKED registration ---------


def _add_worktree(repo: Path, path: Path) -> None:
    _git(repo, "worktree", "add", "--detach", str(path), "HEAD")


def _registered(repo: Path, path: Path) -> bool:
    return os.path.realpath(path) in {
        os.path.realpath(line[len("worktree ") :])
        for line in _git(repo, "worktree", "list", "--porcelain").splitlines()
        if line.startswith("worktree ")
    }


def test_cleanup_removes_a_worktree_locked_as_initializing(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path, _PASSING_CONFIG)
    runner = _runner(repo)
    path = runner._gate_worktree_path()
    _add_worktree(repo, path)
    _git(repo, "worktree", "lock", "--reason", "initializing", str(path))

    assert runner._remove_worktree(path) is False
    assert runner.errors == []
    assert not _registered(repo, path)
    assert not path.exists()


def test_cleanup_removes_a_locked_registration_whose_directory_is_gone(
    tmp_path: Path,
) -> None:
    repo = _make_repo(tmp_path, _PASSING_CONFIG)
    runner = _runner(repo)
    path = runner._gate_worktree_path()
    _add_worktree(repo, path)
    _git(repo, "worktree", "lock", "--reason", "initializing", str(path))
    shutil.rmtree(path)

    assert runner._remove_worktree(path) is False
    assert not _registered(repo, path)


_SMUDGE_ATTRIBUTES = "a.txt filter=slow\n"


def _make_repo_with_slow_checkout(tmp_path: Path, marker: str, config: str) -> Path:
    """A repo whose checkout (of a NEW worktree) blocks inside a smudge filter."""
    repo = _make_repo(tmp_path, config)
    (repo / ".gitattributes").write_text(_SMUDGE_ATTRIBUTES)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "attributes")
    # Configured only after the commit, so only the later checkout is slow.
    _git(repo, "config", "filter.slow.smudge", f"sleep {marker}; cat")
    return repo


def _locks(repo: Path) -> List[Path]:
    return list((repo / ".git" / "worktrees").glob("*/locked"))


@needs_pre_commit
@posix_only
@needs_pgrep
def test_sigkill_of_git_mid_checkout_leaves_a_locked_registration(
    tmp_path: Path,
) -> None:
    """Reproduction of the premise: SIGKILL during `worktree add` leaves a lock."""
    marker = _unique_marker(31339)
    repo = _make_repo_with_slow_checkout(tmp_path, marker, _PASSING_CONFIG)
    runner = _runner(repo)
    path = runner._gate_worktree_path()
    proc = subprocess.Popen(
        ["git", "worktree", "add", "--detach", str(path), "HEAD"],
        cwd=repo,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    try:
        assert _wait_until(lambda: bool(_pids_with(marker))), "checkout never blocked"
        assert _locks(repo), "git holds no lock while checking out"
        os.killpg(proc.pid, signal.SIGKILL)  # git's own cleanup never runs
        proc.wait(timeout=60)
        _kill_pids(_pids_with(marker), marker)
        assert _locks(repo)[0].read_text().strip() == "initializing"
        _git(repo, "worktree", "prune")
        assert _registered(repo, path), "prune is expected to skip a locked entry"
        refused = subprocess.run(
            ["git", "worktree", "remove", "--force", str(path)],
            cwd=repo,
            capture_output=True,
            text=True,
        )
        assert refused.returncode != 0, "a single remove --force must be refused"

        assert runner._remove_worktree(path) is False
        assert not _registered(repo, path) and not path.exists()
        assert not _locks(repo)
    finally:
        if proc.poll() is None:
            os.killpg(proc.pid, signal.SIGKILL)
        _kill_pids(_pids_with(marker), marker)


@needs_pre_commit
@posix_only
@needs_pgrep
def test_sigterm_to_the_gate_during_checkout_leaves_no_locked_worktree(
    tmp_path: Path,
) -> None:
    marker = _unique_marker(31339)
    repo = _make_repo_with_slow_checkout(tmp_path, marker, _PASSING_CONFIG)
    proc = _start_gate(tmp_path, _GATE_SCRIPT, repo)
    try:
        _read_until(proc, "READY")
        assert _wait_until(lambda: bool(_pids_with(marker))), "checkout never blocked"
        assert _locks(repo), "git holds no lock while checking out"
        proc.send_signal(signal.SIGTERM)
        proc.wait(timeout=120)
        assert "prepush-gate-" not in _git(repo, "worktree", "list")
        assert not list((repo / "tmp").glob("prepush-gate-*"))
        assert not _locks(repo)
        assert _gone(marker)
    finally:
        proc.kill()
        _kill_pids(_pids_with(marker), marker)


# --- F2: every gate call owns a unique worktree ------------------------------


def test_gate_worktree_paths_are_unique_per_call(tmp_path: Path) -> None:
    runner = _runner(_make_repo(tmp_path, _PASSING_CONFIG))
    paths = {runner._gate_worktree_path() for _ in range(50)}
    assert len(paths) == 50
    assert all(p.name.startswith(f"prepush-gate-{os.getpid()}-") for p in paths)


@needs_pre_commit
def test_concurrent_gate_calls_in_one_process_do_not_share_or_remove_worktrees(
    tmp_path: Path,
) -> None:
    repo = _make_repo(tmp_path, _PASSING_CONFIG)
    runners = [_runner(repo) for _ in range(3)]
    results: List[bool] = []
    barrier = threading.Barrier(len(runners))

    def run(runner: "local_validation.ValidationRunner") -> None:
        barrier.wait()
        results.append(runner.check_pre_commit_hooks())

    threads = [threading.Thread(target=run, args=(r,)) for r in runners]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert results == [True] * len(runners), [r.errors for r in runners]
    assert "prepush-gate-" not in _git(repo, "worktree", "list")


@needs_pre_commit
def test_concurrent_gate_calls_in_one_process_are_serialised(tmp_path: Path) -> None:
    """The gate is held for the whole call, so calls queue instead of overlapping."""
    repo = _make_repo(tmp_path, _PASSING_CONFIG)
    runners = [_runner(repo) for _ in range(3)]
    lock = threading.Lock()
    state = {"active": 0, "max": 0}
    paths: List[str] = []

    def watch(runner: "local_validation.ValidationRunner") -> None:
        real = runner.run_command

        def wrapped(cmd: List[str], *args: Any, **kwargs: Any) -> Tuple:
            if cmd[:3] == ["git", "worktree", "add"]:
                paths.append(cmd[-2])
            if cmd and cmd[0] == "pre-commit":
                with lock:
                    state["active"] += 1
                    state["max"] = max(state["max"], state["active"])
                time.sleep(0.4)
                try:
                    return real(cmd, *args, **kwargs)
                finally:
                    with lock:
                        state["active"] -= 1
            return real(cmd, *args, **kwargs)

        setattr(runner, "run_command", wrapped)

    for runner in runners:
        watch(runner)
    barrier = threading.Barrier(len(runners))
    results: List[bool] = []

    def run(runner: "local_validation.ValidationRunner") -> None:
        barrier.wait()
        results.append(runner.check_pre_commit_hooks())

    threads = [threading.Thread(target=run, args=(r,)) for r in runners]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert results == [True] * len(runners)
    assert state["max"] == 1, "gate calls overlapped"
    assert len(set(paths)) == len(paths) == len(runners)


# --- F3: deletion is confined to worktrees this call chose under <repo>/tmp ---


def _refused(
    runner: "local_validation.ValidationRunner", path: Path, check: str
) -> None:
    assert runner._remove_worktree(path) is True
    assert any(str(path) in e and check in e for e in runner.errors), runner.errors


def test_remove_worktree_refuses_the_repo_root_itself(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path, _PASSING_CONFIG)
    before = _tracked_bytes(repo)
    runner = _runner(repo)

    _refused(runner, repo, "directly under")
    assert (repo / ".git").is_dir() and _tracked_bytes(repo) == before


def test_remove_worktree_refuses_a_path_outside_tmp(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path, _PASSING_CONFIG)
    runner = _runner(repo)
    outside = tmp_path / "elsewhere" / runner._gate_worktree_path().name
    outside.mkdir(parents=True)
    (outside / "keep.txt").write_bytes(b"precious")

    _refused(runner, outside, "directly under")
    assert (outside / "keep.txt").read_bytes() == b"precious"


def test_remove_worktree_refuses_a_non_matching_name(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path, _PASSING_CONFIG)
    runner = _runner(repo)
    other = repo / "tmp" / "keep-me"
    other.mkdir(parents=True)
    (other / "keep.txt").write_bytes(b"precious")

    _refused(runner, other, "name")
    assert (other / "keep.txt").read_bytes() == b"precious"


def test_remove_worktree_refuses_a_matching_name_this_call_did_not_choose(
    tmp_path: Path,
) -> None:
    repo = _make_repo(tmp_path, _PASSING_CONFIG)
    runner = _runner(repo)
    foreign = repo / "tmp" / f"prepush-gate-{os.getpid()}-0123abcd"
    foreign.mkdir(parents=True)
    (foreign / "keep.txt").write_bytes(b"someone else's")

    _refused(runner, foreign, "chosen")
    assert (foreign / "keep.txt").read_bytes() == b"someone else's"


def test_remove_worktree_refuses_a_symlink_at_the_chosen_path(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path, _PASSING_CONFIG)
    runner = _runner(repo)
    victim = tmp_path / "victim"
    victim.mkdir()
    (victim / "keep.txt").write_bytes(b"precious")
    link = runner._gate_worktree_path()
    link.parent.mkdir(parents=True)
    link.symlink_to(victim)

    _refused(runner, link, "symlink")
    assert (victim / "keep.txt").read_bytes() == b"precious" and link.is_symlink()


def test_a_symlinked_tmp_is_refused_and_nothing_is_created_or_deleted(
    tmp_path: Path,
) -> None:
    repo = _make_repo(tmp_path, _PASSING_CONFIG)
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "keep.txt").write_bytes(b"precious")
    (repo / "tmp").symlink_to(outside)
    runner = _runner(repo)

    assert runner.check_pre_commit_hooks() is False
    assert any("symlink" in e and "tmp" in e for e in runner.errors), runner.errors
    assert sorted(p.name for p in outside.iterdir()) == ["keep.txt"]
    assert (outside / "keep.txt").read_bytes() == b"precious"

    chosen = outside / runner._gate_worktree_path().name
    chosen.mkdir()
    (chosen / "keep.txt").write_bytes(b"precious too")
    runner._owned_worktrees.add(str(repo / "tmp" / chosen.name))
    assert runner._remove_worktree(repo / "tmp" / chosen.name) is True
    assert (chosen / "keep.txt").read_bytes() == b"precious too"


@needs_pre_commit
def test_a_failed_add_never_touches_another_calls_live_worktree(
    tmp_path: Path,
) -> None:
    repo = _make_repo(tmp_path, _PASSING_CONFIG)
    live = repo / "tmp" / f"prepush-gate-{os.getpid()}-live0000"
    _add_worktree(repo, live)
    (live / "marker.txt").write_text("in use by another call\n")

    runner = _runner(repo)
    _intercepting_run_command(runner, ["worktree", "add"], (128, "", "fatal: boom"))
    assert runner.check_pre_commit_hooks() is False

    assert (live / "marker.txt").exists()
    assert _registered(repo, live)


# --- F3: a relative repo_root is made absolute -------------------------------


@needs_pre_commit
def test_relative_repo_root_creates_and_removes_the_worktree_in_the_repo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target_root = tmp_path / "target"
    target_root.mkdir()
    repo = _make_repo(target_root, _PASSING_CONFIG)
    monkeypatch.chdir(tmp_path)
    runner = local_validation.ValidationRunner(
        verbose=False, repo_root=Path("target") / "repo"
    )
    assert runner.repo_root.is_absolute()

    assert runner.check_pre_commit_hooks() is True
    assert runner.errors == []
    assert not (repo / "repo").exists(), "worktree created relative to the wrong dir"
    assert "prepush-gate-" not in _git(repo, "worktree", "list")
    assert not list((repo / "tmp").glob("prepush-gate-*"))


# --- F6: the repo-env variable list is discovered once per process -----------


def test_repo_env_var_list_is_discovered_once_per_process(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: List[int] = []

    def counting() -> List[str]:
        calls.append(1)
        return ["GIT_DIR"]

    monkeypatch.setattr(local_validation, "_discover_repo_env_vars", counting)
    for _ in range(3):
        local_validation.sanitized_git_env()
    assert len(calls) == 1
