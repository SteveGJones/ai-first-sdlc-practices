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
