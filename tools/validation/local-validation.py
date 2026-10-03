#!/usr/bin/env python3
"""
Local Validation Script - Pre-Push Validation for AI-First SDLC

This script mirrors CI/CD checks locally to prevent push-fail-fix cycles.
Run this before every commit to ensure code quality.

Usage:
    python tools/validation/local-validation.py           # Full validation
    python tools/validation/local-validation.py --syntax  # Syntax only
    python tools/validation/local-validation.py --quick   # Fast checks only
    python tools/validation/local-validation.py --pre-push # Pre-push validation
"""

import ast
import functools
import os
import shutil
import subprocess
import hashlib
import re
import signal
import sys
import threading
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import argparse
import time


#: Directory names never worth walking: gitignored scratch (`tmp/` — the
#: location CLAUDE.md mandates for scratch work), vendored dependencies, and
#: build caches. Files under these cannot be pushed, so failing a pre-push
#: gate on them blocks a legitimate push for no benefit.
_SKIP_DIRS = frozenset({"tmp", "node_modules", "__pycache__", "venv", "build", "dist"})

#: Paths whose git index entries must be byte-for-byte stable across a
#: ``--pre-push`` run (verbatim assessment evidence).
_PROTECTED_PATHS = ("research/poker-capstone",)

#: Seconds allowed for the pre-commit gate; the first run in a fresh
#: worktree may have to install every hook environment.
_PRE_COMMIT_TIMEOUT = 1800

#: Seconds to wait for output to drain after a timed-out command's process
#: group has been killed, before giving up on it.
_POST_KILL_TIMEOUT = 10


#: Repository-selection variables (the fallback for ``git rev-parse
#: --local-env-vars``). Inherited from a git hook they override the working
#: directory of every child git/pre-commit process and point it at the
#: developer's MAIN checkout.
_FALLBACK_REPO_ENV_VARS = (
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_COMMON_DIR",
    "GIT_CONFIG",
    "GIT_CONFIG_PARAMETERS",
    "GIT_CONFIG_COUNT",
    "GIT_DIR",
    "GIT_GRAFT_FILE",
    "GIT_IMPLICIT_WORK_TREE",
    "GIT_INDEX_FILE",
    "GIT_NO_REPLACE_OBJECTS",
    "GIT_OBJECT_DIRECTORY",
    "GIT_PREFIX",
    "GIT_REPLACE_REF_BASE",
    "GIT_SHALLOW_FILE",
    "GIT_WORK_TREE",
)

#: Never removed: these isolate configuration, they do not select a repository.
_KEPT_GIT_ENV_VARS = frozenset({"GIT_CONFIG_GLOBAL", "GIT_CONFIG_NOSYSTEM"})


