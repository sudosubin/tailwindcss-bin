from __future__ import annotations

import os
import subprocess
import sys
import sysconfig
import time
import zipfile
from pathlib import Path

import pytest
from tailwindcss_bin import find_tailwindcss_bin

WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
PKG_ROOT = WORKSPACE_ROOT / "packages" / "tailwindcss-bin"
BASELINE_WHEELHOUSE = os.environ.get("TAILWINDCSS_BIN_BASELINE_WHEELHOUSE")


@pytest.fixture(params=["glibc", "musl"] if BASELINE_WHEELHOUSE else ["native"])
def native_cli_command(request, tmp_path, tmp_path_factory):
    if request.param == "native":
        yield [find_tailwindcss_bin()]
        return

    assert BASELINE_WHEELHOUSE is not None
    wheelhouse = Path(BASELINE_WHEELHOUSE)
    platform = "manylinux" if request.param == "glibc" else "musllinux"
    core = list(wheelhouse.glob(f"tailwindcss_bin-*-{platform}_*.whl"))
    plugins = list(wheelhouse.glob("*-none-any.whl"))
    assert len(core) == 1, core
    assert len(plugins) == 2, plugins
    staging = tmp_path_factory.mktemp(request.param)
    for wheel in [*core, *plugins]:
        with zipfile.ZipFile(wheel) as archive:
            archive.extractall(staging)
    (binary,) = staging.glob("*.data/scripts/tailwindcss-bin")
    binary.rename(staging / "tailwindcss-bin").chmod(0o755)
    node_path = ":".join(
        f"/wheels/tailwindcss_bin/plugins/{name}/node_modules"
        for name in ("tailwindcss_motion", "tw_animate_css")
    )
    image = "debian:stretch-slim" if request.param == "glibc" else "alpine:3.24"
    container = run_cmd(
        [
            "docker",
            "run",
            "--detach",
            "--rm",
            "--workdir",
            "/smoke",
            "--volume",
            f"{staging}:/wheels:ro",
            "--volume",
            f"{tmp_path}:/smoke",
            "--env",
            f"NODE_PATH={node_path}",
            image,
            "tail",
            "-f",
            "/dev/null",
        ],
        check=True,
        timeout=120,
    ).stdout.strip()
    try:
        if request.param == "musl":
            run_cmd(
                [
                    "docker",
                    "exec",
                    container,
                    "apk",
                    "add",
                    "--no-cache",
                    "libstdc++",
                    "libgcc",
                ],
                check=True,
                timeout=120,
            )
        yield ["docker", "exec", "-i", container, "/wheels/tailwindcss-bin"]
    finally:
        run_cmd(["docker", "rm", "--force", container], check=True)


@pytest.fixture
def write_source(tmp_path, native_cli_command):
    def write(name, content):
        if native_cli_command[0] == "docker":
            # Write inside the container so native watch sees the change.
            run_cmd(
                native_cli_command[:-1] + ["tee", name],
                input=content,
                check=True,
            )
        else:
            (tmp_path / name).write_text(content, encoding="utf-8")

    return write


@pytest.fixture(params=["binary", "console", "module"])
def cli_command(request) -> list[str]:
    if request.param == "binary":
        return [find_tailwindcss_bin()]
    if request.param == "module":
        return [sys.executable, "-m", "tailwindcss_bin"]
    exe = "tailwindcss" + (sysconfig.get_config_var("EXE") or "")
    return [str(Path(sysconfig.get_path("scripts")) / exe)]


def run_cmd(
    argv: list[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    check: bool = False,
    input: str | None = None,
    timeout: float = 30,
) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            argv,
            cwd=cwd,
            env=env,
            check=check,
            capture_output=True,
            text=True,
            input=input,
            timeout=timeout,
        )
    except subprocess.CalledProcessError as error:
        print(error.stdout, end="")
        print(error.stderr, end="", file=sys.stderr)
        raise


def wait_for_css(process, output, selector):
    log = output.parent / "watch.log"
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        assert process.poll() is None, log.read_text(encoding="utf-8")
        if output.is_file():
            css = output.read_text(encoding="utf-8")
            if selector in css:
                return css
        time.sleep(0.05)
    pytest.fail(
        f"CSS watcher did not generate {selector}\n"
        f"{log.read_text(encoding='utf-8')}"
    )
