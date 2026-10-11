from __future__ import annotations

import os
import sys

import pytest
from conftest import run_cmd
from tailwindcss_bin import apply_node_path, find_tailwindcss_bin

pytest.importorskip("tailwindcss_bin.plugins.tw_animate_css")
pytest.importorskip("tailwindcss_bin.plugins.tailwindcss_motion")


def test_plugins_compile(tmp_path):
    (tmp_path / "input.css").write_text(
        '@import "tailwindcss";\n'
        '@import "tw-animate-css";\n'
        '@plugin "tailwindcss-motion";\n'
    )
    (tmp_path / "index.html").write_text(
        '<p class="animate-in motion-preset-fade"></p>'
    )
    apply_node_path()
    env = os.environ.copy()
    tailwindcss = find_tailwindcss_bin()
    out = run_cmd(
        [tailwindcss, "-i", "input.css"],
        cwd=tmp_path,
        env=env,
        check=True,
    ).stdout
    assert ".animate-in" in out
    assert ".motion-preset-fade" in out


def test_plugins_via_module_entry(tmp_path):
    (tmp_path / "input.css").write_text(
        '@import "tailwindcss";\n@import "tw-animate-css";\n'
    )
    (tmp_path / "index.html").write_text('<p class="animate-in"></p>')
    out = run_cmd(
        [sys.executable, "-m", "tailwindcss_bin", "-i", "input.css"],
        cwd=tmp_path,
        check=True,
    ).stdout
    assert ".animate-in" in out
