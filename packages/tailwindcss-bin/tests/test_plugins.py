from __future__ import annotations

import os
import subprocess
import sys

import pytest
from tailwindcss_bin import apply_node_path, find_tailwindcss_bin
from tailwindcss_bin._plugins import node_module_paths

pytest.importorskip("tailwindcss_bin.plugins.tw_animate_css")
pytest.importorskip("tailwindcss_bin.plugins.tailwindcss_motion")


def run(cmd, cwd, env) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd, cwd=cwd, env=env, check=True, capture_output=True, text=True
    )


def test_node_module_paths():
    assert len(node_module_paths()) >= 2


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
    out = run([tailwindcss, "-i", "input.css"], tmp_path, env).stdout
    assert ".animate-in" in out
    assert ".motion-preset-fade" in out


def test_module_entry(tmp_path):
    (tmp_path / "input.css").write_text(
        '@import "tailwindcss";\n@import "tw-animate-css";\n'
    )
    (tmp_path / "index.html").write_text('<p class="animate-in"></p>')
    out = run(
        [sys.executable, "-m", "tailwindcss_bin", "-i", "input.css"],
        tmp_path,
        os.environ.copy(),
    ).stdout
    assert ".animate-in" in out
