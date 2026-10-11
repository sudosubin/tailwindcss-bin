from __future__ import annotations

import subprocess
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
PKG_ROOT = WORKSPACE_ROOT / "packages" / "tailwindcss-bin"


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
    )
