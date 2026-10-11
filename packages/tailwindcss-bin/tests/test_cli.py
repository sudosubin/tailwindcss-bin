from __future__ import annotations

import sys
from importlib.metadata import version

from conftest import run_cmd
from packaging.version import Version
from tailwindcss_bin import find_tailwindcss_bin

TAILWINDCSS = find_tailwindcss_bin()
COMMANDS = [[TAILWINDCSS], [sys.executable, "-m", "tailwindcss_bin"]]


def test_reports_bundled_version():
    expected = Version(version("tailwindcss-bin")).base_version
    for cmd in COMMANDS:
        assert f"tailwindcss v{expected}" in run_cmd(cmd + ["--help"]).stdout


def test_compiles_css(tmp_path):
    (tmp_path / "input.css").write_text('@import "tailwindcss";')
    (tmp_path / "index.html").write_text('<p class="p-4 md:flex"></p>')
    result = run_cmd(
        [TAILWINDCSS, "-i", "input.css"],
        cwd=tmp_path,
        check=True,
    )
    assert ".p-4" in result.stdout
    assert r".md\:flex" in result.stdout


def test_propagates_exit_code(tmp_path):
    for cmd in COMMANDS:
        assert (
            run_cmd(cmd + ["-i", "missing.css"], cwd=tmp_path).returncode != 0
        )
