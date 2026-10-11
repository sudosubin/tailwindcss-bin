from __future__ import annotations

import re
import subprocess
import sys
from textwrap import dedent

import pytest
from conftest import WORKSPACE_ROOT


@pytest.fixture(scope="module")
def upstream_version_check() -> str:
    workflow = (WORKSPACE_ROOT / ".github/workflows/update.yml").read_text()
    match = re.search(
        r"<<'PY_VERSION'[^\n]*\n(.*?)^[ \t]*PY_VERSION[ \t]*$",
        workflow,
        re.MULTILINE | re.DOTALL,
    )
    assert match is not None, "Version check heredoc is missing from update.yml"
    return dedent(match[1])


@pytest.mark.parametrize(
    ("current", "candidate", "code"),
    [
        ("4.3.3.dev1", "4.3.3", 0),
        ("4.3.3.post2", "4.3.3", 1),
        ("4.3.3.post2", "4.3.4", 0),
        ("4.3.3", "4.3.2", 1),
        ("4.3.9", "4.3.10", 0),
        ("4.3.3", "4.4.0-beta.1", 2),
        ("4.3.3", "4.4.0+local", 2),
        ("invalid", "4.4.0", 2),
    ],
)
def test_update_only_accepts_newer_stable_upstreams(
    current, candidate, code, upstream_version_check
):
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            upstream_version_check,
            current,
            candidate,
        ],
        capture_output=True,
        check=False,
        text=True,
        timeout=10,
    )
    assert result.returncode == code, result.stderr