def _discover_repo_env_vars() -> Optional[List[str]]:
    """Ask git for its repository-local variables; None if it cannot say."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--local-env-vars"],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    names = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    return names or None


@functools.lru_cache(maxsize=1)
def _repo_env_var_names() -> frozenset:
    """The variable names to strip, computed once per process.

    The list is a property of the installed git, not of the call, so asking
    git for it on every command would double the process count of the gate.
    Tests that patch ``_discover_repo_env_vars`` must call
    ``_repo_env_var_names.cache_clear()``.
    """
    return frozenset(_discover_repo_env_vars() or ()) | frozenset(
        _FALLBACK_REPO_ENV_VARS
    )


def sanitized_git_env() -> Dict[str, str]:
    """The current environment minus repository-selection variables.

    Git documents that these must be cleared when operating on another
    worktree or repository; every git and pre-commit child of the gate gets
    this environment so ``cwd`` alone decides which repository is used.
    """
    names = set(_repo_env_var_names())
    names -= _KEPT_GIT_ENV_VARS
    return {key: value for key, value in os.environ.items() if key not in names}


class GateTerminated(BaseException):
    """Raised from the SIGTERM handler so ``finally`` blocks clean up.

    Derives from BaseException so no ``except Exception`` swallows it.
    """


#: Held for the whole of ``check_pre_commit_hooks`` so concurrent gate calls
#: in one process queue instead of interleaving (they would otherwise share
#: the process-wide SIGTERM disposition and the ``tmp/`` directory).
_GATE_LOCK = threading.Lock()

#: The only names the gate ever deletes: ``tmp/prepush-gate-<pid>-<8 hex>``.
_GATE_WORKTREE_NAME = re.compile(r"^prepush-gate-\d+-[0-9a-f]{8}$")


class _SigtermScope:
    """SIGTERM handling for ONE gate call; holds no module-level state.

    POSIX main thread only: elsewhere (Windows, worker threads) it installs
    nothing and every method is a no-op. The scheme is mask-based, not
    flag-based:

    * the handler blocks further SIGTERM for the thread, then raises
      ``GateTerminated`` so ``finally`` blocks run; in a SINGLE-THREADED
      process a second signal stays pending in the kernel instead of
      interrupting the unwinding (``pthread_sigmask`` is per thread: with
      another live thread that has SIGTERM unmasked, a second SIGTERM before
      cleanup begins can raise ``GateTerminated`` again; the CLI is
      single-threaded, so this is theoretical there);
    * cleanup blocks SIGTERM first, restores the PREVIOUS handler, and only
      then unblocks, so a SIGTERM that arrived at any point in cleanup
      (including one with no earlier signal) is delivered to the original
      disposition afterwards and is never dropped. The one exception is a
      previous disposition of SIG_IGN: while the gate runs, the gate's handler
      REPLACES it, so a SIGTERM during the gate raises ``GateTerminated``; the
      original SIG_IGN is restored afterwards, so a SIGTERM that is still
      pending at that point is discarded by the caller's choice.

    Residual window: it runs from the end of the ``try`` body until the
    cleanup flag is set (entering the ``finally``, the ``begin_cleanup`` call
    and its conditional); several interpreter checks fall in that span. A
    SIGTERM whose Python handler runs there raises ``GateTerminated`` before
    the cleanup is in place, which would skip that call's cleanup. This is
    theoretical for a developer-run gate and is not closed. Children spawned
    during cleanup inherit the blocked mask.

    Known limit: the "kill live children" step only affects children still
    registered when cleanup begins; ``run_command``'s own ``finally`` removes
    a process from the live list once its call ends, so in the single-thread
    case there is usually nothing left to kill. A signal landing after
    ``Popen`` returns but before the ``try`` in ``_communicate`` can orphan the
    child. Theoretical; a small follow-up is to kill the group in
    ``run_command``'s ``finally`` when unwinding with an exception.
    """

    def __init__(self) -> None:
        self.active = (
            os.name != "nt"
            and hasattr(signal, "pthread_sigmask")
            and threading.current_thread() is threading.main_thread()
        )
        self._previous: object = signal.SIG_DFL
        self._installed = False
        self._was_blocked = False
        self._cleaning = False
        self._deferred = False

    def _handler(self, signum: int, frame: object) -> None:
        signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGTERM})
        if self._cleaning:
            # Raised too late to be useful (cleanup already began): keep it
            # for delivery to the original disposition after the restore.
            self._deferred = True
            return
        raise GateTerminated(f"received signal {signum}")

    def install(self) -> None:
        if not self.active:
            return
        # Blocked while swapping so no signal can land between the swap and
        # the bookkeeping; it is delivered (to our handler) on unblock.
        old_mask = signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGTERM})
        self._was_blocked = signal.SIGTERM in old_mask
        try:
            self._previous = signal.signal(signal.SIGTERM, self._handler)
            self._installed = True
        finally:
            if not self._was_blocked:
                signal.pthread_sigmask(signal.SIG_UNBLOCK, {signal.SIGTERM})

    def begin_cleanup(self) -> None:
        if not self.active:
            return
        self._cleaning = True
        signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGTERM})

    def restore_handler(self) -> None:
        if not (self.active and self._installed):
            return
        previous = self._previous
        handler: Any = signal.SIG_DFL if previous is None else previous
        signal.signal(signal.SIGTERM, handler)
        self._installed = False
        if self._deferred and previous != signal.SIG_IGN:
            os.kill(os.getpid(), signal.SIGTERM)  # pending until unblocked

    def unblock(self) -> None:
        if self.active and not self._was_blocked:
            signal.pthread_sigmask(signal.SIG_UNBLOCK, {signal.SIGTERM})


class ValidationRunner:
    """Runs comprehensive local validation checks"""

    def __init__(self, verbose: bool = False, repo_root: Optional[Path] = None):
        self.verbose = verbose
        # Absolute: git resolves paths against cwd=repo_root while Path.exists()
        # resolves against the process cwd; a relative root would disagree.
        self.repo_root = Path(
            repo_root if repo_root is not None else Path.cwd()
        ).resolve()
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.start_time = time.time()
        self._owned_worktrees: set = set()
        self._live_procs: List["subprocess.Popen[str]"] = []

    def log(self, message: str, level: str = "INFO") -> None:
        """Log messages with timestamps"""
        if self.verbose or level in ["ERROR", "WARNING"]:
            timestamp = time.strftime("%H:%M:%S")
            prefix = {"INFO": "ℹ️", "WARNING": "⚠️", "ERROR": "❌", "SUCCESS": "✅"}
            print(f"[{timestamp}] {prefix.get(level, '')} {message}")

    def run_command(
        self,
        cmd: List[str],
        description: str = "",
        cwd: Optional[Path] = None,
        timeout: int = 300,
    ) -> Tuple[int, str, str]:
        """Run shell command and capture output (default 5 minute timeout).

        On POSIX the child runs in its own session, and on timeout (or any
        interruption) the WHOLE process group is killed, so grandchildren such
        as pre-commit hook processes cannot outlive the command or the
        worktree it was running in.
        """
        self.log(f"Running: {' '.join(cmd)}")
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                cwd=cwd,
                env=sanitized_git_env(),
                start_new_session=os.name != "nt",
            )
        except Exception as e:
            error_msg = f"Command failed: {' '.join(cmd)} - {str(e)}"
            self.errors.append(error_msg)
            return 1, "", error_msg

        self._live_procs.append(proc)
        try:
            return self._communicate(proc, cmd, timeout)
        finally:
            if proc in self._live_procs:
                self._live_procs.remove(proc)

    def _communicate(
        self, proc: "subprocess.Popen[str]", cmd: List[str], timeout: int
    ) -> Tuple[int, str, str]:
        try:
            stdout, stderr = proc.communicate(timeout=timeout)
            return proc.returncode, stdout, stderr
        except subprocess.TimeoutExpired:
            self._kill_process_group(proc)
            try:
                proc.communicate(timeout=_POST_KILL_TIMEOUT)
            except subprocess.TimeoutExpired:
                # A descendant that called setsid (or the Windows fallback)
                # can keep the pipes open after the kill; give up cleanly.
                pass
            error_msg = f"Command timed out: {' '.join(cmd)}"
            self.errors.append(error_msg)
            return 1, "", error_msg
        except BaseException:
            self._kill_process_group(proc)
            raise

    def _kill_live_children(self) -> None:
        """Kill the process group of any child still running (cleanup step)."""
        for proc in list(self._live_procs):
            try:
                if proc.poll() is None:
                    self._kill_process_group(proc)
            except Exception:  # cleanup must continue to the worktree removal
                pass

    @staticmethod
    def _kill_process_group(proc: "subprocess.Popen[str]") -> None:
        """Kill the child and, on POSIX, every process in its group."""
        try:
            if os.name == "nt":
                proc.kill()
            else:
                os.killpg(proc.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            # The group has already exited (or is not ours to signal): there
            # is nothing left to kill, which is the outcome we want.
            pass

    def check_python_syntax(self) -> bool:
        """Check Python syntax using AST parsing"""
        self.log("🐍 Checking Python syntax...", "INFO")

        python_files = []
        for root, dirs, files in os.walk("."):
            # Skip hidden dirs, test dirs, and scratch/vendored dirs that are
            # gitignored and so can never be pushed. `tmp/` matters especially:
            # CLAUDE.md directs all scratch work there and .gitignore excludes
            # it, so scanning it blocks a push on files that are not part of
            # the repo — e.g. deliberately-captured malformed model output.
            dirs[:] = [
                d
                for d in dirs
                if not d.startswith(".") and "test-" not in d and d not in _SKIP_DIRS
            ]
            for file in files:
                if file.endswith(".py"):
                    python_files.append(os.path.join(root, file))

        syntax_errors = []
        for file_path in python_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    source = f.read()
                ast.parse(source, filename=file_path)
                self.log(f"✓ {file_path}")
            except SyntaxError as e:
                error_msg = (
                    f"SYNTAX ERROR in {file_path}:{e.lineno}:{e.offset}: {e.msg}"
                )
                syntax_errors.append(error_msg)
                self.log(error_msg, "ERROR")
            except Exception as e:
                error_msg = f"FILE ERROR in {file_path}: {str(e)}"
                syntax_errors.append(error_msg)
                self.log(error_msg, "ERROR")

        if syntax_errors:
            self.errors.extend(syntax_errors)
            self.log(f"Found {len(syntax_errors)} syntax errors", "ERROR")
            return False
        else:
            self.log(
                f"All {len(python_files)} Python files have valid syntax", "SUCCESS"
            )
            return True

    def check_pre_commit_hooks(self) -> bool:
        """Run pre-commit hooks without mutating the working checkout.

        Hooks such as black or pretty-format-json rewrite files in place, which
        previously rewrote tracked files (including byte-identical evidence)
        during ``--pre-push``. The hooks therefore run in a throwaway detached
        worktree of HEAD and the worktree is always removed afterwards.

        This validates the COMMITTED state (HEAD), not uncommitted edits:
        commit first, then run the gate. Any non-zero exit or diff output is
        a failure and the hook output is included in the report.
        """
        self.log(
            "🪝 Running pre-commit hooks (HEAD, in a throwaway worktree)...", "INFO"
        )

        with _GATE_LOCK:
            return self._run_gate_locked()

    def _run_gate_locked(self) -> bool:
        tmp_error = self._tmp_dir_error()
        if tmp_error:
            self.errors.append(f"Pre-commit hooks failed: {tmp_error}")
            return False
        worktree = self._gate_worktree_path()
        hook_result: Optional[Tuple[int, str, str]] = None
        removal_failed = False
        claimed = False
        scope = _SigtermScope()
        try:
            # Inside the try: a SIGTERM delivered when install() unblocks must
            # still reach the cleanup below.
            scope.install()
            if os.path.lexists(worktree):
                self.errors.append(
                    f"Pre-commit hooks failed: {worktree} already exists; "
                    "refusing to use it"
                )
                return False
            claimed = True
            # A registration left by a killed earlier run whose directory is
            # gone would make `git worktree add` refuse; this call's path is
            # unique, but prune keeps the registry tidy.
            self.run_command(["git", "worktree", "prune"], cwd=self.repo_root)
            added, _, add_err = self.run_command(
                ["git", "worktree", "add", "--detach", str(worktree), "HEAD"],
                cwd=self.repo_root,
            )
            if added != 0:
                self.errors.append(
                    f"Pre-commit hooks failed: cannot create worktree: {add_err}"
                )
                return False
            hook_result = self.run_command(
                ["pre-commit", "run", "--all-files", "--show-diff-on-failure"],
                cwd=worktree,
                timeout=_PRE_COMMIT_TIMEOUT,
            )
        finally:
            # Order matters and is fixed: block SIGTERM, kill the hook's
            # process group (only children still registered; see the
            # _SigtermScope known limit), remove the worktree, restore the
            # previous handler, unblock. Each step is nested so a failure
            # cannot skip a later one.
            scope.begin_cleanup()
            try:
                self._kill_live_children()
            finally:
                try:
                    if claimed:
                        removal_failed = self._remove_worktree(worktree)
                finally:
                    try:
                        scope.restore_handler()
                    finally:
                        scope.unblock()

        if hook_result is None:
            # Every early exit above returns, so this is unreachable today;
            # fail closed rather than read an unassigned result.
            self.errors.append("Pre-commit hooks failed: the hooks did not run")
            return False
        returncode, stdout, stderr = hook_result
        output = "\n".join(part for part in (stdout, stderr) if part)
        if returncode != 0 or "diff --git" in output:
            self.errors.append(f"Pre-commit hooks failed:\n{output}")
            self.log("Pre-commit hooks failed", "ERROR")
            if output:
                self.log(output, "ERROR")
            return False

        if removal_failed:
            return False

        self.log("Pre-commit hooks passed", "SUCCESS")
        return True

    def _tmp_dir_error(self) -> Optional[str]:
        """Why ``<repo>/tmp`` cannot safely hold the worktree, or None.

        The "symlinked ancestor" branch is unreachable (``repo_root`` is
        already resolved, so only ``tmp`` itself can be a link); it is kept as
        a harmless defensive check.
        """
        tmp = self.repo_root / "tmp"
        if os.path.islink(tmp):
            return f"{tmp} is a symlink; refusing to create a worktree outside the repo"
        if os.path.lexists(tmp) and os.path.realpath(tmp) != os.path.join(
            os.path.realpath(self.repo_root), "tmp"
        ):
            return f"{tmp} resolves outside the repo (symlinked ancestor); refusing"
        return None

    def _gate_worktree_path(self) -> Path:
        """A resolved path unique to one gate call, recorded as owned by this runner.

        The pid alone is shared by threads of one process, and a failed
        ``add`` for one call must never remove another call's live worktree.
        Ownership is tracked per runner (the set of paths minted here), not
        per call. Only paths minted here are ever deleted by
        ``_remove_worktree``.
        """
        name = f"prepush-gate-{os.getpid()}-{uuid.uuid4().hex[:8]}"
        path = Path(os.path.realpath(self.repo_root)) / "tmp" / name
        self._owned_worktrees.add(str(path))
        return path

    def _removal_refusal(self, worktree: Path) -> Optional[str]:
        """Which safety check ``worktree`` fails, or None if deletion is allowed."""
        repo = os.path.realpath(self.repo_root)
        tmp = os.path.join(repo, "tmp")
        path = os.path.abspath(worktree)
        if os.path.islink(path):
            return "it is a symlink"
        if os.path.realpath(os.path.dirname(path)) != tmp or os.path.islink(tmp):
            return f"it is not directly under the repo's own tmp/ ({tmp})"
        if not _GATE_WORKTREE_NAME.match(os.path.basename(path)):
            return "its name does not match prepush-gate-<pid>-<8 hex>"
        real = os.path.realpath(path)
        if real == repo or repo.startswith(real + os.sep):
            return "it is, or contains, the repository root"
        if path not in self._owned_worktrees:
            return "it was not the path chosen by this gate call (ownership)"
        return None

    def _registered_worktrees(self) -> Optional[set]:
        """Real paths git has registered as worktrees; None if git cannot say."""
        returncode, stdout, _ = self.run_command(
            ["git", "worktree", "list", "--porcelain"], cwd=self.repo_root
        )
        if returncode != 0:
            return None
        return {
            os.path.realpath(line[len("worktree ") :])
            for line in stdout.splitlines()
            if line.startswith("worktree ")
        }

    def _remove_worktree(self, worktree: Path) -> bool:
        """Remove whatever exists of the throwaway worktree; True if it failed.

        ``worktree`` must be a path this runner minted under ``<repo>/tmp`` with the
        gate's name pattern and not a symlink; otherwise nothing is touched and
        True is returned with an error. Handles creation that was
        partial, interrupted, or never happened. A creation killed mid-checkout
        leaves a registration LOCKED with the reason "initializing" (git's own
        cleanup never ran), which a plain ``remove --force`` and ``prune``
        both refuse, so on failure it unlocks, retries, then deletes the
        directory and prunes. It catches ``Exception`` (it runs in ``finally``
        and must not mask the error being propagated); a ``KeyboardInterrupt``
        can still propagate, which is why the caller nests the later steps.
        """
        refusal = self._removal_refusal(worktree)
        if refusal:
            self.errors.append(
                f"Pre-commit hooks: refusing to remove {worktree}: {refusal}; "
                "nothing was touched"
            )
            self.log(self.errors[-1], "ERROR")
            return True
        failed = False
        try:
            target = os.path.realpath(worktree)

            def present() -> bool:
                registered = self._registered_worktrees()
                return worktree.exists() or (
                    registered is not None and target in registered
                )

            if present():
                removed, _, remove_err = self.run_command(
                    ["git", "worktree", "remove", "--force", str(worktree)],
                    cwd=self.repo_root,
                )
                if removed != 0:
                    self.run_command(
                        ["git", "worktree", "unlock", str(worktree)],
                        cwd=self.repo_root,
                    )
                    removed, _, remove_err = self.run_command(
                        ["git", "worktree", "remove", "--force", str(worktree)],
                        cwd=self.repo_root,
                    )
                if removed != 0:
                    shutil.rmtree(worktree, ignore_errors=True)
                    self.run_command(["git", "worktree", "prune"], cwd=self.repo_root)
                    if present():
                        failed = True
                        self.errors.append(
                            f"Pre-commit hooks: could not remove throwaway worktree "
                            f"{worktree}: {remove_err.strip()}"
                        )
                        self.log(self.errors[-1], "ERROR")
            self.run_command(["git", "worktree", "prune"], cwd=self.repo_root)
        except Exception as exc:  # cleanup must not mask the original error
            failed = True
            self.errors.append(f"Pre-commit hooks: worktree cleanup failed: {exc}")
        return failed

    def _git_output(self, args: List[str]) -> str:
        result = subprocess.run(
            ["git", *args],
            cwd=self.repo_root,
            capture_output=True,
            text=True,
            env=sanitized_git_env(),
        )
        return result.stdout

    @staticmethod
    def _hash_file(path: Path) -> str:
        """SHA-256 of a file, read in chunks."""
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1 << 20), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def _tree_snapshot(self) -> Dict[str, str]:
        """Capture the git state a validation run must not change.

        For every path git reports as modified or staged (tracked), records
        its status code and a content hash. For UNTRACKED paths
        (``--untracked-files=all`` so a new file inside an already-untracked
        directory is seen individually) only the path is recorded, not the
        content: the gate's own output may legitimately be redirected into an
        untracked file inside the repo (``... | tee command-runs/x.log``) and
        that file grows during the run. The index entries of the protected
        evidence paths are hashed too.

        Limits: untracked file CONTENT and gitignored files are not covered
        (``tmp/`` scratch is deliberately allowed), and the tripwire cannot
        tell WHO changed the tree, so a concurrent writer to the same checkout
        (an editor, another agent) that adds or removes untracked paths, or
        edits tracked files, during the run would be blamed on the gate.
        """
        snapshot: Dict[str, str] = {}
        raw = self._git_output(["status", "--porcelain", "-z", "--untracked-files=all"])
        records = raw.split("\0")
        i = 0
        while i < len(records):
            record = records[i]
            i += 1
            if len(record) < 4:
                continue
            code, path = record[:2], record[3:]
            if code[0] in "RC" or code[1] in "RC":
                i += 1  # the following record is the rename/copy source
            if code == "??":
                snapshot[f"untracked:{path}"] = "present"
                continue
            target = self.repo_root / path
            digest = self._hash_file(target) if target.is_file() else "-"
            snapshot[f"file:{path}"] = f"{code}:{digest}"
        for path in _PROTECTED_PATHS:
            snapshot[f"index:{path}"] = hashlib.sha256(
                self._git_output(["ls-files", "-s", "--", path]).encode("utf-8")
            ).hexdigest()
        return snapshot

    def _tripwire_report(
        self, before: Dict[str, str], after: Dict[str, str]
    ) -> List[str]:
        """Describe how the tree changed between two snapshots (empty if none).

        Only the DIFFERENCE is reported: files that were already dirty before
        the run and are unchanged are not mentioned.
        """
        problems: List[str] = []
        changed_files = sorted(
            key[5:]
            for key in set(before) | set(after)
            if key.startswith("file:") and before.get(key) != after.get(key)
        )
        if changed_files:
            problems.append("files changed during the run: " + ", ".join(changed_files))
        changed_untracked = sorted(
            key[10:]
            for key in set(before) | set(after)
            if key.startswith("untracked:") and before.get(key) != after.get(key)
        )
        if changed_untracked:
            problems.append(
                "untracked files appeared or disappeared during the run: "
                + ", ".join(changed_untracked)
            )
        for key, value in before.items():
            if key.startswith("index:") and after.get(key) != value:
                problems.append(f"{key[6:]} index entries changed")
        return problems

    def check_technical_debt(self) -> bool:
        """Check technical debt using framework tools"""
        self.log("🔍 Checking technical debt...", "INFO")

        # Use the pipeline's technical debt check which properly applies
        # framework policy
        returncode, stdout, stderr = self.run_command(
            [
                "python",
                "tools/validation/validate-pipeline.py",
                "--checks",
                "technical-debt",
            ]
        )

        if returncode != 0:
            self.errors.append("Technical debt check failed")
            self.log("Technical debt violations found", "ERROR")
            if stderr:
                self.log(stderr, "ERROR")
            return False
        else:
            self.log("Technical debt check passed", "SUCCESS")
            return True

    def check_architecture_compliance(self) -> bool:
        """Check architecture documentation compliance"""
        self.log("🏗️ Checking architecture compliance...", "INFO")

        returncode, stdout, stderr = self.run_command(
            ["python", "tools/validation/validate-architecture.py"]
        )

        if returncode not in [0, 2]:  # 0=success, 2=bootstrap mode ok
            self.errors.append("Architecture validation failed")
            self.log("Architecture validation failed", "ERROR")
            if stderr:
                self.log(stderr, "ERROR")
            return False
        else:
            self.log("Architecture validation passed", "SUCCESS")
            return True

    def check_type_safety(self) -> bool:
        """Check type safety with mypy"""
        self.log("🔒 Checking type safety...", "INFO")

        returncode, stdout, stderr = self.run_command(
            [
                "python",
                "tools/validation/validate-pipeline.py",
                "--checks",
                "type-safety",
            ]
        )

        if returncode != 0:
            self.warnings.append("Type safety issues found")
            self.log("Type safety issues found", "WARNING")
            return True  # Don't fail build on warnings
        else:
            self.log("Type safety check passed", "SUCCESS")
            return True

    def check_security(self) -> bool:
        """Run security checks"""
        self.log("🛡️ Running security checks...", "INFO")

        returncode, stdout, stderr = self.run_command(
            ["python", "tools/validation/validate-pipeline.py", "--checks", "security"]
        )

        if returncode != 0:
            self.errors.append("Security vulnerabilities found")
            self.log("Security vulnerabilities found", "ERROR")
            return False
        else:
            self.log("Security checks passed", "SUCCESS")
            return True

    def check_logging_compliance(self) -> bool:
        """Check logging compliance using framework tools"""
        self.log("📝 Checking logging compliance...", "INFO")

        returncode, stdout, stderr = self.run_command(
            [
                "python",
                "tools/validation/check-logging-compliance.py",
                ".",
                "--threshold",
                "0",
            ]
        )

        if returncode != 0:
            self.errors.append("Logging compliance check failed")
            self.log("Logging compliance violations found", "ERROR")
            if stderr:
                self.log(stderr, "ERROR")
            return False
        else:
            self.log("Logging compliance check passed", "SUCCESS")
            return True

    def check_static_analysis(self) -> bool:
        """Run CodeQL-style static analysis checks"""
        self.log("🔍 Running static analysis checks...", "INFO")

        # Check for argument count mismatches and other static analysis issues
        python_files = list(Path("tools").rglob("*.py"))
        issues_found = []

        for file_path in python_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Parse the AST to check for potential issues
                tree = ast.parse(content)

                # Look for potential argument count issues
                for node in ast.walk(tree):
                    if isinstance(node, ast.Call):
                        # This is a simplified check - in practice would need
                        # more sophisticated analysis
                        if hasattr(node.func, "attr"):
                            func_name = node.func.attr
                            if (
                                func_name in ["save_context", "setup"]
                                and len(node.args) == 1
                            ):
                                issues_found.append(
                                    f"{file_path}:{node.lineno}: Potential argument count issue in {func_name} call"
                                )

                    elif isinstance(node, ast.ClassDef):
                        # Check for class instantiation issues
                        for child in ast.walk(node):
                            if isinstance(child, ast.Call) and hasattr(
                                child.func, "id"
                            ):
                                class_name = child.func.id
                                if (
                                    class_name.endswith("Configurator")
                                    and len(child.args) > 4
                                ):
                                    msg = (
                                        f"{file_path}:{child.lineno}: "
                                        f"Potential argument order issue in {class_name} instantiation"
                                    )
                                    issues_found.append(msg)

            except (SyntaxError, UnicodeDecodeError) as e:
                issues_found.append(f"{file_path}: Parse error: {e}")

        if issues_found:
            self.warnings.extend(issues_found[:5])  # Limit output
            self.log(
                f"Static analysis found {len(issues_found)} potential issues", "WARNING"
            )
            for issue in issues_found[:3]:  # Show first 3 issues
                self.log(issue, "WARNING")
            return True  # Don't fail build on warnings, just report
        else:
            self.log("Static analysis checks passed", "SUCCESS")
            return True

    def run_quick_validation(self) -> bool:
        """Run only the fastest, most critical checks"""
        self.log("🚀 Running quick validation...", "INFO")

        checks = [
            ("Syntax Check", self.check_python_syntax),
        ]

        all_passed = True
        for name, check_func in checks:
            if not check_func():
                all_passed = False

        return all_passed

    def run_pre_push_validation(self) -> bool:
        """Run comprehensive pre-push validation"""
        self.log("📤 Running pre-push validation...", "INFO")

        checks = [
            ("Syntax Check", self.check_python_syntax),
            ("Pre-commit Hooks", self.check_pre_commit_hooks),
            ("Technical Debt", self.check_technical_debt),
            ("Architecture", self.check_architecture_compliance),
            ("Type Safety", self.check_type_safety),
            ("Security", self.check_security),
            ("Logging Compliance", self.check_logging_compliance),
            ("Static Analysis", self.check_static_analysis),
        ]

        before = self._tree_snapshot()
        all_passed = True
        for name, check_func in checks:
            self.log(f"Running {name}...", "INFO")
            if not check_func():
                all_passed = False

        problems = self._tripwire_report(before, self._tree_snapshot())
        if problems:
            all_passed = False
            self.errors.append(
                "TRIPWIRE: the pre-push run modified the working tree: "
                + " | ".join(problems)
            )
            self.log(self.errors[-1], "ERROR")

        return all_passed

    def run_full_validation(self) -> bool:
        """Run all validation checks"""
        self.log("🔍 Running full validation...", "INFO")
        return self.run_pre_push_validation()

    def print_summary(self, success: bool) -> None:
        """Print validation summary"""
        duration = time.time() - self.start_time

        print(f"\n{'='*60}")
        print(f"{'🎯 VALIDATION SUMMARY':^60}")
        print(f"{'='*60}")

        if success:
            print(f"✅ {'VALIDATION PASSED':^58} ✅")
        else:
            print(f"❌ {'VALIDATION FAILED':^58} ❌")

        print(f"\nDuration: {duration:.1f} seconds")
        print(f"Errors: {len(self.errors)}")
        print(f"Warnings: {len(self.warnings)}")

        if self.errors:
            print(f"\n❌ ERRORS ({len(self.errors)}):")
            for i, error in enumerate(self.errors, 1):
                print(f"   {i}. {error}")

        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for i, warning in enumerate(self.warnings, 1):
                print(f"   {i}. {warning}")

        if success:
            print("\n🚀 Ready to push! All validation checks passed.")
        else:
            print("\n🛑 DO NOT PUSH! Fix errors before committing.")
            print("💡 Tip: Run with --syntax first to fix basic issues quickly.")

        print(f"{'='*60}")


def main():
    parser = argparse.ArgumentParser(
        description="Local validation for AI-First SDLC projects",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tools/validation/local-validation.py           # Full validation
  python tools/validation/local-validation.py --syntax  # Syntax only
  python tools/validation/local-validation.py --quick   # Fast checks
  python tools/validation/local-validation.py --pre-push # Pre-push validation
        """,
    )

    parser.add_argument(
        "--syntax", action="store_true", help="Check Python syntax only"
    )
    parser.add_argument(
        "--quick", action="store_true", help="Run quick validation only"
    )
    parser.add_argument(
        "--pre-push", action="store_true", help="Run pre-push validation"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    # Change to repository root
    repo_root = Path(__file__).parent.parent.parent
    os.chdir(repo_root)

    validator = ValidationRunner(verbose=args.verbose, repo_root=repo_root)

    try:
        if args.syntax:
            success = validator.check_python_syntax()
        elif args.quick:
            success = validator.run_quick_validation()
        elif args.pre_push:
            success = validator.run_pre_push_validation()
        else:
            success = validator.run_full_validation()

        validator.print_summary(success)
        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n\n⚠️ Validation interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Validation script error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
