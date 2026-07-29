"""docker-compose lifecycle for a submitted implementation. See
exemplar/docs/design-server.md "Packaging contract" for what's required
of the implementation's docker-compose.yml (a service named `server`
exposing container port 8000)."""

from __future__ import annotations

import subprocess
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path


class HarnessError(Exception):
    """Raised for anything that stops the harness before scoring can
    happen at all — a build failure, a health-check timeout, a malformed
    compose file. Distinct from a scenario ASSERTION failure (see
    scenarios.py), which means the harness ran fine and found a bug."""


@dataclass
class RunningStack:
    impl_dir: Path
    project_name: str
    base_url: str
    client_url: str | None = None


def _run(cmd: list[str], cwd: Path, timeout: int) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)


def bring_up(
    impl_dir: Path,
    project_name: str,
    build_timeout_s: int = 900,
    health_timeout_s: int = 60,
) -> RunningStack:
    compose_file = impl_dir / "docker-compose.yml"
    if not compose_file.exists():
        raise HarnessError(f"no docker-compose.yml at {impl_dir}")

    build = _run(
        ["docker", "compose", "-p", project_name, "build"],
        cwd=impl_dir,
        timeout=build_timeout_s,
    )
    if build.returncode != 0:
        raise HarnessError(f"docker compose build failed:\n{build.stderr[-4000:]}")

    up = _run(
        ["docker", "compose", "-p", project_name, "up", "-d"],
        cwd=impl_dir,
        timeout=build_timeout_s,
    )
    if up.returncode != 0:
        raise HarnessError(f"docker compose up failed:\n{up.stderr[-4000:]}")

    port_result = _run(
        ["docker", "compose", "-p", project_name, "port", "server", "8000"],
        cwd=impl_dir,
        timeout=20,
    )
    if port_result.returncode != 0 or not port_result.stdout.strip():
        tear_down(impl_dir, project_name)
        raise HarnessError(
            "could not discover the 'server' service's host port for container "
            f"port 8000 — is the compose file's server service named exactly "
            f"'server'? docker compose port output: {port_result.stdout!r} "
            f"stderr: {port_result.stderr!r}"
        )
    host_port = port_result.stdout.strip().rsplit(":", 1)[-1]
    base_url = f"http://localhost:{host_port}"

    deadline = time.time() + health_timeout_s
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(f"{base_url}/healthz", timeout=3) as resp:
                if resp.status == 200:
                    return RunningStack(
                        impl_dir=impl_dir,
                        project_name=project_name,
                        base_url=base_url,
                        client_url=_discover_client_url(impl_dir, project_name),
                    )
        except (urllib.error.URLError, OSError) as exc:
            last_error = exc
        time.sleep(1)

    tear_down(impl_dir, project_name)
    raise HarnessError(
        f"server never became healthy within {health_timeout_s}s: {last_error}"
    )


def _discover_client_url(
    impl_dir: Path, project_name: str, wait_s: int = 15
) -> str | None:
    """Best-effort — a client is optional per HARNESS-CONTRACT.md, so
    absence here is not a HarnessError, just None (callers that need a
    client skip/fail their own scenarios, not bring_up itself). Waits
    briefly for it to actually serve something, since unlike the server
    there's no required /healthz to gate on here."""
    port_result = _run(
        ["docker", "compose", "-p", project_name, "port", "client", "80"],
        cwd=impl_dir,
        timeout=20,
    )
    if port_result.returncode != 0 or not port_result.stdout.strip():
        return None
    host_port = port_result.stdout.strip().rsplit(":", 1)[-1]
    client_url = f"http://localhost:{host_port}"

    deadline = time.time() + wait_s
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(client_url, timeout=3) as resp:
                if resp.status == 200:
                    return client_url
        except (urllib.error.URLError, OSError):
            pass
        time.sleep(1)
    return client_url  # discovered but never confirmed serving — let the caller's own checks decide


def tear_down(impl_dir: Path, project_name: str) -> None:
    _run(
        ["docker", "compose", "-p", project_name, "down", "-v"],
        cwd=impl_dir,
        timeout=60,
    )
