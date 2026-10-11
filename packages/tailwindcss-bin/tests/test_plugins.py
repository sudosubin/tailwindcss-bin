from __future__ import annotations

import os
from importlib import import_module
from pathlib import Path

from conftest import run_cmd
from tailwindcss_bin import apply_node_path
from tailwindcss_bin._find_tailwindcss import bundled_cli_name


def test_both_plugins_are_installed():
    for name in ("tailwindcss_motion", "tw_animate_css"):
        module = import_module(f"tailwindcss_bin.plugins.{name}")
        assert module.__file__ is not None
        assert (Path(module.__file__).parent / "node_modules").is_dir()


def test_plugins_compile(tmp_path, cli_command, monkeypatch):
    (tmp_path / "input.css").write_text(
        '@import "tailwindcss";\n'
        '@import "tw-animate-css";\n'
        '@plugin "tailwindcss-motion";\n'
    )
    (tmp_path / "index.html").write_text(
        '<p class="animate-in motion-preset-fade"></p>'
    )
    monkeypatch.delenv("NODE_PATH", raising=False)
    if Path(cli_command[0]).name == bundled_cli_name():
        apply_node_path()
    out = run_cmd(
        cli_command + ["-i", "input.css"],
        cwd=tmp_path,
        env=os.environ.copy(),
        check=True,
    ).stdout
    assert ".animate-in" in out
    assert ".motion-preset-fade" in out
