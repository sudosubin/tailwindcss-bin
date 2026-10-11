from __future__ import annotations

import subprocess
import sys
import sysconfig
from pathlib import Path

import pytest
from tailwindcss_bin import find_tailwindcss_bin

WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
PKG_ROOT = WORKSPACE_ROOT / "packages" / "tailwindcss-bin"


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
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        argv,
        cwd=cwd,
        env=env,
        check=check,
        capture_output=True,
        text=True,
        timeout=30,
    )
