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
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple

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

    runner.check_technical_debt = mutate  # type: ignore[method-assign]
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

    runner.check_security = scratch  # type: ignore[method-assign]
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

    runner.check_technical_debt = mutate  # type: ignore[method-assign]
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

    runner.check_security = add_file  # type: ignore[method-assign]
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

    runner.check_type_safety = rewrite  # type: ignore[method-assign]
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

    runner.check_type_safety = stage_rewrite  # type: ignore[method-assign]
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

    def fake(cmd: List[str], *args: object, **kwargs: object) -> Tuple:
        if all(part in cmd for part in needle):
            return result
        return real(cmd, *args, **kwargs)  # type: ignore[arg-type]

    runner.run_command = fake  # type: ignore[method-assign]


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
def test_gate_reports_worktree_remove_failure_with_path(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path, _PASSING_CONFIG)
    runner = _runner(repo)
    _intercepting_run_command(runner, ["worktree", "remove"], (1, "", "locked"))

    try:
        assert runner.check_pre_commit_hooks() is False
        removal = [e for e in runner.errors if "could not remove" in e]
        assert removal and "prepush-gate-" in removal[0] and "locked" in removal[0]
    finally:
        _git(repo, "worktree", "remove", "--force", *_leftover(repo))


def _leftover(repo: Path) -> List[str]:
    return [str(p) for p in (repo / "tmp").glob("prepush-gate-*")][:1]


@needs_pre_commit
def test_gate_survives_a_stale_registered_worktree_at_the_same_path(
    tmp_path: Path,
) -> None:
    repo = _make_repo(tmp_path, _PASSING_CONFIG)
    stale = repo / "tmp" / f"prepush-gate-{os.getpid()}"
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
        entry: sleep 31337
        language: system
        pass_filenames: false
        always_run: true
