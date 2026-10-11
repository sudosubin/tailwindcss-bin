from __future__ import annotations

import subprocess
import sys
import sysconfig
import time
from pathlib import Path

import pytest
from tailwindcss_bin import find_tailwindcss_bin

WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
PKG_ROOT = WORKSPACE_ROOT / "packages" / "tailwindcss-bin"


@pytest.fixture
def native_cli_command() -> list[str]:
    return [find_tailwindcss_bin()]


@pytest.fixture(params=["binary", "tailwindcss", "tailwindcss-bin", "module"])
def cli_command(request) -> list[str]:
    if request.param == "binary":
        return [find_tailwindcss_bin()]
    if request.param == "module":
        return [sys.executable, "-m", "tailwindcss_bin"]
    exe = request.param + (sysconfig.get_config_var("EXE") or "")
    return [str(Path(sysconfig.get_path("scripts")) / exe)]


def run_cmd(
    argv: list[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    check: bool = False,
) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            argv,
            cwd=cwd,
            env=env,
            check=check,
            capture_output=True,
            text=True,
            timeout=30,
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