"""


def _sleepers() -> str:
    result = subprocess.run(
        ["pgrep", "-f", "sleep 31337"], capture_output=True, text=True
    )
    return result.stdout.strip()


@needs_pre_commit
@pytest.mark.skipif(os.name == "nt", reason="process groups are POSIX-only")
@pytest.mark.skipif(shutil.which("pgrep") is None, reason="pgrep not available")
def test_gate_timeout_fails_removes_worktree_and_kills_grandchildren(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _make_repo(tmp_path, _SLEEP_CONFIG)
    monkeypatch.setattr(local_validation, "_PRE_COMMIT_TIMEOUT", 5)
    runner = _runner(repo)
    try:
        assert runner.check_pre_commit_hooks() is False
        assert any("timed out" in e for e in runner.errors)
        assert "prepush-gate-" not in _git(repo, "worktree", "list")
        assert not list((repo / "tmp").glob("prepush-gate-*"))
        assert _sleepers() == "", "hook grandchild outlived the gate"
    finally:
        subprocess.run(["pkill", "-f", "sleep 31337"], check=False)


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

    runner.check_security = keep_logging  # type: ignore[method-assign]
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

    runner.check_security = add_file  # type: ignore[method-assign]
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

    runner.check_security = remove  # type: ignore[method-assign]
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

    runner.check_security = mutate_again  # type: ignore[method-assign]
    assert runner.run_pre_push_validation() is False
    assert any("a.txt" in e and "TRIPWIRE" in e for e in runner.errors)


def test_status_parser_skips_rename_source_when_rename_is_in_second_column(
    tmp_path: Path,
) -> None:
    repo = _make_repo(tmp_path, _PASSING_CONFIG)
    runner = _runner(repo)
    (repo / "new.txt").write_text("n\n")
    runner._git_output = lambda args: (  # type: ignore[method-assign]
        " R new.txt\0a-rather-long-rename-source.txt\0" if args[0] == "status" else ""
    )
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


@needs_pre_commit
@pytest.mark.skipif(os.name == "nt", reason="signals and process groups are POSIX")
@pytest.mark.skipif(shutil.which("pgrep") is None, reason="pgrep not available")
def test_sigterm_to_the_gate_removes_worktree_and_kills_children(
    tmp_path: Path,
) -> None:
    import signal
    import time

    repo = _make_repo(tmp_path, _SLEEP_CONFIG)
    script = tmp_path / "gate.py"
    script.write_text(_GATE_SCRIPT)
    env = dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1")
    proc = subprocess.Popen(
        [sys.executable, str(script), str(_SCRIPT), str(repo)],
        stdout=subprocess.PIPE,
        text=True,
        env=env,
    )
    try:
        assert proc.stdout is not None
        assert proc.stdout.readline().strip() == "READY"
        deadline = time.time() + 60
        while time.time() < deadline and not _sleepers():
            time.sleep(0.2)
        assert _sleepers(), "the hook never started"
        proc.send_signal(signal.SIGTERM)
        proc.wait(timeout=60)
        assert "prepush-gate-" not in _git(repo, "worktree", "list")
        assert not list((repo / "tmp").glob("prepush-gate-*"))
        assert _sleepers() == "", "hook grandchild survived SIGTERM"
    finally:
        proc.kill()
        subprocess.run(["pkill", "-f", "sleep 31337"], check=False)


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


def _create_then(runner: "local_validation.ValidationRunner", action: "object") -> None:
    """After the real `git worktree add` succeeds, run ``action`` (e.g. raise)."""
    real = runner.run_command

    def fake(cmd: List[str], *args: object, **kwargs: object) -> Tuple:
        result = real(cmd, *args, **kwargs)  # type: ignore[arg-type]
        if "worktree" in cmd and "add" in cmd:
            action()  # type: ignore[operator]
        return result

    runner.run_command = fake  # type: ignore[method-assign]


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

    def fake(cmd: List[str], *args: object, **kwargs: object) -> Tuple:
        if "worktree" in cmd and "remove" in cmd:
            raise OSError("cleanup exploded")
        return real(cmd, *args, **kwargs)  # type: ignore[arg-type]

    def boom() -> None:
        raise RuntimeError("original error")

    runner.run_command = fake  # type: ignore[method-assign]
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

def slow(cmd, *args, **kwargs):
    if "worktree" in cmd and "add" in cmd:
        # A slow git: registers the worktree, then lingers before returning.
        wrapped = ["sh", "-c", 'git worktree add --detach "$0" HEAD; sleep 31338', cmd[-2]]
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


def _slow_adders() -> str:
    result = subprocess.run(
        ["pgrep", "-f", "sleep 31338"], capture_output=True, text=True
    )
    return result.stdout.strip()


@needs_pre_commit
@pytest.mark.skipif(os.name == "nt", reason="signals and process groups are POSIX")
@pytest.mark.skipif(shutil.which("pgrep") is None, reason="pgrep not available")
def test_sigterm_during_worktree_creation_leaves_no_worktree_or_orphan(
    tmp_path: Path,
) -> None:
    import signal
    import time

    repo = _make_repo(tmp_path, _PASSING_CONFIG)
    script = tmp_path / "slow_gate.py"
    script.write_text(_SLOW_ADD_SCRIPT)
    env = dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1")
    proc = subprocess.Popen(
        [sys.executable, str(script), str(_SCRIPT), str(repo)],
        stdout=subprocess.PIPE,
        text=True,
        env=env,
    )
    try:
        assert proc.stdout is not None
        assert proc.stdout.readline().strip() == "READY"
        assert proc.stdout.readline().strip() == "ADDING"
        deadline = time.time() + 60
        while time.time() < deadline and not _slow_adders():
            time.sleep(0.1)
        assert _slow_adders(), "the slow worktree add never started"
        deadline = time.time() + 30
        while time.time() < deadline and "prepush-gate-" not in _git(
            repo, "worktree", "list"
        ):
            time.sleep(0.1)
        proc.send_signal(signal.SIGTERM)
        proc.wait(timeout=60)
        assert "prepush-gate-" not in _git(repo, "worktree", "list")
        assert not list((repo / "tmp").glob("prepush-gate-*"))
        assert _slow_adders() == "", "slow git child survived SIGTERM"
    finally:
        proc.kill()
        subprocess.run(["pkill", "-f", "sleep 31338"], check=False)
